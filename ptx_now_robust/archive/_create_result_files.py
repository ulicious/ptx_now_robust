import pandas as pd
import os

from _helpers_analysis import create_linear_system_of_equations, create_linear_system_of_equations_emissions
from _helpers_gui import save_current_parameters_and_options

import plotly.graph_objects as go
from datetime import datetime


def check_integer_variables(all_variables_dict, pm_object):
    time_depending_variables = {}
    list_values = {}

    status_variables = ['status_on', 'status_off', 'status_off_switch_on', 'status_off_switch_off',
                        'status_standby_switch_on', 'status_standby_switch_off', 'status_standby',
                        'storage_charge_binary', 'storage_discharge_binary']

    for variable_name in status_variables:

        if variable_name not in [*all_variables_dict.keys()]:
            continue

        for key in [*all_variables_dict[variable_name].keys()]:

            c = key[0]

            if all_variables_dict['nominal_cap'][c] == 0:
                continue

            if variable_name not in [*list_values.keys()]:
                list_values[variable_name] = {}

            if c not in [*list_values[variable_name].keys()]:
                list_values[variable_name][c] = []

            list_values[variable_name][c].append(all_variables_dict[variable_name][key])

    for variable_name in [*list_values.keys()]:
        for component in [*list_values[variable_name].keys()]:
            time_depending_variables[(variable_name, component)] = list_values[variable_name][component]

    if pm_object.get_uses_representative_periods():
        columns = ['c' + str(c) + '_' + str(t)
                   for c in range(pm_object.get_number_clusters())
                   for t in range(pm_object.get_covered_period())]
    else:
        columns = [i for i in range(pm_object.get_covered_period())]

    ind = pd.MultiIndex.from_tuples([*time_depending_variables.keys()], names=('Variable', 'Component'))
    time_depending_variables_df = pd.DataFrame(index=ind,
                                               columns=columns)
    time_depending_variables_df = time_depending_variables_df.sort_index()

    for key in [*time_depending_variables.keys()]:
        time_depending_variables_df.loc[key] = time_depending_variables[key]

    if True:
        # Only for maintenance

        if len(time_depending_variables_df.index) > 0:
            time_depending_variables_df.to_excel(pm_object.get_path_data() + '/time_series_binaries.xlsx')


def _create_result_files(pm_object, path_results):

    def create_assumptions_file():

        index_df = []
        base_investment = []
        base_capacity = []
        scaling_factor = []
        capex = []
        capex_unit = []
        fixed_om = []
        variable_om = []
        lifetime = []
        start_up_costs = []

        for c in pm_object.get_final_components_objects():

            if c.component_type == 'storage':
                index_df.append(c.get_name() + ' Storage')
            else:
                index_df.append(c.get_name())

            if c.component_type == 'conversion':

                if c.is_scalable():
                    base_investment.append(c.get_base_investment())
                    base_capacity.append(c.get_base_capacity())
                    scaling_factor.append(c.get_economies_of_scale())
                else:
                    base_investment.append('')
                    base_capacity.append('')
                    scaling_factor.append('')

                capex_basis = c.get_capex_basis()

                main_input = c.get_main_input()
                main_output = c.get_main_output()

                inputs = c.get_inputs()
                outputs = c.get_outputs()

                coefficient = outputs[main_output] / inputs[main_input]

                if c.get_fixed_capacity() > 0:

                    if capex_basis == 'input':
                        capex.append(c.get_investment() / c.get_fixed_capacity())
                        commodity_name = main_input
                        unit = pm_object.get_commodity(main_input).get_unit()
                    else:
                        capex.append(c.get_investment() / (c.get_fixed_capacity() * coefficient))
                        commodity_name = main_output
                        unit = pm_object.get_commodity(main_output).get_unit()

                else:
                    capex.append(0)
                    commodity_name = main_output
                    unit = pm_object.get_commodity(main_output).get_unit()

                if unit == 'MWh':
                    text_capex_unit = monetary_unit + ' / MW ' + commodity_name
                elif unit == 'kWh':
                    text_capex_unit = monetary_unit + ' / kW ' + commodity_name
                else:
                    text_capex_unit = monetary_unit + ' / ' + unit + ' ' + commodity_name + ' * h'

                capex_unit.append(text_capex_unit)

                if c.get_shut_down_ability():
                    start_up_costs.append(c.get_start_up_costs())
                else:
                    start_up_costs.append(0)

            elif c.component_type == 'storage':

                base_investment.append('')
                base_capacity.append('')
                scaling_factor.append('')

                capex.append(c.get_capex())
                commodity_name = c.get_name()
                unit = pm_object.get_commodity(c.get_name()).get_unit()
                capex_unit.append(monetary_unit + ' / ' + unit + ' ' + commodity_name)

                start_up_costs.append(0)

            else:
                base_investment.append('')
                base_capacity.append('')
                scaling_factor.append('')

                capex.append(c.get_capex())
                unit = pm_object.get_commodity(c.get_generated_commodity()).get_unit()
                generated_commodity = c.get_generated_commodity()

                if unit == 'MWh':
                    text_capex_unit = monetary_unit + ' / MW ' + generated_commodity
                elif unit == 'kWh':
                    text_capex_unit = monetary_unit + ' / kW ' + generated_commodity
                else:
                    text_capex_unit = monetary_unit + ' / ' + unit + ' ' + generated_commodity + ' * h'

                capex_unit.append(text_capex_unit)

                start_up_costs.append(0)

            fixed_om.append(c.get_fixed_OM())
            variable_om.append(c.get_variable_OM())
            lifetime.append(c.get_lifetime())

        assumptions_df = pd.DataFrame(index=index_df)
        assumptions_df['Capex'] = capex
        assumptions_df['Capex Unit'] = capex_unit
        assumptions_df['Fixed Operation and Maintenance'] = fixed_om
        assumptions_df['Variable Operation and Maintenance'] = variable_om
        assumptions_df['Lifetime'] = lifetime
        assumptions_df['Start-Up Costs'] = start_up_costs

        assumptions_df.to_excel(new_result_folder + '/0_assumptions.xlsx')

    def analyze_components():

        columns = ['Capacity [input]', 'Capacity Unit [input]', 'Investment [per input]',
                   'Capacity [output]', 'Capacity Unit [output]', 'Investment [per output]', 'Capacity Factor',
                   'Total Investment', 'Annuity', 'Fixed Operation and Maintenance',
                   'Variable Operation and Maintenance', 'Start-Up Costs',
                   'Installation CO2 Emissions', 'Fixed Yearly CO2 Emissions', 'Variable Yearly CO2 Emissions',
                   'Disposal CO2 Emissions']

        capacity_df = pd.DataFrame(columns=columns)
        for component_object in pm_object.get_final_components_objects():
            component_name = component_object.get_name()

            capacity = component_object.get_fixed_capacity()
            investment = component_object.get_investment()
            annuity = component_object.get_annualized_investment()
            fixed_om = component_object.get_total_fixed_costs()
            variable_om = component_object.get_total_variable_costs()

            if component_object.get_component_type() == 'conversion':
                capex_basis = component_object.get_capex_basis()

                main_input = component_object.get_main_input()
                commodity_object_input = pm_object.get_commodity(main_input)
                name_commodity = main_input
                unit_input = commodity_object_input.get_unit()

                main_output = component_object.get_main_output()
                commodity_object_output = pm_object.get_commodity(main_output)
                name_commodity_output = main_output
                unit_output = commodity_object_output.get_unit()

                inputs = component_object.get_inputs()
                outputs = component_object.get_outputs()

                if unit_input == 'MWh':
                    unit_input = 'MW ' + name_commodity
                elif unit_input == 'kWh':
                    unit_input = 'kW ' + name_commodity
                else:
                    unit_input = unit_input + ' ' + name_commodity + ' / h'

                if unit_output == 'MWh':
                    unit_output = 'MW ' + name_commodity_output
                elif unit_output == 'kWh':
                    unit_output = 'kW ' + name_commodity_output
                else:
                    unit_output = unit_output + ' ' + name_commodity_output + ' / h'

                coefficient = outputs[main_output] / inputs[main_input]

                capacity_df.loc[component_name, 'Capacity Basis'] = capex_basis
                capacity_df.loc[component_name, 'Capacity [input]'] = capacity
                capacity_df.loc[component_name, 'Capacity Unit [input]'] = unit_input

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per input]'] = 0
                else:
                    capacity_df.loc[component_name, 'Investment [per input]'] = investment / capacity

                capacity_df.loc[component_name, 'Capacity [output]'] = capacity * coefficient
                capacity_df.loc[component_name, 'Capacity Unit [output]'] = unit_output

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per output]'] = 0
                else:
                    capacity_df.loc[component_name, 'Investment [per output]'] = investment / (capacity * coefficient)

                if capacity > 0:
                    total_input_component = component_object.get_specific_consumed_commodity(name_commodity)
                    capacity_factor = total_input_component / (capacity * 8760)

                else:
                    capacity_factor = 0

                capacity_df.loc[component_name, 'Capacity Factor'] = capacity_factor

                capacity_df.loc[component_name, 'Start-Up Costs'] = component_object.get_total_start_up_costs()

            elif component_object.get_component_type() == 'generator':
                commodity_object = pm_object.get_commodity(component_object.get_generated_commodity())
                name_commodity = commodity_object.get_name()
                unit = commodity_object.get_unit()
                uses_ppa = component_object.get_uses_ppa()

                capacity_df.loc[component_name, 'Capacity [output]'] = capacity
                if unit == 'MWh':
                    unit = 'MW ' + name_commodity
                elif unit == 'kWh':
                    unit = 'kW ' + name_commodity
                else:
                    unit = unit + ' ' + name_commodity + ' / h'

                capacity_df.loc[component_name, 'Capacity Unit [output]'] = unit

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per output]'] = 0
                else:
                    if not uses_ppa:
                        capacity_df.loc[component_name, 'Investment [per output]'] = investment / capacity
                    else:
                        capacity_df.loc[component_name, 'Investment [per output]'] = 0

            else:
                commodity_object = pm_object.get_commodity(component_name)

                component_name += ' Storage'

                commodity_name = commodity_object.get_name()
                unit = commodity_object.get_unit()

                capacity_df.loc[component_name, 'Capacity [input]'] = capacity
                capacity_df.loc[component_name, 'Capacity Unit [input]'] = unit + ' ' + commodity_name

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per input]'] = 0
                else:
                    capacity_df.loc[component_name, 'Investment [per input]'] = investment / capacity

            capacity_df.loc[component_name, 'Total Investment'] = investment
            capacity_df.loc[component_name, 'Annuity'] = annuity
            capacity_df.loc[component_name, 'Fixed Operation and Maintenance'] = fixed_om
            capacity_df.loc[component_name, 'Variable Operation and Maintenance'] = variable_om

            capacity_df.loc[component_name, 'Installation CO2 Emissions'] = component_object.get_total_installation_co2_emissions()
            capacity_df.loc[component_name, 'Fixed Yearly CO2 Emissions'] = component_object.get_total_fixed_co2_emissions()
            capacity_df.loc[component_name, 'Variable Yearly CO2 Emissions'] = component_object.get_total_variable_co2_emissions()
            capacity_df.loc[component_name, 'Disposal CO2 Emissions'] = component_object.get_total_disposal_co2_emissions()

            # todo: Laufzeit der Anlage muss geklärt werden
            capacity_df.loc[component_name, 'Total Yearly CO2 Emissions'] \
                = component_object.get_total_installation_co2_emissions() / 20 \
                + component_object.get_total_fixed_co2_emissions() \
                + component_object.get_total_variable_co2_emissions() \
                + component_object.get_total_disposal_co2_emissions() / 20

        capacity_df.to_excel(new_result_folder + '/2_components.xlsx')

        # Calculate efficiency
        total_energy_input = 0
        total_energy_output = 0
        total_demand = 0

        demanded_commodity = None
        demanded_commodity_unit = None

        for commodity_object in pm_object.get_final_commodities_objects():
            energy_content = commodity_object.get_energy_content()

            purchased = commodity_object.get_purchased_quantity()
            available = commodity_object.get_available_quantity()
            generated = commodity_object.get_generated_quantity()

            total_commodity_in = purchased + available + generated

            total_energy_input += total_commodity_in * energy_content

            sold = commodity_object.get_sold_quantity()
            demand = commodity_object.get_demanded_quantity()

            total_commodity_out = sold + demand

            total_energy_output += total_commodity_out * energy_content

            total_demand += commodity_object.get_demanded_quantity()

            if commodity_object.is_demanded():
                demanded_commodity = commodity_object.get_name()
                demanded_commodity_unit = commodity_object.get_unit()

        efficiency = str(round(total_energy_output / total_energy_input, 4))

        index_overview = ['Annual Production [' + demanded_commodity_unit + ' ' + demanded_commodity + ']',
                          'Total Investment [' + pm_object.get_monetary_unit() + ']',
                          'Total Fix Costs [' + pm_object.get_monetary_unit() + ']',
                          'Total Variable Costs [' + pm_object.get_monetary_unit() + ']',
                          'Total Annual Costs [' + pm_object.get_monetary_unit() + ']',
                          'Production Costs per Unit [' + pm_object.get_monetary_unit() + ' / ' + demanded_commodity_unit + ' ' + demanded_commodity + ']',
                          'Total Fixed Annual CO2 Emissions [t CO2]',
                          'Total Variable Annual CO2 Emissions [t CO2]',
                          'Total Annual CO2 Emissions [t CO2]',
                          'CO2 Emissions per Unit [' + 't CO2 / ' + demanded_commodity_unit + ' ' + demanded_commodity + ']',
                          'Efficiency', 'Production Costs per Unit Objective Function']

        total_production = total_demand
        total_investment = capacity_df['Total Investment'].sum()
        fix_costs = capacity_df['Annuity'].sum() + capacity_df['Fixed Operation and Maintenance'].sum()

        variable_costs = 0
        for commodity_object in pm_object.get_final_commodities_objects():
            variable_costs += commodity_object.get_purchase_costs()
            variable_costs += commodity_object.get_selling_revenue()

        variable_costs += sum(component_object.get_total_variable_costs()
                              for component_object in pm_object.get_final_components_objects())

        fixed_co2_emissions \
            = capacity_df['Installation CO2 Emissions'].sum() + capacity_df['Fixed Yearly CO2 Emissions'].sum() \
            + capacity_df['Disposal CO2 Emissions'].sum()

        variable_co2_emissions = capacity_df['Variable Yearly CO2 Emissions'].sum()
        for commodity_object in pm_object.get_final_commodities_objects():
            variable_co2_emissions += commodity_object.get_total_co2_emissions_available()
            variable_co2_emissions += commodity_object.get_total_co2_emissions_purchase()
            variable_co2_emissions += commodity_object.get_total_co2_emissions_sale()

        annual_costs = fix_costs + variable_costs
        production_costs_per_unit = annual_costs / total_production

        annual_co2_emissions = fixed_co2_emissions + variable_co2_emissions
        co2_emissions_per_unit = annual_co2_emissions / total_production

        production_costs_per_unit_obj = objective_function_value / total_production

        results_overview = pd.Series([total_production, total_investment,
                                      fix_costs, variable_costs, annual_costs, production_costs_per_unit,
                                      fixed_co2_emissions, variable_co2_emissions, annual_co2_emissions,
                                      co2_emissions_per_unit,
                                      efficiency, production_costs_per_unit_obj])
        results_overview.index = index_overview

        results_overview.to_excel(new_result_folder + '/1_results_overview.xlsx')

        exported_results['Production Costs'] = production_costs_per_unit

    def analyze_generation():

        generation_df = pd.DataFrame()
        weightings = pm_object.get_weightings_time_series()

        if len(pm_object.get_final_generator_components_objects()) > 0:

            path = pm_object.get_path_data() + pm_object.get_profile_data()

            if path.split('.')[-1] == 'xlsx':
                generation_profile = pd.read_excel(path, index_col=0)
            else:
                generation_profile = pd.read_csv(path, index_col=0)

            for generator_object in pm_object.get_final_generator_components_objects():
                generator_name = generator_object.get_name()
                generated_commodity = generator_object.get_generated_commodity()

                t_range = range(pm_object.get_covered_period() * pm_object.get_number_clusters())
                generator_profile = generation_profile.iloc[t_range][generator_name]

                capacity = generator_object.get_fixed_capacity()
                investment = generator_object.get_investment()
                annualized_investment = generator_object.get_annualized_investment()
                total_fixed_costs = generator_object.get_total_fixed_costs()
                total_variable_costs = generator_object.get_total_variable_costs()

                generation_df.loc[generator_name, 'Generated Commodity'] = generated_commodity
                generation_df.loc[generator_name, 'Capacity'] = capacity
                
                generation_df.loc[generator_name, 'Investment'] = investment
                generation_df.loc[generator_name, 'Annuity'] = annualized_investment
                generation_df.loc[generator_name, 'Fixed Operation and Maintenance'] = total_fixed_costs
                generation_df.loc[generator_name, 'Variable Operation and Maintenance'] = total_variable_costs

                if capacity != 0:
                    
                    generation_df.loc[generator_name, 'Potential Generation'] \
                        = potential_generation = generator_object.get_potential_generation_quantity()
                    generation_df.loc[generator_name, 'Potential Capacity Factor'] \
                        = generator_object.get_potential_capacity_factor()

                    generation_df.loc[generator_name, 'LCOE before Curtailment'] = \
                        generator_object.get_potential_LCOE()

                    generation_df.loc[generator_name, 'Actual Generation'] \
                        = generator_object.get_generated_quantity()
                    generation_df.loc[generator_name, 'Actual Capacity Factor']\
                        = generator_object.get_actual_capacity_factor()

                    generation_df.loc[generator_name, 'Curtailment'] = generator_object.get_curtailment()
                    generation_df.loc[generator_name, 'LCOE after Curtailment'] = \
                        generator_object.get_actual_LCOE()

                    generation_df.loc[generator_name, 'PPA Price'] = generator_object.get_ppa_price()
                    generation_df.loc[generator_name, 'Total PPA Costs']\
                        = generator_object.get_ppa_price() * potential_generation
                    generation_df.loc[generator_name, 'Sunk Costs from Curtailment'] \
                        = generator_object.get_ppa_price() * generator_object.get_curtailment()
                else:

                    potential_generation = sum(
                        generator_profile.loc[generator_profile.index[t + cl*pm_object.get_covered_period()]] * weightings[cl]
                        for cl in range(pm_object.get_number_clusters()) for t in range(pm_object.get_covered_period()))
                    generation_df.loc[generator_name, 'Potential Generation'] = 0
                    generation_df.loc[generator_name, 'Potential Full-load Hours'] = potential_generation

                    # Calculate potential LCOE
                    wacc = pm_object.get_wacc()
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

                    generation_df.loc[
                        generator_name, 'LCOE before Curtailment'] = total_costs_1_capacity / potential_generation + variable_om

                    generation_df.loc[generator_name, 'Actual Generation'] = 0
                    generation_df.loc[generator_name, 'Actual Full-load Hours'] = 0

                    generation_df.loc[generator_name, 'Curtailment'] = 0
                    generation_df.loc[generator_name, 'LCOE after Curtailment'] = '-'

                    generation_df.loc[generator_name, 'PPA Price'] = generator_object.get_ppa_price()
                    generation_df.loc[generator_name, 'Total PPA Costs'] = 0
                    generation_df.loc[generator_name, 'Sunk Costs from Curtailment'] = 0

            generation_df.to_excel(new_result_folder + '/6_generation.xlsx')

    def analyze_total_costs():
        # Total costs: annuity, maintenance, buying and selling, taxes and insurance, etc.
        total_production = 0
        for commodity_object in pm_object.get_final_commodities_objects():
            if commodity_object.is_demanded():
                total_production += commodity_object.get_demanded_quantity()

        cost_distribution = pd.DataFrame()
        emission_distribution = pd.DataFrame()
        total_costs = 0
        total_emissions = 0

        for component_object in pm_object.get_final_components_objects():
            component_name = component_object.get_name()

            if component_name not in pm_object.get_final_components_names():
                component_name = component_name + ' Storage'

            capacity = component_object.get_fixed_capacity()

            if capacity == 0:
                continue

            annuity = component_object.get_annualized_investment()
            if annuity != 0:
                cost_distribution.loc[component_name + ' Annuity', 'Total'] = annuity
                total_costs += annuity

            fixed_om_costs = component_object.get_total_fixed_costs()
            if fixed_om_costs != 0:
                cost_distribution.loc[component_name + ' Fixed Operation and Maintenance Costs', 'Total'] = \
                    fixed_om_costs
                total_costs += fixed_om_costs

            variable_om_costs = component_object.get_total_variable_costs()
            if variable_om_costs != 0:
                cost_distribution.loc[component_name + ' Variable Operation and Maintenance Costs', 'Total'] = \
                    variable_om_costs
                total_costs += variable_om_costs

            installation_emissions = component_object.get_installation_co2_emissions()
            if installation_emissions != 0:
                emission_distribution.loc[component_name + ' Installation Emissions', 'Total'] = \
                    installation_emissions
                total_costs += installation_emissions

            disposal_emissions = component_object.get_disposal_co2_emissions()
            if disposal_emissions != 0:
                emission_distribution.loc[component_name + ' Disposal Emissions', 'Total'] = \
                    disposal_emissions
                total_costs += disposal_emissions

            fixed_emissions = component_object.get_fixed_co2_emissions()
            if fixed_emissions != 0:
                emission_distribution.loc[component_name + ' Fixed Emissions', 'Total'] = \
                    fixed_emissions
                total_costs += fixed_emissions

            variable_emissions = component_object.get_variable_co2_emissions()
            if variable_emissions != 0:
                emission_distribution.loc[component_name + ' Variable Emissions', 'Total'] = \
                    variable_emissions
                total_costs += variable_emissions

            if component_object.get_component_type() == 'conversion':
                if component_object.get_shut_down_ability():
                    start_up_costs = component_object.get_total_start_up_costs()
                    if start_up_costs != 0:
                        cost_distribution.loc[component_name + ' Start-Up Costs', 'Total'] = start_up_costs
                        total_costs += start_up_costs

            if component_object.get_component_type() == 'generator':
                if component_object.get_uses_ppa():
                    cost_distribution.loc[component_name + ' PPA Costs', 'Total'] \
                        = component_object.get_potential_generation_quantity() * component_object.get_ppa_price()
                    total_costs += component_object.get_potential_generation_quantity() * component_object.get_ppa_price()

        for commodity_object in pm_object.get_final_commodities_objects():
            commodity_name = commodity_object.get_name()

            if commodity_object.get_purchased_quantity() != 0:
                cost_distribution.loc['Purchase Costs ' + commodity_name, 'Total'] \
                    = commodity_object.get_purchase_costs()
                total_costs += commodity_object.get_purchase_costs()

            if commodity_object.get_selling_revenue() < 0:
                cost_distribution.loc['Disposal ' + commodity_name, 'Total'] \
                    = commodity_object.get_selling_revenue()
                total_costs += commodity_object.get_selling_revenue()

            if commodity_object.get_selling_revenue() >= 0:
                cost_distribution.loc['Revenue ' + commodity_name, 'Total'] \
                    = commodity_object.get_selling_revenue()
                total_costs += commodity_object.get_selling_revenue()

            if commodity_object.get_total_co2_emissions_available() != 0:
                emission_distribution.loc['Available Emissions ' + commodity_name, 'Total'] \
                    = commodity_object.get_total_co2_emissions_available()
                total_emissions += commodity_object.get_total_co2_emissions_available()

            if commodity_object.get_total_co2_emissions_emitted() != 0:
                emission_distribution.loc['Direct Emissions ' + commodity_name, 'Total'] \
                    = commodity_object.get_total_co2_emissions_emitted()
                total_emissions += commodity_object.get_total_co2_emissions_emitted()

            if commodity_object.get_total_co2_emissions_purchase() != 0:
                emission_distribution.loc['Purchase Emissions ' + commodity_name, 'Total'] \
                    = commodity_object.get_total_co2_emissions_purchase()
                total_emissions += commodity_object.get_total_co2_emissions_purchase()

            if commodity_object.get_total_co2_emissions_sale() != 0:
                emission_distribution.loc['Selling Emissions ' + commodity_name, 'Total'] \
                    = commodity_object.get_total_co2_emissions_sale()
                total_emissions += commodity_object.get_total_co2_emissions_sale()

        cost_distribution.loc['Total', 'Total'] = total_costs
        cost_distribution.loc[:, 'Per Output'] = cost_distribution.loc[:, 'Total'] / total_production
        cost_distribution.loc[:, '%'] = cost_distribution.loc[:, 'Total'] / cost_distribution.loc['Total', 'Total']
        cost_distribution.to_excel(new_result_folder + '/3_cost_distribution.xlsx')

        emission_distribution.loc['Total', 'Total'] = total_emissions
        emission_distribution.loc[:, 'Per Output'] = emission_distribution.loc[:, 'Total'] / total_production
        emission_distribution.loc[:, '%'] = emission_distribution.loc[:, 'Total'] / total_emissions
        emission_distribution.to_excel(new_result_folder + '/3_emission_distribution.xlsx')

    def copy_input_data():
        import shutil
        if len(pm_object.get_final_generator_components_names()) > 0:

            path = pm_object.get_path_data() + pm_object.get_profile_data()

            if path.split('.')[-1] == 'xlsx':
                shutil.copy(path,
                            new_result_folder + '/8_profile_data.xlsx')
            else:
                shutil.copy(path,
                            new_result_folder + '/8_profile_data.csv')

    # instance = pm_object.instance
    file_name = pm_object.get_project_name()
    monetary_unit = pm_object.get_monetary_unit()
    objective_function_value = pm_object.get_objective_function_value()

    status_variables = ['status_on', 'status_off', 'status_off_switch_on', 'status_off_switch_off',
                        'status_standby_switch_on', 'status_standby_switch_off', 'status_standby',
                        'storage_charge_binary', 'storage_discharge_binary']

    exported_results = {}

    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M%S")

    profile_name = ''
    if pm_object.get_profile_data():
        if pm_object.get_single_or_multiple_profiles() == 'multiple':
            profile_name = pm_object.get_profile_data().split('/')[1].split('.')[0]
        else:
            profile_name = pm_object.get_profile_data().split('.')[0]

    if file_name is None:
        new_result_folder = path_results + dt_string + profile_name
    else:
        new_result_folder = path_results + dt_string + '_' + file_name + '_' + profile_name
    os.makedirs(new_result_folder)

    create_assumptions_file()
    create_linear_system_of_equations(pm_object, new_result_folder)
    create_linear_system_of_equations_emissions(pm_object, new_result_folder)
    analyze_components()
    analyze_generation()
    analyze_total_costs()
    # check_integer_variables()
    pm_object.get_operation_time_series().to_excel(new_result_folder + '/4_operations_time_series.xlsx')
    copy_input_data()

    # build_sankey_diagram(only_energy=False)

    save_current_parameters_and_options(pm_object, new_result_folder + '/7_settings.yaml')
