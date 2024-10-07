import time

import pandas as pd

from ptx_now_robust.optimization_problems.primal_model_gurobi import GurobiPrimalProblem
from ptx_now_robust.optimization_problems.dual_model_gurobi import GurobiDualProblem

import ptx_now_robust.parameters as parameters


def run_decomposition(pm_object, solver, input_profiles, number_cluster, worst_case_cluster, weighting,
                      all_profiles, number_profiles, path_results, costs_missing_product,
                      input_profiles_clusters, input_profiles_iteration, weightings_cluster, weighting_iteration):

    # initialize
    tolerance = 0.01
    UB = float('inf')
    iteration = 0

    kwargs = {}

    capacities = {}
    total_costs_dict = {'UB': {},
                        'LB': {}}

    capacity_df = None

    _, total_demand = pm_object.get_demand_time_series()
    time_start = time.time()

    times = pd.DataFrame(columns=['first', 'second', 'total'])

    not_robust_capacities = {}

    first_iteration = True
    while True:
        time_first = time.time()

        # setup and optimize super problem
        sup_problem = GurobiPrimalProblem(pm_object, solver, input_profiles, number_cluster, weighting,
                                          iteration, costs_missing_product, parameters.demand_type)
        sup_problem.prepare()
        sup_problem.optimize()
        objective_function_value = sup_problem.objective_function_value
        capacities_new = sup_problem.get_results()

        print(capacities_new)
        print(objective_function_value)

        times.at[iteration, 'first'] = (time.time() - time_first) / 60
        time_second = time.time()

        if first_iteration:
            # first super problem minimization gives deterministic capacities
            not_robust_capacities = capacities_new
            first_iteration = False

        capacities[iteration] = capacities_new

        LB = objective_function_value

        total_costs_LB = LB / total_demand[parameters.energy_carrier]
        print('Production costs first stage: ' + str(total_costs_LB))

        # setup and optimize sub problem
        sub_problem = GurobiDualProblem(pm_object, solver, capacities_new, input_profiles[iteration], all_profiles,
                                        worst_case_cluster, weighting, number_profiles, costs_missing_product,
                                        parameters.demand_type, **kwargs)
        sub_problem.optimize()

        times.at[iteration, 'second'] = (time.time() - time_second) / 60
        times.at[iteration, 'total'] = (time.time() - time_first) / 60

        times.at[iteration, 'primal_cont_vars'] = sup_problem.num_cont_vars
        times.at[iteration, 'dual_cont_vars'] = sub_problem.num_cont_vars
        times.at[iteration, 'dual_bin_vars'] = sub_problem.num_bin_vars

        UB = min(UB, sup_problem.objective_function_value - sup_problem.auxiliary_variable_value + sub_problem.objective_function_value)
        print('Time Iteration [m]: ' + str((time.time() - time_first) / 60))

        total_costs_UB = UB / total_demand[parameters.energy_carrier]
        total_costs_dict['UB'][iteration] = total_costs_UB

        total_costs_LB = LB / total_demand[parameters.energy_carrier]
        total_costs_dict['LB'][iteration] = total_costs_LB

        print('Iteration number: ' + str(iteration))

        print(sup_problem.auxiliary_variable_value)
        print(sub_problem.objective_function_value)

        print('Specific costs UB: ' + str(total_costs_UB))
        print('Specific costs LB: ' + str(total_costs_LB))

        # difference = (UB - LB) / LB
        difference = UB - LB
        print('Difference is: ' + str(difference))

        # if difference <= tolerance --> exit
        if difference <= tolerance:

            # get capacity results
            first = True
            for k in [*capacities.keys()]:
                if first:
                    capacity_df = pd.DataFrame.from_dict(capacities[k], orient='index')
                    first = False
                else:
                    capacity_df[k] = pd.DataFrame.from_dict(capacities[k], orient='index')

            capacity_df.to_excel(path_results + 'capacity.xlsx')

            # get chosen worst case profiles
            profiles_df = pd.DataFrame()
            for i in [*input_profiles.keys()]:
                for g in [*input_profiles[i].keys()]:
                    for c in [*input_profiles[i][g].keys()]:
                        profiles_df[str(i) + '_' + g + '_' + str(c)] = input_profiles[i][g][c]

            profiles_df.to_excel(path_results + 'profiles.xlsx')

            # get total costs results
            first = True
            total_costs_df = pd.DataFrame()
            for k in [*total_costs_dict.keys()]:
                if first:
                    total_costs_df = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
                    first = False
                else:
                    total_costs_df[k] = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
            total_costs_df.to_excel(path_results + 'total_costs.xlsx')

            # get calculation times
            times.at['final', 'total'] = (time.time() - time_start) / 60
            times.to_excel(path_results + 'times.xlsx')

            print('optimization successful')
            print('time needed: ' + str((time.time() - time_start) / 60) + ' minutes')

            break

        else:
            # difference > tolerance --> add worst case profile, go into next iteration and restart loop

            iteration += 1
            input_profiles[iteration] = {}

            input_profiles[iteration]['Wind'] = input_profiles[0]['Wind'].copy()
            input_profiles[iteration]['Solar'] = input_profiles[0]['Solar'].copy()

            input_profiles[iteration]['Wind'][worst_case_cluster] = sub_problem.chosen_profiles['Wind']
            input_profiles[iteration]['Solar'][worst_case_cluster] = sub_problem.chosen_profiles['Solar']

    return capacities_new, not_robust_capacities
