# Importing all required libraries
import os
import sys
from configobj import ConfigObj
import time
import threading
import vtk # Visualisation toolkit
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import Qt  # This is to use Qt.LeftDockWidgetArea

# Definition of the main window class
class MainWindow(QMainWindow):
    # Initalises this main window object
    def __init__(self):
        super().__init__()

        self.getConfig() # Get configuration

        # Window setup
        self.setWindowTitle("3D Printer Visualiser") # Set window title
        self.setGeometry(100, 100, 800, 600)         # Set initial window position & size

        self.setupVtkWindow() # Runs setup function for the renderer
        self.addMenuBar()     # Runs setup function for the menu bar
        self.addDockToolbar() # Runs setup function for the toolbar dock

    def getConfig(self): # Runs the config setup for the program
        self.config = ConfigObj('settings.ini') # ConfigObj reads the file and reads the settings.ini file

        for section in self.config: # Loops for each section in the config file
            print(f'[{section}]')   # Prints the section name for each section
            for key, value in self.config[section].items(): # Loops for each value in the section
                print(f'{key} = {value}')                   # Prints the key and value for each value
            print()                                         # This adds empty line for better readability

        time.sleep(int(self.config["DEFAULT"]["configDelay"])) # Waits for defined time to let the user read the config

    # Method to set up the VTK window
    def setupVtkWindow(self):
        # Create a frame and layout ready for VTK renderer initialisation
        self.frame = QFrame()             # Formats frame (container) for the 3D visualisation
        self.vl = QVBoxLayout()           # Lines up widgets vertically
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame) # Puts a embeded VTK render window inside a Qt application, in this case self.frame
        self.vl.addWidget(self.vtkWidget) # Adds the VTK render window interactor to the layout self.vl

        self.getFileNames() # Get the printer model file names from the provided directory
        if (int(self.config["PRINTER_MODEL"]["rebuildPrinterModel"])): # Rebuilds the processed object file when set to import a new printer
            self.rebuildPrinterModel()

        # Object setup
        model = vtk.vtkOBJImporter()       # Source object to read .stl files
        model.SetFileName("processed.obj") # Sets the file name of the obj to be converted and viewed
        filePath = self.config["PRINTER_MODEL"]["3DPrinterModelDirectory"] + "\\" + self.mtlFile # Generates the relative file address
        model.SetFileNameMTL(filePath)     # Sets the mtl file for the obj
        model.Read()                       # Read and import the OBJ data

        # Add the imported graphics to the renderer
        model.SetRenderWindow(self.vtkWidget.GetRenderWindow()) # Setting the renderer for the 'model' object to be rendered in
        model.Update() # Updates the model object and converts the stl to vtk format

        self.renderer = model.GetRenderer()                                # Gets the renderer for the model for later use
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)        # Adds the self.renderer to the QVTKRenderWindowInteractor's VTK render window to be displayed in PyQt
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor() # Gets the QVTKRenderWindowInteractor's interactor for later use

        # Adjust camera and lighting
        self.renderer.SetBackground(0.5, 0.5, 0.5) # A light gray background
        self.interactor.Initialize() # Initalises the interactor to prepare it for interaction

        # Arranges and displays widgets within the main window
        self.frame.setLayout(self.vl)     # Sets self.vl QVBoxLayout instance to be displayed inside self.frame, arranged vertically
        self.setCentralWidget(self.frame) # Sets self.frame as the central widget of the main window, making it the primary content area

        # Extracting actors from the renderer
        self.actors = self.renderer.GetActors()     # Gets a list of all the actors that are a part of the scene managed by this renderer
        self.itemRanges = self.generateItemRanges() # Retrieves item ranges from the config and makes them into an array

        self.actors.InitTraversal()                     # Sets up the collection of actors to be iterated through
        self.actorCollection = vtk.vtkActorCollection() # Creates actor collection object

        for item in range(self.actors.GetNumberOfItems()): # Cycles through the number of items (number of nets in the object file)
            self.actor = self.actors.GetNextActor()        # Sets self.actor to the current actor in the list
            self.actorCollection.AddItem(self.actor)       # Adds each actor in turn to the actor collection list

        XPos = int(self.config["DEFAULT"]["XPosition"])
        YPos = int(self.config["DEFAULT"]["YPosition"])
        ZPos = int(self.config["DEFAULT"]["ZPosition"])
        position = [XPos, YPos, ZPos]
        self.updatePosition(position)

    def updatePosition(self, position):
        for direction, item in enumerate(self.itemRanges):
            print("Direction " + str(direction) + " " + str(item))
            for itemRange in item:
                print("Ranges " + str(itemRange))
                for i in range(itemRange[0], itemRange[1]):
                    self.actor = self.actorCollection.GetItemAsObject(i)
                    transform = vtk.vtkTransform()  # Create a vtkTransform object
                    if direction == 0: # Extruder
                        transform.Translate(position[0], 0, 0)
                    if direction == 1: # Bed
                        transform.Translate(0, position[1], 0)
                    if direction == 2: # Gantry
                        transform.Translate(0, 0, position[2])

                    self.actor.SetUserTransform(transform)

        self.renderer.GetRenderWindow().Render()


    def getFileNames(self):
        # Import and get printer model, .obj, and .mtl file names in specified folder
        dirList = os.listdir(self.config["PRINTER_MODEL"]["3DPrinterModelDirectory"]) # Lists the files in the selected folder
        for i in range(len(dirList)):            # Repeats for each file in folder (should only be 2)
            extension = dirList[i].split(".")[1] # Sets the extension to the file extension of the current file
            if (extension == "mtl"):             # Checks if current file is a .mtl file
                self.mtlFile = dirList[i]        # If it is a .mtl file it writes the current file name to mtlFile
            elif (extension == "obj"):           # Checks if current file is an .obj file
                self.objFile = dirList[i]        # If it is a .obj file it writes the current file name to objFile

    # Setup menu bar
    def addMenuBar(self):
        # Create a menu bar
        menuBar = self.menuBar()           # Adding menu bar to PyQt window
        viewMenu = menuBar.addMenu("View") # Making viewMenu menu to pre existing menu bar

        # Add an action to toggle the dock widget
        self.toggleDockAction = viewMenu.addAction("Toggle Dock")          # Adding toggle item to viewMenu menu
        self.toggleDockAction.triggered.connect(self.toggleDockVisibility) # Runs toggleDockVisibility method each time the action is triggered

    # Method to toggle the dock visibility
    def toggleDockVisibility(self):
        # Toggle the visibility of the dock widget
        self.dockWidget.setVisible(not self.dockWidget.isVisible()) # Toggles the dock visibility

    # Method to add a dock toolbar to the main window
    def addDockToolbar(self):
        # Create a dock widget
        self.dockWidget = QDockWidget("Options", self)         # Creates a dock widget that can inside a main window or floated as a top level window on the desktop
        self.dockWidget.setAllowedAreas(Qt.LeftDockWidgetArea) # Specifies where the dock widget can be positioned within the main window

        # Create a widget to hold your buttons
        self.dockWidgetContents = QWidget()   # Creates a new empty widget
        self.dockWidgetLayout = QVBoxLayout() # Creates a new Vertical Box Layout instance

        # Add buttons to the layout
        self.rotateButton = QPushButton("Rotate Sphere")        # Adds rotate button
        self.dockWidgetLayout.addWidget(self.rotateButton)      # Adds button to widget
        self.changeColorButton = QPushButton("Change Color")    # Adds change colour button
        self.dockWidgetLayout.addWidget(self.changeColorButton) # Adds button to widget

        self.dockWidgetContents.setLayout(self.dockWidgetLayout)   # Set the layout to the widget
        self.dockWidget.setWidget(self.dockWidgetContents)         # Add the widget to the dock widget
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget) # Add the dock widget to the main window

    # Method to use multithreading to run though and process the 3D printer model file
    def rebuildPrinterModel(self):
        # Open and process input model data and opening output file
        filePath = self.config["PRINTER_MODEL"]["3DPrinterModelDirectory"] + "\\" + self.objFile # Generates the relative file address
        file = open(filePath)      # Opens the 3D Printer Model file as read only
        content = file.readlines() # Reads the 3D printer model file into the content variable
        file.close()               # Closes the original Printer 3D Model file
        length = len(content)      # Calculates the number of lines in the variable

        # Setting up threading variables
        numThreads = int(self.config['DEFAULT']['CPUThreads']) # Gets the number
        chunkSize = length // numThreads                     # Calculate a chunk size relative to the number of threads being used
        threads = []                                         # Initialises the threads list
        outputLines = [[] for i in range(numThreads)]     # Loops to make a list of empty arrays for each thread used

        # Setting up threading actions
        for i in range(numThreads):   # Loops for each thread used
            startLine = i * chunkSize # Calculates the start line based on the chunkSize
            if i < numThreads - 1:    # True for every time appart from the last loop
                endLine = (i + 1) * chunkSize # Sets the end of the chunk to the begining of the next
            else:                     # For the last loop
                endLine = length      # Sets the end of the chunk to the end of the file
            thread = threading.Thread(target=self.processChunk, args=(i, startLine, endLine, content, outputLines)) # Makes a new thead object with a target and arguments ready to run
            threads.append(thread) # adds the thread object to the list threads
            thread.start()         # starts all the created thread objects

        # Wait for all threads to finish
        for thread in threads: # Cycles through each thread in threads
            thread.join() # Joins the thread to the main thread

        # Write to the output file in the original order
        with open("processed.obj", "w") as output: # Makes and opens processed.obj document as write only
            for buffer in outputLines:             # Cycles through each line stored in outputBuffers
                output.writelines(buffer)          # Writes each line to the output file

        # Updating settings file
        self.config['PRINTER_MODEL']['rebuildPrinterModel'] = '0' # Sets the rebuildPrinterModel to 0 now that it has finished running
        self.config.write()                                       # Writes the config save to the settings.ini file

    # Generates a structured array of items in the object file
    def generateItemRanges(self):
        # Retrieves Y, Z, X item ranges from the settings.ini file
        XItems = self.config["PRINTER_MODEL"]["XItems"] # Model items that make up the X axis
        YItems = self.config["PRINTER_MODEL"]["YItems"] # Model items that make up the Y axis
        ZItems = self.config["PRINTER_MODEL"]["ZItems"] # Model items that make up the Z axis

        # Makes the structured array using item ranges
        itemRanges = [XItems, YItems, ZItems] # Puts item range strings into an array
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
                filePath = (self.config["PRINTER_MODEL"]["3DPrinterModelDirectory"] + "\\" + self.mtlFile) # Generates the relative file directory for the .mtl file
                output += currentLine[0] + " " + filePath + "\n" # Re-writes the correct .mtl file in its place
            elif (currentLine[0] == "vt"):                       # Checks if the first section of the current line is vt, relating to texture mapping
                output += currentLine[0] + " " + currentLine[1] + " " + currentLine[2] + "\n" # Writes the vt line with the correct formating
            else:                                     # For all other first sections, the line remains unchanged
                for j in range(len(currentLine) - 1): # Loops for the number of sections in the current line minus one
                    output += currentLine[j] + " "    # Builds the current line
                output += currentLine[-1]             # Adds the end of the current line separately to remove space at the end of the line
            outputLines[chunkId].append(output)    # Appends the output line to the outputBuffers array

# Main function of the script
def main():
    app = QApplication(sys.argv) # Creates a QApplication instance to handle events and widgets
    mainWin = MainWindow()       # Creates a MainWindow instance stored but not displayed
    mainWin.show()               # Makes the MainWindow visible
    sys.exit(app.exec_())        # Starts the applications main loop to respond to inputs and exits the application loop ends (closing the window)

# Checks if script is the main program being run
if __name__ == '__main__':
    main() # Runs the main function