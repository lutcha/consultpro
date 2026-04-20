from django.test import TestCase

from ..models import Team
from .factories import TeamFactory, UserFactory


class TeamModelTests(TestCase):
    def test_str_representation(self):
        team = TeamFactory(name='Alpha Team')
        self.assertEqual(str(team), 'Alpha Team')

    def test_default_description_blank(self):
        team = TeamFactory(description='')
        self.assertEqual(team.description, '')

    def test_members_many_to_many(self):
        user1 = UserFactory()
        user2 = UserFactory()
        team = TeamFactory(members=[user1, user2])
        self.assertEqual(team.members.count(), 2)
        self.assertIn(user1, team.members.all())
        self.assertIn(user2, team.members.all())

    def test_team_ordering(self):
        older = TeamFactory()
        older.created_at = older.created_at.__class__.now() - older.created_at.__class__.timedelta(days=1)
        older.save()

        newer = TeamFactory()
        team_list = list(Team.objects.all())
        self.assertEqual(team_list[0], newer)
        self.assertEqual(team_list[1], older)

    def test_no_members(self):
        team = TeamFactory()
        self.assertEqual(team.members.count(), 0)
