
import os, json, random
from visualize_metrics import run_pipeline

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ABS_RESULTS = os.path.join(BASE, 'results')
ABS_AWS = os.path.join(BASE, 'aws')

def score(metrics):
    agent = metrics['agent']
    return (
        agent['sharpe_like']
        - 0.30 * agent['fsr']
        - 0.0010 * agent['trades']
        + 0.00005 * agent['total_pnl']
    )

def random_search(iters=10, seed=42, n_ticks=3500, baseline_latency=5, agent_latency=2,
                  cost_bps=0.8, slip_bps=0.5, out_json=None):
    random.seed(seed)
    best = None
    best_score = -1e9
    for _ in range(iters):
        params = {
            'ewma_alpha': random.uniform(0.02, 0.10),
            'ewma_z': random.uniform(2.2, 3.2),
            'vol_window': random.randint(30, 120),
            'vol_max': random.uniform(0.005, 0.015),
            'persist_hold': random.randint(3, 6),
            'persist_mean_alpha': random.uniform(0.02, 0.10),
            'persist_z': random.uniform(0.18, 0.4),
            'pos_calm': random.uniform(0.6, 1.0),
            'pos_volatile': random.uniform(0.3, 0.6),
            'pos_jumpy': random.uniform(0.2, 0.5),
            'min_interval_ticks': random.randint(5, 10),
            'max_trades_per_100': random.randint(10, 18),
            'confirm': random.randint(2, 3),
        }
        metrics = run_pipeline(
            n_ticks=n_ticks,
            baseline_latency=baseline_latency, agent_latency=agent_latency,
            cost_bps=cost_bps, slip_bps=slip_bps,
            generate_artifacts=False,
            out_dir=ABS_RESULTS, logs_path=os.path.join(ABS_AWS, 'reasoning_logs.jsonl'),
            **params
        )
        s = score(metrics)
        if s > best_score:
            best_score = s
            best = {'score': s, 'params': params, 'metrics': metrics['agent']}
    if best:
        os.makedirs(ABS_RESULTS, exist_ok=True)
        out_path = out_json or os.path.join(ABS_RESULTS, 'best_params.json')
        with open(out_path, 'w') as f:
            json.dump(best, f, indent=2)
    return best

if __name__ == '__main__':
    result = random_search()
    print('Best:', json.dumps(result, indent=2))
