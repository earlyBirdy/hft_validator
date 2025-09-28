import json, os
from app.data import load_prices_csv
from app.strategies.auto_select import smart_choose_and_run
def handler(event, context):
    prices=load_prices_csv(os.environ.get("DATA_PATH","data/sample_prices.csv"))
    chosen=smart_choose_and_run(prices)
    return {"statusCode":200,"headers":{"Content-Type":"application/json"},
            "body": json.dumps({"decision":{"strategy":chosen["strategy"],"params":chosen["params"],"features":chosen["features"]}})}
