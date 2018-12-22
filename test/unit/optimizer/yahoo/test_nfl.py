import unittest
import json
from unittest.mock import mock_open, patch

from fantasyasst.constants import *
from fantasyasst.optimizer.yahoo.nfl import NflDfsOptimizer


class TestNflDfsOptimizer(unittest.TestCase):
    def setUp(self):
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.return_value = True
            with patch('builtins.open',
                       mock_open(read_data='Id,First Name,Last Name,Position,'
                                           'Team,Opponent,Game,Time,Salary,'
                                           'FPPG,Injury Status,Starting\n'
                                           'nfl.p.27540,Odell,Beckham Jr.,WR,'
                                           'NYG,IND,NYG@IND,1:00PM EST,26,36.0,'
                                           'D,No\n'
                                           'nfl.p.30972,Saquon,Barkley,RB,NYG,'
                                           'IND,NYG@IND,1:00PM EST,36,21.6,\" '
                                           '\",No\n'
                                           'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
                                           'NYG@IND,1:00PM EST,25,15.0,'
                                           '\" \",No')):
                ignore_conditions = [('Injury Status', 'D')]

                self.optimizer = NflDfsOptimizer.load_instance_from_csv(
                    'test.csv', {'QB': 1, FLEX_POSITION: 1}, ignore_conditions,
                    200, {'RB', 'WR'})

    def test_load_instance_from_csv(self):
        result = self.optimizer.players
        correct = {
            "nfl.p.30972": {
                "First Name": "Saquon",
                "Last Name": "Barkley",
                "player_position": "RB",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                "player_salary": 36,
                "player_points_projection": 21.6,
                "Injury Status": " ",
                "Starting": "No"
            },
            "nfl.p.6760": {
                "First Name": "Eli",
                "Last Name": "Manning",
                "player_position": "QB",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                "player_salary": 25,
                "player_points_projection": 15.0,
                "Injury Status": " ",
                "Starting": "No"
            }
        }
        self.assertDictEqual(correct, result)

    def test_generate_lineup(self):
        result = self.optimizer.generate_lineup()
        correct = {
            "DEF": [],
            "QB": [
                {
                    "Game Time": "1:00PM EST",
                    "Injury Status": " ",
                    "Name": "Eli Manning",
                    "Opponent": "IND",
                    "Projected Points": 15.0,
                    "Salary": 25
                }
            ],
            "RB": [
                {
                    "Game Time": "1:00PM EST",
                    "Injury Status": " ",
                    "Name": "Saquon Barkley",
                    "Opponent": "IND",
                    "Projected Points": 21.6,
                    "Salary": 36
                }
            ],
            "TE": [],
            "WR": []
        }
        self.assertDictEqual(correct, result)


if __name__ == '__main__':
    unittest.main()
