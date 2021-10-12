from heuristic import *
from rpc_utils import *

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

max_eta = 5
max_block_height = 1240503

time_dict = {}
mixin_dict = {}

mixins_m = [i for i in range(1000)]
week_t = [i for i in range(150)]

mixin_dict["mixins"] = mixins_m
time_dict["week"] = week_t

for eta, keys_to_analyze in enumerate(heuristic_1(max_eta, max_block_height), start=1):
    # Initialize lists
    total_m = [0 for i in range(1000)]
    anonimity_size_m = [ [0] * (i + 1) for i in range(1000)]
    tractable_m = [0 for i in range(1000)]

    total_t = [0 for i in range(150)]
    tractable_t = [0 for i in range(150)]

    # Fill lists
    for input in keys_to_analyze:
        idx = input.number_of_mixins
        total_m[idx] += 1
        anonimity_size_m[idx][len(input.keys) - 1] += 1

        week = input.block_timestamp // 604800 - 2311
        total_t[week] += 1
        
        if len(input.keys) == 1:
            tractable_m[idx] += 1
            tractable_t[week] += 1

    # Add to dictionary
    mixin_dict["total_{}".format(eta)] = total_m
    mixin_dict["anonimity_set_size_{}".format(eta)] = anonimity_size_m
    mixin_dict["tractable_{}".format(eta)] = tractable_m

    time_dict["total_{}".format(eta)] = total_t
    time_dict["tractable_{}".format(eta)] = tractable_t

for eta in range(1, max_eta + 1):
    mixin_dict["eta = {}".format(eta)] = [np.float64(i) / j for i, j in zip(mixin_dict["tractable_{}".format(eta)], mixin_dict["total_{}".format(eta)])]
    time_dict["eta = {}".format(eta)] = [np.float64(i) / j for i, j in zip(time_dict["tractable_{}".format(eta)], time_dict["total_{}".format(eta)])]

# Create dataframe from dict
dft = pd.DataFrame(time_dict)
dfm = pd.DataFrame(mixin_dict)

dft.plot(x="week", y=["eta = 1", "eta = 3", "eta = 5"], ylim=(0,1))
plt.show()

dfm10 = dfm[dfm["mixins"] <= 10]
dfm10.plot(x="mixins", y=["eta = 1", "eta = 3", "eta = 5"], kind="bar", ylim=(0,1))
plt.show()
print("test")