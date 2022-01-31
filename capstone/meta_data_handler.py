import datetime

import dataAcquisitionHelperFunctions as run
import datetime
import numpy as np
import tkinter as tk
from tqdm import tqdm
import csv
import guiHelperFunctions as gui


class meta_data_handler():

    def __init__(self, frame, plots, canvas, fibchecks, save, saveall, mean, stdev):
        self.frame = frame
        self.metadata = [None] * 6
        self.dataAcq = None
        self.currfilename = None
        self.chanNumber = 0
        self.ifstopped = tk.BooleanVar()
        self.plots = plots
        self.canvas = canvas
        self.tvsd = [[]]*4
        self.fibchecks = fibchecks
        self.save = save
        self.saveall = saveall
        self.mean = mean
        self.stdev = stdev
        
        #counts, directory name, fiber length, Distance Away, uncertainty,  fiber name,

    def grab_meta_data(self):
        counter = 0
        for widget in self.frame.winfo_children():
            if counter == 5:
                break
            if widget.winfo_class() == 'Entry':
                self.metadata[counter] = widget.get()
                counter = counter + 1
        for i in range(3):
            if self.fibchecks[i].get() == True:
                self.metadata[5] = 'Fiber' + str(i+1)

    def runNext(self):
        self.dataAcq.results = []
        self.grab_meta_data()
        time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.currfilename = self.metadata[1] + '\\' + 'MATHUSLA_' + self.metadata[0] + '_' +self.metadata[5] + '_' + '_'.join(self.metadata[2:4]) + '_' + time + '.csv'
        for i in tqdm(range(int(self.metadata[0]))):
            if i % 20 == 0:
                self.plotHist()
            if self.ifstopped.get() == True:
                break
            else:
                self.dataAcq.collectData(channels=self.chanNumber)
        # Plot data
        try:
            x, pd, mu, sigma = run.curveFit(self.plots[0], array = self.dataAcq.results)
        except:
            gui.baddata()

        self.mean.set(mu)
        self.stdev.set(sigma)

        self.plotHist()

        if self.save.get():
            np.savetxt(self.currfilename, self.dataAcq.results, delimiter=",")

        self.plots[0].plot(x,pd)

        sigmad = float(self.metadata[3])
        d = float(self.metadata[4])

        self.tvsd[0] = self.tvsd[0] + [d]
        self.tvsd[1] = self.tvsd[1] + [mu]
        self.tvsd[2] = self.tvsd[2] + [sigmad]
        self.tvsd[3] = self.tvsd[3] + [sigma]

        self.plots[1].clear()
        self.plots[1].set_title("Timing vs. Length")
        self.plots[1].set_xlabel("Length (cm)")
        self.plots[1].set_ylabel("Time (s)")


        self.plots[1].plot(self.tvsd[0], self.tvsd[1], 'ro', picker=10)
        self.plots[1].errorbar(self.tvsd[0], self.tvsd[1], yerr=self.tvsd[3], xerr=self.tvsd[2], fmt='r+')

        self.canvas.draw()
        self.frame.update()

    def delete(self, ind):
        del seld.tvsd[ind]
        return 0

    def lockin(self):
        counter = 0
        bcounter = 0

        if not gui.threewayxor(self.fibchecks[0].get(), self.fibchecks[1].get(),self.fibchecks[2].get()):
            gui.invalidinput()
        for widget in self.frame.winfo_children():
            if counter < 4:
                if widget.winfo_class() == 'Entry':
                    if widget.get() == "":
                        gui.invalidinput()
                    elif counter != 1:
                        try:
                            test = float(widget.get())
                        except:
                            gui.invalidinput()
                    counter = counter + 1
        counter = 0
        for widget in self.frame.winfo_children():
            if counter < 3:
                if widget.winfo_class() == 'Entry':
                    if widget.get() == "":
                        gui.invalidinput()
                    widget.config(state = "disabled")
                    counter = counter + 1
            if widget.winfo_class() == 'Frame':
                for w in widget.winfo_children():
                    if w.winfo_class() == 'Checkbutton':
                        w.config(state="disabled")
                    if w.winfo_class() == 'Button':
                        if bcounter == 0:
                            w.config(state = "disabled")
                        if bcounter == 1 or bcounter == 2:
                            w.config(state = "normal")
                        bcounter = bcounter + 1


        self.ifstopped.set(False)
        self.grab_meta_data()
        trigParams, chanParams, timeParams, chanNumbers = run.setupOscilloscopeInput()
        self.chanNumber = chanNumbers
        dataAcq = run.dataAcquisition()
        dataAcq.prepareOscilloscope(triggerParameters=trigParams, channelParameters=chanParams,
                                    timeParameters= timeParams)

        self.dataAcq = dataAcq


    def stopscan(self):
        if not self.metadata == [None] * 6 and self.saveall.get() and self.tvsd[0]:
            time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            tvsdfilename = self.metadata[1] + '\\' + 'MATHUSLA_' + self.metadata[0] + '_' + self.metadata[5] + '_'.join(
                self.metadata[2:4]) + '_' + time + '_TvsD' +'.csv'
            print(tvsdfilename)
            with open(tvsdfilename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                for i in range(len(self.tvsd[0])):
                    print([self.tvsd[0][i], self.tvsd[1][i],self.tvsd[2][i], self.tvsd[3][i]])
                    writer.writerow([self.tvsd[0][i], self.tvsd[1][i],self.tvsd[2][i], self.tvsd[3][i]])

        self.ifstopped.set(True)
        self.tvsd = [[]]*4
        counter = 0
        bcounter = 0
        for widget in self.frame.winfo_children():
            if counter < 3:
                if widget.winfo_class() == 'Entry':
                    widget.config(state = "normal")
                    counter = counter + 1
            if widget.winfo_class() == 'Frame':
                for w in widget.winfo_children():
                    if w.winfo_class() == 'Checkbutton':
                        w.config(state="normal")
                    if w.winfo_class() == 'Button':
                        if bcounter == 0:
                            w.config(state = "normal")
                        if bcounter == 1 or bcounter == 2:
                            w.config(state = "disabled")
                        bcounter = bcounter + 1
        self.dataAcq = None

    def plotHist(self):
        # try:
        self.dataAcq.plotHistogram(self.plots[0], plotParameters = None, filename = self.currfilename, counts = int(self.metadata[0]))
        self.canvas.draw()
        self.frame.update()
        # except:
        #     print("WTF IS GOING ON")
        return 0



