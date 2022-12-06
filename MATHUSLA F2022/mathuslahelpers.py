from typing import Optional
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
from sklearn.mixture import GaussianMixture
import numpy as np
from scipy.stats import norm
import scipy

"""
-------------------------------------------------------------
gaussian_fit(): 
Fit a gaussian (or mixture of gaussians) to data. Returns means, stds, weights of all gaussians found in the mixture.
-------------------------------------------------------------

-------------------------------------------------------------
Parameters
-------------------------------------------------------------
data (array): data you are fitting.

num_peaks (int): number of PE peaks / gaussians in the data.

bins (int): number if bins to plot histogram with

plot (bool): plot the histogram and gaussian fit, if true.
-------------------------------------------------------------

"""
def gaussian_fit(data, bins, plot=False):
    
    if plot==True:
        plt.figure()
        plt.xlim(0, 360)

    data = np.array(data)
    a = []
    y,x,c = plt.hist(data, bins=bins)


    if plot==False:
        plt.close()

    counter = 0
    ext = argrelextrema(y, np.greater, order=7)
    
    gmm = GaussianMixture(n_components = len(ext[0])).fit(data.reshape(-1, 1))
    means =  gmm.means_
    stds = gmm.covariances_
    weights = gmm.weights_

    if plot==True:
        
        f_axis = data.copy().ravel()
        f_axis.sort()
        
        plt.scatter(x[ext],y[ext], color='red')

        for weight, mean, covar in zip(gmm.weights_, gmm.means_, gmm.covariances_):
            counter+=1
            a.append(weight*norm.pdf(f_axis, mean, np.sqrt(covar)).ravel())
            plt.plot(f_axis, a[-1], label=counter)

        plt.xlabel('Amplitude (V)')
        plt.ylabel('Counts')
        plt.tight_layout()
        plt.xlim(min(data), max(data))

        plt.legend()
        plt.show()

    return means, stds, weights

"""
-------------------------------------------------------------
find_rmsd(): 
This function is used to find the RMSD of the fit of the data (i.e. quantitating how good our fit is -- the lower the better). 
It is based on the equation sqrt(sum (y_e - y_o)^2) / n, where y_e is the expected value of the data (i.e. y value of the fit), 
and y_o is the observed data, n is the number of data points. In particular, the fit we are we are considering is of the form
A*e^(Bx)


Returns the RMSD of the fit to the data.
-------------------------------------------------------------


-------------------------------------------------------------
Parameters
-------------------------------------------------------------
x (array or list): the x value of the data

observed_y (array or list): observed y values 

a (number): the fitted A value for the A*e^(Bx) fit

b (number): the fitted B value for the A*e^(Bx) fit

c (number): (optional) c value for a fit where f(x) = A*e^(Bx) + C
-------------------------------------------------------------
"""
def find_rmsd(x, observed_y, a,b,c=0):

    
    rmsd = 0
    for i in range(len(x)):
        #print("OBSERVED:", observed_y[i], "FIT:",a * np.exp(b * x[i]), "X:",  x[i])
        
        expected = a * np.exp(b * x[i]) + c
        rmsd += (observed_y[i] - expected) ** 2
        
        #print((observed_y[i] - a * np.exp(b * x[i])) ** 2, "\n")
        
    print("rmsd: ", np.sqrt(rmsd / len(x)))
    return np.sqrt(rmsd/len(x))

"""
coupling_eff(): Plots a stem plot of the average of each datapoint in a folder. Typically used to test coupling effiency between two points
                in the experiment, to find what eprcentage deviation each datapoint is from the mean.

                Returns nothing.

folder (string): The path to the data (must be csv files)
            
"""
def coupling_eff(amps):
    
    for ch in amps:
        plt.style.use("seaborn")
        fig = plt.figure()
        ax = fig.add_subplot(111)
        x=range(len(amps[ch]))

        avg = np.mean(amps[ch])

        plt.stem(x,amps[ch],use_line_collection=True,bottom=avg)
        plt.title("Channel "+ ch)
        plt.xlabel("Dataset")
        plt.ylabel("Mean Amplitude (mV)")

        # Annotate each data point with the percent deviation from the mean
        for x,y in zip(x, amps[ch]):                                       
            ax.annotate("{:7.1f} % deviation".format( (avg-y)/avg * 100), [x,y], textcoords='data',fontsize=12) 

        plt.show()

"""
summary_attenuation(): Plots the Raw attenutation (and fit) of Channels 1 and 4, the ratios of Ch4 / Ch1 (and fit), and a scatterplot of
                        Ch1 against Ch4. Has the capability of plotting multiple datasets against each other.

                        Returns nothing

distances (array of (number) arrays): All the distances used for each dataset. If you are only plotting one dataset, nest the array of distances within 
                            another array.

amps (array of (number) arrays): All the (average) amplitudes found for each dataset. If you are only plotting one dataset, nest the array of distances within 
                        another array.    

amps (array of (string) arrays): All the diameters of the fibres used (in mm), as strings. If you are only plotting one dataset, nest the array of distances within 
                        another array.

colors (array of (string) arrays): All the different colours you wish to color code your seperate datasets to distinguish them on the plots.

All Arrays must be of the same size

"""
def summary_attn(distances, amps, fibre_diams, colors):

    if len(amps) != len(colors):
        ValueError("You must input as many matplotlib colours as there are datasets you want to plot. You have {:.1f} datasets and {:.1f} colours".format(len(amps), len(colors)))
    
    keys = amps[0].keys()
    for amp_dict in amps:
        if(amp_dict.keys() != keys):
            ValueError("All input datasets must have data from the same channels. If they dont, call this function individually for each dataset.")

    # Raw amplitudes of all channels
    for ch in amps[0]:
        plt.style.use('seaborn-whitegrid')
        fig, ax = plt.subplots(figsize=(8,6))
        ax.set_facecolor('snow')
        for amp_dict,fibre,colour in zip(amps, fibre_diams, colors):

            # Channel Raw Attn
            opt = scipy.optimize.curve_fit(lambda t,a,b: a*np.exp(b*t),  distances,  amp_dict[ch])
            a, b = opt[0]
            plt.scatter(distances, amp_dict[ch],label = fibre+ "mm", color=colour)
            plt.plot(np.linspace(0,3, 100), a * np.exp(b * np.linspace(0,3, 100)), label = "Fit Ae^(Bx), A={:.3f}, B={:.3f}".format(a,b), color=colour)
            plt.xlabel("Delay Distance (m)", fontsize=14)
            plt.ylabel("Average (Abs. Max) Amplitude (mV)", fontsize=14)
            plt.title("CH{} Raw Attenuation".format(ch),fontsize=14)

            if len(amps) == 1:
                rmsd=find_rmsd(distances, amp_dict[ch], a, b)
        plt.legend(fontsize=13, frameon=True)
        plt.show()
    
    # Quotient of Data
    if len(amps[0]) == 2:
        plt.style.use('seaborn-whitegrid')
        fig, ax = plt.subplots(figsize=(8,6))
        ax.set_facecolor('snow')
        for amp_dict, fibre, colour in zip(amps, fibre_diams, colors):
            ch1, ch2 = amp_dict.keys()
            opt_quotient = scipy.optimize.curve_fit(lambda t,a,b: a*np.exp(b*t),  distances,  np.array(amp_dict[ch2])/np.array(amp_dict[ch1]))
            a,b= opt_quotient[0]
            plt.scatter(distances, np.array(amp_dict[ch2])/np.array(amp_dict[ch1]),label = fibre+ "mm", color=colour)
            plt.plot(np.linspace(0,3, 100), a * np.exp(b * np.linspace(0,3, 100)), label = "Fit Ae^(Bx), A={:.3f}, B={:.3f}".format(a,b), color=colour)
            plt.xlabel("Delay Distance (m)", fontsize=14)
            plt.ylabel("Average (Abs. Max) Amplitude (mV)", fontsize=14)
            plt.title("CH{} / CH{} ".format(ch2,ch1),fontsize=14)

            if len(amps) == 1:
                rmsd=find_rmsd(distances, amp_dict[ch], a, b)
        plt.legend(fontsize=13, frameon=True)
        plt.show()
          
"""
get_fm(): Returns the location of where the data reaches the constant fraction of the maxmimum amplitude.

    data (array): Data for which you wish to find the index of the constant fraction of max. amplitude

    fraction (num): constant fraction of the max amplitude whose index you want returned.


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
td_compare(): Takes two timedelay dicts as datapoints and outputs a histogram of them both on overlayed plots.
              Intended use it to compare CFD and T@Max methods for the same experiment.

    td_CFD (dict): dict of time delays found using the CFD method

    frac (num): fraction used for the cfd method

    tams (dict): dict of time delays found using the T@Max method

    channel (str): channels for which the time delay was plotted. (i.e. the keys in the above dicts you wish to plot). 
                    e.g. '1-4' or '2-3'


"""
def td_compare(td_CFD,frac, td_TAM, channel):

    
    plt.style.use('seaborn-whitegrid')
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_facecolor('snow')

    # plot the histogram and gaussian fit of the constant fraction method
    plt.hist(np.array(td_CFD[channel]), density=True, alpha=0.6, color='purple', bins=10, label = "Constant Fraction {:.1f} %".format(frac * 100))

    mu, std = norm.fit(td_CFD[channel])
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mu, std)

    plt.plot(x, p, 'k', linewidth=2)
    plt.title('CDF vs. t@Max')
    plt.xlabel("Delay (s)")
    plt.ylabel("Frequency")

    # plot the histogram and gaussian fit of the leading edge method
    plt.hist(np.array(td_TAM[channel]), density=True, alpha=0.6, color='blue', label = 't@Max', bins=10)
    mu, std = norm.fit(td_TAM[channel])
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = norm.pdf(x, mu, std)

    plt.plot(x, p, 'k', linewidth=2)
    plt.legend(fontsize=13, frameon=True)
    plt.show()

"""
summary_timing(): Plots the
                    - Mean (maxmimum) amplitude of both cfd and t@max methods as a function of delay distance
                    - sample standard deviation of both cfd and t@max methods as a function of delay distance

    distances (list): the distances over which the timing data were taken

    cfds (dict): dictonary containing the time delays of the cfd method

    tams (dict): dictonary containing the time delays of the t@max method

    channel (str): channel for which you wish to plot this summary (i.e. dictorinary key). E.g. '1-4' or '2-3'

"""
def summary_timing(distances, cfds, tams, channel, frac=Optional):

    cfd_std = []
    tam_std = []
    cfd_mean = []
    tam_mean = []

    for cfd in cfds:
        cfd_std.append(np.std(cfd[channel]))
        cfd_mean.append(np.mean(cfd[channel]))

    for tam in tams:
        tam_std.append(np.std(tam[channel]))
        tam_mean.append(np.mean(tam[channel]))

    if type(frac) == float:
        cfdlabel='Constant Fraction {:1f}'.format(frac * 100)
    else: 
        cfdlabel='Constant Fraction'


    plt.style.use('seaborn-whitegrid')
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_facecolor('snow')

    plt.scatter(distances, cfd_std, label = cfdlabel)
    plt.scatter(distances, tam_std, label = 't@Max')
    plt.ylim(min(min(tam_std),min(cfd_std)) * 0.5, max(max(cfd_std), max(tam_std)) * 1.2)
    plt.legend(fontsize = 13, frameon=True)
    plt.xlabel('Distance from Ch1 to Pulse (mm)', fontsize=14)
    plt.ylabel('Standard Deviation in Time Delay (s)', fontsize=14)
    plt.title('Constant Fraction vs t@Max: standard devs.', fontsize=14)
    plt.show()


    plt.style.use('seaborn-whitegrid')
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_facecolor('snow')
    plt.scatter(distances, cfd_mean, label = cfdlabel)
    plt.scatter(distances, tam_mean, label = 't@Max')
    plt.ylim(min(cfd_mean) * 1.3, max(cfd_mean) * 0.8)

    plt.legend(fontsize = 13, frameon=True)
    plt.xlabel('Distance from Ch1 to Pulse (mm)', fontsize=14)
    plt.ylabel('Mean Time Delay (s)', fontsize=14)
    plt.title('Constant Fraction vs t@Max: mean time delay', fontsize=14)
    plt.show()

"""
cfd_multifrac(): Overlays multiple instances of the cfd method for different fractions.

    timing_class (Timing): timing object that you wish to plot multiple cfd histograms for

    fractions (list of num): fractions for the cfds you wish to plot

    sigma (int): Integer corresponding to the filtering level in gaussian filtering

    channel (str) Channels of delay you wish to plot this for. e.g. '1-4' or '2-3'
"""
def cfd_multifrac(timing_class, fractions, sigma, channel, colours=Optional):

    if len(fractions) > 10 and len(colours) <= 10:
        print("You must enter your own list of {:.1f} colours".format(len(fractions)))

    else:
        colours=["red", "chocolate", "orange", "gold", "yellow", "yellowgreen", "green","turquoise", "blue", "mediumpurple", "purple"]

    
    h_shift = np.mean(timing_class.td_CFD(fractions[0], sigma, plot=False)[channel])

    plt.style.use('seaborn-whitegrid')
    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_facecolor('snow')
    for frac, colour in zip(fractions, colours):
        curr_tds = timing_class.td_CFD(frac, sigma, plot=False)[channel]
        mu, std = norm.fit(np.array(curr_tds) + h_shift)
        plt.hist(np.array(curr_tds) + h_shift, density=True, alpha=0.6, color=colour, bins=10, label="{:0.2}, std = {:0.3} ns".format(frac, std * 1e9))
        
        # gaussian fit plot
        plt.rcParams["figure.figsize"] = (7,4.5)
        
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        p = norm.pdf(x, mu, std)
        plt.plot(x, p, 'k', linewidth=2,color=colour)

        print("std for {:.1f}% CDF: {:.3f} ns".format(frac * 100, std * 1e9))
        
        h_shift += 0.1e-8
    plt.legend(fontsize=13, frameon=True)
    plt.show()