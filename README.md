# Introduction

This repo contains the codes for two case studies for optimising facilities locations using location cover models. Two models are used:

- The Location Set Covering Problem (LSCP)
- Maximum Coverage Location Problem (MCLP)

Four software packages are used for these cases, which are:

- ArcGIS location-allocation (version 10.4)
- [PySpatialOpt](https://github.com/apulverizer/pyspatialopt) (based on Python 2.7)
- [FLP Solver](https://people.bath.ac.uk/ge277/index.php/flp-spreadsheet-solver/) (based on Excel and Visual Basic)
- [Maxcovr](https://github.com/huanfachen/maxcovr) (based on R 3.4.0)

# Using ArcGIS

1. To run the code using ArcGIS and Arcpy (version 10.4), you need to install and configure relevant packages appropriately. The dependencies can be found in ```mclp_lscp_wrapper_arcgis_v2.py```.
2. Run the code of ```arcgis_SF_store.py``` and ```arcgis_York_Tower.py``` in the folder of ```ArcGIS```.
3. The codes will save the results as shapefiles. Inspect the results in the saved shapefiles.
4. More on location-allocation analysis of ArcGIS can be found [here](https://pro.arcgis.com/en/pro-app/latest/tool-reference/network-analyst/add-locations.htm) and [here](https://desktop.arcgis.com/en/arcmap/10.3/tools/network-analyst-toolbox/solve-location-allocation-output.htm).

# Using PySpatialOpt

1. Install the PySpatialOpt package following the guidance [here](https://github.com/apulverizer/pyspatialopt). I suggest you create an Anaconda environment and then install all relevant packages in this environment.
2. Prerequisites of the two cases include **Arcpy** (version 10.4) and **glpk**, which is an open-source optimisation solver. To run the code, you need to install and configure these packages appropriately.
3. Run the code of ```pso_SF_Store_dist_matrix.py``` and ```pso_York_Tower_haversine_dist.py``` in the folder of ```PySpatialOpt```. (Note: pso is short for PySpatialOpt)
4. The codes will save the result as shapefiles. Inspect the results in the saved shapefiles.
5. Note that the network-based distance matrix of the San Francisco store case has been generated using Network Analyst in ArcGIS. This matrix is used for PySpatialOpt/Maxcovr/FLP Solver.

# Using FLP Solver

1. You can find the manual for FLP Solver from the official [website](https://people.bath.ac.uk/ge277/index.php/flp-spreadsheet-solver/).
2. To run the FLP Solver for the San Francisco case, go to the folder of ```FLP_Solver``` and open the Excel document of ```FLP_Spreadsheet_Solver_v2.51_SF_Case.xlsm```. This file is self-contained. The ```FLP Solver Console``` tab contains model specs, and the tab of ```1. Locations``` contains the IDs of demand locations and potential facility sites. The distance matrix is saved in the tab of ```2.Costs and Coverage```.
3. To run an MCLP, you could change the number of facilities in the 'FLP Solver Console' tab. To run an LSCP, you would need to run many MCLPs with number of facilities ranging from 1 to the maximum.
4. Note that we only provide the code for the San Francisco store case.

# Using Maxcovr

1. In your R environment, install the maxcovr package from Github:

   ```R
   # install.packages("devtools")
   devtools::install_github("huanfachen/maxcovr")
   ```

2. Run the code of ```maxcovr_York_Tower.R``` and ```maxcovr_SF_Store.R``` in the folder of ```Maxcovr```.

3. The results are saved as rds and csv files. Inspect the results. Some codes in the file of ```maxcovr_York_Tower.R``` may be helpful.

# References

[To be updated]