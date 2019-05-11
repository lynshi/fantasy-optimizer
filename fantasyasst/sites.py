from enum import Enum

from fantasyasst.player import Player


class Site(Enum):
    YAHOO = 'Yahoo'


class Yahoo:
    """ NFL """
    NFL_POSITIONS = {
        'QB': 1,
        'RB': 2,
        'WR': 3,
        'TE': 1,
        'DEF': 1
    }
    NFL_BUDGET = 200
    NFL_FLEX_POSITIONS = {'FLEX': ({'RB', 'WR', 'TE'}, 1)}
    NFL_PLAYER_IGNORE_CONDITIONS = [
        (Player.INJURY_STATUS, 'O'),
        (Player.INJURY_STATUS, 'IR'),
        (Player.INJURY_STATUS, 'D')
    ]
    NFL_UTILITY_POSITIONS = 0

    """ NBA """
    NBA_POSITIONS = {
        'PG': 1,
        'SG': 1,
        'SF': 1,
        'PF': 1,
        'C': 1
    }
    NBA_BUDGET = 200
    NBA_FLEX_POSITIONS = {
        'G': ({'PG', 'SG'}, 1),
        'F': ({'SF', 'PF'}, 1)
    }
    NBA_PLAYER_IGNORE_CONDITIONS = [
        (Player.INJURY_STATUS, 'O'),
        (Player.INJURY_STATUS, 'INJ'),
        (Player.INJURY_STATUS, 'OFS')
    ]
    NBA_UTILITY_POSITIONS = 1
