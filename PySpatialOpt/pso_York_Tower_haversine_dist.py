# -*- coding: UTF-8 -*-
import pso_mclp_lscp_wrapper
from pso_mclp_lscp_wrapper import *
import csv
import os

if __name__ == "__main__":
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
    
    workspace_path = r'../Data/York_Tower'
    york_facility_service_area = r'york_facility_subset_buffer_200.shp'
    york_crime_point = r'york_crime_subset_591.shp'
    york_distance_demand_file = r'york_haversine_distance_crime_591_facility_1921.csv'
    outpath = r'Outputs'
    service_dist = 200
    p_facility = 22
    # list_p_fac = range(1, 12)
    list_p_fac = range(1, 23)
    case = "York_Tower"

    # read dict
    with open(os.path.join(workspace_path, york_distance_demand_file)) as csvfile:
        dict_pairwise_distance = [{k: v for k, v in row.items()}
        for row in csv.DictReader(csvfile, skipinitialspace=True)]
    print(dict_pairwise_distance[1])
    # test generate_binary_coverage_from_dist_matrix
    # (f1, dict_facility_demand_distance, dl_id_field, fl_id_field, dist_threshold, demand_field="demand", distance_field="distance", fl_variable_name=None)
    dict_coverage = generate_binary_coverage_from_dist_matrix(fl = os.path.join(workspace_path,york_facility_service_area), list_dict_facility_demand_distance = dict_pairwise_distance, dl_id_field = "id", fl_id_field = "object_id", dist_threshold = service_dist)
    print dict_coverage["totalServiceableDemand"]
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
    # test LSCP
    print 'Solve LSCP'
    lscp_func = partial(lscp_solver_coverage_dict, dict_coverage = dict_coverage, env_path = workspace_path, demand_point = york_crime_point, facility_service_area = york_facility_service_area, id_demand_point = "id", id_facility="object_id", attr_demand="demand",id_facility_as_string=True)
    # lscp_res = lscp_solver(workspace_path, links_ND2, york_facility_sample_point, york_crime_sample_point, service_dist)
    lscp_res = lscp_func()
# 
    # timing
    # timing_lscp = %timeit -n1 -o lscp_func()
    timing_lscp = timeit.repeat(lscp_func, repeat=1, number=1)
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
    batch_mclp_res = mclp_batch_solver_coverage_dict(dict_coverage, workspace_path, york_crime_point, york_facility_service_area, id_demand_point = "id", id_facility="object_id", attr_demand="demand", list_num_facility=list_p_fac,id_facility_as_string=True)
    batch_mclp_res.to_csv("MCLP_" + case + "_" + time.strftime("%Y%m%d_%H%M%S") + ".csv")
