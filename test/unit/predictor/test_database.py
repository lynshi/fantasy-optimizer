import unittest

from fantasyasst import *
from fantasyasst.predictor.database import Statistics


class TestStatistics(unittest.TestCase):
    def setUp(self):
        self.fetchers = {}
        for league in League:
            if league != League.NBA:
                continue
            self.fetchers[league] = Statistics(league)

    def test_league_set_on_construction(self):
        d = {
            League.NBA: 'NBA',
            League.NFL: 'NFL',
            League.MLB: 'MLB'
        }
        for league in League:
            if league != League.NBA:
                continue
            self.assertEqual(league, self.fetchers[league].league)
            self.assertEqual(d[league], self.fetchers[league]._league)

    def test_get_team_statistics(self):
        stats = self.fetchers[League.NBA].get_team_statistics(
            'CHI', 2018, 82, 5, 1
        )
        print(stats)
