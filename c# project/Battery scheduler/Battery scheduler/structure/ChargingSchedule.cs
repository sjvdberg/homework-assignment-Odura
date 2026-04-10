using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Battery_scheduler.structure
{
    public class ChargingSchedule
    {
        public Energyprices prices;
        public Battery battery;

        public Dictionary<DateTime, double> schedule;
        public double profit;
        

        public ChargingSchedule(Energyprices prices, Battery battery)
        {
            this.prices = prices;
            this.battery = battery;

            schedule = new Dictionary<DateTime, double>();
        }

        public bool Checkvalidity()
        {
            profit = 0;

            double currentcharge = battery.initialCharge;

            if (currentcharge > battery.maxSoC || currentcharge < battery.minSoC)
                // Initial charge not in correct range
                return false;
            foreach (DateTime time in prices.orderedTimestamps)
            {
                double intervalprice = prices.prices[time];
                double chargeSpeed = schedule[time];
                double chargeChange = prices.timeperiod * chargeSpeed;

                if (chargeSpeed > 0)
                    currentcharge += chargeChange * Math.Sqrt(battery.roundTripEfficiency);
                else
                    currentcharge += chargeChange;

                if (chargeChange > battery.maxCapacityChange / Math.Sqrt(battery.roundTripEfficiency) || chargeChange < -battery.maxCapacityChange)
                    // Charge change capacity not in correct range
                    return false;
                if (currentcharge > battery.maxSoC * battery.capacity + 0.01 || currentcharge < battery.minSoC * battery.capacity - 0.01)
                    // Charge not in correct range
                    return false;

            }
            return true;
        }

        public double GetProfit()
        {
            profit = 0;

            double totdegradationloss = 0;
            double totsellvalue = 0;
            double totbuyvalue = 0;
            foreach(DateTime time in prices.orderedTimestamps)
            {
                double intervalprice = prices.prices[time];
                double chargeSpeed = schedule[time];
                double chargeChange = prices.timeperiod * chargeSpeed;

                if (chargeSpeed > 0)
                {
                    double buyvalue = chargeChange * intervalprice;
                    totbuyvalue += buyvalue;

                    profit -= buyvalue;

                }
                else
                {
                    //Degradation loss will be negative as chargeChange is negative
                    double degradationcosts = chargeChange * battery.degradationLoss;
                    totdegradationloss += degradationcosts;

                    double sellvalue = - chargeChange * intervalprice * Math.Sqrt(battery.roundTripEfficiency);
                    totsellvalue += sellvalue;

                    profit += sellvalue + degradationcosts;
                }
            }
            return profit;
        }
    }
}
