from abc import ABC
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

        :raises ValueError: if FLEX_POSITION in positions but flex_positions is
            None
        """

        if FLEX_POSITION in positions and flex_positions is None:
            raise ValueError('\'flex_positions\' cannot be empty if '
                             '\'FLEX_POSITION\' in \'positions\'')

        # pass '%' so there is no leading underscore in the variable name
        self.player_variables = pulp.LpVariable.dict('%s', players.keys(),
                                                     lowBound=0, upBound=1,
                                                     cat='Integer')
        self.position_constraints = {}
        for position, requirement in positions.items():
            if position == FLEX_POSITION:
                affine_expression = \
                    pulp.LpAffineExpression([(self.player_variables[player], 1)
                                             for player, attributes in
                                             players.items() if
                                             attributes[PLAYER_POSITION] in
                                             flex_positions])
            else:
                affine_expression = \
                    pulp.LpAffineExpression([(self.player_variables[player], 1)
                                             for player, attributes in
                                             players.items() if
                                             attributes[PLAYER_POSITION] ==
                                             position])

            self.position_constraints[position] = pulp.LpConstraint(
                affine_expression, pulp.LpConstraintEQ, position, requirement)
