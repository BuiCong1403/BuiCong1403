import unittest
from unittest.mock import Mock, patch

import combined_m3u_collector as collector


class HttpRecoveryTests(unittest.TestCase):
    def test_das_retries_plain_url_after_bad_response(self):
        blocked = Mock(status_code=403)
        blocked.raise_for_status.side_effect = RuntimeError("HTTP 403")
        good = Mock(text="<html>" + "video page " * 30)
        with patch.object(collector, "request_get", side_effect=[blocked, good]) as get, patch.object(collector.time, "sleep"):
            self.assertIn("video page", collector.dasfootball_fetch_text("https://dasfootball.com/"))
        self.assertIsNone(get.call_args.kwargs["params"])

    def test_vsc_redirect_preserves_post(self):
        redirect = Mock(status_code=301, headers={"Location": "https://www.vsc9.top/api/proxy/data/lives/matches"})
        good = Mock(status_code=200)
        good.json.return_value = {"result": {"data": [], "totalPages": 1}}
        with patch.object(collector, "collect_vsc9_miwam", return_value=[]), patch.object(collector.requests, "post", side_effect=[redirect, good, good]) as post:
            self.assertEqual(collector.collect_vsc9_api(), [])
        self.assertEqual(post.call_args_list[1].args[0], redirect.headers["Location"])
        for call in post.call_args_list:
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertIn("json", call.kwargs)


if __name__ == "__main__":
    unittest.main()
