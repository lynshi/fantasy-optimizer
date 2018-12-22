import unittest
from unittest.mock import mock_open, patch


class TestPlayerLoader(unittest.TestCase):
    # def test_import_csv(self):
    #     with patch('os.path.isfile') as mock_isfile:
    #         mock_isfile.return_value = True
    #         with patch('builtins.open',
    #                    mock_open(read_data='Id,First Name,Last Name,Position,'
    #                                        'Team,Opponent,Game,Time,Salary,'
    #                                        'FPPG,Injury Status,Starting\n'
    #                                        'nfl.p.27540,Odell,Beckham Jr.,WR,'
    #                                        'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
    #                                        'Q,No\n'
    #                                        'nfl.p.30972,Saquon,Barkley,RB,NYG,'
    #                                        'IND,NYG@IND,1:00PM EST,36,21.6,\" '
    #                                        '\",No\n'
    #                                        'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
    #                                        'NYG@IND,1:00PM EST,25,15.0,'
    #                                        '\" \",No')):
    #             ignore_conditions = [('Injury Status', 'O'),
    #                                  ('Injury Status', 'IR'),
    #                                  ('Injury Status', 'D')]
    #
    #             def make_name(row):
    #                 return row['First Name'] + ' ' + row['Last Name']
    #
    #             def make_name_backwards(row):
    #                 return row['Last Name'] + ' ' + row['First Name']
    #
    #             apply_functions = [(PLAYER_NAME, make_name),
    #                                (PLAYER_NAME[::-1], make_name_backwards)]
    #
    #             column_renames = {
    #                 'Position': PLAYER_POSITION,
    #                 'FPPG': PLAYER_POINTS_PROJECTION,
    #                 'Salary': PLAYER_SALARY
    #             }
    #
    #             result = DfsOptimizer.import_csv('test.csv',
    #                                              'Id',
    #                                              {
    #                                                  'FPPG': np.float,
    #                                                  'Salary': np.int
    #                                              }, column_renames,
    #                                              ignore_conditions,
    #                                              apply_functions)
    #
    #     correct = {
    #         "nfl.p.27540": {
    #             "First Name": "Odell",
    #             "Last Name": "Beckham Jr.",
    #             PLAYER_POSITION: "WR",
    #             "Team": "NYG",
    #             "Opponent": "IND",
    #             "Game": "NYG@IND",
    #             "Time": "1:00PM EST",
    #             PLAYER_SALARY: 26,
    #             PLAYER_POINTS_PROJECTION: 16.0,
    #             "Injury Status": "Q",
    #             "Starting": "No",
    #             "player_name": "Odell Beckham Jr.",
    #             "eman_reyalp": "Beckham Jr. Odell"
    #         },
    #         "nfl.p.30972": {
    #             "First Name": "Saquon",
    #             "Last Name": "Barkley",
    #             PLAYER_POSITION: "RB",
    #             "Team": "NYG",
    #             "Opponent": "IND",
    #             "Game": "NYG@IND",
    #             "Time": "1:00PM EST",
    #             PLAYER_SALARY: 36,
    #             PLAYER_POINTS_PROJECTION: 21.6,
    #             "Injury Status": " ",
    #             "Starting": "No",
    #             "player_name": "Saquon Barkley",
    #             "eman_reyalp": "Barkley Saquon"
    #         },
    #         "nfl.p.6760": {
    #             "First Name": "Eli",
    #             "Last Name": "Manning",
    #             PLAYER_POSITION: "QB",
    #             "Team": "NYG",
    #             "Opponent": "IND",
    #             "Game": "NYG@IND",
    #             "Time": "1:00PM EST",
    #             PLAYER_SALARY: 25,
    #             PLAYER_POINTS_PROJECTION: 15.0,
    #             "Injury Status": " ",
    #             "Starting": "No",
    #             "player_name": "Eli Manning",
    #             "eman_reyalp": "Manning Eli"
    #         }
    #     }
    #     self.assertDictEqual(correct, result)
    #
    # def test_import_csv_from_not_csv(self):
    #     with patch('os.path.isfile') as mock_isfile:
    #         mock_isfile.return_value = True
    #         with patch('builtins.open',
    #                    mock_open(read_data='Id,First Name,Last Name,Position,'
    #                                        'Team,Opponent,Game,Time,Salary,'
    #                                        'FPPG,Injury Status,Starting\n'
    #                                        'nfl.p.27540,Odell,Beckham Jr.,WR,'
    #                                        'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
    #                                        'Q,No\n'
    #                                        'nfl.p.30972,Saquon,Barkley,RB,NYG,'
    #                                        'IND,NYG@IND,1:00PM EST,36,21.6,\" '
    #                                        '\",No\n'
    #                                        'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
    #                                        'NYG@IND,1:00PM EST,25,15.0,'
    #                                        '\" \",No')):
    #             self.assertRaises(ValueError,
    #                               DfsOptimizer.import_csv, 'testcsv', 'Id',
    #                               {'FPPG': np.float, 'Salary': np.int}, None,
    #                               None, None)
    #
    # def import_csv_from_nonexistent_file(self):
    #     with patch('os.path.isfile') as mock_isfile:
    #         mock_isfile.return_value = False
    #         with patch('builtins.open',
    #                    mock_open(read_data='Id,First Name,Last Name,Position,'
    #                                        'Team,Opponent,Game,Time,Salary,'
    #                                        'FPPG,Injury Status,Starting\n'
    #                                        'nfl.p.27540,Odell,Beckham Jr.,WR,'
    #                                        'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
    #                                        'Q,No\n'
    #                                        'nfl.p.30972,Saquon,Barkley,RB,NYG,'
    #                                        'IND,NYG@IND,1:00PM EST,36,21.6,\" '
    #                                        '\",No\n'
    #                                        'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
    #                                        'NYG@IND,1:00PM EST,25,15.0,'
    #                                        '\" \",No')):
    #             self.assertRaises(RuntimeError,
    #                               DfsOptimizer.import_csv, 'test.csv', 'Id',
    #                               {'FPPG': np.float, 'Salary': np.int}, None,
    #                               None, None)
