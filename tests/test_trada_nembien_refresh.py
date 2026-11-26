import unittest
from unittest.mock import patch

import refresh_trada_nembien as refresh


class RefreshTests(unittest.TestCase):
    def test_only_two_sources_are_collected_then_merged(self):
        c = refresh.collector
        with patch.object(c, 'load_source_cache', return_value=[]) as cache, \
             patch.object(c, 'collect_tradatv', return_value=[{'source': 'TraDaTV'}]) as trada, \
             patch.object(c, 'collect_nembientv', return_value=[{'source': 'NemBienTV'}]) as nembien, \
             patch.object(c, 'collect_antlive', return_value=[]) as ant, \
             patch.object(c, 'merge_slow_source_playlists') as merge:
            refresh.main()
        trada.assert_called_once_with()
        nembien.assert_called_once_with()
        ant.assert_called_once_with()
        self.assertEqual(cache.call_count, 3)
        merge.assert_called_once_with([{'source': 'TraDaTV'}, {'source': 'NemBienTV'}], [])


if __name__ == '__main__':
    unittest.main()
