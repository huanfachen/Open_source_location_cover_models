# batch_maxcovr_dist_mat.R

# Use max_covrage function to solve the MCLP with different facilitiy number. Write the result to a RDS file and a csv file.

maxcovr_batch_dist_mat <- function(file_demand, file_facility_site, file_dist_mat, vec_n_facility, dist_service, name_case){
    # Solving a list of MCLPs with different facility numbers on a case study. Using the maxcovr package. Write the maxcovr objects to a file.

    # Args:
    #   file_demand: the csv file containing the data frame of demand
    #   file_facility_site: the csv file constaining the data frame of facility sites
    #   file_distance_mat: the csv file containing the data frame of distance matrix. The required columns include distance, name (i.e. potential facility ID), DestinationName (i.e. demand ID), demand
    #   vec_n_facility: a vector of facility numbers
    #   dist_service: the maximal service distance (in metres)
    #   name_case: the name of the case
    #
    # Outputs:
    #   a .Rdata file: containing the maxcovr objects
    #   a .csv file: containing the testing result
    # Returns:
    #   None
    
    require(dplyr)
    require(purrr)
    require(data.table)
  
    # install the maxcovr if necessary
    if(!require(maxcovr)){
      devtools::install_github('huanfachen/maxcovr', force = TRUE)  
      require(maxcovr)
    }
  
    # df_demand <- file_demand %>% data.table::fread()
    # df_site <- file_facility_site %>% data.table::fread()
    
    # read distance matrix file. Convert to a matrix in R. Remember to set the class
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
    
    # run multiple MCLPs
    list_mclp_res <- purrr::map(vec_n_facility,
                             ~ solve_mclp_record_time(existing_facility = df_facility_fake, 
                                                      proposed_facility = df_site, 
                                                      user = df_demand,
                                                      distance_cutoff = dist_service,
                                                      d_proposed_user = dist_mat,
                                                      n_added = .x)
                             )
    names(list_mclp_res) <- vec_n_facility
    # save results: a .rdata file, a csv file
    # filename: MCLP_case_YYMMDD_HHMM.rds/csv
    
    time_stamp <- format(Sys.time(), "%Y%m%d_%H%M")
    file_prefix = paste0("MCLP","_", name_case, "_", time_stamp)
    file_rds = paste0(file_prefix, ".rds")
    file_csv = paste0(file_prefix, ".csv")
    save(list_mclp_res, file = file_rds)
    
    df_res <- purrr::map_dfr(list_mclp_res, magrittr::extract, c("n_facility", "demand_coverage", "comp_sec"))
    df_res %>% 
        as.data.frame() %>%
        write.csv(file_csv)
    
    print(paste0("Saving results to RDS file: ", file_rds))
    print(paste0("Saving results to CSV file: ", file_csv))
          
}

solve_mclp_record_time <- function(...){
    time_comp <- system.time(
        mclp_sol <- maxcovr::max_coverage_weighted(...)
    )
    # record the system computation time, in seconds
    
    mclp_sol$comp_sec <- time_comp[2]
    mclp_sol$demand_coverage <- percent_weight_coverage(mclp_sol)
    mclp_sol$n_facility <- mclp_sol$model_coverage[[1]]$n_added
    mclp_sol
}

# compute the percent of demand weight covered
# Compute the percent of covered weights
percent_weight_coverage <- function(mc_result){
  mc_result$user_affected[[1]]$weight %>% sum() / (mc_result$augmented_users[[1]]$weight %>% sum()) * 100.0
}
