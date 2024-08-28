import time

import pandas as pd

from primal_model import SuperProblemRepresentative
from primal_model_gurobi import GurobiPrimalProblem
from dual_model import ExtremeCaseBilinear
# from dual_model_gurobi import GurobiDualProblem
from old_dual import GurobiDualProblem
from dual_model_gurobi_no_uncertainty import GurobiDualProblem as dual_no_uncertainty

import parameters


def run_decomposition(pm_object, solver, input_profiles, worst_case_cluster, weighting,
                      all_profiles, number_profiles, path_results, costs_missing_product):

    now = time.time()

    times = {}

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
    first = True
    while True:
        if False:
            time_old = time.time()

            print('old approach')
            sup_problem = SuperProblemRepresentative(pm_object, solver, input_profiles, worst_case_cluster, weighting, iteration)
            sup_problem.optimize()

            capacities_new = sup_problem.optimal_capacities
            capacities[iteration] = capacities_new

            print(sup_problem.obj_value)
            print(capacities_new)
            LB = sup_problem.obj_value

            total_costs_LB = LB / total_demand['FT']
            print('Production costs first stage: ' + str(total_costs_LB))

            # sub_problem = ExtremeCaseBilinear(pm_object, solver, capacities_new, input_profiles, all_profiles,
            #                                   worst_case_cluster,
            #                                   weighting, number_profiles, costs_missing_product, **kwargs)
            # sub_problem.optimize()
            # UB = min(UB, sup_problem.obj_value - sup_problem.auxiliary_variable + sub_problem.obj_value)
            # print(UB)

            print(time.time() - time_old)
            print('___________________________')

        if True:
            time_new = time.time()
            sup_problem = GurobiPrimalProblem(pm_object, solver, input_profiles, worst_case_cluster, weighting,
                                              iteration, costs_missing_product, parameters.demand_type)
            sup_problem.prepare()
            sup_problem.optimize()
            objective_function_value = sup_problem.objective_function_value
            capacities_new = sup_problem.get_results()

            if first:
                not_robust_capacities = capacities_new
                first = False

            # if len(input_profiles.keys()) > 1:
            #     for k in input_profiles.keys():
            #
            #         test_profiles = {0: input_profiles[k]}
            #         test_iteration = 0
            #
            #         test = GurobiPrimalProblem(pm_object, solver, test_profiles, worst_case_cluster, weighting,
            #                                    test_iteration, costs_missing_product, parameters.demand_type)
            #         test.prepare()
            #         test.optimize()
            #         print(test.auxiliary_variable_value)

            print(objective_function_value)
            print(capacities_new)

            capacities[iteration] = capacities_new

            total_electricity = 0
            for cl in range(worst_case_cluster+1):
                for t in range(pm_object.get_covered_period()):
                    total_electricity += sup_problem.mass_energy_purchase_commodity['Electricity', cl, t, iteration].X * weighting[cl]
            print(total_electricity * parameters.electricity_price)

            # test = dual_no_uncertainty(pm_object, solver, capacities[0], input_profiles[iteration], all_profiles,
            #                            worst_case_cluster, weighting, number_profiles, costs_missing_product,
            #                            parameters.demand_type)
            # test.optimize()
            #
            # print('sup: ' + str(sup_problem.auxiliary_variable_value))
            # print('sub: ' + str(test.objective_function_value))

            LB = objective_function_value

            total_costs_LB = LB / total_demand['FT']
            print('Production costs first stage: ' + str(total_costs_LB))

            sub_problem = GurobiDualProblem(pm_object, solver, capacities_new, input_profiles[iteration], all_profiles,
                                            worst_case_cluster, weighting, number_profiles, costs_missing_product,
                                            parameters.demand_type, **kwargs)
            sub_problem.optimize()

            UB = min(UB, sup_problem.objective_function_value - sup_problem.auxiliary_variable_value + sub_problem.objective_function_value)
            print('Time Iteration [m]: ' + str((time.time() - time_new) / 60))

            print(sum(sub_problem.y_demand_constraint_variable[s].X * sub_problem.total_demand_dict[s]
                for s in sub_problem.demanded_commodities))

            print(sum((sub_problem.y_conv_cap_ub_constraint_variable[c, t, n].X * sub_problem.maximal_power_dict[c]
                 - sub_problem.y_conv_cap_lb_constraint_variable[c, t, n].X * sub_problem.minimal_power_dict[c]
                 + sub_problem.y_conv_cap_ramp_up_constraint_variable[c, t, n].X * sub_problem.ramp_up_dict[c]
                 + sub_problem.y_conv_cap_ramp_down_constraint_variable[c, t, n].X * sub_problem.ramp_down_dict[c])
                * sub_problem.optimal_capacities[c]
                for t in sub_problem.time for c in sub_problem.conversion_components for n in sub_problem.clusters))

            print(sum(sub_problem.y_generation_constraint_variable_active[
                    g, sub_problem.pm_object.get_component(g).get_generated_commodity(), t, n].X
                * sub_problem.optimal_capacities[g] * sub_problem.generation_profiles_certain_dict[g, t, n]
                for n in sub_problem.clusters if n < max(sub_problem.clusters) for t in sub_problem.time for g in
                sub_problem.generator_components))

            print(sum(sub_problem.auxiliary_variable[g, sub_problem.pm_object.get_component(g).get_generated_commodity(), t, p].X
                for g in sub_problem.generator_components for t in sub_problem.time for p in sub_problem.profiles))

            print(sum((sub_problem.y_soc_ub_constraint_variable[s, t, n].X * sub_problem.maximal_soc_dict[s]
                 - sub_problem.y_soc_lb_constraint_variable[s, t, n].X * sub_problem.minimal_soc_dict[s]
                 + sub_problem.y_soc_charge_limit_constraint_variable[s, t, n].X / sub_problem.ratio_capacity_power_dict[s]
                 + sub_problem.y_soc_discharge_limit_constraint_variable[s, t, n].X / sub_problem.ratio_capacity_power_dict[
                     s]) *
                sub_problem.optimal_capacities[s]
                for t in sub_problem.time for s in sub_problem.storage_components for n in sub_problem.clusters))

        total_costs_UB = UB / total_demand['FT']
        total_costs_dict['UB'][iteration] = total_costs_UB

        total_costs_LB = LB / total_demand['FT']
        total_costs_dict['LB'][iteration] = total_costs_LB

        print('Iteration number: ' + str(iteration))

        print(sup_problem.auxiliary_variable_value)
        print(sub_problem.objective_function_value)

        print('Specific costs UB: ' + str(total_costs_UB))
        print('Specific costs LB: ' + str(total_costs_LB))

        # difference = (UB - LB) / LB
        difference = UB - LB
        print('Difference is: ' + str(difference))

        # if -tolerance <= difference <= tolerance:
        if difference <= tolerance:

            print(path_results + 'capacity.xlsx')

            first = True
            for k in [*capacities.keys()]:
                if first:
                    capacity_df = pd.DataFrame.from_dict(capacities[k], orient='index')
                    first = False
                else:
                    capacity_df[k] = pd.DataFrame.from_dict(capacities[k], orient='index')

            capacity_df.to_excel(path_results + 'capacity.xlsx')

            profiles_df = pd.DataFrame()
            for i in [*input_profiles.keys()]:
                for g in [*input_profiles[i].keys()]:
                    for c in [*input_profiles[i][g].keys()]:
                        profiles_df[str(i) + '_' + g + '_' + str(c)] = input_profiles[i][g][c]

            profiles_df.to_excel(path_results + 'profiles.xlsx')

            if True:

                first = True
                total_costs_df = pd.DataFrame()
                for k in [*total_costs_dict.keys()]:
                    if first:
                        total_costs_df = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
                        first = False
                    else:
                        total_costs_df[k] = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
                total_costs_df.to_excel(path_results + 'total_costs.xlsx')

            times[iteration] = (time.time() - time_new) / 60
            times['total'] = (time.time() - time_start) / 60

            times_df = pd.DataFrame(times.values(), index=[*times.keys()])
            times_df.to_excel(path_results + 'times.xlsx')

            print('optimization successful')
            print('time needed: ' + str((time.time() - time_start) / 60) + ' minutes')

            break

        else:
            times[iteration] = (time.time() - time_new) / 60

            iteration += 1
            input_profiles[iteration] = {}

            input_profiles[iteration]['Wind'] = input_profiles[0]['Wind'].copy()
            input_profiles[iteration]['Solar'] = input_profiles[0]['Solar'].copy()

            input_profiles[iteration]['Wind'][worst_case_cluster] = sub_problem.chosen_profiles['Wind']
            input_profiles[iteration]['Solar'][worst_case_cluster] = sub_problem.chosen_profiles['Solar']

            # chosen_profile = None
            # for p in range(number_profiles):
            #     if sub_problem.weighting_profiles_binary[p].X == 1:
            #         chosen_profile = p
            #
            # adjusted_columns = [c for c in all_profiles.columns
            #                     if '_' + str(chosen_profile) not in c]
            # all_profiles = all_profiles[adjusted_columns]
            # number_profiles -= 1

    return capacities_new, not_robust_capacities
