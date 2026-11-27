import unittest
import combined_m3u_collector as c


class VtvRoleTests(unittest.TestCase):
    def test_promoted_and_backup(self):
        for number in range(1, 11):
            primary = c.assign_vtv_role(dict(name=f'VTV{number} HD 50-1', group='VTV'))
            self.assertEqual(primary['group'], 'VTV')
            self.assertEqual(primary['name'], f'VTV{number} HD 50-1')
            backup = c.assign_vtv_role(dict(name=f'VTV{number}', group='VTV'))
            self.assertEqual(backup['group'], 'VTV')

    def test_go_unchanged_and_on_backup(self):
        for name in ('VTVGo Event 1-1', 'VTVgo Ca Nhac-1'):
            row = dict(name=name, group='VTV', stream_url='https://example.com/master.m3u8')
            self.assertEqual(c.assign_vtv_role(dict(row)), row)
        for name in ('ON FootBall', 'ON Sports News', 'ON Sports'):
            self.assertEqual(c.assign_vtv_role(dict(name=name, group='VTV backup'))['group'], 'VTV')
