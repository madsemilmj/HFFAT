using System;
using System.Net.Http;
using cAlgo.API;
using cAlgo.API.Internals;
using Newtonsoft.Json.Linq;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class PythonSignalBot : Robot
    {

        [Parameter("Theta", DefaultValue = 0.001)]
        public double theta { get; set; }

        private HttpClient _httpClient;

        protected override void OnStart()
        {
            Print("Bot started.");
            _httpClient = new HttpClient();
        }

        protected override void OnTick()
        {
            double askPrice = Symbol.Ask; 
            // Call the method to get trade signal and execute orders
            GetTradeSignalAndExecute(askPrice);
        }

        private void GetTradeSignalAndExecute(double tickPrice)
        {
            string signal = GetTradeSignal(tickPrice);

            if (signal == "buy")
            {
                Print("Received buy signal.");
                CloseAllPositions(TradeType.Sell);
                ExecuteMarketOrder(TradeType.Buy, SymbolName, 1000, "PythonSignalBot");
            }
            else if (signal == "sell")
            {
                Print("Received sell signal.");
                CloseAllPositions(TradeType.Buy);
                //ExecuteMarketOrder(TradeType.Sell, SymbolName, 1000, "PythonSignalBot");
            }
            else if (signal != "hold")
            {
                Print("No valid signal received.");
            }
        }

        private void CloseAllPositions(TradeType tradeType)
        {
            foreach (var position in Positions.FindAll("PythonSignalBot", SymbolName, tradeType))
            {
                ClosePosition(position);
            }
        }

        private string GetTradeSignal(double tickPrice)
        {
            try
            {
                string url = $"http://127.0.0.1:8000/signal/{tickPrice}/theta?theta={theta}";
                HttpResponseMessage response = _httpClient.GetAsync(url).GetAwaiter().GetResult();
                response.EnsureSuccessStatusCode();

                string responseBody = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
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
 
                string url = $"http://127.0.0.1:8000/resetparameters";
                HttpResponseMessage response = _httpClient.GetAsync(url).GetAwaiter().GetResult();
                response.EnsureSuccessStatusCode();

            Print("Bot stopped.");
            _httpClient.Dispose();
        }
    }
}
