import numpy as np
import pandas as pd
from entsoe import EntsoePandasClient
from config import *
from datetime import datetime, date, time
import matplotlib.pyplot as plt



def import_entsoe_data():
    client = EntsoePandasClient(api_key=entsoe_api_key)
    start = pd.Timestamp('20250101', tz='Europe/Amsterdam')
    end = pd.Timestamp('20251231', tz='Europe/Amsterdam')
    country_code = 'NL'

    ts = client.query_day_ahead_prices(country_code, start, end)
    ts.to_csv('data/day_ahead_data.csv')

def clean_entsoe_data():

    prices = pd.read_csv('data/day_ahead_data.csv')
    prices['datetime'] = pd.to_datetime(prices['datetime'], utc=True)
    prices = prices.set_index('datetime')
    min15_prices = prices.resample('15min').interpolate()

    min15_prices.to_csv('data/clean_day_ahead_data.csv')

def clean_weather_data():
    hourly_weather_data = pd.read_csv('data/uurdata_knmi_2025.txt', comment='#')
    hourly_weather_data.columns = hourly_weather_data.columns.str.strip()
    hourly_weather_data['datetime'] = pd.to_datetime(hourly_weather_data['YYYYMMDD'], format='%Y%m%d') + pd.to_timedelta(hourly_weather_data['HH'] -1, unit='h')
    hourly_weather_data = hourly_weather_data[["datetime", "FH", "T", "SQ", "Q"]]
    hourly_weather_data = hourly_weather_data.set_index('datetime')
    hourly_weather_data.index = hourly_weather_data.index.tz_localize('Europe/Amsterdam', ambiguous='NaT', nonexistent='NaT')
    hourly_weather_data = hourly_weather_data[hourly_weather_data.index.notna()]
    hourly_weather_data.index = hourly_weather_data.index.tz_convert('UTC')

    min15_weather_data = hourly_weather_data.resample('15min').ffill()

    
    min15_weather_data.to_csv('data/min15_weather_data.csv')



def plot_data():
    prices = pd.read_csv('data/clean_day_ahead_data.csv')
    prices.plot(x='datetime', y='price')
    plt.show()

def daily_average():
    prices = pd.read_csv('data/clean_day_ahead_data.csv', parse_dates=['datetime'])
    prices = prices.set_index('datetime')
    prices = prices.tz_convert('Europe/Amsterdam')

    daily_mean = prices.resample('ME').mean()


    daily_mean.plot( y='price')
    plt.show()


daily_average()