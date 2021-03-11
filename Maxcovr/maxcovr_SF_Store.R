# maxcovr_SF_Store.R
# using distance matrix

source("batch_maxcovr_dist_mat.R")
df_res <- maxcovr_batch_dist_mat(file_demand = "../Data/San_Francisco_store/SF_demand_205_centroid_uniform_weight.csv", 
                        file_facility_site = "../Data/San_Francisco_store/SF_store_site_16_longlat.csv", 
                        file_dist_mat = "../Data/San_Francisco_store/SF_network_distance_candidateStore_16_censusTract_205_new.csv",
                        seq(1,12), 
                        dist_service = 5000, 
                        name_case = "SF_Store")

source("LSCP.R")
LSCP(file_demand = "../Data/San_Francisco_store/SF_demand_205_centroid_uniform_weight.csv", 
     file_facility_site = "../Data/San_Francisco_store/SF_store_site_16_longlat.csv", 
     file_dist_mat = "../Data/San_Francisco_store/SF_network_distance_candidateStore_16_censusTract_205_new.csv",
     dist_service = 5000, 
     name_case = "SF_Store")


