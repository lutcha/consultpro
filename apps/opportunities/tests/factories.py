import factory
from django.utils import timezone

from apps.users.models import User

from ..models import Opportunity, Requirement, Risk


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
    region = factory.Faker('city')
    value = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    currency = 'USD'
    deadline = factory.Faker('future_datetime', tzinfo=timezone.get_current_timezone())
    status = 'new'
    description = factory.Faker('paragraph')
    evaluation_criteria = 'qcbs'
    technical_weight = 70
    financial_weight = 30
    reference_number = factory.Sequence(lambda n: f'REF-{n:04d}')
    url_source = factory.Faker('url')
    ai_summary = factory.Faker('paragraph')
    ai_analysis_status = 'pending'

    @factory.post_generation
    def assigned_to(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.assigned_to.add(user)


class RequirementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Requirement

    opportunity = factory.SubFactory(OpportunityFactory)
    category = 'functional'
    description = factory.Faker('paragraph')
    priority = 'mandatory'
    is_covered = False
    covered_in = ''
    extracted_by_ai = False


class RiskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Risk

    opportunity = factory.SubFactory(OpportunityFactory)
    description = factory.Faker('sentence')
    severity = 'medium'
    mitigation = factory.Faker('sentence')
    identified_by_ai = False
