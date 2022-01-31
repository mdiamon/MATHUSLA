import guiHelperFunctions as gui
from left_frame import *
from right_frame import *

#creating window
window, w, h = gui.createWindow()
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)

plots = [None] * 2

#declaring global fitting variable since left frame will change it and right frame will update
mean = StringVar(value=0)
stdev = StringVar(value=0)

#declaring skeltons of rightFrame. Can't add functionality yet because metadatahandler is not declared yet
rightFrame, fig, plots[0], plots[1], canvas = create_right_frame(window)
#metadatahandler is the core all of interactive functionality and it is instantiated within the create left frame function
leftFrame, metadatahandler = create_left_frame(window, plots, canvas, mean, stdev)
#now that we have metadatahandler we can finish putting interactive capability to rightFrame
finish_right_frame(rightFrame,plots, fig, metadatahandler, mean, stdev)

#initiates menubar
menubar = gui.create_menubar(window, leftFrame)

#places the frames accordingly
leftFrame.grid(row=0, column=0, padx=20, pady=50)
rightFrame.grid(row=0, column=1, padx=20, pady=50)

window.mainloop()

