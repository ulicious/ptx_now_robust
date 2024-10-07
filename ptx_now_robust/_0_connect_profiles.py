import numpy as np
import pandas as pd
import os

import parameters

from _helpers_clustering import cluster_data_head_script


def connect_profiles():

    # this method uses all yearly profiles of a location to create representative data with target length of the clusters

    path_data = parameters.working_directory + c + '/applied_data/' + str(cl)

    if not os.path.exists(path_data):
        os.makedirs(path_data)

    all_profile_data = pd.DataFrame(index=range(cl))
    profile_data = None
    columns = []

    ind = 0
    column_number = 0
    # read all the yearly profiles and create single dataframe containing all data in correct form
    # afterward, cluster all data to representative data
    for year in [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]:

        try:
            current_file = pd.read_csv(parameters.data_path + c + '/' + str(year) + '.csv', index_col=0)
        except:
            current_file = pd.read_excel(parameters.data_path + c + '/' + str(year) + '.xlsx', index_col=0)

        current_file.reset_index(inplace=True, drop=True)

        current_file = current_file.loc[range(8760)]

        if cl == 8760:

            for column in current_file.columns:

                if profile_data is None:
                    profile_data = np.array(current_file.loc[:, column].values)
                else:
                    profile_data = np.c_[profile_data, current_file.loc[:, column].values]

                columns.append(column + '_' + str(column_number))

            column_number += 1

            # choose any year as representative data
            current_file['Weighting'] = 1
            current_file.to_excel(path_data + '/representative_data.xlsx')

        else:

            for cluster_index in range(0, 8760, cl):
                if cluster_index == 0:
                    continue

                for column in current_file.columns:

                    if profile_data is None:
                        profile_data = np.array(current_file.loc[cluster_index - cl: cluster_index - 1, column].values)
                    else:
                        profile_data = np.c_[profile_data, current_file.loc[cluster_index - cl: cluster_index - 1, column].values]

                    columns.append(column + '_' + str(column_number))

                column_number += 1

        ind += 1

    # save all profiles file
    all_profile_data.loc[:, columns] = profile_data
    all_profile_data.to_excel(path_data + '/all_profiles_with_cluster_length.xlsx')

    if cl != 8760:
        # cluster data to representative data
        clustered_data = cluster_data_head_script(all_profile_data, cl)
        clustered_data.to_excel(path_data + '/representative_data.xlsx')

# iterate over all countries and cluster lengths to create representative profiles file and file containing all profiles
for c in parameters.countries:
    print(c)
    for cl in parameters.cluster_lengths:
        print(cl)
        connect_profiles()
