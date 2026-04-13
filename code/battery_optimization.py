import pyomo.environ as pyo
import numpy as np
import pandas as pd
from datetime import datetime
import math
from  config import *


# Function that gets the data for a specific date and saves it to a file
def extract_day_prices(year, month, day, write_to_file = True):
    day_ahead_prices = pd.read_csv('data/clean_day_ahead_data.csv')
    day_ahead_prices['datetime'] = pd.to_datetime(day_ahead_prices['datetime'], utc=True)
    day_ahead_prices = day_ahead_prices.set_index('datetime')


    start = pd.Timestamp(year, month, day, tz='Europe/Amsterdam')
    end = start + pd.Timedelta(hours=23, minutes=45)
    

    day_data = day_ahead_prices.loc[start:end]

    if write_to_file:
        day_data.to_csv(f'data/days/{year}-{month}-{day}.csv')

    return day_data

# Function that gets the data for a specific month and saves it to a file
def extract_month_prices(year, month, write_to_file = True):
    day_ahead_prices = pd.read_csv('data/clean_day_ahead_data.csv')
    day_ahead_prices['datetime'] = pd.to_datetime(day_ahead_prices['datetime'], utc=True)
    day_ahead_prices = day_ahead_prices.set_index('datetime')


    start = pd.Timestamp(year, month, 1, tz='Europe/Amsterdam')
    end = pd.Timestamp(year, month + 1, 1, tz='Europe/Amsterdam')
    

    month_data = day_ahead_prices.loc[start:end]
    if write_to_file:
        month_data.to_csv(f'data/days/{year}-{month}.csv')
    
    return month_data

# Function that builds an LP model for the battery optimization
def optimize_model(year = None, month = None, day = None, file_name = None, data=None, print_results = True):
    # Check whether a specific file was submitted or that we instead take a day/month from the default one
    if year is None or month is None:
        if file_name is None:
            if data is None:
                raise ValueError("No valid date, month, file or dataframe selected")
            else:
                df_prices = data
        else:
            df_prices = pd.read_csv(file_name)
    elif day is None:
        df_prices = extract_month_prices(year, month, False)
    else:
        df_prices = extract_day_prices(year, month, day, False)

    prices = df_prices['price'].tolist()
    indices = list(range(len(prices)))


    opt_model = pyo.ConcreteModel()

    # Create model variables
    opt_model.charge = pyo.Var(indices, domain=pyo.NonNegativeReals, bounds=(min_soc * battery_capacity, max_soc * battery_capacity))
    opt_model.inflow = pyo.Var(indices, domain=pyo.NonNegativeReals, bounds=(0, max_load_change))
    opt_model.outflow = pyo.Var(indices, domain=pyo.NonNegativeReals, bounds=(0, max_load_change / math.sqrt(round_trip_efficiency)))


    # Create objective function
    opt_model.profit = pyo.Objective(expr=sum((prices[i] * math.sqrt(round_trip_efficiency) - degradation_cost) * time_period * opt_model.outflow[i] - prices[i] * time_period * opt_model.inflow[i] for i in indices) , sense=pyo.maximize)

    # Create flow constraints
    def flow_constraints(opt_model, i):
        if i == 0:
            return opt_model.charge[0] == opt_model.inflow[0] * math.sqrt(round_trip_efficiency) * time_period - opt_model.outflow[i] * time_period + initial_charge
        return opt_model.charge[i-1] + opt_model.inflow[i] * math.sqrt(round_trip_efficiency) * time_period - opt_model.outflow[i] * time_period == opt_model.charge[i]
    opt_model.flow_constraints = pyo.Constraint(indices, rule=flow_constraints)


    solver = pyo.SolverFactory("appsi_highs")
    result = solver.solve(opt_model)

    # Get results
    df_results = df_prices
    df_results['inflow'] = [pyo.value(opt_model.inflow[i]) for i in indices]
    df_results['outflow'] = [pyo.value(opt_model.outflow[i]) for i in indices]
    df_results['charge'] = [pyo.value(opt_model.charge[i]) for i in indices]

    
    if print_results:
        df_results.to_csv(f'results/day_schedules/{year}-{month}-{day}.csv')
        print(pyo.value(opt_model.profit))
    return df_results, pyo.value(opt_model.profit)
