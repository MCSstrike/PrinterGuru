# Importing all required libraries
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

        # Initialise the VTK renderer and add it to the VTK window
        self.renderer = vtk.vtkRenderer() # Create a vtkRenderer with a black background, a white ambient light, two-sided lighting turned on, a viewport of (0,0,1,1), and backface culling turned off.
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)        # Adds the self.renderer to the QVTKRenderWindowInteractor's VTK render window to be displayed in PyQt
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor() # Gets the QVTKRenderWindowInteractor's interactor for later use

        ### START OBJECT HERE ###
        # Sphere setup
        model = vtk.vtkSTLReader()            # Source object to read .stl files
        model.SetFileName("cube-Test-02.stl") # Sets the file name of the stl to be converted and viewed
        model.Update()                        # Updates the model object and converts the stl to vtk format

        modelMapper = vtk.vtkPolyDataMapper()                 # Creates a vtkpolydatamapper class to store polygonal data (vertices, lines and faces)
        modelMapper.SetInputConnection(model.GetOutputPort()) # Converts the sphere data to the mapper where it can be understood and rendered by the graphics hardware
        modelActor = vtk.vtkActor()                           # Creates a vtkactor class to represent an entity in the 3D scene
        modelActor.SetMapper(modelMapper)                     # Links the geometry provided by sphereMapper to sphereActor

        # Set sphere color
        modelActor.GetProperty().SetColor(1, 0, 0)  # Set the sphere's colour to red

        # Add the sphere actor to the renderer
        self.renderer.AddActor(modelActor) # Adds the sphere actor to the 3D scene
        ### STOP OBJECT HERE ###

        # Adjust camera and lighting
        self.renderer.SetBackground(0.3, 0.3, 0.3)  # A dark blue-ish background
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
