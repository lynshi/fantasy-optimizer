from abc import ABC, abstractmethod
import os
import pandas as pd


class PlayerLoader(ABC):
    def __init__(self, df):
        """
        Initialize PlayerLoaderInstance

        :param df: DataFrame of data
        :type df: pd.DataFrame
        """
        self.df = df

    @classmethod
    @abstractmethod
    def load_players(cls, csv_file):
        pass

    @staticmethod
    def import_csv(file_name, index_column, data_type, column_renames,
                   row_ignore_conditions,
                   functions_to_apply) -> pd.DataFrame:
        """
        Load player data from csv find at 'file_name'

        :param file_name: /path/to/file.csv
        :param index_column: column to use as 'index_col' when loading csv as
            pandas DataFrame
        :param data_type: type requirements for columns
        :param column_renames: dict of name -> new_name for renaming columns
        :param row_ignore_conditions: list of tuples (column, value)
            specifying that rows with value in column should be dropped
        :param functions_to_apply: list of tuples (column, function) specifying
            functions to apply on DataFrame with axis=1
        :return: DataFrame of players
        :raises ValueError: if file_name does not have .csv extension
        :raise RuntimeError: if file_name does not exist
        """

        if file_name.split('.')[-1] != 'csv':
            raise ValueError('file ' + file_name + ' does not have .csv '
                                                   'extension')
        elif os.path.isfile(file_name) is False:
            raise RuntimeError('file ' + file_name + ' does not exist')

        with open(file_name) as infile:
            df = pd.read_csv(infile, index_col=index_column, dtype=data_type)

        if row_ignore_conditions is not None:
            for col, val in row_ignore_conditions:
                df = df[df[col] != val]

        if functions_to_apply is not None:
            for col, func in functions_to_apply:
                df[col] = df.apply(func, axis=1)
        df.dropna(inplace=True)

        if column_renames is not None:
            df.rename(index=str, columns=column_renames, inplace=True)

        return df

    def get_player_dict(self):
        return self.df.to_dict('index')
