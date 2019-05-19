import numpy as np
import pandas as pd

from fantasyopt import SITE_DEFAULTS, Player, Site
from fantasyopt.loader.base import PlayerLoader


class NflLoader(PlayerLoader):
    def __init__(self, df):
        """
        Initialize NflLoader instance

        :param df: DataFrame of data
        :type df: pd.DataFrame
        """
        super().__init__(df)

    @classmethod
    def load_players(cls, file_name, ignore_conditions=None):
        """
        Load player data from csv find at 'file_name'

        :param file_name: /path/to/file.csv
        :param ignore_conditions: conditions for which to ignore players
        :return: NflLoader instance
        """
        if ignore_conditions is None:
            ignore_conditions = \
                SITE_DEFAULTS[Site.YAHOO].NFL_PLAYER_IGNORE_CONDITIONS

        column_renames = {
            'Position': Player.POSITION,
            'FPPG': Player.POINTS_PROJECTION,
            'Salary': Player.SALARY,
            'Injury Status': Player.INJURY_STATUS,
            'Time': Player.GAME_TIME,
            'Opponent': Player.OPPONENT,
            'Team': Player.TEAM
        }

        def make_name(row):
            return row['First Name'] + ' ' + row['Last Name']

        apply_functions = [(Player.NAME, make_name)]

        return cls(PlayerLoader.import_csv(file_name, index_column='Id',
                                           data_type={
                                               'FPPG': np.float,
                                               'Salary': np.int
                                           }, column_renames=column_renames,
                                           row_ignore_conditions=
                                           ignore_conditions,
                                           functions_to_apply=apply_functions))
