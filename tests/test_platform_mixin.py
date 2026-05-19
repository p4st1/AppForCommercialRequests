import unittest

from ui_mixins.platform_mixin import PlatformMixin


class PlatformMixinSearchTests(unittest.TestCase):
    def test_short_search_text_requires_minimum_length(self):
        self.assertTrue(PlatformMixin._is_search_text_too_short("1"))
        self.assertTrue(PlatformMixin._is_search_text_too_short("12"))
        self.assertFalse(PlatformMixin._is_search_text_too_short(""))
        self.assertFalse(PlatformMixin._is_search_text_too_short("125"))

    def test_filter_trades_matches_registered_number_case_insensitive(self):
        trades = [
            {
                "id": 1,
                "title": "Запасные части",
                "registeredNumber": "125570-ТТ",
                "bidSubmissionEndDate": "2026-05-20T10:00:00",
            },
            {
                "id": 2,
                "title": "Другая заявка",
                "registeredNumber": "999999-ТТ",
                "bidSubmissionEndDate": "2026-05-20T10:00:00",
            },
        ]

        filtered = PlatformMixin._filter_trades(
            trades,
            active_only=False,
            search_text="125570-тт",
        )

        self.assertEqual([trade["id"] for trade in filtered], [1])

    def test_filter_trades_can_apply_active_only_before_search(self):
        trades = [
            {"id": 1, "title": "Насос", "registeredNumber": "125", "bidSubmissionEndDate": None},
            {
                "id": 2,
                "title": "Насос",
                "registeredNumber": "126",
                "bidSubmissionEndDate": "2026-05-20",
            },
        ]

        filtered = PlatformMixin._filter_trades(
            trades,
            active_only=True,
            search_text="насос",
        )

        self.assertEqual([trade["id"] for trade in filtered], [2])


if __name__ == "__main__":
    unittest.main()
