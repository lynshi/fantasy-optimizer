from google.cloud import datastore


class Statistics:
    def __init__(self, league):
        """
        Construct Statistics object, which provides an interface to a
        Google Datastore instance with player data

        :param league:
        """
        self.league = league
        self.client = datastore.Client.from_service_account_json(
            '../.api_credentials/gcloud-datastore.json'
        )

    def get_team_statistics(self, team, n_games, weight):
        pass
