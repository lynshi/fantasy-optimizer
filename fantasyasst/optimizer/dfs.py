from abc import ABC, abstractmethod
import numpy as np
import os
import pandas as pd
import pulp

from fantasyasst.constants import *


class DfsOptimizer(ABC):
    def __init__(self, players, positions, budget, flex_positions=None):
        """
        Construct IP model for player selection optimization

        :param players:  dictionary of dictionaries representing players
        :type players: dict
        :param positions: dictionary of position -> limit
        :type positions: dict
        :param budget: budget for player selection
        :type budget: int
        :param flex_positions: set of positions capable of being used in flex
        :type flex_positions: set

        :raises ValueError:
            if FLEX_POSITION in positions but flex_positions is None
            if any player does not have all required attributes
        """

        if FLEX_POSITION in positions and flex_positions is None:
            raise ValueError('\'flex_positions\' cannot be empty if '
                             '\'FLEX_POSITION\' in \'positions\'')

        for player, attributes in players.items():
            for attr in [PLAYER_POSITION, PLAYER_POINTS, PLAYER_SALARY]:
                if attr not in attributes.keys():
                    raise ValueError('player \'' + player + '\' is missing '
                                                            'required '
                                                            'attribute \'' +
                                     attr + '\'')

        # pass '%' so there is no leading underscore in the variable name
        player_variables = pulp.LpVariable.dict('%s', players.keys(),
                                                lowBound=0, upBound=1,
                                                cat='Integer')
        position_constraints = {}
        if FLEX_POSITION not in positions:
            for position, requirement in positions.items():
                affine_expression = \
                    pulp.LpAffineExpression([(player_variables[player], 1)
                                             for player, attributes in
                                             players.items() if
                                             attributes[PLAYER_POSITION] ==
                                             position])

                position_constraints[position] = pulp.LpConstraint(
                    affine_expression, pulp.LpConstraintEQ, position,
                    requirement)
        else:
            non_flex_total = 0
            # the number of players at flex positions that
            # aren't used for the flex position
            for position, requirement in positions.items():
                if position != FLEX_POSITION and position in flex_positions:
                    non_flex_total += requirement
                    affine_expression = \
                        pulp.LpAffineExpression([(player_variables[player], 1)
                                                 for player, attributes in
                                                 players.items() if
                                                 attributes[PLAYER_POSITION] ==
                                                 position])

                    position_constraints[position + LB_SUFFIX] = \
                        pulp.LpConstraint(
                            affine_expression, pulp.LpConstraintGE,
                            position + LB_SUFFIX,
                            requirement)

                    position_constraints[position + UB_SUFFIX] = \
                        pulp.LpConstraint(
                            affine_expression, pulp.LpConstraintLE,
                            position + UB_SUFFIX,
                            requirement + positions[FLEX_POSITION])
                elif position != FLEX_POSITION:
                    affine_expression = \
                        pulp.LpAffineExpression([(player_variables[player], 1)
                                                 for player, attributes in
                                                 players.items() if
                                                 attributes[PLAYER_POSITION] ==
                                                 position])

                    position_constraints[position] = pulp.LpConstraint(
                        affine_expression, pulp.LpConstraintEQ, position,
                        requirement)

            affine_expression = \
                pulp.LpAffineExpression([(player_variables[player], 1)
                                         for player, attributes in
                                         players.items() if
                                         attributes[PLAYER_POSITION] in
                                         flex_positions])

            position_constraints[FLEX_POSITION] = pulp.LpConstraint(
                affine_expression, pulp.LpConstraintEQ, FLEX_POSITION,
                positions[FLEX_POSITION] + non_flex_total)

        budget_expression = \
            pulp.LpAffineExpression([(player_variables[player],
                                      attributes[PLAYER_SALARY])
                                     for player, attributes in players.items()])
        budget_constraint = pulp.LpConstraint(
            budget_expression, pulp.LpConstraintLE, LINEUP_SALARY_STR, budget)

        self.model = pulp.LpProblem('DFS Optimizer', pulp.LpMaximize)
        self.model += sum([
            attributes[PLAYER_POINTS] * player_variables[player]
            for player, attributes in players.items()
        ])

        self.model.constraints = position_constraints
        self.model.constraints.update({LINEUP_SALARY_STR: budget_constraint})

    def optimize(self) -> dict:
        """
        Optimize IP to find best lineup for given model

        :return: dictionary of the form {
            IP_STATUS_STR: solve status,
            LINEUP_COST_STR: cost of lineup,
            LINEUP_PLAYERS_STR: set of players to put in lineup,
            LINEUP_POINTS_STR: total points scored projection
        }
        """
        self.model.solve()

        result = {IP_STATUS_STR: self.model.status, LINEUP_SALARY_STR: None,
                  LINEUP_PLAYERS_STR: set(), LINEUP_POINTS_STR: None}
        if self.model.status != pulp.LpStatusOptimal:
            return result

        result[LINEUP_SALARY_STR] = \
            pulp.value(self.model.constraints[LINEUP_SALARY_STR]) - \
            self.model.constraints[LINEUP_SALARY_STR].constant
        result[LINEUP_POINTS_STR] = pulp.value(self.model.objective)

        for var_name, var in self.model.variablesDict().items():
            if var.varValue == 1:
                result[LINEUP_PLAYERS_STR].add(var.name)

        return result

    @classmethod
    @abstractmethod
    def load_dfs_instance_from_csv(cls):
        pass

    @staticmethod
    def import_csv(file_name, index_column, data_type,
                   row_ignore_conditions,
                   functions_to_apply) -> dict:
        """
        Load player data from csv find at 'file_name'

        :param file_name: /path/to/file.csv
        :param index_column: column to use as 'index_col' when loading csv as
            pandas DataFrame
        :param data_type: type requirements for columns
        :param row_ignore_conditions: list of tuples (column, value)
            specifying that rows with value in column should be dropped
        :param functions_to_apply: list of tuples (column, function) specifying
            functions to apply on DataFrame with axis=1
        :return: dictionary of players
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

        return df.to_dict('index')

    @abstractmethod
    def generate_lineup(self):
        pass
