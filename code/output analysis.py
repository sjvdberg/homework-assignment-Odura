from price_prediction import *
from battery_optimization import *
import pandas as pd


# Gets energy price predictions using a number of variable combinations
def gather_all_data():

    models = {'xgboost' : xgboost_model, 'elastic_net' : elastic_net, 'naive_model' : naive_model}
    starting_dates = range(171, 365)
    training_lengths = [30 * 96, 60 * 96, 90 * 96, 180 * 96]
    test_lengths = [96, 2 * 96, 4 * 96, 10 * 96, 30 * 96]

    results = []
    

    
    for date in starting_dates:
        print(f'day {date}')
        for training_length in training_lengths:
            for test_length in test_lengths:
                print(f'training length {training_length} test length {test_length}')
                for model in models:
                    if date * 96 + training_length + test_length < 34990:
                        _ , metrics = models[model](date * 96, training_length, test_length, False)
                        results.append((model, date, training_length, test_length, metrics[0], metrics[1], metrics[2]))
        if date % 10 == 0:
            df_results = pd.DataFrame(results, columns=['model', 'date', 'training_length', 'test_length', 'mae', 'msae', 'rho'])
            df_results.to_csv('results/all_results_2.csv')


# Gets the optimal battery schedule for each day in a year
def get_year_prediction(year):

    dates = pd.date_range(start=f'{year}-31-01', end=f'{year}-12-30', freq='D')
    month_day = [(d.month, d.day) for d in dates]
    res = []
    for month, day in month_day:
        _ , profit = optimize_model(year, month, day, print_results=False)
        res.append((datetime(year, month, day), profit))
    
    df_results = pd.DataFrame(res, columns=['date', 'profit'])
    df_results = df_results.set_index('date')
    df_results.to_csv('results/battery_optimization.csv')


def compare_year_prediction(year, model):

    days = range(0,365-181)

    results = []
    for date in days:
        preds, _ = model(date * 96, 180 * 96, 96, False)
        preds['price'] = preds['preds']
        _ , profit = optimize_model(data=preds, print_results=False)
        results.append(profit)

    df_results = pd.DataFrame({'predicted_profit' : results})
    df_results.index = pd.to_datetime(df_results.index + 180, unit='D', origin='2025-01-01')
    
    optimal_profit = pd.read_csv('results/battery_optimization.csv', parse_dates=['date'])
    optimal_profit = optimal_profit.set_index(['date'])

    df_combined = pd.merge(optimal_profit, df_results, left_index=True, right_index=True, how='inner')


    df_combined.to_csv('results/combined_prediction.csv')


def create_graph():
    
    day_profits = pd.read_csv('results/combined_prediction.csv', parse_dates=['date'])

    day_profits = day_profits.set_index('date')
    day_profits = day_profits.rename(columns={'predicted_profit': 'prediction based profit'})
    day_profits = day_profits.rename(columns={'profit': 'optimal profit'})
    print(day_profits['optimal profit'].sum())
    print(day_profits['prediction based profit'].sum())
    # Plot actual vs predicted
    day_profits.plot(figsize=(14, 4), ylim=0)
    plt.title('battery profits vs prediction based profit')
    plt.show()



def create_results_graphs(metric):
    data = pd.read_csv('results/all_results.csv')

    data['date'] = pd.to_datetime(data['date'] - 1, unit='D', origin='2025-01-01')

    data['date'] = data['date'] + pd.Timedelta(days=184)


    model_dfs = {model: group.drop(columns=['model']).reset_index(drop=True) for model, group in data.groupby('model')}

    best_metric_per_day = {}

    for model in model_dfs:
        best_config = (
            model_dfs[model].groupby(['training_length', 'test_length'])[metric]
            .mean()
            .idxmin()  # returns (training_length, test_length) of best config
            )
        best_df = model_dfs[model][
            (model_dfs[model]['training_length'] == 17280) &
            (model_dfs[model]['test_length']     == 96)
            ][['date', metric]].set_index('date')
        best_metric_per_day[model] = best_df[metric]
        print(f'best metric {model} is training time {best_config[0]} and test time {best_config[1]}')
        print(f'mean {metric} is {best_df[metric].mean()}')
    
    df_best = pd.DataFrame(best_metric_per_day)

    df_best.plot(figsize=(14, 4))
    plt.title(f'{metric} for different models')
    plt.show()

create_graph()