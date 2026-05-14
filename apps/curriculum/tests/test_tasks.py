import io
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from docx import Document

from apps.curriculum.models import CVOpportunityMatch, Curriculum, CVSuggestion
from apps.curriculum.matching import match_cv_to_opportunity
from apps.curriculum.tasks import analyze_cv_with_ai
from apps.opportunities.models import Requirement
from apps.opportunities.tests.factories import OpportunityFactory
from apps.opportunities.tests.factories import UserFactory


def _docx_file(text):
    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile(
        'consultant.docx',
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )


@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class CurriculumAnalysisTaskTests(TestCase):
    def test_analyze_docx_cv_persists_extracted_data_and_suggestions(self):
        user = UserFactory()
        curriculum = Curriculum.objects.create(
            user=user,
            file_name='consultant.docx',
            file_type='docx',
            file=_docx_file('Senior consultant with governance and M&E experience.'),
        )
        extracted = {
            'name': 'Ana Silva',
            'email': 'ana@example.com',
            'phone': '+238 999 99 99',
            'location': 'Praia, Cabo Verde',
            'summary': 'Senior consultant in governance.',
            'experience': [{'title': 'Consultant', 'organization': 'Firm', 'dateRange': '2020-2026'}],
            'education': [{'title': 'MSc', 'organization': 'University', 'dateRange': '2018'}],
            'skills': ['Governance', 'M&E', 'Procurement', 'Strategy', 'Reporting'],
            'languages': ['Portuguese (Native)', 'English (Fluent)'],
            'certifications': [],
            'publications': [],
        }

        with patch('apps.curriculum.tasks._ai_extract', return_value=extracted):
            result = analyze_cv_with_ai(curriculum.id)

        curriculum.refresh_from_db()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(curriculum.status, 'analyzed')
        self.assertEqual(curriculum.extracted_data['name'], 'Ana Silva')
        self.assertGreater(curriculum.analysis_score, 0)
        self.assertTrue(CVSuggestion.objects.filter(curriculum=curriculum).exists())

    def test_legacy_doc_cv_fails_with_clear_error_status(self):
        user = UserFactory()
        curriculum = Curriculum.objects.create(
            user=user,
            file_name='legacy.doc',
            file_type='doc',
            file=SimpleUploadedFile('legacy.doc', b'not a docx file'),
        )

        result = analyze_cv_with_ai(curriculum.id)

        curriculum.refresh_from_db()
        self.assertEqual(result['status'], 'error')
        self.assertEqual(curriculum.status, 'error')


class CVOpportunityMatchTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def _curriculum(self):
        return Curriculum.objects.create(
            user=self.user,
            file_name='consultant.docx',
            file_type='docx',
            file=SimpleUploadedFile('consultant.docx', b'placeholder'),
            status='analyzed',
            extracted_data={
                'skills': ['Procurement', 'Monitoring and Evaluation', 'Governance'],
                'experience': [
                    {
                        'title': 'Senior Consultant',
                        'description': 'Led procurement governance and monitoring assignments.',
                    }
                ],
                'education': [{'title': 'MSc Public Policy'}],
                'languages': ['Portuguese', 'English'],
            },
        )

    def _opportunity(self):
        opportunity = OpportunityFactory(
            title='Governance procurement monitoring',
            description='Requires procurement, governance, monitoring and reporting experience.',
        )
        Requirement.objects.create(
            opportunity=opportunity,
            category='technical',
            description='Procurement governance monitoring and reporting',
            priority='mandatory',
        )
        return opportunity

    def test_match_cv_to_opportunity_persists_score_and_gaps(self):
        curriculum = self._curriculum()
        opportunity = self._opportunity()

        match = match_cv_to_opportunity(curriculum, opportunity)

        self.assertEqual(match.curriculum, curriculum)
        self.assertEqual(match.opportunity, opportunity)
        self.assertGreater(match.overall_score, 0)
        self.assertIn('procurement', match.matched_skills)
        self.assertTrue(CVOpportunityMatch.objects.filter(curriculum=curriculum, opportunity=opportunity).exists())

    def test_match_opportunity_endpoint_computes_missing_match(self):
        curriculum = self._curriculum()
        opportunity = self._opportunity()
        url = reverse(
            'curriculum:curriculum-match-opportunity',
            kwargs={'pk': curriculum.pk, 'opp_id': opportunity.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['curriculum'], curriculum.id)
        self.assertEqual(response.data['opportunity'], opportunity.id)
        self.assertGreater(response.data['overall_score'], 0)
