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


if __name__ == "__main__":
    unittest.main()
