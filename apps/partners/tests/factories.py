import factory

from apps.partners.models import PartnerProfile


class PartnerProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartnerProfile

    name = factory.Sequence(lambda n: f'Partner {n}')
    sectors = factory.LazyFunction(list)
    geographies = factory.LazyFunction(list)
    capabilities = factory.LazyFunction(list)
    trust_score = 50
    is_active = True
