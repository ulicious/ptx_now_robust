import numpy as np
import pandas as pd
import os
import shutil


def connect_profiles(country, length_cluster):

    location = None
    if country == 'Saudi Arabia':
        location = 'c3650x2850'
    elif country == 'Australia':
        location = 'c12775x-3075'
    elif country == 'Kazakhstan':
        location = 'c5000x4850'
    elif country == 'Germany':
        location = 'c875x5375'
    elif country == 'Chile':
        location = 'c-7100x-5300'

    path_raw_data = r'/run/user/1000/gvfs/smb-share:server=iipsrv-file3.iip.kit.edu,share=ssbackup/weatherOut/weatherOut_Uwe/' + country + '/Full_Profiles/2030/'
    path_clustered_data = r'/run/user/1000/gvfs/smb-share:server=iipsrv-file3.iip.kit.edu,share=ssbackup/weatherOut/weatherOut_Uwe/' + country + '/Clustered_Profiles/2030/' + str(length_cluster) + '/'
    path_processed_data = r'/run/user/1000/gvfs/smb-share:server=iipsrv-file1.iip.kit.edu,share=synergie/Group_TE/GM_Uwe/PtL_Robust/data/' + country + '/' + str(length_cluster)

    for f in os.listdir(path_clustered_data):
        if location in f:
            shutil.copyfile(path_clustered_data + f, path_processed_data + '/representative_data.xlsx')

    all_profile_file = pd.DataFrame()

    representative_data = pd.DataFrame(index=range(length_cluster))
    profile_data = None
    columns = []

    ind = 0
    column_number = 0
    for year in [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]:

        f = country + '_y' + str(year) + '_' + location + '_t2030.csv'

        current_file = pd.read_csv(path_raw_data + f, index_col=0)

        if len(current_file.index) > 8760:
            current_file = current_file.iloc[0:8760]

        current_file.index = range(8760)
        current_file.to_excel(path_processed_data + '/yearly_profiles/' + str(year) + '.xlsx')

        for cluster_index in range(0, 8760, length_cluster):
            if cluster_index == 0:
                continue

            for column in current_file.columns:

                if profile_data is None:
                    profile_data = np.array(current_file.loc[cluster_index - length_cluster: cluster_index - 1, column].values)
                else:
                    profile_data = np.c_[profile_data, current_file.loc[cluster_index - length_cluster: cluster_index - 1, column].values]

                columns.append(column + '_' + str(column_number))

            column_number += 1

        new_columns = [c + '_' + str(ind) for c in current_file.columns]
        current_file.columns = new_columns

        # all_profile_file = pd.concat([all_profile_file, current_file], axis=1)

        ind += 1

    representative_data.loc[:, columns] = profile_data

    # all_profile_file.to_csv('P:/Group_TE/GM_Uwe/PtL Robust/yearly_profiles.csv')
    # all_profile_file.to_excel('P:/Group_TE/GM_Uwe/PtL Robust/yearly_profiles.xlsx')

    representative_data.to_excel(path_processed_data + '/all_profiles_with_cluster_length.xlsx')
