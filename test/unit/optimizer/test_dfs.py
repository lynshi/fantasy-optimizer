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
                PLAYER_POINTS: 15,
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

    def test_variable_construction(self):
        for p in self.players:
            self.assertTrue(p in self.dfs_optimizer.player_variables)

            var = self.dfs_optimizer.player_variables[p]
            self.assertEqual(var.lowBound, 0)
            self.assertEqual(var.upBound, 1)
            self.assertEqual(var.name, p)
            self.assertTrue(var.isInteger())

    def test_position_requirement_constraint_construction(self):
        for position, requirement in self.positions.items():
            self.assertTrue(position in self.dfs_optimizer.position_constraints)

            constraint = self.dfs_optimizer.position_constraints[position]
            self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
            self.assertEqual(-constraint.constant, requirement)

            terms = constraint.items()
            variables_in_constraint = set()
            for tup in terms:
                self.assertEqual(self.players[tup[0].name][PLAYER_POSITION],
                                 position)
                self.assertEqual(tup[1], 1)
                variables_in_constraint.add(tup[0].name)

    def test_position_requirement_with_flex_constraint_construction(self):
        for position, requirement in self.positions_with_flex.items():
            self.assertTrue(
                position in self.dfs_optimizer_with_flex.position_constraints)

            constraint = self.dfs_optimizer_with_flex.position_constraints[
                position]
            self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
            self.assertEqual(-constraint.constant, requirement)

            terms = constraint.items()
            variables_in_constraint = set()
            for tup in terms:
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
