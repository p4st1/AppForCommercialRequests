import unittest

from config import Config
from tools import DatabaseTools as Tool


class ConfigMergeTests(unittest.TestCase):
    def test_payment_templates_default_when_key_missing(self):
        merged = Tool.merge_config_with_defaults({"config": {}, "settings": {}})
        self.assertEqual(
            merged["config"]["paymentTemplates"],
            Config.DEFAULT_PAYMENT_TEMPLATES,
        )

    def test_payment_templates_trimmed_and_deduplicated(self):
        merged = Tool.merge_config_with_defaults(
            {
                "config": {
                    "paymentTemplates": [
                        "  На дату оплаты  ",
                        "",
                        "На дату оплаты",
                        "Предоплата 50%",
                    ]
                },
                "settings": {},
            }
        )
        self.assertEqual(
            merged["config"]["paymentTemplates"],
            ["На дату оплаты", "Предоплата 50%"],
        )

    def test_payment_templates_allows_empty_list(self):
        merged = Tool.merge_config_with_defaults(
            {"config": {"paymentTemplates": []}, "settings": {}}
        )
        self.assertEqual(merged["config"]["paymentTemplates"], [])

    def test_payment_templates_supports_legacy_string(self):
        merged = Tool.merge_config_with_defaults(
            {"config": {"paymentTemplates": "После поставки"}, "settings": {}}
        )
        self.assertEqual(merged["config"]["paymentTemplates"], ["После поставки"])

    def test_auto_trade_settings_defaults_applied(self):
        merged = Tool.merge_config_with_defaults({"config": {}, "settings": {}})
        self.assertFalse(merged["settings"]["skip_auto_trade_warning"])
        self.assertFalse(merged["settings"]["use_auto_trade_timer"])
        self.assertEqual(merged["settings"]["auto_trade_timer_minutes"], 30)

    def test_auto_trade_timer_minutes_keeps_integer_value(self):
        merged = Tool.merge_config_with_defaults(
            {"config": {}, "settings": {"auto_trade_timer_minutes": "45"}}
        )
        self.assertEqual(merged["settings"]["auto_trade_timer_minutes"], 45)

    def test_auto_trade_timer_minutes_falls_back_on_invalid_value(self):
        merged = Tool.merge_config_with_defaults(
            {"config": {}, "settings": {"auto_trade_timer_minutes": "bad"}}
        )
        self.assertEqual(
            merged["settings"]["auto_trade_timer_minutes"],
            Config.DEFAULT_SETTINGS["auto_trade_timer_minutes"],
        )


if __name__ == "__main__":
    unittest.main()
