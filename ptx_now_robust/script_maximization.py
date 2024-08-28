import os

import yaml

import pandas as pd
from datetime import datetime

from object_framework import ParameterObject
from _load_projects import load_project

from primal_model_gurobi_maximization import OptimizationGurobiModel

import parameters

for country in parameters.countries:
    for cluster_length in parameters.cluster_lengths:

        print(country)
        print(cluster_length)

        path_data = parameters.basic_path + 'data/'
        path_data_country = path_data + country + '/'
        path_results = path_data_country + '/results_' + str(cluster_length) + '/'

        name_parameters = parameters.framework_name

        solver = 'gurobi'

        # create pm_object and fill with data
        pm_object_robust = ParameterObject('parameter', integer_steps=10, path_data=path_data_country + 'yearly_profiles/')

        robust_yaml_file = open(path_results + 'robust_' + name_parameters)
        robust_case_data = yaml.load(robust_yaml_file, Loader=yaml.FullLoader)

        pm_object_robust = load_project(pm_object_robust, robust_case_data)
        pm_object_robust.set_project_name('robust optimization')

        # create pm_object and fill with data
        pm_object_not_robust = ParameterObject('parameter', integer_steps=10, path_data=path_data_country + 'yearly_profiles/')

        not_robust_yaml_file = open(path_results + 'not_robust_' + name_parameters)
        not_robust_case_data = yaml.load(not_robust_yaml_file, Loader=yaml.FullLoader)

        pm_object_not_robust = load_project(pm_object_not_robust, not_robust_case_data)
        pm_object_not_robust.set_project_name('not robust optimization')

        # load data
        pm_object_robust.set_covered_period(8760)
        pm_object_robust.set_uses_representative_periods(False)
        pm_object_robust.set_single_or_multiple_profiles('multiple')

        if parameters.electricity_available:
            electricity_commodity = pm_object_robust.get_commodity('Electricity')
            electricity_commodity.set_purchasable(True)
            electricity_commodity.set_purchase_price(parameters.electricity_price)

        pm_object_not_robust.set_covered_period(8760)
        pm_object_not_robust.set_uses_representative_periods(False)
        pm_object_not_robust.set_single_or_multiple_profiles('multiple')

        if parameters.electricity_available:
            electricity_commodity = pm_object_not_robust.get_commodity('Electricity')
            electricity_commodity.set_purchasable(True)
            electricity_commodity.set_purchase_price(parameters.electricity_price)

        # optimize objects
        years = []
        robust_results = {'produced_quantity': [],
                          'objective_function_value': [],
                          'bought_electricity': [],
                          'win_loss_per_unit': []}
        not_robust_results = {'produced_quantity': [],
                              'objective_function_value': [],
                              'bought_electricity': [],
                              'win_loss_per_unit': []}

        for file in sorted(os.listdir(path_data_country + 'yearly_profiles/')):
            print(file.split('.')[0])
            years.append(file.split('.')[0])

            pm_object_robust.set_profile_data(file)
            robust_optimization = OptimizationGurobiModel(pm_object_robust, solver, 8760, parameters.cost_selling,
                                                          parameters.costs_missing, parameters.demand_type)
            robust_optimization.prepare()
            robust_optimization.optimize()

            produced_quantity = 0
            bought_electricity = 0
            for t in robust_optimization.time:
                produced_quantity += robust_optimization.mass_energy_demand['FT', t].X
                bought_electricity += robust_optimization.mass_energy_purchase_commodity['Electricity', t].X

            print('robust')
            print('produced quantity: ' + str(produced_quantity))
            print('bought electricity: ' + str(bought_electricity))
            print('objective function: ' + str(robust_optimization.objective_function_value))
            print('win / loss per unit: ' + str(robust_optimization.objective_function_value / produced_quantity))

            robust_results['produced_quantity'].append(produced_quantity)
            robust_results['objective_function_value'].append(robust_optimization.objective_function_value)
            robust_results['bought_electricity'].append(bought_electricity)
            robust_results['win_loss_per_unit'].append(robust_optimization.objective_function_value / produced_quantity)

            # pm_object_robust.set_objective_function_value(robust_optimization.objective_function_value)
            # gurobi_ofv = robust_optimization.objective_function_value
            # pm_object_robust.set_instance(robust_optimization.instance)
            # pm_object_robust.process_results(path_results, robust_optimization.model_type)

            print('')

            pm_object_not_robust.set_profile_data(file)
            not_robust_optimization = OptimizationGurobiModel(pm_object_not_robust, solver, 8760,
                                                              parameters.cost_selling, parameters.costs_missing,
                                                              parameters.demand_type)
            not_robust_optimization.prepare()
            not_robust_optimization.optimize()

            produced_quantity = 0
            bought_electricity = 0
            for t in not_robust_optimization.time:
                produced_quantity += not_robust_optimization.mass_energy_demand['FT', t].X
                bought_electricity += not_robust_optimization.mass_energy_purchase_commodity['Electricity', t].X

            print('deterministic')
            print('produced quantity: ' + str(produced_quantity))
            print('bought electricity: ' + str(bought_electricity))
            print('objective function: ' + str(not_robust_optimization.objective_function_value))
            print('win / loss per unit: ' + str(not_robust_optimization.objective_function_value / produced_quantity))

            not_robust_results['produced_quantity'].append(produced_quantity)
            not_robust_results['objective_function_value'].append(not_robust_optimization.objective_function_value)
            not_robust_results['bought_electricity'].append(bought_electricity)
            not_robust_results['win_loss_per_unit'].append(not_robust_optimization.objective_function_value / produced_quantity)

            # pm_object_not_robust.set_objective_function_value(not_robust_optimization.objective_function_value)
            # gurobi_ofv = not_robust_optimization.objective_function_value
            # pm_object_not_robust.set_instance(not_robust_optimization.instance)
            # pm_object_not_robust.process_results(path_results, not_robust_optimization.model_type)

            print('----')

        result_dataframe = pd.DataFrame(0, index=['robust_objective', 'robust_quantity', 'robust_electricity', 'robust_win_loss',
                                                  'not_robust_objective', 'not_robust_quantity', 'not_robust_electricity', 'not_robust_win_loss'],
                                        columns=years, dtype=float)
        for n, year in enumerate(years):
            result_dataframe.at['robust_objective', year] = robust_results['objective_function_value'][n]
            result_dataframe.at['robust_quantity', year] = robust_results['produced_quantity'][n]
            result_dataframe.at['robust_electricity', year] = robust_results['bought_electricity'][n]
            result_dataframe.at['robust_win_loss', year] = robust_results['win_loss_per_unit'][n]

            result_dataframe.at['not_robust_objective', year] = not_robust_results['objective_function_value'][n]
            result_dataframe.at['not_robust_quantity', year] = not_robust_results['produced_quantity'][n]
            result_dataframe.at['not_robust_electricity', year] = not_robust_results['bought_electricity'][n]
            result_dataframe.at['not_robust_win_loss', year] = not_robust_results['win_loss_per_unit'][n]

        result_dataframe.to_excel(path_results + 'applied_capacities_results.xlsx')
