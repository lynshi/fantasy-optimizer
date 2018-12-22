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
        self.players = players

    @classmethod
    def load_instance_from_csv(cls, file_name, positions=None,
                               ignore_conditions=None, budget=None,
                               flex_positions=None):
        """
        Load player data from csv find at 'file_name'

        :param file_name: /path/to/file.csv
        :param positions: dict of position -> requirement
        :param ignore_conditions: conditions for which to ignore players
        :param budget: budget for player selection
        :param flex_positions: set of positions capable of being used in flex
        :return: NflDfsOptimizer instance
        :raises ValueError: file_name does not exist
        """

        if os.path.isfile(file_name) is False:
            raise ValueError('file ' + file_name + ' does not exist')

        if positions is None:
            positions = {
                NFL_POSITION_QB: 1,
                NFL_POSITION_RB: 2,
                NFL_POSITION_WR: 3,
                NFL_POSITION_TE: 1,
                FLEX_POSITION: 1,
                NFL_POSITION_DEF: 1
            }

        if budget is None:
            budget = 200

        if flex_positions is None:
            flex_positions = {NFL_POSITION_RB, NFL_POSITION_WR, NFL_POSITION_TE}

        if ignore_conditions is None:
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

    def generate_lineup(self, display_lineup=True) -> dict:
        """
        Generate optimal DFS lineup based on player salaries and point
            projections

        :param display_lineup: if true, print lineup in JSON to console
        :return: dict that is the lineup, organized by position
        """
        result = self.optimize()
        lineup = {
            'QB': [],
            'RB': [],
            'WR': [],
            'TE': [],
            'DEF': [],
        }

        for p in result[LINEUP_PLAYERS_STR]:
            player = self.players[p]
            pos = player[PLAYER_POSITION]
            lineup[pos].append({
                NAME_STR: player['First Name'] + ' ' + player['Last Name'],
                PROJECTED_POINTS_STR: player[PLAYER_POINTS_PROJECTION],
                OPPONENT_STR: player['Opponent'],
                GAME_TIME_STR: player['Time'],
                SALARY_STR: player[PLAYER_SALARY],
                INJURY_STATUS_STR: player['Injury Status']
            })

        if display_lineup is True:
            print(json.dumps(lineup, sort_keys=True, indent=4))

        return lineup
