"""Failure-oriented checks for the demo evaluator; no simulator required."""
import copy
import unittest

from metrics import MODELS, TARGET, evaluate


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.initial = {n:[-.2,.3,0,0,0,0,1] for n in MODELS}
        self.initial[MODELS[1]] = [float(TARGET[0]),float(TARGET[1]),0,0,0,0,1]
        self.samples = []
        for i in range(101):
            poses = copy.deepcopy(self.initial)
            if i < 45: poses[MODELS[1]][2] = .13
            self.samples.append({'t':i*.1,'poses':poses})

    def test_nominal_release(self):
        self.assertTrue(evaluate(self.samples,self.initial,6)['passed'])

    def test_bystander_moves_then_returns(self):
        self.samples[20]['poses'][MODELS[0]][0] += .03
        self.assertFalse(evaluate(self.samples,self.initial,6)['passed'])

    def test_short_or_missing_observation(self):
        self.assertFalse(evaluate(self.samples[:80],self.initial,6)['passed'])
        self.assertFalse(evaluate(self.samples[:75]+self.samples[85:],self.initial,6)['passed'])

    def test_tipped_battery(self):
        self.samples[-1]['poses'][MODELS[1]][3:] = [1,0,0,0]
        self.assertFalse(evaluate(self.samples,self.initial,6)['passed'])

    def test_drop_outside_target(self):
        for s in self.samples[60:]: s['poses'][MODELS[1]][0] += .1
        self.assertFalse(evaluate(self.samples,self.initial,6)['passed'])


if __name__ == '__main__':
    unittest.main()
