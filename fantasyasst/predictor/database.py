from google.cloud import datastore

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
            '../.api_credentials/gcloud-datastore.json'
        )

    @property
    def _league(self):
        return self.league.value

    def get_team_statistics(self, team, season, game, n_games_back, weight):
        query = self.client.query(kind=str(season),
                                  ancestor=self.client.key(self._league, team))
        if game - n_games_back < 1:
            raise ValueError('Cross season retrieval not yet implemented')
        query.add_filter(Statistics.RK, '<', game)
        query.add_filter(Statistics.RK, '>=', game - n_games_back)
        query.add_filter(Statistics.TM, '=', team)

        return list(query.fetch())
