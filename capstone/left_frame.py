import tkinter as tk
from tkinter import ttk
import guiHelperFunctions as gui
from meta_data_handler import meta_data_handler
from tkinter import filedialog
import csv
from linearreg import *
import matplotlib as plt
import numpy as np

def askopen(frame, filename):
    #opening t vs d plot to load
    f = filedialog.askopenfilename(filetypes=(("T vs D Data", "*TvsD.csv"),("All Files", "*.*") ))
    filename.set(f)
    frame.update()

def changetvsd(metadata, filename):
    #this is loading the t vs d raw data to the bottom right plot
    file = filename.get()
    #csv read to metadata tvsd internal structure
    with open(file, "r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for lines in csv_reader:
            for i in range(4):
                metadata.tvsd[i] = metadata.tvsd[i] + [float(lines[i])]

    metadata.plots[1].clear()

    metadata.plots[1].set_title("Timing vs. Length")
    metadata.plots[1].set_xlabel("Length (cm)")
    metadata.plots[1].set_ylabel("Time (s)")
    metadata.plots[1].plot(metadata.tvsd[0], metadata.tvsd[1], 'ro', picker=10)
    metadata.plots[1].errorbar(metadata.tvsd[0], metadata.tvsd[1], yerr=metadata.tvsd[3], xerr=metadata.tvsd[2], fmt='r+')
    metadata.canvas.draw()
    metadata.frame.update()

def linearfit(metadata, slopes, inter, derr,intererr,pi):
    #this runs the linear regression algorithm to fit the t vs d data
    result = linfit(metadata.tvsd[0], metadata.tvsd[1], metadata.tvsd[2], metadata.tvsd[3])

    x_vals = np.array(metadata.plots[1].get_xlim())
    y_vals = result[1] + result[0] * x_vals

    metadata.plots[1].plot(x_vals, y_vals, '--')
    metadata.canvas.draw()
    slopes.set(result[0])
    inter.set(result[1])
    derr.set(result[2])
    intererr.set(result[3])
    pi.set(result[4])
    metadata.frame.update()

def cald(frame, result, time, timuncer, dpos, duncer, fit):
    #this is calculating the d vs t plot uncertainty

    usererr = timuncer/time
    time = time*10**(-9)
    pos = time * result[0] + result[1]
    dpos.set(pos)

    #error from linear regression
    linregerr = np.sqrt((time * result[2]/result[0])**2 + (result[3]/result[1])**2)

    #error from fiber dispersion
    fituncer = (fit[0] * pos**2 + fit[1] * pos + fit[2])

    #total error calculated in quadrature
    totalerr = np.sqrt(linregerr**2 + usererr**2 + fituncer**2) * pos
    duncer.set(totalerr)
    frame.update()

def dvstFrame(metadata, fiblength, symmetric, degree):
    if symmetric.get() and fiblength == "":
        gui.invalidinput()

    if metadata.tvsd == [[]]*4:
        gui.invalidinput()

    win = tk.Toplevel()
    win.wm_title("DvsT Plot")

    fig, ax1, ax2, canvas = gui.initDvsTFigures(win, 0)

    ax1.plot(metadata.tvsd[1], metadata.tvsd[0], 'ro', picker=10)
    ax1.errorbar(metadata.tvsd[1], metadata.tvsd[0], xerr=metadata.tvsd[3], yerr=metadata.tvsd[2], fmt='r+')
    result = linfit(metadata.tvsd[1], metadata.tvsd[0], metadata.tvsd[3], metadata.tvsd[2], 1000000)

    absuncer = [np.sqrt((metadata.tvsd[3][i]/metadata.tvsd[1][i])**2+(metadata.tvsd[2][i]/metadata.tvsd[0][i])**2) for i in range(len(metadata.tvsd[2]))]
    dcer = metadata.tvsd[0]

    if symmetric.get():
        dcer = dcer + [float(fiblength) - i for i in metadata.tvsd[0]]
        absuncer = absuncer + absuncer

    ax2.scatter(dcer, absuncer)
    p = np.polyfit(dcer, absuncer, degree)
    xlim2 = ax2.get_xlim()
    x_vals2 = np.linspace(xlim2[0], xlim2[1], 1000)
    y_vals2 = np.zeros(1000)

    y_vals2 = y_vals2 + p[4]

    for j in range(1000):
        for i in range(0,degree):
            y_vals2[j] = y_vals2[j] + p[i] * x_vals2[j]**(degree-i)

    ax2.plot(x_vals2, y_vals2, '--')

    x_vals = np.array(ax1.get_xlim())
    y_vals = result[1] + result[0] * x_vals

    ax1.plot(x_vals, y_vals, '--')
    canvas.draw()

    dpos = tk.DoubleVar(value=0)
    duncer = tk.DoubleVar(value=0)
    timed = tk.DoubleVar(value=0)
    timuncer = tk.DoubleVar(value=0)
    iframe = tk.Frame(win)

    iframe.grid(row=1, column =0, rowspan=2, pady = 10)
    tk.Label(iframe, text = "Enter Timing Delay (ns)").grid(row=0,column = 0, padx = 10, sticky=tk.W)
    tk.Entry(iframe, textvariable = timed).grid(row=0,column = 1, padx = 10, sticky=tk.W)
    tk.Label(iframe, text = "Enter Delay Uncertainty (ns)").grid(row=0,column = 2, padx = 10, sticky=tk.W)
    tk.Entry(iframe, textvariable = timuncer).grid(row=0,column = 3, padx = 10, sticky=tk.W)

    tk.Button(iframe, text="Calculate", command = lambda : cald(win, result, timed.get(), timuncer.get(), dpos, duncer, p)).grid(row=0,column=4, padx = 10, sticky=tk.W)


    tk.Label(iframe, text = "Position Hit (cm)").grid(row=2,column = 0, padx = 10, sticky=tk.W)
    tk.Label(iframe, textvariable=dpos).grid(row=2,column = 1, padx = 10, sticky=tk.W)
    tk.Label(iframe, text = "Uncertainty").grid(row=2,column = 2, padx = 10, sticky=tk.W)
    tk.Label(iframe, textvariable=duncer).grid(row=2,column = 3, padx = 10, sticky=tk.W)


    fitFrame = tk.Frame(win)
    fitFrame.grid(row=3, column=0, pady=10)
    tk.Label(fitFrame, text = "The fitted slope is:").grid(column=0, row=1, sticky=tk.W)
    tk.Label(fitFrame, text=result[0], width = 25).grid(column=1, row=1, sticky=tk.W)

    tk.Label(fitFrame, text="The fitted Intercept is:").grid(column=0, row=2, sticky=tk.W)
    tk.Label(fitFrame, text=result[1], width=25).grid(column=1, row=2, sticky=tk.W)

    tk.Label(fitFrame, text="The standard deviation on slope is:").grid(column=0, row=3, sticky=tk.W)
    tk.Label(fitFrame, text=result[2], width=25).grid(column=1, row=3, sticky=tk.W)

    tk.Label(fitFrame, text="The standard deviation on the intercept is:").grid(column=0, row=4, sticky=tk.W)
    tk.Label(fitFrame, text=result[3], width=25).grid(column=1, row=4, sticky=tk.W)

    tk.Label(fitFrame, text="With residual variance of:").grid(column=0, row=5, sticky=tk.W)
    tk.Label(fitFrame, text=result[4], width=25).grid(column=1, row=5, sticky=tk.W)

    win.mainloop()

def create_left_frame(container, plots, canvas, mu, sigma):

    frame = tk.Frame(container)

    # grid layout for the input frame
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=2)
    frame.columnconfigure(2, weight=1)

    tk.Label(frame, text='Total counts:').grid(column=0, row=0, sticky=tk.W)
    keyword = tk.Entry(frame, width=25)
    keyword.focus()
    keyword.insert(0, '0')
    keyword.grid(column=1, row=0, sticky=tk.W)

    folderPath = gui.selectSaveDirectory(frame, 1, "Home Directory")

    tk.Label(frame, text='Fibre Name:').grid(column=0, row=2, sticky=tk.W)
    fibframe = tk.Frame(frame)
    fibframe.grid(column=1, row = 2, columnspan=1)
    selfib1 = tk.BooleanVar()
    tk.Checkbutton(fibframe, text="Fibre 1", variable=selfib1).grid(column = 1, row =1)
    selfib2 = tk.BooleanVar()
    tk.Checkbutton(fibframe, text="Fibre 2", variable=selfib2).grid(column=2, row =1)
    selfib3 = tk.BooleanVar()
    tk.Checkbutton(fibframe, text="Fibre 3", variable=selfib3).grid(column=3, row =1)

    tk.Label(frame, text='Fibre Length:').grid(column=0, row=3, sticky=tk.W)
    fiblen = tk.Entry(frame, width=25)
    fiblen.grid(column=1, row=3, sticky=tk.W)

    tk.Label(frame, text='Distance Uncertainty:').grid(column=0, row=4, sticky=tk.W)
    distway = tk.Entry(frame, width=25)
    distway.grid(column=1, row=4, sticky=tk.W)

    tk.Label(frame, text='Distance Away from Ref SiPM:').grid(column=0, row=5, sticky=tk.W)
    distuncer = tk.Entry(frame, width=25)
    distuncer.grid(column=1, row=5, sticky=tk.W)


    bottombuttonframe = tk.Frame(frame)
    bottombuttonframe.grid(row = 6, columnspan = 4)
    save = tk.BooleanVar()
    tk.Checkbutton(bottombuttonframe, text="Save All Raw Data", variable=save).grid(column = 0, row =0)

    saveall = tk.BooleanVar()
    tk.Checkbutton(bottombuttonframe, text="Save T vs D Data", variable=saveall).grid(column=1, row =0)

    metadata = meta_data_handler(frame, plots, canvas, [selfib1, selfib2, selfib3], save, saveall, mu, sigma)

    tk.Button(bottombuttonframe, text='Lock in Parameter', command = metadata.lockin).grid(column=2, row=0)
    tk.Button(bottombuttonframe, text='Run Next', command=metadata.runNext, state = 'disabled').grid(column=3, row=0)
    tk.Button(bottombuttonframe, text='Stop', command=metadata.stopscan, state = 'disabled').grid(column=4, row=0)


    separator = ttk.Separator(frame, orient='horizontal')
    separator.grid(row=7, columnspan=4, sticky = tk.EW)

    tk.Label(frame, text='Import Data:').grid(column=0, row=8, sticky=tk.W)

    readpath = tk.StringVar(value="No file selected")
    tk.Label(frame, text='Read T vs D Data:').grid(column=0, row=9, sticky=tk.W)
    tk.Label(frame, textvariable=readpath, width = 25).grid(column=1, row=9, sticky=tk.W)
    tk.Button(frame, text='Browse', command=lambda : askopen(frame, readpath)).grid(column=2, row=9, sticky=tk.W)

    slope = tk.StringVar(value="Not yet fitted")
    intercept = tk.StringVar(value="Not yet fitted")
    derr = tk.StringVar(value="Not yet fitted")
    intererr = tk.StringVar(value = "Not yet fitted")
    p = tk.StringVar(value="Not yet fitted")

    iframe = tk.Frame(frame)
    iframe.grid(row = 11, column =0, columnspan=2)

    tk.Label(iframe, text='Fiber Length').grid(column=0,row=0,sticky = tk.W, padx=5, pady=5)
    lenthent = tk.Entry(iframe, width=10)
    lenthent.grid(column=1,row=0)

    symmetric = tk.BooleanVar()
    tk.Checkbutton(iframe, text="Symmetric?", variable=symmetric).grid(column=2, row=0)

    tk.Label(iframe, text='Degree of Polynomial Fit').grid(column=3,row=0,sticky = tk.W, padx=5, pady=5)
    deg = tk.Entry(iframe, width=10)
    deg.grid(column=4,row=0)

    buttonframe = tk.Frame(frame)
    buttonframe.grid(column=1, row=10, columnspan=2)


    tk.Button(buttonframe, text='Load T vs D Data', width=15, command = lambda : changetvsd(metadata,readpath)).grid(column=2, row=0,sticky=tk.W, padx=5,pady=5)
    tk.Button(buttonframe, text='Linear Fit', command = lambda : linearfit(metadata, slope, intercept, derr, intererr, p)).grid(column=3, row=0, sticky=tk.W, padx=5,pady=5)
    tk.Button(buttonframe, text='D vs T Graph', command = lambda : dvstFrame(metadata, lenthent.get(), symmetric, int(deg.get()))).grid(column=4, row=0, sticky=tk.W, padx=5,pady=5)

    tk.Label(frame, text = "The fitted slope is:").grid(column=0, row=12, sticky=tk.W)
    tk.Label(frame, textvariable=slope, width = 25).grid(column=1, row=12, sticky=tk.W)

    tk.Label(frame, text="The fitted Intercept is:").grid(column=0, row=13, sticky=tk.W)
    tk.Label(frame, textvariable=intercept, width=25).grid(column=1, row=13, sticky=tk.W)

    tk.Label(frame, text="The standard deviation on slope is:").grid(column=0, row=14, sticky=tk.W)
    tk.Label(frame, textvariable=derr, width=25).grid(column=1, row=14, sticky=tk.W)

    tk.Label(frame, text="The standard deviation on the intercept is:").grid(column=0, row=15, sticky=tk.W)
    tk.Label(frame, textvariable=intererr, width=25).grid(column=1, row=15, sticky=tk.W)

    tk.Label(frame, text="With residual variance of:").grid(column=0, row=16, sticky=tk.W)
    tk.Label(frame, textvariable=p, width=25).grid(column=1, row=16, sticky=tk.W)
    # tk.Button(buttonframe, text='Plot Flat Color Plot', width=15).grid(column=0, row=1, sticky=tk.E, padx=5,pady=5)
    # tk.Button(buttonframe, text='Plot Full 3D Plot', width=15).grid(column=1, row=1, sticky=tk.W, padx=5,pady=5)

    # separator = ttk.Separator(frame, orient='horizontal')
    # separator.grid(row=13, columnspan=4, sticky = tk.EW)
    #
    # tk.Label(frame, text='View specific raw data:').grid(column=0, row=14, sticky=tk.W)
    # plotpath = gui.selectSaveDirectory(frame, 15, "Read Directory")
    # tk.Button(frame, text='View Plot').grid(column=2, row=16, padx=5,pady=5)

    for widget in frame.winfo_children():
        widget.grid(padx=0, pady=5)

    return frame, metadata

