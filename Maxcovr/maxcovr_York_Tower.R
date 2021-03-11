# maxcovr_York_Tower.R

# using the distance matrix for this case
# the code is very fast on the desktop with 16GB memory
source("batch_maxcovr_dist_mat.R")

df_res <- maxcovr_batch_dist_mat(file_demand = "../Data/York_Tower/york_crime_subset_591_longlat.csv", 
                        file_facility_site = "../Data/York_Tower/york_facility_subset_1821_longlat.csv", 
                        file_dist_mat = "../Data/York_Tower/york_haversine_distance_crime_591_facility_1921_col_renamed.csv",
                        seq(1,22), 
                        dist_service = 200, 
                        name_case = "York_Tower_subset")

source("LSCP.R")
LSCP(file_demand = "../Data/York_Tower/york_crime_subset_591_longlat.csv", 
     file_facility_site = "../Data/York_Tower/york_facility_subset_1821_longlat.csv", 
     file_dist_mat = "../Data/York_Tower/york_haversine_distance_crime_591_facility_1921_col_renamed.csv",
     dist_service = 200, 
     name_case = "York_Tower_subset")

### Not run ### 
### Codes for exploring the results
# replace the file names if needed
con <- gzfile("MCLP_York_Tower_subset_20190613_1911.rds")
load(con)
close(con)

res_mclp_22 <- list_mclp_res[["22"]]
res_mclp_22$facility_selected

require(magrittr)

vec_objectID_SF_MCLP_22 <- list_mclp_res[["22"]]$facility_selected[[1]]$object_id %>% as.character()


vec_objectID_SF_MCLP_22_PSO <- c('3217', '3242', '3271', '3408', '3414', '3419', '3444', '3632', '3664', '3670', '3775', '4010', '4042', '4100', '4165', '4184', '4245', '4353', '4354', '4433', '4474', '4571')
setequal(vec_objectID_SF_MCLP_22, vec_objectID_SF_MCLP_22_PSO)
setdiff(vec_objectID_SF_MCLP_22, vec_objectID_SF_MCLP_22_PSO)
setdiff(vec_objectID_SF_MCLP_22_PSO, vec_objectID_SF_MCLP_22)
intersect(vec_objectID_SF_MCLP_22,vec_objectID_SF_MCLP_22_PSO)

# 21 facilities

vec_objectID_SF_MCLP_21_PSO <- c('3217', '3242', '3260', '3291', '3301', '3348', '3351', '3419', '3428', '3437', '3632', '3670', '3853', '4010', '4110', '4184', '4245', '4332', '4354', '4560', '4571')
vec_objectID_SF_MCLP_21 <- list_mclp_res[["21"]]$facility_selected[[1]]$object_id %>% as.character()
setequal(vec_objectID_SF_MCLP_21, vec_objectID_SF_MCLP_21_PSO)
intersect(vec_objectID_SF_MCLP_21, vec_objectID_SF_MCLP_21_PSO)

# the demand point left out by PSO

# investigate the result of locating 20 facilities and save results as Shapefiles

require(magrittr)
require(dplyr)
con <- gzfile("MCLP_York_Tower_subset_20190613_1911.rds")
load(con)
close(con)
vec_objectID_York_MCLP_20 <- list_mclp_res[["20"]]$facility_selected[[1]]$object_id
obj_York_MCLP_20 <- list_mclp_res[["20"]]
vec_id_York_crime <- list_mclp_res[["20"]]$user_affected[[1]] %>% select(id) %>% pull()

require(rgdal)
spdf_facility_591 <- readOGR("../../York_Tower/york_crime_longlat_subset_591.shp")
spdf_facility_591@data <- spdf_facility_591@data %>% mutate(covered = case_when(id %in% vec_id_York_crime ~ 1, TRUE ~ 0))
spdf_facility_591 %>% writeOGR(dsn = "../../York_Tower", layer = "york_crime_longlat_subset_591_covered_MCLP_20", driver = "ESRI Shapefile")

spdf_facility_1821 <- readOGR("../../York_Tower/york_facility_subset_1821.shp") %>% spTransform(CRSobj = proj4string(spdf_facility_591))
proj4string(spdf_facility_1821)

spdf_facility_1821@data <- spdf_facility_1821@data %>% mutate(selected = case_when(object_id %in% vec_objectID_York_MCLP_20 ~ 1, TRUE ~ 0))
spdf_facility_1821 %>% writeOGR(dsn = "../../York_Tower", layer = "york_facility_1821_selected_MCLP_20", driver = "ESRI Shapefile")


BNG_CRS <- spdf_facility_591 <- readOGR("../../York_Tower/york_crime_longlat_subset_591.shp") %>% proj4string()
readOGR("../../York_Tower/york_facility_1821_selected_MCLP_20.shp") %>% spTransform(CRSobj = BNG_CRS) %>%
  writeOGR(dsn = "../../York_Tower", layer = "york_facility_1821_selected_MCLP_20", driver = "ESRI Shapefile", overwrite_layer = TRUE)

readOGR("../../York_Tower/york_crime_longlat_subset_591_covered_MCLP_20.shp") %>% spTransform(CRSobj = BNG_CRS) %>%
  writeOGR(dsn = "../../York_Tower", layer = "york_crime_longlat_subset_591_covered_MCLP_20", driver = "ESRI Shapefile", overwrite_layer = TRUE)
