using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Battery_scheduler.structure
{
    /// <summary>
    /// Class that represents a charging schedule for a specific battery.
    /// prices contains the energy prices for the day
    /// battery is the battery that this is a schedule for
    /// 
    /// schedule is the actual schedule indicating whether we are loading (if positive) or unloading (if negative) at each timestep.
    /// profit is the expected profit of the schedule
    /// </summary>
    public class ChargingSchedule
    {
        public EnergyMarket prices;
        public Battery battery;

        public Dictionary<DateTime, double> schedule;
        public double profit;
        

        public ChargingSchedule(EnergyMarket prices, Battery battery)
        {
            this.prices = prices;
            this.battery = battery;

            schedule = new Dictionary<DateTime, double>();
        }

        /// <summary>
        /// Checks whether the schedule is valid for the battery and does not break any constraints.
        /// </summary>
        /// <returns></returns>
        public bool CheckFeasibility()
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

        /// <summary>
        /// Computes the total profit for the schedule and updates the profit variable accordingly.
        /// </summary>
        /// <returns></returns>
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
                    //Loading means energy is bought, so profit decreases
                    double buyvalue = chargeChange * intervalprice;
                    totbuyvalue += buyvalue;

                    profit -= buyvalue;

                }
                else
                {
                    //Unloading (or doing nothing) means energy is sold, so profit increases unless the degradation cost outweighs the sell value.

                    //Degradation loss will be negative as chargeChange is negative
                    double degradationcosts = chargeChange * battery.degradationLoss;
                    totdegradationloss += degradationcosts;

                    //Sellvalue will be positive if and only if interval price is as well as chargeChange is negative.
                    double sellvalue = - chargeChange * intervalprice * Math.Sqrt(battery.roundTripEfficiency);
                    totsellvalue += sellvalue;

                    profit += sellvalue + degradationcosts;
                }
            }
            return profit;
        }
    }
}
