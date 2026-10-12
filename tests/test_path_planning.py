import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from taxi import Taxi


def make_taxi(graph):
    taxi = Taxi.__new__(Taxi)
    taxi._map = graph
    taxi._onDutyPos = (0, 0)
    return taxi


class DijkstraPathPlanningTests(unittest.TestCase):
    def test_direct_route(self):
        graph = {(0, 0): {(1, 0): (0, 1.0)}, (1, 0): {(0, 0): (2, 1.0)}}
        self.assertEqual(make_taxi(graph)._planPath((0, 0), (1, 0)), [(0, 0), (1, 0)])

    def test_selects_minimum_total_distance_not_fewest_edges(self):
        graph = {
            (0, 0): {(1, 0): (0, 10.0), (0, 1): (1, 1.0)},
            (1, 0): {(0, 0): (2, 10.0), (1, 1): (1, 10.0)},
            (0, 1): {(0, 0): (3, 1.0), (1, 1): (0, 1.0)},
            (1, 1): {(0, 1): (2, 1.0), (1, 0): (3, 10.0), (2, 1): (0, 1.0)},
            (2, 1): {(1, 1): (2, 1.0)},
        }
        route = make_taxi(graph)._planPath((0, 0), (2, 1))
        self.assertEqual(route, [(0, 0), (0, 1), (1, 1), (2, 1)])
        self.assertAlmostEqual(sum(graph[a][b][1] for a, b in zip(route, route[1:])), 3.0)

    def test_avoids_blocked_or_removed_direct_edge(self):
        graph = {
            (0, 0): {(1, 0): (0, 1.0), (0, 1): (1, 1.0)},
            (1, 0): {(0, 0): (2, 1.0), (1, 1): (1, 1.0)},
            (0, 1): {(0, 0): (3, 1.0), (1, 1): (0, 1.0)},
            (1, 1): {(0, 1): (2, 1.0), (1, 0): (3, 1.0)},
        }
        del graph[(0, 0)][(1, 0)]
        route = make_taxi(graph)._planPath((0, 0), (1, 0))
        self.assertEqual(route, [(0, 0), (0, 1), (1, 1), (1, 0)])
        self.assertTrue(all(b in graph[a] for a, b in zip(route, route[1:])))

    def test_unreachable_destination_returns_empty_path(self):
        graph = {(0, 0): {}, (1, 0): {}}
        self.assertEqual(make_taxi(graph)._planPath((0, 0), (1, 0)), [])

    def test_same_origin_and_destination(self):
        graph = {(0, 0): {}}
        self.assertEqual(make_taxi(graph)._planPath((0, 0), (0, 0)), [(0, 0)])

    def test_unknown_node_returns_empty_path(self):
        graph = {(0, 0): {}}
        self.assertEqual(make_taxi(graph)._planPath((0, 0), (99, 99)), [])

    def test_missing_origin_preserves_starter_convention(self):
        taxi = make_taxi({})
        taxi._onDutyPos = (4, 5)
        self.assertEqual(taxi._planPath(None, (2, 2)), [(4, 5)])

    def test_route_edges_are_valid(self):
        graph = {
            (0, 0): {(1, 0): (0, 2.0)},
            (1, 0): {(0, 0): (2, 2.0), (2, 0): (0, 3.0)},
            (2, 0): {(1, 0): (2, 3.0)},
        }
        route = make_taxi(graph)._planPath((0, 0), (2, 0))
        self.assertTrue(all(b in graph[a] for a, b in zip(route, route[1:])))
        self.assertEqual(route[0], (0, 0))
        self.assertEqual(route[-1], (2, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
