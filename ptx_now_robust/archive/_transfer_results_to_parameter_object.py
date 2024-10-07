import math
import pandas as pd
from pyomo.core import *
from operator import itemgetter

from _create_result_files import check_integer_variables


def _transfer_results_to_parameter_object(pm_object, model_type):
    all_variables_dict = {}

    if model_type == 'pyomo':
        # access instance to get results from variables

        for v in pm_object.instance.component_objects(Var, active=True):

            variable_dict = v.extract_values()
            if not bool(variable_dict):
                continue

            all_variables_dict.update({str(v): variable_dict})
    elif model_type == 'gurobi':
        for v in pm_object.instance.binary_variables:
            variable_name = [*v.keys()][0]

            if not v[variable_name]:
                continue

            variable_dict = {}

            for key in [*v[variable_name].keys()]:
                variable_dict[key] = v[variable_name][key].X

            all_variables_dict.update({variable_name: variable_dict})

        for v in pm_object.instance.continuous_variables:
            variable_name = [*v.keys()][0]

            if not v[variable_name]:
                continue

            variable_dict = {}

            for key in [*v[variable_name].keys()]:
                variable_dict[key] = v[variable_name][key].X

            all_variables_dict.update({variable_name: variable_dict})

    elif model_type == 'highs':

        result_list = pm_object.instance.solution.col_value

        for var in [*pm_object.instance.index_identifier.keys()]:

            index_list = [*pm_object.instance.index_identifier[var].keys()]
            var_index_list = [*pm_object.instance.index_identifier[var].values()]

            variable_dict = {element: result_list[var_index_list[i]]
                             for i, element in enumerate(index_list)}

            all_variables_dict.update({var: variable_dict})

    # transfer results to parameter object
    annuity_factor = pm_object.get_annuity_factor()
    component_parameters = pm_object.get_all_technical_component_parameters()
    fixed_om = component_parameters[1]
    variable_om = component_parameters[2]
    weightings = pm_object.get_weightings_time_series()

    for key in all_variables_dict['nominal_cap']:
        component = pm_object.get_component(key)
        c = key

        component.set_fixed_capacity(all_variables_dict['nominal_cap'][c])

        installation_co2_emissions = component.get_installation_co2_emissions()
        fixed_co2_emissions = component.get_fixed_co2_emissions()
        disposal_co2_emissions = component.get_disposal_co2_emissions()

        if all_variables_dict['investment'][c] > 0:
            component.set_investment(all_variables_dict['investment'][c])
            component.set_annualized_investment(
                all_variables_dict['investment'][c] * annuity_factor[c])
            component.set_total_fixed_costs(
                all_variables_dict['investment'][c] * fixed_om[c])

            component.set_total_installation_co2_emissions(
                all_variables_dict['nominal_cap'][c] * installation_co2_emissions)
            component.set_total_fixed_co2_emissions(
                all_variables_dict['nominal_cap'][c] * fixed_co2_emissions)
            component.set_total_disposal_co2_emissions(
                all_variables_dict['nominal_cap'][c] * disposal_co2_emissions)
        else:
            component.set_investment(0)
            component.set_annualized_investment(0)
            component.set_total_fixed_costs(0)

            component.set_total_installation_co2_emissions(0)
            component.set_total_disposal_co2_emissions(0)

        variable_co2_emissions = component.get_variable_co2_emissions()

        if component.get_component_type() == 'conversion':

            main_output = pm_object.get_component(c).get_main_output()
            commodity_object = pm_object.get_commodity(main_output)
            total_variable_costs = \
                sum(all_variables_dict['mass_energy_component_out_commodities'][(c, main_output, cl, t)]
                    * variable_om[c] * weightings[cl]
                    for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

            if component.get_shut_down_ability():
                total_start_up_costs = sum(all_variables_dict['restart_costs'][(c, cl, t)]
                                           for cl in range(pm_object.get_number_clusters())
                                           for t in range(pm_object.get_covered_period()))
            else:
                total_start_up_costs = 0

            component.set_total_start_up_costs(total_start_up_costs)

            commodity_object.set_total_production_costs(commodity_object.get_total_production_costs()
                                                        + all_variables_dict['investment'][c] * annuity_factor[c]
                                                        + all_variables_dict['investment'][c] * fixed_om[c]
                                                        + total_variable_costs
                                                        + total_start_up_costs)

            total_variable_co2_emissions = \
                sum(all_variables_dict['mass_energy_component_out_commodities'][(c, main_output, cl, t)]
                    * variable_co2_emissions * weightings[cl]
                    for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

            commodity_object.set_total_co2_emissions_production(
                commodity_object.get_total_co2_emissions_production()
                + all_variables_dict['nominal_cap'][c] * installation_co2_emissions
                + all_variables_dict['nominal_cap'][c] * fixed_co2_emissions
                + total_variable_co2_emissions
                + all_variables_dict['nominal_cap'][c] * disposal_co2_emissions)

        elif component.get_component_type() == 'storage':
            commodity_object = pm_object.get_commodity(component.get_name())
            total_variable_costs = \
                sum(all_variables_dict['mass_energy_storage_in_commodities'][(c, cl, t)]
                    * variable_om[c] * weightings[cl]
                    for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

            commodity_object.set_total_storage_costs(commodity_object.get_total_storage_costs()
                                                     + all_variables_dict['investment'][c] * annuity_factor[c]
                                                     + all_variables_dict['investment'][c] * fixed_om[c]
                                                     + total_variable_costs)

            total_variable_co2_emissions = \
                sum(all_variables_dict['mass_energy_storage_in_commodities'][(c, cl, t)]
                    * variable_co2_emissions * weightings[cl]
                    for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

            commodity_object.set_total_co2_emissions_storage(
                commodity_object.get_total_co2_emissions_storage()
                + all_variables_dict['nominal_cap'][c] * installation_co2_emissions
                + all_variables_dict['nominal_cap'][c] * fixed_co2_emissions
                + total_variable_co2_emissions
                + all_variables_dict['nominal_cap'][c] * disposal_co2_emissions)

        else:
            generated_commodity = component.get_generated_commodity()
            commodity_object = pm_object.get_commodity(generated_commodity)
            if not component.get_uses_ppa():
                total_variable_costs = \
                    sum(all_variables_dict['mass_energy_generation'][(c, generated_commodity, cl, t)]
                        * variable_om[c] * weightings[cl]
                        for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

            else:

                path = pm_object.get_path_data() + pm_object.get_profile_data()

                if path.split('.')[-1] == 'xlsx':
                    generation_profile = pd.read_excel(path, index_col=0)
                else:
                    generation_profile = pd.read_csv(path, index_col=0)

                generator_profile = generation_profile[c]

                total_variable_costs = \
                    sum(generator_profile.loc[generator_profile.index[t + cl * pm_object.get_covered_period()]]
                        * all_variables_dict['nominal_cap'][c] * component.get_ppa_price() * weightings[cl]
                        for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

            commodity_object.set_total_generation_costs(commodity_object.get_total_generation_costs()
                                                        + all_variables_dict['investment'][c] * annuity_factor[c]
                                                        + all_variables_dict['investment'][c] * fixed_om[c]
                                                        + total_variable_costs)

            total_variable_co2_emissions = \
                sum(all_variables_dict['mass_energy_generation'][(c, generated_commodity, cl, t)]
                    * variable_co2_emissions * weightings[cl]
                    for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

            commodity_object.set_total_co2_emissions_generation(
                commodity_object.get_total_co2_emissions_generation()
                + all_variables_dict['nominal_cap'][c] * installation_co2_emissions
                + all_variables_dict['nominal_cap'][c] * fixed_co2_emissions
                + total_variable_co2_emissions
                + all_variables_dict['nominal_cap'][c] * disposal_co2_emissions)

        component.set_total_variable_costs(total_variable_costs)
        component.set_total_variable_co2_emissions(total_variable_co2_emissions)

    # Operational results
    purchase_price_dict = pm_object.get_purchase_price_time_series()
    sell_price_dict = pm_object.get_sale_price_time_series()

    list_values_local = {}
    time_depending_variables_local = {}

    commodity_three_index = ['mass_energy_available', 'mass_energy_emitted', 'mass_energy_storage_in_commodities',
                             'mass_energy_storage_out_commodities', 'soc', 'mass_energy_sell_commodity',
                             'mass_energy_purchase_commodity', 'mass_energy_demand']

    commodity_four_index = ['mass_energy_component_in_commodities', 'mass_energy_component_out_commodities',
                            'mass_energy_generation', 'mass_energy_hot_standby_demand']

    variable_nice_names = {'mass_energy_purchase_commodity': 'Purchase',
                           'mass_energy_available': 'Freely Available',
                           'mass_energy_component_in_commodities': 'Input',
                           'mass_energy_component_out_commodities': 'Output',
                           'mass_energy_generation': 'Generation',
                           'mass_energy_total_generation': 'Total Generation',
                           'mass_energy_storage_in_commodities': 'Charging',
                           'mass_energy_storage_out_commodities': 'Discharging',
                           'soc': 'State of Charge',
                           'mass_energy_sell_commodity': 'Selling',
                           'mass_energy_emitted': 'Emitting',
                           'mass_energy_demand': 'Demand',
                           'mass_energy_hot_standby_demand': 'Hot Standby Demand'}

    all_commodities = []
    for commodity in pm_object.get_final_commodities_objects():
        all_commodities.append(commodity.get_name())

    """ Allocates costs to commodities """
    # Calculate the total availability of each commodity (purchase, from conversion, available)
    for variable in commodity_three_index:
        if variable not in [*all_variables_dict.keys()]:
            continue

        variable_dict = all_variables_dict[variable]

        for k in [*variable_dict.keys()]:

            commodity = k[0]
            commodity_object = pm_object.get_commodity(commodity)
            cluster = k[1]

            specific_co2_emissions_available = commodity_object.get_specific_co2_emissions_available()
            specific_co2_emissions_emitted = commodity_object.get_specific_co2_emissions_emitted()
            specific_co2_emissions_purchase = commodity_object.get_specific_co2_emissions_purchase()
            specific_co2_emissions_sale = commodity_object.get_specific_co2_emissions_sale()

            # get time series from variables
            if variable_dict[k] is None:
                continue

            # create vector from data
            if variable not in [*list_values_local.keys()]:
                list_values_local[variable] = {}

            if commodity not in [*list_values_local[variable].keys()]:
                list_values_local[variable][commodity] = []

            list_values_local[variable][commodity].append(variable_dict[k])

            # get total values from variables
            if variable == 'mass_energy_available':
                commodity_object.set_available_quantity(commodity_object.get_available_quantity()
                                                        + variable_dict[k] * weightings[cluster])

                commodity_object.set_total_co2_emissions_available(commodity_object.get_total_co2_emissions_available()
                                                                   + variable_dict[k] * weightings[cluster]
                                                                   * specific_co2_emissions_available)

            if variable == 'mass_energy_emitted':
                commodity_object.set_emitted_quantity(commodity_object.get_emitted_quantity()
                                                      + variable_dict[k] * weightings[cluster])

                commodity_object.set_total_co2_emissions_emitted(commodity_object.get_total_co2_emissions_emitted()
                                                                 + variable_dict[k] * weightings[cluster]
                                                                 * specific_co2_emissions_emitted)

            if variable == 'mass_energy_purchase_commodity':
                commodity_object.set_purchased_quantity(commodity_object.get_purchased_quantity()
                                                        + variable_dict[k]
                                                        * weightings[cluster])

                commodity_object.set_purchase_costs(commodity_object.get_purchase_costs()
                                                    + variable_dict[k]
                                                    * weightings[cluster]
                                                    * purchase_price_dict[k])

                commodity_object.set_total_co2_emissions_purchase(commodity_object.get_total_co2_emissions_purchase()
                                                                  + variable_dict[k] * weightings[cluster]
                                                                  * specific_co2_emissions_purchase)

            if variable == 'mass_energy_sell_commodity':
                commodity_object.set_sold_quantity(commodity_object.get_purchased_quantity()
                                                   + variable_dict[k] * weightings[cluster])

                commodity_object.set_selling_revenue(commodity_object.get_selling_revenue()
                                                     + variable_dict[k] * weightings[cluster]
                                                     * sell_price_dict[k])

                commodity_object.set_total_co2_emissions_sale(commodity_object.get_total_co2_emissions_sale()
                                                              + variable_dict[k] * weightings[cluster]
                                                              * specific_co2_emissions_sale)

            if variable == 'mass_energy_demand':
                commodity_object.set_demanded_quantity(commodity_object.get_demanded_quantity()
                                                       + variable_dict[k] * weightings[cluster])

            if variable == 'mass_energy_storage_in_commodities':
                commodity_object.set_charged_quantity(commodity_object.get_charged_quantity()
                                                      + variable_dict[k] * weightings[cluster])

            if variable == 'mass_energy_storage_out_commodities':
                commodity_object.set_discharged_quantity(commodity_object.get_discharged_quantity()
                                                         + variable_dict[k] * weightings[cluster])

    for variable in [*list_values_local.keys()]:
        for element in [*list_values_local[variable].keys()]:
            if sum(list_values_local[variable][element]) > 0:
                if variable in [*variable_nice_names.keys()]:
                    time_depending_variables_local[(variable_nice_names[variable], '', element)] \
                        = list_values_local[variable][element]

    list_values_local = {}
    for variable in commodity_four_index:
        if variable not in [*all_variables_dict.keys()]:
            continue

        variable_dict = all_variables_dict[variable]

        for k in [*variable_dict.keys()]:

            if variable_dict[k] is None:
                continue

            component = k[0]
            component_object = pm_object.get_component(component)

            commodity = k[1]
            commodity_object = pm_object.get_commodity(commodity)

            cluster = k[2]

            # get time series data
            if variable not in [*list_values_local.keys()]:
                list_values_local[variable] = {}

            if component not in [*list_values_local[variable].keys()]:
                list_values_local[variable][component] = {}

            if commodity not in [*list_values_local[variable][component].keys()]:
                list_values_local[variable][component][commodity] = []

            list_values_local[variable][component][commodity].append(variable_dict[k])

            # get total values from variables
            ratio = 1
            if component in pm_object.get_conversion_components_names():

                # Check if commodity is fully conversed or parts of it remain
                inputs = pm_object.get_component(component).get_inputs()
                outputs = pm_object.get_component(component).get_outputs()
                if (commodity in [*inputs.keys()]) & (commodity in [*outputs.keys()]):
                    ratio = outputs[commodity] / inputs[commodity]

            if variable == 'mass_energy_component_out_commodities':
                commodity_object.set_produced_quantity(commodity_object.get_produced_quantity()
                                                       + variable_dict[k] * weightings[cluster] * ratio)

                component_object.set_specific_produced_commodity(commodity,
                                                                 component_object.get_specific_produced_commodity(
                                                                     commodity)
                                                                 + variable_dict[k] * weightings[cluster] * ratio)

            if variable == 'mass_energy_component_in_commodities':
                commodity_object.set_consumed_quantity(commodity_object.get_consumed_quantity()
                                                       + variable_dict[k]
                                                       * weightings[cluster] * ratio)

                component_object.set_specific_consumed_commodity(commodity,
                                                                 component_object.get_specific_consumed_commodity(
                                                                     commodity)
                                                                 + variable_dict[k] * weightings[cluster] * ratio)

            if variable == 'mass_energy_generation':
                commodity_object.set_generated_quantity(commodity_object.get_generated_quantity()
                                                        + variable_dict[k] * weightings[cluster])

                component_object.set_generated_quantity(component_object.get_generated_quantity()
                                                        + variable_dict[k] * weightings[cluster])

            if variable == 'mass_energy_hot_standby_demand':
                commodity_object.set_standby_quantity(commodity_object.get_standby_quantity()
                                                      + variable_dict[k] * weightings[cluster])

                component_object.set_standby_quantity(component_object.get_standby_quantity()
                                                      + variable_dict[k] * weightings[cluster])

    for variable in [*list_values_local.keys()]:
        for element in [*list_values_local[variable].keys()]:
            for commodity in [*list_values_local[variable][element].keys()]:
                if sum(list_values_local[variable][element][commodity]) > 0:
                    if variable in [*variable_nice_names.keys()]:
                        time_depending_variables_local[(variable_nice_names[variable], element, commodity)] = \
                            list_values_local[variable][element][commodity]

    # process renewable generation
    total_profile = {}

    if len(pm_object.get_final_generator_components_names()) > 0:

        path = pm_object.get_path_data() + pm_object.get_profile_data()

        if path.split('.')[-1] == 'xlsx':
            generation_profiles = pd.read_excel(path, index_col=0)
        else:
            generation_profiles = pd.read_csv(path, index_col=0)

        for generator in pm_object.get_final_generator_components_names():

            generator_object = pm_object.get_component(generator)
            generator_name = generator
            generated_commodity = generator_object.get_generated_commodity()

            t_range = range(pm_object.get_covered_period() * pm_object.get_number_clusters())
            generator_profile = generation_profiles.iloc[t_range][generator_name]

            capacity = generator_object.get_fixed_capacity()

            if capacity != 0:
                potential_generation = sum(
                    generator_profile.loc[generator_profile.index[t + cl * pm_object.get_covered_period()]]
                    * weightings[cl]
                    for cl in range(pm_object.get_number_clusters())
                    for t in range(pm_object.get_covered_period())) * capacity

                generator_object.set_potential_generation_quantity(potential_generation)
                generator_object.set_potential_capacity_factor(potential_generation / (capacity * 8760))
                generator_object.set_potential_LCOE((generator_object.get_annualized_investment()
                                                     + generator_object.get_total_fixed_costs()
                                                     + generator_object.get_total_variable_costs())
                                                    / potential_generation)

                actual_generation = generator_object.get_generated_quantity()
                generator_object.set_actual_capacity_factor(actual_generation / (capacity * 8760))
                generator_object.set_actual_LCOE((generator_object.get_annualized_investment()
                                                  + generator_object.get_total_fixed_costs()
                                                  + generator_object.get_total_variable_costs())
                                                 / actual_generation)

                curtailment = potential_generation - actual_generation
                generator_object.set_curtailment(curtailment)

                # Get time series
                covered_index = generator_profile.index[
                                0:pm_object.get_covered_period() * pm_object.get_number_clusters()]

                potential_generation = generator_profile * capacity

                time_depending_variables_local[
                    'Potential Generation', generator_object.get_name(), generated_commodity] \
                    = potential_generation.loc[covered_index].tolist()

                if generated_commodity not in [*total_profile.keys()]:
                    total_profile[generated_commodity] = generator_profile
                else:
                    total_profile[generated_commodity] = total_profile[generated_commodity] + generator_profile

            else:

                potential_generation = sum(
                    generator_profile.loc[generator_profile.index[t + cl * pm_object.get_covered_period()]]
                    * weightings[cl]
                    for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))

                generator_object.set_potential_generation_quantity(0)
                generator_object.set_potential_capacity_factor(potential_generation)

                # Calculate potential LCOE
                wacc = pm_object.get_wacc()
                generator_object = pm_object.get_component(generator)
                lifetime = generator_object.get_lifetime()
                if lifetime != 0:
                    anf_component = (1 + wacc) ** lifetime * wacc \
                                    / ((1 + wacc) ** lifetime - 1)
                else:
                    anf_component = 0

                capex = generator_object.get_capex()
                fixed_om = generator_object.get_fixed_OM()
                variable_om = generator_object.get_variable_OM()

                total_costs_1_capacity = capex * (anf_component + fixed_om)

                generator_object.set_potential_LCOE(total_costs_1_capacity / potential_generation + variable_om)
                generator_object.set_actual_capacity_factor(0)
                generator_object.set_actual_LCOE(math.nan)
                generator_object.set_curtailment(0)

    # store operational time series as df
    ind = pd.MultiIndex.from_tuples([*time_depending_variables_local.keys()],
                                    names=('Variable', 'Component', 'Commodity'))

    if pm_object.get_uses_representative_periods():
        columns = ['c' + str(c) + '_' + str(t)
                   for c in range(pm_object.get_number_clusters())
                   for t in range(pm_object.get_covered_period())]
    else:
        columns = [i for i in range(pm_object.get_covered_period())]

    pm_object.operation_time_series = pd.DataFrame(index=ind, columns=['unit'] + columns)
    pm_object.operation_time_series = pm_object.operation_time_series.sort_index()

    for key in [*time_depending_variables_local.keys()]:
        unit = pm_object.get_commodity(key[2]).get_unit()
        if unit == 'MWh':
            unit = 'MW'
        elif unit == 'kWh':
            unit = 'kW'
        else:
            unit = unit + ' / h'
        pm_object.operation_time_series.loc[key, 'unit'] = unit
        # t_range = range(pm_object.pm_object.get_covered_period() * pm_object.pm_object.get_number_clusters())
        pm_object.operation_time_series.loc[key, columns] = time_depending_variables_local[key]

    weighting_list = []
    for cl in range(pm_object.get_number_clusters()):
        for t in range(pm_object.get_covered_period()):
            weighting_list.append(weightings[cl])
    pm_object.operation_time_series.loc[('Weighting', '', ''), columns] = weighting_list

    # Sort index for better readability
    ordered_list = ['Weighting', 'Freely Available', 'Purchase', 'Emitting', 'Selling', 'Demand', 'Charging',
                    'Discharging', 'State of Charge', 'Total Potential Generation', 'Total Generation',
                    'Potential Generation', 'Generation', 'Input', 'Output', 'Hot Standby Demand']

    index_order = []
    for o in ordered_list:
        index = pm_object.operation_time_series[
            pm_object.operation_time_series.index.get_level_values(0) == o].index.tolist()
        if index:
            index_order += pm_object.operation_time_series[
                pm_object.operation_time_series.index.get_level_values(0) == o].index.tolist()

    pm_object.operation_time_series = pm_object.operation_time_series.reindex(index_order).round(3)

    check_integer_variables(all_variables_dict, pm_object)
    
    return all_variables_dict
