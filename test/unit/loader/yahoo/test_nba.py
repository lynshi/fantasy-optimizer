import unittest
from unittest.mock import mock_open, patch

from fantasyasst.loader.yahoo.nba import NbaLoader
from fantasyasst.player import Player


class TestNbaLoader(unittest.TestCase):
    def test_import_and_df_to_dict_default(self):
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.return_value = True
            with patch('builtins.open',
                       mock_open(read_data='Id,First Name,Last Name,Position,'
                                           'Team,Opponent,Game,Time,Salary,'
                                           'FPPG,Injury Status,Starting\n'
                                           'nba.p.3407,Jamal,Crawford,SG,PHO,'
                                           'WAS,PHO@WAS,7:00PM EST,10,13.4,'
                                           'INJ,No\n'
                                           'nba.p.3860,Trevor,Ariza,SF,WAS,PHO,'
                                           'PHO@WAS,7:00PM EST,24,26.7,'
                                           'GTD,No\n'
                                           'nba.p.4483,Ryan,Anderson,PF,PHO,'
                                           'WAS,PHO@WAS,7:00PM EST,10,9.0,'
                                           '\" \",No'
                                 )):

                player_loader = NbaLoader.load_players('test.csv')

        correct = {
            "nba.p.3860": {
                "First Name": "Trevor",
                "Last Name": "Ariza",
                Player.POSITION: "SF",
                Player.TEAM: "WAS",
                Player.OPPONENT: "PHO",
                "Game": "PHO@WAS",
                Player.GAME_TIME: "7:00PM EST",
                Player.SALARY: 24,
                Player.POINTS_PROJECTION: 26.7,
                Player.INJURY_STATUS: "GTD",
                "Starting": "No",
                Player.NAME: "Trevor Ariza"
            },
            "nba.p.4483": {
                "First Name": "Ryan",
                "Last Name": "Anderson",
                Player.POSITION: "PF",
                Player.TEAM: "PHO",
                Player.OPPONENT: "WAS",
                "Game": "PHO@WAS",
                Player.GAME_TIME: "7:00PM EST",
                Player.SALARY: 10,
                Player.POINTS_PROJECTION: 9.0,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: "Ryan Anderson"
            }
        }
        self.assertDictEqual(correct, player_loader.get_player_dict())

    def test_import_and_df_to_dict(self):
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.return_value = True
            with patch('builtins.open',
                       mock_open(read_data='Id,First Name,Last Name,Position,'
                                           'Team,Opponent,Game,Time,Salary,'
                                           'FPPG,Injury Status,Starting\n'
                                           'nba.p.3407,Jamal,Crawford,SG,PHO,'
                                           'WAS,PHO@WAS,7:00PM EST,10,13.4,'
                                           'INJ,No\n'
                                           'nba.p.3860,Trevor,Ariza,SF,WAS,PHO,'
                                           'PHO@WAS,7:00PM EST,24,26.7,'
                                           'GTD,No\n'
                                           'nba.p.4483,Ryan,Anderson,PF,PHO,'
                                           'WAS,PHO@WAS,7:00PM EST,10,9.0,'
                                           '\" \",No'
                                 )):
                ignore_conditions = [
                    (Player.INJURY_STATUS, 'O'),
                    (Player.INJURY_STATUS, 'INJ'),
                    (Player.INJURY_STATUS, 'OFS'),
                    (Player.INJURY_STATUS, 'GTD')
                ]

                player_loader = NbaLoader.load_players('test.csv',
                                                       ignore_conditions)

        correct = {
            "nba.p.4483": {
                "First Name": "Ryan",
                "Last Name": "Anderson",
                Player.POSITION: "PF",
                Player.TEAM: "PHO",
                Player.OPPONENT: "WAS",
                "Game": "PHO@WAS",
                Player.GAME_TIME: "7:00PM EST",
                Player.SALARY: 10,
                Player.POINTS_PROJECTION: 9.0,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: "Ryan Anderson"
            }
        }
        self.assertDictEqual(correct, player_loader.get_player_dict())
