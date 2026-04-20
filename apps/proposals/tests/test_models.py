import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import AISuggestion, Proposal, ProposalSection
from .factories import (
    AISuggestionFactory,
    BudgetFactory,
    BudgetItemFactory,
    CommentFactory,
    ProposalFactory,
    ProposalSectionFactory,
    ProposalTeamMemberFactory,
)

pytestmark = pytest.mark.django_db


class TestProposalModel:
    def test_create_proposal(self):
        proposal = ProposalFactory()
        assert proposal.title
        assert proposal.status == 'draft'

    def test_proposal_ordering(self):
        ProposalFactory()
        ProposalFactory()
        proposals = list(Proposal.objects.all())
        assert proposals[0].updated_at >= proposals[1].updated_at


class TestProposalTeamMemberModel:
    def test_create_team_member(self):
        member = ProposalTeamMemberFactory()
        assert member.role
        assert member.hours >= 0

    def test_cv_upload(self):
        member = ProposalTeamMemberFactory()
        member.cv_document = SimpleUploadedFile('cv.pdf', b'file content')
        member.save()
        assert member.cv_document


class TestProposalSectionModel:
    def test_section_ordering(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, order=2)
        ProposalSectionFactory(proposal=proposal, order=1)
        sections = list(proposal.sections.all())
        assert sections[0].order < sections[1].order


class TestCommentModel:
    def test_create_comment(self):
        comment = CommentFactory()
        assert comment.text
        assert comment.resolved is False


class TestAISuggestionModel:
    def test_create_suggestion(self):
        suggestion = AISuggestionFactory()
        assert suggestion.action in [c[0] for c in AISuggestion.ACTION_CHOICES]
        assert suggestion.applied is False


class TestBudgetModel:
    def test_create_budget(self):
        budget = BudgetFactory()
        assert budget.total >= 0
        assert budget.currency == 'USD'


class TestBudgetItemModel:
    def test_create_budget_item(self):
        item = BudgetItemFactory()
        assert item.amount >= 0
        assert item.category in [c[0] for c in BudgetItem.CATEGORY_CHOICES]
