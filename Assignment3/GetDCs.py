from fastapi import FastAPI
import json
app = FastAPI()
buffer = []
max_length = 30
minprice = 10000000
maxprice = -10
mindate = ""
maxdate = ""
direction = "down"
pdcc_up = 0
pdcc_down = 0
upward_trends = []
downward_trends = []


@app.get("/signal/{tickprice}/{date}/{threshold}")
async def read_price(tickprice,date,threshold):
    global buffer
    global max_length
    global direction
    global minprice
    global maxprice
    global mindate
    global maxdate
    global theta
    global pdcc_up
    global pdcc_down
    global upward_trends
    global downward_trends
    
    current_price = float(tickprice.replace(",","."))
    theta = float(threshold.replace(",","."))
    buffer = append_with_limit(buffer,current_price,max_length)
    if direction == 'up':
        
        minprice,direction,mindate = identifyUpwardDC(current_price, minprice,mindate,theta,date)
        if direction == 'up':
            return {"tradeSignal": 'hold'}
        else:
            signal = 'buy'
            return {"tradeSignal": signal}
    
    if direction == 'down':
        
        maxprice,direction,maxdate = identifyDownwardDC(current_price, maxprice,maxdate,theta,date)
        if direction == 'down':
            return {"tradeSignal": 'hold'}
        else:
            signal = 'Sell'

            return {"tradeSignal": signal}
    else:
        return {"tradeSignal": 'hold'}


    
def identifyUpwardDC(current_price, minprice,mindate,threshold,date):
    direction = "up"
    if current_price < minprice:
        minprice = current_price
        mindate = date
        
                
    if current_price > minprice:
        change = (current_price - minprice)/minprice
        if change >= threshold:
            #UPWARD DC FOUND
            #print(f"KØBER, pris: {current_price}, Dato: {date}, fra-pris: {minprice}, fra-date: {mindate}")
            upward_trends.append([(mindate,minprice), (date,current_price)])
            #APPEND TO A JSON FILE 
            append_to_json(f'upward_trends_{threshold}.json', {"start": {"date": mindate, "price": minprice}, "end": {"date": date, "price": current_price}})
            append_to_json(f'upward_ticks_{threshold}.json', {"ticks":buffer})
            append_to_json(f'minOSV_{threshold}.json', {"osv":minprice})
            pdcc_up=current_price
            #minprice = current_price
            
            minprice = 10000000
            direction = "down"
    return minprice,direction,mindate
def identifyDownwardDC(current_price, maxprice,maxdate,threshold,date):
    direction = 'down'
    if current_price > maxprice:
        maxprice = current_price
        maxdate = date
        
        
    if current_price < maxprice:
        change = (maxprice - current_price)/maxprice
        if change >= threshold:
            #DOWNWARD DC FOUND
            #print(f"SÆLGER, pris: {current_price}, Dato: {date}, fra-pris: {maxprice}, fra-date: {maxdate}")
            downward_trends.append([(maxdate,maxprice), (date,current_price)])
            append_to_json(f'downward_trends_{threshold}.json', {"start": {"date": maxdate, "price": maxprice}, "end": {"date": date, "price": current_price}})
            append_to_json(f'downward_ticks_{threshold}.json', {"ticks":buffer})
            append_to_json(f'maxOSV_{threshold}.json', {"osv":maxprice})
            pdcc_down = current_price
            #maxprice = current_price
            
            maxprice = -10
            direction = 'up'
    return maxprice,direction,maxdate




def append_to_json(filename: str, data: dict):
    try:
        with open(filename, 'r+') as file:
            file_data = json.load(file)
            file_data.append(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)
    except FileNotFoundError:
        with open(filename, 'w') as file:
            json.dump([data], file, indent=4)

def append_with_limit(lst, item, max_length):
    if len(lst) >= max_length:
        _ = lst.pop(0) # Remove the oldest item
    lst.append(item)
    return lst


@app.get("/gettrends/")
async def get_trends():
    return {"Upward": upward_trends,
            "DownWard": downward_trends}



