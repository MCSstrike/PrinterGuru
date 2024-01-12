# Importing all required libraries
import os
import sys
from configobj import ConfigObj
import time
import threading
from functools import partial
import vtk # Visualisation toolkit
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QVBoxLayout, QPushButton, QWidget, QSlider, QLabel
from PyQt5.QtCore import Qt  # This is to use Qt.LeftDockWidgetArea

# Definition of the main window class
class MainWindow(QMainWindow):
    # Initalises this main window object
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("3D Printer Visualiser") # Set window title
        resolution = config["SETUP"]["WindowResolution"].split("x")        # Get initial resolution from config file
        self.setGeometry(20, 20, int(resolution[0]), int(resolution[1])) # Set initial window position & size

        # vtk and menu setup
        self.setupVtkWindow() # Runs setup function for the renderer
        self.addMenuBar()     # Runs setup function for the menu bar
        self.addDockToolbar() # Runs setup function for the toolbar dock

    # Method to set up the VTK window
    def setupVtkWindow(self):
        # Create a frame and layout ready for VTK renderer initialisation
        self.frame = QFrame()             # Formats frame (container) for the 3D visualisation
        self.vl = QVBoxLayout()           # Lines up widgets vertically
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame) # Puts a embeded VTK render window inside a Qt application, in this case self.frame
        self.vl.addWidget(self.vtkWidget) # Adds the VTK render window interactor to the layout self.vl

        # Retrieves and prepares the printer model for importing and rendering
        self.getFileNames() # Get the printer model file names from the provided directory
        if (int(config["PRINTER_MODEL"]["rebuildPrinterModel"])): # Rebuilds the processed object file when set to import a new printer
            self.RebuildPrinterModel() # Calls to rebuild the printer model

        # Object setup
        model = vtk.vtkOBJImporter()       # Source object to read .stl files
        model.SetFileName("processed.obj") # Sets the file name of the obj to be converted and viewed
        filePath = config["PRINTER_MODEL"]["3DPrinterModelDirectory"] + "\\" + self.mtlFile # Generates the relative file address
        model.SetFileNameMTL(filePath)     # Sets the mtl file for the obj
        model.Read()                       # Read and import the OBJ data

        # Add the imported graphics to the renderer
        model.SetRenderWindow(self.vtkWidget.GetRenderWindow()) # Setting the renderer for the 'model' object to be rendered in
        model.Update() # Updates the model object and converts the stl to vtk format

        # Prepare rendering and interaction for printer model
        self.renderer = model.GetRenderer()                                # Gets the renderer for the model for later use
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)        # Adds the self.renderer to the QVTKRenderWindowInteractor's VTK render window to be displayed in PyQt
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor() # Gets the QVTKRenderWindowInteractor's interactor for later use
        self.customStyle = CustomInteractorStyle()
        self.interactor.SetInteractorStyle(self.customStyle)

        # Adjust camera and lighting
        self.camera = self.renderer.GetActiveCamera() # Get camera object
        self.camera.SetClippingRange(1, 10000)        # Set large clipping distance
        self.resetCameraView()                        # Reset camera view
        self.renderer.SetBackground(0.5, 0.5, 0.5)    # A light gray background
        self.interactor.Initialize()                  # Initalises the interactor to prepare it for interaction

        # Arranges and displays widgets within the main window
        self.frame.setLayout(self.vl)     # Sets self.vl QVBoxLayout instance to be displayed inside self.frame, arranged vertically
        self.setCentralWidget(self.frame) # Sets self.frame as the central widget of the main window, making it the primary content area

        # Extracting actors from the renderer
        self.actors = self.renderer.GetActors()     # Gets a list of all the actors that are a part of the scene managed by this renderer
        self.itemRanges = self.generateItemRanges() # Retrieves item ranges from the config and makes them into an array

        # Preparing to generate actor list
        self.actors.InitTraversal()                     # Sets up the collection of actors to be iterated through
        self.actorCollection = vtk.vtkActorCollection() # Creates actor collection object

        # Generating actor collection object for future reference
        for item in range(self.actors.GetNumberOfItems()): # Cycles through the number of items (number of nets in the object file)
            self.actor = self.actors.GetNextActor()        # Sets self.actor to the current actor in the list
            self.actorCollection.AddItem(self.actor)       # Adds each actor in turn to the actor collection list

        # Setting initial printer position
        XPos = int(config["DEFAULT"]["XPosition"]) # Get initial X position
        YPos = int(config["DEFAULT"]["YPosition"]) # Get initial y position
        ZPos = int(config["DEFAULT"]["ZPosition"]) # Get initial z position
        self.defaultPosition = [XPos, YPos, ZPos]        # Create position coordinate list
        self.updatePrinterPosition(self.defaultPosition) # Update printer position with coordinate list
        print(self.defaultPosition)

    # Method to reset camera position and focus
    def resetCameraView(self):
        coord = config["DEFAULT"]["cameraPosition"].split(" ")               # Gets camera position from config file
        self.camera.SetPosition(int(coord[0]), int(coord[1]), int(coord[2])) # Set camera position
        coord = config["DEFAULT"]["focalPoint"].split(" ")                     # Gets focal point from config file
        self.camera.SetFocalPoint(int(coord[0]), int(coord[1]), int(coord[2])) # Set focal point
        self.upDirection = int(config["DEFAULT"]["upDirection"]) # Gets up direction from config file
        self.cameraSetViewUp()                                   # Sets camera direction
        self.renderer.GetRenderWindow().Render()                 # Updates renderer

    # Sets the camera's up direction as specified in the config file
    def cameraSetViewUp(self):
        match self.upDirection:                 # Match value of up direction
            case 0:                             # +x
                self.camera.SetViewUp(1, 0, 0)  # Set the up direction for camera
            case 1:                             # +y
                self.camera.SetViewUp(0, 1, 0)  # Set the up direction for camera
            case 2:                             # +z
                self.camera.SetViewUp(0, 0, 1)  # Set the up direction for camera
            case 3:                             # -x
                self.camera.SetViewUp(-1, 0, 1) # Set the up direction for camera
            case 4:                             # -y
                self.camera.SetViewUp(0, -1, 1) # Set the up direction for camera
            case 5:                             # -z
                self.camera.SetViewUp(0, 0, -1) # Set the up direction for camera

    # Method to update position with position x, y, z list
    def updatePrinterPosition(self, position):
        for direction, item in enumerate(self.itemRanges): # Loops for each value in self.itemRanges (3 for items x, y, and z)
            for itemRange in item:                         # Loops for each range in item
                for i in range(itemRange[0], itemRange[1]+1):            # Loops for each value inbetweem the selected numbers
                    self.actor = self.actorCollection.GetItemAsObject(i) # Gets the actor object for each value
                    transform = vtk.vtkTransform()                       # Create a vtkTransform object for translation
                    match direction:                                         # Checks for each case of direction
                        case 0:                                              # Extruder movement ± X and ± Z
                            transform.Translate(position[0], 0, position[2]) # Translates in the X and Z direction
                        case 1:                                              # Bed movement ± Y
                            transform.Translate(0, position[1], 0)           # Translates in the Y direction
                        case 2:                                              # Gantry movement ± Z
                            transform.Translate(0, 0, position[2])           # Translates in the Z direction

                    # Updating vtk
                    self.actor.SetUserTransform(transform) # Update actor with transform changes
        self.renderer.GetRenderWindow().Render()           # Updates renderer

    # Scans model directory for file names
    def getFileNames(self):
        # Import and get printer model, .obj, and .mtl file names in specified folder
        dirList = os.listdir(config["PRINTER_MODEL"]["3DPrinterModelDirectory"]) # Lists the files in the selected folder
        for i in range(len(dirList)):            # Repeats for each file in folder (should only be 2)
            extension = dirList[i].split(".")[1] # Sets the extension to the file extension of the current file
            if extension == "mtl":               # Checks if current file is a .mtl file
                self.mtlFile = dirList[i]        # If it is a .mtl file it writes the current file name to mtlFile
            elif extension == "obj":             # Checks if current file is an .obj file
                self.objFile = dirList[i]        # If it is a .obj file it writes the current file name to objFile

    # Setup menu bar
    def addMenuBar(self):
        # Create a menu bar
        menuBar = self.menuBar()                # Adding menu bar to PyQt window
        viewMenu = menuBar.addMenu("View")      # Adding view menu to menu bar
        optionMenu = menuBar.addMenu("Options") # Adding options menu to menu bar

        # Adds dock toggle to view menu
        self.toggleDockAction = viewMenu.addAction("Toggle Dock")          # Adding toggle item to viewMenu menu
        self.toggleDockAction.setCheckable(True)                           # Lets this action display a tick box beside itself
        self.toggleDockAction.setChecked(True)                             # Sets this tick box by default
        self.toggleDockAction.triggered.connect(self.toggleDockVisibility) # Runs toggleDockVisibility method each time the action is triggered

        # Adds initial printer model setup to options menu
        self.printerModelSetup = optionMenu.addAction("Run Printer Model Setup")
        self.printerModelSetup.triggered.connect(self.toggleDockVisibility)

    # Method to toggle the dock visibility
    def toggleDockVisibility(self):
        # Toggle the visibility of the dock widget
        self.dockWidget.setVisible(not self.dockWidget.isVisible()) # Toggles the dock visibility

    #def printerItemsSetup(self):
        #

    # Method to add a dock toolbar to the main window
    def addDockToolbar(self):
        # Create a dock widget
        self.dockWidget = QDockWidget("Options", self)         # Creates a dock widget that can inside a main window or floated as a top level window on the desktop
        self.dockWidget.setAllowedAreas(Qt.LeftDockWidgetArea) # Specifies where the dock widget can be positioned within the main window

        # Create a widget to hold your buttons
        self.dockWidgetContents = QWidget()   # Creates a new empty widget
        self.dockWidgetLayout = QVBoxLayout() # Creates a new Vertical Box Layout instance

        # Adds home view button to the layout
        self.resetView = QPushButton("Home View")            # Adds rotate button
        self.dockWidgetLayout.addWidget(self.resetView)      # Adds button to widget
        self.resetView.clicked.connect(self.resetCameraView) # When pressed resets camera view


        self.sliders = []
        self.generateMovementRanges()
        print(self.movementRanges)

        for i in range(3):
            # Setting variables
            label = QLabel("", self)
            slider = QSlider(Qt.Horizontal, self)

            realMin = self.movementRanges[i][0][0]
            realMax = self.movementRanges[i][0][1]
            simMin = self.movementRanges[i][1][0]
            simMax = self.movementRanges[i][1][1]
            defaultVal = self.defaultPosition[i]

            # Setup slider widget
            self.sliders.append([label, slider, realMin, realMax, simMin, simMax, defaultVal])
            self.sliders[i][1].setMinimum(realMin)
            self.sliders[i][1].setMaximum(realMax)
            self.sliders[i][1].setValue(defaultVal)
            self.sliders[i][1].setTickInterval(1)
            self.sliders[i][1].valueChanged.connect(self.updateLabel)

            # Label for the slider
            self.sliders[i][0].setAlignment(Qt.AlignCenter)  # Center align the label text

            # Add widgets to layout
            self.dockWidgetLayout.addWidget(self.sliders[i][0])
            self.dockWidgetLayout.addWidget(self.sliders[i][1])

        self.updateLabel()

        self.dockWidgetContents.setLayout(self.dockWidgetLayout)   # Set the layout to the widget
        self.dockWidget.setWidget(self.dockWidgetContents)         # Add the widget to the dock widget
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget) # Add the dock widget to the main window

    def generateMovementRanges(self):
        xSliderPhysical = config["PRINTER_MODEL"]["XSliderPhysical"].split(" ")
        ySliderPhysical = config["PRINTER_MODEL"]["YSliderPhysical"].split(" ")
        zSliderPhysical = config["PRINTER_MODEL"]["ZSliderPhysical"].split(" ")

        xSliderSimulate = config["PRINTER_MODEL"]["XSliderSimulate"].split(" ")
        ySliderSimulate = config["PRINTER_MODEL"]["YSliderSimulate"].split(" ")
        zSliderSimulate = config["PRINTER_MODEL"]["ZSliderSimulate"].split(" ")

        self.movementRanges = []
        self.movementRanges.append([[int(xSliderPhysical[0]), int(xSliderPhysical[1])], [int(xSliderSimulate[0]), int(xSliderSimulate[1])]])
        self.movementRanges.append([[int(ySliderPhysical[0]), int(ySliderPhysical[1])], [int(ySliderSimulate[0]), int(ySliderSimulate[1])]])
        self.movementRanges.append([[int(zSliderPhysical[0]), int(zSliderPhysical[1])], [int(zSliderSimulate[0]), int(zSliderSimulate[1])]])

    def convert(self, i, value):
        #label, slider, realMin, realMax, simMin, simMax, defaultVal
        realSpan = self.sliders[i][3] - self.sliders[i][2]
        simSpan = self.sliders[i][5] - self.sliders[i][4]

        valueScaled = float(value - self.sliders[i][2]) / float(realSpan)

        return self.sliders[i][4] + (valueScaled * simSpan)

    def updateLabel(self):
        position = []
        for i in range(3):
            currentPosition = self.sliders[i][1].value()
            position.append(self.convert(i, currentPosition))
            self.sliders[i][0].setText(f"Value: {currentPosition}")

        self.updatePrinterPosition(position)

    def setChangePosition(self):
        XPos = self.xSlider.value()
        YPos = self.ySlider.value()
        ZPos = self.zSlider.value()
        position = [XPos, YPos, ZPos]
        self.updatePrinterPosition(position)
        print("X = " + str(XPos))
        print("Y = " + str(YPos))
        print("Z = " + str(ZPos))

    # Rebuilds the printer object file to be compatible with vtk
    def RebuildPrinterModel(self):
        filePath = config["PRINTER_MODEL"]["3DPrinterModelDirectory"] + "\\" + self.objFile  # Generates the relative file address
        self.rebuildObjectFile(filePath, "processed.obj") # Runs the 3D printer model file through the object processing method

        # Updating settings file
        config['PRINTER_MODEL']['rebuildPrinterModel'] = '0' # Sets the rebuildPrinterModel to 0 now that it has finished running
        config.write()                                       # Writes the config save to the settings.ini file

        # Method to use multithreading to run and process Object files

    # Opens originalFile, processes it to work with vtk and outputs to processedFile
    def rebuildObjectFile(self, originalFile, processedFile):
        # Open and process input model data and opening output file
        file = open(originalFile)      # Opens the model file as read only
        content = file.readlines() # Reads the model file into the content variable
        file.close()               # Closes the original model file
        length = len(content)      # Calculates the number of lines in the variable

        # Setting up threading variables
        numThreads = int(config['SETUP']['CPUThreads']) # Gets the number
        chunkSize = length // numThreads                # Calculate a chunk size relative to the number of threads being used
        threads = []                                    # Initialises the threads list
        outputLines = [[] for i in range(numThreads)]   # Loops to make a list of empty arrays for each thread used

        # Setting up threading actions
        for i in range(numThreads):   # Loops for each thread used
            startLine = i * chunkSize # Calculates the start line based on the chunkSize
            if i < numThreads - 1:    # True for every time apart from the last loop
                endLine = (i + 1) * chunkSize # Sets the end of the chunk to the beginning of the next
            else:                     # For the last loop
                endLine = length      # Sets the end of the chunk to the end of the file
            thread = threading.Thread(target=self.processChunk, args=(i, startLine, endLine, content, outputLines)) # Makes a new thead object with a target and arguments ready to run
            threads.append(thread) # adds the thread object to the list threads
            thread.start()         # starts all the created thread objects

        # Wait for all threads to finish
        for thread in threads: # Cycles through each thread in threads
            thread.join() # Joins the thread to the main thread

        # Write to the output file in the original order
        with open(processedFile, "w") as output: # Makes and opens processedFile document as write only
            for buffer in outputLines:             # Cycles through each line stored in outputBuffers
                output.writelines(buffer)          # Writes each line to the output file

    # Generates a structured array of items in the object file
    def generateItemRanges(self):
        # Retrieves Y, Z, X item ranges from the settings.ini file
        xItems = config["PRINTER_MODEL"]["XItems"] # Model items that make up the X axis
        yItems = config["PRINTER_MODEL"]["YItems"] # Model items that make up the Y axis
        zItems = config["PRINTER_MODEL"]["ZItems"] # Model items that make up the Z axis

        # Makes the structured array using item ranges
        itemRanges = [xItems, yItems, zItems] # Puts item range strings into an array
        output = []                           # Initialises output list
        for ranges in itemRanges:             # Loops for each value in ranges
            subOutput = []                    # Initialises sub output list
            for range in ranges.split(" "):   # Loops for each range in the split item string
                number = range.split("-")     # Splits string range into its two parts and saves into number
                subOutput.append([int(number[0]), int(number[1])]) # Appends int value of number list to subOutput
            output.append(subOutput) # Appends subOutput to the end of output
        return output                # Returns structured array

    # Function to process the printer obj to a compatible format for the vtk library
    def processChunk(self, chunkId, startLine, endLine, content, outputLines):
        for i in range(startLine, endLine): # Loops for each line this thread has to process
            output = ""                     # Initialises the output variable
            currentLine = content[i].split(" ") # Splits the line by spaces
            if (currentLine[0] == "mtllib"):    # Checks if the first section of the current line is mtllib, relating to the material library
                filePath = (config["PRINTER_MODEL"]["3DPrinterModelDirectory"] + "\\" + self.mtlFile) # Generates the relative file directory for the .mtl file
                output += currentLine[0] + " " + filePath + "\n" # Re-writes the correct .mtl file in its place
            elif (currentLine[0] == "vt"):                       # Checks if the first section of the current line is vt, relating to texture mapping
                output += currentLine[0] + " " + currentLine[1] + " " + currentLine[2] + "\n" # Writes the vt line with the correct formating
            else:                                     # For all other first sections, the line remains unchanged
                for j in range(len(currentLine) - 1): # Loops for the number of sections in the current line minus one
                    output += currentLine[j] + " "    # Builds the current line
                output += currentLine[-1]             # Adds the end of the current line separately to remove space at the end of the line
            outputLines[chunkId].append(output)       # Appends the output line to the outputBuffers array

class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, parent=None):
        self.AddObserver("MiddleButtonPressEvent", self.middleButtonPressEvent)
        self.AddObserver("MiddleButtonReleaseEvent", self.middleButtonReleaseEvent)
        self.AddObserver("MouseWheelForwardEvent", self.mouseWheelForwardEvent)
        self.AddObserver("MouseWheelBackwardEvent", self.mouseWheelBackwardEvent)
        self.AddObserver("MouseMoveEvent", self.mouseMoveEvent)
        self.isPanning = False
        self.isRotating = False

    def middleButtonPressEvent(self, obj, event):
        if self.GetInteractor().GetShiftKey():
            self.isRotating = True
            self.StartRotate()
        else:
            self.isPanning = True
            self.StartPan()
        return

    def middleButtonReleaseEvent(self, obj, event):
        if self.isPanning:
            self.isPanning = False
            self.EndPan()
        if self.isRotating:
            self.isRotating = False
            self.EndRotate()
        return

    def mouseMoveEvent(self, obj, event):
        if self.isPanning:
            self.Pan()
        elif self.isRotating:
            mainWin.cameraSetViewUp()  # Set the up direction for the camera
            self.Rotate()
        return

    def mouseWheelForwardEvent(self, obj, event):
        self.StartZoom()
        self.Zoom()
        self.EndZoom()
        return

    def mouseWheelBackwardEvent(self, obj, event):
        self.StartZoom()
        self.Zoom()
        self.EndZoom()
        return

# Reads and runs setup for the config variable
def getConfig(configFile): # Runs the config setup for the program
    # Config setup
    global config                  # Initialises global config variable
    config = ConfigObj(configFile) # ConfigObj reads the file and reads the settings.ini file

    # Debug setup
    global debug                          # Initialises global debug variable
    debug = int(config["SETUP"]["DEBUG"]) # Sets the debug variable to the integer value in the config file

    # Lists the config file to the user
    for section in config:    # Loops for each section in the config file
        print(f'[{section}]') # Prints the section name for each section
        for key, value in config[section].items():  # Loops for each value in the section
            print(f'{key} = {value}')               # Prints the key and value for each value
        print()                                     # This adds empty line for better readability
    time.sleep(int(config["SETUP"]["configDelay"])) # Waits for defined time to let the user read the config

# Main function of the script
def main():
    app = QApplication(sys.argv) # Creates a QApplication instance to handle events and widgets
    getConfig("settings.ini")    # Get configuration from settings.ini
    global mainWin               # Initialises global mainWin variable
    mainWin = MainWindow()       # Creates a MainWindow instance stored but not displayed
    mainWin.show()               # Makes the MainWindow visible
    sys.exit(app.exec_())        # Starts the applications main loop to respond to inputs and exits the application loop ends (closing the window)

# Checks if script is the main program being run
if __name__ == '__main__':
    main() # Runs the main function