import numpy as np
import pulp
import unittest
from unittest.mock import mock_open, patch

from fantasyasst.optimizer.dfs import DfsOptimizer
from fantasyasst.optimizer.exceptions import OptimizerException
from fantasyasst.player import Player


class TestDfsOptimizer(unittest.TestCase):
    POS_ONLY = 'positions_only'
    W_FLEX = 'with_flex'
    W_UTILITY = 'with_utility'
    W_FLEX_W_UTILITY = 'with_flex_with_utility'

    def setUp(self):
        self.players = {
            'p1': {
                Player.NAME: 'player_1',
                Player.POINTS_PROJECTION: 25,
                Player.POSITION: 'position_1',
                Player.SALARY: 3
            },
            'p2': {
                Player.NAME: 'player_2',
                Player.POINTS_PROJECTION: 30,
                Player.POSITION: 'position_1',
                Player.SALARY: 15
            },
            'p3': {
                Player.NAME: 'player_3',
                Player.POINTS_PROJECTION: 4,
                Player.POSITION: 'position_2',
                Player.SALARY: 5
            },
            'p4': {
                Player.NAME: 'player_4',
                Player.POINTS_PROJECTION: 2,
                Player.POSITION: 'position_2',
                Player.SALARY: 2
            },
            'p5': {
                Player.NAME: 'player_5',
                Player.POINTS_PROJECTION: 30,
                Player.POSITION: 'position_3',
                Player.SALARY: 9
            },
            'p6': {
                Player.NAME: 'player_6',
                Player.POINTS_PROJECTION: 1,
                Player.POSITION: 'position_3',
                Player.SALARY: 8
            },
            'p7': {
                Player.NAME: 'player_1',
                Player.POINTS_PROJECTION: 25,
                Player.POSITION: 'position_4',
                Player.SALARY: 1
            },
            'p8': {
                Player.NAME: 'player_8',
                Player.POINTS_PROJECTION: 25,
                Player.POSITION: 'position_4',
                Player.SALARY: 2
            },
            'p9': {
                Player.NAME: 'player_9',
                Player.POINTS_PROJECTION: 3,
                Player.POSITION: 'position_5',
                Player.SALARY: 5
            }
        }

        self.positions = {
            'position_1': 1,
            'position_2': 1,
            'position_3': 1,
            'position_4': 1,
            'position_5': 1
        }

        self.budget = 35

        self.flex_positions = {
            '1_2': ({'position_1', 'position_2'}, 1),
            '3_4': ({'position_3', 'position_4'}, 1),
        }

        self.utility_requirement = 1

        self.optimizers = {
            self.POS_ONLY: DfsOptimizer(self.players,
                                        self.positions,
                                        self.budget),
            self.W_FLEX: DfsOptimizer(self.players, self.positions,
                                      self.budget,
                                      flex_positions=self.flex_positions),
            self.W_UTILITY: DfsOptimizer(self.players, self.positions,
                                         self.budget, utility_requirement=
                                         self.utility_requirement),
            self.W_FLEX_W_UTILITY: DfsOptimizer(self.players, self.positions,
                                                self.budget,
                                                utility_requirement=
                                                self.utility_requirement),
        }

    def test_player_dict_copy(self):
        for name, optimizer in self.optimizers.items():
            self.assertDictEqual(self.players, optimizer.players,
                                 msg=name + ' failed')

    def test_player_variable_construction(self):
        for name, optimizer in self.optimizers.items():
            variables = optimizer.model.variablesDict()
            for p in self.players:
                self.assertIn(p, variables, msg=name + ' failed')
                var = variables[p]
                self.assertEqual(p, var.name, msg=name + ' failed')
                self.assertEqual(0, var.lowBound, msg=name + ' failed')
                self.assertEqual(1, var.upBound, msg=name + ' failed')
                self.assertTrue(var.isInteger(), msg=name + ' failed')

            for var_key in variables.keys():
                self.assertIn(var_key, self.players, msg=name + ' failed')

    def test_position_requirement_equality_constraint(self):
        model = self.optimizers[self.POS_ONLY].model
        for position, requirement in self.positions.items():
            self.assertIn(position, model.constraints)

            constraint = model.constraints[position]
            self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
            self.assertEqual(-constraint.constant, requirement)

            terms = constraint.items()
            variables_in_constraint = set()
            for tup in terms:
                self.assertIn(tup[0].name, self.players)
                self.assertEqual(self.players[tup[0].name][Player.POSITION],
                                 position)
                self.assertEqual(tup[1], 1)
                variables_in_constraint.add(tup[0].name)

            for i, p in self.players.items():
                if p[Player.POSITION] == position:
                    self.assertIn(i, variables_in_constraint)

    def test_position_requirement_lb_constraint(self):
        for name, optimizer in self.optimizers.items():
            if name == self.POS_ONLY:
                continue
            model = optimizer.model
            for position, requirement in self.positions.items():
                constraint_name = position
                sense = pulp.LpConstraintEQ
                if self.W_UTILITY in name:
                    constraint_name += DfsOptimizer.LB_SUFFIX
                    sense = pulp.LpConstraintGE
                elif self.W_FLEX in name:
                    for flex, (allowed, req) in self.flex_positions.items():
                        if position in allowed:
                            constraint_name += DfsOptimizer.LB_SUFFIX
                            sense = pulp.LpConstraintGE
                            break

                self.assertIn(constraint_name, model.constraints,
                              msg=name + ' failed')

                constraint = model.constraints[constraint_name]
                self.assertEqual(sense, constraint.sense, msg=name + ' failed')
                self.assertEqual(-constraint.constant, requirement,
                                 msg=name + ' failed')

                terms = constraint.items()
                variables_in_constraint = set()
                for tup in terms:
                    self.assertIn(tup[0].name, self.players,
                                  msg=name + ' failed')
                    self.assertEqual(self.players[tup[0].name][Player.POSITION],
                                     position, msg=name + ' failed')
                    self.assertEqual(tup[1], 1, msg=name + ' failed')
                    variables_in_constraint.add(tup[0].name)

                for i, p in self.players.items():
                    if p[Player.POSITION] == position:
                        self.assertIn(i, variables_in_constraint,
                                      msg=name + ' failed')

    def test_position_requirement_ub_constraint(self):
        for name, optimizer in self.optimizers.items():
            buffer = 0
            if name == self.POS_ONLY:
                continue
            if name == self.W_UTILITY or name == self.W_FLEX_W_UTILITY:
                buffer += self.utility_requirement
            model = optimizer.model

            for position, requirement in self.positions.items():
                if name == self.W_FLEX or name == self.W_FLEX_W_UTILITY:
                    for flex, (allowed, req) in self.flex_positions:
                        if position in allowed:
                            buffer += req
                            break

                constraint_name = position + DfsOptimizer.UB_SUFFIX
                self.assertTrue(constraint_name in model.constraints)

                constraint = model.constraints[constraint_name]
                self.assertEqual(pulp.LpConstraintGE, constraint.sense)
                self.assertEqual(-constraint.constant, requirement)

                terms = constraint.items()
                variables_in_constraint = set()
                for tup in terms:
                    self.assertTrue(tup[0].name in self.players)
                    self.assertEqual(self.players[tup[0].name][Player.POSITION],
                                     position)
                    self.assertEqual(tup[1], 1)
                    variables_in_constraint.add(tup[0].name)

                for i, p in self.players.items():
                    if p[Player.POSITION] == position:
                        self.assertIn(i, variables_in_constraint)

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
                          {'p1': {PLAYER_SALARY: 1,
                                  PLAYER_POINTS_PROJECTION: 1}},
                          self.positions,
                          10)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1',
                                  PLAYER_POINTS_PROJECTION: 1}},
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
                          {'p1': {PLAYER_SALARY: 1,
                                  PLAYER_POINTS_PROJECTION: 1}},
                          self.positions_with_flex,
                          10, self.flex_positions)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1',
                                  PLAYER_POINTS_PROJECTION: 1}},
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
            self.assertEqual(tup[1], self.players[tup[0].name][
                PLAYER_POINTS_PROJECTION])
            variables_in_objective.add(tup[0].name)

        for player, attributes in self.players.items():
            self.assertTrue(player in variables_in_objective)

    def test_objective_with_flex_construction(self):
        objective = self.dfs_optimizer_with_flex.model.objective
        terms = objective.items()
        variables_in_objective = set()
        for tup in terms:
            self.assertTrue(tup[0].name in self.players)
            self.assertEqual(tup[1], self.players[tup[0].name][
                PLAYER_POINTS_PROJECTION])
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


if __name__ == '__main__':
    unittest.main()
