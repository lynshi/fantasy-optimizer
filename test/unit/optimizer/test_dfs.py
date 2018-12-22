import pulp
import unittest

from fantasyasst.optimizer.dfs import DfsOptimizer
from fantasyasst.optimizer.exceptions import OptimizerException
from fantasyasst.player import Player


class TestDfsOptimizer(unittest.TestCase):
    POS_ONLY = 'positions_only'
    W_FLEX = 'with_flex'
    W_UTILITY = 'with_utility'
    W_FLEX_W_UTILITY = 'with_flex_with_utility'

    def setUp(self):
        self.players = {
            'p1': {
                Player.NAME: 'player_1',
                Player.POINTS_PROJECTION: 25,
                Player.POSITION: 'position_1',
                Player.SALARY: 3
            },
            'p2': {
                Player.NAME: 'player_2',
                Player.POINTS_PROJECTION: 30,
                Player.POSITION: 'position_1',
                Player.SALARY: 15
            },
            'p3': {
                Player.NAME: 'player_3',
                Player.POINTS_PROJECTION: 4,
                Player.POSITION: 'position_2',
                Player.SALARY: 5
            },
            'p4': {
                Player.NAME: 'player_4',
                Player.POINTS_PROJECTION: 2,
                Player.POSITION: 'position_2',
                Player.SALARY: 2
            },
            'p5': {
                Player.NAME: 'player_5',
                Player.POINTS_PROJECTION: 30,
                Player.POSITION: 'position_3',
                Player.SALARY: 9
            },
            'p6': {
                Player.NAME: 'player_6',
                Player.POINTS_PROJECTION: 1,
                Player.POSITION: 'position_3',
                Player.SALARY: 8
            },
            'p7': {
                Player.NAME: 'player_7',
                Player.POINTS_PROJECTION: 25,
                Player.POSITION: 'position_4',
                Player.SALARY: 1
            },
            'p8': {
                Player.NAME: 'player_8',
                Player.POINTS_PROJECTION: 25,
                Player.POSITION: 'position_4',
                Player.SALARY: 2
            },
            'p9': {
                Player.NAME: 'player_9',
                Player.POINTS_PROJECTION: 3,
                Player.POSITION: 'position_5',
                Player.SALARY: 5
            }
        }

        self.positions = {
            'position_1': 1,
            'position_2': 1,
            'position_3': 1,
            'position_4': 1,
            'position_5': 1
        }

        self.budget = 35

        self.flex_positions = {
            '1_2': ({'position_1', 'position_2'}, 1),
            '3_4': ({'position_3', 'position_4'}, 1),
        }

        self.utility_requirement = 1

        self.optimizers = {
            self.POS_ONLY: DfsOptimizer(self.players,
                                        self.positions,
                                        self.budget),
            self.W_FLEX: DfsOptimizer(self.players, self.positions,
                                      self.budget,
                                      flex_positions=self.flex_positions),
            self.W_UTILITY: DfsOptimizer(self.players, self.positions,
                                         self.budget, utility_requirement=
                                         self.utility_requirement),
            self.W_FLEX_W_UTILITY: DfsOptimizer(self.players, self.positions,
                                                self.budget,
                                                flex_positions=
                                                self.flex_positions,
                                                utility_requirement=
                                                self.utility_requirement),
        }

    def test_player_missing_attributes_exception(self):
        for flex, util in [(None, None), (None, self.utility_requirement),
                           (self.flex_positions, None),
                           (self.flex_positions, self.utility_requirement)]:
            self.assertRaises(ValueError,
                              DfsOptimizer,
                              {'p1': {Player.SALARY: 1,
                                      Player.POINTS_PROJECTION: 1}},
                              self.positions,
                              10, flex, util)
            self.assertRaises(ValueError,
                              DfsOptimizer,
                              {'p1': {Player.POSITION: 'pos_1',
                                      Player.POINTS_PROJECTION: 1}},
                              self.positions,
                              10, flex, util)
            self.assertRaises(ValueError,
                              DfsOptimizer,
                              {'p1': {Player.POSITION: 'pos_1',
                                      Player.SALARY: 1}},
                              self.positions,
                              10, flex, util)

    def test_player_dict_copy(self):
        for name, optimizer in self.optimizers.items():
            self.assertDictEqual(self.players, optimizer.players,
                                 msg=name + ' failed')

    def test_player_variable_construction(self):
        for name, optimizer in self.optimizers.items():
            variables = optimizer.model.variablesDict()
            for p in self.players:
                self.assertIn(p, variables,
                              msg=name + ' failed for ' + p)
                var = variables[p]
                self.assertEqual(p, var.name,
                                 msg=name + ' failed for ' + p)
                self.assertEqual(0, var.lowBound,
                                 msg=name + ' failed for ' + p)
                self.assertEqual(1, var.upBound,
                                 msg=name + ' failed for ' + p)
                self.assertTrue(var.isInteger(),
                                msg=name + ' failed for ' + p)

            for var_key in variables.keys():
                self.assertIn(var_key, self.players,
                              msg=name + ' failed for ' + var_key)

    def test_position_requirement_lb_or_eq_constraint(self):
        for name, optimizer in self.optimizers.items():
            model = optimizer.model
            for position, requirement in self.positions.items():
                sense = pulp.LpConstraintEQ
                if self.W_UTILITY in name:
                    sense = pulp.LpConstraintGE
                elif self.W_FLEX in name:
                    for flex, (allowed, req) in self.flex_positions.items():
                        if position in allowed:
                            sense = pulp.LpConstraintGE
                            break

                self.assertIn(position, model.constraints,
                              msg=name + ' failed for ' + position)

                constraint = model.constraints[position]
                self.assertEqual(sense, constraint.sense,
                                 msg=name + ' failed for ' + position)
                self.assertEqual(requirement, -constraint.constant,
                                 msg=name + ' failed for ' + position)

                terms = constraint.items()
                variables_in_constraint = set()
                for tup in terms:
                    self.assertIn(tup[0].name, self.players,
                                  msg=name + ' failed for ' + position)
                    self.assertEqual(position,
                                     self.players[tup[0].name][Player.POSITION],
                                     msg=name + ' failed for ' + position)
                    self.assertEqual(1, tup[1],
                                     msg=name + ' failed for ' + position)
                    variables_in_constraint.add(tup[0].name)

                for i, p in self.players.items():
                    if p[Player.POSITION] == position:
                        self.assertIn(i, variables_in_constraint,
                                      msg=name + ' failed for ' + position)

    def test_flex_requirement_lb_or_eq_constraint(self):
        for name, optimizer in self.optimizers.items():
            if self.W_FLEX not in name:
                continue

            model = optimizer.model
            for flex, (allowed, requirement) in self.flex_positions.items():
                sense = pulp.LpConstraintEQ
                buffer = 0
                for a in allowed:
                    buffer += self.positions[a]
                if self.W_UTILITY in name:
                    sense = pulp.LpConstraintGE

                self.assertIn(flex, model.constraints,
                              msg=name + ' failed for ' + flex)

                constraint = model.constraints[flex]
                self.assertEqual(sense, constraint.sense,
                                 msg=name + ' failed for ' + flex)
                self.assertEqual(requirement + buffer, -constraint.constant,
                                 msg=name + ' failed for ' + flex)

                terms = constraint.items()
                variables_in_constraint = set()
                for tup in terms:
                    self.assertIn(tup[0].name, self.players,
                                  msg=name + ' failed for ' + flex)
                    self.assertIn(self.players[tup[0].name][Player.POSITION],
                                  allowed, msg=name + ' failed for ' + flex)
                    self.assertEqual(1, tup[1],
                                     msg=name + ' failed for ' + flex)
                    variables_in_constraint.add(tup[0].name)

                for i, p in self.players.items():
                    if p[Player.POSITION] in allowed:
                        self.assertIn(i, variables_in_constraint,
                                      msg=name + ' failed for ' + flex)

    def test_utility_requirement_constraint(self):
        for name, optimizer in self.optimizers.items():
            if self.W_UTILITY not in name:
                continue

            model = optimizer.model
            required = self.utility_requirement
            for p, count in self.positions.items():
                required += count
            if self.W_FLEX in name:
                for flex, (allowed, req) in self.flex_positions.items():
                    required += req

            self.assertIn(DfsOptimizer.UTILITY_CONSTRAINT,
                          model.constraints)

            constraint = model.constraints[DfsOptimizer.UTILITY_CONSTRAINT]
            self.assertEqual(pulp.LpConstraintEQ, constraint.sense)
            self.assertEqual(required, -constraint.constant)

            terms = constraint.items()
            variables_in_constraint = set()
            for tup in terms:
                self.assertIn(tup[0].name, self.players)
                self.assertEqual(1, tup[1])
                variables_in_constraint.add(tup[0].name)

            for i, p in self.players.items():
                self.assertIn(i, variables_in_constraint)

    def test_budget_constraint(self):
        for name, optimizer in self.optimizers.items():
            model = optimizer.model
            self.assertIn(DfsOptimizer.LINEUP_SALARY, model.constraints)
            constraint = model.constraints[DfsOptimizer.LINEUP_SALARY]

            self.assertEqual(pulp.LpConstraintLE, constraint.sense)
            self.assertEqual(self.budget, -constraint.constant)

            terms = constraint.items()
            variables_in_constraint = set()
            for tup in terms:
                self.assertIn(tup[0].name, self.players)
                self.assertEqual(self.players[tup[0].name][Player.SALARY],
                                 tup[1])
                variables_in_constraint.add(tup[0].name)

            for i, p in self.players.items():
                self.assertIn(i, variables_in_constraint)

    def test_all_constraints_are_valid(self):
        for name, optimizer in self.optimizers.items():
            constraints = optimizer.model.constraints
            allowed_constraints = {DfsOptimizer.LINEUP_SALARY}
            for pos in self.positions:
                allowed_constraints.add(pos)

            if self.W_FLEX in name:
                for flex in self.flex_positions:
                    allowed_constraints.add(flex)
            if self.W_UTILITY in name:
                allowed_constraints.add(DfsOptimizer.UTILITY_CONSTRAINT)

            for constraint_name in constraints.keys():
                self.assertIn(constraint_name, allowed_constraints)

    def test_objective_construction(self):
        for name, optimizer in self.optimizers.items():
            objective = optimizer.model.objective

            terms = objective.items()
            variables_in_objective = set()
            for tup in terms:
                self.assertIn(tup[0].name, self.players)
                self.assertEqual(self.players[tup[0].name][
                                     Player.POINTS_PROJECTION],
                                 tup[1])
                variables_in_objective.add(tup[0].name)

            for i, p in self.players.items():
                self.assertIn(i, variables_in_objective)

    def test_optimize_result_format(self):
        for name, optimizer in self.optimizers.items():
            result = optimizer.optimize()
            for key in [DfsOptimizer.IP_STATUS,
                        DfsOptimizer.LINEUP_SALARY,
                        DfsOptimizer.LINEUP_PLAYERS,
                        DfsOptimizer.LINEUP_POINTS]:
                self.assertIn(key, result, msg=name + ' failed')

    def test_optimize_positions_only(self):
        result = self.optimizers[self.POS_ONLY].optimize()
        lineup = {'p9', 'p7', 'p3', 'p2', 'p5'}
        salary = 35.0
        projection = 92.0

        correct = {
            DfsOptimizer.IP_STATUS: pulp.LpStatusOptimal,
            DfsOptimizer.LINEUP_PLAYERS: lineup,
            DfsOptimizer.LINEUP_SALARY: salary,
            DfsOptimizer.LINEUP_POINTS: projection
        }

        self.assertDictEqual(correct, result)

    #
    # def test_optimize_result(self):
    #     result = self.dfs_optimizer.optimize()
    #     lineup = {'p1', 'p2', 'p4'}
    #     salary = 10
    #     projection = 105
    #     self.assertEqual(result[LINEUP_POINTS_STR], projection)
    #     self.assertEqual(result[LINEUP_SALARY_STR], salary)
    #     self.assertSetEqual(result[LINEUP_PLAYERS_STR], lineup)
    #
    # def test_optimize_with_flex_result(self):
    #     result = self.dfs_optimizer_with_flex.optimize()
    #     lineup = {'p1', 'p2', 'p5', 'p6'}
    #     salary = 9
    #     projection = 100
    #     self.assertEqual(result[LINEUP_POINTS_STR], projection)
    #     self.assertEqual(result[LINEUP_SALARY_STR], salary)
    #     self.assertSetEqual(result[LINEUP_PLAYERS_STR], lineup)
    #
    # @patch.multiple(DfsOptimizer, __abstractmethods__=set())
    # def test_infeasible_result(self):
    #     optimizer = DfsOptimizer({'p1': {PLAYER_POSITION: 'position_1',
    #                                      PLAYER_SALARY: 1,
    #                                      PLAYER_POINTS_PROJECTION: 25}},
    #                              self.positions, 10)
    #     self.assertRaises(OptimizerException, optimizer.optimize)
    #
    #     optimizer = DfsOptimizer({'p1': {PLAYER_POSITION: 'position_1',
    #                                      PLAYER_SALARY: 1,
    #                                      PLAYER_POINTS_PROJECTION: 25}},
    #                              self.positions_with_flex, 10,
    #                              self.flex_positions)
    #     self.assertRaises(OptimizerException, optimizer.optimize)
    #
    # def test_import_csv(self):
    #     with patch('os.path.isfile') as mock_isfile:
    #         mock_isfile.return_value = True
    #         with patch('builtins.open',
    #                    mock_open(read_data='Id,First Name,Last Name,Position,'
    #                                        'Team,Opponent,Game,Time,Salary,'
    #                                        'FPPG,Injury Status,Starting\n'
    #                                        'nfl.p.27540,Odell,Beckham Jr.,WR,'
    #                                        'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
    #                                        'Q,No\n'
    #                                        'nfl.p.30972,Saquon,Barkley,RB,NYG,'
    #                                        'IND,NYG@IND,1:00PM EST,36,21.6,\" '
    #                                        '\",No\n'
    #                                        'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
    #                                        'NYG@IND,1:00PM EST,25,15.0,'
    #                                        '\" \",No')):
    #             ignore_conditions = [('Injury Status', 'O'),
    #                                  ('Injury Status', 'IR'),
    #                                  ('Injury Status', 'D')]
    #
    #             def make_name(row):
    #                 return row['First Name'] + ' ' + row['Last Name']
    #
    #             def make_name_backwards(row):
    #                 return row['Last Name'] + ' ' + row['First Name']
    #
    #             apply_functions = [(PLAYER_NAME, make_name),
    #                                (PLAYER_NAME[::-1], make_name_backwards)]
    #
    #             column_renames = {
    #                 'Position': PLAYER_POSITION,
    #                 'FPPG': PLAYER_POINTS_PROJECTION,
    #                 'Salary': PLAYER_SALARY
    #             }
    #
    #             result = DfsOptimizer.import_csv('test.csv',
    #                                              'Id',
    #                                              {
    #                                                  'FPPG': np.float,
    #                                                  'Salary': np.int
    #                                              }, column_renames,
    #                                              ignore_conditions,
    #                                              apply_functions)
    #
    #     correct = {
    #         "nfl.p.27540": {
    #             "First Name": "Odell",
    #             "Last Name": "Beckham Jr.",
    #             PLAYER_POSITION: "WR",
    #             "Team": "NYG",
    #             "Opponent": "IND",
    #             "Game": "NYG@IND",
    #             "Time": "1:00PM EST",
    #             PLAYER_SALARY: 26,
    #             PLAYER_POINTS_PROJECTION: 16.0,
    #             "Injury Status": "Q",
    #             "Starting": "No",
    #             "player_name": "Odell Beckham Jr.",
    #             "eman_reyalp": "Beckham Jr. Odell"
    #         },
    #         "nfl.p.30972": {
    #             "First Name": "Saquon",
    #             "Last Name": "Barkley",
    #             PLAYER_POSITION: "RB",
    #             "Team": "NYG",
    #             "Opponent": "IND",
    #             "Game": "NYG@IND",
    #             "Time": "1:00PM EST",
    #             PLAYER_SALARY: 36,
    #             PLAYER_POINTS_PROJECTION: 21.6,
    #             "Injury Status": " ",
    #             "Starting": "No",
    #             "player_name": "Saquon Barkley",
    #             "eman_reyalp": "Barkley Saquon"
    #         },
    #         "nfl.p.6760": {
    #             "First Name": "Eli",
    #             "Last Name": "Manning",
    #             PLAYER_POSITION: "QB",
    #             "Team": "NYG",
    #             "Opponent": "IND",
    #             "Game": "NYG@IND",
    #             "Time": "1:00PM EST",
    #             PLAYER_SALARY: 25,
    #             PLAYER_POINTS_PROJECTION: 15.0,
    #             "Injury Status": " ",
    #             "Starting": "No",
    #             "player_name": "Eli Manning",
    #             "eman_reyalp": "Manning Eli"
    #         }
    #     }
    #     self.assertDictEqual(correct, result)
    #
    # def test_import_csv_from_not_csv(self):
    #     with patch('os.path.isfile') as mock_isfile:
    #         mock_isfile.return_value = True
    #         with patch('builtins.open',
    #                    mock_open(read_data='Id,First Name,Last Name,Position,'
    #                                        'Team,Opponent,Game,Time,Salary,'
    #                                        'FPPG,Injury Status,Starting\n'
    #                                        'nfl.p.27540,Odell,Beckham Jr.,WR,'
    #                                        'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
    #                                        'Q,No\n'
    #                                        'nfl.p.30972,Saquon,Barkley,RB,NYG,'
    #                                        'IND,NYG@IND,1:00PM EST,36,21.6,\" '
    #                                        '\",No\n'
    #                                        'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
    #                                        'NYG@IND,1:00PM EST,25,15.0,'
    #                                        '\" \",No')):
    #             self.assertRaises(ValueError,
    #                               DfsOptimizer.import_csv, 'testcsv', 'Id',
    #                               {'FPPG': np.float, 'Salary': np.int}, None,
    #                               None, None)
    #
    # def import_csv_from_nonexistent_file(self):
    #     with patch('os.path.isfile') as mock_isfile:
    #         mock_isfile.return_value = False
    #         with patch('builtins.open',
    #                    mock_open(read_data='Id,First Name,Last Name,Position,'
    #                                        'Team,Opponent,Game,Time,Salary,'
    #                                        'FPPG,Injury Status,Starting\n'
    #                                        'nfl.p.27540,Odell,Beckham Jr.,WR,'
    #                                        'NYG,IND,NYG@IND,1:00PM EST,26,16.0,'
    #                                        'Q,No\n'
    #                                        'nfl.p.30972,Saquon,Barkley,RB,NYG,'
    #                                        'IND,NYG@IND,1:00PM EST,36,21.6,\" '
    #                                        '\",No\n'
    #                                        'nfl.p.6760,Eli,Manning,QB,NYG,IND,'
    #                                        'NYG@IND,1:00PM EST,25,15.0,'
    #                                        '\" \",No')):
    #             self.assertRaises(RuntimeError,
    #                               DfsOptimizer.import_csv, 'test.csv', 'Id',
    #                               {'FPPG': np.float, 'Salary': np.int}, None,
    #                               None, None)


if __name__ == '__main__':
    unittest.main()
