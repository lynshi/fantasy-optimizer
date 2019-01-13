from sklearn import linear_model

from fantasyasst import *
from fantasyasst.predictor.database import Statistics


class AbilityApproximator:
    def __init__(self, league, season, game, n_games_back):
        """
        Construct object to approximate innate offensive and defensive
        capabilities of teams and players.

        :param league: enum of League defining the league for which
            abilities should be approximated
        :param season: season of current game
        :param game: game number of current game
        :param n_games_back: number of previous games to get data for
        """
        self.model = linear_model.LinearRegression()
        self.league = league
        self.database = Statistics(league)
        self.season = season
        self.game = game
        self.n_games_back = n_games_back

        self._approximate_teams()

    def _approximate_teams(self):
        """
        Approximate innative offensive and defensive capabilities of teams in
        recent games.

        :return: None
        """
        teams = LEAGUE_TEAMS[self.league]

        matrix = [[0 for i in range(len(teams))] for j in range(len(teams))]
        for team_idx, team in enumerate(teams):
            entities = self.database.get_team_statistics(team, self.season,
                                                         self.game,
                                                         self.n_games_back)
            for game_idx, entity in enumerate(entities):
                coefficient = 2 ** (-game_idx)
                opponent = entity['Opp']
                matrix[team_idx][teams.index(opponent)] = coefficient
