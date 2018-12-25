import sys

from fantasyasst import *
import fantasyasst.loader.yahoo as yh
from fantasyasst.optimizer.dfs import DfsOptimizer


def optimize_lineup(site, csv_location):
    if site not in SITE_DEFAULTS:
        raise ValueError('Unsupported site ' + site)
    ignore_conditions = {(Player.INJURY_STATUS, 'Q')}
    ignore_conditions.update(
        SITE_DEFAULTS[site].NFL_PLAYER_IGNORE_CONDITIONS)

    optimizer = DfsOptimizer(load_players(site, csv_location,
                                          ignore_conditions).get_player_dict(),
                             SITE_DEFAULTS[site].NFL_POSITIONS,
                             SITE_DEFAULTS[site].NFL_BUDGET,
                             SITE_DEFAULTS[site].NFL_FLEX_POSITIONS,
                             SITE_DEFAULTS[site].NFL_UTILITY_POSITIONS)

    players = input('Enter players to require [First Last].\n\t'
                    'If multiple players,'
                    ' use a comma-separated list\n\t'
                    '(e.g. Patrick Mahomes,Saquon Barkley): ')
    players += 'George Kittle'
    if players != '':
        for p in players.split(','):
            optimizer.require_player(p)

    players = input('Enter players to ignore [First Last].\n\t'
                    'If multiple players,'
                    ' use a comma-separated list\n\t'
                    '(e.g. Nathan Peterman,Steven Ridley): ')
    players += 'Ryan Fitzpatrick,Stevan Ridley,Kirk Cousins,' \
               'Charcandrick West,Ted Ginn Jr.,Mitchell Trubisky,' \
               'C.J. Beathard,Allen Robinson II,Matt Barkley,' \
               'Josh Johnson,John Brown,Adrian Peterson'
    if players != '':
        for p in players.split(','):
            optimizer.ignore_player(p)

    teams = input('Enter teams to ignore.\n\tIf multiple teams,'
                  ' use a comma-separated list\n\t(e.g. TB,MIA): ')
    teams += 'JAX,CAR,MIA,MIN,CLE,NYG,PHI'
    if teams != '':
        for t in teams.split(','):
            optimizer.ignore_team(t)

    maximum = input('Enter the maximum allowed number of players '
                    'allowed from a team.\n\t'
                    'If no preference, enter nothing: ')
    if maximum != '':
        optimizer.set_max_players_from_same_team(str(maximum))

    optimizer.generate_lineup()


def load_players(site, csv_location, ignore_conditions):
    loaders = {
        Site.YAHOO: yh.nfl.NflLoader
    }

    if site not in loaders:
        raise ValueError('Unsupported site for loading: ' + site)

    return loaders[site].load_players(csv_location, ignore_conditions)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python -m bin.optimize_nfl.py [site name] [csv location]')
        exit(1)

    optimize_lineup(sys.argv[1], sys.argv[2])
