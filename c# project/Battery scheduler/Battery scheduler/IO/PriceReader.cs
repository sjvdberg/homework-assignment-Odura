using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Battery_scheduler.structure;

namespace Battery_scheduler.IO
{
    static public class PriceReader
    {

        public static Energyprices GetPrices(string file)
        {
            StreamReader sr = new StreamReader(file);

            Dictionary<DateTime, double> prices = new Dictionary<DateTime, double>();
            List<DateTime> orderedTimestamps = new List<DateTime>();

            sr.ReadLine();
            string line = sr.ReadLine();
            while(line != null)
            {
                string[] parts = line.Split(',');
                DateTime time =  DateTime.Parse(parts[0]);
                double value = double.Parse(parts[1]);

                prices.Add(time, value);
                orderedTimestamps.Add(time);

                line = sr.ReadLine();
            }

            orderedTimestamps.Sort();
            return new Energyprices(0.25, prices, orderedTimestamps);
        }
    }
}
