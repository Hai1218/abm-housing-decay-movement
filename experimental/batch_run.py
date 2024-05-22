from geo_housing.model import GeoHousing
from mesa import batch_run
import numpy as np
import pandas as pd

# NOTE: You do not need this as a separate file BUT it can be nice to track
# can also call the file and it makes things a little cleaner as it runs

# Here you will have elements that you want to sweep, eg:
# parameters that will remain constant
# parameters you want to vary
parameters = {"has_regulation": [True, False],
              "rent_discount": np.linspace(0.1,0.5,5),
              "init_num_people": 2,
              "base_decay_constant": 0.15,
              "decay_differential": 0.05,
              "num_month_rent_renovation": range(6,13,1),
              "rent_increase_differential": np.linspace(0.01,0.1,10),
              "max_complaint": range(3,6,1)} 

# what to run and what to collect
# iterations is how many runs per parameter value
# max_steps is how long to run the model
results = batch_run(GeoHousing, 
                    parameters,
                    iterations=10,  
                    max_steps=20, 
                    data_collection_period = 2,
                    number_processes = 12) #how often do you want to pull the data



# Convert the results to a DataFrame
results_df = pd.DataFrame(results)

# Save the results to a CSV file for further analysis
results_df.to_csv("batch_data_final.csv", index=False)
