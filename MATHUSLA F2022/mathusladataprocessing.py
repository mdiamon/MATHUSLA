from importlib.util import set_package
from multiprocessing.sharedctypes import Value
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math as math
import scipy
from scipy.stats import norm
from scipy.signal import argrelextrema
from sklearn.mixture import GaussianMixture
import os, glob
from mathuslahelpers import *



class Attenuation():
    
    """class Attenuation()


    A class defining the attenuation object, used to analyze attenuation data from the oscilliscope.

    ------------------------------
    Attributes
    ------------------------------
    x_distances (list of num): x distances over which the attenuation data was taken. Is optional, and not needed
                            for plotting histograms of the data.

    y_data (str): folder location of the data taken from the oscilloscope.

    channels (list of char): The channels on the oscilliscope on which the data was recorded. E.g. ['1', '4']

    maxx (str): 'max' or 'min', depending on where the absolute max of the data is located according to your SiPM. E.g.
                Broadcom SiPMs display the slow output inversely, so the absolute max. would be 'min'.

    colours (list of str): Colours you want when displaying your data. Automatically set if less than 4 channels provided,
                           else you need to provide them.

    ------------------------------
    Methods 
    ------------------------------
    histogram(): Plots the histogram of the (absolute) maxmimum data, and overlays a fitted gaussian. 
                 Returns the mean max. amplitude and sample standard deviation for each dataset
    
        bins (int): Number of bins you wish your histogram to have

        single_fit (Bool): Boolean describing if you want the data fitted as a single gaussian, or a mixture of Gaussians.
                           Used to plot multiple gaussians over quantized photoelectron peaks if set to False. Auto set to True.

        plot (Bool): Boolean describing if you want to histogram plotted. True automatically

    find_single_pe(): Finds single photon energy given a dataset where quantized peaks are easily seen. Will work with any csv 
                      file that it is fed, but will not produce meaningful results outside its intended use case. Prints
                      the energy of a single photoelectron for that SiPM.
        
        bins (int): Number of bins in the histogram. Needed to visualize the quantized peaks and determine how many
                    gaussians to fit in the gaussian mixture.
    
    amplitudes(): Returns the mean (absolute maximum) amplitude of each dataset in the folder as dictionary, where the keys are
                  the channels over which the data was taken.
    
    """

    def __init__(self, x_distances, y_data, channels,maxx, colors=['sandybrown','cadetblue', 'forestgreen', 'mediumorchid']):

        # Sort the data files
        self.datafiles = sorted(glob.glob(os.path.join(y_data, "*.csv")))

        self.distances = x_distances

        # Check if the channels are numbers
        if (ch for ch in channels if ch.isdigit()):
            self.channels = channels
        else: 
            raise ValueError("Ensure that your list of channels is a subset of ['1','2','3','4', ...., 'N']")
        
        # Check if file location is valid
        if not(os.path.isfile(y_data)) and not(os.path.isdir(y_data)):
            raise ValueError("The y_data you have entered is in a location that doesn't exist!")

        # Define either max. or min. (for reading oscilliscope data)
        if maxx == 'min':
            self.max='Minimum'
        elif maxx == 'max':
            self.max='Maximum'
        else:
            raise ValueError("Please input either 'max' or 'min' based on the slow output absolute maximum of your SiPM")
        
        if len(colors) < len(channels):
            raise ValueError("You have only input {:.1f} colours. You must have at least {:.1f} colours for {:.f} channels".format(len(colors), len(channels),len(channels)))
        

        self.colorroster=colors

        # set the single photon energy
        self.pevalue=None
    
    def histogram(self, bins,single_fit=True, plot=True):

        means = {}
        stds = {}
        # Initialzie all the means and stds of the histogram(s)
        for chan in self.channels:
            means[chan] = []
            stds[chan] = []

        all_amps = []
        # Plot the histogram for each file
        for f in self.datafiles:
            print(f)

            # Create a dictonary for each channel and their amplitudes.
            data = pd.read_csv(f)
            channel_amps = {}

            # Fill the dictonary with channel / amplitudes key & value.
            for chan in self.channels:
                channel_amps[chan] = np.array(data[self.max + "("+chan+")" + " (V)"])

            # Find problem points to filter out
            del_args = np.array([])
            for ch in channel_amps:
                
                #del_args = np.append(del_args, np.where(channel_amps[ch] > np.quantile(channel_amps[ch], 0.95)))
                #del_args = np.append(del_args, np.where(channel_amps[ch] < np.quantile(channel_amps[ch], 0.05)))
                del_args = np.append(del_args, np.where(abs(channel_amps[ch]) > 1e10))

            # Filter out the problem points
            for ch in channel_amps:
                del_args = del_args.astype(int)
                channel_amps[ch] =  np.delete(channel_amps[ch], del_args)

            # Now, we can plot the histograms.
            for ch in channel_amps:
                curr_ch = channel_amps[ch]
                # Single Gaussian fit (used when light intensity is too high to differentiate single photon peaks)
                if single_fit:
                    
                    mu, std = norm.fit(curr_ch)
                    if plot==True:
                        plt.hist(curr_ch, bins=bins, density=True, alpha=0.6, color=self.colorroster[int(ch) - 1], histtype='step')
                        xmin, xmax = plt.xlim()
                        x = np.linspace(xmin, xmax, 100)
                        p = norm.pdf(x, mu, std)
                        plt.plot(x, p, 'k', linewidth=2, color=self.colorroster[int(ch) - 1], label="Ch"+ch)
                    means[ch].append(mu)
                    stds[ch].append(std)
                    
                # Gaussian Mixture fit (used to differentiate different photon peaks)
                else:
                    mus, ss, wts = gaussian_fit(curr_ch, bins=bins, plot=plot)
                    means[ch].append(sorted(mus, key = lambda x:float(x)))
                    stds[ch].append(sorted(ss, key = lambda x:float(x)))
            all_amps.append(channel_amps)   
            if single_fit:
                plt.legend()
                plt.show()
                
        return means, stds, all_amps

    def find_single_pe(self, bins):
        means_dict, stds_dict = self.histogram(bins,single_fit=False, plot=False)
        
        # compute 1 PE energy for each channel 
        for ch in means_dict:
            pes=[]
            meanss = means_dict[ch]
            
            # Find the average distance between each Gaussian from the gaussian mixture model.
            for means in meanss:
                pe=0
                m = sorted(means, key = lambda x:float(x))
                prev = m[0]
                for mean in m[1:]:
                    pe += (mean-prev)
                    prev = mean
                
                pe=pe/(len(m ) - 1)
                pes.append(pe)
            avgpe = sum(pes)/len(pes) * 1000

            # Find the average std between each Gaussian from the gaussian mixture model.
            stds = stds_dict[ch]
            s=[]
            for ss in stds:
                for i in ss:
                    s.append(np.sqrt(i[0][0]))

            avgs = sum(s)/len(s) * 1000 
                
            print("\nChannel", ch, ": 1 PE is approx", round(avgpe[0],3), "+/-", round(avgs,3), " mV")

            self.pevalue = avgpe

    def amplitudes(self):

        avgmaxes = {}
        # Initialzie all the means and stds of the histogram(s)
        for ch in self.channels:
            avgmaxes[ch] = []

        for f in self.datafiles:

            # Create a dictonary for each channel and their amplitudes.
            data = pd.read_csv(f)
            channel_amps = {}

            # Fill the dictonary with channel / amplitudes key & value.
            for chan in self.channels:
                channel_amps[chan] = np.array(data[self.max + "("+chan+")" + " (V)"])

            # Find problem points to filter out
            del_args = np.array([])
            for ch in channel_amps:
                
                del_args = np.append(del_args, np.where(channel_amps[ch] > np.quantile(channel_amps[ch], 0.95)))
                del_args = np.append(del_args, np.where(channel_amps[ch] < np.quantile(channel_amps[ch], 0.05)))

            # Filter out the problem points, and find the average amplitude of the dataset.
            for ch in channel_amps:
                del_args = del_args.astype(int)
                channel_amps[ch] =  np.delete(channel_amps[ch], del_args)
                numpts =len(channel_amps[ch])
                avgmaxes[ch].append(sum(channel_amps[ch])/numpts)

        return avgmaxes

class Timing():

    """class Timing()


    A class defining the attenuation object, used to analyze attenuation data from the oscilliscope.

    ------------------------------
    Attributes
    ------------------------------
    datatype (str): Either 't@max' or 'trace'. 't@max' represents data taken using the oscilliscope functions, and 'trace'
                    Reprents pulse data taken using the trace function of the data acquisition software.

    channels (list of char): The channels on the oscilliscope on which the data was recorded. E.g. ['1', '4']

    data (file): file (or folder) where the data is located.

    ------------------------------
    Methods
    ------------------------------

    td_TAM(): Plot the histogram of the time delay data between the all channels inputted (e.g. is channels =['1', '2', '4']
              will plot the histograms of 1-2, 1-4, 2-4), using the t@max method. For more info about this method check the wiki.
              Returns the time delays between all channels in a dict. Can only be used when datatype='t@max'.

        plot (Bool): Boolean representing whether or not to plot the data. Automaticall True


    td_CFD(frac, sigma): Plots the histogram of the time delay data between all channels using the CFD method. 
                         Can only be used when datatype='trace'.

        frac (float): constant fraction used for discrimination

        sigma (int): Filtering parameter for gaussian filtering of the pulse data

        plot (Bool): Boolean representing whether or not to plot the data. Automaticall True


    single_histograms(): Plots the histogram of each channel's time data on the same plot. Only supports 't@max' datatype.

    pulsegraph(): Plots the pulses taken from trace data. Only supports 'trace' datatype.

        sigma (int): Filtering parameter for gaussian filtering of the pulse data

        stop (int): Number of traces to plot before stopping. Automatically set to 50

    """
    def __init__(self, datatype, channels, data):
        if datatype != 'trace' and datatype != 't@max':
            raise ValueError("Please entre either 'trace' or 't@max' for your type of data." )
        self.datatype=datatype

                
        if not(os.path.isfile(data)) and not(os.path.isdir(data)):
            raise ValueError("The data you have entered is in a location that doesn't exist!")


        if (ch for ch in channels if ch.isdigit()):
            self.channels = channels
        else: 
            raise ValueError("Ensure that your list of channels is a subset of ['1','2','3','4', ...., 'N']")
        
        self.data = data

    def td_TAM(self, plot=True):

        data = pd.read_csv(self.data)

        # Ensure t@max data is fed, and not trace data.
        if self.datatype != 't@max':
            raise ValueError("This function can only be called when the datatype is 't@max'. Your datatype is: ", self.datatype)
        
        timedelays = {}
        channeldata = {}

        # Initialize the dict for all the time delays between all channels. To avoid duplicates, its done in order. e.g. if channels are
        # ['1', '2', '4'] then the dict will store '1-2','1-4', '2-4' in that order.
        for i in range(len(self.channels)):
            ch_curr = self.channels[i]
            for ch_td in self.channels[i+1:]:
                key = ch_curr + '-' + ch_td
                timedelays[key] = []

        
        # Get data for each channel
        for channel in self.channels:
            channeldata[channel] = np.array(data["X at Max Y("+channel+")"])

        # Clean the data from extremities + problem points
        del_args = np.array([])
        for ch in channeldata:
            del_args = np.append(del_args, np.where(channeldata[ch] > np.quantile(channeldata[ch], 0.95)))
            del_args = np.append(del_args, np.where(channeldata[ch] < np.quantile(channeldata[ch], 0.05)))
            del_args = np.append(del_args, np.where(abs(channeldata[ch]) > 1e10))

        # Filter out the problem points
        for ch in channeldata:
            del_args = del_args.astype(int)
            channeldata[ch] =  np.delete(channeldata[ch], del_args)
        
        # Get the time delays and fill the timedelay dict
        for key in timedelays.keys():
            delay_chans = key.split("-")
            ch1 = delay_chans[0]
            ch2 = delay_chans[1]
            timedelays[key] = channeldata[ch1] - channeldata[ch2]
        
        # Create plot, if desired
        if(plot == True):
            for td_key in timedelays:

                plt.rcParams["figure.figsize"] = (6.5,4)

                td = timedelays[td_key]
                # histogram
                plt.title("T @ Max timing method: Channels"+ td_key)
                plt.xlabel("Delay (s)")
                plt.ylabel("Frequency")
                plt.axvline(td.mean(),color='k', linestyle='dashed', linewidth=1)
                plt.hist(td, density=True, alpha=0.6, color='b')


                # gaussian fit to histogram
                mu, std = norm.fit(td) # find the mean & std of the data fitted to a norm. dist.
                xmin, xmax = plt.xlim()
                x = np.linspace(xmin, xmax, 100)
                p = norm.pdf(x, mu, std)
                plt.plot(x, p, 'k', linewidth=2)
                plt.show()

                # display relevant statistics   
                mean_rounded = "{:.3f}".format((np.mean(td)) * 10 ** 9)
                sr_rounded = "{:.3f}".format((np.std(td)) * 10 ** 9)
                median_rounded = "{:.3f}".format((np.median(td)) * 10 ** 9)
                
                mean = "- Mean: " + str(mean_rounded) + " ns \\\ "
                SD = "- Standard Deviation: " + str(sr_rounded) + " ns \\\ "
                median = "- Median: " + str(median_rounded) + " ns \\\ "
                
                print(mean)
                print(SD)
                print(median)

        return timedelays
        
    def td_CFD(self, frac, sigma, plot=True):
        # Ensure t@max data is fed, and not t@max data.
        if self.datatype != 'trace':
            raise ValueError("This function can only be called when the datatype is 'trace'. Your datatype is: ", self.datatype)


        csv_files = glob.glob(os.path.join(self.data, "*.csv"))
        timedelays = {}

        if frac == 1:
            frac=0.999999999

        # Initialize the dict for all the time delays between all channels. To avoid duplicates, its done in order. e.g. if channels are
        # ['1', '2', '4'] then the dict will store '1-2','1-4', '2-4' in that order.
        for i in range(len(self.channels)):
            ch_curr = self.channels[i]
            for ch_td in self.channels[i+1:]:
                key = ch_curr + '-' + ch_td
                timedelays[key] = []
        
        # Loop through each trace taken
        for f in csv_files:
            
            breaktrue=False
            channeldata = {}
            data = pd.read_csv(f, skiprows=1)
            time = np.array(data['Time (s)'])

            # filter data and add it
            for ch in self.channels:
                pulse = np.array(data[ch+' (VOLT)'])
                channeldata[ch] = scipy.ndimage.gaussian_filter(pulse, sigma = sigma)

            # iterate through each delay you're finding, (i.e. ch1 and ch2, ch1 and ch4, etc...) and calculate the delay.
            for key in timedelays.keys():
                delay_chans = key.split("-")
                ch1 = channeldata[delay_chans[0]]
                ch2 = channeldata[delay_chans[1]]

                # Filter out problem points
                if(all(i < 0.001 for i in ch1) or all(i < 0.001 for i in ch2)):
                    break                

                # Get the indicies of where the constant fraction amplitude is located
                id_1 = get_fm(ch1, frac)
                id_2 = get_fm(ch2, frac)
                
                timedelays[key].append(time[id_1] - time[id_2])
        # Create plot, if desired
        if(plot == True):
            for td_key in timedelays:

                plt.rcParams["figure.figsize"] = (6.5,4)

                td = np.array(timedelays[td_key])
                # histogram
                plt.title("CFD Method: Channels "+ td_key)
                plt.xlabel("Delay (s)")
                plt.ylabel("Frequency")
                plt.axvline(td.mean(),color='k', linestyle='dashed', linewidth=1)
                plt.hist(td, density=True, alpha=0.6, color='b')


                # gaussian fit to histogram
                mu, std = norm.fit(td) # find the mean & std of the data fitted to a norm. dist.
                xmin, xmax = plt.xlim()
                x = np.linspace(xmin, xmax, 100)
                p = norm.pdf(x, mu, std)
                plt.plot(x, p, 'k', linewidth=2)
                plt.show()

                # display relevant statistics   
                mean_rounded = "{:.3f}".format((np.mean(td)) * 10 ** 9)
                sr_rounded = "{:.3f}".format((np.std(td)) * 10 ** 9)
                median_rounded = "{:.3f}".format((np.median(td)) * 10 ** 9)
                
                mean = "- Mean: " + str(mean_rounded) + " ns \\\ "
                SD = "- Standard Deviation: " + str(sr_rounded) + " ns \\\ "
                median = "- Median: " + str(median_rounded) + " ns \\\ "
                
                print(mean)
                print(SD)
                print(median)

        return timedelays
            
    def single_histograms(self):
        data = pd.read_csv(self.data)

        # Ensure t@max data is fed, and not trace data.
        if self.datatype != 't@max':
            raise ValueError("This function can only be called when the datatype is 't@max'. Your datatype is: ", self.datatype)
        
        channeldata = {}
        
        # Get data for each channel
        for channel in self.channels:
            channeldata[channel] = np.array(data["X at Max Y("+channel+")"])

        # Clean the data from extremities + problem points
        del_args = np.array([])
        for ch in channeldata:
            del_args = np.append(del_args, np.where(channeldata[ch] > np.quantile(channeldata[ch], 0.95)))
            del_args = np.append(del_args, np.where(channeldata[ch] < np.quantile(channeldata[ch], 0.05)))
            del_args = np.append(del_args, np.where(abs(channeldata[ch]) > 1e10))

        # Filter out the problem points
        for ch in channeldata:
            del_args = del_args.astype(int)
            channeldata[ch] =  np.delete(channeldata[ch], del_args)

        for ch in channeldata:

            plt.rcParams["figure.figsize"] = (6.5,4)

            # histogram
            plt.title("T @ Max timing method")
            plt.xlabel("Delay (s)")
            plt.ylabel("Frequency")
            plt.axvline(channeldata[ch].mean(),color='k', linestyle='dashed', linewidth=1)
            plt.hist(channeldata[ch], density=True, alpha=0.6, label=ch)


            # gaussian fit to histogram
            print("**Channel " + ch + " stats** \\")
            mu, std = norm.fit(channeldata[ch]) # find the mean & std of the data fitted to a norm. dist.
            xmin, xmax = plt.xlim()
            x = np.linspace(xmin, xmax, 100)
            p = norm.pdf(x, mu, std)
            plt.plot(x, p, 'k', linewidth=2)

            # display relevant statistics   
            mean_rounded = "{:.3f}".format((np.mean(channeldata[ch])) * 10 ** 9)
            sr_rounded = "{:.3f}".format((np.std(channeldata[ch])) * 10 ** 9)
            median_rounded = "{:.3f}".format((np.median(channeldata[ch])) * 10 ** 9)
            
            mean = "- Mean: " + str(mean_rounded) + " ns \\\ "
            SD = "- Standard Deviation: " + str(sr_rounded) + " ns \\\ "
            median = "- Median: " + str(median_rounded) + " ns \\\ \n"
            
            print(mean)
            print(SD)
            print(median)

        plt.legend(frameon=True, fontsize=13)
        plt.show()

    def pulsegraph(self, sigma, stop=50):

        if self.datatype != 'trace':
            ValueError("Can onyl graph pulses from trace data! Your datatype: ", self.datatype)

        colours=['hotpink', 'forestgreen', 'maroon', 'aqua']
        csv_files = glob.glob(os.path.join(self.data, "*.csv"))
        
        counter=0
        for f in csv_files:
            if counter==stop:
                break
            channeldata = {}
            data = pd.read_csv(f, skiprows=1)
            time = np.array(data['Time (s)'])

            # filter data and add it
            for ch in self.channels:
                pulse = np.array(data[ch+' (VOLT)'])
                channeldata[ch] = scipy.ndimage.gaussian_filter(pulse, sigma = sigma)

            # iterate through each delay you're finding, (i.e. ch1 and ch2, ch1 and ch4, etc...) and calculate the delay.
            for ch, col in zip(self.channels,colours):
                plt.xlabel("time (s)")
                plt.ylabel("voltage (v)")
                #plt.ylim(min(channeldata[ch]), max(channeldata[ch]))
                plt.plot(time, channeldata[ch],color=col, alpha=0.3)
                
            counter+=1
        plt.show()
            
            
            

            

            
