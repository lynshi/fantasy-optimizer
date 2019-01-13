from google.cloud import datastore
import json
import typing

from fantasyasst import *


class Statistics:
    RK = 'Rk'
    TM = 'Tm'
    NAME = 'Name'

    COUNTING_STATS = {
        League.NBA: {'AST', 'BLK', 'PTS', 'STL', 'TOV', 'TRB'}
    }

    def __init__(self, league):
        """
        Construct Statistics object, which provides an interface to a
        Google Datastore instance with player data

        :param league: enum of League defining the league for which
            statistics should be fetched
        :type league: League
        """
        self.league = league
        self.client = datastore.Client.from_service_account_json(
            'gcloud-datastore.json'
        )

        with open(league.value.lower() + '_players.json') as infile:
            self.player_id_dict = json.load(infile)

        self.player_name_dict = {}
        for p_id, p_dict in self.player_id_dict.items():
            if Player.TEAM not in p_dict:  # player not currently on a team
                continue
            self.player_name_dict[(p_dict[Player.NAME],
                                   p_dict[Player.TEAM])] = p_id

    @property
    def _league(self):
        return self.league.value

    def get_team_statistics(self, team, season, game, n_games_back) \
            -> typing.List[datastore.Entity]:
        """
        Gather team statistics for the last 'n_games_back' games

        :param team: name of team to get statistics for
        :param season: season of current game
        :param game: game number of current game
        :param n_games_back: number of previous games to get data for
        :return: list of Entities
        """
        if game - n_games_back < 1:
            raise ValueError('Cross season retrieval not yet implemented')

        query = self.client.query(kind=str(season),
                                  ancestor=self.client.key(self._league, team))
        query.add_filter(Statistics.RK, '<', game)
        query.add_filter(Statistics.RK, '>=', game - n_games_back - 1)
        query.add_filter(Statistics.TM, '=', team)

        return list(query.fetch())

    def get_player_statistics(self, name, team, season, game, n_games_back) \
            -> typing.List[datastore.Entity]:
        """
        Gather player statistics for the last 'n_games_back' games

        :param name: name of player to get statistics for
        :param team: name of team to get statistics for
        :param season: season of current game
        :param game: game number of current game
        :param n_games_back: number of previous games to get data for
        :return: list of Entities
        """
        if game - n_games_back < 1:
            raise ValueError('Cross season retrieval not yet implemented')

        query = self.client.query(kind=str(season),
                                  ancestor=self.client.key(self._league,
                                                           self.player_name_dict
                                                           [(name, team)]))
        query.add_filter(Statistics.RK, '<', game)
        query.add_filter(Statistics.RK, '>=', game - n_games_back - 1)
        query.add_filter(Statistics.TM, '=', team)
        query.add_filter(Statistics.NAME, '=', name)

        return list(query.fetch())
