using System;
using System.Net.Http;
using cAlgo.API;
using cAlgo.API.Internals;
using cAlgo.API.Indicators;
using Newtonsoft.Json.Linq;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.FullAccess)]
    public class FastAPI_Bollinger : Robot
    {
        [Parameter("Source")]
        public DataSeries Source { get; set; }
        [Parameter("BandPeriods", DefaultValue = 14)]
        public int BandPeriod { get; set; }
        [Parameter("Std", DefaultValue = 1.8)]
        public double std { get; set; }
        [Parameter("MAType")]
        public MovingAverageType MAType { get; set; }
        [Parameter("Initial Volume Percent", DefaultValue = 1, MinValue = 0)]
        public double InitialVolumePercent { get; set; }
        [Parameter("Stop Loss", DefaultValue = 100)]
        public int StopLoss { get; set; }
        [Parameter("Take Profit", DefaultValue = 100)]
        public int TakeProfit { get; set; }
        
        private readonly string label = "FastAPI_Bollinger";
        private HttpClient _httpClient;
        private BollingerBands boll;

        protected override void OnStart()
        {
            // Put your initialization logic here
            Print("Bot started.");
            _httpClient = new HttpClient();
            boll = Indicators.BollingerBands(Source, BandPeriod, std, MAType);
        }

        protected override void OnBar()
        {
            Print("Balance{0}", Account.Balance);
            Print("Equity{0}", Account.Equity);
            GetTradeSignalAndExecute();
        }
        
        private void GetTradeSignalAndExecute()
        {
            //Print($"Sending request to Python backend with tick price: {tickPrice}");
            string signal = GetTradeSignal();
            var Volume = Math.Floor(Account.Balance * 10 * InitialVolumePercent / 10000) * 10000;
            
            if (signal == "buy")
            {
                //Print("Received buy signal.");
                ExecuteMarketOrder(TradeType.Buy, Symbol.Name, Volume, label, StopLoss, TakeProfit);
            }
            else if (signal == "sell")
            {
                // Print("Received sell signal.");
                ExecuteMarketOrder(TradeType.Sell, Symbol.Name, Volume, label, StopLoss, TakeProfit);
            }
            else if (signal != "hold")
            {
                Print("No valid signal received.");
            }
        }

        private string GetTradeSignal()
        {
            double closeCurrent = Bars.Last(1).Close;
            double closePrevious = Bars.Last(2).Close;
            double topBollingerCurrent = boll.Top.Last(1);
            double topBollingerPrevious = boll.Top.Last(2);
            double bottomBollingerCurrent = boll.Bottom.Last(1);
            double bottomBollingerPrevious = boll.Bottom.Last(2);
            
            try
            {
                string url = "http://127.0.0.1:8000/signal/?";
                url += $"price_curr={closeCurrent}&"
                 + $"price_prev={closePrevious}&"
                 + $"boll_top_curr={topBollingerCurrent}&"
                 + $"boll_top_prev={topBollingerPrevious}&"
                 + $"boll_bot_curr={bottomBollingerCurrent}&"
                 + $"boll_bot_prev={bottomBollingerPrevious}";
                Print(url);
                
                HttpResponseMessage response = _httpClient.GetAsync(url).GetAwaiter().GetResult();
                response.EnsureSuccessStatusCode();

                string responseBody = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                Print($"Response from Python backend: {responseBody}");
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
            foreach (var position in Positions.FindAll(label, SymbolName))
            {
                ClosePosition(position);
            }
        }
    }
}
