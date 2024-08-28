import yaml

import pandas as pd
from datetime import datetime

from object_framework import ParameterObject
from _load_projects import load_project

from primal_model_gurobi import GurobiPrimalProblem
from dual_model_gurobi import GurobiDualProblem
from dual_model import ExtremeCaseBilinear
# from dual_model_gurobi_adjusted import GurobiDualProblem
# from dual_model_gurobi_no_uncertainty import GurobiDualProblem

import parameters

country = parameters.country

path_data = '/run/user/1000/gvfs/smb-share:server=iipsrv-file1.iip.kit.edu,share=synergie/Group_TE/GM_Uwe/PtL_Robust/data/'
path_data_country = path_data + country + '/'
path_results = path_data_country + 'results/'

name_parameters = parameters.framework_name

solver = 'gurobi'

costs_missing_product = 3.5

use_minimal_example = True

# create pm_object and fill with data
pm_object = ParameterObject('parameter', integer_steps=10, path_data=path_data_country)

yaml_file = open(path_results + 'robust_' + name_parameters)
case_data = yaml.load(yaml_file, Loader=yaml.FullLoader)

pm_object = load_project(pm_object, case_data)
pm_object.set_project_name('robust optimization')

electricity_commodity = pm_object.get_commodity('Electricity')
electricity_commodity.set_purchasable(parameters.electricity_available)
electricity_commodity.set_purchase_price(parameters.electricity_price)

# load data
representative_profiles = pd.read_excel(path_data_country + 'representative_data.xlsx', index_col=0)

pm_object.set_profile_data('representative_data.xlsx')
pm_object.set_covered_period(parameters.cluster_length)

# for s in pm_object.get_storage_components_objects():
#     s.set_final(False)

period_length = pm_object.get_covered_period()
number_clusters = int(len(representative_profiles.index) / period_length)

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
all_profiles = pd.DataFrame(index=range(parameters.cluster_length))
all_profiles['Wind_0'] = input_profiles[0]['Wind'][0]
all_profiles['Solar_0'] = input_profiles[0]['Solar'][0]
# all_profiles = all_profiles[used_columns]

number_profiles = int(len(all_profiles.columns) / len(input_profiles[0].keys()))

iteration = 0

sup_problem = GurobiPrimalProblem(pm_object, solver, input_profiles, number_clusters, weighting,
                                  iteration, costs_missing_product, parameters.demand_type)
sup_problem.prepare()
sup_problem.optimize()
objective_function_value = sup_problem.objective_function_value
capacities_new = sup_problem.get_results()

capacities = {0: capacities_new}

sub_problem = GurobiDualProblem(pm_object, solver, capacities_new, input_profiles[0], all_profiles,
                                number_clusters, weighting, number_profiles, costs_missing_product,
                                parameters.demand_type)
sub_problem.optimize()

print('super: ' + str(sup_problem.auxiliary_variable_value))
print('sub: ' + str(sub_problem.objective_function_value))
