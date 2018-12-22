import sys

import fantasyasst.optimizer.yahoo as yh


def optimize_lineup(site, csv_location):
    optimizers = {
        'Yahoo': yh.nfl.NflDfsOptimizer
    }

    if site not in optimizers:
        raise ValueError('Unsupported site ' + site)

    optimizer = optimizers[site].load_instance_from_csv(csv_location)
    optimizer.generate_lineup()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python -m bin.optimize_nfl.py [site name] [csv location]')
        exit(1)

    optimize_lineup(sys.argv[1], sys.argv[2])
