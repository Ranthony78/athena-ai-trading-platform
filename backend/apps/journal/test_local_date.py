"""
Regression: "today" must be the local (Asia/Kolkata) date, not the UTC date.

Between 00:00 and 05:30 IST it is still the previous day in UTC. The journal
used the UTC date, so an entry written at 02:00 on the 4th was filed under the
3rd, and "today's entries" looked for the wrong day.
"""

from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.journal.models import JournalEntry
from apps.journal.repositories.journal_repository import JournalEntryRepository
from apps.journal.services.journal_service import JournalService

User = get_user_model()

# 2026-10-03 20:30 UTC is 2026-10-04 02:00 IST.
NIGHT = datetime(2026, 10, 3, 20, 30, tzinfo=dt_timezone.utc)
LOCAL_DAY = date(2026, 10, 4)


@patch("django.utils.timezone.now", return_value=NIGHT)
class JournalLocalDateTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("jo", "jo@example.com", "pw-Jo-123456")

    def test_a_new_entry_without_a_date_is_filed_under_the_local_day(self, _now):
        entry = JournalService.create_entry(self.user, {"title": "After midnight"})

        self.assertEqual(entry.date, LOCAL_DAY)

    def test_todays_entries_are_found_by_the_local_day(self, _now):
        entry = JournalEntry.objects.create(
            user=self.user, date=LOCAL_DAY, title="Written at 02:00 IST"
        )

        found = list(JournalEntryRepository.get_today(self.user))

        self.assertEqual([e.pk for e in found], [entry.pk])

    def test_yesterdays_entry_is_not_todays(self, _now):
        JournalEntry.objects.create(
            user=self.user, date=date(2026, 10, 3), title="Yesterday"
        )

        self.assertEqual(list(JournalEntryRepository.get_today(self.user)), [])
