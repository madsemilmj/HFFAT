import numpy as np
from fastapi import FastAPI, Query

app = FastAPI()

class TradingStrategy:
    def __init__(self):
        self.prev_dc_events = []
        self.prev_os_events = []
        self.prev_profits = []
        self.prev_open_events = []
        self.prev_take_profit_events = []
        self.prev_stop_loss_events = []
        self.prev_prices = []
        
        self.dc_events = []
        self.os_events = []
        self.profits = []
        self.open_events = []
        self.take_profit_events = []
        self.stop_loss_events = []
        self.prices = []
        
        self.threshold = -0.4
        self.theta = 0.001
        
        self.extreme_price = None
        self.signal = None
        self.trend = None
        self.theta = None
        self.last_low = None
        self.last_high = None 
        self.open_price = None
        self.has_open_position = False
        self.open_price = None
        
        self.counter = 0

    def detect_trend(self, tickprice):
        trend = None
        if (self.extreme_price * (1 + self.theta)) <= tickprice:
            trend = 'up'
        elif (self.extreme_price * (1 - self.theta)) >= tickprice:
            trend = 'down'
        return trend
    
    def increment_counter(self):
        self.counter += 1
        
    def reset_parameters(self):
        self.extreme_price = None
        self.max_uptrend_osv = 0
        self.max_downtrend_osv = 0
        self.signal = None
        self.trend = None
        self.theta = None
        self.last_low = None
        self.last_high = None 
        self.open_price = None
        self.dc_events = []
        self.os_events = []
        self.profits = []
        self.open_events = []
        self.take_profit_events = []
        self.stop_loss_events = []
        self.has_open_position = False
        self.open_price = None
        self.prices = []
        self.counter = 0

strategy = TradingStrategy()

@app.get("/signal/{tickprice}/theta")
async def read_price(tickprice, theta = Query(...)):
    if not isinstance(tickprice, float):
        tickprice = float(tickprice.replace(',', '.'))
    
    if not isinstance(theta, float):
        theta = float(theta.replace(',', '.'))
    
    if not strategy.theta:
        strategy.theta = theta
    
    strategy.signal = 'hold'
    strategy.prices.append([strategy.counter, tickprice])

    if not strategy.trend:
        if not strategy.extreme_price:
            strategy.extreme_price = tickprice
            strategy.last_high = [0, tickprice]
            strategy.last_low = [0, tickprice]
            strategy.dc_events.append([0, tickprice])
            print(f'First price is {tickprice}')
            
        strategy.trend = strategy.detect_trend(tickprice)
        
        if strategy.trend:
            print(f'First trend is {strategy.trend} @ {tickprice}')
            strategy.dc_events.append([strategy.counter, tickprice])
    
    elif strategy.trend == 'down':
        if strategy.last_low[1] > tickprice:
            strategy.last_low = [strategy.counter, tickprice]
            
        p_ext = strategy.dc_events[-1][1]
        p_dcc = p_ext * (1 - strategy.theta)
    
        osv = ((tickprice - p_dcc) / p_dcc) / strategy.theta
        
        if ((osv <= strategy.threshold) and (not strategy.has_open_position)):
            strategy.signal = 'buy'
            strategy.has_open_position = True
            print(f'Position opened @ {tickprice}')
            strategy.open_price = tickprice
            strategy.open_events.append([strategy.counter, strategy.open_price])

        if tickprice >= strategy.last_low[1] * (1 + strategy.theta):
            print(f'Trend changed to up')
            strategy.trend = 'up'
            strategy.dc_events.append([strategy.counter, tickprice])
            strategy.os_events.append(strategy.last_low)
            strategy.last_high = [strategy.counter, tickprice]
            
            if strategy.has_open_position:
                strategy.signal = 'sell'
                strategy.has_open_position = False
                
                if tickprice > strategy.open_price:
                    strategy.take_profit_events.append([strategy.counter, tickprice])
                    print(f'Took profit @ {tickprice}')
                else:
                    strategy.stop_loss_events.append([strategy.counter, tickprice])
                    print(f'Stopped Loss @ {tickprice}')
    
    elif strategy.trend == 'up':
        if strategy.last_high[1] < tickprice:
            strategy.last_high = [strategy.counter, tickprice]
            
        if tickprice <= strategy.last_high[1] * (1 - strategy.theta):
            strategy.dc_events.append([strategy.counter, tickprice])
            strategy.os_events.append(strategy.last_high)
            strategy.trend = 'down'
            strategy.last_low = [strategy.counter, tickprice]
            
            if strategy.has_open_position:
                strategy.signal = 'sell'
                strategy.has_open_position = False
                
                if tickprice > strategy.open_price:
                    strategy.take_profit_events.append([strategy.counter, tickprice])
                    print(f'Took profit @ {tickprice}')
                else:
                    strategy.stop_loss_events.append([strategy.counter, tickprice])
                    print(f'Stopped Loss @ {tickprice}')
            
    strategy.increment_counter()
        
    return {"tradeSignal": strategy.signal}

@app.get("/get_data")
async def read_data():
    return {
        "prices": strategy.prev_prices,
        "dc_events": strategy.prev_dc_events,
        "os_events": strategy.prev_os_events,
        "open_events": strategy.prev_open_events,
        "take_profit_events": strategy.prev_take_profit_events,
        "stop_loss_events": strategy.prev_stop_loss_events,
        "profits": strategy.prev_profits,
    }
    
@app.get("/resetparameters")
async def reset_parameters():
    strategy.prev_dc_events = strategy.dc_events
    strategy.prev_os_events = strategy.os_events
    strategy.prev_profits = strategy.profits
    strategy.prev_open_events = strategy.open_events
    strategy.prev_take_profit_events = strategy.take_profit_events
    strategy.prev_stop_loss_events = strategy.stop_loss_events
    strategy.prev_prices = strategy.prices
    
    strategy.reset_parameters()