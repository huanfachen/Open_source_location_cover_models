# -*- coding: UTF-8 -*-
import arcpy
import pandas as pd
from arcpy import env
from functools import partial
import timeit
arcpy.CheckOutExtension("Network")

def load_package():
    """
    Load important packages and modules
    """
    import arcpy
    import pandas as pd
    from arcpy import env
    from functools import partial
    import timeit
    arcpy.CheckOutExtension("Network")

def mclp_solver(env_path, road_network, demand_point, potential_facility_site, service_distance, num_facility, demand_weight_attr):
    """
    Solve a MCLP using the given inputs and parameters. This function will overwrite the FeatureClass called mclp_analysis_layer
    :param env_path: (string) Path of the env
    :param road_network: (string) File name of the network layer
    :param demand_point: (string) File name of the demand point layer
    :param potential_facility_site: (string) File name of the facility sites
    :param service_distance: (float or int) Service distance in meters
    :param num_facility: (int) Number of facilities to site
    :param demand_weight_attr: (string) Attribute name of demand weights
    :return: (A dict of objects) [demand_coverage, feature_output_lines, n_facility]

    """

    env.workspace = env_path
    env.overwriteOutput = True
        
    layer_name = "mclp_analysis_layer"
    if arcpy.Exists(layer_name):
        arcpy.Delete_management(layer_name)

    result_object = arcpy.na.MakeLocationAllocationLayer(road_network,layer_name,
                                     "Meters",
                                     "FACILITY_TO_DEMAND",
                                     "MAXIMIZE_COVERAGE",
                                     num_facility,
                                     service_distance, "LINEAR", hierarchy = False)
    # arcpy.AddLocations_na(layer_name,"Facilities",potential_facility_site)
    # arcpy.AddLocations_na(layer_name,"Demand Points",demand_point)                                 
    # arcpy.Solve_na(layer_name)
    # Get the layer object from the result object
    layer_object = result_object.getOutput(0)

    # Get the names of all the sublayers
    sublayer_names = arcpy.na.GetNAClassNames(layer_object)
    # print sublayer_names

    # Store the layer names that will be used later
    facilities_layer_name = sublayer_names["Facilities"]
    demand_points_layer_name = sublayer_names["DemandPoints"]
    # print demand_points_layer_name

    # Add candidate store
    arcpy.na.AddLocations(layer_object, facilities_layer_name, potential_facility_site, "", "", exclude_restricted_elements="EXCLUDE")

    # Add demand points
    demand_field_mappings = arcpy.na.NAClassFieldMappings(layer_object,
                                                    demand_points_layer_name)

    # Specify demand weight attribute                                                    
    demand_field_mappings["Weight"].mappedFieldName = demand_weight_attr
    arcpy.na.AddLocations(layer_object, demand_points_layer_name, demand_point,
                          demand_field_mappings, "",
                          exclude_restricted_elements="EXCLUDE")

    # query the total demand
    demand_sublayer = arcpy.mapping.ListLayers(layer_object, demand_points_layer_name)[0]
    demand_total = 0
    cursor_dem = arcpy.SearchCursor(demand_sublayer)
    for dem in cursor_dem:
        demand_total += dem.getValue("Weight")
    # print "Demand total: "
    # print demand_total

    # arcpy.AddLocations_na(layer_name,"Facilities",potential_facility_site)
    # arcpy.AddLocations_na(layer_name,"Demand Points",demand_point)
    arcpy.Solve_na(layer_object)
    
    # New layers? No
    # sublayer_names = arcpy.na.GetNAClassNames(layer_object)
    # print sublayer_names

    # analyse the results
    # how many feature layers in layer_name?
    # datasetList = arcpy.ListDatasets("*", "Feature")  
    # for dataset in datasetList:  
    #     print dataset  
    #     fcList = arcpy.ListFeatureClasses("*","",dataset)  
    #     fcList.sort()  
    #     for fc in fcList:  
    #         print fc  
    # attributes of the Facilities layer?

    result = {}

    # query the demand covered
    facility_sublayer = arcpy.mapping.ListLayers(layer_object, sublayer_names["Facilities"])[0]
    demand_covered = 0
    list_facility = []
    cursor_fac = arcpy.SearchCursor(facility_sublayer)
    for fac in cursor_fac:
        if fac.getValue("FacilityType") == 3:
            demand_covered += fac.getValue("DemandWeight")
            list_facility.append(fac.getValue("ObjectID"))
    # print "Demand covered: "
    # print demand_covered

    # query the demand points
    demand_LALine_sublayer = arcpy.mapping.ListLayers(layer_object, sublayer_names[u'LALines'])[0]
    list_id_demand_covered = []

    # get attributes
    desc = arcpy.Describe(demand_LALine_sublayer)
    for field in desc.fields:
        print field.name

    cursor_LALine = arcpy.SearchCursor(demand_LALine_sublayer)
    for LALine in cursor_LALine:
        list_id_demand_covered.append(LALine.getValue("DemandID"))
        # FacilityOID
    print "List of demand covered", list_id_demand_covered


    # write results
    result["list_id_facility"] = " ".join(str(x) for x in list_facility)
    result["feature_output_lines"] = arcpy.mapping.ListLayers(layer_object, sublayer_names["LALines"])[0]
    # n_demand_covered = arcpy.GetCount_management(result["feature_output_lines"])
    # n_demand_total = arcpy.GetCount_management(demand_point)
    
    # result["demand_coverage"] = float(n_demand_covered.getOutput(0)) / float(n_demand_total.getOutput(0))
    result["demand_coverage"] = float(demand_covered) / float(demand_total)
    result["n_facility"] = num_facility
    return result
    
def mclp_batch_solver(env_path, road_network, demand_point, potential_facility_site, service_distance, list_num_facility, demand_weight_attr):
    """
    Solve multiple MCLPs using the given inputs and a list of number of facilities. This function will call the function of mclp_solver
    :param env_path: (string) Path of the env
    :param road_network: (string) File name of the network layer
    :param demand_point: (string) File name of the demand point layer
    :param potential_facility_site: (string) File name of the facility sites
    :param service_distance: (float or int) Service distance in meters
    :param list_num_facility: (list of int) A list of number of facilities to site
    :param demand_weight_attr: (string) Attribute name of demand weights
    :return: (A Pandas dataframe) A dataframe with the column names of [n_facility, comp_sec, demand_coverage]
    """
    # to calculate the time: timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
    # print env_path
    
    list_timing = []
    list_cover_prop = []
    list_id_facility = []
    for p_fac in list_num_facility:
        # repeat for three times
        newFunc = partial(mclp_solver, env_path=env_path, road_network=road_network, demand_point=demand_point,potential_facility_site=potential_facility_site, service_distance=service_distance, num_facility=p_fac, demand_weight_attr = demand_weight_attr)
        res_timing = timeit.repeat(newFunc, repeat=1, number=1)
        res_mclp = newFunc()
        list_cover_prop.append(res_mclp["demand_coverage"])
        list_timing.append(sum(res_timing)/(float(len(res_timing))))
        list_id_facility.append(res_mclp["list_id_facility"])
    
    df_res = pd.DataFrame({'n_facility':list_num_facility, 'comp_sec':list_timing, "demand_coverage":list_cover_prop, "list_id_facility":list_id_facility})
    return df_res   
        

def lscp_solver(env_path, road_network, demand_point, potential_facility_site, service_distance, demand_weight_attr):
    """
    Solve a MCLP using the given inputs and parameters
    :param env_path: (string) Path of the env
    :param road_network: (string) File name of the network layer
    :param demand_point: (string) File name of the demand point layer
    :param potential_facility_site: (string) File name of the facility sites
    :param service_distance: (float or int) Service distance in meters
    :param demand_weight_attr: (string) Attribute name of demand weights
    :return: (A dict of objects) [demand_coverage, n_facility, feature_output_lines]
    """
    env.workspace = env_path
    env.overwriteOutput = True
        
    layer_name = "lscp_analysis_layer"
    if arcpy.Exists(layer_name):
        arcpy.Delete_management(layer_name)

    result_object = arcpy.na.MakeLocationAllocationLayer(in_network_dataset = road_network,
                                    out_network_analysis_layer = layer_name,
                                    impedance_attribute = "Meters",
                                    loc_alloc_from_to = "FACILITY_TO_DEMAND",
                                    loc_alloc_problem_type = "MINIMIZE_FACILITIES",
                                    number_facilities_to_find = "",
                                    impedance_cutoff = service_distance, 
                                    impedance_transformation = "LINEAR",
                                    hierarchy = False)
    # arcpy.AddLocations_na(layer_name,"Facilities",potential_facility_site)
    # arcpy.AddLocations_na(layer_name,"Demand Points",demand_point)                                 
    # arcpy.Solve_na(layer_name)
    # Get the layer object from the result object
    layer_object = result_object.getOutput(0)

    # Get the names of all the sublayers
    sublayer_names = arcpy.na.GetNAClassNames(layer_object)
    # print sublayer_names

    # Store the layer names that will be used later
    facilities_layer_name = sublayer_names["Facilities"]
    demand_points_layer_name = sublayer_names["DemandPoints"]
    # print demand_points_layer_name

    # Add candidate store
    search_tolerance = "5000 Meters"
    arcpy.na.AddLocations(in_network_analysis_layer = layer_object, sub_layer = facilities_layer_name, in_table = potential_facility_site, search_tolerance = search_tolerance, exclude_restricted_elements="EXCLUDE")

    # Add demand points
    demand_field_mappings = arcpy.na.NAClassFieldMappings(layer_object,
                                                    demand_points_layer_name)

    # Specify demand weight attribute                                                    
    demand_field_mappings["Weight"].mappedFieldName = demand_weight_attr
    arcpy.na.AddLocations(in_network_analysis_layer = layer_object, sub_layer = demand_points_layer_name, in_table = demand_point,
                          field_mappings = demand_field_mappings, search_tolerance = search_tolerance,
                          exclude_restricted_elements="EXCLUDE")

    # query the total demand
    demand_sublayer = arcpy.mapping.ListLayers(layer_object, demand_points_layer_name)[0]
    demand_total = 0
    cursor_dem = arcpy.SearchCursor(demand_sublayer)
    for dem in cursor_dem:
        demand_total += dem.getValue("Weight")
    arcpy.Solve_na(layer_object)
    print "Total demand: ", demand_total
    
    # New layers? No
    # sublayer_names = arcpy.na.GetNAClassNames(layer_object)
    # print sublayer_names

    # analyse the results
    # how many feature layers in layer_name?
    # datasetList = arcpy.ListDatasets("*", "Feature")  
    # for dataset in datasetList:  
    #     print dataset  
    #     fcList = arcpy.ListFeatureClasses("*","",dataset)  
    #     fcList.sort()  
    #     for fc in fcList:  
    #         print fc  
    # attributes of the Facilities layer?

    result = {}

    # query the demand covered
    facility_sublayer = arcpy.mapping.ListLayers(layer_object, sublayer_names["Facilities"])[0]
    demand_covered = 0
    num_facility = 0
    list_facility = []
    cursor_fac = arcpy.SearchCursor(facility_sublayer)
    for fac in cursor_fac:
        demand_covered += fac.getValue("DemandWeight")
        if fac.getValue("FacilityType") == 3:
            num_facility += 1
            list_facility.append(fac.getValue("ObjectID"))
    print "Covered demand: ", demand_covered

    # How many LALines
    LALine_layer = arcpy.mapping.ListLayers(layer_object, sublayer_names["LALines"])[0]
    num_LALine = [row for row in arcpy.da.SearchCursor(LALine_layer, "*")]
    print "Number of LALines: ", len(num_LALine)

    # query the uncovered demand
    demand_sublayer = arcpy.mapping.ListLayers(layer_object, sublayer_names["DemandPoints"])[0]
    cursor_dem = arcpy.SearchCursor(demand_sublayer)
    dict_status = {0:"OK", 1: "Not located", 2:"Network element not located", 3:"Element not traversable", 4:"Invalid field values", 5:"Not reached"}
    for fac in cursor_dem:
        if fac.getValue("AllocatedWeight") is None:
            print "A demand point is not covered. ID: ", fac.getValue("ObjectID")
            print "Name: ", fac.getValue("Name")
            print "Status: ", dict_status[fac.getValue("Status")]
        
    
    # Another way to get number of facilities:
    # facility_chosen = [row for row in arcpy.da.SearchCursor(facility_sublayer, "*", "FacilityType = 3")]
    # print len(facility_chosen)

    # print "Demand covered: "
    # print demand_covered

    # write results
    result["list_id_facility"] = " ".join(str(x) for x in list_facility)
    result["feature_output_lines"] = arcpy.mapping.ListLayers(layer_object, sublayer_names["LALines"])[0]
    # n_demand_covered = arcpy.GetCount_management(result["feature_output_lines"])
    # n_demand_total = arcpy.GetCount_management(demand_point)
    
    # result["demand_coverage"] = float(n_demand_covered.getOutput(0)) / float(n_demand_total.getOutput(0))
    result["demand_coverage"] = float(demand_covered) / float(demand_total)

    result["n_facility"] = num_facility
    # result["n_facility"] = num_facility
    return result

if __name__ == "__main__":
    # paths for testing. May change if needed.
    # workspace_path = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample'
    # links_ND2 = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\links_ND2.nd'
    # york_facility_sample_point = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\york_facility_sample_point.shp'
    # york_crime_sample_point = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\york_crime_sample_point.shp'
    # outpath = r'D:\aaaaa\shapefile for practice\york\small_area_sample\small_area_sample\Outputs'

    workspace_path = r'C:\Users\Huanfa Chen\Dropbox\Share_With_Rui_Jiang\Rui\shp for sample area'
    links_ND2 = r'links_ND2.nd'
    york_facility_sample_point = r'york_facility_sample_point.shp'
    york_crime_sample_point = r'york_crime_sample_point.shp'
    outpath = r'Outputs'
    service_dist = 100
    p_facility = 5
    list_p_fac = range(1, 5)
    case = "York_Tower_sample"

    #######################################
    ## test MCLP
    print 'Solve MCLP'
    mclp_func = partial(mclp_solver, env_path = workspace_path, road_network = links_ND2, demand_point = york_facility_sample_point, potential_facility_site = york_crime_sample_point, service_distance = service_dist, num_facility = p_facility)
    mclp_res = lscp_func()
    timing_mclp = timeit.repeat(lscp_func, repeat=3, number=1)
    print "Seconds of MCLP: ", sum(timing_mclp)/float(len(timing_mclp))

    ## MCLP results
    print 'Computation time in seconds: ', ' {:.2%}'.format(mclp_res["comp_time"])
    print 'Coverage proportion: ', ' {:.2%}'.format(mclp_res["demand_coverage"])
    # arcpy.FeatureClassToFeatureClass_conversion(mclp_res["feature_output_lines"], outpath, 'result_mclp')
    
    #######################################
    ## test LSCP
    print 'Solve LSCP'
    lscp_func = partial(lscp_solver, env_path = workspace_path, road_network = links_ND2, demand_point = york_facility_sample_point, potential_facility_site = york_crime_sample_point, service_distance = service_dist)
    # lscp_res = lscp_solver(workspace_path, links_ND2, york_facility_sample_point, york_crime_sample_point, service_dist)
    lscp_res = lscp_func()

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
    batch_mclp_res = mclp_batch_solver(workspace_path, links_ND2, york_facility_sample_point, york_crime_sample_point, service_dist, range(1,2))
    batch_mclp_res.to_csv("MCLP_" + case + "_" + time.strftime("%Y%m%d-%H%M%S") + ".csv")

    # [1,2,3]
    # batch_mclp_res = mclp_batch_solver(workspace_path, links_ND2, york_facility_sample_point, york_crime_sample_point, service_dist, range(1,4))
    # batch_mclp_res.to_csv("MCLP_" + time.strftime("%Y%m%d-%H%M%S") + ".csv")
