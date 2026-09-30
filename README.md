
# ANSYS REINF BEAM

Fully parameterized APDL input files for reinforced concrete beam in a 4 point bending setup using two symmetry planes.

## Model

Two different model types

* 1: concrete with Drucker-Prager material model (and SOLID185 elements)
* 2: concrete with Microplane material model (and CPT215 elements)

Slightly different pre-processing between the two models

## Running

Open ANSYS Mechanical APDL Product Launcher, pick this folder, execute the input.mac file.

## Parameters

Parameters are split into material parameters (parameters_material.txt) and other parameters (parameters.txt).

## Post-processing

After running the simulation a text file with results is created. They can be plotted using the auswertung.py script.

