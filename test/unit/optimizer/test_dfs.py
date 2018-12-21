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

    def test_variable_construction(self):
        for p in self.players:
            self.assertTrue(p in self.dfs_optimizer.player_variables)

            var = self.dfs_optimizer.player_variables[p]
            self.assertEqual(var.lowBound, 0)
            self.assertEqual(var.upBound, 1)
            self.assertTrue(var.isInteger())
