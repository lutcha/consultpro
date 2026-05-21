import factory

from apps.opportunities.models import Opportunity
from apps.users.models import User
from apps.proposals.models import (
    AISuggestion,
    Budget,
    BudgetItem,
    Comment,
    Proposal,
    ProposalExportRequest,
    ProposalPostMortem,
    ProposalSection,
    ProposalTeamMember,
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class OpportunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Opportunity

    title = factory.Faker('sentence', nb_words=4)
    client = factory.Faker('company')
    sector = factory.Faker('word')
    value = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    deadline = factory.Faker('future_datetime')
    description = factory.Faker('paragraph')


class ProposalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Proposal

    opportunity = factory.SubFactory(OpportunityFactory)
    title = factory.Faker('sentence', nb_words=6)
    version = 1
    status = 'draft'
    created_by = factory.SubFactory(UserFactory)


class ProposalTeamMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProposalTeamMember

    proposal = factory.SubFactory(ProposalFactory)
    user = factory.SubFactory(UserFactory)
    role = factory.Faker('job')
    hours = 40
    hourly_rate = 100.00
    cv_attached = False


class ProposalSectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProposalSection

    proposal = factory.SubFactory(ProposalFactory)
    section_type = 'cover'
    title = factory.Faker('sentence', nb_words=3)
    content = factory.Faker('paragraph')
    order = factory.Sequence(lambda n: n)
    is_complete = False


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    section = factory.SubFactory(ProposalSectionFactory)
    user = factory.SubFactory(UserFactory)
    text = factory.Faker('paragraph')
    resolved = False


class AISuggestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AISuggestion

    section = factory.SubFactory(ProposalSectionFactory)
    action = 'expand'
    description = factory.Faker('sentence')
    generated_content = ''
    applied = False


class BudgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Budget

    proposal = factory.SubFactory(ProposalFactory)
    total = 10000.00
    currency = 'USD'


class BudgetItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BudgetItem

    budget = factory.SubFactory(BudgetFactory)
    category = 'personnel'
    amount = 5000.00
    description = factory.Faker('sentence')


class ProposalPostMortemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProposalPostMortem

    proposal = factory.SubFactory(ProposalFactory)
    outcome = 'lost'
    outcome_reason = 'Pricing was not competitive.'
    client_feedback = 'Technically strong, commercially expensive.'
    lessons_learned = factory.LazyFunction(lambda: ['Review pricing assumptions'])
    scoring_adjustments = factory.LazyFunction(lambda: {'margin': -5})
    sentiment = 'negative'
    evidence = factory.LazyFunction(dict)
    created_by = factory.SubFactory(UserFactory)


class ProposalExportRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProposalExportRequest

    proposal = factory.SubFactory(ProposalFactory)
    export_type = 'executive_summary'
    status = 'completed'
    requested_by = factory.SubFactory(UserFactory)
    parameters = factory.LazyFunction(dict)
    executive_summary = 'Executive summary'
    output_metadata = factory.LazyFunction(lambda: {'generator': 'deterministic_v1'})
