import numpy as np
import pulp
import unittest
from unittest.mock import mock_open, patch

from fantasyasst.constants import *
from fantasyasst.optimizer.dfs import DfsOptimizer
from fantasyasst.optimizer.exceptions import OptimizerException


class TestDfsOptimizer(unittest.TestCase):
    @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    def setUp(self):
        self.players = {
            'p1': {
                PLAYER_NAME: 'player_1',
                PLAYER_POINTS_PROJECTION: 25,
                PLAYER_POSITION: 'position_1',
                PLAYER_SALARY: 3
            },
            'p2': {
                PLAYER_NAME: 'player_2',
                PLAYER_POINTS_PROJECTION: 50,
                PLAYER_POSITION: 'position_3',
                PLAYER_SALARY: 1
            },
            'p3': {
                PLAYER_NAME: 'player_3',
                PLAYER_POINTS_PROJECTION: 100,
                PLAYER_POSITION: 'position_1',
                PLAYER_SALARY: 10
            },
            'p4': {
                PLAYER_NAME: 'player_4',
                PLAYER_POINTS_PROJECTION: 30,
                PLAYER_POSITION: 'position_2',
                PLAYER_SALARY: 6
            },
            'p5': {
                PLAYER_NAME: 'player_4',
                PLAYER_POINTS_PROJECTION: 5,
                PLAYER_POSITION: 'position_2',
                PLAYER_SALARY: 2
            },
            'p6': {
                PLAYER_NAME: 'player_4',
                PLAYER_POINTS_PROJECTION: 20,
                PLAYER_POSITION: 'position_2',
                PLAYER_SALARY: 3
            },
            'p7': {
                PLAYER_NAME: 'player_7',
                PLAYER_POINTS_PROJECTION: 45,
                PLAYER_POSITION: 'position_3',
                PLAYER_SALARY: 1
            }
        }

        self.positions = {
            'position_1': 1,
            'position_2': 1,
            'position_3': 1
        }

        self.budget = 10

        self.dfs_optimizer = DfsOptimizer(self.players, self.positions,
                                          self.budget)

        self.positions_with_flex = {
            'position_1': 1,
            'position_2': 1,
            'position_3': 1,
            FLEX_POSITION: 1
        }

        self.non_flex_total = 2

        self.flex_positions = {'position_1', 'position_2'}

        self.dfs_optimizer_with_flex = DfsOptimizer(self.players,
                                                    self.positions_with_flex,
                                                    self.budget,
                                                    self.flex_positions)

    def test_player_variable_construction(self):
        variables = self.dfs_optimizer.model.variablesDict()
        for p in self.players:
            self.assertTrue(p in variables)
            var = variables[p]
            self.assertEqual(p, var.name)
            self.assertEqual(0, var.lowBound)
            self.assertEqual(1, var.upBound)
            self.assertTrue(var.isInteger())

        for var_key in variables.keys():
            self.assertTrue(var_key in self.players)

    def test_player_variable_with_flex_construction(self):
        variables = self.dfs_optimizer_with_flex.model.variablesDict()
        for p in self.players:
            self.assertTrue(p in variables)
            var = variables[p]
            self.assertEqual(p, var.name)
            self.assertEqual(0, var.lowBound)
            self.assertEqual(1, var.upBound)
            self.assertTrue(var.isInteger())

        for var_key in variables.keys():
            self.assertTrue(var_key in self.players)

    def test_position_requirement_constraint_construction(self):
        for position, requirement in self.positions.items():
            self.assertTrue(position in self.dfs_optimizer.model.constraints)

            constraint = self.dfs_optimizer.model.constraints[position]
            self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
            self.assertEqual(-constraint.constant, requirement)

            terms = constraint.items()
            variables_in_constraint = set()
            for tup in terms:
                self.assertTrue(tup[0].name in self.players)
                self.assertEqual(self.players[tup[0].name][PLAYER_POSITION],
                                 position)
                self.assertEqual(tup[1], 1)
                variables_in_constraint.add(tup[0].name)

    def test_position_requirement_with_flex_constraint_construction(self):
        for position, requirement in self.positions_with_flex.items():
            if position != FLEX_POSITION and \
                    position not in self.flex_positions:
                self.assertTrue(
                    position in self.dfs_optimizer_with_flex.model.constraints)

                constraint = self.dfs_optimizer_with_flex.model.constraints[
                    position]
                self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
                self.assertEqual(-constraint.constant, requirement)

                lb_terms = constraint.items()
                variables_in_constraint = set()
                for tup in lb_terms:
                    self.assertTrue(tup[0].name in self.players)
                    self.assertEqual(
                        self.players[tup[0].name][PLAYER_POSITION],
                        position)
                    self.assertEqual(tup[1], 1)
                    variables_in_constraint.add(tup[0].name)

                for player, attributes in self.players.items():
                    if attributes[PLAYER_POSITION] == position:
                        self.assertTrue(player in variables_in_constraint)
            elif position == FLEX_POSITION:
                self.assertTrue(
                    position in self.dfs_optimizer_with_flex.model.constraints)

                constraint = self.dfs_optimizer_with_flex.model.constraints[
                    position]
                self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
                self.assertEqual(-constraint.constant, requirement +
                                 self.non_flex_total)

                lb_terms = constraint.items()
                variables_in_constraint = set()
                for tup in lb_terms:
                    self.assertTrue(tup[0].name in self.players)
                    self.assertTrue(
                        self.players[tup[0].name][PLAYER_POSITION] in
                        self.flex_positions)
                    self.assertEqual(tup[1], 1)
                    variables_in_constraint.add(tup[0].name)

                for player, attributes in self.players.items():
                    if attributes[PLAYER_POSITION] in self.flex_positions:
                        self.assertTrue(player in variables_in_constraint)
            else:
                self.assertTrue(
                    position + LB_SUFFIX in
                    self.dfs_optimizer_with_flex.model.constraints)
                self.assertTrue(
                    position + UB_SUFFIX in
                    self.dfs_optimizer_with_flex.model.constraints)

                lb_constraint = self.dfs_optimizer_with_flex.model.constraints[
                    position + LB_SUFFIX]
                ub_constraint = self.dfs_optimizer_with_flex.model.constraints[
                    position + UB_SUFFIX]
                self.assertEqual(pulp.LpConstraintGE, lb_constraint.sense)
                self.assertEqual(pulp.LpConstraintLE, ub_constraint.sense)
                self.assertEqual(-lb_constraint.constant, requirement)
                self.assertEqual(-ub_constraint.constant, requirement +
                                 self.positions_with_flex[FLEX_POSITION])

                lb_terms = lb_constraint.items()
                variables_in_constraint = set()
                for tup in lb_terms:
                    self.assertTrue(tup[0].name in self.players)
                    self.assertTrue(
                        self.players[tup[0].name][PLAYER_POSITION] in
                        self.flex_positions)
                    self.assertEqual(tup[1], 1)
                    variables_in_constraint.add(tup[0].name)

                for player, attributes in self.players.items():
                    if attributes[PLAYER_POSITION] == position:
                        self.assertTrue(player in variables_in_constraint)

                ub_terms = lb_constraint.items()
                variables_in_constraint = set()
                for tup in ub_terms:
                    self.assertTrue(tup[0].name in self.players)
                    self.assertTrue(
                        self.players[tup[0].name][PLAYER_POSITION] in
                        self.flex_positions)
                    self.assertEqual(tup[1], 1)
                    variables_in_constraint.add(tup[0].name)

                for player, attributes in self.players.items():
                    if attributes[PLAYER_POSITION] == position:
                        self.assertTrue(player in variables_in_constraint)

    @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    def test_no_flex_positions_exception(self):
        self.assertRaises(ValueError,
                          DfsOptimizer, self.players, self.positions_with_flex,
                          10)

    @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    def test_player_missing_attributes(self):
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_SALARY: 1, PLAYER_POINTS_PROJECTION: 1}},
                          self.positions,
                          10)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1', PLAYER_POINTS_PROJECTION: 1}},
                          self.positions,
                          10)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1', PLAYER_SALARY: 1}},
                          self.positions,
                          10)

    @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    def test_player_missing_attributes_with_flex(self):
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_SALARY: 1, PLAYER_POINTS_PROJECTION: 1}},
                          self.positions_with_flex,
                          10, self.flex_positions)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1', PLAYER_POINTS_PROJECTION: 1}},
                          self.positions_with_flex,
                          10, self.flex_positions)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1', PLAYER_SALARY: 1}},
                          self.positions_with_flex,
                          10, self.flex_positions)

    def test_objective_construction(self):
        objective = self.dfs_optimizer.model.objective
        terms = objective.items()
        variables_in_objective = set()
        for tup in terms:
            self.assertTrue(tup[0].name in self.players)
            self.assertEqual(tup[1], self.players[tup[0].name][PLAYER_POINTS_PROJECTION])
            variables_in_objective.add(tup[0].name)

        for player, attributes in self.players.items():
            self.assertTrue(player in variables_in_objective)

    def test_objective_with_flex_construction(self):
        objective = self.dfs_optimizer_with_flex.model.objective
        terms = objective.items()
        variables_in_objective = set()
        for tup in terms:
            self.assertTrue(tup[0].name in self.players)
            self.assertEqual(tup[1], self.players[tup[0].name][PLAYER_POINTS_PROJECTION])
            variables_in_objective.add(tup[0].name)

        for player, attributes in self.players.items():
            self.assertTrue(player in variables_in_objective)

    def test_budget_constraint_construction(self):
        self.assertTrue(
            LINEUP_SALARY_STR in self.dfs_optimizer.model.constraints)
        constraint = self.dfs_optimizer.model.constraints[LINEUP_SALARY_STR]
        self.assertEqual(pulp.LpConstraintLE, constraint.sense)
        self.assertEqual(-constraint.constant, self.budget)

        terms = constraint.items()
        variables_in_constraint = set()
        for tup in terms:
            self.assertTrue(tup[0].name in self.players)
            self.assertEqual(tup[1], self.players[tup[0].name][PLAYER_SALARY])
            variables_in_constraint.add(tup[0].name)

        for player, attributes in self.players.items():
            self.assertTrue(player in variables_in_constraint)

    def test_budget_with_flex_constraint_construction(self):
        self.assertTrue(
            LINEUP_SALARY_STR in self.dfs_optimizer_with_flex.model.constraints)
        constraint = \
            self.dfs_optimizer_with_flex.model.constraints[LINEUP_SALARY_STR]
        self.assertEqual(pulp.LpConstraintLE, constraint.sense)
        self.assertEqual(-constraint.constant, self.budget)

        terms = constraint.items()
        variables_in_constraint = set()
        for tup in terms:
            self.assertTrue(tup[0].name in self.players)
            self.assertEqual(tup[1], self.players[tup[0].name][PLAYER_SALARY])
            variables_in_constraint.add(tup[0].name)

        for player, attributes in self.players.items():
            self.assertTrue(player in variables_in_constraint)

    def test_optimize_result_format(self):
        result = self.dfs_optimizer.optimize()
        result_with_flex = self.dfs_optimizer_with_flex.optimize()
        for key in [IP_STATUS_STR, LINEUP_SALARY_STR,
                    LINEUP_PLAYERS_STR, LINEUP_POINTS_STR]:
            self.assertTrue(key in result)
            self.assertTrue(key in result_with_flex)

    def test_optimize_result(self):
        result = self.dfs_optimizer.optimize()
        lineup = {'p1', 'p2', 'p4'}
        salary = 10
        projection = 105
        self.assertEqual(result[LINEUP_POINTS_STR], projection)
        self.assertEqual(result[LINEUP_SALARY_STR], salary)
        self.assertSetEqual(result[LINEUP_PLAYERS_STR], lineup)

    def test_optimize_with_flex_result(self):
        result = self.dfs_optimizer_with_flex.optimize()
        lineup = {'p1', 'p2', 'p5', 'p6'}
        salary = 9
        projection = 100
        self.assertEqual(result[LINEUP_POINTS_STR], projection)
        self.assertEqual(result[LINEUP_SALARY_STR], salary)
        self.assertSetEqual(result[LINEUP_PLAYERS_STR], lineup)

    @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    def test_infeasible_result(self):
        optimizer = DfsOptimizer({'p1': {PLAYER_POSITION: 'position_1',
                                         PLAYER_SALARY: 1,
                                         PLAYER_POINTS_PROJECTION: 25}},
                                 self.positions, 10)
        self.assertRaises(OptimizerException, optimizer.optimize)

        optimizer = DfsOptimizer({'p1': {PLAYER_POSITION: 'position_1',
                                         PLAYER_SALARY: 1,
                                         PLAYER_POINTS_PROJECTION: 25}},
                                 self.positions_with_flex, 10,
                                 self.flex_positions)
        self.assertRaises(OptimizerException, optimizer.optimize)

    def test_import_csv(self):
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
                ignore_conditions = [('Injury Status', 'O'),
                                     ('Injury Status', 'IR'),
                                     ('Injury Status', 'D')]

                def make_name(row):
                    return row['First Name'] + ' ' + row['Last Name']

                def make_name_backwards(row):
                    return row['Last Name'] + ' ' + row['First Name']

                apply_functions = [(PLAYER_NAME, make_name),
                                   (PLAYER_NAME[::-1], make_name_backwards)]

                column_renames = {
                    'Position': PLAYER_POSITION,
                    'FPPG': PLAYER_POINTS_PROJECTION,
                    'Salary': PLAYER_SALARY
                }

                result = DfsOptimizer.import_csv('test.csv',
                                                 'Id',
                                                 {
                                                     'FPPG': np.float,
                                                     'Salary': np.int
                                                 }, column_renames,
                                                 ignore_conditions,
                                                 apply_functions)

        correct = {
            "nfl.p.27540": {
                "First Name": "Odell",
                "Last Name": "Beckham Jr.",
                PLAYER_POSITION: "WR",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                PLAYER_SALARY: 26,
                PLAYER_POINTS_PROJECTION: 16.0,
                "Injury Status": "Q",
                "Starting": "No",
                "player_name": "Odell Beckham Jr.",
                "eman_reyalp": "Beckham Jr. Odell"
            },
            "nfl.p.30972": {
                "First Name": "Saquon",
                "Last Name": "Barkley",
                PLAYER_POSITION: "RB",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                PLAYER_SALARY: 36,
                PLAYER_POINTS_PROJECTION: 21.6,
                "Injury Status": " ",
                "Starting": "No",
                "player_name": "Saquon Barkley",
                "eman_reyalp": "Barkley Saquon"
            },
            "nfl.p.6760": {
                "First Name": "Eli",
                "Last Name": "Manning",
                PLAYER_POSITION: "QB",
                "Team": "NYG",
                "Opponent": "IND",
                "Game": "NYG@IND",
                "Time": "1:00PM EST",
                PLAYER_SALARY: 25,
                PLAYER_POINTS_PROJECTION: 15.0,
                "Injury Status": " ",
                "Starting": "No",
                "player_name": "Eli Manning",
                "eman_reyalp": "Manning Eli"
            }
        }
        self.assertDictEqual(correct, result)

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
                                  DfsOptimizer.import_csv, 'testcsv', 'Id',
                                  {'FPPG': np.float, 'Salary': np.int}, None,
                                  None, None)

    def import_csv_from_nonexistent_file(self):
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
                                  DfsOptimizer.import_csv, 'test.csv', 'Id',
                                  {'FPPG': np.float, 'Salary': np.int}, None,
                                  None, None)
