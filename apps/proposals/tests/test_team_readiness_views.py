"""
Tests for GET /api/proposals/{id}/team-readiness/

Verifies: endpoint availability, response structure, correct
readiness values for empty team, member without CV, member with CV,
and member with linked curriculum. Does NOT test QC logic.
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.curriculum.models import Curriculum
from apps.proposals.tests.factories import (
    OpportunityFactory,
    ProposalFactory,
    ProposalTeamMemberFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager_user():
    return UserFactory(role='manager')


@pytest.fixture
def auth_client(manager_user):
    """APIClient authenticated as a manager (can see all proposals)."""
    client = APIClient()
    client.force_authenticate(user=manager_user)
    return client, manager_user


@pytest.fixture
def proposal(manager_user):
    return ProposalFactory(
        opportunity=OpportunityFactory(),
        created_by=manager_user,
    )


def _readiness_url(proposal_id):
    return f'/api/proposals/{proposal_id}/team-readiness/'


class TestTeamReadinessEndpoint:
    def test_requires_authentication(self, proposal):
        client = APIClient()
        response = client.get(_readiness_url(proposal.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_200_for_authenticated_user(self, auth_client, proposal):
        client, _ = auth_client
        response = client.get(_readiness_url(proposal.id))
        assert response.status_code == status.HTTP_200_OK

    def test_404_for_missing_proposal(self, auth_client):
        client, _ = auth_client
        response = client.get(_readiness_url(99999))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_response_has_required_keys(self, auth_client, proposal):
        client, _ = auth_client
        response = client.get(_readiness_url(proposal.id))
        data = response.data
        required_keys = [
            'proposal_id', 'readiness', 'total_members', 'confirmed_count',
            'cv_missing_count', 'suggested_count', 'members',
            'missing_cvs', 'suggested_profiles', 'warnings',
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

    def test_empty_team_readiness(self, auth_client, proposal):
        client, _ = auth_client
        response = client.get(_readiness_url(proposal.id))
        data = response.data
        assert data['readiness'] == 'not_started'
        assert data['total_members'] == 0
        assert data['members'] == []

    def test_proposal_id_in_response(self, auth_client, proposal):
        client, _ = auth_client
        response = client.get(_readiness_url(proposal.id))
        assert response.data['proposal_id'] == proposal.id


class TestTeamReadinessWithMembers:
    def test_member_without_cv_in_missing_cvs(self, auth_client, proposal):
        client, _ = auth_client
        ProposalTeamMemberFactory(
            proposal=proposal,
            cv_attached=False,
            cv_document=None,
            team_member_status='cv_pending',
        )
        response = client.get(_readiness_url(proposal.id))
        data = response.data
        assert data['readiness'] == 'in_progress'
        assert data['cv_missing_count'] == 1
        assert len(data['missing_cvs']) == 1
        assert len(data['members']) == 1
        assert data['members'][0]['has_cv'] is False

    def test_member_with_cv_document_not_in_missing_cvs(self, auth_client, proposal):
        client, _ = auth_client
        fake_cv = SimpleUploadedFile('cv.pdf', b'dummy', content_type='application/pdf')
        ProposalTeamMemberFactory(
            proposal=proposal,
            cv_attached=False,
            cv_document=fake_cv,
            team_member_status='cv_pending',
        )
        response = client.get(_readiness_url(proposal.id))
        data = response.data
        assert data['cv_missing_count'] == 0
        assert data['members'][0]['has_cv'] is True
        assert data['members'][0]['curriculum_score'] is None

    def test_member_with_curriculum_gets_score(self, auth_client, proposal):
        client, _ = auth_client
        user = UserFactory()
        curriculum = Curriculum.objects.create(
            user=user,
            file_name='cv.docx',
            file=SimpleUploadedFile('cv.docx', b'content'),
            file_type='docx',
            status='analyzed',
            extracted_data={
                'skills': ['management', 'consulting'],
                'experience': [{'title': 'Consultant'}],
                'education': [{'degree': 'MBA'}],
                'languages': ['english'],
            },
        )
        ProposalTeamMemberFactory(
            proposal=proposal,
            user=user,
            curriculum=curriculum,
            team_member_status='confirmed',
        )
        response = client.get(_readiness_url(proposal.id))
        data = response.data
        member_data = data['members'][0]
        assert member_data['curriculum_id'] == curriculum.id
        assert member_data['curriculum_score'] is not None
        assert data['cv_missing_count'] == 0

    def test_suggested_profile_no_user(self, auth_client, proposal):
        client, _ = auth_client
        ProposalTeamMemberFactory(
            proposal=proposal,
            user=None,
            team_member_status='suggested_profile',
            suggested_profile={'name': 'Senior Data Analyst'},
        )
        response = client.get(_readiness_url(proposal.id))
        data = response.data
        assert data['suggested_count'] == 1
        assert len(data['suggested_profiles']) == 1
        assert data['members'][0]['team_member_status'] == 'suggested_profile'

    def test_confirmed_team_with_cv_returns_ready(self, auth_client, proposal):
        client, _ = auth_client
        for _ in range(2):
            ProposalTeamMemberFactory(
                proposal=proposal,
                cv_attached=True,
                team_member_status='confirmed',
            )
        response = client.get(_readiness_url(proposal.id))
        data = response.data
        assert data['readiness'] == 'ready'
        assert data['confirmed_count'] == 2
        assert data['warnings'] == []

    def test_team_readiness_does_not_affect_qc(self, auth_client, manager_user):
        """
        Calling team-readiness must never change proposal status or QC score.
        Purely informational assertion: POST to team-readiness is not allowed.
        """
        client, _ = auth_client
        proposal = ProposalFactory(status='draft', created_by=manager_user)
        response = client.post(_readiness_url(proposal.id))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        proposal.refresh_from_db()
        assert proposal.status == 'draft'
