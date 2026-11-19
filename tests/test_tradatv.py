import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
import combined_m3u_collector as c


class TraDaTests(unittest.TestCase):
    def fixture(self):
        kickoff = datetime.now(c.TZ_VN) + timedelta(minutes=5)
        return dict(title='Home vs Away', startTime=kickoff.isoformat(), sport='volleyball',
                    home={}, status='upcoming', streams=[
                        {'url': 'https://example.com/live.m3u8', 'label': 'BLV'},
                        {'url': 'https://example.com/live.flv', 'label': 'BLV 2'},
                        {'url': 'https://example.com/live.mpd'},
                        {'url': 'https://example.com/live.m3u8'}])

    def test_all_sports_all_unique_streams_and_ott(self):
        match = self.fixture()
        rows = c.parse_tradatv_matches([match])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['sport'], 'volleyball')
        self.assertTrue(rows[0]['name'].startswith(datetime.fromisoformat(match['startTime']).strftime('%H:%M %d/%m')))
        self.assertEqual(len(c.select_ott_compatible_channels(rows)), 2)
        self.assertEqual(len(c.split_ott_channels(rows)[0]), 1)

    def test_empty_finished_and_old_events_not_fabricated(self):
        match = self.fixture()
        self.assertEqual(c.parse_tradatv_matches([dict(match, streams=[])]), [])
        self.assertEqual(c.parse_tradatv_matches([dict(match, status='finished')]), [])
        self.assertEqual(c.parse_tradatv_matches([dict(match, startTime='2020-01-01T00:00:00Z')]), [])

    def test_failure_uses_cache_but_successful_empty_does_not(self):
        with patch.object(c, 'fetch_json_no_cache', side_effect=TimeoutError), \
             patch.object(c, 'load_source_cache', return_value=[]) as cache:
            self.assertEqual(c.collect_tradatv(), [])
            cache.assert_called_once()
        with patch.object(c, 'fetch_json_no_cache', return_value=[]), \
             patch.object(c, 'save_source_cache'), patch.object(c, 'load_source_cache') as cache:
            self.assertEqual(c.collect_tradatv(), [])
            cache.assert_not_called()


if __name__ == '__main__':
    unittest.main()
