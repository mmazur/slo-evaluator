#!/usr/bin/env python3

import pandas as pd
import numpy as np


rows = 20*1000
step = 10
startts = 1610000000

rng = np.random.default_rng()

timestamps = pd.DataFrame(range(startts, startts+(rows*step), step), columns=["timestamp"])
values = pd.DataFrame(rng.integers(45, 100, size=(rows, 1)), columns=["value"])

df = pd.concat([timestamps, values], axis=1)
df.set_index("timestamp", inplace=True)

df.insert(0, "__name__", "laptop_temp")

df.to_csv("out.csv")



