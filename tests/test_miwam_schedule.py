import unittest

import combined_m3u_collector as collector


class MiwamTests(unittest.TestCase):
    def test_resolves_teams_and_preserves_all_distinct_streams(self):
        data = {"relation": {"teams": [{"id": "a", "name": "Team A"}, {"id": "b", "name": "Team B"}]},
                "matches": [{"info": {"homeTeamId": "a", "awayTeamId": "b", "matchTime": "2026-10-21T18:30:00+07:00"},
                             "livestreams": {"links": [
                                 {"commentator": "One", "url": "https://example.org/a.m3u8", "urlSecure": "https://example.org/a.m3u8?token=x", "streamUrl": "https://example.org/a.flv"},
                                 {"commentator": "Two", "urlSecure": "https://example.org/b.m3u8?token=y"}]}}]}
        channels = collector.parse_miwam_schedule(data)
        self.assertEqual(len(channels), 3)
        self.assertTrue(all(channel["source"] == "VSC9" for channel in channels))
        self.assertIn("18:30 21/10 Team A vs Team B", channels[0]["name"])
        self.assertTrue(all(not channel["referer"] for channel in channels))

    def test_bad_match_date_is_skipped(self):
        self.assertEqual(collector.parse_miwam_schedule({"matches": [{"info": {"matchTime": "invalid"}}]}), [])


if __name__ == "__main__":
    unittest.main()
