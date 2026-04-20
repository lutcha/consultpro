import factory

from apps.users.models import User

from ..models import Team


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'teamuser{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'consultant'


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f'Team {n}')
    description = factory.Faker('paragraph')

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.members.add(user)
