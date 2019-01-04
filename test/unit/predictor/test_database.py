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
        for league, fetcher in self.fetchers.items():
            self.assertEqual(league, fetcher.league)
            self.assertEqual(d[league], fetcher._league)

    def test_get_nba_team_statistics(self):
        team = 'CHI'
        season = 2018
        game = 82
        n = 5
        entities = self.fetchers[League.NBA].get_team_statistics(
            team, season, game, n
        )
        necessary_stats = {'3P', '3PA', 'AST', 'BLK', 'DRB', 'FG', 'FGA',
                           'FT', 'FTA', 'ORB', 'Opp', 'PF', 'PTS', 'Rk',
                           'STL', 'TOV', 'TRB', 'Tm'}

        needed_games = [game - i for i in range(1, n + 2)]
        for entity in entities:
            for stat in necessary_stats:
                self.assertIn(stat, entity)
            self.assertEqual('2018', entity.key.kind)
            self.assertGreater(game, entity.key.id)
            self.assertLessEqual(game - n - 1, entity.key.id)
            self.assertEqual('NBA', entity.key.parent.kind)
            self.assertEqual(team, entity.key.parent.name)
            needed_games.remove(entity.key.id)

        self.assertFalse(needed_games)
