import os
import time
import math

import pandas as pd

from copy import deepcopy
from pyomo.core import *

from optimization_pyomo_model import OptimizationPyomoModel
from optimization_gurobi_model import OptimizationGurobiModel
from optimization_highs_model import OptimizationHighsModel

from joblib import Parallel, delayed
from tqdm import tqdm
import multiprocessing

from os import walk
from datetime import datetime


def optimize_single_profile_not_multi_objective(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                                                solver, path_results):

    optimization_model_pyomo = OptimizationPyomoModel
    optimization_model_gurobi = OptimizationGurobiModel
    optimization_model_highs = OptimizationHighsModel

    if False:

        now = time.time()
        optimization_problem = optimization_model_pyomo(pm_object_copy_pyomo, solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        pyomo_time_optimization = time.time() - now
        now = time.time()

        pm_object_copy_pyomo.set_objective_function_value(optimization_problem.objective_function_value)
        pyomo_ofv = optimization_problem.objective_function_value
        pm_object_copy_pyomo.set_instance(optimization_problem.instance)
        pm_object_copy_pyomo.process_results(path_results, optimization_problem.model_type)

        pyomo_time_analysis = time.time() - now

    if True:

        now = time.time()
        optimization_problem = optimization_model_gurobi(pm_object_copy_gurobi, solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        gurobi_time_optimization = time.time() - now
        now = time.time()

        pm_object_copy_gurobi.set_objective_function_value(optimization_problem.objective_function_value)
        gurobi_ofv = optimization_problem.objective_function_value
        pm_object_copy_gurobi.set_instance(optimization_problem.instance)
        pm_object_copy_gurobi.process_results(path_results, optimization_problem.model_type)

        gurobi_time_analysis = time.time() - now

    if False:

        now = time.time()
        optimization_problem = optimization_model_highs(pm_object_copy_pyomo, solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        highs_time_optimization = time.time() - now
        now = time.time()

        pm_object_copy_pyomo.set_objective_function_value(optimization_problem.objective_function_value)
        highs_ofv = optimization_problem.objective_function_value
        pm_object_copy_pyomo.set_instance(optimization_problem.instance)
        pm_object_copy_pyomo.process_results(path_results, optimization_problem.model_type)
        highs_time_analysis = time.time() - now

        print('Comparison OFV: highs: ' + str(highs_ofv) + ' | Gurobi: ' + str(gurobi_ofv) + ' | Pyomo: ' + str(pyomo_ofv))
        print('Comparison Time Optimization: highs: ' + str(highs_time_optimization) + ' | Gurobi: ' + str(gurobi_time_optimization) + ' | Pyomo: ' + str(pyomo_time_optimization))
        print('Comparison Time Analysis: highs: ' + str(highs_time_analysis) + ' | Gurobi: ' + str(gurobi_time_analysis) + ' | Pyomo: ' + str(pyomo_time_analysis))


def optimize_single_profile_multi_objective(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                                            solver, path_results):
    # the multi objective optimization follows the epsilon constraint method. This means
    # that the payoff table is calculated, deriving the nadir and udir value
    # of the second objective function. Afterwards, the range between these two values is separated into
    # small segments and each segment is included in the multi objective optimization
    # For more details, see
    # Mavrotas (2009): Effective implementation of the ε-constraint method in
    # Multi-Objective Mathematical Programming problems
    # todo: check nadir udir correct

    def run_multi_objective_optimization_in_parallel(input_local):
        # input: 0: eps; 1: optimization_model; 2: pm_object
        multi_objective_optimization_problem = input_local[1](input_local[2], solver)
        multi_objective_optimization_problem.prepare(optimization_type='multiobjective', eps_value_ecologic=input_local[0])
        multi_objective_optimization_problem.optimize()

        capacity, utilization, installation_emissions, disposal_emissions, fixed_emissions, variable_emissions = \
            multi_objective_optimization_problem.get_multi_objective_results()

        return multi_objective_optimization_problem.economic_objective_function_value, \
            multi_objective_optimization_problem.ecologic_objective_function_value, capacity, utilization, \
            installation_emissions, disposal_emissions, fixed_emissions, variable_emissions

    num_cores = min(120, multiprocessing.cpu_count() - 1)
    number_intervalls = 3

    # first calculate economical nadir value
    if False:
        pyomo_time = time.time()

        economic_optimization_problem = OptimizationPyomoModel(pm_object_copy_pyomo, solver)
        economic_optimization_problem.prepare(optimization_type='economical')
        economic_optimization_problem.optimize()

        ecologic_optimization_problem = OptimizationPyomoModel(pm_object_copy_pyomo, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological')
        ecologic_optimization_problem.optimize()

        economic_minimum = economic_optimization_problem.objective_function_value
        ecologic_minimum = ecologic_optimization_problem.objective_function_value

        ecologic_optimization_problem = OptimizationPyomoModel(pm_object_copy_pyomo, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological', eps_value_economic=economic_minimum)
        ecologic_optimization_problem.optimize()

        ecologic_supremum = ecologic_optimization_problem.objective_function_value

        # create intervalls of the ecological value and repeat multi objective optimization
        objective_function_value_combinations = {}
        columns = []
        intervall_objective_function = (ecologic_supremum - ecologic_minimum) / number_intervalls

        for i in range(0, number_intervalls):

            # eps = ecologic_minimum + i * intervall_objective_function
            value_ecologic = eps
            values = []
            columns = ['Economic OFV', 'Ecologic OFV']

            if False:

                for v in optimization_problem.instance.component_objects(Var, active=True):

                    if str(v) == 'nominal_cap':

                        variable_dict = v.extract_values()
                        for key in [*variable_dict.keys()]:
                            values.append(variable_dict[key])

                            if key not in columns:
                                columns.append(key)

                    elif str(v) == 'slack_ecological':
                        variable_dict = v.extract_values()
                        dict_values = variable_dict.values()
                        value_ecologic -= variable_dict.values()[0]

            objective_function_value_combinations[i] = tuple([value_economic, value_ecologic] + values)

        result_df = pd.DataFrame(objective_function_value_combinations).transpose()
        result_df.columns = columns
        result_df.to_excel('C:/Users/mt5285/ptx_data/test_multiO_pyomo.xlsx')

        pyomo_time = time.time() - pyomo_time

    # first calculate economical nadir value # todo: here you get minima of economic and ecologic --> save somewhere
    economic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    economic_optimization_problem.prepare(optimization_type='economical')
    economic_optimization_problem.optimize()

    ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    ecologic_optimization_problem.prepare(optimization_type='ecological')
    ecologic_optimization_problem.optimize()

    # economic_minimum = economic_optimization_problem.objective_function_value
    economic_minimum = math.ceil(economic_optimization_problem.objective_function_value * 100) / 100
    ecologic_minimum = ecologic_optimization_problem.objective_function_value

    ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    ecologic_optimization_problem.prepare(optimization_type='ecological', eps_value_economic=economic_minimum)
    ecologic_optimization_problem.optimize()

    ecologic_supremum = ecologic_optimization_problem.objective_function_value

    # create intervalls of the ecological value and repeat multi objective optimization
    objective_function_value_combinations = {}
    intervall_objective_function = (ecologic_supremum - ecologic_minimum) / number_intervalls

    inputs = []
    for i in range(0, number_intervalls):
        eps = ecologic_minimum + i * intervall_objective_function
        inputs.append((eps, OptimizationGurobiModel, pm_object_copy_gurobi))

    inputs = tqdm(inputs)
    results = Parallel(n_jobs=2)(delayed(run_multi_objective_optimization_in_parallel)(i) for i in inputs)

    columns = ['Economic', 'Ecologic']
    for number, element in enumerate(results):
        value_economic = element[0]
        value_ecologic = element[1]
        values = [value_economic, value_ecologic]

        value_capacity = element[2]
        value_utilization = element[3]

        value_installation_emissions = element[4]
        value_disposal_emissions = element[5]
        value_fixed_emissions = element[6]
        value_variable_emissions = element[7]

        for k in list(value_capacity.keys()):
            values.append(value_capacity[k])

            if k + '_capacity' not in columns:
                columns.append(k + '_capacity')

        for k in list(value_utilization.keys()):
            values.append(value_utilization[k])

            if k + '_utilization' not in columns:
                columns.append(k + '_utilization')

        for k in list(value_installation_emissions.keys()):
            values.append(value_installation_emissions[k])

            if k + '_installation_emissions' not in columns:
                columns.append(k + '_installation_emissions')

        for k in list(value_disposal_emissions.keys()):
            values.append(value_disposal_emissions[k])

            if k + '_disposal_emissions' not in columns:
                columns.append(k + '_disposal_emissions')

        for k in list(value_fixed_emissions.keys()):
            values.append(value_fixed_emissions[k])

            if k + '_fixed_emissions' not in columns:
                columns.append(k + '_fixed_emissions')

        for k in list(value_variable_emissions.keys()):
            values.append(value_variable_emissions[k])

            if k + '_variable_emissions' not in columns:
                columns.append(k + '_variable_emissions')

        objective_function_value_combinations[number] = tuple(values)

    result_df = pd.DataFrame(objective_function_value_combinations).transpose()
    result_df.columns = columns
    result_df.to_excel(path_mo_result + f)

    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_df.to_excel(path_results + dt_string + '_'
                       + pm_object_copy_gurobi.get_project_name() + '_multi_objective.xlsx')


def optimize_multi_profiles_no_multi_optimization(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                                                  solver, path_results):

    def multi_processing_optimization(input_data):  # 0: pm_object, 1: path to file
        input_data[0].set_profile_data(path_data_before + '/' + input_data[1])

        optimization_problem = optimization_model_global(input_data[0], solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        input_data[0].set_objective_function_value(optimization_problem.objective_function_value)

        # todo: might get problems as folder names are not unique --> to many at same time
        # input_data[0].set_instance(optimization_problem.instance)
        # input_data[0].process_results(path_results, optimization_problem.model_type)

        return optimization_problem.objective_function_value

    num_cores = min(120, multiprocessing.cpu_count() - 1)

    optimization_model_global = OptimizationGurobiModel

    path_data_before = pm_object_copy_gurobi.get_profile_data()
    path_to_profiles = pm_object_copy_gurobi.get_path_data() + pm_object_copy_gurobi.get_profile_data()
    _, _, filenames = next(walk(path_to_profiles))

    new_input = []
    for f in filenames:
        new_input.append((deepcopy(pm_object_copy_gurobi), f))

    inputs = tqdm(new_input)
    results_gurobi = Parallel(n_jobs=num_cores)(delayed(multi_processing_optimization)(i) for i in inputs)

    pm_object_copy_gurobi.set_profile_data(path_data_before)

    result_df = pd.DataFrame(results_gurobi, index=filenames)

    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_df.to_excel(path_results + dt_string + '_' + pm_object_copy_gurobi.get_project_name() + '.xlsx')


def multi_profiles_multi_objective(pm_object_copy_gurobi, solver, path_results):
    def run_multi_objective_optimization_in_parallel(input_local):
        # input: 0: eps; 1: optimization_model; 2: pm_object
        multi_objective_optimization_problem = input_local[1](input_local[2], solver)
        multi_objective_optimization_problem.prepare(optimization_type='multiobjective', eps_value_ecologic=input_local[0])
        multi_objective_optimization_problem.optimize()

        capacity, utilization, installation_emissions, disposal_emissions, fixed_emissions, variable_emissions = \
            multi_objective_optimization_problem.get_multi_objective_results()

        return multi_objective_optimization_problem.economic_objective_function_value,\
            multi_objective_optimization_problem.ecologic_objective_function_value, capacity, utilization, \
            installation_emissions, disposal_emissions, fixed_emissions, variable_emissions

    num_cores = min(120, multiprocessing.cpu_count() - 1)
    number_intervals = 100

    path_data_before = pm_object_copy_gurobi.get_profile_data()
    path_to_profiles = pm_object_copy_gurobi.get_path_data() + pm_object_copy_gurobi.get_profile_data()
    _, _, filenames = next(walk(path_to_profiles))

    # create new results folder for multi objective results
    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_mo_result = path_results + dt_string + '_' + pm_object_copy_gurobi.get_project_name() + '/'
    os.mkdir(path_mo_result)

    all_pareto_fronts = pd.DataFrame()

    for f in filenames:

        pm_object_copy_gurobi.set_profile_data(path_data_before + '/' + f)

        economic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
        economic_optimization_problem.prepare(optimization_type='economical')
        economic_optimization_problem.optimize()

        ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological')
        ecologic_optimization_problem.optimize()

        economic_minimum = math.ceil(economic_optimization_problem.economic_objective_function_value * 100) / 100
        # economic_minimum = economic_optimization_problem.economic_objective_function_value
        ecologic_minimum = ecologic_optimization_problem.ecologic_objective_function_value

        ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological', eps_value_economic=economic_minimum)
        ecologic_optimization_problem.optimize()

        ecologic_supremum = ecologic_optimization_problem.ecologic_objective_function_value

        # create intervalls of the ecological value and repeat multi objective optimization
        objective_function_value_combinations = {}
        interval_objective_function = (ecologic_supremum - ecologic_minimum) / number_intervals

        inputs = []
        for i in range(0, number_intervals):
            eps = ecologic_minimum + i * interval_objective_function
            inputs.append((eps, OptimizationGurobiModel, pm_object_copy_gurobi))

        inputs = tqdm(inputs)
        results = Parallel(n_jobs=num_cores)(
            delayed(run_multi_objective_optimization_in_parallel)(i) for i in inputs)

        columns = ['Economic', 'Ecologic']
        for number, element in enumerate(results):
            value_economic = element[0]
            value_ecologic = element[1]
            values = [value_economic, value_ecologic]

            value_capacity = element[2]
            value_utilization = element[3]

            value_installation_emissions = element[4]
            value_disposal_emissions = element[5]
            value_fixed_emissions = element[6]
            value_variable_emissions = element[7]

            for k in list(value_capacity.keys()):
                values.append(value_capacity[k])

                if k + '_capacity' not in columns:
                    columns.append(k + '_capacity')

            for k in list(value_utilization.keys()):
                values.append(value_utilization[k])

                if k + '_utilization' not in columns:
                    columns.append(k + '_utilization')

            for k in list(value_installation_emissions.keys()):
                values.append(value_installation_emissions[k])

                if k + '_installation_emissions' not in columns:
                    columns.append(k + '_installation_emissions')

            for k in list(value_disposal_emissions.keys()):
                values.append(value_disposal_emissions[k])

                if k + '_disposal_emissions' not in columns:
                    columns.append(k + '_disposal_emissions')

            for k in list(value_fixed_emissions.keys()):
                values.append(value_fixed_emissions[k])

                if k + '_fixed_emissions' not in columns:
                    columns.append(k + '_fixed_emissions')

            for k in list(value_variable_emissions.keys()):
                values.append(value_variable_emissions[k])

                if k + '_variable_emissions' not in columns:
                    columns.append(k + '_variable_emissions')

            objective_function_value_combinations[number] = tuple(values)

        result_df = pd.DataFrame(objective_function_value_combinations).transpose()
        result_df.columns = columns
        result_df.to_excel(path_mo_result + f)

        all_pareto_fronts[f + ' Economic'] = result_df['Economic']
        all_pareto_fronts[f + ' Ecologic'] = result_df['Ecologic']

    all_pareto_fronts.to_excel(path_mo_result + 'all_pareto_fronts.xlsx')

    pm_object_copy_gurobi.set_profile_data(path_data_before)


def optimize_no_profile(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                        solver, path_results):

    optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    optimization_problem.prepare(optimization_type=optimization_type)
    optimization_problem.optimize()

    # pm_object_copy_gurobi.set_objective_function_value(optimization_problem.objective_function_value)
    # pm_object_copy_gurobi.set_instance(optimization_problem.instance)
    # pm_object_copy_gurobi.process_results(path_results, optimization_problem.model_type)

    # optimization_problem = OptimizationHighsModel(pm_object_copy_gurobi, solver)
    # optimization_problem.prepare(optimization_type=optimization_type)
    # optimization_problem.optimize()

    pm_object_copy_gurobi.set_objective_function_value(optimization_problem.objective_function_value)
    pm_object_copy_gurobi.set_instance(optimization_problem.instance)
    pm_object_copy_gurobi.process_results(path_results, optimization_problem.model_type)
