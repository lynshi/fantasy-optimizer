import unittest
from unittest.mock import mock_open, patch

from fantasyasst.loader.yahoo.nba import NbaLoader


class TestNflLoader(unittest.TestCase):
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
                "Position": "SF",
                "Team": "WAS",
                "Opponent": "PHO",
                "Game": "PHO@WAS",
                "Time": "7:00PM EST",
                "Salary": 24,
                "Points_Projection": 26.7,
                "Injury Status": "GTD",
                "Starting": "No",
                "Name": "Trevor Ariza"
            },
            "nba.p.4483": {
                "First Name": "Ryan",
                "Last Name": "Anderson",
                "Position": "PF",
                "Team": "PHO",
                "Opponent": "WAS",
                "Game": "PHO@WAS",
                "Time": "7:00PM EST",
                "Salary": 10,
                "Points_Projection": 9.0,
                "Injury Status": " ",
                "Starting": "No",
                "Name": "Ryan Anderson"
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
                    ('Injury Status', 'O'),
                    ('Injury Status', 'INJ'),
                    ('Injury Status', 'OFS'),
                    ('Injury Status', 'GTD')
                ]

                player_loader = NbaLoader.load_players('test.csv',
                                                       ignore_conditions)

        correct = {
            "nba.p.4483": {
                "First Name": "Ryan",
                "Last Name": "Anderson",
                "Position": "PF",
                "Team": "PHO",
                "Opponent": "WAS",
                "Game": "PHO@WAS",
                "Time": "7:00PM EST",
                "Salary": 10,
                "Points_Projection": 9.0,
                "Injury Status": " ",
                "Starting": "No",
                "Name": "Ryan Anderson"
            }
        }
        self.assertDictEqual(correct, player_loader.get_player_dict())
