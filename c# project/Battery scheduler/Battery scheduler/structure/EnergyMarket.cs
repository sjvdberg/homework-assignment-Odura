using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Battery_scheduler.structure
{
    /// <summary>
    /// Contains data about the energy market.
    /// prices contains data on the price for each interval in the market. Indexed by the start time of the interval.
    /// orderedTimestamps contains the start time of each interval.
    /// timeperiod contains the length of the invervals. This is assumed to be the same duration for each interval.
    /// </summary>
    public class EnergyMarket
    {
        public List<DateTime> orderedTimestamps;
        public Dictionary<DateTime, double> prices;
        public double timeperiod = 0.25;

        public EnergyMarket(double timeperiod, Dictionary<DateTime, double> prices, List<DateTime> orderedTimestamps)
        {
            this.orderedTimestamps = orderedTimestamps;
            this.prices = prices;  
            this.timeperiod = timeperiod;

        }
    }
}
