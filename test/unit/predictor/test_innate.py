import unittest

from fantasyasst import *
from fantasyasst.predictor.innate import AbilityApproximator


class TestInnate(unittest.TestCase):
    def setUp(self):
        self.approximators = {}
        for league in League:
            if league != League.NBA:
                continue
            self.approximators[league] = AbilityApproximator(league, 2019,
                                                             15, 5)

    def test_approximation(self):
        pass
