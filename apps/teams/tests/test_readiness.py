"""
Tests for apps.teams.readiness - team readiness service.

Covers: no team, member without CV, member with cv_document,
member with linked curriculum, suggested_profile status, confirmed status.
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.curriculum.models import Curriculum
from apps.proposals.models import ProposalTeamMember
from apps.proposals.tests.factories import (
    OpportunityFactory,
    ProposalFactory,
    ProposalTeamMemberFactory,
    UserFactory,
)
from apps.teams.readiness import compute_team_readiness

pytestmark = pytest.mark.django_db


@pytest.fixture
def proposal_with_opportunity():
    opportunity = OpportunityFactory()
    return ProposalFactory(opportunity=opportunity)


class TestComputeTeamReadinessNoMembers:
    def test_empty_team_returns_not_started(self, proposal_with_opportunity):
        result = compute_team_readiness(proposal_with_opportunity)
        assert result['readiness'] == 'not_started'
        assert result['total_members'] == 0
        assert result['confirmed_count'] == 0
        assert result['members'] == []
        assert result['missing_cvs'] == []
        assert result['suggested_profiles'] == []
        assert result['warnings'] == []


class TestComputeTeamReadinessMemberNoCv:
    def test_member_without_cv_is_in_missing_cvs(self, proposal_with_opportunity):
        member = ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            cv_attached=False,
            cv_document=None,
            team_member_status='cv_pending',
        )
        result = compute_team_readiness(proposal_with_opportunity)
        assert result['readiness'] == 'in_progress'
        assert result['cv_missing_count'] == 1
        assert len(result['missing_cvs']) == 1
        assert result['missing_cvs'][0]['member_id'] == member.id
        assert result['members'][0]['has_cv'] is False

    def test_member_without_cv_has_warning(self, proposal_with_opportunity):
        ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            cv_attached=False,
            cv_document=None,
        )
        result = compute_team_readiness(proposal_with_opportunity)
        assert any('CV' in w for w in result['warnings'])


class TestComputeTeamReadinessMemberWithCvDocument:
    def test_member_with_cv_document_has_cv(self, proposal_with_opportunity):
        fake_cv = SimpleUploadedFile('cv.pdf', b'dummy', content_type='application/pdf')
        member = ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            cv_attached=False,
            cv_document=fake_cv,
            team_member_status='cv_pending',
        )
        result = compute_team_readiness(proposal_with_opportunity)
        entry = next(m for m in result['members'] if m['member_id'] == member.id)
        assert entry['has_cv'] is True
        assert entry['has_cv_document'] is True
        assert entry['curriculum_id'] is None
        assert entry['curriculum_score'] is None

    def test_member_with_cv_attached_flag_has_cv(self, proposal_with_opportunity):
        member = ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            cv_attached=True,
            team_member_status='cv_pending',
        )
        result = compute_team_readiness(proposal_with_opportunity)
        entry = next(m for m in result['members'] if m['member_id'] == member.id)
        assert entry['has_cv'] is True
        assert entry['curriculum_score'] is None


class TestComputeTeamReadinessMemberWithCurriculum:
    def test_member_with_curriculum_gets_score(self, proposal_with_opportunity):
        user = UserFactory()
        curriculum = Curriculum.objects.create(
            user=user,
            file_name='cv_test.docx',
            file=SimpleUploadedFile('cv_test.docx', b'content'),
            file_type='docx',
            status='analyzed',
            extracted_data={
                'skills': ['python', 'django', 'management'],
                'experience': [{'title': 'Senior Consultant', 'years': 5}],
                'education': [{'degree': 'MBA'}],
                'languages': ['english', 'french'],
            },
        )
        member = ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            user=user,
            curriculum=curriculum,
            team_member_status='confirmed',
            cv_attached=False,
        )
        result = compute_team_readiness(proposal_with_opportunity)
        entry = next(m for m in result['members'] if m['member_id'] == member.id)
        assert entry['has_cv'] is True
        assert entry['curriculum_id'] == curriculum.id
        assert entry['curriculum_score'] is not None
        assert isinstance(entry['curriculum_score'], int)
        assert 0 <= entry['curriculum_score'] <= 100

    def test_curriculum_not_in_missing_cvs(self, proposal_with_opportunity):
        user = UserFactory()
        curriculum = Curriculum.objects.create(
            user=user,
            file_name='cv.pdf',
            file=SimpleUploadedFile('cv.pdf', b'content'),
            file_type='pdf',
            status='analyzed',
            extracted_data={'skills': [], 'experience': [], 'education': [], 'languages': []},
        )
        ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            user=user,
            curriculum=curriculum,
            team_member_status='confirmed',
        )
        result = compute_team_readiness(proposal_with_opportunity)
        assert result['cv_missing_count'] == 0
        assert result['missing_cvs'] == []


class TestComputeTeamReadinessSuggestedProfile:
    def test_suggested_profile_status_appears_in_suggested_profiles(
        self, proposal_with_opportunity
    ):
        member = ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            user=None,
            team_member_status='suggested_profile',
            suggested_profile={'name': 'Data Scientist', 'seniority': 'senior'},
        )
        result = compute_team_readiness(proposal_with_opportunity)
        assert len(result['suggested_profiles']) == 1
        assert result['suggested_profiles'][0]['member_id'] == member.id
        assert any('sugerido' in w.lower() for w in result['warnings'])

    def test_all_suggested_returns_not_started(self, proposal_with_opportunity):
        ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            user=None,
            team_member_status='suggested_profile',
            suggested_profile={'name': 'Analyst'},
        )
        result = compute_team_readiness(proposal_with_opportunity)
        assert result['readiness'] == 'not_started'


class TestComputeTeamReadinessConfirmedTeam:
    def test_all_confirmed_with_cv_returns_ready(self, proposal_with_opportunity):
        for _ in range(2):
            ProposalTeamMemberFactory(
                proposal=proposal_with_opportunity,
                cv_attached=True,
                team_member_status='confirmed',
            )
        result = compute_team_readiness(proposal_with_opportunity)
        assert result['readiness'] == 'ready'
        assert result['confirmed_count'] == 2
        assert result['cv_missing_count'] == 0
        assert result['warnings'] == []

    def test_mixed_statuses_returns_in_progress(self, proposal_with_opportunity):
        ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            cv_attached=True,
            team_member_status='confirmed',
        )
        ProposalTeamMemberFactory(
            proposal=proposal_with_opportunity,
            cv_attached=False,
            team_member_status='cv_pending',
        )
        result = compute_team_readiness(proposal_with_opportunity)
        assert result['readiness'] == 'in_progress'
        assert result['confirmed_count'] == 1
