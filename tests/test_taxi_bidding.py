import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from taxi import Taxi, FareInfo


class FakeNode:
    def __init__(self, index):
        self.index = index


class FakeWorld:
    def __init__(self, times=None, sim_time=10):
        self.simTime = sim_time
        self.times = times or {}
        self.nodes = {(i, 0): FakeNode((i, 0)) for i in range(4)}

    def getNode(self, x, y):
        return self.nodes.get((x, y))

    def travelTime(self, start, end):
        if start is None or end is None:
            return -1
        return self.times.get((start.index, end.index), abs(start.index[0] - end.index[0]))


def make_taxi(times=None, account=100, sim_time=10, max_wait=50):
    world = FakeWorld(times=times, sim_time=sim_time)
    taxi = Taxi.__new__(Taxi)
    taxi._world = world
    taxi._loc = world.getNode(0, 0)
    taxi._passenger = None
    taxi._availableFares = {}
    taxi._account = account
    taxi._maxFareWait = max_wait
    return taxi


class TaxiBiddingTests(unittest.TestCase):
    def test_bids_on_profitable_fare_with_nearby_pickup(self):
        taxi = make_taxi(times={(((0, 0)), ((1, 0))): 2,
                                (((1, 0)), ((3, 0))): 10})
        self.assertTrue(taxi._bidOnFare(10, (1, 0), (3, 0), 40))

    def test_declines_fare_with_negative_expected_return(self):
        taxi = make_taxi(times={(((0, 0)), ((1, 0))): 10,
                                (((1, 0)), ((3, 0))): 30})
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 20))

    def test_declines_if_already_carrying_passenger(self):
        taxi = make_taxi()
        taxi._passenger = object()
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 100))

    def test_declines_if_another_fare_is_allocated(self):
        taxi = make_taxi()
        taxi._availableFares[(5, 1, 0)] = FareInfo((3, 0), 100)
        taxi._availableFares[(5, 1, 0)].allocated = True
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 100))

    def test_declines_unreachable_trip(self):
        taxi = make_taxi(times={(((0, 0)), ((1, 0))): -1,
                                (((1, 0)), ((3, 0))): 10})
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 100))

    def test_declines_when_pickup_window_has_expired(self):
        taxi = make_taxi(sim_time=60, max_wait=50)
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 100))

    def test_declines_when_taxi_cannot_reach_before_wait_limit(self):
        taxi = make_taxi(times={(((0, 0)), ((1, 0))): 45,
                                (((1, 0)), ((3, 0))): 5}, max_wait=50)
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 100))

    def test_declines_if_account_cannot_fund_approach(self):
        taxi = make_taxi(account=2, times={(((0, 0)), ((1, 0))): 3,
                                           (((1, 0)), ((3, 0))): 5})
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 100))

    def test_declines_non_finite_travel_time(self):
        taxi = make_taxi(times={(((0, 0)), ((1, 0))): math.inf,
                                (((1, 0)), ((3, 0))): 5})
        self.assertFalse(taxi._bidOnFare(10, (1, 0), (3, 0), 100))

    def test_zero_minute_pickup_is_allowed_if_expected_return_is_positive(self):
        taxi = make_taxi(times={(((0, 0)), ((1, 0))): 0,
                                (((1, 0)), ((3, 0))): 10})
        self.assertTrue(taxi._bidOnFare(10, (1, 0), (3, 0), 30))


if __name__ == '__main__':
    unittest.main(verbosity=2)
