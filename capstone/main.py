# File: main.py
# Author: Andrija Paurevic
# Student Number: 1003995297
# Date: Fri Nov 12, 2021
# Description:

# Import Modules
import numpy as np
import matplotlib.pyplot as plt
import dataAcquisitionHelperFunctions as run
from tqdm import tqdm

# Get parameters that the oscilloscope requires to run and collect data
trigParams, chanParams, timeParams, chanNumbers = run.setupOscilloscopeInput()

# Number of data points
numOfIterations = 5
collectData = True

# Execute Functions
if collectData:
    dataAcq = run.dataAcquisition()
    dataAcq.prepareOscilloscope(triggerParameters=trigParams,channelParameters=chanParams,timeParameters=timeParams)
    for i in tqdm(range(numOfIterations)):
        dataAcq.collectData(channels=chanNumbers)
    # Plot data
    dataAcq.plotHistogram(plotParameters=None)
else:
    run.curveFit("16cm_from_sipm_maskingtape_channel4.csv")