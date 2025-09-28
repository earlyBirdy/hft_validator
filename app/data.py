import csv
def load_prices_csv(path):
    with open(path,'r') as f:
        r=csv.DictReader(f)
        return [(row['time'], float(row['price'])) for row in r]
