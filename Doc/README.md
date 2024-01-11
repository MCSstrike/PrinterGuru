# 3D Printer Visualiser Application

## Overview
This document provides an overview of the 3D Printer Visualiser application, a PyQt-based GUI tool that integrates VTK for 3D visualisation and real time control.

## Current Look of the Program 
![Screenshot 2024-01-11 202924.png](Screenshot%202024-01-11%20202924.png)

## Libraries Used
- **PyQt5**: Used for creating the graphical user interface (GUI).
- **VTK (Visualisation Toolkit)**: Utilised for rendering 3D graphics within the PyQt application.
- **configobj**: To manage the config file usage.
- **threading**: Giving support for multithreading for longer processes.

## Application Structure

### Main Window
The application's main window (`MainWindow`) is created as an instance of `QMainWindow`. It serves as the primary window where other widgets and layouts are added.

### VTK Integration
A `QVTKRenderWindowInteractor` widget is used to embed VTK's rendering capabilities into the PyQt application. This widget displays the 3D visualisation and handles user interactions.

### Dock Widget
A `QDockWidget` (`self.dockWidget`) is added to the left side of the main window. It is intended to hold various control elements like buttons and sliders. Currently, this dock widget contains:

- A vertical layout (`QVBoxLayout`), which organizes the contents vertically.
- A container widget (`QWidget`), which holds the layout and its contents.

### Buttons
The following buttons are added to the dock widget but are currently NON-FUNCTIONAL:
- **Rotate Sphere**: Intended to allow rotation of the 3D sphere.
- **Change Color**: Intended to change the color of the 3D sphere.

### Menu Bar
A menu bar is added to the main window with the following functionality:
- **Toggle Dock**: Allows users to show/hide the dock widget.

## Features

### Multi-threading Support to Process Printer Model
Uses multithreading to speed up complex processing
When a new printer model needs to be rebuilt from its object file. The vtk .obj importer is very specific about what it requires as an input.
By default, the .obj file produced by autodesk products such as Fusion 360 are not quite compatible with vtk's .obj importer, to fix this the entire file is read, processed, and saved as a new file. These files are very large and the processing can be effectively multithreaded, as long as care is taken to maintain order of the file. 

This 3D printer model processing will only run when the user sets the setting.ini rebuildPrinterModel variable to 1, once ran, the program will set this variable back to 0.

### Options Dock
The Dock gives further utilisation of the vtk window. It has control for the 3D printer's x, y, and z position and can reset the camera view.
The "Home View" of the camera has been designed to give you a good geometric view of the printer and any models that may be on the bed whilst blocking as little of the printer bed as possible

## Current Status
As of now, the application:
- Initializes and displays the main window with a 3D visualization area and a dockable sidebar.
- Processes the 3D Printer OBJ model file when the user sets it to do so, using multithreading for speed. This will run once then will not run again until asked to do so in order to save time on program launch after the initial launch
- Imports and renders the processed OBJ file and splits it into sections for the printer simulation
- Adds menu bar to toggle the visibility of the dock widget.
- Adds buttons within the dock widget for basic control over the vtk renderer

## Next Steps
Future development will focus on:
- Enhancing the 3D visualization capabilities and making the first 3D printer model to simulate.
- Integrating actual 3D printer controls and feedback.

