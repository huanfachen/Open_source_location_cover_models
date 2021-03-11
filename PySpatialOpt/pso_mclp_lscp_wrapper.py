# -*- coding: UTF-8 -*-
import logging
import arcpy
import pulp
from pyspatialopt.analysis import arcpy_analysis
from pyspatialopt.models import utilities
from pyspatialopt.models import covering
import timeit
import os
import pandas as pd
from functools import partial

logger = None

def load_package():
    """
    Load important packages and modules
    """
    import logging
    import arcpy
    import pulp
    from pyspatialopt.analysis import arcpy_analysis
    from pyspatialopt.models import utilities
    from pyspatialopt.models import covering
    import timeit
    import os
    import pandas as pd
    from functools import partial

def set_logger(new_log):
    global logger
    logger = new_log

def test_logger():
    logger.info("Success!")

def mclp_solver(env_path, demand_point, facility_service_area, attr_demand, id_demand_point, id_facility, num_facility, id_facility_as_string = True):
    """
    Solve a MCLP using the given inputs and parameters. This function will overwrite the FeatureClass called mclp_analysis_layer
    :param env_path: (string) Path of the env
    :param demand_point: (string) File name of the demand point layer
    :param facility_service_area: (string) File name of the facility service areas
    :param attr_demand: (int or float) the attribute of demand
    :param id_demand_point: (int or string) the ID attribute in demand_point
    :param id_facility: (int or string) the ID attribute in facility_service_area
    :param num_facility: (int) Number of facilities to site
    :param id_facility_as_string: (boolean) whether the ID attribute of facilities is string
    :return: (A dict of objects) [demand_coverage, n_facility, list_id_facility]
    """
    # demand layer
    demand_polygon_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, demand_point)).getOutput(0)
    # service layer
    facility_service_areas_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, 
        facility_service_area)).getOutput(0)
    # Create binary coverage (polygon) dictionary structure
    # Use "demand" of each polygon as demand,
    # Use "id" as the unique field
    # Use "object_id" as the unique id for the facilities
    print(arcpy.Describe(facility_service_areas_fl).shapeType)
    binary_coverage_polygon = arcpy_analysis.generate_binary_coverage(demand_polygon_fl, facility_service_areas_fl,
                                                                      attr_demand,
                                                                      id_demand_point, 
                                                                      id_facility)
    # Create the mclp model
    # Maximize the total coverage (binary polygon) using at most 5 out of 8 facilities
    # logger.info("Creating MCLP model...")
    mclp = covering.create_mclp_model(binary_coverage_polygon, {"total": num_facility})
    # Solve the model using GLPK
    print("Solving MCLP...")
    mclp.solve(pulp.GLPK())
    # print(mclp.variables())

    # get the ids not covered
    # print('Demand not covered: ')
    # for var in mclp.variables():
    #     if var.name.split("$")[0] == "Y":
    #         if var.varValue < 1.0:
    #             print(var.name)

    # get the ids covered
    print('Demand covered: ')
    list_objectid_dem_covered = []
    for var in mclp.variables():
        if var.name.split("$")[0] == "Y":
            if var.varValue >= 1.0:
                list_objectid_dem_covered.append(var.name.split("$")[1])
    print list_objectid_dem_covered

    # get rid of the file postfix: .shp
    # example: york_facility_sample_buffer_100
    facility_layer_name = os.path.splitext(facility_service_area)[0]
    # print(facility_layer_name)
    ids = utilities.get_ids(mclp, facility_layer_name)
    print 'List of selected facilities: ', ids

    # As the attribute object_id is a string type, the 'wrap_values_in_quotes' should be set as True
    select_query = arcpy_analysis.generate_query(ids, unique_field_name=id_facility, wrap_values_in_quotes=id_facility_as_string)
    logger.info("Output query to use to generate maps is: {}".format(select_query))
    
    # Determine how much demand is covered by the results
    facility_service_areas_fl.definitionQuery = select_query
    
    total_coverage = arcpy_analysis.get_covered_demand(demand_polygon_fl, attr_demand, "binary",
                                                       facility_service_areas_fl)
    
    logger.info(total_coverage)
    logger.info(binary_coverage_polygon["totalDemand"])
    # logger.info("{0:.2f}% of demand is covered".format((100 * total_coverage) / binary_coverage_polygon["totalDemand"]))
    result = {}
    result["demand_coverage"] = (total_coverage) / binary_coverage_polygon["totalDemand"]
    result["n_facility"] = num_facility
    result["list_id_facility"] = " ".join(str(x) for x in ids)
    print result["list_id_facility"]
    return result

def mclp_batch_solver(env_path, demand_point, facility_service_area, attr_demand, id_demand_point, id_facility, list_num_facility, id_facility_as_string=True):
    """
    Solve multiple MCLPs using the given inputs and a list of number of facilities. This function will call the function of mclp_solver
    :param env_path: (string) Path of the env
    :param road_network: (string) File name of the network layer
    :param demand_point: (string) File name of the demand point layer
    :param facility_service_area: (string) File name of the facility service areas
    :param list_num_facility: (list of int) A list of number of facilities to site
    :param id_facility_as_string: (boolean) whether the ID attribute of facilities is string
    :return: (A Pandas dataframe) A dataframe with the column names of [n_facility, comp_sec, demand_coverage, list_id_facility]
    """
    # to calculate the time: timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
    # print env_path
    
    list_timing = []
    list_cover_prop = []
    list_id_facility = []
    for p_fac in list_num_facility:
        # repeat for three times
        newFunc = partial(mclp_solver, env_path=env_path, demand_point=demand_point, facility_service_area=facility_service_area, num_facility=p_fac, id_demand_point=id_demand_point, id_facility=id_facility, attr_demand=attr_demand, id_facility_as_string=id_facility_as_string)
        res_timing = timeit.repeat(newFunc, repeat=3, number=1)
        res_mclp = newFunc()
        list_cover_prop.append(res_mclp["demand_coverage"])
        list_timing.append(sum(res_timing)/(float(len(res_timing))))
        list_id_facility.append(" ".join(str(x) for x in res_mclp["list_id_facility"]))
    
    df_res = pd.DataFrame({'n_facility':list_num_facility, 'comp_sec':list_timing, "demand_coverage":list_cover_prop, "list_id_facility":list_id_facility})
    return df_res   

def lscp_solver(env_path, demand_point, facility_service_area, attr_demand, id_demand_point, id_facility, id_facility_as_string = True):
    """
    Solve a LSCP using the given inputs and parameters
    :param env_path: (string) Path of the env
    :param demand_point: (string) File name of the demand point layer
    :param facility_service_area: (string) File name of the facility service areas
    :param id_facility_as_string: (boolean) whether the ID attribute of facilities is string
    :return: (A dict of objects) [demand_coverage, n_facility, list_id_facility]
    """
        # demand layer
    demand_polygon_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, demand_point)).getOutput(0)
    # service layer
    facility_service_areas_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, 
        facility_service_area)).getOutput(0)
    # Create binary coverage (polygon) dictionary structure
    # Use "demand" of each polygon as demand,
    # Use "id" as the unique field
    # Use "object_id" as the unique id for the facilities
    binary_coverage_polygon = arcpy_analysis.generate_binary_coverage(demand_polygon_fl, facility_service_areas_fl,
                                                                      attr_demand,
                                                                      id_demand_point, id_facility)
    # Create the mclp model
    # Maximize the total coverage (binary polygon) using at most 5 out of 8 facilities
    logger.info("Creating LSCP model...")

    lscp = covering.create_lscp_model(binary_coverage_polygon)
    # Solve the model using GLPK
    # logger.info("Solving MCLP...")
    lscp.solve(pulp.GLPK())

    # get rid of the file postfix: .shp
    # example: york_facility_sample_buffer_100
    facility_layer_name = os.path.splitext(facility_service_area)[0]
    # print(facility_layer_name)
    ids = utilities.get_ids(lscp, facility_layer_name)
    # print "List of IDs: ", ids

    select_query = arcpy_analysis.generate_query(ids, unique_field_name=id_facility, wrap_values_in_quotes=id_facility_as_string)
    # logger.info("Output query to use to generate maps is: {}".format(select_query))
    # Determine how much demand is covered by the results
    facility_service_areas_fl.definitionQuery = select_query
    total_coverage = arcpy_analysis.get_covered_demand(demand_polygon_fl, attr_demand, "binary",
                                                       facility_service_areas_fl)
  
    # logger.info("{0:.2f}% of demand is covered".format((100 * total_coverage) / binary_coverage_polygon["totalDemand"]))
    result = {}
    print "Total demand is: ", binary_coverage_polygon["totalDemand"]

    result["demand_coverage"] = (total_coverage) / binary_coverage_polygon["totalDemand"]
    # number of facilities used
    result["n_facility"] = len(ids)

    result["list_id_facility"] = " ".join(str(x) for x in ids)
    
    return result

def generate_binary_coverage_from_dist_matrix(fl, list_dict_facility_demand_distance, dl_id_field, fl_id_field, dist_threshold, demand_field="demand", distance_field="distance", fl_variable_name=None):
    """
    Generates a dictionary representing the binary coverage of a facility to demand points
    :param fl: (Feature Layer) The facility service area polygon layer
    :param list_dict_facility_demand_distance: (string) A dictionary containing pairwise distance and demand
    :param dl_id_field: (string) The name of the demand point id field in the list_dict_facility_demand_distance object
    :param fl_id_field: (string) The name of the facility id field in the list_dict_facility_demand_distance object AND fl
    :param demand_field: (string) The name of demand weight field in the list_dict_facility_demand_distance object
    :param distance_field: (string) The name of distance in metres field in the list_dict_facility_demand_distance object
    :param dist_threshold：(Numeric) The distance threshold
    :param fl_variable_name: (string) The name to use to represent the facility variable
     
    :return: (dictionary) A nested dictionary storing the coverage relationships
    """
    # need to review the codes
    # Check parameters so we get useful exceptions and messages

    if fl_variable_name is None:
        fl_variable_name = os.path.splitext(os.path.basename(arcpy.Describe(fl).name))[0]

    logging.getLogger().info("Initializing facilities in output...")
    
    output = {
        # "version": version.__version__,
        "version": "1",
        "type": {
            "mode": "coverage",
            "type": "binary",
        },
        "demand": {},
        "totalDemand": 0.0,
        "totalServiceableDemand": 0.0,
        "facilities": {fl_variable_name: []}
    }

    # List all facilities
    with arcpy.da.SearchCursor(fl, [fl_id_field]) as cursor:
        for row in cursor:
            output["facilities"][fl_variable_name].append(str(row[0]))

    logging.getLogger().info("Determining binary coverage for each demand unit...")
    # logic: iterate over the data frame. If the demand id is not in the output, add an empty item. Then, check out if the facility covers the demand. If so, add to the list of coverage.
    # for each demand unit
    for row in list_dict_facility_demand_distance:
        # row: [dl_id_field, fl_id_field, distance, demand_field]

        # add new key if necessary
        if str(row[dl_id_field]) not in output["demand"]:
            output["demand"][str(row[dl_id_field])] = {
            "area": 0,
            "demand": float(row[demand_field]),
            "serviceableDemand": 0.0,
            "coverage": {fl_variable_name: {}}
        }
        if float(row[distance_field]) <= dist_threshold:
            output["demand"][str(row[dl_id_field])]["serviceableDemand"] = \
                output["demand"][str(row[dl_id_field])]["demand"]
            output["demand"][str(row[dl_id_field])]["coverage"][fl_variable_name][str(row[fl_id_field])] = 1

    # summary
    for row in output["demand"].values():
        output["totalServiceableDemand"] += row["serviceableDemand"]
        output["totalDemand"] += row["demand"]    
    logging.getLogger().info("Binary coverage successfully generated.")
    return output

def mclp_solver_coverage_dict(dict_coverage, env_path, demand_point, facility_service_area, attr_demand, id_demand_point, id_facility, num_facility, id_facility_as_string = True):
    """
    Solve a MCLP using the given inputs and parameters. This function will overwrite the FeatureClass called mclp_analysis_layer. A coverage dictionary is provided as a parameter.
    :param dict_coverage: (dictionary) Dictionay of coverage
    :param env_path: (string) Path of the env
    :param demand_point: (string) File name of the demand point layer
    :param facility_service_area: (string) File name of the facility service areas
    :param attr_demand: (int or float) the attribute of demand
    :param id_demand_point: (int or string) the ID attribute in demand_point
    :param id_facility: (int or string) the ID attribute in facility_service_area
    :param num_facility: (int) Number of facilities to site
    :param id_facility_as_string: (boolean) whether the ID attribute of facilities is string
    :return: (A dict of objects) [demand_coverage, n_facility, list_id_facility]
    """
    # demand layer
    demand_polygon_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, demand_point)).getOutput(0)
    # # service layer
    # facility_service_areas_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, 
    #     facility_service_area)).getOutput(0)
    # # Create binary coverage (polygon) dictionary structure
    # # Use "demand" of each polygon as demand,
    # # Use "id" as the unique field
    # # Use "object_id" as the unique id for the facilities
    # print(arcpy.Describe(facility_service_areas_fl).shapeType)
    # binary_coverage_polygon = arcpy_analysis.generate_binary_coverage(demand_polygon_fl, facility_service_areas_fl,
    #                                                                   attr_demand,
    #                                                                   id_demand_point, 
    #                                                                   id_facility)

    binary_coverage_polygon = dict_coverage
    # Create the mclp model
    # Maximize the total coverage (binary polygon) using at most 5 out of 8 facilities
    # logger.info("Creating MCLP model...")
    mclp = covering.create_mclp_model(binary_coverage_polygon, {"total": num_facility})
    # Solve the model using GLPK
    print("Solving MCLP...")
    mclp.solve(pulp.GLPK())
    # print(mclp.variables())

    # get the ids not covered
    # print('Demand not covered: ')
    # for var in mclp.variables():
    #     if var.name.split("$")[0] == "Y":
    #         if var.varValue < 1.0:
    #             print(var.name)

    # # get the ids covered
    # print('Demand covered: ')
    # list_objectid_dem_covered = []
    # for var in mclp.variables():
    #     if var.name.split("$")[0] == "Y":
    #         if var.varValue >= 1.0:
    #             list_objectid_dem_covered.append(var.name.split("$")[1])
    # print list_objectid_dem_covered

    # get rid of the file postfix: .shp
    # example: york_facility_sample_buffer_100
    facility_layer_name = os.path.splitext(facility_service_area)[0]
    # print(facility_layer_name)
    ids = utilities.get_ids(mclp, facility_layer_name)
    print 'List of selected facilities: ', ids

    # As the attribute object_id is a string type, the 'wrap_values_in_quotes' should be set as True
    select_query = arcpy_analysis.generate_query(ids, unique_field_name=id_facility, wrap_values_in_quotes=id_facility_as_string)
    logger.info("Output query to use to generate maps is: {}".format(select_query))
    
    # Determine how much demand is covered by the results
    # Write a new function
    total_coverage = 0
    # iterate over all demand points
    for row in binary_coverage_polygon["demand"].values():
        list_facility_id_covering = row["coverage"].values()[0].keys()
        # print(list_facility_id_covering)
        # print(type(list_facility_id_covering))
        # iterate over all selected facilities
        for selected_fac_id in ids:
            # if a selected facility id is in the covering list, then add its demand to total_coverage and break
            if selected_fac_id in list_facility_id_covering:
                total_coverage += row["serviceableDemand"]
                break

    # facility_service_areas_fl.definitionQuery = select_query
    
    # total_coverage = arcpy_analysis.get_covered_demand(demand_polygon_fl, attr_demand, "binary",
    #                                                    facility_service_areas_fl)
    
    logger.info(total_coverage)
    logger.info(binary_coverage_polygon["totalDemand"])
    # logger.info("{0:.2f}% of demand is covered".format((100 * total_coverage) / binary_coverage_polygon["totalDemand"]))
    result = {}
    result["demand_coverage"] = (total_coverage) / binary_coverage_polygon["totalDemand"]
    result["n_facility"] = num_facility
    result["list_id_facility"] = " ".join(str(x) for x in ids)
    print result["list_id_facility"]
    return result

def mclp_batch_solver_coverage_dict(dict_coverage, env_path, demand_point, facility_service_area, attr_demand, id_demand_point, id_facility, list_num_facility, id_facility_as_string=True):
    """
    Solve multiple MCLPs using the given inputs and a list of number of facilities. This function will call the function of mclp_solver
    :param dict_coverage: (dictionary) Dictionay of coverage
    :param env_path: (string) Path of the env
    :param road_network: (string) File name of the network layer
    :param demand_point: (string) File name of the demand point layer
    :param facility_service_area: (string) File name of the facility service areas
    :param list_num_facility: (list of int) A list of number of facilities to site
    :param id_facility_as_string: (boolean) whether the ID attribute of facilities is string
    :return: (A Pandas dataframe) A dataframe with the column names of [n_facility, comp_sec, demand_coverage, list_id_facility]
    """
    # to calculate the time: timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
    # print env_path
    
    list_timing = []
    list_cover_prop = []
    list_id_facility = []
    for p_fac in list_num_facility:
        # repeat for three times
        newFunc = partial(mclp_solver_coverage_dict, dict_coverage = dict_coverage, env_path=env_path, demand_point=demand_point, facility_service_area=facility_service_area, num_facility=p_fac, id_demand_point=id_demand_point, id_facility=id_facility, attr_demand=attr_demand, id_facility_as_string=id_facility_as_string)
        res_timing = timeit.repeat(newFunc, repeat=3, number=1)
        res_mclp = newFunc()
        list_cover_prop.append(res_mclp["demand_coverage"])
        list_timing.append(sum(res_timing)/(float(len(res_timing))))
        list_id_facility.append(" ".join(str(x) for x in res_mclp["list_id_facility"]))
    
    df_res = pd.DataFrame({'n_facility':list_num_facility, 'comp_sec':list_timing, "demand_coverage":list_cover_prop, "list_id_facility":list_id_facility})
    return df_res   

def lscp_solver_coverage_dict(dict_coverage, env_path, demand_point, facility_service_area, attr_demand, id_demand_point, id_facility, id_facility_as_string = True):
    """
    Solve a LSCP using the given inputs and parameters
    :param dict_coverage: (dictionary) Dictionay of coverage
    :param env_path: (string) Path of the env
    :param demand_point: (string) File name of the demand point layer
    :param facility_service_area: (string) File name of the facility service areas
    :param attr_demand: (string) Field name of demand weight. Not used now
    :param id_facility_as_string: (boolean) whether the ID attribute of facilities is string
    :return: (A dict of objects) [demand_coverage, n_facility, list_id_facility]
    """
    # demand layer
    demand_polygon_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, demand_point)).getOutput(0)
    # service layer
    facility_service_areas_fl = arcpy.MakeFeatureLayer_management(os.path.join(env_path, 
        facility_service_area)).getOutput(0)
    # Create binary coverage (polygon) dictionary structure
    # Use "demand" of each polygon as demand,
    # Use "id" as the unique field
    # Use "object_id" as the unique id for the facilities
    
    binary_coverage_polygon = dict_coverage

    # Create the mclp model
    # Maximize the total coverage (binary polygon) using at most 5 out of 8 facilities
    logger.info("Creating LSCP model...")

    lscp = covering.create_lscp_model(binary_coverage_polygon)
    # Solve the model using GLPK
    # logger.info("Solving MCLP...")
    lscp.solve(pulp.GLPK())

    # get rid of the file postfix: .shp
    # example: york_facility_sample_buffer_100
    facility_layer_name = os.path.splitext(facility_service_area)[0]
    # print(facility_layer_name)
    ids = utilities.get_ids(lscp, facility_layer_name)
    # print "List of IDs: ", ids

    # select_query = arcpy_analysis.generate_query(ids, unique_field_name=id_facility, wrap_values_in_quotes=id_facility_as_string)
    # # logger.info("Output query to use to generate maps is: {}".format(select_query))
    # # Determine how much demand is covered by the results
    # facility_service_areas_fl.definitionQuery = select_query
    # total_coverage = arcpy_analysis.get_covered_demand(demand_polygon_fl, attr_demand, "binary",
    #                                                    facility_service_areas_fl)
  
    # # logger.info("{0:.2f}% of demand is covered".format((100 * total_coverage) / binary_coverage_polygon["totalDemand"]))
    result = {}
    print "Total demand is: ", binary_coverage_polygon["totalDemand"]

    # result["demand_coverage"] = (total_coverage) / binary_coverage_polygon["totalDemand"]

    result["demand_coverage"] = 1.0
    # number of facilities used
    result["n_facility"] = len(ids)

    result["list_id_facility"] = " ".join(str(x) for x in ids)
    
    return result

if __name__ == "__main__":

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    # paths for testing. May change if needed.
    # workspace_path = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample'
    # links_ND2 = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\links_ND2.nd'
    # york_facility_sample_point = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\york_facility_sample_point.shp'
    # york_crime_sample_point = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\york_crime_sample_point.shp'
    # outpath = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\Outputs'

    workspace_path = r'N:\SpOpt\York_Tower'
    links_ND2 = r'links_ND2.nd'
    # york_facility_sample_point = r'york_facility_sample_point.shp'
    # york_facility_sample_service_area = r'york_facility_buffer_100.shp'
    york_facility_sample_service_area = r'york_facility_sample_buffer_100.shp'
    york_crime_sample_point = r'york_crime_sample_point.shp'
    outpath = r'Outputs'
    service_dist = 100
    p_facility = 3
    list_p_fac = range(1, 5)
    case = "York_Tower_sample"

    #######################################
    ## test MCLP
    print 'Solve MCLP'
    mclp_func = partial(mclp_solver, env_path = workspace_path, demand_point = york_crime_sample_point, facility_service_area = york_facility_sample_service_area, num_facility = p_facility, id_demand_point = "id", id_facility="object_id", attr_demand="demand")
    mclp_res = mclp_func()
    timing_mclp = timeit.repeat(mclp_func, repeat=3, number=1)
    print "Seconds of MCLP: ", sum(timing_mclp)/float(len(timing_mclp))

    ## MCLP results
    # print 'Computation time in seconds: ', ' {:.2%}'.format(mclp_res["comp_time"])
    # print mclp_res["demand_coverage"]
    print 'Coverage proportion: ', mclp_res["demand_coverage"]
    # arcpy.FeatureClassToFeatureClass_conversion(mclp_res["feature_output_lines"], outpath, 'result_mclp')
    
    #######################################
    ## test LSCP
    print 'Solve LSCP'
    lscp_func = partial(lscp_solver, env_path = workspace_path, demand_point = york_crime_sample_point, facility_service_area = york_facility_sample_service_area, id_demand_point = "id", id_facility="object_id", attr_demand="demand")
    # lscp_res = lscp_solver(workspace_path, links_ND2, york_facility_sample_point, york_crime_sample_point, service_dist)
    lscp_res = lscp_func()
# 
    # timing
    # timing_lscp = %timeit -n1 -o lscp_func()
    timing_lscp = timeit.repeat(lscp_func, repeat=3, number=1)
    print "Seconds of LSCP: ", sum(timing_lscp)/float(len(timing_lscp))

    ## LSCP results
    print 'Coverage proportion: ', ' {:.2%}'.format(lscp_res["demand_coverage"])
    print 'Number of facilities needed: ', lscp_res["n_facility"]
    ## write to file
    # arcpy.FeatureClassToFeatureClass_conversion(lscp_res["feature_output_lines"],outpath,'result_lscp')

    # res_timing = %timeit -n1 -o mclp_solver(env_path, road_network, demand_point, potential_facility_site, service_distance, p_fac)
    # print 'Computation time in seconds: ', ' {:.2%}'.format(lscp_res["Comp_time"])
    # print 'Coverage proportion: ', ' {:.2%}'.format(lscp_res["Coverage_prop"])
    # print 'Number of facilities needed: ', lscp_res["num_facility"]
    # arcpy.FeatureClassToFeatureClass_conversion(lscp_res["feature_output_lines"],outpath,'result_lscp')

    #######################################
    ## test batch MCLP. Write to a csv file

    # only one item in the list
    print 'Solve batch MCLP'
    batch_mclp_res = mclp_batch_solver(workspace_path, york_crime_sample_point, york_facility_sample_service_area, id_demand_point = "id", id_facility="object_id", attr_demand="demand", list_num_facility=range(1,2))
    batch_mclp_res.to_csv("MCLP_" + case + "_" + time.strftime("%Y%m%d-%H%M%S") + ".csv")

    # [1,2,3]
    # batch_mclp_res = mclp_batch_solver(workspace_path, links_ND2, york_facility_sample_point, york_crime_sample_point, service_dist, range(1,4))
    # batch_mclp_res.to_csv("MCLP_" + time.strftime("%Y%m%d-%H%M%S") + ".csv")
