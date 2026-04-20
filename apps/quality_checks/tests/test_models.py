import pytest

from ..models import QCCheckCategory, QCItem, QCSuggestion, QualityCheck
from .factories import (
    QCCheckCategoryFactory,
    QCItemFactory,
    QCSuggestionFactory,
    QualityCheckFactory,
)

pytestmark = pytest.mark.django_db


class TestQualityCheckModel:
    def test_create_quality_check(self):
        qc = QualityCheckFactory()
        assert qc.status == 'pending'
        assert qc.overall_score == 0
        assert qc.can_submit is False

    def test_quality_check_proposal_relation(self):
        qc = QualityCheckFactory()
        assert qc.proposal is not None
        assert qc.proposal.quality_check == qc


class TestQCCheckCategoryModel:
    def test_create_category(self):
        cat = QCCheckCategoryFactory()
        assert cat.category in [c[0] for c in QCCheckCategory.CATEGORY_CHOICES]
        assert cat.status in [c[0] for c in QCCheckCategory.STATUS_CHOICES]

    def test_category_quality_check_relation(self):
        qc = QualityCheckFactory()
        cat = QCCheckCategoryFactory(quality_check=qc)
        assert qc.categories.count() == 1
        assert qc.categories.first() == cat


class TestQCItemModel:
    def test_create_item(self):
        item = QCItemFactory()
        assert item.description
        assert item.status in [c[0] for c in QCItem.STATUS_CHOICES]

    def test_item_category_relation(self):
        cat = QCCheckCategoryFactory()
        item = QCItemFactory(category=cat)
        assert cat.items.count() == 1
        assert cat.items.first() == item


class TestQCSuggestionModel:
    def test_create_suggestion(self):
        suggestion = QCSuggestionFactory()
        assert suggestion.text
        assert suggestion.action in [c[0] for c in QCSuggestion.ACTION_CHOICES]
        assert suggestion.applied is False
        assert suggestion.ignored is False

    def test_suggestion_quality_check_relation(self):
        qc = QualityCheckFactory()
        suggestion = QCSuggestionFactory(quality_check=qc)
        assert qc.suggestions.count() == 1
        assert qc.suggestions.first() == suggestion
