# Week 4 experiment manifest

Three 1,440-tick trials per configuration; seed labels 20261013–20261015. The same seed labels are used, but model changes can alter random-number consumption, so the runs are not perfectly paired.

| Label | Source | Traffic | Raw CSV | Duty series |
|---|---|---|---|---|
| baseline_no_traffic | `baseline_bidding_src/` | off | `baseline_no_traffic_raw.csv` | `baseline_no_traffic_duty_timeseries.csv` |
| improved_no_traffic | `src/` | off | `improved_no_traffic_raw.csv` | `improved_no_traffic_duty_timeseries.csv` |
| baseline_traffic | `baseline_bidding_src/` | on | `baseline_traffic_raw.csv` | `baseline_traffic_duty_timeseries.csv` |
| improved_traffic | `src/` | on | `improved_traffic_raw.csv` | `improved_traffic_duty_timeseries.csv` |

## Interpretation
- The improved policy has higher mean completed fares and joint return in both traffic conditions in this three-trial sample.
- Cancellation rate remains high (about 86–89%) and is slightly higher for the improved policy in this sample.
- These are preliminary results: use at least five trials per condition for stronger evidence before making a final coursework claim.
- The policy uses a uniform-survival approximation and 15% pickup / 25% trip cost safety margins; these are explicit heuristics, not a learned probability model.
