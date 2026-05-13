import factory

from apps.users.models import User

from ..models import ActivityLog, Notification, NotificationPreference


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    type = 'info'
    title = factory.Sequence(lambda n: f'Notification {n}')
    message = factory.Faker('paragraph')
    action_label = ''
    action_url = ''
    read = False


class NotificationPreferenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationPreference

    user = factory.SubFactory(UserFactory)
    email_on_new_opportunity = True
    email_on_proposal_status = True
    email_on_scrape_complete = True


class ActivityLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActivityLog

    user = factory.SubFactory(UserFactory)
    type = 'proposal_created'
    description = factory.Faker('paragraph')
    metadata = factory.LazyFunction(dict)
