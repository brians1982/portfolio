**FEA Surrogate Demonstration**

This FEA Surrogate example goes through the steps of: 
  1. Defining parameter definitions and parameter sets for model generation
  2. Creating a parametric FEA model with Abaqus scripting in Python
  3. Solving the models and extracting stress results
  4. Processing stresses to get uniform locations
  5. Training a Neural Network and checking the results

Files:
  1. <code>Generate_TrainingModels.ipynb</code> Creates sets of model parameters using random generators and saves to CSV
  2. <code>beamscript.py</code> Creates Abaqus CAE models and Input Decks for solving
  3. <code>ExtractStress.py</code> Performs Nodal averaging and extracts stress results from results files
  4. <code>Normalize_and_Train.ipynb</code> Normalizes stress positions along fillet and trains Neural Network
