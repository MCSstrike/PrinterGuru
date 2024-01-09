# Importing all required libraries
import os
import sys
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

        # Window setup
        self.setWindowTitle("3D Printer Visualiser") # Set window title
        self.setGeometry(100, 100, 800, 600)         # Set initial window position & size

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

        # Import and get printer model and mtl file names in specified folder
        printerModelDir = "Prusa-i3-MK3S"        # Printer 3D Model folder containing the .obj and related .mtl files
        dirList = os.listdir(printerModelDir)    # Lists the files in the selected folder
        for i in range(len(dirList)):            # Repeats for each file in folder (should only be 2)
            extension = dirList[i].split(".")[1] # Sets the extension to the file extension of the current file
            if (extension == "mtl"):             # Checks if current file is a .mtl file
                mtlFile = dirList[i]             # If it is a .mtl file it writes the current file name to mtlFile
            elif (extension == "obj"):           # Checks if current file is an .obj file
                objFile = dirList[i]             # If it is a .obj file it writes the current file name to objFile

        # Open and process object model to output string
        #print(printerModelDir + "\\" + objectFile)
        file = open("Prusa-i3-MK3S-v2.obj")
        content = file.readlines()
        output = ""
        length = len(content)
        for i in range(len(content)):
            print(f"{i}, {round(i/length*100, 2)}%")
            currentLine = content[i].split(" ")
            if (currentLine[0] == "mtllib"):
                output += currentLine[0] + " " + mtlFile + "\n"
            if (currentLine[0] == "vt"):
                output += currentLine[0] + " " + currentLine[1] + " " + currentLine[2] + "\n"
            else:
                for j in range(len(currentLine)-1):
                    output += currentLine[j] + " "
                output += currentLine[-1]
        file.close()

        # Open and write output string to processed.obj file
        file = open("processed.obj", "w")
        file.write(output)
        file.close()

        ### START OBJECT HERE ###
        # Object setup
        model = vtk.vtkOBJImporter()                 # Source object to read .stl files
        model.SetFileName("processed.obj")           # Sets the file name of the obj to be converted and viewed
        model.SetFileNameMTL("Prusa-i3-MK3S-v2.mtl") # Sets the mtl file for the obj
        model.Read()                                 # Read and import the OBJ data

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

    # Setup menu bar
    def addMenuBar(self):
        # Create a menu bar
        menuBar = self.menuBar() # Adding menu bar to PyQt window
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

# Main function of the script
def main():
    app = QApplication(sys.argv) # Creates a QApplication instance to handle events and widgets
    mainWin = MainWindow()       # Creates a MainWindow instance stored but not displayed
    mainWin.show()               # Makes the MainWindow visible
    sys.exit(app.exec_())        # Starts the applications main loop to respond to inputs and exits the application loop ends (closing the window)

# Checks if script is the main program being run
if __name__ == '__main__':
    main() # Runs the main function
