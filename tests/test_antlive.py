import unittest
import json
import tempfile
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
import combined_m3u_collector as c


class AntLiveTests(unittest.TestCase):
    def test_actual_streams_and_deduplicate(self):
        room = dict(houseName='A vs B', nickName='BLV', houseId='123',
                    playStreamAddress='https://example.com/a.flv',
                    playStreamAddress2='https://example.com/a.m3u8',
                    playStreamAddress3='https://example.com/a.flv')
        rows = c.parse_antlive_streams({'data': {'ongoingLivestreams': [room, room]}})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['name'], 'A vs B (BLV) [FLV]')
        self.assertEqual(len(c.select_ott_compatible_channels(rows)), 2)
        self.assertEqual(len(c.split_ott_channels(rows)[0]), 1)
        self.assertTrue(all(c.ott_output_group(row) == 'AntLive' for row in rows))

    def test_no_synthetic_stream(self):
        self.assertEqual(c.parse_antlive_streams({'data': {'ongoingLivestreams': [{'houseId': '123'}]}}), [])

    def test_failure_cache_expires_without_refreshing_timestamp(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(c, 'BASE_DIR', Path(folder)):
            path = Path(folder) / 'antlive_cache.json'
            row = dict(name='Test', stream_url='https://example.com/live.flv')
            for hours, count in ((1, 1), (4, 0)):
                payload = dict(updated=(c.datetime.now(c.TZ_VN)-timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M ICT'), channels=[row])
                path.write_text(json.dumps(payload), encoding='utf-8')
                before = path.read_bytes()
                with patch.object(c, 'fetch_json_no_cache', side_effect=TimeoutError()):
                    self.assertEqual(len(c.collect_antlive()), count)
                self.assertEqual(path.read_bytes(), before)
