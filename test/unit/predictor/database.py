import unittest

from fantasyasst import *
from fantasyasst.predictor.database import Statistics


class TestStatistics(unittest.TestCase):
    def test_league_set_on_construction(self):
        str_repr = {
            League.NBA: 'NBA',
            League.NFL: 'NFL',
            League.MLB: 'MLB'
        }
        for league in League:
            stat_fetcher = Statistics(league)
            self.assertEqual(league, stat_fetcher.league)
            self.assertEqual(str_repr[league], stat_fetcher._league)
