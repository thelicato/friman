"""Regression tests for bounded, proxy-aware metadata downloads."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

from typer.testing import CliRunner
from friman.main import app
from friman.utils import definitions, exceptions, helpers


class NetworkRequestTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def opener(self, response=None, error=None):
        # create=True lets the old implementation run and fail the regression
        # assertion rather than fail importing a newly introduced symbol.
        factory = self.stack.enter_context(patch.object(helpers, "build_opener", create=True))
        opener = factory.return_value
        if error is not None:
            opener.open.side_effect = error
        else:
            response = response or Mock()
            response.headers = {}
            response.read.side_effect = [b"fixture", b""]
            opener.open.return_value.__enter__.return_value = response
        # Never let the baseline implementation perform a real network request.
        old_http = self.stack.enter_context(patch("http.client.HTTPSConnection"))
        old_http.return_value.getresponse.return_value.status = 200
        old_http.return_value.getresponse.return_value.read.return_value = b"fixture"
        return opener

    def test_network_request_passes_finite_timeout(self):
        opener = self.opener()
        self.assertEqual(helpers.make_request("example.invalid", "/asset", {}), b"fixture")
        opener.open.assert_called_once()
        timeout = opener.open.call_args.kwargs["timeout"]
        self.assertGreater(timeout, 0)
        self.assertLessEqual(timeout, 30)

    def test_timeout_reports_host(self):
        self.opener(error=TimeoutError("read timed out"))
        with self.assertRaisesRegex(TimeoutError, "example.invalid"):
            helpers.make_request("example.invalid", "/asset", {})

    def test_wrapped_connect_timeout_reports_host(self):
        self.opener(error=URLError(TimeoutError("connect timed out")))
        with self.assertRaisesRegex(TimeoutError, "example.invalid"):
            helpers.make_request("example.invalid", "/asset", {})

    def test_response_closes_when_read_fails(self):
        opener = self.opener()
        opener.open.return_value.__enter__.return_value.read.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            helpers.make_request("example.invalid", "/asset", {})
        opener.open.return_value.__exit__.assert_called_once()

    def test_rate_limit_still_raises_project_exception(self):
        error = HTTPError("https://example.invalid/", 403, "Forbidden", {}, io.BytesIO(b"limited"))
        self.opener(error=error)
        with self.assertRaises(exceptions.RateLimitException):
            helpers.make_request("example.invalid", "/", {})
        self.assertTrue(error.closed)

    def test_http_error_closes_response(self):
        error = HTTPError("https://example.invalid/", 404, "Not Found", {}, io.BytesIO(b"missing"))
        self.opener(error=error)
        with self.assertRaisesRegex(Exception, "404"):
            helpers.make_request("example.invalid", "/", {})
        self.assertTrue(error.closed)

    def handler(self, follow=True, maximum=5):
        cls = getattr(helpers, "_RedirectHandler", None)
        self.assertIsNotNone(cls, "explicit redirect policy is missing")
        return cls(follow, maximum)

    def test_redirect_limit_is_enforced(self):
        handler = self.handler(maximum=0)
        with self.assertRaisesRegex(Exception, "Too many redirects"):
            handler.redirect_request(Request("https://example.invalid/a"), None, 302, "", {}, "https://example.invalid/b")

    def test_cross_host_redirect_drops_authorization(self):
        handler = self.handler()
        req = Request("https://example.invalid/a", headers={"Authorization": "fixture", "User-Agent": "friman"})
        redirected = handler.redirect_request(req, None, 302, "", {}, "https://asset.invalid/b?key=fixture")
        self.assertIsNone(redirected.get_header("Authorization"))
        self.assertEqual(redirected.full_url, "https://asset.invalid/b?key=fixture")

    def test_same_host_redirect_preserves_authorization(self):
        handler = self.handler()
        req = Request("https://example.invalid/a", headers={"Authorization": "fixture"})
        redirected = handler.redirect_request(req, None, 302, "", {}, "https://example.invalid/b")
        self.assertEqual(redirected.get_header("Authorization"), "fixture")

    def test_redirect_disabled(self):
        handler = self.handler(follow=False)
        self.assertIsNone(handler.redirect_request(Request("https://example.invalid/a"), None, 302, "", {}, "https://example.invalid/b"))

    def test_https_downgrade_rejected(self):
        handler = self.handler()
        with self.assertRaises(ValueError):
            handler.redirect_request(Request("https://example.invalid/a"), None, 302, "", {}, "http://example.invalid/b")


class OfflineCommandTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="friman-network-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.multiple(
            definitions, FRIMAN_FOLDER=str(self.root),
            FRIMAN_ENV_FOLDER=str(self.root / "env"),
            FRIMAN_BIN_FOLDER=str(self.root / "bin"),
            FRIMAN_CURRENT_FOLDER=str(self.root / "current"),
            FRIMAN_CONFIG_FILE=str(self.root / "config.json"),
            FRIMAN_COMPATIBILITY_MATRIX_FILE=str(self.root / "matrix.json"),
        ))
        self.download = self.stack.enter_context(patch.object(helpers, "download_compatibility_matrix", side_effect=TimeoutError("example.invalid timed out")))

    def test_local_commands_never_download_matrix(self):
        for args in ([], ["current"], ["list"], ["disable"], ["use", "17.17.0"], ["uninstall", "17.17.0"], ["install", "--help"]):
            with self.subTest(args=args):
                CliRunner().invoke(app, args)
        self.download.assert_not_called()

    def test_install_timeout_is_attempted_once_and_visible(self):
        with patch.object(helpers, "get_pypi_versions", return_value=["17.17.0"]):
            result = CliRunner().invoke(app, ["install", "17.17.0"])
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(self.download.call_count, 1)
        self.assertIn("example.invalid timed out", result.output)

    def test_cached_tags_matrix_timeout_is_visible(self):
        Path(definitions.FRIMAN_CONFIG_FILE).write_text(json.dumps({"tags": ["17.17.0"], "updated_at": "2026-09-20 00:00:00"}))
        result = CliRunner().invoke(app, ["install", "17.17.0"])
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(self.download.call_count, 1)
        self.assertIn("example.invalid timed out", result.output)

    def test_update_failure_returns_nonzero(self):
        with patch.object(helpers, "get_pypi_versions", side_effect=TimeoutError("pypi timed out")):
            result = CliRunner().invoke(app, ["update"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("pypi timed out", result.output)
        self.download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
