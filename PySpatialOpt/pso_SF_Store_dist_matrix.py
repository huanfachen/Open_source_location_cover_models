# -*- coding: UTF-8 -*-
# Run LSCP and MCLP models on a facility selection problem

import pso_mclp_lscp_wrapper
from pso_mclp_lscp_wrapper import *
import csv
import os

if __name__ == "__main__":

    bRunLSCP = True
    bRunMCLP = True
    load_package()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    pso_mclp_lscp_wrapper.set_logger(logger)
    pso_mclp_lscp_wrapper.test_logger()
    
    workspace_path = r'..\Data\San_Francisco_store'

    
    outpath = r'Outputs'
    
    service_dist = 5000.0 
    # in meters
    p_facility = 4
    list_p_fac = range(1, 13)
    case = "SF_Store"

    # distance matrix file
    SF_distance_demand_file = r'SF_network_distance_candidateStore_16_censusTract_205_new.csv'
    # field names in distance matrix file. This file should contain exactly 4 fields
    demand_id_field = "DestinationName"
    facility_id_field = "name"
    demand_weight_fiedl = "demand"
    distance_field = "distance"

    # Note: the facility file must contain an id field named facility_id_field and the format of this id should be string
    file_facility_service_area = r'ServiceAreas_4.shp'
    # The demand file must contain an id filed named demand_id_field and the format of this id should be string
    file_demand_point = r'SF_tract_centroid_205.shp'

    ## read distance matrix file as a dict
    with open(os.path.join(workspace_path, SF_distance_demand_file)) as csvfile:
        dict_pairwise_distance = [{k: v for k, v in row.items()}
        for row in csv.DictReader(csvfile, skipinitialspace=True)]
    print(dict_pairwise_distance[1])
    # {'distance': '1333.708062515136', 'name': 'Store_1', 'DestinationName': '060750479.02', 'demand': '3539'}

    # test generate_binary_coverage_from_dist_matrix
    # (f1, dict_facility_demand_distance, dl_id_field, fl_id_field, dist_threshold, demand_field="demand", distance_field="distance", fl_variable_name=None)
    dict_coverage = generate_binary_coverage_from_dist_matrix(fl = os.path.join(workspace_path,file_facility_service_area), list_dict_facility_demand_distance = dict_pairwise_distance, dl_id_field = demand_id_field, fl_id_field = facility_id_field, dist_threshold = service_dist)
    print dict_coverage["totalServiceableDemand"]

    # test: print coverage_dict["facilities"][facility_type]
    fl_variable_name = dict_coverage["facilities"].keys()[0]
    print dict_coverage["facilities"][fl_variable_name]

    #######################################
    # test MCLP
    # print 'Solve MCLP'
    # mclp_func = partial(mclp_solver_coverage_dict, dict_coverage = dict_coverage,env_path = workspace_path, demand_point = york_crime_point, facility_service_area = york_facility_service_area, num_facility = p_facility, id_demand_point = "id", id_facility="object_id", attr_demand="demand", id_facility_as_string=True)
    # mclp_res = mclp_func()
    # # timing_mclp = timeit.repeat(mclp_func, repeat=3, number=1)
    # # print "Seconds of MCLP: ", sum(timing_mclp)/float(len(timing_mclp))

    # print 'Coverage proportion: ', mclp_res["demand_coverage"]
    # arcpy.FeatureClassToFeatureClass_conversion(mclp_res["feature_output_lines"], outpath, 'result_mclp')
    
    #######################################
    # run LSCP
    if bRunLSCP is True:
        print 'Solve LSCP'
        lscp_func = partial(lscp_solver_coverage_dict, dict_coverage = dict_coverage, env_path = workspace_path, demand_point = file_demand_point, facility_service_area = file_facility_service_area, id_demand_point = "DestinationName", id_facility="name", attr_demand="demand",id_facility_as_string=True)
        # lscp_res = lscp_solver(workspace_path, links_ND2, york_facility_sample_point, york_crime_sample_point, service_dist)
        lscp_res = lscp_func()
    # 
        # timing
        timing_lscp = timeit.repeat(lscp_func, repeat=1, number=1)
        print "Seconds of LSCP: ", sum(timing_lscp)/float(len(timing_lscp))
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
    ## Run batch MCLP. Write to a csv file
    if bRunMCLP is True:
        print 'Solve batch MCLP'
        batch_mclp_res = mclp_batch_solver_coverage_dict(dict_coverage, workspace_path, file_demand_point, file_facility_service_area, id_demand_point = "DestinationName", id_facility="name", attr_demand="demand", list_num_facility=list_p_fac,id_facility_as_string=True)
        batch_mclp_res.to_csv("MCLP_" + case + "_" + time.strftime("%Y%m%d_%H%M%S") + ".csv")
