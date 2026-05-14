import io
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from docx import Document

from apps.curriculum.models import Curriculum, CVSuggestion
from apps.curriculum.tasks import analyze_cv_with_ai
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
