"""Run Task 3a taxi-bidding comparisons in clear and traffic-on conditions.

Run from the project root: python run_week4_experiments.py
Optional: python run_week4_experiments.py --trials 5 --seed-start 20261013
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--seed-start', type=int, default=20261013)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error('--trials must be at least 1')

    runs = [
        ('baseline_bidding_src', 'baseline_no_traffic', False),
        ('src', 'improved_no_traffic', False),
        ('baseline_bidding_src', 'baseline_traffic', True),
        ('src', 'improved_traffic', True),
    ]
    for source, label, traffic in runs:
        env = os.environ.copy()
        env.update({
            'ROBO_SRC': source,
            'ROBO_LABEL': label,
            'ROBO_TRIALS': str(args.trials),
            'ROBO_SEED_START': str(args.seed_start),
            'ROBO_TRAFFIC': '1' if traffic else '0',
            'ROBO_OUTDIR': os.path.join('results', 'week4_taxi_bidding'),
            # Stabilise hash-based iteration order between fresh processes.
            'PYTHONHASHSEED': '0',
        })
        print(f"\n=== {label}: source={source}, traffic={'on' if traffic else 'off'} ===", flush=True)
        subprocess.run([sys.executable, os.path.join(HERE, 'run_trials.py')], cwd=HERE, env=env, check=True)
    print('\nAll Week 4 runs completed. Results: results/week4_taxi_bidding/', flush=True)


if __name__ == '__main__':
    main()
