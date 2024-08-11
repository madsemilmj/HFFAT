using System;
using System.Net.Http;
using cAlgo.API;
using cAlgo.API.Internals;
using Newtonsoft.Json.Linq;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.FullAccess)]
    public class PythonSignalBot : Robot
    {
        [Parameter("Threshold", DefaultValue = 0.001)]
        public double Threshold { get; set; }
        [Parameter("Volume", DefaultValue = 1000000, MinValue = 100000)]
        public int Volume { get; set; }
        
        private HttpClient _httpClient;
        //private static readonly HttpClient _httpClient = new HttpClient();
        
        
        
        protected override void OnStart()
        {
            Print("Bot started.");
            _httpClient = new HttpClient();
        }

        protected override void OnTick()
        {
            
            double askPrice = Symbol.Ask;
            // Print($"Current ask price: {askPrice}");
            string date = Server.Time.ToString("yyyy.MM.dd.HH:mm:ss.fff");
            // Call the method to get trade signal and execute orders
         
            GetTradeSignalAndExecute(askPrice,date,Threshold);
        }

        private void GetTradeSignalAndExecute(double tickPrice, string date, double Threshold)
        {
            //Print($"Sending request to Python backend with tick price: {tickPrice}");
            string signal = GetTradeSignal(tickPrice, date, Threshold);

            if (signal == "buy")
            {
                
                //ExecuteMarketOrder(TradeType.Buy, SymbolName, Volume, label);
            }
            else if (signal == "close")
            {
                
                // ExecuteMarketOrder(TradeType.Sell, SymbolName, 1000, "PythonSignalBot");
                //var position = Positions.Find(label, Symbol.Name);
                //ClosePosition(position);
            }
            else if (signal == "hold")
            {
                //Print("Doing nothing");
            }
        }

        private string GetTradeSignal(double tickPrice, string date, double Threshold)
        {
            try
            {
                
                string url = $"http://127.0.0.1:8000/signal/{tickPrice}/{date}/{Threshold}";
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

        protected override void OnStop()
        {
            Print("Bot stopped.");
            _httpClient.Dispose();
        }
    }
}
