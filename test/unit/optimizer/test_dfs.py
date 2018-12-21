import pulp
import unittest
from unittest.mock import patch

from fantasyasst.constants import *
from fantasyasst.optimizer.dfs import DfsOptimizer


class TestDfsOptimizer(unittest.TestCase):
    @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    def setUp(self):
        self.players = {
            'p1': {
                PLAYER_NAME: 'player_1',
                PLAYER_POINTS: 25,
                PLAYER_POSITION: 'position_1',
                PLAYER_SALARY: 3
            },
            'p2': {
                PLAYER_NAME: 'player_2',
                PLAYER_POINTS: 1,
                PLAYER_POSITION: 'position_1',
                PLAYER_SALARY: 2
            },
            'p3': {
                PLAYER_NAME: 'player_3',
                PLAYER_POINTS: 100,
                PLAYER_POSITION: 'position_1',
                PLAYER_SALARY: 10
            },
            'p4': {
                PLAYER_NAME: 'player_4',
                PLAYER_POINTS: 30,
                PLAYER_POSITION: 'position_2',
                PLAYER_SALARY: 6
            },
            'p5': {
                PLAYER_NAME: 'player_4',
                PLAYER_POINTS: 5,
                PLAYER_POSITION: 'position_2',
                PLAYER_SALARY: 4
            },
            'p6': {
                PLAYER_NAME: 'player_4',
                PLAYER_POINTS: 20,
                PLAYER_POSITION: 'position_2',
                PLAYER_SALARY: 3
            }
        }

        self.positions = {
            'position_1': 1,
            'position_2': 1
        }

        self.budget = 10

        self.dfs_optimizer = DfsOptimizer(self.players, self.positions,
                                          self.budget)

        self.positions_with_flex = {
            'position_1': 1,
            'position_2': 1,
            FLEX_POSITION: 1
        }

        self.flex_positions = {'position_1', 'position_2'}

        self.dfs_optimizer_with_flex = DfsOptimizer(self.players,
                                                    self.positions_with_flex,
                                                    self.budget,
                                                    self.flex_positions)

    def test_player_variable_construction(self):
        for p in self.players:
            self.assertTrue(p in self.dfs_optimizer.player_variables)
            var = self.dfs_optimizer.player_variables[p]
            self.assertEqual(p, var.name)
            self.assertEqual(0, var.lowBound)
            self.assertEqual(1, var.upBound)
            self.assertTrue(var.isInteger())

        for var_key in self.dfs_optimizer.player_variables.keys():
            self.assertTrue(var_key in self.players)

    def test_player_variable_with_flex_construction(self):
        for p in self.players:
            self.assertTrue(p in self.dfs_optimizer_with_flex.player_variables)
            var = self.dfs_optimizer_with_flex.player_variables[p]
            self.assertEqual(p, var.name)
            self.assertEqual(0, var.lowBound)
            self.assertEqual(1, var.upBound)
            self.assertTrue(var.isInteger())

        for var_key in self.dfs_optimizer_with_flex.player_variables.keys():
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
            self.assertTrue(
                position in self.dfs_optimizer_with_flex.model.constraints)

            constraint = self.dfs_optimizer_with_flex.model.constraints[
                position]
            self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
            self.assertEqual(-constraint.constant, requirement)

            terms = constraint.items()
            variables_in_constraint = set()
            for tup in terms:
                self.assertTrue(tup[0].name in self.players)
                if position == FLEX_POSITION:
                    self.assertTrue(self.players[tup[0].name][PLAYER_POSITION]
                                    in self.flex_positions)
                else:
                    self.assertEqual(
                        self.players[tup[0].name][PLAYER_POSITION],
                        position)
                self.assertEqual(tup[1], 1)
                variables_in_constraint.add(tup[0].name)

            for player, attributes in self.players.items():
                if position == FLEX_POSITION and \
                        attributes[PLAYER_POSITION] in self.flex_positions:
                    self.assertTrue(player in variables_in_constraint)
                elif attributes[PLAYER_POSITION] == position:
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
                          {'p1': {PLAYER_SALARY: 1, PLAYER_POINTS: 1}},
                          self.positions,
                          10)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1', PLAYER_POINTS: 1}},
                          self.positions,
                          10)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_SALARY: 'pos_1', PLAYER_POSITION: 1}},
                          self.positions,
                          10)

    @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    def test_player_missing_attributes_with_flex(self):
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_SALARY: 1, PLAYER_POINTS: 1}},
                          self.positions_with_flex,
                          10, self.flex_positions)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_POSITION: 'pos_1', PLAYER_POINTS: 1}},
                          self.positions_with_flex,
                          10, self.flex_positions)
        self.assertRaises(ValueError,
                          DfsOptimizer,
                          {'p1': {PLAYER_SALARY: 'pos_1', PLAYER_POSITION: 1}},
                          self.positions_with_flex,
                          10, self.flex_positions)

    def test_objective_construction(self):
        objective = self.dfs_optimizer.model.objective
        terms = objective.items()
        variables_in_objective = set()
        for tup in terms:
            self.assertTrue(tup[0].name in self.players)
            self.assertEqual(tup[1], self.players[tup[0].name][PLAYER_POINTS])
            variables_in_objective.add(tup[0].name)

        for player, attributes in self.players.items():
            self.assertTrue(player in variables_in_objective)

    def test_objective_with_flex_construction(self):
        objective = self.dfs_optimizer_with_flex.model.objective
        terms = objective.items()
        variables_in_objective = set()
        for tup in terms:
            self.assertTrue(tup[0].name in self.players)
            self.assertEqual(tup[1], self.players[tup[0].name][PLAYER_POINTS])
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
        lineup = {'p1', 'p4'}
        salary = 9
        projection = 55
        self.assertEqual(result[LINEUP_POINTS_STR], projection)
        self.assertEqual(result[LINEUP_SALARY_STR], salary)
        self.assertSetEqual(result[LINEUP_PLAYERS_STR], lineup)

    def test_optimize_with_flex_result(self):
        result = self.dfs_optimizer_with_flex.optimize()
        lineup = {'p1', 'p5', 'p6'}
        salary = 10
        projection = 50
        print(result)
        self.assertEqual(result[LINEUP_POINTS_STR], projection)
        self.assertEqual(result[LINEUP_SALARY_STR], salary)
        self.assertSetEqual(result[LINEUP_PLAYERS_STR], lineup)
