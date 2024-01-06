# 3D Printer Visualizer Application

## Overview
This document provides an overview of the 3D Printer Visualiser application, a PyQt-based GUI tool that integrates VTK for 3D visualisation and real time control.

## Current Look of the Program 
![Screenshot 2024-01-06 052451.png](Screenshot%202024-01-06%20052451.png)

## Libraries Used
- **PyQt5**: Used for creating the graphical user interface (GUI).
- **VTK (Visualization Toolkit)**: Utilized for rendering 3D graphics within the PyQt application.

## Application Structure

### Main Window
The application's main window (`MainWindow`) is created as an instance of `QMainWindow`. It serves as the primary window where other widgets and layouts are added.

### VTK Integration
A `QVTKRenderWindowInteractor` widget is used to embed VTK's rendering capabilities into the PyQt application. This widget displays the 3D visualization and handles user interactions.

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

## Current Status
As of now, the application:
- Initializes and displays the main window with a 3D visualization area and a dockable sidebar.
- Contains a menu bar to toggle the visibility of the dock widget.
- Includes buttons within the dock widget, but these buttons are NOT YET FUNCTIONAL.

## Next Steps
Future development will focus on:
- Implementing functionality and adding more control buttons in the dock widget.
- Enhancing the 3D visualization capabilities and making the first 3D printer model to simulate.
- Integrating actual 3D printer controls and feedback.

