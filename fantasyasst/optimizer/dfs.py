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
                                                            'required '
                                                            'attribute \'' +
                                     attr + '\'')

        # pass '%' so there is no leading underscore in the variable name
        self.player_variables = pulp.LpVariable.dict('%s', players.keys(),
                                                     lowBound=0, upBound=1,
                                                     cat='Integer')
        position_constraints = {}
        for position, requirement in positions.items():
            if position == FLEX_POSITION:
                total = 0
                for pos in positions.keys():
                    if pos == FLEX_POSITION:
                        continue
                    total += positions[pos]
                affine_expression = \
                    pulp.LpAffineExpression([(self.player_variables[player], 1)
                                             for player, attributes in
                                             players.items() if
                                             attributes[PLAYER_POSITION] in
                                             flex_positions])
                requirement += total
            else:
                affine_expression = \
                    pulp.LpAffineExpression([(self.player_variables[player], 1)
                                             for player, attributes in
                                             players.items() if
                                             attributes[PLAYER_POSITION] ==
                                             position])

            position_constraints[position] = pulp.LpConstraint(
                affine_expression, pulp.LpConstraintEQ, position, requirement)

        budget_expression = \
            pulp.LpAffineExpression([(self.player_variables[player],
                                      attributes[PLAYER_SALARY])
                                     for player, attributes in players.items()])
        budget_constraint = pulp.LpConstraint(
            budget_expression, pulp.LpConstraintLE, LINEUP_SALARY_STR, budget)

        self.model = pulp.LpProblem('DFS Optimizer', pulp.LpMaximize)
        self.model += sum([
            attributes[PLAYER_POINTS] * self.player_variables[player]
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

        for var_name, var in self.player_variables.items():
            if var.varValue == 1:
                result[LINEUP_PLAYERS_STR].add(var.name)

        return result
