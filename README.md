# Introduction 
This is a colletion of code to support the LX20 project. They are not complete enough to be put in a repo on its own, but are formal enough to be tracked and share with others to support the development work

# Getting Started
No automated build process yet. The following packges are quired and can be installed with pip:
```
git clone https://southbow@dev.azure.com/southbow/Leak%20Detection%20Engineering/_git/sps_interface
git clone https://southbow@dev.azure.com/southbow/Leak%20Detection%20Engineering/_git/pipeline_simulation
pip install ./sps_interface ./pipeline_simulation pandas matplotlib numpy ipynbname
```

# Description

## Ground temperature painting
This is done with a Jupyter Notebook, which takes ground temperature profiles and its associated SPS model as input and generate an INTRAN file to paint the ground temperature of the SPS model

The notebook is ./notebooks/Ground_temperature.ipynb.

- Input:
    - SPS model: ./sps_model/*
    - Ground temperature profile: ./data/SimSuite_gound_temperature_profiles_March_24_2025.xlsx

- Output:
    - ./output/GROUND_TEMPERATURE.INC