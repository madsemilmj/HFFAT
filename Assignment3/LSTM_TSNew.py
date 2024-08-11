from fastapi import FastAPI
import json
import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import numpy as np
import torch.nn as nn
import torch.nn.functional as F

app = FastAPI()
buffer = []
max_length = 30
minprice = 10000000
maxprice = -10
mindate = ""
maxdate = ""
direction = "up"
pdcc_up = 0
pdcc_down = 0
upward_trends = []
downward_trends = []
not_traded = []




#LSTM MODEL
class SimpleLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=50,num_classes=3, num_layers=1):
        super(SimpleLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)
        self.dropout = nn.Dropout(p=0.5)
        self.relu = nn.ReLU()

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        x = out[:, -1, :]
        
        x = self.dropout(x)
        x = self.fc(x)
        
        return x



input_size = 1  # Each input is a single feature
hidden_size = 64
num_classes = 3
num_layers = 2

model = SimpleLSTM(input_size, hidden_size, num_classes, num_layers)
#Loading weights from training
model.load_state_dict(torch.load("norm_LR0.0005_ACC0.57_LOSS0.71model_weights.pth", weights_only=True))
model.eval()


@app.get("/signal/{tickprice}/{date}/{threshold}/{SL}/{TP}")
async def read_price(tickprice,date,threshold,SL,TP):
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
    global model
    global not_traded
    
    current_price = float(tickprice.replace(",","."))
    theta = float(threshold.replace(",","."))
    buffer = append_with_limit(buffer,current_price,max_length)
    print(SL,TP)
    if direction == 'up':
        
        minprice,direction,mindate = identifyUpwardDC(current_price, minprice,mindate,theta,date)
        if direction == 'up':
            return {"tradeSignal": 'hold'}
        else:
            return {"tradeSignal": 'upward'}
    
    if direction == 'down':
        
        maxprice,direction,maxdate = identifyDownwardDC(current_price, maxprice,maxdate,theta,date)
        if direction == 'down':
            return {"tradeSignal": 'hold'}
        else:
            return {"tradeSignal": 'upward'}
            
    else:
        return {"tradeSignal": 'hold'}


    
def identifyUpwardDC(current_price, minprice,mindate,threshold,date):
    direction = "up"
    #signal = ""
    if current_price < minprice:
        minprice = current_price
        mindate = date
        
    if current_price > minprice:
        change = (current_price - minprice)/minprice
        if change >= threshold:
            
            #signal = produce_signal(model,buffer)

            minprice = 10000000
            direction = "down"
    return minprice,direction,mindate
def identifyDownwardDC(current_price, maxprice,maxdate,threshold,date):
    direction = 'down'
    #signal = ""
    if current_price > maxprice:
        maxprice = current_price
        maxdate = date
        
        
    if current_price < maxprice:
        change = (maxprice - current_price)/maxprice
        if change >= threshold:
            
            #signal = produce_signal(model,buffer)

            maxprice = -10
            direction = 'up'
    return maxprice,direction,maxdate



@app.get("/lstm/{bufferString}")
async def returnsignal(bufferString):
    global model
    buffer =  [float(x.replace(",",".")) for x in bufferString.split(";")]
    signal,probs = produce_signal(model,buffer)
    
    return {"tradeSignal": signal, "probs": probs.item()}



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



def normalize_sequence(x):
    # Assuming sequence is of shape (sequence_length, feature_dim)
    themean = np.mean(x,1,keepdims=True)
    thestd = np.std(x,1,keepdims=True)
    # Avoid division by zero in case std is zero
    
    #std = torch.clamp(std, min=1e-8)
    normalized_sequence = (x - themean) / thestd
    return normalized_sequence


def calcualte_log_returns(x):
    return np.log(x[:, 1:] / x[:, :-1])







def produce_signal(model,buffer):
    data_np = np.array([buffer[-21:]]) #One observation is removed when return is calculated so we end at 20
    norm_ret = normalize_sequence(calcualte_log_returns(data_np))
    input_data = torch.tensor(norm_ret,dtype=torch.float32)
    
    input_data = input_data.view(-1, 20, 1)  # Reshape for LSTM input
    with torch.no_grad():
        output = model(input_data)
    probs = F.softmax(output,dim=1)
    pred = torch.argmax(output).item()
    if pred == 1:
        signal = "buy"
    elif pred == 2:
        signal = "sell"
    else:
        signal = "hold"

    #print(probs)        
    #if probs[0][0] > 0.4:
    #    signal = "hold"

    
    return signal,probs[0][pred]



@app.get("/gettrends/")
async def get_trends():
    return {"Upward": upward_trends,
            "Downward": downward_trends,
            "Not": not_traded}



