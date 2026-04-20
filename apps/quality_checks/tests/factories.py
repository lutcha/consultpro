import factory
from django.utils import timezone

from apps.opportunities.models import Opportunity
from apps.proposals.models import Proposal
from apps.users.models import User

from ..models import QCCheckCategory, QCItem, QCSuggestion, QualityCheck


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')


class OpportunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Opportunity

    title = factory.Sequence(lambda n: f'Opportunity {n}')
    client = factory.Faker('company')
    sector = factory.Faker('word')
    country = factory.Faker('country')
    value = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    deadline = factory.Faker('future_datetime', tzinfo=timezone.get_current_timezone())
    description = factory.Faker('paragraph')


class ProposalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Proposal

    opportunity = factory.SubFactory(OpportunityFactory)
    title = factory.Sequence(lambda n: f'Proposal {n}')
    version = 1
    status = 'draft'
    created_by = factory.SubFactory(UserFactory)


class QualityCheckFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QualityCheck

    proposal = factory.SubFactory(ProposalFactory)
    overall_score = 0
    status = 'pending'
    can_submit = False


class QCCheckCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QCCheckCategory

    quality_check = factory.SubFactory(QualityCheckFactory)
    category = 'compliance'
    score = 100
    status = 'pass'


class QCItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QCItem

    category = factory.SubFactory(QCCheckCategoryFactory)
    description = factory.Faker('sentence')
    status = 'pass'
    section = ''


class QCSuggestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QCSuggestion

    quality_check = factory.SubFactory(QualityCheckFactory)
    text = factory.Faker('paragraph')
    action = 'replace'
    target_section = 'Resumo Executivo'
    applied = False
    ignored = False
