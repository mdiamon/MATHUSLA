import numpy as np
import matplotlib.pyplot as plt
from scipy.odr import *

import random

#linear regression fitting model
def lin_func(p, x):
     m, c = p
     return m*x + c

def linfit(x, y, xerr, yerr, guess = 1):
    #linear regression code with x and y error
    lin_model = Model(lin_func)

    # Create a RealData object using our initiated data from above.
    data = RealData(x, y, sx=xerr, sy=yerr)

    # Set up ODR with the model and data.
    odr = ODR(data, lin_model, beta0=[guess, 1])

    # Run the regression.
    out = odr.run()

    return [out.beta[0], out.beta[1], out.sd_beta[0], out.sd_beta[1], out.res_var]
    # Use the in-built pprint method to give us results.
