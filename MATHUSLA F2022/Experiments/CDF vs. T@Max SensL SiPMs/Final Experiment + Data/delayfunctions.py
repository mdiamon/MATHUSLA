
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math as math
import scipy
from scipy.stats import norm
from scipy.signal import argrelextrema
import os, glob


"""
get_fm(): Returns the index of the fraction of maximum amplitude of data

data: a list of values for the data (Voltage)
fraction: num btw 0 and 1 (fraction of max. amplitude you wish to obtain)


"""
def get_fm(data, fraction):

    # get the desired constant fraction of the amplitude
    frac = max(data) * fraction
    idxs=[]

    # find the data points whose voltage is more than the constant fraction amplitude
    for i in range(len(data)):
        if data[i] >= frac:
            idxs.append(i)

    # return the minimum of these to get the point it first reaches the desired fraction
    return min(idxs)

"""
get_timing_delays_trace(): Plots the histogram of timing delays for a collection of trace data.
                           Returns the time delays in a list. 

path: path to the folder containing the traces taken
num_traces: number of traces taken
sigma: sigma for the gaussian filtering function (https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html)
fraction: what fraction of the maximum amplitude you want to use for constant fraction timing

"""

def get_timing_delays_trace(path,sigma, fraction, plot=True):
    
    time_delays = []
    num_traces = len([entry for entry in os.listdir(path) if os.path.isfile(os.path.join(path, entry))])
    csv_files = glob.glob(os.path.join(path, "*.csv"))
    counter = 1

    # loop through all files in a folder
    for f in csv_files:

        # read the csv file
        data = pd.read_csv(f, skiprows=1)
        
        # get the column data
        p1 = np.array(data['1 (VOLT)'])
        p2 = np.array(data['4 (VOLT)'])
        time = np.array(data['Time (s)'])
        
        # filter the data with a gaussian filter
        p1 = scipy.ndimage.gaussian_filter(p1, sigma = sigma)
        p2 = scipy.ndimage.gaussian_filter(p2, sigma = sigma)

        # this is used to filter out bad data; when its just dark counts instead of the signal
        if(all(i < 0.001 for i in p1) or all(i < 0.001 for i in p2)):
            print("True")
            continue
        
        # Get the indicies of where the constant fraction amplitude is located
        id_1 = get_fm(p1, fraction)
        id_2 = get_fm(p2, fraction)
        
        # find the time delay
        time_delay = time[id_1]-time[id_2]
        time_delays.append(time_delay)

        counter = counter + 1
    
    mu, std = norm.fit(time_delays)
    # plot the results, if desired
    if(plot == True):

        plt.rcParams["figure.figsize"] = (6.5,4)

        # histogram plot
        plt.hist(np.array(time_delays), density=True, alpha=0.6, color='purple', bins=10)

        plt.xlabel("Delay (s)")
        plt.ylabel("Frequency")
        # gaussian fit plot
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        p = norm.pdf(x, mu, std)
        plt.plot(x, p, 'k', linewidth=2)
        
        plt.title("Constant Fraction Timing Method")
        plt.show()
        
        # display relevant statistics 
        mean_rounded = "{:.3f}".format((np.mean(time_delays)) * 10 ** 9)
        sr_rounded = "{:.3f}".format((np.std(time_delays)) * 10 ** 9)
        median_rounded = "{:.3f}".format((np.median(time_delays)) * 10 ** 9)

        mean = "- Mean: " + str(mean_rounded) + " ns \\\ "
        SD = "- Standard Deviation: " + str(sr_rounded) + " ns \\\ "
        median = "- Median: " + str(median_rounded) + " ns \\\ "

        print(mean)
        print(SD)
        print(median)
    
    return time_delays, std

"""
get_timing_delays_leadingedge(): plot the histogram of leading edge measurements time delay

data: pandas DataFrame; data from BenchVue software for X @ Max scanned for both channels.
small_length: thickness of fiber, in mm

"""

def get_timing_delays_leadingedge(data, small_length, length, plot = True): 
    
    # Grab the data
    data.columns
    pulse1 = np.array(data['X at Max Y(1)'])
    pulse2 = np.array(data['X at Max Y(4)'])

    
    # delete the largest arguments from both datasets (to take care of messy data and outliers)
    argument1 = np.where(pulse1 > np.quantile(pulse1, 0.95))
    argument3 = np.where(pulse1 < np.quantile(pulse1,0.05))
    argument2 = np.where(pulse2 > np.quantile(pulse2, 0.95))
    argument4 = np.where(pulse2 < np.quantile(pulse2,0.05))
    
    # create array of indecies of the data points we want to delete
    del_args = np.append(argument1, np.append(argument2, np.append(argument3, argument4)))
    
    pulse1_clean = np.delete(pulse1, del_args)
    pulse2_clean = np.delete(pulse2, del_args)

    # create an array of the difference between the new datasets
    time_delays = []
    for i in range(len(pulse1_clean)):
        time_delays.append(pulse1_clean[i] - pulse2_clean[i])

    time_delays = np.array(time_delays)

    # Create plot, if desired
    if(plot == True):
        plt.rcParams["figure.figsize"] = (6.5,4)

        # histogram
        plt.title("T @ Max timing method")
        plt.xlabel("Delay (s)")
        plt.ylabel("Frequency")
        plt.axvline(time_delays.mean(),color='k', linestyle='dashed', linewidth=1)
        plt.hist(time_delays, density=True, alpha=0.6, color='b')


        # gaussian fit to histogram
        mu, std = norm.fit(time_delays) # find the mean & std of the data fitted to a norm. dist.
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        p = norm.pdf(x, mu, std)
        plt.plot(x, p, 'k', linewidth=2)
        plt.show()

        # display relevant statistics   
        mean_rounded = "{:.3f}".format((np.mean(time_delays)) * 10 ** 9)
        sr_rounded = "{:.3f}".format((np.std(time_delays)) * 10 ** 9)
        median_rounded = "{:.3f}".format((np.median(time_delays)) * 10 ** 9)
        
        mean = "- Mean: " + str(mean_rounded) + " ns \\\ "
        SD = "- Standard Deviation: " + str(sr_rounded) + " ns \\\ "
        median = "- Median: " + str(median_rounded) + " ns \\\ "
        
        print(mean)
        print(SD)
        print(median)

    return time_delays

"""

pulsegraph(): Graphs all trace data overlayed with one another

pathname: (str) path to folder containing all trace data

"""

def pulsegraph(pathname): 
    csv_files = glob.glob(os.path.join(pathname, "*.csv"))

    # loop over the list of csv files
    for f in csv_files:

        # read the csv file
        data = pd.read_csv(f, skiprows=1)

        # print the location and filename

        # grab pulses from csv cols.
        p1 = np.array(data['1 (VOLT)'])
        p2 = np.array(data['4 (VOLT)'])
        
        # filter the data
        p1 = scipy.ndimage.gaussian_filter(p1, sigma = 5)
        p2 = scipy.ndimage.gaussian_filter(p2, sigma = 5)
        
        # plot the filtered pulses
        time = np.array(data['Time (s)'])
        plt.xlabel("time (s)")
        plt.ylabel("voltage (v)")
        plt.plot(time, p1,color='orange')
        plt.plot(time, p2,color='black')


"""

overlay_plots(): Overlay the histograms of leading edge and constant fraction methods

pathname: (str) path to folder containing all trace data

"""

def overlay_plots(trace_td, meas_td):

    plt.rcParams["figure.figsize"] = (7,4.5)

    # plot the histogram and gaussian fit of the constant fraction method
    plt.hist(np.array(trace_td), density=True, alpha=0.6, color='purple', bins=10, label = 'Constant Fraction')

    mu, std = norm.fit(trace_td)
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mu, std)

    plt.plot(x, p, 'k', linewidth=2)
    plt.title('CDF vs. t@Max')
    plt.xlabel("Delay (s)")
    plt.ylabel("Frequency")

    # plot the histogram and gaussian fit of the leading edge method
    plt.hist(np.array(meas_td), density=True, alpha=0.6, color='blue', label = 't@Max', bins=10)
    mu, std = norm.fit(meas_td)
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mu, std)

    plt.plot(x, p, 'k', linewidth=2)
    plt.legend()
    plt.show()

def time_delay_cdf(signal1, signal2, time1, time2):

    # Finding the zero crossing point

    # PULSE 1 -------------------------------------
    #local_maxes = argrelextrema(signal1, np.greater)
    minn = np.where(signal1 == min(signal1))[0][0]
    maxx = np.where(signal1 == max(signal1))[0][0]


    # get the local maxes to find the big dip 
    range1 = maxx
    #diff = abs(local_maxes[0][0] - minn)
    #print(local_maxes)
    """
    for maxx in local_maxes[0]:
        if abs(maxx - minn) < diff and maxx < minn:
            range1 = maxx

    """
    range2 = minn

    # find the zero and its index
    zero1 = signal1[range1]
    for value in signal1[range1:range2]:
        if abs(0 - value) < zero1:
            zero1 = value


    root1_idx = np.where(signal1 == zero1)

    #print(time1[root1_idx])

    # PULSE 2 ------------------------------------

    #local_maxes = argrelextrema(signal2, np.greater)

    minn = np.where(signal2 == min(signal2))[0][0]
    maxx = np.where(signal2 == max(signal2))[0][0]


    # get the local maxes to find the big dip 
    range1 = maxx
    #diff = abs(local_maxes[0][0] - minn)
    #for maxx in local_maxes[0]:
    #    if abs(maxx - minn) < diff and maxx < minn:
    #        range1 = maxx
    range2 = minn

    

    # find the zero and its index
    zero2 = signal2[range1]
    for value in signal2[range1:range2]:
        if abs(0 - value) < zero2:
            zero2 = value

    root2_idx = np.where(signal2 == zero2)

    #print(time2[root2_idx])

    return time1[root1_idx], time2[root2_idx] , time1[root1_idx] - time2[root2_idx] 

def cdf(signal, time, fraction):

    # Building the new signal

    sampling_freq = time[1] - time[0]

    max_idx = np.where(signal == max(signal))[0][0]
    min_idx = np.where(signal == min(signal))[0][0]

    attenuated_signal = np.array(signal) * fraction 
    inverted_signal = np.array(signal) * -1

    rise_time = abs(time[max_idx] - time[min_idx])
    shift_factor = rise_time * 0.2

    x_scale_factor = int(shift_factor / sampling_freq)

    time_shift = np.array(time) + shift_factor
    
    front_trail_time = []
    back_trail_time = []

    curr_shift = time_shift[0] - sampling_freq
    for i in range(x_scale_factor):
        front_trail_time.insert(0, curr_shift)
        curr_shift -= sampling_freq


    curr_shift = time[-1] + sampling_freq
    for i in range(x_scale_factor):
        back_trail_time.append(curr_shift)
        curr_shift += sampling_freq

    trail_front = np.zeros(x_scale_factor) + inverted_signal[0]
    trail_back = np.zeros(x_scale_factor) + attenuated_signal[-1]

    time_shift = np.concatenate((front_trail_time, time_shift))
    time = np.concatenate((time, back_trail_time))

    attenuated_signal = np.concatenate((attenuated_signal, trail_back))
    inverted_signal = np.concatenate((trail_front, inverted_signal))



    return time, attenuated_signal+inverted_signal

    
