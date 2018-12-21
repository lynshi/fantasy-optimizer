from abc import ABC
import pulp

from fantasyasst.constants import *


class DfsOptimizer(ABC):
    def __init__(self, players, positions, budget):
        """
        Construct IP model for player selection optimization

        :param players:  dictionary of dictionaries representing players
        :type players: dict
        :param positions: dictionary of position -> limit
        :type positions: dict
        :param budget: budget for player selection
        :type budget: int
        """

        self.player_variables = pulp.LpVariable.dict('', players.keys(),
                                                     lowBound=0, upBound=1,
                                                     cat='Integer')

