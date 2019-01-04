from google.cloud import datastore
import typing

from fantasyasst import *


class Statistics:
    RK = 'Rk'
    TM = 'Tm'

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
        query = self.client.query(kind=str(season),
                                  ancestor=self.client.key(self._league, team))
        if game - n_games_back < 1:
            raise ValueError('Cross season retrieval not yet implemented')
        query.add_filter(Statistics.RK, '<', game)
        query.add_filter(Statistics.RK, '>=', game - n_games_back - 1)
        query.add_filter(Statistics.TM, '=', team)

        return list(query.fetch())
