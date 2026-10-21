# Robo-Uber coursework task sequence

- Task 1a: baseline evaluation.
- Task 1b: taxi path planning (`Taxi._planPath`) — Week 2 work.
- Task 2a: dispatcher allocation (`Dispatcher._allocateFare`) — Week 3 work.
- Task 2b: dispatcher pricing (`Dispatcher._costFare`) — Week 3 work.
- Task 3a: taxi bidding (`Taxi._bidOnFare`) — Week 4 work.

## Snapshot roles
- `baseline_src/`: original starter algorithms.
- `baseline_dispatcher_src/`: Dijkstra path planner + original dispatcher.
- `allocation_only_src/`: Dijkstra + improved allocation, original pricing.
- `cost_only_src/`: Dijkstra + original allocation, improved pricing.
- `baseline_bidding_src/`: combined Week 2 + Week 3 version before the Task 3a bidding change.
- `src/`: current combined implementation, including the Task 3a bidding improvement.
