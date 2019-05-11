import sys

from fantasyasst import *
import fantasyasst.loader.yahoo as yh
from fantasyasst.optimizer.dfs import DfsOptimizer


def optimize_lineup(site, csv_location):
    if site not in SITE_DEFAULTS:
        raise ValueError('Unsupported site ' + site)
    ignore_conditions = {(Player.INJURY_STATUS, 'Q')}
    ignore_conditions.update(
        SITE_DEFAULTS[site].NBA_PLAYER_IGNORE_CONDITIONS)

    optimizer = DfsOptimizer(load_players(site, csv_location,
                                          ignore_conditions).get_player_dict(),
                             SITE_DEFAULTS[site].NBA_POSITIONS,
                             SITE_DEFAULTS[site].NBA_BUDGET,
                             SITE_DEFAULTS[site].NBA_FLEX_POSITIONS,
                             SITE_DEFAULTS[site].NBA_UTILITY_POSITIONS)
    optimizer.generate_lineup()


def load_players(site, csv_location, ignore_conditions):
    loaders = {
        Site.YAHOO: yh.nba.NbaLoader
    }

    if site not in loaders:
        raise ValueError('Unsupported site for loading: ' + site)

    return loaders[site].load_players(csv_location, ignore_conditions)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python -m bin.optimize_nfl.py [site name] [csv location]')
        exit(1)

    optimize_lineup(sys.argv[1], sys.argv[2])
