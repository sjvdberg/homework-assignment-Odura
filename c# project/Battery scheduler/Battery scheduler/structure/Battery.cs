using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Battery_scheduler.structure
{
    public class Battery
    {
        public double capacity;
        public double maxCapacityChange;
        public double minSoC, maxSoC;
        public double roundTripEfficiency;
        public double degradationLoss;

        public Battery()
        {
            capacity = 4;
            maxCapacityChange = 2;
            minSoC = 0.05;
            maxSoC = 0.95;
            roundTripEfficiency = 0.88;
            degradationLoss = 80;
        }
    }
}
