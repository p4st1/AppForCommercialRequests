import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from version_check import (
    VersionMeta,
    check_release_version,
    compare_versions,
    fetch_release_version,
    load_local_version_meta,
)


class FakeUrlResponse:
    def __init__(self, payload: dict):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class VersionCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "utilities").mkdir(parents=True, exist_ok=True)

    def _resource_path(self, relative_path: str) -> str:
        return str(self.root / relative_path)

    def _write_local_version(self, payload: dict):
        target = self.root / "utilities" / "version.json"
        target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_compare_versions(self):
        self.assertEqual(compare_versions("2.0.0", "2.0.1"), -1)
        self.assertEqual(compare_versions("2.0.0", "2.0.0"), 0)
        self.assertEqual(compare_versions("2.1.0", "2.0.9"), 1)

    def test_load_local_version_meta_reads_json(self):
        self._write_local_version(
            {
                "version": "2.0.0",
                "repo": "example/repo",
                "release_branch": "release",
                "release_url": "https://example.com/releases",
            }
        )

        meta = load_local_version_meta(self._resource_path)
        self.assertEqual(meta.version, "2.0.0")
        self.assertEqual(meta.repo, "example/repo")
        self.assertEqual(meta.release_branch, "release")
        self.assertEqual(meta.release_url, "https://example.com/releases")

    def test_load_local_version_meta_defaults_to_latest_release_url(self):
        self._write_local_version(
            {
                "version": "2.0.0",
                "repo": "example/repo",
                "release_branch": "release",
            }
        )

        meta = load_local_version_meta(self._resource_path)

        self.assertEqual(meta.release_url, "https://github.com/example/repo/releases/latest")

    def test_fetch_release_version_uses_github_latest_release(self):
        meta = VersionMeta(
            version="2.0.0",
            repo="example/repo",
            release_branch="main",
            release_url="https://example.com/releases/latest",
        )

        with patch(
            "version_check.urlopen",
            return_value=FakeUrlResponse({"tag_name": "v2.0.1"}),
        ) as mocked_urlopen:
            result = fetch_release_version(meta)

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(result, "v2.0.1")
        self.assertEqual(
            request.full_url,
            "https://api.github.com/repos/example/repo/releases/latest",
        )

    def test_fetch_release_version_falls_back_to_remote_version_json(self):
        meta = VersionMeta(
            version="2.0.0",
            repo="example/repo",
            release_branch="main",
            release_url="https://example.com/releases/latest",
        )
        latest_release_error = HTTPError(
            "https://api.github.com/repos/example/repo/releases/latest",
            404,
            "Not found",
            hdrs=None,
            fp=None,
        )

        with patch(
            "version_check.urlopen",
            side_effect=[
                latest_release_error,
                FakeUrlResponse({"version": "2.0.1"}),
            ],
        ) as mocked_urlopen:
            result = fetch_release_version(meta)

        fallback_request = mocked_urlopen.call_args_list[1].args[0]
        self.assertEqual(result, "2.0.1")
        self.assertEqual(
            fallback_request.full_url,
            "https://raw.githubusercontent.com/example/repo/main/utilities/version.json",
        )

    def test_check_release_version_outdated(self):
        self._write_local_version(
            {
                "version": "2.0.0",
                "repo": "p4st1/AppForCommercialRequests",
                "release_branch": "release",
            }
        )

        with patch("version_check.fetch_release_version", return_value="2.0.1"):
            result = check_release_version(self._resource_path)

        self.assertEqual(result.status, "outdated")
        self.assertEqual(result.local_version, "2.0.0")
        self.assertEqual(result.remote_version, "2.0.1")

    def test_check_release_version_unknown_when_network_error(self):
        self._write_local_version(
            {
                "version": "2.0.0",
                "repo": "p4st1/AppForCommercialRequests",
                "release_branch": "release",
            }
        )

        with patch("version_check.fetch_release_version", side_effect=URLError("offline")):
            result = check_release_version(self._resource_path)

        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.local_version, "2.0.0")
        self.assertEqual(result.remote_version, "")
        self.assertIn("Не удалось получить версию release", result.details)

    def test_check_release_version_unknown_when_invalid_semver(self):
        self._write_local_version(
            {
                "version": "broken-version",
                "repo": "p4st1/AppForCommercialRequests",
                "release_branch": "release",
            }
        )

        with patch("version_check.fetch_release_version", return_value="2.0.1"):
            result = check_release_version(self._resource_path)

        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.remote_version, "2.0.1")
        self.assertIn("Некорректный формат версии", result.details)


if __name__ == "__main__":
    unittest.main()
