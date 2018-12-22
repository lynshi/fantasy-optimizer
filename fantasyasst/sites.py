class Site:
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
        ('Injury Status', 'O'),
        ('Injury Status', 'IR'),
        ('Injury Status', 'D')
    ]

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
        ('Injury Status', 'O'),
        ('Injury Status', 'INJ'),
        ('Injury Status', 'OFS')
    ]
    NBA_UTILITY_POSITIONS = 1
