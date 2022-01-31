# File: dataAcquisitionHelperFunctions.py
# Author: Andrija Paurevic
# Student Number: 1003995297
# Date: Fri Nov 12, 2021
# Description:
from scipy.stats import norm
# Import modules
try:
    import pyvisa as visa
    import sys, os, platform
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy import optimize, special
    import pylab
except ModuleNotFoundError or ImportError as error:
    print("Please check you have all the necessary modules installed correctly: {0}".format(error.msg))
    exit(1)

def setupOscilloscopeInput():
    """"""

    # Channel numbers you wish to interact/collect data on
    channelNumbers = [3, 4]

    # Trigger inputs
    trigMode = "EDGE"
    trigSource = "WGEN1"
    if "WGEN" in trigSource:
        trigLevel = ""
    else:
        trigLevel = ""

    # Time inputs
    timeMode = "MAIN"
    timeScale = 2.5
    timeOffset = 95

    # Channel inputs
    chan3BWLimit = "OFF"
    chan3Scale = 0.026
    chan3Offset = 0.070
    chan3Impedance = "FIFTy"

    chan4BWLimit = "OFF"
    chan4Scale = 0.022
    chan4Offset = 0.070
    chan4Impedance = "FIFTy"

    chan3Params = [3, chan3Scale, chan3Offset, chan3BWLimit, chan3Impedance]
    chan4Params = [4, chan4Scale, chan4Offset, chan4BWLimit, chan4Impedance]

    # Set-up arrays needed for functions
    trigParams = [trigMode, trigSource, trigLevel]
    chanParams = [chan3Params, chan4Params]
    timeParams = [timeMode, timeScale, timeOffset]

    return trigParams, chanParams, timeParams, channelNumbers

def generateCurveFitData(data):
    # Set-up histogram to extract data
    n, bins, patches = plt.hist(data, round(np.sqrt(len(data))),color="white")

    # Set-up output arrays
    x = np.array([])
    y = np.array([])
    dy = np.array([])
    for item in patches:
        # Ignore any 0 counts, this helps with data fitting
        if np.sqrt(item.get_height()) < 1:
            pass
        else:
            # Update:
            # x -> bin avg value
            # y -> counts
            # dy -> sqrt(counts)
            X,Y,DY = item.get_x(),item.get_height(),np.sqrt(item.get_height())
            x = np.append(x,X)
            y = np.append(y,Y)
            dy = np.append(dy,DY)
    return x,y,dy

def curveFit(plot, fileName = None, array = None):
    # Load data and convert to ns scale
    data = []
    if not fileName == None:
        data = np.loadtxt(fileName)
    elif not array.any() == None:
        data = array
    else:
        print("yo dumb")
        #pop up for granddad
    mu, sigma = norm.fit(data)
    x = np.linspace(min(data), max(data), len(data))
    #x, y_data, y_sigma = generateCurveFitData(data)

    # Set-up guess
    # background = 0.
    # mean = -5 * 1e-9
    # sigma = 0.15 * 1e-9
    # peakValue = len(data)/3
    # pGuess = (background, peakValue, mean,sigma)

    # Curve fit begins
    # p, cov = optimize.curve_fit(gaussian, x, y_data, p0=pGuess, sigma=y_sigma)
    pd = norm.pdf(x, mu, sigma)
    # print("Estimated parameters: ", p)
    # try:
    #     print("Estimated uncertainties: ", np.sqrt(cov.diagonal()))
    # except AttributeError:
    #     print("Not calculated; fit is bad.")

    # Plotting
    return x, pd, mu, sigma
    #plot.errorbar(x, y_data, yerr=y_sigma, fmt='r+')
    #plot.show()

class dataAcquisition:

    def __init__(self):
        """"""
        if platform.system() == "Windows":
            os.add_dll_directory("C:\\Program Files\\Keysight\\IO Libraries Suite\\bin")
            self.rm = visa.ResourceManager("ktvisa32")
            self.infiniiVision = self.rm.open_resource("USB0::2391::6076::MY60101365::0::INSTR")
            self.infiniiVision.timeout = 50000
            self.debug = 0

        if platform.system() == "Darwin":
            self.rm = visa.ResourceManager("@py")
            self.infiniiVision = self.rm.open_resource("USB0::2391::6076::MY60101365::0::INSTR")
            self.infiniiVision.timeout = 50000
            self.debug = 0
        else:
            try:
                self.rm = visa.ResourceManager("@py")
                self.infiniiVision = self.rm.open_resource("USB0::2391::6076::MY60101365::0::INSTR")
                self.infiniiVision.timeout = 50000
                self.debug = 0
            except:
                print("Using an unfamiliar system, please figure out how to connect to the oscilloscope!")

        # Set-up results array to store data
        self.results = []

    def doCommand(self, command, hideParams=False):
        """"""

        if hideParams:
            (header, data) = command.split(" ", 1)
            if self.debug:
                print("\nCmd = '%s'" % header)
        else:
            if self.debug:
                print("\nCmd = '%s'" % command)
        self.infiniiVision.write("%s" % command)
        if hideParams:
            self.checkInstrumentErrors(header)
        else:
            self.checkInstrumentErrors(command)

    def getQueryResult(self, query):
        if self.debug:
            print("Qys = '%s'" % query)
        result = self.infiniiVision.query("%s" % query)
        self.checkInstrumentErrors(query)
        return result

    def checkInstrumentErrors(self, command):
        """"""
        while True:
            errorString = self.infiniiVision.query(":SYSTem:ERRor?")
            if errorString:  # If there is an error string value.
                if errorString.find("+0,", 0, 3) == -1:  # Not "No error".
                    print("ERROR: %s, command: '%s'" % (errorString, command))
                    print("Exited because of error.")
                    sys.exit(1)
                else:  # "No error"
                    break
            else:  # :SYSTem:ERRor? should always return string.
                print("ERROR: :SYSTem:ERRor? returned nothing, command: '%s'" % command)
                print("Exited because of error.")
                sys.exit(1)

    def setTriggerParameters(self, triggerParameters=None):
        """
        Adjusts the trigger parameters remotely on the oscilloscope.

        :param triggerParameters: [type, source, trigger level (V)]
                                  e.g. ["EDGE", "WGEN2", ""] or ["EDGE","CHANnel 1", "1"]
        """

        try:
            self.doCommand(":TRIGger:MODE {}".format(triggerParameters[0]))
            self.doCommand(":TRIGger:EDGE:SLOPe POSitive")
            if "WGEN" in triggerParameters[1]:
                self.doCommand(":TRIGger:EDGE:SOURce {}".format(triggerParameters[1]))
            else:
                self.doCommand(":TRIGger:EDGE:SOURce {}".format(triggerParameters[1]))
                self.doCommand(":TRIGger:EDGE:LEVel {}".format(triggerParameters[2]))
        except:
            print("Error adjusting the trigger parameters on the Oscilloscope.")

    def setChannelParameters(self, channelParameters):
        """
        Adjusts the channel parameters remotely on the oscilloscope.

        :param channelParameters: [[Channel Number (1,2,3,4), Vertical Scale (V), Offset (V), BWLimit (ON/OFF), Impedance], [], ...]
        """

        for channel in channelParameters:
            try:
                self.doCommand(":CHANnel{0}:SCALe {1}".format(channel[0],channel[1]))
                self.doCommand(":CHANnel{0}:OFFSet {1}".format(channel[0],channel[2]))
                self.doCommand(":CHANnel{0}:BWLimit {1}".format(channel[0],channel[3]))
                self.doCommand(":CHANnel{0}:IMPedance {1}".format(channel[0],channel[4]))
            except:
                print("Error in setting channels for channel {}".format(channel[0]))

    def setTimeParameters(self, timeParameters):
        """
        Adjust the time parameters remotely on the oscilloscope

        :param timeParameters: [Mode, Horizontal Scale (ns), Position (ns)]
        """

        try:
            self.doCommand(":TIMebase:MODE {}".format(timeParameters[0]))
            self.doCommand(":TIMebase:SCALe {}E-9".format(timeParameters[1]))
            self.doCommand(":TIMebase:POSition {}E-9".format(timeParameters[2]))
        except:
            print("Error in adjusting the time parameters on the oscilloscope.")

    def digitizeChannels(self, channels):
        """
        Digitizes channels provided in order to prep them for signal measurement and data
        acquisition.

        :param channels: Array of channels that need digitizing
        """

        try:
            self.doCommand(":ACQuire:TYPE NORMal")
            self.doCommand(":DIGitize CHANnel{0},CHANnel{1}".format(channels[0],channels[1]))
        except:
            print("Error digitizing signals, please double check your code.")

    def measureSignals(self, channels):
        """"""

        try:
            query = ":MEASure:DELay? CHANnel{0},CHANnel{1}".format(channels[0],channels[1])
            delay = self.getQueryResult(query)
            return delay
        except:
            print("Error in measuring the delay between the two channel signals.")

    def returnOscilloscopeID(self):
        idnString = self.getQueryResult("*IDN?")
        print("Identification String: {}".format(idnString))

    def prepareOscilloscope(self, triggerParameters, channelParameters, timeParameters):
        """"""

        self.returnOscilloscopeID()

        self.setTriggerParameters(triggerParameters)

        self.setChannelParameters(channelParameters)

        self.setTimeParameters(timeParameters)

    def collectData(self, channels):
        """"""

        self.digitizeChannels(channels)
        delay = self.measureSignals(channels)
        self.storeData(float(delay))

    def storeData(self, data):
        """"""
        self.results += [data]

#to delete
    def plotHistogram(self, plot, plotParameters, filename, counts):
        """"""
        #fibreName = "Y-11J"
        plot.clear()
        plot.set_title("Most recent collection")
        plot.set_xlabel("Time (ns)")
        plot.set_ylabel("Normalized Counts")
        plot.hist(self.results,bins=int(np.sqrt(counts)),density=True)


