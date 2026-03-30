import unittest
from importlib.util import find_spec

from app.services.web_parser_service import WebPageParser


class WebPageParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = WebPageParser()

    def test_compact_text(self):
        self.assertEqual(self.parser.compact_text("  a \n  b\tc  "), "a b c")

    @unittest.skipUnless(find_spec("lxml") is not None, "lxml is not installed in this test environment")
    def test_extract_payload_basic_html(self):
        html_text = """
        <html>
          <head><title>  Test Page  </title></head>
          <body>
            <h1> Header </h1>
            <form method="post" action="/submit">
              <input name="login" type="text" />
              <input name="password" type="password" />
            </form>
            <table>
              <tr><th>A</th><th>B</th></tr>
              <tr><td>1</td><td>2</td></tr>
            </table>
            <a href="/link"> Link </a>
            <iframe src="/frame"></iframe>
          </body>
        </html>
        """

        payload = self.parser.extract_payload(html_text, current_url="https://example.com/page")

        self.assertEqual(payload["url"], "https://example.com/page")
        self.assertEqual(payload["title"], "Test Page")
        self.assertEqual(payload["forms_count"], 1)
        self.assertEqual(payload["tables_count"], 1)
        self.assertEqual(payload["links_count"], 1)
        self.assertEqual(payload["frames_count"], 1)
        self.assertEqual(payload["forms"][0]["method"], "POST")
        self.assertEqual(payload["forms"][0]["action"], "/submit")
        self.assertEqual(payload["links_preview"][0]["href"], "/link")


if __name__ == "__main__":
    unittest.main()
