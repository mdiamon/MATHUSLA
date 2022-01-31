import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import os
matplotlib.use('TkAgg')

def createWindow():
    #initiate window and set default geometry
    window = tk.Tk()
    window.title("MATHUSLA Timing Measurement GUI")
    w, h = window.winfo_screenwidth(), window.winfo_screenheight()
    #window.geometry("{0}x{1}+0+0".format(w, h))
    return window, w, h

def openDirectory(folderPath, cwd):
    #function to open up directory
    folderSelected = askdirectory(initialdir="{}".format(cwd), title="Please select a folder...")
    folderPath.set(folderSelected)

def selectSaveDirectory(window, placerow, name):
    # open directory and save the selected string into the entry
    cwd = os.getcwd()
    folderPath = tk.StringVar()
    folderPath.set(cwd)
    browseLabel = tk.Label(window, text=name)
    browseEntry = tk.Entry(window, textvariable=folderPath, width = 25)
    browseButton = tk.Button(window,text="Browse",width="6",command=lambda: openDirectory(folderPath, cwd))
    
    # Locations
    browseEntry.grid(row=placerow, column=1, sticky=tk.W, pady=10)
    browseLabel.grid(row=placerow, column=0, sticky=tk.W, pady=5)
    browseButton.grid(row=placerow, column=2)

    return folderPath

def initDvsTFigures(window,row):
    #Initialize the two plots that are run in the D VS T plot
    #This function will create a figure with 2 subplots stacked horizontally

    fig, (ax1, ax2) = plt.subplots(1, 2)

    fig.set_figheight(5)
    fig.set_figwidth(10)

    ax1.set_title("D vs T")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Distance away (cm)")

    ax2.set_title("Uncertainty")
    ax2.set_xlabel("Distance away (cm)")
    ax2.set_ylabel("Percent Uncertainty")

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().grid(column=0, row = row)
    canvas.draw()

    return fig, ax1, ax2, canvas

def initPlotFigures(window, row):
    #Initialize the two plots that are run in the rightFrame
    #This function will create a figure with 2 subplots stacked vertically
    fig, ax = plt.subplots(2)

    a = ax[0]
    a.set_title("Most recent collection")
    a.set_xlabel("Time (ns)")
    a.set_ylabel("Counts")

    b = ax[1]
    b.set_title("Timing vs. Length")
    b.set_xlabel("Length (cm)")
    b.set_ylabel("Time (s)")

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().grid(column=0, row = row)
    canvas.draw()


    return fig, a, b, canvas

def threewayxor(a, b, c):
    #threewayxor to check for misinput for fiber selection
    return (a ^ b ^ c) and (not(a and b and c))

def baddata():
    #bad data collection
    win = tk.Toplevel()
    win.wm_title("Bad Data")

    l = tk.Label(win, text="Data Collected is too wild?", font=25)
    l.grid(row=0, column=0, padx=20, pady=10)

    a = tk.Button(win, text="Okay", command=win.destroy)
    a.grid(row=1, column=0, padx=20, pady=10)

    win.mainloop()

def invalidinput():
    #invalid input error catching page
    win = tk.Toplevel()
    win.wm_title("Bad Input")

    l = tk.Label(win, text="Hey! No Pressure King. But did you put something wrong in here?", font=25)
    l.grid(row=0, column=0, padx=20, pady=10)

    a = tk.Button(win, text="Yeah you right mb", command=win.destroy)
    a.grid(row=1, column=0, padx=20, pady=10)

    win.mainloop()

def on_pick(event):
    #on pick event handler for the plot
    artist = event.artist
    ind = event.ind
    x, y = artist.get_xdata()[ind[0]], artist.get_ydata()[ind[0]]
    #popup warning before the user wish to delete the point of interest
    popup_warning([x, y], ind)

    return 0

def file_save(plots, fig):
    #save the cropped graphical plot to a specified file name
    f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=(("PDF", "*.pdf"),("JPEG", "*.jpg"),("PNG", "*.png"),("All Files", "*.*") ))
    if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
        return
    extent = plots[1].get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    extent = extent.expanded(1.4, 1.8)
    extent.y1 = extent.y1 * 0.9
    fig.savefig(f, bbox_inches=extent)

def popup_warning(pos, ind):
    win = tk.Toplevel()
    win.wm_title("Hold Up")

    l = tk.Label(win, text="Are you sure you want to delete point at {} and {} ?".format(pos[0], pos[1]), font=25)
    l.grid(row=0, column=0, padx = 20, pady=10)


    buttonframe = Frame(win)
    buttonframe.grid(row = 1, column = 0, pady=10)
    #okay will call the function to delete the point
    a = ttk.Button(buttonframe, text="Okay", command=lambda : deletepoint(win ,ind))
    b = ttk.Button(buttonframe, text="Cancel", command=win.destroy)
    a.grid(row=1, column=0)
    b.grid(row=1, column=1)

    win.mainloop()

def deletepoint(frame, metadatahandler, ind):
    #delete the point from the tvsd data storage within metadatahandler
    for i in range(4):
        del metadatahandler.tvsd[i][ind[0]]

    #first clearing the plot and reset the x and y label since clearing the plot also clears them
    metadatahandler.plots[1].clear()
    metadatahandler.plots[1].set_title("Timing vs. Length")
    metadatahandler.plots[1].set_xlabel("Length (cm)")
    metadatahandler.plots[1].set_ylabel("Time (s)")

    #replotting notice that it is important to turn on the "picker" option to allow for on_pick event
    metadatahandler.plots[1].plot(metadatahandler.tvsd[0], metadatahandler.tvsd[1], 'ro', picker=10)
    metadatahandler.plots[1].errorbar(metadatahandler.tvsd[0], metadatahandler.tvsd[1], yerr=metadatahandler.tvsd[3], xerr=metadatahandler.tvsd[2], fmt='r+')

    metadatahandler.canvas.draw()
    metadatahandler.frame.update()
    frame.destroy()

def constructprofile():
    #construct experimental profile
    win = tk.Toplevel()
    win.wm_title("Construct Experiment Profile")

    win.columnconfigure(0, weight=1)
    win.columnconfigure(1, weight=2)
    win.columnconfigure(2, weight=1)

    tk.Label(win, text='Total counts:').grid(column=0, row=0, sticky=tk.W)
    keyword = tk.Entry(win, width=25)
    keyword.focus()
    keyword.insert(0, '0')
    keyword.grid(column=1, row=0, sticky=tk.W)

    folderPath = selectSaveDirectory(win, 1, "Home Directory")

    tk.Label(win, text='Fibre Name:').grid(column=0, row=2, sticky=tk.W)
    fibframe = tk.Frame(win)
    fibframe.grid(column=1, row = 2, columnspan=1)
    selfib1 = tk.BooleanVar()
    tk.Checkbutton(fibframe, text="Fibre 1", variable=selfib1).grid(column = 1, row =1)
    selfib2 = tk.BooleanVar()
    tk.Checkbutton(fibframe, text="Fibre 2", variable=selfib2).grid(column=2, row =1)
    selfib3 = tk.BooleanVar()
    tk.Checkbutton(fibframe, text="Fibre 3", variable=selfib3).grid(column=3, row =1)

    tk.Label(win, text='Fibre Length:').grid(column=0, row=3, sticky=tk.W)
    fiblen = tk.Entry(win, width=25)
    fiblen.grid(column=1, row=3, sticky=tk.W)

    tk.Label(win, text='Distance Uncertainty:').grid(column=0, row=4, sticky=tk.W)
    distuncer = tk.Entry(win, width=25)
    distuncer.grid(column=1, row=4, sticky=tk.W)

    tk.Label(win, text='Distance Away from Ref SiPM:').grid(column=0, row=5, sticky=tk.W)
    distaway = tk.Entry(win, width=25)
    distaway.grid(column=1, row=5, sticky=tk.W)

    tk.Button(win, text='Create Experiment Profile', command = lambda: saveparameter(win, keyword.get(), folderPath.get(), fiblen.get(), distuncer.get(), distaway.get(), [selfib1, selfib2, selfib3])).grid(column=2, row=6)

    for widget in win.winfo_children():
        widget.grid(padx=5, pady=5)

    win.mainloop()

def saveparameter(frame, counts, path, fiblength, disuncer, disaway, fib):

    #save experiment parameter profile
    #error checking to see if the profile is invalid
    if not threewayxor(fib[0].get(), fib[1].get(), fib[2].get()):
        invalidinput()
        return -1
    if path == "" or path == None:
        invalidinput()
        return -1
    for i in [counts, fiblength, disuncer,disaway]:
        try:
            test = float(i)
        except:
            invalidinput()
            return -1

    f = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=(("Text File", "*.txt"),("All Files", "*.*")))
    fibname = None
    for i in range(3):
        if fib[i].get() == True:
            fibname = 'Fiber' + str(i + 1)
    np.savetxt(f, [counts, path, fiblength, disuncer, disaway, fibname], fmt = '%s')
    frame.destroy()

def loadparam(leftframe):

    #load selected parameters into each fields of the left frame
    f = filedialog.askopenfilename(defaultextension=".txt", filetypes=(("Text File", "*.txt"),("All Files", "*.*")))
    data = np.loadtxt(f, dtype = 'U')
    fibselected = int(data[5][-1]) - 1
    fcounter = 0
    counter = 0
    #iterating through all the widgets within the left frame. Notice that this is a first level iteration and will not
    #go deeper - for example, if you have a frame within the frame the iteration will not process the widget inside
    #the nested frame
    for widget in leftframe.winfo_children():
        if counter < 5:
            if widget.winfo_class() == 'Entry':
                widget.delete(0, 'end')
                widget.insert(0, data[counter])
                counter = counter + 1

        if widget.winfo_class() == 'Frame':
            for w in widget.winfo_children():
                if w.winfo_class() == 'Checkbutton' and fcounter == fibselected:
                    w.select()
                    break
                fcounter = fcounter + 1
    leftframe.update()
    return 0

def clearplots(metadata):
    #resetting and clearing the plot
    #notice we need to reset the x and y label too

    metadata.tvsd = [[]] * 4

    metadata.plots[0].clear()
    metadata.plots[1].clear()
    metadata.plots[0].set_title("Most recent collection")
    metadata.plots[0].set_xlabel("Time (ns)")
    metadata.plots[0].set_ylabel("Normalized Counts")
    metadata.plots[1].set_title("Timing vs. Length")
    metadata.plots[1].set_xlabel("Length (cm)")
    metadata.plots[1].set_ylabel("Time (s)")
    metadata.canvas.draw()
    metadata.frame.update()

def savedata(metadatahandler):
    #save raw data for the t vs d plot currently in the bottom right
    tvsdfilename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=(("T vs D Data", "*TvsD.csv"),("All Files", "*.*")))
    with open(tvsdfilename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for i in range(len(metadatahandler.tvsd[0])):
            writer.writerow([metadatahandler.tvsd[0][i], metadatahandler.tvsd[1][i], metadatahandler.tvsd[2][i], metadatahandler.tvsd[3][i]])

def create_menubar(frame, leftFrame):
    #create menubar for the main frame
    menubar = tk.Menu(frame)
    frame.config(menu=menubar)

    fileMenu = tk.Menu(menubar)
    fileMenu.add_command(label="Experiment Profile Builder...", command=constructprofile)
    fileMenu.add_command(label="Load Experiment Profile", command=lambda: loadparam(leftFrame))
    fileMenu.add_command(label="Exit", command=frame.quit)

    menubar.add_cascade(label="File", menu=fileMenu)