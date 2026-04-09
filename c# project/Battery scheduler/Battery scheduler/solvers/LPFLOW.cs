using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Battery_scheduler.structure;
using Google.OrTools.LinearSolver;

namespace Battery_scheduler.solvers
{
    public class LPFLOW
    {
        Dictionary<DateTime, Variable> inflow;
        Dictionary<DateTime, Variable> outflow;
        Dictionary<DateTime, Variable> currentCharge;
        Dictionary<DateTime, Constraint> flowconstraint;


        public LPFLOW(Battery battery, Energyprices prices)
        {
            inflow = new Dictionary<DateTime, Variable>();
            outflow = new Dictionary<DateTime, Variable>();
            currentCharge = new Dictionary<DateTime, Variable>();
            flowconstraint = new Dictionary<DateTime, Constraint>();

            Solver solver = Solver.CreateSolver("GLOP");
            Objective objective = solver.Objective();

            for (int i = 0; i < prices.orderedTimestamps.Count; i++)
            {
                DateTime time = prices.orderedTimestamps[i];
                inflow.Add(time, solver.MakeNumVar(0, battery.maxCapacityChange * Math.Sqrt(battery.roundTripEfficiency), "var inflow " + i));
                outflow.Add(time, solver.MakeNumVar(0, battery.maxCapacityChange, "var outflow " + i));
                currentCharge.Add(time, solver.MakeNumVar(battery.minSoC * battery.capacity, battery.maxSoC * battery.capacity, "var charge " + i));
                flowconstraint.Add(time, solver.MakeConstraint(0, 0, "constraint inflow " + i));
                flowconstraint[time].SetCoefficient(currentCharge[time], -1);
                flowconstraint[time].SetCoefficient(inflow[time], prices.timeperiod);
                flowconstraint[time].SetCoefficient(outflow[time], -prices.timeperiod);
                if (i > 0)
                    flowconstraint[time].SetCoefficient(currentCharge[prices.orderedTimestamps[-1]], 1);

                objective.SetCoefficient(inflow[time], -prices.prices[time] * prices.timeperiod / Math.Sqrt(battery.roundTripEfficiency));
                objective.SetCoefficient(outflow[time], prices.prices[time] * prices.timeperiod * Math.Sqrt(battery.roundTripEfficiency) - battery.degradationLoss);
            }

            solver.Solve();
            double res = objective.Value();

            ChargingSchedule schedule = new ChargingSchedule(prices, battery);

            foreach(DateTime time in prices.orderedTimestamps)
            {
                double locinflow = inflow[time].SolutionValue() / Math.Sqrt(battery.roundTripEfficiency);
                double locoutflow = outflow[time].SolutionValue();
                if (locinflow != 0 && locoutflow != 0)
                    throw new Exception("Simultaneous in and outflow");
                if (locinflow != 0)
                    schedule.schedule[time] = -locinflow;
                else
                    schedule.schedule[time] = locoutflow;

                if (!schedule.Checkvalidity(0))
                    throw new Exception("Invalid solution");
                if (Math.Abs(schedule.GetProfit() - res) < 0.01)
                    throw new Exception("Result values do not line up");
            }

        }


    }

}
