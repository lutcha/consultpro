import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ..models import Budget
from .factories import (
    BudgetFactory,
    OpportunityFactory,
    ProposalFactory,
    ProposalSectionFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user


class TestProposalViewSet:
    def test_list_proposals(self, authenticated_client):
        client, user = authenticated_client
        ProposalFactory(created_by=user)
        url = reverse('proposal-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_create_proposal(self, authenticated_client):
        client, user = authenticated_client
        opportunity = OpportunityFactory()
        url = reverse('proposal-list')
        data = {
            'opportunity': opportunity.id,
            'title': 'New Proposal',
            'version': 1,
            'status': 'draft',
        }
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_sections_action(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        ProposalSectionFactory(proposal=proposal)
        url = reverse('proposal-sections', kwargs={'pk': proposal.pk})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_section_detail_get(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        section = ProposalSectionFactory(proposal=proposal)
        url = reverse(
            'proposal-section-detail',
            kwargs={'pk': proposal.pk, 'section_id': section.pk},
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == section.id

    def test_section_detail_put(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        section = ProposalSectionFactory(proposal=proposal)
        url = reverse(
            'proposal-section-detail',
            kwargs={'pk': proposal.pk, 'section_id': section.pk},
        )
        response = client.put(
            url, {'content': 'Updated content'}, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        section.refresh_from_db()
        assert section.content == 'Updated content'

    def test_add_comment(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        section = ProposalSectionFactory(proposal=proposal)
        url = reverse('proposal-add-comment', kwargs={'pk': proposal.pk})
        response = client.post(
            url,
            {'section_id': section.id, 'text': 'Nice work'},
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_ai_suggest(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        section = ProposalSectionFactory(proposal=proposal)
        url = reverse('proposal-ai-suggest', kwargs={'pk': proposal.pk})
        response = client.post(
            url,
            {'section_id': section.id, 'action': 'expand'},
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_save_action(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        url = reverse('proposal-save', kwargs={'pk': proposal.pk})
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.auto_save_status == 'saved'
        assert proposal.last_saved_at is not None

    def test_submit_action(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        url = reverse('proposal-submit', kwargs={'pk': proposal.pk})
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK
        proposal.refresh_from_db()
        assert proposal.status == 'qc_check'
        assert proposal.submitted_at is not None

    def test_team_action(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        url = reverse('proposal-team', kwargs={'pk': proposal.pk})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_add_team_member(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        new_user = UserFactory()
        url = reverse('proposal-add-team-member', kwargs={'pk': proposal.pk})
        response = client.post(
            url,
            {
                'user_id': new_user.id,
                'role': 'Consultant',
                'hours': 10,
                'hourly_rate': 50.00,
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_budget_get(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        BudgetFactory(proposal=proposal)
        url = reverse('proposal-budget', kwargs={'pk': proposal.pk})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_budget_post_create(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        url = reverse('proposal-budget', kwargs={'pk': proposal.pk})
        response = client.post(
            url,
            {'total': 5000.00, 'currency': 'EUR'},
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Budget.objects.filter(proposal=proposal).exists()

    def test_budget_post_update(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(created_by=user)
        BudgetFactory(proposal=proposal, total=1000.00)
        url = reverse('proposal-budget', kwargs={'pk': proposal.pk})
        response = client.post(
            url,
            {'total': 2000.00},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        proposal.budget.refresh_from_db()
        assert proposal.budget.total == 2000.00
