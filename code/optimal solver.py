import pyomo.environ as pyo
import numpy as np
import pandas as pd
import math
from  config import *


def extract_day_prices(year, month, day):
    day_ahead_prices = pd.read_csv('data/clean_day_ahead_data.csv')
    day_ahead_prices['datetime'] = pd.to_datetime(day_ahead_prices['datetime'], utc=True)
    day_ahead_prices = day_ahead_prices.set_index('datetime')


    start = pd.Timestamp(year, month, day, tz='Europe/Amsterdam')
    end = pd.Timestamp(year, month, day + 1, tz='Europe/Amsterdam')
    

    day_data = day_ahead_prices.loc[start:end]

    day_data.to_csv(f'data/days/{year}-{month}-{day}.csv')

def extract_month_prices(year, month):
    day_ahead_prices = pd.read_csv('data/clean_day_ahead_data.csv')
    day_ahead_prices['datetime'] = pd.to_datetime(day_ahead_prices['datetime'], utc=True)
    day_ahead_prices = day_ahead_prices.set_index('datetime')


    start = pd.Timestamp(year, month, 1, tz='Europe/Amsterdam')
    end = pd.Timestamp(year, month + 1, 1, tz='Europe/Amsterdam')
    

    day_data = day_ahead_prices.loc[start:end]

    day_data.to_csv(f'data/days/{year}-{month}.csv')

def define_model(year, month, day):
    extract_day_prices(year, month, day)

    df_prices = pd.read_csv(f'data/days/{year}-{month}-{day}.csv', parse_dates=['datetime'])

    prices = df_prices['price'].tolist()
    indices = list(range(len(prices)))


    opt_model = pyo.ConcreteModel()

    opt_model.charge = pyo.Var(indices, domain=pyo.NonNegativeReals, bounds=(min_soc * battery_capacity, max_soc * battery_capacity))
    opt_model.inflow = pyo.Var(indices, domain=pyo.NonNegativeReals, bounds=(0, max_load_change))
    opt_model.outflow = pyo.Var(indices, domain=pyo.NonNegativeReals, bounds=(0, max_load_change / math.sqrt(round_trip_efficiency)))

    opt_model.init = pyo.Constraint(expr=opt_model.charge[0] == opt_model.inflow[0] + initial_charge)

    opt_model.profit = pyo.Objective(expr=sum((prices[i] * math.sqrt(round_trip_efficiency) - degradation_cost) * time_period * opt_model.outflow[i] - prices[i] * time_period * opt_model.inflow[i] for i in indices) , sense=pyo.maximize)


    def flow_constraints(opt_model, i):
        if i == 0:
            return pyo.Constraint.Skip
        return opt_model.charge[i-1] + opt_model.inflow[i] * math.sqrt(round_trip_efficiency) * time_period - opt_model.outflow[i] * time_period == opt_model.charge[i]

    opt_model.flow_constraints = pyo.Constraint(indices, rule=flow_constraints)


    solver = pyo.SolverFactory("appsi_highs")
    result = solver.solve(opt_model)

    df_results = df_prices
    df_results['inflow'] = [pyo.value(opt_model.inflow[i]) for i in indices]
    df_results['outflow'] = [pyo.value(opt_model.outflow[i]) for i in indices]
    df_results['charge'] = [pyo.value(opt_model.charge[i]) for i in indices]

    df_results.to_csv(f'results/{year}-{month}-{day}.csv')
    print(pyo.value(opt_model.profit))


define_model(2025,5, 5)