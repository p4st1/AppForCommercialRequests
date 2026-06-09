import unittest

from app.ui.info_dialogs_mixin import build_about_text


class InfoDialogsMixinTests(unittest.TestCase):
    def test_build_about_text_uses_current_version(self):
        text = build_about_text("3.1.12")

        self.assertIn("Версия 3.1.12", text)
        self.assertNotIn("Версия 1.0.5", text)

    def test_build_about_text_escapes_version(self):
        text = build_about_text("3.1.12<script>")

        self.assertIn("Версия 3.1.12&lt;script&gt;", text)


if __name__ == "__main__":
    unittest.main()
