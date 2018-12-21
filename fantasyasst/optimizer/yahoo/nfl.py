import numpy as np
import os
import pandas as pd

from fantasyasst.constants import *
from fantasyasst.optimizer.dfs import DfsOptimizer


class NflDfsOptimizer(DfsOptimizer):
    @classmethod
    def load_from_csv(cls, file_name, positions=None, budget=None,
                      flex_positions=None):
        """
        Load player data from csv find at 'file_name'

        :param file_name: /path/to/file.csv
        :param positions: dictionary of position -> limit
        :type positions: dict
        :param budget: budget for player selection
        :type budget: int
        :param flex_positions: set of positions capable of being used in flex
        :type flex_positions: set
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

        with open(file_name) as infile:
            df = pd.read_csv(infile, index_col='Id', dtype={
                'FPPG': np.float,
                'Salary': np.int
            })

        df = df[(df['Injury Status' != 'O']) & (df['Injury Status'] != 'IR')]

        def make_name(row):
            return row['First Name'] + ' ' + row['Last Name']

        df[PLAYER_NAME] = df.apply(make_name, axis=1)
        df.drop(['First Name', 'Last Name'], inplace=True)
        df.dropna(inplace=True)

        super().__init__(df.to_dict('index'), positions, budget, flex_positions)

    def generate_lineup(self):
        pass
