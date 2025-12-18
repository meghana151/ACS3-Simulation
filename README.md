# ACS3-Simulation
## Problem Statement
The aim of this project is to simulate how the ACS3 solar sail satellite would appear when observed through a 406.4 mm aperture, f/10 telescope from Earth under realistic conditions. To replicate these observational effects, Blender is used to render physically consistent images by incorporating viewing geometry, illumination conditions, and telescope parameters.
## Repository Structure
```
acs3-observation-simulation/
│
├── blender_scripts/
│   └── code.py                   # Main Blender Python script
│
├── models/
│   └── Solar Sail concept 2.lwo  # ACS3 3D model (LightWave format)
│
├── outputs/
│   └── images/
│       ├── 1262.png
│       ├── 1217.png
│       ├── 1339.png
│       └── 1101.png
│
├── final_report.pdf
│
├── README.md
└── LICENSE
```
## How to Run

## Prerequisites
- Blender 3.x or higher  
- Python enabled within Blender  

## How to Run
To set up and run the simulation locally:

### 1. Clone the repository
```bash
git clone https://github.com/your-username/acs3-observation-simulation.git
cd acs3-observation-simulation
```
### 2. Load the ACS3 model

Open Blender
Import the ACS3 model from the models directory (.lwo file)

### 3. Run the Blender script

Switch to the Scripting workspace in Blender
Open the Python script from the blender_scripts directory
Click Run Script

### 4. View outputs

Rendered images will be saved in the outputs/images directory

## Future Work

Atmospheric seeing and noise modeling

Support for multiple telescope configurations

Time-sequenced rendering of satellite passes
