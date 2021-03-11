# LSCP.R
# An implementation of Location Set Covering Problem model using maxcovr
# Using some codes from batch_maxcovr.R

LSCP <- function(file_demand, file_facility_site, file_dist_mat, dist_service, name_case){
  # Solving the Location Set Covering Problem on a case study. Using the maxcovr package. Write the maxcovr objects to a file.
  
  # Args:
  #   file_demand: the csv file containing the data frame of demand
  #   file_facility_site: the csv file constaining the data frame of facility sites
  #   file_dist_mat: the csv file containing the data frame of distance matrix. The required columns include distance, name, DestinationName, demand
  #   dist_service: the maximal service distance (in metres)
  #   name_case: the name of the case
  #
  # Outputs:
  #   a .Rdata file: containing a maxcovr object corresponding to the fewest facilities that are able to cover all demands
  #   a .csv file: containing the testing result
  #
  # Returns:
  #   None
  source("batch_maxcovr_dist_mat.R")
  require(dplyr)
  require(maxcovr)
  require(purrr)
  require(data.table)
  # df_demand <- file_demand %>% data.table::fread()
  # df_site <- file_facility_site %>% data.table::fread()
  
  df_dist <- file_dist_mat %>% 
    data.table::fread(colClasses = c("name" = "character", "DestinationName" = "character"))
  
  dist_mat <- xtabs(df_dist$distance ~ df_dist$name + df_dist$DestinationName)
  
  # fake existing facility
  df_facility_fake <- data.frame(long = NA, lat = NA, weight = NA)
  
  # proposed facility
  df_site <- data.frame(long = NA, lat = NA, id = rownames(dist_mat))
  
  # coerce the same order of demand id in the columns of distance matrix and df_demand
  df_demand <- df_dist %>% 
    select(id = DestinationName, weight = demand) %>%
    distinct(id, .keep_all = TRUE) %>%
    arrange(factor(id, levels = colnames(dist_mat))) %>%
    mutate(long = NA, lat = NA)
  
  # assert: data frames must contain two columns: long, lat
  if(!all(c("long","lat") %in% names(df_demand))){
    stop("Error: Demand data must contain long and lat")
  }
  
  if(!all(c("long","lat") %in% names(df_site))){
    stop("Error: Facility site data must contain long and lat")
  }
  
  num_all_facility <- nrow(df_site)
  
  # test if it is possible to cover all demands using all facilities
  res_mclp_all_fac <- solve_mclp_record_time(existing_facility = df_facility_fake, 
                                             proposed_facility = df_site, 
                                             user = df_demand,
                                             distance_cutoff = dist_service, 
                                             d_proposed_user = dist_mat,
                                             n_added = num_all_facility)
  
  if(res_mclp_all_fac$demand_coverage < 1){
    stop("There is no feasible solution to this LSCP. Unable to cover all demands")
  }
  
  # use a loop to test different numbers of facility from 1 to maximum
  num_facility <- 1
  temp_res_mclp <- NULL
  
  while(num_facility <= num_all_facility){
    temp_res_mclp <- solve_mclp_record_time(existing_facility = df_facility_fake, 
                           proposed_facility = df_site, 
                           user = df_demand,
                           d_proposed_user = dist_mat,
                           distance_cutoff = dist_service, 
                           n_added = num_facility)
    
    if(temp_res_mclp$demand_coverage >= 100){
      break
    }else{
      num_facility <- num_facility + 1
    }
  }
  
  print("How many facilities needed to cover all demands?")
  print(num_facility)
  # write the result
  list_lscp_res <- list(temp_res_mclp)
  names(list_lscp_res) <- num_facility
  # save results: a .rdata file, a csv file
  # filename: MCLP_case_YYMMDD_HHMM.rds/csv
  
  time_stamp <- format(Sys.time(), "%Y%m%d_%H%M")
  file_prefix <- paste0("LSCP","_", name_case, "_", time_stamp)
  file_rds <- paste0(file_prefix, ".rds")
  file_csv <- paste0(file_prefix, ".csv")
  save(list_lscp_res, file = file_rds)
  
  df_res <- purrr::map_dfr(list_lscp_res, magrittr::extract, c("n_facility", "demand_coverage", "comp_sec"))
  df_res %>% 
    as.data.frame() %>%
    write.csv(file_csv)
  
  print(paste0("Saving results to RDS file: ", file_rds))
  print(paste0("Saving results to CSV file: ", file_csv))
}