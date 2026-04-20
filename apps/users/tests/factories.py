import factory
from apps.users.models import User, Certification


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'consultant'
    availability = 'available'
    skills = factory.LazyFunction(list)
    languages = factory.LazyFunction(list)


class CertificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Certification

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('word')
    issuer = factory.Faker('company')
    issued_date = factory.Faker('date_object')
    verified = False
