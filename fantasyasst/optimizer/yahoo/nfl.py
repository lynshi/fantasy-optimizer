import json
import numpy as np
import os

from fantasyasst.constants import *
from fantasyasst.optimizer.dfs import DfsOptimizer


class NflDfsOptimizer(DfsOptimizer):
    def __init__(self, players, positions, budget, flex_positions=None):
        """
        Construct NflDfsOptimizer for player selection optimization

        :param players:  dictionary of dictionaries representing players
        :type players: dict
        :param positions: dictionary of position -> limit
        :type positions: dict
        :param budget: budget for player selection
        :type budget: int
        :param flex_positions: set of positions capable of being used in flex
        :type flex_positions: set
        """
        super().__init__(players, positions, budget, flex_positions)

    @classmethod
    def load_instance_from_csv(cls, file_name, positions=None, budget=None,
                               flex_positions=None):
        """
        Load player data from csv find at 'file_name'

        :param file_name: /path/to/file.csv
        :param positions: dict of position -> requirement
        :param budget: budget for player selection
        :param flex_positions: set of positions capable of being used in flex
        :return: NflDfsOptimizer instance
        :raises ValueError: file_name does not exist
        """

        if os.path.isfile(file_name) is False:
            raise ValueError('file ' + file_name + ' does not exist')

        if positions is None:
            positions = {
                NFL_POSITIONS_QB: 1,
                NFL_POSITION_RB: 2,
                NFL_POSITION_WR: 3,
                NFL_POSITION_TE: 1,
                FLEX_POSITION: 1,
                NFL_POSITION_DST: 1
            }

        if budget is None:
            budget = 200

        if flex_positions is None:
            flex_positions = {NFL_POSITION_RB, NFL_POSITION_WR, NFL_POSITION_TE}

        ignore_conditions = [('Injury Status', 'O'),
                             ('Injury Status', 'IR'),
                             ('Injury Status', 'D')]
        column_renames = {
            'Position': PLAYER_POSITION,
            'FPPG': PLAYER_POINTS_PROJECTION,
            'Salary': PLAYER_SALARY
        }

        players = DfsOptimizer.import_csv(file_name, 'Id',
                                          {
                                              'FPPG': np.float,
                                              'Salary': np.int
                                          }, column_renames,
                                          ignore_conditions,
                                          None)

        return cls(players, positions, budget, flex_positions)

    def generate_lineup(self):
        result = self.optimize()

    def print_lineup(self):
        pass
