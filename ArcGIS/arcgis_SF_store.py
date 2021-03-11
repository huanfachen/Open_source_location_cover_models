# -*- coding: UTF-8 -*-
from mclp_lscp_wrapper_arcgis_v2 import *

if __name__ == "__main__":
    load_package()
    workspace_path = r'../Data/San_Francisco_store/SanFrancisco.gdb'
    file_network = r'Transportation/Streets_ND'
    # file_facility_site = r'Analysis\Stores'
    file_facility_site = r'Analysis/CandidateStores'
    file_demand_point = r'Analysis/TractCentroids_205'
    # the weight attribute in the file_demand_point
    demand_weight_attr = "POP2000"

    outpath = r'San_Francisco_store/Output.gdb'
    service_dist = 5000.0
    p_facility = 4
    list_p_fac = range(1, 17)
    
    
    case = "SF_Store"

    print 'Solve MCLP'
    mclp_func = partial(mclp_solver, env_path = workspace_path, road_network = file_network, demand_point = file_demand_point, potential_facility_site = file_facility_site, service_distance = service_dist, num_facility = p_facility, demand_weight_attr = demand_weight_attr)
    # mclp_func = partial(mclp_solver, env_path = workspace_path, road_network = file_network, demand_point = file_demand_point, potential_facility_site = file_facility_site, service_distance = service_dist, num_facility = p_facility)
    mclp_res = mclp_func()
    # timing_mclp = timeit.repeat(mclp_func, repeat=3, number=1)
    # print "Seconds of MCLP: ", sum(timing_mclp)/float(len(timing_mclp))

    # print list of list_id_facility
    print "List of selected facilities", mclp_res["list_id_facility"]
    print 'Number of facilities: ', mclp_res["n_facility"]
    print 'Coverage proportion: ', mclp_res["demand_coverage"]
    print 'Coverage proportion: ', ' {:.2%}'.format(mclp_res["demand_coverage"])
    # arcpy.FeatureClassToFeatureClass_conversion(mclp_res["feature_output_lines"], outpath, 'result_mclp')

    # # # #######################################
    # # test LSCP
    # print 'Solve LSCP'
    # lscp_func = partial(lscp_solver, env_path = workspace_path, road_network = file_network, demand_point = file_demand_point, potential_facility_site = file_facility_site, service_distance = service_dist, demand_weight_attr = demand_weight_attr)
    # lscp_res = lscp_func()

    # # timing
    # timing_lscp = timeit.repeat(lscp_func, repeat=3, number=1)
    # print "Seconds of LSCP: ", sum(timing_lscp)/float(len(timing_lscp))

    ## LSCP results
    # print 'Coverage proportion: ', ' {:.2%}'.format(lscp_res["demand_coverage"])
    # print 'Number of facilities needed: ', lscp_res["n_facility"]
    # df_lscp_res = pd.DataFrame({'n_facility':lscp_res["n_facility"], 
    # 'comp_sec':sum(timing_lscp)/float(len(timing_lscp)), 
    # "demand_coverage":lscp_res["demand_coverage"],
    # "list_id_facility":lscp_res["list_id_facility"]
    # }, index = [0])
    # df_lscp_res.to_csv("LSCP_" + case + "_" + time.strftime("%Y%m%d_%H%M%S") + ".csv")

    # # write to file
    # # arcpy.FeatureClassToFeatureClass_conversion(lscp_res["feature_output_lines"],outpath,'result_lscp')

    # # #######################################
    # # ## test batch MCLP. Write to a csv file
    # # # only one item in the list
    # print 'Solve batch MCLP'
    # batch_mclp_res = mclp_batch_solver(env_path=workspace_path, road_network=file_network, potential_facility_site=file_facility_site, demand_point=file_demand_point, service_distance=service_dist, list_num_facility=list_p_fac, demand_weight_attr = demand_weight_attr)
    # file_name = "MCLP_" + case + "_" + time.strftime("%Y%m%d_%H%M%S") + ".csv"
    # print "Save to file:", file_name
    # batch_mclp_res.to_csv(file_name)

