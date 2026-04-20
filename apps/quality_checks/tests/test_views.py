import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ..models import QCCheckCategory, QCItem, QCSuggestion, QualityCheck
from .factories import (
    ProposalFactory,
    QCCheckCategoryFactory,
    QCItemFactory,
    QCSuggestionFactory,
    QualityCheckFactory,
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


class TestQualityCheckViewSet:
    def test_list_quality_checks(self, authenticated_client):
        client, user = authenticated_client
        QualityCheckFactory()
        url = reverse('quality-check-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_retrieve_quality_check(self, authenticated_client):
        client, user = authenticated_client
        qc = QualityCheckFactory()
        cat = QCCheckCategoryFactory(quality_check=qc)
        QCItemFactory(category=cat)
        QCSuggestionFactory(quality_check=qc)

        url = reverse('quality-check-detail', kwargs={'pk': qc.pk})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'categories' in response.data
        assert 'suggestions' in response.data
        assert 'checks' in response.data

    def test_run_action(self, authenticated_client):
        client, user = authenticated_client
        qc = QualityCheckFactory(status='pending')

        url = reverse('quality-check-run', kwargs={'pk': qc.pk})
        data = {
            'categories': [
                {
                    'category': 'compliance',
                    'score': 90,
                    'status': 'pass',
                    'items': [
                        {'description': 'Item 1', 'status': 'pass', 'section': 'Sec 1'}
                    ],
                },
                {
                    'category': 'coherence',
                    'score': 80,
                    'status': 'warn',
                    'items': [
                        {'description': 'Item 2', 'status': 'warn', 'section': 'Sec 2'}
                    ],
                },
            ]
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        qc.refresh_from_db()
        assert qc.status == 'completed'
        assert qc.overall_score == 85
        assert qc.can_submit is True
        assert qc.categories.count() == 2

    def test_run_action_with_fail(self, authenticated_client):
        client, user = authenticated_client
        qc = QualityCheckFactory(status='pending')

        url = reverse('quality-check-run', kwargs={'pk': qc.pk})
        data = {
            'categories': [
                {
                    'category': 'compliance',
                    'score': 90,
                    'status': 'pass',
                    'items': [],
                },
                {
                    'category': 'budget',
                    'score': 70,
                    'status': 'fail',
                    'items': [],
                },
            ]
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        qc.refresh_from_db()
        assert qc.overall_score == 80
        assert qc.can_submit is False

    def test_apply_suggestion(self, authenticated_client):
        client, user = authenticated_client
        qc = QualityCheckFactory()
        suggestion = QCSuggestionFactory(quality_check=qc)

        url = reverse('quality-check-apply-suggestion', kwargs={'pk': qc.pk})
        response = client.post(url, {'suggestion_id': suggestion.id}, format='json')
        assert response.status_code == status.HTTP_200_OK

        suggestion.refresh_from_db()
        assert suggestion.applied is True

    def test_apply_suggestion_missing_id(self, authenticated_client):
        client, user = authenticated_client
        qc = QualityCheckFactory()

        url = reverse('quality-check-apply-suggestion', kwargs={'pk': qc.pk})
        response = client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ignore_suggestion(self, authenticated_client):
        client, user = authenticated_client
        qc = QualityCheckFactory()
        suggestion = QCSuggestionFactory(quality_check=qc)

        url = reverse('quality-check-ignore-suggestion', kwargs={'pk': qc.pk})
        response = client.post(url, {'suggestion_id': suggestion.id}, format='json')
        assert response.status_code == status.HTTP_200_OK

        suggestion.refresh_from_db()
        assert suggestion.ignored is True

    def test_approve_action(self, authenticated_client):
        client, user = authenticated_client
        proposal = ProposalFactory(status='qc_check')
        qc = QualityCheckFactory(proposal=proposal)

        url = reverse('quality-check-approve', kwargs={'pk': qc.pk})
        response = client.post(url)
        assert response.status_code == status.HTTP_200_OK

        proposal.refresh_from_db()
        assert proposal.status == 'approved'
