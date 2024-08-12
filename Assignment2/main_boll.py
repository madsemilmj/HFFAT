from fastapi import FastAPI
from basic_bollinger_bot import *

app = FastAPI()
robot = BollingerRobot()

@app.get("/signal/")
async def read_indicators(price_curr, price_prev, boll_top_curr, boll_top_prev, boll_bot_curr, boll_bot_prev):
    global robot
    processed_args = map(lambda x: float(x.replace(",", ".")), [
        price_curr, price_prev, boll_top_curr, boll_top_prev, boll_bot_curr, boll_bot_prev
    ])
    return robot.on_bar(*processed_args)

# To run:
# uvicorn main_boll:app --reload