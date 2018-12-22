import json
import os
import pandas as pd
import pulp

from fantasyasst.player import Player
from fantasyasst.optimizer.exceptions import OptimizerException


class DfsOptimizer:
    UTILITY_CONSTRAINT = 'utility_constraint'
    LB_SUFFIX = '_lb'
    UB_SUFFIX = '_ub'
    IP_STATUS_STR = 'ip_solve_status'
    LINEUP_SALARY_STR = 'lineup_cost'
    LINEUP_POINTS_STR = 'lineup_points'
    LINEUP_PLAYERS_STR = 'lineup_players'

    def __init__(self, players, positions, budget, flex_positions=None,
                 utility_requirement=0):
        """
        Construct IP model for player selection optimization

        :param players:  dictionary of dictionaries representing players
        :param positions: dictionary of position -> requirement
        :param budget: budget for player selection
        :param flex_positions: dict of
            flex position name -> (set of valid positions, number required)
            One position should not be present in two flex positions
        :param utility_requirement: number of utility players required. This
            parameter should only be used for roster positions that accept
            players from any position (e.g. Util in Yahoo NBA DFS)

        :raises ValueError: if any player does not have all required attributes
        """

        for player, attributes in players.items():
            for attr in [Player.POSITION, Player.POINTS_PROJECTION,
                         Player.SALARY]:
                if attr not in attributes.keys():
                    raise ValueError('player \'' + player + '\' is missing '
                                                            'required '
                                                            'attribute \'' +
                                     attr + '\'')

        self.players = players

        # pass '%' so there is no leading underscore in the variable name
        player_variables = pulp.LpVariable.dict('%s', players.keys(),
                                                lowBound=0, upBound=1,
                                                cat='Integer')
        position_constraints = {}
        non_flex_count = self.add_position_constraints(player_variables,
                                                       position_constraints,
                                                       positions,
                                                       flex_positions,
                                                       utility_requirement)

        if flex_positions is not None:
            self.add_flex_constraints(player_variables,
                                      position_constraints, flex_positions,
                                      non_flex_count,
                                      utility_requirement)

        if utility_requirement > 0:
            non_utility_count = 0
            for pos, count in positions.items():
                non_utility_count += count
            if flex_positions is not None:
                for flex, (pos, count) in flex_positions.items():
                    non_utility_count += count

            self.add_utility_constraint(player_variables, position_constraints,
                                        utility_requirement, non_utility_count)

        budget_expression = \
            pulp.LpAffineExpression([(player_variables[player],
                                      attributes[Player.SALARY])
                                     for player, attributes in players.items()])
        budget_constraint = pulp.LpConstraint(
            budget_expression, pulp.LpConstraintLE,
            DfsOptimizer.LINEUP_SALARY_STR, budget)

        self.model = pulp.LpProblem('DFS Optimizer', pulp.LpMaximize)
        self.model += sum([
            attributes[Player.POINTS_PROJECTION] * player_variables[player]
            for player, attributes in players.items()
        ])

        self.model.constraints = position_constraints
        self.model.constraints.update({
            self.LINEUP_SALARY_STR: budget_constraint
        })

    def add_position_constraints(self, player_variables,
                                 position_constraints, positions,
                                 flex_positions,
                                 utility_requirement):
        """
        Add position constraints

        :param player_variables: dict of player id -> pulp variable
        :param position_constraints: dict of constraint name -> pulp constraint
        :param positions: dictionary of position -> requirement
        :param flex_positions: dict of
            flex position name -> (set of valid positions, number required)
            One position should not be present in two flex positions
        :param utility_requirement: number of utility players required. This
            parameter should only be used for roster positions that accept
            players from any position (e.g. Util in Yahoo NBA DFS)
        :return: total number of players required
        """
        # the number of players at flex positions that
        # aren't used for the flex position
        non_flex_count = {}
        # position to the flex position they can contribute to
        position_to_flex_map = {}

        if flex_positions is not None:
            for flex, (allowed, requirement) in flex_positions.items():
                non_flex_count[flex] = 0
                for p in allowed:
                    non_flex_count[flex] += positions[p]
                    position_to_flex_map[p] = flex

        for position, requirement in positions.items():
            affine_expression = \
                pulp.LpAffineExpression([(player_variables[player], 1)
                                         for player, attributes in
                                         self.players.items() if
                                         attributes[Player.POSITION] ==
                                         position])

            sense = pulp.LpConstraintEQ
            modifier = ''
            if position in position_to_flex_map or utility_requirement > 0:
                sense = pulp.LpConstraintGE
                modifier = DfsOptimizer.LB_SUFFIX

            position_constraints[position + modifier] = pulp.LpConstraint(
                affine_expression, sense, position + modifier, requirement)

            buffer = utility_requirement
            if position in position_to_flex_map:
                buffer += flex_positions[position_to_flex_map[position]][1]

            if buffer > 0:
                position_constraints[
                    position + DfsOptimizer.UB_SUFFIX] = pulp.LpConstraint(
                    affine_expression, pulp.LpConstraintLE,
                    position + DfsOptimizer.UB_SUFFIX, requirement + buffer)

        return non_flex_count

    def add_flex_constraints(self, player_variables, position_constraints,
                             flex_positions, non_flex_count,
                             utility_requirement):
        """
        Add flex constraints

        :param player_variables: dict of player id -> pulp variable
        :param position_constraints: dict of constraint name -> pulp constraint
        :param flex_positions: dict of
            flex position name -> (set of valid positions, number required)
            One position should not be present in two flex positions
        :param non_flex_count: dict of flex position -> number of players
            required in positional requirements
        :param utility_requirement: number of utility players required. This
            parameter should only be used for roster positions that accept
            players from any position (e.g. Util in Yahoo NBA DFS)
        :return: None
        """
        for flex, (allowed, requirement) in flex_positions.items():
            affine_expression = \
                pulp.LpAffineExpression([(player_variables[player], 1)
                                         for player, attributes in
                                         self.players.items() if
                                         attributes[Player.POSITION] in
                                         allowed])

            sense = pulp.LpConstraintEQ
            modifier = ''
            if utility_requirement > 0:
                sense = pulp.LpConstraintGE
                modifier = DfsOptimizer.LB_SUFFIX

            position_constraints[flex + modifier] = pulp.LpConstraint(
                affine_expression, sense, flex + modifier,
                requirement + non_flex_count[flex])

            if utility_requirement > 0:
                position_constraints[flex + DfsOptimizer.UB_SUFFIX] = \
                    pulp.LpConstraint(
                        affine_expression, pulp.LpConstraintLE,
                        flex + DfsOptimizer.UB_SUFFIX,
                        requirement + non_flex_count[flex] +
                        utility_requirement)

    def add_utility_constraint(self, player_variables, position_constraints,
                               utility_requirement, non_utility_count):
        """
        Add utility position requirement. A utility position is one that accepts
        a player from any position.

        :param player_variables: dict of player id -> pulp variable
        :param position_constraints: dict of constraint name -> pulp constraint
        :param utility_requirement: number of utility players required
        :param non_utility_count: number of players required to be non-utility
        :return: None
        """
        affine_expression = \
            pulp.LpAffineExpression([(player_variables[player], 1)
                                     for player, attributes in
                                     self.players.items()])
        position_constraints[DfsOptimizer.UTILITY_CONSTRAINT] = \
            pulp.LpConstraint(affine_expression, pulp.LpConstraintEQ,
                              DfsOptimizer.UTILITY_CONSTRAINT,
                              utility_requirement + non_utility_count)

    def optimize(self) -> dict:
        """
        Optimize IP to find best lineup for given model

        :return: dictionary of the form {
            DfsOptimizer.IP_STATUS_STR: solve status,
            DfsOptimizer.LINEUP_SALARY_STR: cost of lineup,
            DfsOptimizer.LINEUP_PLAYERS_STR: set of players to put in lineup,
            DfsOptimizer.LINEUP_POINTS_STR: total points scored projection
        }
        """
        self.model.solve()

        result = {DfsOptimizer.IP_STATUS_STR: self.model.status,
                  DfsOptimizer.LINEUP_SALARY_STR: None,
                  DfsOptimizer.LINEUP_PLAYERS_STR: set(),
                  DfsOptimizer.LINEUP_POINTS_STR: None}
        if self.model.status != pulp.LpStatusOptimal:
            raise OptimizerException('Model exited with status ' +
                                     str(self.model.status))

        result[DfsOptimizer.LINEUP_SALARY_STR] = \
            pulp.value(
                self.model.constraints[DfsOptimizer.LINEUP_SALARY_STR]) - \
            self.model.constraints[DfsOptimizer.LINEUP_SALARY_STR].constant

        result[DfsOptimizer.LINEUP_POINTS_STR] = \
            pulp.value(self.model.objective)

        for var_name, var in self.model.variablesDict().items():
            if var.varValue == 1:
                result[DfsOptimizer.LINEUP_PLAYERS_STR].add(var.name)

        return result

    def generate_lineup(self, display_lineup=True):
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

        for p in result[DfsOptimizer.LINEUP_PLAYERS_STR]:
            player = self.players[p]
            pos = player[Player.POSITION]

            # to remove extra information that may be contained in player
            lineup[pos].append({
                Player.NAME: player[Player.NAME],
                Player.POINTS_PROJECTION: player[Player.POINTS_PROJECTION],
                Player.OPPONENT: player[Player.OPPONENT],
                Player.GAME_TIME: player[Player.GAME_TIME],
                Player.SALARY: player[Player.SALARY],
                Player.INJURY_STATUS: player[Player.INJURY_STATUS],
                Player.TEAM: player[Player.TEAM]
            })

        if display_lineup is True:
            print(json.dumps(lineup, sort_keys=True, indent=4))

        return lineup
