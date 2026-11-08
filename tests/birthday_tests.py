import unittest
from zoneinfo import ZoneInfo

from cogs.autocalendar import DEFAULT_TIMEZONE, get_next_date, get_timezone, is_valid_timezone


class BirthdayTimezoneTests(unittest.TestCase):
    def test_default_timezone(self):
        self.assertEqual(DEFAULT_TIMEZONE, 'GMT')
        self.assertEqual(get_timezone().key, 'GMT')

    def test_valid_timezone(self):
        self.assertTrue(is_valid_timezone('Europe/Berlin'))
        self.assertEqual(get_timezone('Europe/Berlin'), ZoneInfo('Europe/Berlin'))

    def test_invalid_timezone_falls_back_to_gmt(self):
        self.assertFalse(is_valid_timezone('Not/A_Timezone'))
        self.assertFalse(is_valid_timezone('/etc/passwd'))
        self.assertEqual(get_timezone('Not/A_Timezone').key, DEFAULT_TIMEZONE)

    def test_next_date_is_timezone_aware(self):
        birthday = get_next_date(1, 1, 'America/New_York')
        self.assertEqual(birthday.tzinfo, ZoneInfo('America/New_York'))


if __name__ == '__main__':
    unittest.main()
