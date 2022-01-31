from tkinter import *
from guiHelperFunctions import *

def create_right_frame(frame):
    #this creates a basic tkinter skeleton of the frame
    rightFrame = Frame(frame)
    rightFrame.rowconfigure(1, weight=8)

    fig, ax1, ax2, canvas = initPlotFigures(rightFrame, 1)
    fig.canvas.callbacks.connect('pick_event', on_pick)

    return rightFrame, fig, ax1, ax2, canvas

def finish_right_frame(rightFrame, plots, fig, metadata, mean, stdev):
    #adding button with corresponding funcitons

    bframe = Frame(rightFrame)
    bframe.grid(column=0, row=2)
    Button(bframe, text='Save Plot', command = lambda: file_save(plots,fig)).grid(column=1, row=0, pady=10, padx=5)
    Button(bframe, text='Clear Plot', command = lambda: clearplots(metadata)).grid(column=0, row=0, pady=10,padx=5)
    Button(bframe, text= 'Save Plot Data', command = lambda:savedata(metadata)).grid(column=2, row=0, pady=10, padx=5)

    topFrame = Frame(rightFrame)
    topFrame.grid(column=0,row=0)
    Label(topFrame, text = 'Fitted Mean:').grid(column=0, row=0)
    Label(topFrame, textvariable = mean).grid(column=1, row=0)
    Label(topFrame, text = 'Fitted Uncertainty:').grid(column=2, row=0)
    Label(topFrame, textvariable = stdev).grid(column=3, row=0)

# Main loop to open GUI window