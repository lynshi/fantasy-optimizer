class Site:
    YAHOO = 'Yahoo'


class Yahoo:
    # NFL
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
