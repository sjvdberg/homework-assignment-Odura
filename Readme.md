Overview of files:

The C# project folder contains the C# solution for prediction optimal battery usage. The solution file is in the Battery scheduler subfolder.

The code folder contains the various python files:
- config.py contains the battery parameters as well as the entso-e API key.
- input analysis.py contains the functions used to transform the input data into the data used by models as well as code for graphs based on the input data.
- price_prediction.py contains the code for the different price prediction models.
- battery_optimization.py contains the code for the LP that creates the optimal battery schedule.
- output analysis.py contains methods calling the above 2 files to get the results.

The data folder contains the raw data for the model. The days folder will be filled by the methods in battery_optimization.py that need data for a single day.

The figures folder contains the figures for the report.

The results data contains the main result files. These are created here automatically by the various functions in the python files.