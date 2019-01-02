import numpy as np
import unittest
from unittest.mock import mock_open, patch

from fantasyasst.loader.base import PlayerLoader
from fantasyasst.player import Player


class TestPlayerLoader(unittest.TestCase):
    @patch.multiple(PlayerLoader, __abstractmethods__=set())
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
                                           '\" \",No')):
                ignore_conditions = [(Player.INJURY_STATUS, 'O'),
                                     (Player.INJURY_STATUS, 'IR'),
                                     (Player.INJURY_STATUS, 'D')]

                def make_name(row):
                    return row['First Name'] + ' ' + row['Last Name']

                def make_name_backwards(row):
                    return row['Last Name'] + ' ' + row['First Name']

                apply_functions = [(Player.NAME, make_name),
                                   (Player.NAME[::-1],
                                    make_name_backwards)]

                column_renames = {
                    'Position': Player.POSITION,
                    'FPPG': Player.POINTS_PROJECTION,
                    'Salary': Player.SALARY,
                    'Injury Status': Player.INJURY_STATUS
                }

                player_loader = PlayerLoader(
                    PlayerLoader.import_csv('test.csv',
                                            'Id',
                                            {
                                                'FPPG': np.float,
                                                'Salary': np.int
                                            }, column_renames,
                                            ignore_conditions,
                                            apply_functions)
                )

        correct = {
            "nfl.p.27540": {
                "First Name": "Odell",
                "Last Name": "Beckham Jr.",
                Player.POSITION: "WR",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                Player.SALARY: 26,
                Player.POINTS_PROJECTION: 16.0,
                Player.INJURY_STATUS: "Q",
                "Starting": "No",
                Player.NAME: "Odell Beckham Jr.",
                Player.NAME[::-1]: "Beckham Jr. Odell"
            },
            "nfl.p.30972": {
                "First Name": "Saquon",
                "Last Name": "Barkley",
                Player.POSITION: "RB",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                Player.SALARY: 36,
                Player.POINTS_PROJECTION: 21.6,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: "Saquon Barkley",
                Player.NAME[::-1]: "Barkley Saquon"
            },
            "nfl.p.6760": {
                "First Name": "Eli",
                "Last Name": "Manning",
                Player.POSITION: "QB",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                Player.SALARY: 25,
                Player.POINTS_PROJECTION: 15.0,
                Player.INJURY_STATUS: " ",
                "Starting": "No",
                Player.NAME: "Eli Manning",
                Player.NAME[::-1]: "Manning Eli"
            }
        }
        self.assertDictEqual(correct, player_loader.get_player_dict())

    def test_import_csv_from_not_csv(self):
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
                                           '\" \",No')):
                self.assertRaises(ValueError,
                                  PlayerLoader.import_csv, 'testcsv', 'Id',
                                  {'FPPG': np.float, 'Salary': np.int}, None,
                                  None, None)

    def test_import_csv_from_nonexistent_file(self):
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.return_value = False
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
                                           '\" \",No')):
                self.assertRaises(RuntimeError,
                                  PlayerLoader.import_csv, 'test.csv', 'Id',
                                  {'FPPG': np.float, 'Salary': np.int}, None,
                                  None, None)
