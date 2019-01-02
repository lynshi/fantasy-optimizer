from google.cloud import datastore

from fantasyasst import *


class Statistics:
    def __init__(self, league):
        """
        Construct Statistics object, which provides an interface to a
        Google Datastore instance with player data

        :param league: member of enum League defining the league for which
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

    def get_team_statistics(self, team, n_games, weight):
        pass
