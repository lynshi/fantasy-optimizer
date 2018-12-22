import unittest
from unittest.mock import mock_open, patch

from fantasyasst import *
from fantasyasst.loader.yahoo.nfl import NflLoader


class TestNflLoader(unittest.TestCase):
    def test_import_and_df_to_dict_default(self):
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.return_value = True
            with patch('builtins.open',
                       mock_open(read_data='Id,First Name,Last Name,Position,'
                                           'Team,Opponent,Game,Time,Salary,'
                                           'FPPG,Injury Status,Starting\n'
                                           'nfl.p.27540,Odell,Beckham Jr.,WR,'
                                           'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
                                           'Q,No\n'
                                           'nfl.p.30972,Saquon,Barkley,RB,NYG,'
                                           'IND,NYG@IND,1:00PM EST,36,21.6,\" '
                                           '\",No\n'
                                           'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
                                           'NYG@IND,1:00PM EST,25,15.0,'
                                           '\" \",No\n'
                                           'nfl.p.6767,Kyle,Lauletta,QB,NYG,'
                                           'IND,NYG@IND,1:00PM EST,25,15.0,'
                                           'O,No'
                                 )):

                player_loader = NflLoader.load_players('test.csv')

        correct = {
            "nfl.p.27540": {
                "First Name": "Odell",
                "Last Name": "Beckham Jr.",
                Player.POSITION: "WR",
                Player.TEAM: "NYG",
                Player.OPPONENT: "IND",
                "Game": "NYG@IND",
                Player.GAME_TIME: "1:00PM EST",
                Player.SALARY: 26,
                Player.POINTS_PROJECTION: 16.0,
                Player.INJURY_STATUS: "Q",
                "Starting": "No",
                Player.NAME: 'Odell Beckham Jr.'
            },
            "nfl.p.30972": {
                "First Name": "Saquon",
                "Last Name": "Barkley",
                Player.POSITION: "RB",
                Player.TEAM: "NYG",
                Player.OPPONENT: "IND",
                "Game": "NYG@IND",
                Player.GAME_TIME: "1:00PM EST",
                Player.SALARY: 36,
                Player.POINTS_PROJECTION: 21.6,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: 'Saquon Barkley'
            },
            "nfl.p.6760": {
                "First Name": "Eli",
                "Last Name": "Manning",
                Player.POSITION: "QB",
                Player.TEAM: "NYG",
                Player.OPPONENT: "IND",
                "Game": "NYG@IND",
                Player.GAME_TIME: "1:00PM EST",
                Player.SALARY: 25,
                Player.POINTS_PROJECTION: 15.0,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: 'Eli Manning'
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
                                           'nfl.p.27540,Odell,Beckham Jr.,WR,'
                                           'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
                                           'Q,No\n'
                                           'nfl.p.30972,Saquon,Barkley,RB,NYG,'
                                           'IND,NYG@IND,1:00PM EST,36,21.6,\" '
                                           '\",No\n'
                                           'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
                                           'NYG@IND,1:00PM EST,25,15.0,'
                                           '\" \",No\n'
                                           'nfl.p.6767,Kyle,Lauletta,QB,NYG,'
                                           'IND,NYG@IND,1:00PM EST,25,15.0,'
                                           'O,No'
                                 )):
                ignore_conditions = [(Player.INJURY_STATUS, 'O'),
                                     (Player.INJURY_STATUS, 'IR'),
                                     (Player.INJURY_STATUS, 'D'),
                                     (Player.INJURY_STATUS, 'Q')]

                player_loader = NflLoader.load_players('test.csv',
                                                       ignore_conditions)

        correct = {
            "nfl.p.30972": {
                "First Name": "Saquon",
                "Last Name": "Barkley",
                Player.POSITION: "RB",
                Player.TEAM: "NYG",
                Player.OPPONENT: "IND",
                "Game": "NYG@IND",
                Player.GAME_TIME: "1:00PM EST",
                Player.SALARY: 36,
                Player.POINTS_PROJECTION: 21.6,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: 'Saquon Barkley'
            },
            "nfl.p.6760": {
                "First Name": "Eli",
                "Last Name": "Manning",
                Player.POSITION: "QB",
                Player.TEAM: "NYG",
                Player.OPPONENT: "IND",
                "Game": "NYG@IND",
                Player.GAME_TIME: "1:00PM EST",
                Player.SALARY: 25,
                Player.POINTS_PROJECTION: 15.0,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: 'Eli Manning'
            }
        }
        self.assertDictEqual(correct, player_loader.get_player_dict())
