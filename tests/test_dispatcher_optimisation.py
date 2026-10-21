import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dispatcher import Dispatcher, FareEntry


class FakeTaxi:
    def __init__(self, location, on_duty=True, name='taxi'):
        self.currentLocation = location
        self.onDuty = on_duty
        self.name = name

    def __repr__(self):
        return self.name


class FakeWorld:
    def __init__(self, graph, sim_time=10):
        self.graph = graph
        self.simTime = sim_time
        self.allocations = []

    def getNode(self, x, y):
        point = (x, y)
        return point if point in self.graph else None

    def distance2Node(self, a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    def allocateFare(self, origin, taxi):
        self.allocations.append((origin, taxi))

    def travelTime(self, a, b):
        return self.distance2Node(a, b)


def make_graph():
    # Weighted road graph: 0--1--2 is cheap; 0--2 direct is expensive.
    return {
        (0, 0): {(1, 0): (0, 1.0), (2, 0): (1, 9.0)},
        (1, 0): {(0, 0): (2, 1.0), (2, 0): (0, 1.0)},
        (2, 0): {(1, 0): (2, 1.0), (0, 0): (3, 9.0)},
        (10, 0): {},
    }


class DispatcherOptimisationTests(unittest.TestCase):
    def setUp(self):
        self.graph = make_graph()
        self.world = FakeWorld(self.graph, sim_time=10)
        self.near = FakeTaxi((1, 0), name='near')
        self.far = FakeTaxi((0, 0), name='far')
        self.dispatcher = Dispatcher(self.world, [self.near, self.far], self.graph)

    def add_fare(self, bidders, origin=(2, 0), destination=(0, 0), calltime=6):
        entry = FareEntry(origin, destination, calltime)
        entry.bidders = list(bidders)
        self.dispatcher._fareBoard.setdefault(origin, {}).setdefault(destination, {})[calltime] = entry
        return entry

    def test_route_distance_uses_lowest_cost_road_route(self):
        self.assertAlmostEqual(self.dispatcher._routeDistance((0, 0), (2, 0)), 2.0)

    def test_route_distance_returns_infinity_for_unreachable_nodes(self):
        self.assertEqual(self.dispatcher._routeDistance((0, 0), (10, 0)), float('inf'))

    def test_price_is_bounded_and_increases_with_trip_distance(self):
        short = FareEntry((0, 0), (1, 0), 0)
        long = FareEntry((0, 0), (2, 0), 0)
        short_price = self.dispatcher._costFare(short)
        long_price = self.dispatcher._costFare(long)
        self.assertGreaterEqual(short_price, 2.0)
        self.assertLessEqual(short_price, 120.0)
        self.assertLessEqual(long_price, 120.0)
        self.assertGreater(long_price, short_price)

    def test_allocation_waits_for_initial_bid_window(self):
        entry = self.add_fare([0, 1], calltime=9)
        self.world.simTime = 10
        self.dispatcher._allocateFare((2, 0), (0, 0), 9)
        self.assertEqual(entry.taxi, -1)
        self.assertEqual(self.world.allocations, [])

    def test_selects_shortest_approach_when_fairness_is_equal(self):
        # taxi 0 at (1,0) is one unit from pickup; taxi 1 at (0,0) is two units away.
        entry = self.add_fare([0, 1], calltime=6)
        self.dispatcher._allocateFare((2, 0), (0, 0), 6)
        self.assertEqual(entry.taxi, 0)
        self.assertEqual(self.world.allocations[-1][1], self.near)

    def test_fairness_breaks_near_tie_in_favour_of_less_used_taxi(self):
        self.dispatcher._allocationCount[self.near] = 2
        self.dispatcher._allocationCount[self.far] = 0
        # Both are bidders; difference in approach is small enough for fairness to matter.
        self.near.currentLocation = (1, 0)
        self.far.currentLocation = (0, 0)
        entry = self.add_fare([0, 1], origin=(1, 0), destination=(2, 0), calltime=6)
        self.dispatcher._allocateFare((1, 0), (2, 0), 6)
        self.assertEqual(entry.taxi, 1)
        self.assertEqual(self.world.allocations[-1][1], self.far)

    def test_ignores_off_duty_and_unreachable_bidders(self):
        self.near.onDuty = False
        self.far.currentLocation = (10, 0)  # disconnected from pickup
        entry = self.add_fare([0, 1], origin=(2, 0), destination=(0, 0), calltime=6)
        self.dispatcher._allocateFare((2, 0), (0, 0), 6)
        self.assertEqual(entry.taxi, -1)
        self.assertEqual(self.world.allocations, [])

    def test_duplicate_bid_indices_do_not_affect_selection(self):
        entry = self.add_fare([0, 0, 0, 1, 1], calltime=6)
        self.dispatcher._allocateFare((2, 0), (0, 0), 6)
        self.assertEqual(entry.taxi, 0)
        self.assertEqual(len(self.world.allocations), 1)

    def test_invalid_fare_location_does_not_allocate(self):
        entry = self.add_fare([0, 1], origin=(99, 99), destination=(0, 0), calltime=6)
        self.dispatcher._allocateFare((99, 99), (0, 0), 6)
        self.assertEqual(entry.taxi, -1)
        self.assertEqual(self.world.allocations, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
