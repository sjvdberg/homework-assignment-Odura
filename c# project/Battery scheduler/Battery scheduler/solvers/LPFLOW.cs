using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Battery_scheduler.structure;
using Google.OrTools.LinearSolver;

namespace Battery_scheduler.solvers
{
    /// <summary>
    /// Flow model
    /// inflow contains the amount of energy taken from the network at each time step.
    /// outflow contains the amount of energy leaving the battery at each time step before loss due to efficiency.
    /// currentCharge is the charge in the battery at the end of the price interval
    /// flowconstraints are the flow constraints used to balance the above
    /// </summary>
    public class LPFLOW
    {
        Dictionary<DateTime, Variable> inflow;
        Dictionary<DateTime, Variable> outflow;
        Dictionary<DateTime, Variable> currentCharge;
        Dictionary<DateTime, Constraint> flowconstraint;

        public ChargingSchedule result;


        public LPFLOW(Battery battery, EnergyMarket prices)
        {
            inflow = new Dictionary<DateTime, Variable>();
            outflow = new Dictionary<DateTime, Variable>();
            currentCharge = new Dictionary<DateTime, Variable>();
            flowconstraint = new Dictionary<DateTime, Constraint>();

            //Declare solver and objective variables
            //GLOP is a LP solver built into Google OR tools, which can be used without a license.
            Solver solver = Solver.CreateSolver("GLOP");
            Objective objective = solver.Objective();

            for (int i = 0; i < prices.orderedTimestamps.Count; i++)
            {
                DateTime time = prices.orderedTimestamps[i];
                //create variables for timestep
                inflow.Add(time, solver.MakeNumVar(0, battery.maxCapacityChange, "var inflow " + i));
                outflow.Add(time, solver.MakeNumVar(0, battery.maxCapacityChange / Math.Sqrt(battery.roundTripEfficiency), "var outflow " + i));
                currentCharge.Add(time, solver.MakeNumVar(battery.minSoC * battery.capacity, battery.maxSoC * battery.capacity, "var charge " + i));

                //Create flow constraint for timestep.
                //This initially creaes a constraint of the form 0 * inflow + 0 * outflow + 0 * currentcharge = 0/-initialCharge
                //The coefficients for the variables are then set to transform it into one of the following:
                //first timse step: currentCharge[0] = initialCharge + inflow * efficiency loss - outflow
                //later time steps: currentCharge[i] = currentCharge[i-1] + inflow * efficiency loss - outflow
                //Both the inflow and the outflow are multipliled by the length of the inverval in hours to go from MW to MWh.
                if (i > 0)
                {
                    flowconstraint.Add(time, solver.MakeConstraint(0, 0, "constraint inflow " + i));
                    flowconstraint[time].SetCoefficient(currentCharge[prices.orderedTimestamps[i - 1]], 1);
                }
                else
                    flowconstraint.Add(time, solver.MakeConstraint(-battery.initialCharge, -battery.initialCharge, "constraint inflow " + i));
                flowconstraint[time].SetCoefficient(currentCharge[time], -1);
                flowconstraint[time].SetCoefficient(inflow[time], prices.timeperiod * Math.Sqrt(battery.roundTripEfficiency) );
                flowconstraint[time].SetCoefficient(outflow[time], -prices.timeperiod);

                //Set the coefficients for each variable in the cost function
                objective.SetCoefficient(inflow[time], -prices.prices[time] * prices.timeperiod);
                objective.SetCoefficient(outflow[time], prices.timeperiod * (prices.prices[time] * Math.Sqrt(battery.roundTripEfficiency) - battery.degradationLoss));
            }

            objective.SetMaximization();
            solver.Solve();
            double res = objective.Value();

            result = new ChargingSchedule(prices, battery);

            foreach(DateTime time in prices.orderedTimestamps)
            {
                //Read solution values for inflow and outflow.
                double locinflow = inflow[time].SolutionValue();
                double locoutflow = outflow[time].SolutionValue();
                if (locinflow != 0 && locoutflow != 0)
                    //Will not happen in an optimal schedule unless there are negative energy prices and degradation costs
                    //are so low that the loss to efficiency alone is worth it.
                    throw new Exception("Simultaneous in and outflow");
                if (locinflow != 0)
                    result.schedule[time] = locinflow;
                else
                    result.schedule[time] = -locoutflow;
            }
            //Check if solution is feasible and that its profit was computed correctly.
            if (!result.CheckFeasibility())
                throw new Exception("Invalid solution");
            if (Math.Abs(result.GetProfit() - res) > 0.01)
                throw new Exception("Result values do not line up");

        }


    }

}
