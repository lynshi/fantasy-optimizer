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
                                     'required attribute \'' + attr + '\'')

        # pass '%' so there is no leading underscore in the variable name
        player_variables = pulp.LpVariable.dict('%s', players.keys(),
                                                     lowBound=0, upBound=1,
                                                     cat='Integer')
        position_constraints = {}
        for position, requirement in positions.items():
            if position == FLEX_POSITION:
                affine_expression = \
                    pulp.LpAffineExpression([(player_variables[player], 1)
                                             for player, attributes in
                                             players.items() if
                                             attributes[PLAYER_POSITION] in
                                             flex_positions])
            else:
                affine_expression = \
                    pulp.LpAffineExpression([(player_variables[player], 1)
                                             for player, attributes in
                                             players.items() if
                                             attributes[PLAYER_POSITION] ==
                                             position])

            position_constraints[position] = pulp.LpConstraint(
                affine_expression, pulp.LpConstraintEQ, position, requirement)

        budget_expression = \
            pulp.LpAffineExpression([(player_variables[player],
                                      attributes[PLAYER_SALARY])
                                     for player, attributes in players.items()])
        budget_constraint = pulp.LpConstraint(
            budget_expression, pulp.LpConstraintLE, 'budget', budget)

        self.model = pulp.LpProblem('DFS Optimizer', pulp.LpMaximize)
        self.model += sum([
            attributes[PLAYER_POINTS] * player_variables[player]
            for player, attributes in players.items()
        ])

        self.model.constraints = position_constraints
        self.model.constraints.update({'budget': budget_constraint})
