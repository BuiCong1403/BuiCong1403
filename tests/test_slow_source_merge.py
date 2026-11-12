import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import combined_m3u_collector as c


class SlowMergeTests(unittest.TestCase):
    def test_merge_is_local_preserves_other_sources_and_replaces_old_flv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            all_file, ott = root / 'all.m3u', root / 'ott.m3u'
            original = ('#EXTM3U\n#EXTINF:-1 group-title="VTV",VTV1\nhttps://example.com/vtv.m3u8\n'
                        '#EXTINF:-1 group-title="FLV",Old stream\nhttps://example.com/old.flv\n'
                        '#EXTINF:-1 group-title="FLV",Other source\nhttps://example.com/other.flv\n')
            for path in (all_file, ott):
                path.write_text(original, encoding='utf-8')
            fresh = [{'source': 'XoiLacZ', 'group': 'Xoi Lac Z TV', 'name': 'New match',
                      'stream_url': 'https://example.com/new.flv'}]
            previous = [dict(fresh[0], stream_url='https://example.com/old.flv')]
            with patch.object(c, 'ALL_M3U', all_file), patch.object(c, 'OTT_M3U', ott), \
                 patch.object(c, 'request_get', side_effect=AssertionError('No network')), \
                 patch.object(c, 'fetch_text', side_effect=AssertionError('No network')):
                c.merge_slow_source_playlists(fresh, previous)
                c.merge_slow_source_playlists(fresh, previous)
            for path in (all_file, ott):
                text = path.read_text(encoding='utf-8')
                self.assertIn('https://example.com/vtv.m3u8', text)
                self.assertIn('https://example.com/other.flv', text)
                self.assertNotIn('https://example.com/old.flv', text)
                self.assertEqual(text.count('https://example.com/new.flv'), 1 if path == ott else 0)

    def test_empty_snapshot_does_not_touch_combined_files(self):
        with patch.object(c, 'write_m3u_text_blocks') as write:
            c.merge_slow_source_playlists([])
            write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
