using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Battery_scheduler.structure
{
    public class Energyprices
    {
        public List<DateTime> orderedTimestamps;
        public Dictionary<DateTime, double> prices;
        public double timeperiod = 0.25;

        public Energyprices(double timeperiod, Dictionary<DateTime, double> prices, List<DateTime> orderedTimestamps)
        {
            this.orderedTimestamps = orderedTimestamps;
            this.prices = prices;  
            this.timeperiod = timeperiod;

        }
    }
}
