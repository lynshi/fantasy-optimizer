import json
import pulp

from fantasyasst.player import Player
from fantasyasst.optimizer.exceptions import OptimizerException


class DfsOptimizer:
    UTILITY_CONSTRAINT = 'utility_constraint'
    IP_STATUS = 'ip_solve_status'
    LINEUP_SALARY = 'lineup_cost'
    LINEUP_POINTS = 'lineup_points'
    LINEUP_PLAYERS = 'lineup_players'

    IGNORE_PLAYER_PREFIX = 'ignore_'
    TEAM_MAX_PREFIX = 'team_max_'
    REQUIRE_PLAYER_PREFIX = 'require_'

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
                         Player.SALARY, Player.TEAM]:
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
            DfsOptimizer.LINEUP_SALARY, budget)

        self.model = pulp.LpProblem('DFS Optimizer', pulp.LpMaximize)
        self.model += sum([
            attributes[Player.POINTS_PROJECTION] * player_variables[player]
            for player, attributes in players.items()
        ])

        self.model.constraints = position_constraints
        self.model.constraints.update({
            self.LINEUP_SALARY: budget_constraint
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
            if position in position_to_flex_map or utility_requirement > 0:
                sense = pulp.LpConstraintGE

            position_constraints[position] = pulp.LpConstraint(
                affine_expression, sense, position, requirement)

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
            if utility_requirement > 0:
                sense = pulp.LpConstraintGE

            position_constraints[flex] = pulp.LpConstraint(
                affine_expression, sense, flex,
                requirement + non_flex_count[flex])

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

        result = {DfsOptimizer.IP_STATUS: self.model.status,
                  DfsOptimizer.LINEUP_SALARY: None,
                  DfsOptimizer.LINEUP_PLAYERS: set(),
                  DfsOptimizer.LINEUP_POINTS: None}
        if self.model.status != pulp.LpStatusOptimal:
            raise OptimizerException('Model exited with status ' +
                                     str(self.model.status))

        result[DfsOptimizer.LINEUP_SALARY] = \
            pulp.value(
                self.model.constraints[DfsOptimizer.LINEUP_SALARY]) - \
            self.model.constraints[DfsOptimizer.LINEUP_SALARY].constant

        result[DfsOptimizer.LINEUP_POINTS] = \
            pulp.value(self.model.objective)

        for var_name, var in self.model.variablesDict().items():
            if var.varValue == 1:
                result[DfsOptimizer.LINEUP_PLAYERS].add(var.name)

        return result

    def generate_lineup(self, display_lineup=True):
        """
        Generate optimal DFS lineup based on player salaries and point
            projections

        :param display_lineup: if true, print lineup in JSON to console
        :return: dict that is the lineup, organized by position
        """
        result = self.optimize()
        lineup = {}

        for p in result[DfsOptimizer.LINEUP_PLAYERS]:
            player = self.players[p]
            pos = player[Player.POSITION]

            if pos not in lineup:
                lineup[pos] = []

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

    def ignore_player(self, player_name, player_position=None,
                      player_team=None):
        """
        Ignore player named by player_name so that it is never used in the
        lineup. The position and team of the player can be specified for
        further granularity (e.g. in the case two players have the same name).
        All players satisfying the given conditions are ignored.

        :param player_name: name of the player; Player.NAME
        :param player_position: position of the player; Player.POSITION
        :param player_team: team of the player; Player.TEAM
        :return: None
        """
        constraint_name = DfsOptimizer.IGNORE_PLAYER_PREFIX + player_name
        player_variables = []
        for var_id, var in self.model.variablesDict().items():
            if self.players[var.name][Player.NAME] == player_name:
                player_variables.append((var, 1))

        if player_position is not None:
            constraint_name += player_position
            temp = []
            for var, coefficient in player_variables:
                if self.players[var.name][Player.POSITION] == player_position:
                    temp.append((var, coefficient))
            player_variables = temp

        if player_team is not None:
            constraint_name += player_team
            temp = []
            for var, coefficient in player_variables:
                if self.players[var.name][Player.TEAM] == player_team:
                    temp.append((var, coefficient))
            player_variables = temp

        affine_expression = pulp.LpAffineExpression(player_variables)
        self.model.constraints[constraint_name] = pulp.LpConstraint(
            affine_expression, pulp.LpConstraintEQ, constraint_name, 0)

    def ignore_team(self, team_name):
        """
        Constrain the solver so that no players from the given team can be
        placed in the lineup.

        :param team_name: name of the team to ignore
        :return: None
        """
        constraint_name = DfsOptimizer.IGNORE_PLAYER_PREFIX + team_name
        player_variables = []
        for var_id, var in self.model.variablesDict().items():
            if self.players[var.name][Player.TEAM] == team_name:
                player_variables.append((var, 1))

        affine_expression = pulp.LpAffineExpression(player_variables)
        self.model.constraints[constraint_name] = pulp.LpConstraint(
            affine_expression, pulp.LpConstraintEQ, constraint_name, 0)

    def set_max_players_from_same_team(self, maximum):
        """
        Constrain the solver so that at most 'maximum' players from the same
        team can be placed in the lineup.

        :param maximum: max number of players from team team_name allowed
        :return: None
        """
        team_expressions = {}
        for var_id, var in self.model.variablesDict().items():
            team = self.players[var.name][Player.TEAM]
            if team not in team_expressions:
                team_expressions[team] = pulp.LpAffineExpression(name=team, constant=0)
                print(team_expressions)
            team_expressions[team] = team_expressions[team] + var

        team_constraints = {}
        for team in team_expressions:
            team_constraints[DfsOptimizer.TEAM_MAX_PREFIX + team] = \
                pulp.LpConstraint(team_expressions[team], pulp.LpConstraintLE,
                                  DfsOptimizer.TEAM_MAX_PREFIX + team, maximum)
        self.model.constraints.update(team_constraints)

    def require_player(self, player_name, player_position=None,
                       player_team=None):
        """
        Requires player named by player_name so that it is always used in the
        lineup. he position and team of the player can be specified for further
        granularity (e.g. in the case two players have the same name). If many
        players satisfy the given condition, exactly one is allowed to be
        chosen.

        :param player_name: name of the player; Player.NAME
        :param player_position: position of the player; Player.POSITION
        :param player_team: team of the player; Player.TEAM
        :return: None
        """

        constraint_name = DfsOptimizer.REQUIRE_PLAYER_PREFIX + player_name
        player_variables = []
        for var_id, var in self.model.variablesDict().items():
            if self.players[var.name][Player.NAME] == player_name:
                player_variables.append((var, 1))

        if player_position is not None:
            constraint_name += player_position
            temp = []
            for var, coefficient in player_variables:
                if self.players[var.name][Player.POSITION] == player_position:
                    temp.append((var, coefficient))
            player_variables = temp

        if player_team is not None:
            constraint_name += player_team
            temp = []
            for var, coefficient in player_variables:
                if self.players[var.name][Player.TEAM] == player_team:
                    temp.append((var, coefficient))
            player_variables = temp

        affine_expression = pulp.LpAffineExpression(player_variables)
        self.model.constraints[constraint_name] = pulp.LpConstraint(
            affine_expression, pulp.LpConstraintEQ, constraint_name, 1)
