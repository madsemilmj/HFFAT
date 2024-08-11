using System;
using System.Net.Http;
using cAlgo.API;
using cAlgo.API.Internals;
using Newtonsoft.Json.Linq;
using System.Collections.Generic;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.FullAccess)]
    public class PythonSignalBot : Robot
    {
        [Parameter("Threshold", DefaultValue = 0.001)]
        public double Threshold { get; set; }
        [Parameter("Volume", DefaultValue = 1000000, MinValue = 100000)]
        public int Volume { get; set; }
        
        [Parameter("Take Profit (pips)", DefaultValue = 50)]
        public int TakeProfit { get; set; }

        [Parameter("Stop Loss (pips)", DefaultValue = 5)]
        public int StopLoss { get; set; }
        //[Parameter("CloseThreshold", DefaultValue = 5)]
        //public int CloseThreshold { get; set; }
        
        private List<double> buffer = new List<double>();
        
        private HttpClient _httpClient;
        //private static readonly HttpClient _httpClient = new HttpClient();
        
        private string label_buy = "lstm_buy";

        private string label_sell = "lstm_sell";
        
        private double maxPrice = 1;
        private double minPrice = 10000000;
        private string direction = "up";
        
        protected override void OnStart()
        {
            Print("Bot started.");
            _httpClient = new HttpClient();
        }

        protected override void OnTick()
        {
            
            
            double askPrice = Symbol.Ask;
            buffer.Add(askPrice);
            if (buffer.Count > 30)
            {
                buffer.RemoveAt(0);
          
            }
            
            
            if (direction == "up"){
            
                //Identify upward dc
                if (askPrice < minPrice){
                    minPrice = askPrice;
                }
                    
                if (askPrice > minPrice){
                    double change = (askPrice - minPrice)/minPrice;
                    if (change >= Threshold){
                        minPrice = 10000000;
                        // PRODUCE SIGNAL
                        GetTradeSignalAndExecute(buffer, direction);
                        //Close any Long positions
                        var position = Positions.Find(label_buy, Symbol.Name);
                        if (position != null){
                            ClosePosition(position);
                        }
                        direction = "down";
                    }
                }
                
                
            }
            
            if (direction == "down"){
            
                //Identify downward dc
                if (askPrice > maxPrice){
                    maxPrice = askPrice;
                }
                    
                    
                if (askPrice < maxPrice){
                    double change = (maxPrice - askPrice)/maxPrice;
                    if (change >= Threshold){
                        
                        
                        GetTradeSignalAndExecute(buffer, direction);
                        //Close any open short positions
                        var position = Positions.Find(label_sell, Symbol.Name);
                        if (position != null){
                            ClosePosition(position);
                        }
                        
                        maxPrice = -10;
                        direction = "up";
                    }
                }
            }
            
            
            
            
            
            
            // Print($"Current ask price: {askPrice}");
            string date = Server.Time.ToString("yyyy.MM.dd.HH:mm:ss.fff");
            // Call the method to get trade signal and execute orders
         
            //string res = ProcessTick(askPrice,date,Threshold,StopLoss,TakeProfit);
            
            //if (res == "upward" | res == "downward"){
            //    GetTradeSignalAndExecute(buffer);
            //}
        }

        private void GetTradeSignalAndExecute(List<double> buffer, string trend)
        {
            //Print($"Sending request to Python backend with tick price: {tickPrice}");
            (string signal, string prob) = GetTradeSignal(buffer);
            
            
            double probability = double.Parse(prob);
            
            if (signal == "buy")
            {
                //Print("Received buy signal.");
                //ExecuteMarketOrder(TradeType.Buy, SymbolName, Volume, label_buy,StopLoss, TakeProfit);
            }
            if (signal == "sell")
            {
                //Print("Received sell signal.");
                //ExecuteMarketOrder(TradeType.Sell, SymbolName, Volume, label_sell,StopLoss, TakeProfit);
                
            }
            if (signal == "hold" & trend == "up")
            
            {
                ExecuteMarketOrder(TradeType.Sell, SymbolName, Volume, label_sell,StopLoss, TakeProfit);
                //Print("Doing nothing");
            }
            
            if (signal == "hold" & trend == "down")
            {
                ExecuteMarketOrder(TradeType.Buy, SymbolName, Volume, label_buy, StopLoss, TakeProfit);
                //Print("Doing nothing");
            }
        }


        
        private string ProcessTick(double tickPrice, string date, double Threshold, int SL, int TP)
        {
            try
            {
                
                string url = $"http://127.0.0.1:8000/signal/{tickPrice}/{date}/{Threshold}/{SL}/{TP}";
                HttpResponseMessage response = _httpClient.GetAsync(url).GetAwaiter().GetResult();
                response.EnsureSuccessStatusCode();
                string responseBody = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                // Print($"Response from Python backend: {responseBody}");
                var json = JObject.Parse(responseBody);
                return json["tradeSignal"].ToString();
            }
            catch (Exception ex)
            {
                Print("Error fetching trade signal: " + ex.Message);
                return null;
            }
        }

        private (string,string) GetTradeSignal(List<double> buffer)
        {
            try
            {
                
                string bufferString = string.Join(";", buffer);
                string url = $"http://127.0.0.1:8000/lstm/{bufferString}";
                HttpResponseMessage response = _httpClient.GetAsync(url).GetAwaiter().GetResult();
                response.EnsureSuccessStatusCode();
                string responseBody = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                // Print($"Response from Python backend: {responseBody}");
                var json = JObject.Parse(responseBody);
                return (json["tradeSignal"].ToString(), json["probs"].ToString());
            }
            catch (Exception ex)
            {
                Print("Error fetching trade signal: " + ex.Message);
                return (null,null);
            }
        }





        protected override void OnStop()
        {
            Print("Bot stopped.");
            _httpClient.Dispose();
        }
    }
}
