using Battery_scheduler.IO;
using Battery_scheduler.structure;
using Battery_scheduler.solvers;
using System;


namespace OduraHomework
{
    internal class Program
    {
        static void Main(string[] args)
        {
            string file = "../../../../../../data/day_schedules/05-05-2025.csv";

            EnergyMarket prices = PriceReader.GetPrices(file);
            Battery battery = new Battery();

            LPFLOW flow = new LPFLOW(battery, prices); 

            Console.WriteLine(flow.result.profit);

            ;
        }
    }
}