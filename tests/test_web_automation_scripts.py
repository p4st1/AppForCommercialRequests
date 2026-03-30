import unittest

from app.services.web_automation_scripts import WebAutomationScripts


class WebAutomationScriptsTests(unittest.TestCase):
    def test_build_web_auth_script_embeds_credentials(self):
        script = WebAutomationScripts.build_web_auth_script('user"1', "p@ss")

        self.assertIn('const loginValue = "user\\"1";', script)
        self.assertIn('const passwordValue = "p@ss";', script)
        self.assertNotIn("__LOGIN__", script)
        self.assertNotIn("__PASSWORD__", script)

    def test_build_bid_request_search_script_embeds_request_number(self):
        script = WebAutomationScripts.build_bid_request_search_script("123-ABC")

        self.assertIn('const requestNumber = "123-ABC";', script)
        self.assertNotIn("__REQUEST_NUMBER__", script)

    def test_build_bid_submission_navigation_script_contains_target_page(self):
        script = WebAutomationScripts.build_bid_submission_navigation_script()

        self.assertIn("purchases.trades.filters.BID_SUBMISSION", script)
        self.assertIn("targetPath = '/trades'", script)


if __name__ == "__main__":
    unittest.main()
