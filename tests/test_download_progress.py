import gzip
import unittest
from unittest.mock import Mock, patch

from friman.utils import helpers


class DownloadProgressTests(unittest.TestCase):
    def request(self, chunks, response_headers=None, request_headers=None):
        response = Mock()
        response.headers = response_headers or {}
        response.read.side_effect = chunks
        with patch.object(helpers, "build_opener") as factory:
            factory.return_value.open.return_value.__enter__.return_value = response
            result = helpers.make_request("pypi.org", "/pypi/frida/json", request_headers or {})
            sent_request = factory.return_value.open.call_args.args[0]
        return result, response, sent_request

    def test_requests_gzip_without_changing_caller_headers(self):
        headers = {"User-Agent": "fixture"}
        _, _, request = self.request([b"{}", b""], request_headers=headers)
        self.assertEqual(request.get_header("Accept-encoding"), "gzip")
        self.assertEqual(headers, {"User-Agent": "fixture"})

    def test_decompresses_gzip_json(self):
        data = b'{"releases": {"17.17.0": []}}'
        result, _, _ = self.request([gzip.compress(data), b""], {"Content-Encoding": "gzip"})
        self.assertEqual(result, data)

    def test_plain_binary_is_unchanged(self):
        data = b"\xfd7zXZ\x00fixture"
        result, _, _ = self.request([data, b""], {"Content-Type": "application/octet-stream"})
        self.assertEqual(result, data)

    def test_response_is_read_in_bounded_chunks(self):
        result, response, _ = self.request([b"a" * 65536, b"b", b""])
        self.assertEqual(result, b"a" * 65536 + b"b")
        self.assertEqual(response.read.call_count, 3)
        for call in response.read.call_args_list:
            self.assertEqual(call.args, (65536,))

    def test_transfer_progress_is_visible(self):
        with patch.object(helpers.frimanlog, "info") as log:
            result, _, _ = self.request([b"a" * 65536, b""], {"Content-Length": "65536"})
        messages = [str(call.args[0]) for call in log.call_args_list]
        self.assertTrue(any("Downloading" in message and "pypi.org" in message for message in messages))
        self.assertTrue(any("Downloaded" in message and "65,536" in message for message in messages))

    def test_unknown_content_length_works(self):
        result, _, _ = self.request([b"{}", b""])
        self.assertEqual(result, b"{}")

    def test_invalid_gzip_is_not_returned_as_valid_data(self):
        with self.assertRaises(gzip.BadGzipFile):
            self.request([b"invalid gzip", b""], {"Content-Encoding": "gzip"})

    def test_respects_explicit_identity_encoding(self):
        _, _, request = self.request([b"{}", b""], request_headers={"Accept-Encoding": "identity"})
        self.assertEqual(request.get_header("Accept-encoding"), "identity")


if __name__ == "__main__":
    unittest.main()
