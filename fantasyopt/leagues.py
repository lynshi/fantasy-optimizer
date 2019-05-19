from enum import Enum


class League(Enum):
    NBA = 'NBA'
    NFL = 'NFL'
    MLB = 'MLB'


LEAGUE_TEAMS = {
    League.NBA: ['SAS', 'NOP', 'PHO', 'POR', 'OKC', 'LAL', 'DAL', 'DEN', 'TOR',
                 'BOS', 'MIL', 'IND', 'MIN', 'ATL', 'HOU', 'LAC', 'UTA', 'MEM',
                 'NYK', 'BRK', 'DET', 'CLE', 'SAC', 'MIA', 'ORL', 'CHO', 'CHI',
                 'PHI', 'WAS', 'GSW']
}
