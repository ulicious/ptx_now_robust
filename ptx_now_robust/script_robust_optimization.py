import yaml
import os

import pandas as pd
from datetime import datetime

from object_framework import ParameterObject
from _load_projects import load_project
from script_decomposition import run_decomposition
from connect_profiles import connect_profiles

import parameters

path_data = '/run/user/1000/gvfs/smb-share:server=iipsrv-file1.iip.kit.edu,share=synergie/Group_TE/GM_Uwe/PtL_Robust/data/'

name_parameters = parameters.framework_name

solver = 'gurobi'

costs_missing_product = parameters.costs_missing

for country in parameters.countries:
    for cluster_length in parameters.cluster_lengths:

        print(country)
        print(cluster_length)

        path_data_country = path_data + country + '/'

        path_results = path_data_country + 'results' + '_' + str(cluster_length) + '/'

        if not os.path.exists(path_results):
            os.makedirs(path_results)

        connect_profiles(country, cluster_length)

        # create pm_object and fill with data
        pm_object = ParameterObject('parameter', integer_steps=10, path_data=path_data_country)

        yaml_file = open(path_data + name_parameters)
        case_data = yaml.load(yaml_file, Loader=yaml.FullLoader)

        pm_object = load_project(pm_object, case_data)
        pm_object.set_project_name('robust optimization')

        electricity_commodity = pm_object.get_commodity('Electricity')
        electricity_commodity.set_purchasable(parameters.electricity_available)
        electricity_commodity.set_purchase_price(parameters.electricity_price)

        # load data
        representative_profiles = pd.read_excel(path_data_country + 'representative_data.xlsx', index_col=0)

        pm_object.set_profile_data('representative_data.xlsx')
        pm_object.set_covered_period(cluster_length)

        period_length = pm_object.get_covered_period()
        number_clusters = int(len(representative_profiles.index) / period_length)

        # for s in pm_object.get_storage_components_objects():
        #     s.set_final(False)

        # nominal implements the profiles used in the super problem
        input_profiles = {0: {}}
        for col in representative_profiles.columns:
            if col != 'Weighting':
                input_profiles[0][col] = {}

        for i in range(number_clusters):
            for col in representative_profiles.columns:
                if col != 'Weighting':

                    if pm_object.get_uses_representative_periods():
                        profile = representative_profiles.loc[i * period_length:(i + 1) * period_length, col]
                    else:
                        profile = representative_profiles[col]

                    profile.index = range(len(profile.index))
                    input_profiles[0][col][i] = profile

        # Set initial worst case cluster
        worst_case_cluster = number_clusters

        input_profiles[0]['Wind'][worst_case_cluster] = input_profiles[0]['Wind'][0]
        input_profiles[0]['Solar'][worst_case_cluster] = input_profiles[0]['Solar'][0]

        # adjust weightings accordingly to include additional worst case cluster
        weighting = {}
        for i in range(number_clusters):
            if number_clusters != 1:
                weighting_reduction = representative_profiles.at[i * period_length, 'Weighting'] / (8760 / period_length)
                weighting[i] = representative_profiles.at[i * period_length, 'Weighting'] - weighting_reduction
            else:
                weighting[i] = 1

        weighting[worst_case_cluster] = 1

        # load all other profiles
        all_profiles = pd.read_excel(path_data_country + 'all_profiles_with_cluster_length.xlsx', index_col=0)
        # used_columns = list(all_profiles.columns[:10]) + ['Wind_165', 'Solar_165', 'Wind_166', 'Solar_166', 'Wind_167', 'Solar_167']
        # all_profiles = all_profiles[used_columns]

        number_profiles = int(len(all_profiles.columns) / len(input_profiles[0].keys()))
        print(number_profiles)

        robust_capacities, not_robust_capacities = run_decomposition(pm_object, solver, input_profiles, worst_case_cluster,
                                                                     weighting, all_profiles, number_profiles, path_results,
                                                                     costs_missing_product)

        for c in [*robust_capacities.keys()]:
            case_data['component'][c]['fixed_capacity'] = robust_capacities[c]
            case_data['component'][c]['has_fixed_capacity'] = True

        file = open(path_results + 'robust_' + name_parameters, "w")
        yaml.dump(case_data, file)
        file.close()

        for c in [*not_robust_capacities.keys()]:
            case_data['component'][c]['fixed_capacity'] = not_robust_capacities[c]
            case_data['component'][c]['has_fixed_capacity'] = True

        file = open(path_results + 'not_robust_' + name_parameters, "w")
        yaml.dump(case_data, file)
        file.close()
