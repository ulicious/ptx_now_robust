import yaml
import os

import pandas as pd

from ptx_now_robust.helpers.object_framework import ParameterObject
from ptx_now_robust.helpers.load_projects import load_project
from ptx_now_robust.helpers.script_decomposition import run_decomposition

import parameters

path_data = parameters.working_directory

name_parameters = parameters.framework_name

solver = 'gurobi'

costs_missing_product = parameters.costs_missing

# iterate over all countries and cluster lengths set in parameters file
for country in parameters.countries:
    for cluster_length in parameters.cluster_lengths:

        print(country)
        print(cluster_length)

        # set paths
        path_country = parameters.working_directory + country + '/'
        path_technology_data = parameters.data_path
        path_data = path_country + '/data/' + str(cluster_length) + '/'

        # create results folders if not already existing
        path_results = path_country + 'results/' + parameters.energy_carrier + '/' + str(cluster_length) + '/'
        if not os.path.exists(path_results):
            os.makedirs(path_results)

        # create parameter object and fill with data
        pm_object = ParameterObject('parameter', integer_steps=10, path_data=path_data)

        yaml_file = open(path_technology_data + name_parameters)
        case_data = yaml.load(yaml_file, Loader=yaml.FullLoader)

        pm_object = load_project(pm_object, case_data)
        pm_object.set_project_name('robust optimization')

        # set electricity availability and price based on parameter setting
        electricity_commodity = pm_object.get_commodity('Electricity')
        electricity_commodity.set_purchasable(parameters.electricity_available)
        electricity_commodity.set_purchase_price(parameters.electricity_price)

        # load data
        representative_profiles = pd.read_excel(path_data + 'representative_data.xlsx', index_col=0)

        # set correct data file and cluster length
        pm_object.set_profile_data('representative_data.xlsx')
        pm_object.set_covered_period(cluster_length)

        period_length = pm_object.get_covered_period()
        number_clusters = int(len(representative_profiles.index) / period_length)

        # setup dictionary with profiles
        input_profiles = {0: {}}
        input_profiles_clusters = {}
        for col in representative_profiles.columns:
            if col != 'Weighting':
                input_profiles[0][col] = {}
                input_profiles_clusters[col] = {}

        # fill dictionary
        for i in range(number_clusters):
            for col in representative_profiles.columns:
                if col != 'Weighting':

                    if pm_object.get_uses_representative_periods():
                        profile = representative_profiles.loc[i * period_length:(i + 1) * period_length, col]
                    else:
                        profile = representative_profiles[col]

                    profile.index = range(len(profile.index))
                    input_profiles[0][col][i] = profile
                    input_profiles_clusters[col][i] = profile

        # Set initial worst case cluster. It only exists if clusters exist at all
        if cluster_length != 8760:
            worst_case_cluster = number_clusters

            input_profiles[0]['Wind'][worst_case_cluster] = input_profiles[0]['Wind'][0]
            input_profiles[0]['Solar'][worst_case_cluster] = input_profiles[0]['Solar'][0]

            input_profiles_iteration = {'Wind': {0: input_profiles[0]['Wind'][0]},
                                        'Solar': {0: input_profiles[0]['Solar'][0]}}

            # adjust weightings accordingly to include additional worst case cluster
            weighting = {}
            for i in range(number_clusters):
                if number_clusters != 1:
                    weighting_reduction = representative_profiles.at[i * period_length, 'Weighting'] / (8760 / period_length)
                    weighting[i] = representative_profiles.at[i * period_length, 'Weighting'] - weighting_reduction
                else:
                    # worst case cluster has always weighting of 1
                    weighting[i] = 1

            weightings_cluster = weighting.copy()
            weighting_iteration = 1

            weighting[worst_case_cluster] = 1
        else:
            # if cluster length is 8760, then only one cluster exists
            weighting = {0: 1}
            worst_case_cluster = 0

            weightings_cluster = weighting.copy()
            weighting_iteration = 1

            input_profiles_iteration = {0: {'Wind': input_profiles[0]['Wind'][0],
                                            'Solar': input_profiles[0]['Solar'][0]}}

            input_profiles_clusters = None

        # load all other profiles --> robust optimization can choose from these profiles
        all_profiles = pd.read_excel(path_data + 'all_profiles_with_cluster_length.xlsx', index_col=0)

        number_profiles = int(len(all_profiles.columns) / len(input_profiles[0].keys()))

        # start adaptive robust optimization
        robust_capacities, not_robust_capacities = run_decomposition(pm_object, solver, input_profiles, number_clusters,
                                                                     worst_case_cluster, weighting, all_profiles,
                                                                     number_profiles, path_results,
                                                                     costs_missing_product,
                                                                     input_profiles_clusters, input_profiles_iteration,
                                                                     weightings_cluster, weighting_iteration)

        # save results
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
