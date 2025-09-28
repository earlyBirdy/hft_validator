from app.data import load_prices_csv
from app.strategies.auto_select import smart_choose_and_run

def test_runs():
    prices=load_prices_csv('data/sample_prices.csv')
    out=smart_choose_and_run(prices)
    assert 'strategy' in out and 'params' in out and 'metrics' in out
