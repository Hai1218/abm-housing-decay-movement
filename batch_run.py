from geo_housing.model import GeoHousing
from mesa import batch_run
import numpy as np
import pandas as pd

# NOTE: You do not need this as a separate file BUT it can be nice to track
# can also call the file and it makes things a little cleaner as it runs

# Here you will have elements that you want to sweep, eg:
# parameters that will remain constant
# parameters you want to vary
parameters = {"rent_discount": 0.5,
              "init_num_people": 2,
              "base_decay_constant": 0.15,
              "decay_differential": np.linspace(0,0.5, 6),
              "max_complaint": range(2,8,1)} 

# what to run and what to collect
# iterations is how many runs per parameter value
# max_steps is how long to run the model
results = batch_run(GeoHousing, 
                    parameters,
                    iterations=50,  
                    max_steps=30, 
                    data_collection_period = 1,
                    number_processes = 12) #how often do you want to pull the data





## NOTE: to do data collection, you need to be sure your pathway is correct to save this!
# Data collection
# extract data as a pandas Data Frame
pd.DataFrame(results).to_csv("batch_data.csv")

