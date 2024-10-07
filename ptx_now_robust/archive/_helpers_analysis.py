import pandas as pd
import numpy as np


def create_linear_system_of_equations(pm_object, new_result_folder):
    # todo: currently, variable o&M are included in the total Fixed Costs and not somewhere else

    total_availability = {}

    # Calculate total commodity availability
    for commodity_object in pm_object.get_final_commodities_objects():
        commodity_name = commodity_object.get_name()

        input_tuples = pm_object.get_main_input_to_input_conversions()[0]

        is_input = False
        for input_tuple in input_tuples:
            if input_tuple[1] == commodity_name:
                is_input = True

        difference = 0
        if commodity_name in pm_object.get_final_storage_components_names():
            # Due to charging and discharging efficiency, some mass or energy gets 'lost'
            total_in = commodity_object.get_charged_quantity()
            total_out = commodity_object.get_discharged_quantity()
            difference = total_in - total_out

        if is_input:
            total_availability[commodity_name] \
                = (commodity_object.get_purchased_quantity() + commodity_object.get_generated_quantity()
                   + commodity_object.get_produced_quantity() + commodity_object.get_emitted_quantity()
                   + commodity_object.get_sold_quantity() - difference)
        else:
            total_availability[commodity_name] = commodity_object.get_produced_quantity()

    not_used_commodities = []
    for key in [*total_availability]:
        if total_availability[key] == 0:
            not_used_commodities.append(key)

    total_generation_costs_per_available_unit = {}
    purchase_costs_per_available_unit = {}
    storage_costs_per_available_unit = {}
    selling_costs_per_available_unit = {}
    for commodity_object in pm_object.get_final_commodities_objects():
        commodity_name = commodity_object.get_name()

        if total_availability[commodity_name] == 0:
            total_generation_costs_per_available_unit[commodity_name] = 0
            purchase_costs_per_available_unit[commodity_name] = 0
            storage_costs_per_available_unit[commodity_name] = 0
            selling_costs_per_available_unit[commodity_name] = 0

        else:
            total_generation_costs_per_available_unit[commodity_name] \
                = commodity_object.get_total_generation_costs() / total_availability[commodity_name]

            purchase_costs_per_available_unit[commodity_name]\
                = commodity_object.get_purchase_costs() / total_availability[commodity_name]

            storage_costs_per_available_unit[commodity_name]\
                = commodity_object.get_total_storage_costs() / total_availability[commodity_name]

            selling_costs_per_available_unit[commodity_name]\
                = commodity_object.get_selling_revenue() / total_availability[commodity_name]

    # Second: Next to intrinsic costs, conversion costs exist.
    # Each commodity, which is the main output of a conversion unit,
    # will be matched with the costs this conversion unit produces
    conversion_costs_per_conversed_unit = {}
    for component_object in pm_object.get_final_conversion_components_objects():
        component_name = component_object.get_name()
        main_output = component_object.get_main_output()

        # Components without capacity are not considered, as they don't converse anything
        if component_object.get_fixed_capacity() == 0:
            continue

        # Calculate the conversion costs per conversed unit
        conversion_costs_per_conversed_unit[component_name] = (component_object.get_total_costs()
                                                               / total_availability[main_output])

    columns_index = [*pm_object.get_all_commodities().keys()]
    for component_object in pm_object.get_final_conversion_components_objects():
        component_name = component_object.get_name()
        if component_object.get_fixed_capacity() > 0:
            columns_index.append(component_name)

    coefficients_df = pd.DataFrame(index=columns_index, columns=columns_index)
    coefficients_df.fillna(value=0, inplace=True)

    main_outputs = []
    main_output_coefficients = {}
    for component_object in pm_object.get_final_conversion_components_objects():
        main_output = component_object.get_main_output()
        main_outputs.append(main_output)
        main_output_coefficients[component_object.get_main_output()] = component_object.get_outputs()[main_output]

    all_inputs = []
    final_commodity = None
    for component_object in pm_object.get_final_conversion_components_objects():
        component_name = component_object.get_name()
        inputs = component_object.get_inputs()
        outputs = component_object.get_outputs()
        main_output = component_object.get_main_output()

        if component_object.get_fixed_capacity() == 0:
            continue

        hot_standby_commodity = ''
        hot_standby_demand = 0
        if component_object.get_hot_standby_ability():
            hot_standby_commodity = [*component_object.get_hot_standby_demand().keys()][0]
            hot_standby_demand = (component_object.get_standby_quantity()
                                  / component_object.get_specific_produced_commodity(main_output))

        # First of all, associate inputs to components
        # If hot standby possible: input + hot standby demand -> hot standby demand prt conversed unit
        # If same commodity in input and output: input - output
        # If neither: just input

        # important: component might only produce a share of the commodity (rest is bought, output of other components
        # Therefore, share has to be adjusted

        for i in [*inputs.keys()]:  # commodity in input

            if component_object.get_specific_produced_commodity(main_output) > 0:
                ratio_consumed_to_total = component_object.get_specific_produced_commodity(main_output) \
                    / total_availability[main_output]

            else:
                ratio_consumed_to_total = 1

            if i not in [*outputs.keys()]:  # commodity not in output
                if component_object.get_hot_standby_ability():  # component has hot standby ability
                    if i != hot_standby_commodity:
                        coefficients_df.loc[i, component_name] = inputs[i] * ratio_consumed_to_total
                    else:
                        coefficients_df.loc[i, component_name] = inputs[i] * ratio_consumed_to_total + hot_standby_demand
                else:  # component has no hot standby ability
                    coefficients_df.loc[i, component_name] = inputs[i] * ratio_consumed_to_total
            else:  # commodity in output
                if i in main_outputs:
                    if component_object.get_hot_standby_ability():  # component has hot standby ability
                        if i != hot_standby_commodity:  # hot standby commodity is not commodity
                            coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_consumed_to_total
                        else:
                            coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_consumed_to_total \
                                                                     + hot_standby_demand
                    else:  # component has no hot standby ability
                        coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_consumed_to_total

            all_inputs.append(i)

        for o in [*outputs.keys()]:
            if (o not in [*inputs.keys()]) & (o != main_output):
                coefficients_df.loc[o, component_name] = -outputs[o]

            if pm_object.get_commodity(o).is_demanded():
                final_commodity = o

        coefficients_df.loc[component_name, component_name] = -1

    if final_commodity is not None:
        # The commodity is produced by one of the conversion units.

        # Matching of costs, which do not influence demanded commodity directly (via inputs)
        # Costs of side commodities with no demand (e.g., flares to burn excess gases)
        # will be added to final commodity
        for component_object in pm_object.get_final_conversion_components_objects():
            main_output = pm_object.get_commodity(component_object.get_main_output())
            main_output_name = main_output.get_name()

            component_name = component_object.get_name()
            if component_object.get_fixed_capacity() == 0:
                continue

            if main_output_name not in all_inputs:  # Check if main output is input of other conversion
                if not main_output.is_demanded():  # Check if main output is demanded
                    coefficients_df.loc[component_name, final_commodity] = 1

        # Each commodity, if main output, has its intrinsic costs and the costs of the conversion component
        for commodity in pm_object.get_final_commodities_names():
            for component_object in pm_object.get_final_conversion_components_objects():
                component_name = component_object.get_name()

                if component_object.get_fixed_capacity() == 0:
                    if commodity in main_outputs:
                        coefficients_df.loc[commodity, commodity] = -1
                    continue

                main_output = component_object.get_main_output()
                outputs = component_object.get_outputs()
                if commodity == main_output:
                    commodity_object = pm_object.get_commodity(commodity)

                    # ratio is when several components have same output
                    ratio_different_components = (component_object.get_specific_produced_commodity(commodity)
                             / commodity_object.get_produced_quantity())
                    coefficients_df.loc[component_name, commodity] = 1 / outputs[commodity] * ratio_different_components

                    coefficients_df.loc[commodity, commodity] = -1

            if commodity not in main_outputs:
                coefficients_df.loc[commodity, commodity] = -1

        old_columns = coefficients_df.columns.tolist()
        new_columns = old_columns.copy()
        for commodity in pm_object.get_final_commodities_names():
            new_columns.append(commodity + ' Generation')
            new_columns.append(commodity + ' Purchase')
            new_columns.append(commodity + ' Selling')
            new_columns.append(commodity + ' Storage')

        for i in new_columns:
            for o in new_columns:
                if (i in old_columns) & (o in old_columns):
                    continue

                elif i == o:
                    coefficients_df.loc[i, o] = -1

                elif (o in i) & (o != i):
                    coefficients_df.loc[i, o] = 1

                else:
                    coefficients_df.loc[i, o] = 0

        if True:
            coefficients_df.to_excel(new_result_folder + '/equations.xlsx')

        # Right hand side (constants)
        coefficients_dict = {}
        commodity_equations_constant = {}
        for column in coefficients_df.columns:
            coefficients_dict.update({column: coefficients_df[column].tolist()})
            if column in pm_object.get_final_commodities_names():
                commodity_equations_constant.update({column: 0})

            if column in pm_object.get_final_conversion_components_names():
                component_object = pm_object.get_component(column)
                if component_object.get_fixed_capacity() == 0:
                    continue

                main_output = component_object.get_main_output()
                commodity_equations_constant.update({column: (-conversion_costs_per_conversed_unit[column]
                                                              * main_output_coefficients[main_output])})

            if 'Generation' in column: # todo: wird aktuell getestet - Das funktioniert so nicht, wenn eine Komponente z.B. FT Crude heißt (Leerzeichen)
                commodity_equations_constant.update({column: -total_generation_costs_per_available_unit[column.split(' Generation')[0]]})
            if 'Purchase' in column:
                commodity_equations_constant.update({column: -purchase_costs_per_available_unit[column.split(' Purchase')[0]]})
            if 'Selling' in column:
                commodity_equations_constant.update({column: -selling_costs_per_available_unit[column.split(' Selling')[0]]})
            if 'Storage' in column:
                commodity_equations_constant.update({column: -storage_costs_per_available_unit[column.split(' Storage')[0]]})

        if True:
            pd.DataFrame.from_dict(commodity_equations_constant, orient='index').to_excel(
                new_result_folder + '/commodity_equations_constant.xlsx')

        values_equations = coefficients_dict.values()
        A = np.array(list(values_equations))
        values_constant = commodity_equations_constant.values()
        B = np.array(list(values_constant))
        X = np.linalg.solve(A, B)

        production_cost_commodity_per_unit = {}
        for i, component_name in enumerate(columns_index):
            production_cost_commodity_per_unit.update({component_name: X[i]})

        commodities_and_costs = pd.DataFrame()
        dataframe_dict = {}

        for column in columns_index:

            if column in pm_object.get_final_commodities_names():
                commodity = column
                commodity_object = pm_object.get_commodity(commodity)
                commodities_and_costs.loc[commodity, 'unit'] = commodity_object.get_unit()
                commodities_and_costs.loc[commodity, 'MWh per unit'] = commodity_object.get_energy_content()

                commodities_and_costs.loc[commodity, 'Available Commodity'] = commodity_object.get_available_quantity()
                commodities_and_costs.loc[commodity, 'Emitted Commodity'] = commodity_object.get_emitted_quantity()
                commodities_and_costs.loc[commodity, 'Purchased Commodity'] = commodity_object.get_purchased_quantity()
                commodities_and_costs.loc[commodity, 'Sold Commodity'] = commodity_object.get_sold_quantity()
                commodities_and_costs.loc[commodity, 'Generated Commodity'] = commodity_object.get_generated_quantity()
                commodities_and_costs.loc[commodity, 'Stored Commodity'] = commodity_object.get_charged_quantity()
                commodities_and_costs.loc[commodity, 'Produced Commodity'] = commodity_object.get_produced_quantity()
                commodities_and_costs.loc[commodity, 'Total Commodity'] = total_availability[commodity]

                commodities_and_costs.loc[commodity, 'Total Purchase Costs'] = commodity_object.get_purchase_costs()
                if commodity_object.get_purchased_quantity() > 0:
                    purchase_costs = commodity_object.get_purchase_costs() / commodity_object.get_purchased_quantity()
                    commodities_and_costs.loc[commodity, 'Average Purchase Costs per purchased Unit'] = purchase_costs
                else:
                    commodities_and_costs.loc[commodity, 'Average Purchase Costs per purchased Unit'] = 0

                commodities_and_costs.loc[commodity, 'Total Selling Revenue/Disposal Costs']\
                    = commodity_object.get_selling_revenue()
                if commodity_object.get_sold_quantity() > 0:
                    revenue\
                        = commodity_object.get_selling_revenue() / commodity_object.get_sold_quantity()
                    commodities_and_costs.loc[
                        commodity, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] \
                        = revenue
                else:
                    commodities_and_costs.loc[
                        commodity, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] \
                        = 0

                total_variable_costs\
                    = commodity_object.get_purchase_costs() + commodity_object.get_selling_revenue()
                commodities_and_costs.loc[commodity, 'Total Variable Costs'] = total_variable_costs

                commodities_and_costs.loc[commodity, 'Total Generation Costs']\
                    = commodity_object.get_total_generation_costs()
                if commodity_object.get_generated_quantity() > 0:
                    commodities_and_costs.loc[commodity, 'Generation Costs per used unit'] \
                        = commodity_object.get_total_generation_costs() / commodity_object.get_generated_quantity()
                else:
                    commodities_and_costs.loc[commodity, 'Costs per used unit'] = 0

                commodities_and_costs.loc[commodity, 'Total Storage Costs'] = commodity_object.get_total_storage_costs()
                if commodity_object.get_discharged_quantity() > 0:
                    stored_costs\
                        = commodity_object.get_total_storage_costs() / commodity_object.get_discharged_quantity()
                    commodities_and_costs.loc[commodity, 'Storage Costs per stored Unit'] = stored_costs
                else:
                    commodities_and_costs.loc[commodity, 'Storage Costs per stored Unit'] = 0

                commodities_and_costs.loc[commodity, 'Total Production Costs']\
                    = commodity_object.get_total_production_costs()
                if commodity_object.get_produced_quantity() > 0:
                    conversion_costs\
                        = commodity_object.get_total_production_costs() / commodity_object.get_produced_quantity()
                    commodities_and_costs.loc[
                        commodity, 'Total Production Costs per produced Unit'] = conversion_costs
                else:
                    commodities_and_costs.loc[commodity, 'Total Production Costs per produced Unit'] = 0

                total_fix_costs \
                    = (commodity_object.get_total_production_costs() + commodity_object.get_total_storage_costs()
                       + commodity_object.get_total_generation_costs())
                commodities_and_costs.loc[commodity, 'Total Fix Costs'] = total_fix_costs

                total_costs = total_variable_costs + total_fix_costs
                commodities_and_costs.loc[commodity, 'Total Costs'] = total_costs

                if total_availability[commodity] > 0:
                    commodities_and_costs.loc[commodity, 'Total Costs per Unit'] \
                        = total_costs / total_availability[commodity]
                else:
                    commodities_and_costs.loc[commodity, 'Total Costs per Unit'] = 0

                if (total_generation_costs_per_available_unit[commodity]
                    + storage_costs_per_available_unit[commodity]
                    + purchase_costs_per_available_unit[commodity]
                    + selling_costs_per_available_unit[commodity]) >= 0:
                    commodities_and_costs.loc[commodity, 'Production Costs per Unit'] \
                        = production_cost_commodity_per_unit[commodity]
                else:
                    commodities_and_costs.loc[commodity, 'Production Costs per Unit'] \
                        = - production_cost_commodity_per_unit[commodity]

                commodities_and_costs.to_excel(new_result_folder + '/5_commodities.xlsx')
                commodities_and_costs = commodities_and_costs

            else:
                component_name = column
                component_object = pm_object.get_component(component_name)

                main_output = component_object.get_main_output()
                main_output_object = pm_object.get_commodity(main_output)

                commodity_object = pm_object.get_commodity(main_output)
                unit = commodity_object.get_unit()

                index = component_name + ' [' + unit + ' ' + main_output + ']'

                component_list = [index, index, index]
                kpis = ['Coefficient', 'Cost per Unit', 'Total Costs']

                arrays = [component_list, kpis]
                m_index = pd.MultiIndex.from_arrays(arrays, names=('Component', 'KPI'))
                components_and_costs = pd.DataFrame(index=m_index)

                conv_costs = round(conversion_costs_per_conversed_unit[component_name], 3)
                total_costs = conv_costs

                components_and_costs.loc[(index, 'Coefficient'), 'Intrinsic'] = 1
                components_and_costs.loc[(index, 'Cost per Unit'), 'Intrinsic'] = conv_costs
                components_and_costs.loc[(index, 'Total Costs'), 'Intrinsic'] = conv_costs

                inputs = component_object.get_inputs()
                outputs = component_object.get_outputs()
                main_output_coefficient = outputs[main_output]
                processed_outputs = []
                for i in [*inputs.keys()]:
                    input_name = i

                    in_coeff = round(inputs[i] / main_output_coefficient, 3)
                    prod_costs = round(production_cost_commodity_per_unit[i], 3)
                    input_costs = round(production_cost_commodity_per_unit[i] * inputs[i]
                                        / main_output_coefficient, 3)

                    input_name += ' (Input)'

                    components_and_costs.loc[(index, 'Coefficient'), input_name] = in_coeff
                    components_and_costs.loc[(index, 'Cost per Unit'), input_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), input_name] = input_costs

                    total_costs += input_costs

                    if i in [*outputs.keys()]:
                        # Handle output earlier s.t. its close to input of same commodity in excel file
                        output_name = i
                        output_object = pm_object.get_commodity(output_name)
                        out_coeff = round(outputs[i] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the commodity needs to be disposed, for example -> positive

                        if output_object.get_selling_revenue() > 0:  # Case 3
                            prod_costs = round(production_cost_commodity_per_unit[i], 3)
                            output_costs = round(production_cost_commodity_per_unit[i] * outputs[i]
                                                 / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_costs = - round(production_cost_commodity_per_unit[i], 3)
                            output_costs = - round(production_cost_commodity_per_unit[i] * outputs[i]
                                                   / main_output_coefficient, 3)

                        output_name += ' (Output)'

                        components_and_costs.loc[(index, 'Coefficient'), output_name] = out_coeff
                        components_and_costs.loc[(index, 'Cost per Unit'), output_name] = prod_costs
                        components_and_costs.loc[(index, 'Total Costs'), output_name] = output_costs

                        total_costs += output_costs

                        processed_outputs.append(i)

                for o in [*outputs.keys()]:
                    if o in processed_outputs:
                        continue

                    output_name = o
                    output_object = pm_object.get_commodity(output_name)

                    if o != component_object.get_main_output():
                        out_coeff = round(outputs[o] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the commodity needs to be disposed, for example -> positive

                        if output_object.get_selling_revenue() > 0:  # Case 3: Disposal costs exist
                            prod_costs = round(production_cost_commodity_per_unit[o], 3)
                            output_costs = round(production_cost_commodity_per_unit[o] * outputs[o]
                                                 / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_costs = - round(production_cost_commodity_per_unit[o], 3)
                            output_costs = - round(production_cost_commodity_per_unit[o] * outputs[o]
                                                   / main_output_coefficient, 3)

                        output_name += ' (Output)'

                        components_and_costs.loc[(index, 'Coefficient'), output_name] = out_coeff
                        components_and_costs.loc[(index, 'Cost per Unit'), output_name] = prod_costs
                        components_and_costs.loc[(index, 'Total Costs'), output_name] = output_costs

                        total_costs += output_costs

                # Further costs, which are not yet in commodity, need to be associated
                # In case that several components have same main output, costs are matched regarding share of production
                component_object = pm_object.get_component(component_name)
                ratio = (component_object.get_specific_produced_commodity(commodity)
                         / main_output_object.get_produced_quantity())

                if main_output in pm_object.get_final_storage_components_names():
                    column_name = 'Storage Costs'
                    components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                    prod_costs = (main_output_object.get_total_storage_costs() / main_output_object.get_produced_quantity())
                    components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                    total_costs += prod_costs * ratio

                if commodity_object.is_demanded():
                    for commodity in pm_object.get_final_commodities_names():
                        if (commodity not in all_inputs) & (commodity in main_outputs) & (commodity != main_output):

                            column_name = commodity + ' (Associated Costs)'
                            components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                            prod_costs = (production_cost_commodity_per_unit[commodity]
                                          * commodity_object.get_produced_quantity()
                                          / main_output_object.get_produced_quantity())
                            components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                            components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                            total_costs += prod_costs * ratio

                prod_costs = round(total_costs, 3)
                components_and_costs.loc[(index, 'Coefficient'), 'Final'] = ''
                components_and_costs.loc[(index, 'Cost per Unit'), 'Final'] = ''
                components_and_costs.loc[(index, 'Total Costs'), 'Final'] = prod_costs

                dataframe_dict[component_name] = components_and_costs

            # Save dataframes in multi-sheet excel file
            if True:
                with pd.ExcelWriter(new_result_folder + '/main_output_costs.xlsx', engine="xlsxwriter") as writer:
                    for df in [*dataframe_dict.keys()]:
                        sheet_name = df.replace("Parallel Unit", "PU")
                        dataframe_dict[df].to_excel(writer, sheet_name)
                    # writer.close()


def create_linear_system_of_equations_emissions(pm_object, new_result_folder):
    # todo: currently, variable o&M are included in the total Fixed Costs and not somewhere else

    total_availability = {}

    # Calculate total commodity availability
    for commodity_object in pm_object.get_final_commodities_objects():
        commodity_name = commodity_object.get_name()

        input_tuples = pm_object.get_main_input_to_input_conversions()[0]

        is_input = False
        for input_tuple in input_tuples:
            if input_tuple[1] == commodity_name:
                is_input = True

        difference = 0
        if commodity_name in pm_object.get_final_storage_components_names():
            # Due to charging and discharging efficiency, some mass or energy gets 'lost'
            total_in = commodity_object.get_charged_quantity()
            total_out = commodity_object.get_discharged_quantity()
            difference = total_in - total_out

        if is_input:
            total_availability[commodity_name] \
                = (commodity_object.get_purchased_quantity() + commodity_object.get_generated_quantity()
                   + commodity_object.get_produced_quantity() + commodity_object.get_emitted_quantity()
                   + commodity_object.get_sold_quantity() - difference)
        else:
            total_availability[commodity_name] = commodity_object.get_produced_quantity()

    not_used_commodities = []
    for key in [*total_availability]:
        if total_availability[key] == 0:
            not_used_commodities.append(key)

    total_generation_emissions_per_available_unit = {}
    purchase_emissions_per_available_unit = {}
    storage_emissions_per_available_unit = {}
    selling_emissions_per_available_unit = {}
    for commodity_object in pm_object.get_final_commodities_objects():
        commodity_name = commodity_object.get_name()

        if total_availability[commodity_name] == 0:
            total_generation_emissions_per_available_unit[commodity_name] = 0
            purchase_emissions_per_available_unit[commodity_name] = 0
            storage_emissions_per_available_unit[commodity_name] = 0
            selling_emissions_per_available_unit[commodity_name] = 0

        else:
            total_generation_emissions_per_available_unit[commodity_name] \
                = commodity_object.get_total_co2_emissions_generation() / total_availability[commodity_name]

            purchase_emissions_per_available_unit[commodity_name] \
                = commodity_object.get_total_co2_emissions_purchase() / total_availability[commodity_name]

            storage_emissions_per_available_unit[commodity_name]\
                = commodity_object.get_total_co2_emissions_available() / total_availability[commodity_name]

            selling_emissions_per_available_unit[commodity_name]\
                = commodity_object.get_total_co2_emissions_sale() / total_availability[commodity_name]

    # Second: Next to intrinsic emissions, conversion emissions exist.
    # Each commodity, which is the main output of a conversion unit,
    # will be matched with the emissions this conversion unit produces
    conversion_emissions_per_conversed_unit = {}
    for component_object in pm_object.get_final_conversion_components_objects():
        component_name = component_object.get_name()
        main_output = component_object.get_main_output()

        # Components without capacity are not considered, as they don't converse anything
        if component_object.get_fixed_capacity() == 0:
            continue

        # Calculate the conversion emissions per conversed unit
        conversion_emissions_per_conversed_unit[component_name] = (component_object.get_total_co2_emissions()
                                                               / total_availability[main_output])

    columns_index = [*pm_object.get_all_commodities().keys()]
    for component_object in pm_object.get_final_conversion_components_objects():
        component_name = component_object.get_name()
        if component_object.get_fixed_capacity() > 0:
            columns_index.append(component_name)

    coefficients_df = pd.DataFrame(index=columns_index, columns=columns_index)
    coefficients_df.fillna(value=0, inplace=True)

    main_outputs = []
    main_output_coefficients = {}
    for component_object in pm_object.get_final_conversion_components_objects():
        main_output = component_object.get_main_output()
        main_outputs.append(main_output)
        main_output_coefficients[component_object.get_main_output()] = component_object.get_outputs()[main_output]

    all_inputs = []
    final_commodity = None
    for component_object in pm_object.get_final_conversion_components_objects():
        component_name = component_object.get_name()
        inputs = component_object.get_inputs()
        outputs = component_object.get_outputs()
        main_output = component_object.get_main_output()

        if component_object.get_fixed_capacity() == 0:
            continue

        hot_standby_commodity = ''
        hot_standby_demand = 0
        if component_object.get_hot_standby_ability():
            hot_standby_commodity = [*component_object.get_hot_standby_demand().keys()][0]
            hot_standby_demand = (component_object.get_standby_quantity()
                                  / component_object.get_specific_produced_commodity(main_output))

        # First of all, associate inputs to components
        # If hot standby possible: input + hot standby demand -> hot standby demand prt conversed unit
        # If same commodity in input and output: input - output
        # If neither: just input

        # important: component might only produce a share of the commodity (rest is bought, output of other components
        # Therefore, share has to be adjusted

        for i in [*inputs.keys()]:  # commodity in input

            if component_object.get_specific_produced_commodity(main_output) > 0:
                ratio_consumed_to_total = component_object.get_specific_produced_commodity(main_output) \
                    / total_availability[main_output]

            else:
                ratio_consumed_to_total = 1

            if i not in [*outputs.keys()]:  # commodity not in output
                if component_object.get_hot_standby_ability():  # component has hot standby ability
                    if i != hot_standby_commodity:
                        coefficients_df.loc[i, component_name] = inputs[i] * ratio_consumed_to_total
                    else:
                        coefficients_df.loc[i, component_name] = inputs[i] * ratio_consumed_to_total + hot_standby_demand
                else:  # component has no hot standby ability
                    coefficients_df.loc[i, component_name] = inputs[i] * ratio_consumed_to_total
            else:  # commodity in output
                if i in main_outputs:
                    if component_object.get_hot_standby_ability():  # component has hot standby ability
                        if i != hot_standby_commodity:  # hot standby commodity is not commodity
                            coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_consumed_to_total
                        else:
                            coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_consumed_to_total \
                                                                     + hot_standby_demand
                    else:  # component has no hot standby ability
                        coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_consumed_to_total

            all_inputs.append(i)

        for o in [*outputs.keys()]:
            if (o not in [*inputs.keys()]) & (o != main_output):
                coefficients_df.loc[o, component_name] = -outputs[o]

            if pm_object.get_commodity(o).is_demanded():
                final_commodity = o

        coefficients_df.loc[component_name, component_name] = -1

    if final_commodity is not None:
        # The commodity is produced by one of the conversion units.

        # Matching of emissions, which do not influence demanded commodity directly (via inputs)
        # Emissions of side commodities with no demand (e.g., flares to burn excess gases)
        # will be added to final commodity
        for component_object in pm_object.get_final_conversion_components_objects():
            main_output = pm_object.get_commodity(component_object.get_main_output())
            main_output_name = main_output.get_name()

            component_name = component_object.get_name()
            if component_object.get_fixed_capacity() == 0:
                continue

            if main_output_name not in all_inputs:  # Check if main output is input of other conversion
                if not main_output.is_demanded():  # Check if main output is demanded
                    coefficients_df.loc[component_name, final_commodity] = 1

        # Each commodity, if main output, has its intrinsic emissions and the emissions of the conversion component
        for commodity in pm_object.get_final_commodities_names():
            for component_object in pm_object.get_final_conversion_components_objects():
                component_name = component_object.get_name()

                if component_object.get_fixed_capacity() == 0:
                    if commodity in main_outputs:
                        coefficients_df.loc[commodity, commodity] = -1
                    continue

                main_output = component_object.get_main_output()
                outputs = component_object.get_outputs()
                if commodity == main_output:
                    commodity_object = pm_object.get_commodity(commodity)

                    # ratio is when several components have same output
                    ratio_different_components = (component_object.get_specific_produced_commodity(commodity)
                             / commodity_object.get_produced_quantity())
                    coefficients_df.loc[component_name, commodity] = 1 / outputs[commodity] * ratio_different_components

                    coefficients_df.loc[commodity, commodity] = -1

            if commodity not in main_outputs:
                coefficients_df.loc[commodity, commodity] = -1

        old_columns = coefficients_df.columns.tolist()
        new_columns = old_columns.copy()
        for commodity in pm_object.get_final_commodities_names():
            new_columns.append(commodity + ' Generation')
            new_columns.append(commodity + ' Purchase')
            new_columns.append(commodity + ' Selling')
            new_columns.append(commodity + ' Storage')

        for i in new_columns:
            for o in new_columns:
                if (i in old_columns) & (o in old_columns):
                    continue

                elif i == o:
                    coefficients_df.loc[i, o] = -1

                elif (o in i) & (o != i):
                    coefficients_df.loc[i, o] = 1

                else:
                    coefficients_df.loc[i, o] = 0

        if True:
            coefficients_df.to_excel(new_result_folder + '/equations.xlsx')

        # Right hand side (constants)
        coefficients_dict = {}
        commodity_equations_constant = {}
        for column in coefficients_df.columns:
            coefficients_dict.update({column: coefficients_df[column].tolist()})
            if column in pm_object.get_final_commodities_names():
                commodity_equations_constant.update({column: 0})

            if column in pm_object.get_final_conversion_components_names():
                component_object = pm_object.get_component(column)
                if component_object.get_fixed_capacity() == 0:
                    continue

                main_output = component_object.get_main_output()
                commodity_equations_constant.update({column: (-conversion_emissions_per_conversed_unit[column]
                                                              * main_output_coefficients[main_output])})

            # todo: wird aktuell getestet - Das funktioniert so nicht, wenn eine Komponente z.B. FT Crude heißt (Leerzeichen)
            if 'Generation' in column:
                commodity_equations_constant.update(
                    {column: -total_generation_emissions_per_available_unit[column.split(' Generation')[0]]})
            if 'Purchase' in column:
                commodity_equations_constant.update(
                    {column: -purchase_emissions_per_available_unit[column.split(' Purchase')[0]]})
            if 'Selling' in column:
                commodity_equations_constant.update(
                    {column: -selling_emissions_per_available_unit[column.split(' Selling')[0]]})
            if 'Storage' in column:
                commodity_equations_constant.update(
                    {column: -storage_emissions_per_available_unit[column.split(' Storage')[0]]})

        if True:
            pd.DataFrame.from_dict(commodity_equations_constant, orient='index').to_excel(
                new_result_folder + '/commodity_emissions_equations_constant.xlsx')

        values_equations = coefficients_dict.values()
        A = np.array(list(values_equations))
        values_constant = commodity_equations_constant.values()
        B = np.array(list(values_constant))
        X = np.linalg.solve(A, B)

        production_cost_commodity_per_unit = {}
        for i, component_name in enumerate(columns_index):
            production_cost_commodity_per_unit.update({component_name: X[i]})

        # todo: define column headers before
        commodities_and_emissions = pd.DataFrame()
        dataframe_dict = {}

        for column in columns_index:

            commodity = column

            if column in pm_object.get_final_commodities_names():
                commodity_object = pm_object.get_commodity(commodity)
                commodities_and_emissions.loc[commodity, 'unit'] = commodity_object.get_unit()
                commodities_and_emissions.loc[commodity, 'MWh per unit'] = commodity_object.get_energy_content()

                commodities_and_emissions.loc[commodity, 'Available Commodity'] = commodity_object.get_available_quantity()
                commodities_and_emissions.loc[commodity, 'Emitted Commodity'] = commodity_object.get_emitted_quantity()
                commodities_and_emissions.loc[commodity, 'Purchased Commodity'] = commodity_object.get_purchased_quantity()
                commodities_and_emissions.loc[commodity, 'Sold Commodity'] = commodity_object.get_sold_quantity()
                commodities_and_emissions.loc[commodity, 'Generated Commodity'] = commodity_object.get_generated_quantity()
                commodities_and_emissions.loc[commodity, 'Stored Commodity'] = commodity_object.get_charged_quantity()
                commodities_and_emissions.loc[commodity, 'Produced Commodity'] = commodity_object.get_produced_quantity()
                commodities_and_emissions.loc[commodity, 'Total Commodity'] = total_availability[commodity]

                commodities_and_emissions.loc[commodity, 'Total Purchase Emissions'] = commodity_object.get_total_co2_emissions_purchase()
                if commodity_object.get_purchased_quantity() > 0:
                    purchase_emissions = commodity_object.get_total_co2_emissions_purchase() / commodity_object.get_purchased_quantity()
                    commodities_and_emissions.loc[commodity, 'Average Purchase Emissions per purchased Unit'] = purchase_emissions
                else:
                    commodities_and_emissions.loc[commodity, 'Average Purchase Emissions per purchased Unit'] = 0

                commodities_and_emissions.loc[commodity, 'Total Emissions Sold']\
                    = commodity_object.get_total_co2_emissions_sale()
                if commodity_object.get_sold_quantity() > 0:
                    revenue\
                        = commodity_object.get_selling_revenue() / commodity_object.get_sold_quantity()
                    commodities_and_emissions.loc[
                        commodity, 'Average Emissions Sold per sold/disposed Unit'] \
                        = revenue
                else:
                    commodities_and_emissions.loc[
                        commodity, 'Average Emissions Sold per sold/disposed Unit'] \
                        = 0

                total_variable_emissions\
                    = commodity_object.get_total_co2_emissions_purchase() - commodity_object.get_total_co2_emissions_sale()
                commodities_and_emissions.loc[commodity, 'Total Variable Emissions'] = total_variable_emissions

                commodities_and_emissions.loc[commodity, 'Total Generation Emissions']\
                    = commodity_object.get_total_co2_emissions_generation()
                if commodity_object.get_generated_quantity() > 0:
                    commodities_and_emissions.loc[commodity, 'Generation Emissions per used unit'] \
                        = commodity_object.get_total_co2_emissions_generation() / commodity_object.get_generated_quantity()
                else:
                    commodities_and_emissions.loc[commodity, 'Emissions per used unit'] = 0

                commodities_and_emissions.loc[commodity, 'Total Storage Emissions'] = commodity_object.get_total_co2_emissions_storage()
                if commodity_object.get_discharged_quantity() > 0:
                    stored_emissions\
                        = commodity_object.get_total_co2_emissions_storage() / commodity_object.get_discharged_quantity()
                    commodities_and_emissions.loc[commodity, 'Storage Emissions per stored Unit'] = stored_emissions
                else:
                    commodities_and_emissions.loc[commodity, 'Storage Emissions per stored Unit'] = 0

                commodities_and_emissions.loc[commodity, 'Total Production Emissions']\
                    = commodity_object.get_total_co2_emissions_production()
                if commodity_object.get_produced_quantity() > 0:
                    conversion_emissions\
                        = commodity_object.get_total_co2_emissions_production() / commodity_object.get_produced_quantity()
                    commodities_and_emissions.loc[
                        commodity, 'Total Production Emissions per produced Unit'] = conversion_emissions
                else:
                    commodities_and_emissions.loc[commodity, 'Total Production Emissions per produced Unit'] = 0

                total_fix_emissions \
                    = (commodity_object.get_total_co2_emissions_production() + commodity_object.get_total_co2_emissions_storage()
                       + commodity_object.get_total_co2_emissions_generation())
                commodities_and_emissions.loc[commodity, 'Total Fix Emissions'] = total_fix_emissions

                total_emissions = total_variable_emissions + total_fix_emissions
                commodities_and_emissions.loc[commodity, 'Total Emissions'] = total_emissions

                if total_availability[commodity] > 0:
                    commodities_and_emissions.loc[commodity, 'Total Emissions per Unit'] \
                        = total_emissions / total_availability[commodity]
                else:
                    commodities_and_emissions.loc[commodity, 'Total Emissions per Unit'] = 0

                if (total_generation_emissions_per_available_unit[commodity]
                        + storage_emissions_per_available_unit[commodity]
                        + purchase_emissions_per_available_unit[commodity]
                        + selling_emissions_per_available_unit[commodity]) >= 0:
                    commodities_and_emissions.loc[commodity, 'Production Emissions per Unit'] \
                        = production_cost_commodity_per_unit[commodity]
                else:
                    commodities_and_emissions.loc[commodity, 'Production Emissions per Unit'] \
                        = - production_cost_commodity_per_unit[commodity]

                commodities_and_emissions.to_excel(new_result_folder + '/5_commodity_emissions.xlsx')
                commodities_and_emissions = commodities_and_emissions

            else:
                component_name = column
                component_object = pm_object.get_component(component_name)

                main_output = component_object.get_main_output()
                main_output_object = pm_object.get_commodity(main_output)

                commodity_object = pm_object.get_commodity(main_output)
                unit = commodity_object.get_unit()

                index = component_name + ' [' + unit + ' ' + main_output + ']'

                component_list = [index, index, index]
                kpis = ['Coefficient', 'Cost per Unit', 'Total Emissions']

                arrays = [component_list, kpis]
                m_index = pd.MultiIndex.from_arrays(arrays, names=('Component', 'KPI'))
                components_and_emissions = pd.DataFrame(index=m_index)

                conv_emissions = round(conversion_emissions_per_conversed_unit[component_name], 3)
                total_emissions = conv_emissions

                components_and_emissions.loc[(index, 'Coefficient'), 'Intrinsic'] = 1
                components_and_emissions.loc[(index, 'Cost per Unit'), 'Intrinsic'] = conv_emissions
                components_and_emissions.loc[(index, 'Total Emissions'), 'Intrinsic'] = conv_emissions

                inputs = component_object.get_inputs()
                outputs = component_object.get_outputs()
                main_output_coefficient = outputs[main_output]
                processed_outputs = []
                for i in [*inputs.keys()]:
                    input_name = i

                    in_coeff = round(inputs[i] / main_output_coefficient, 3)
                    prod_emissions = round(production_cost_commodity_per_unit[i], 3)
                    input_emissions = round(production_cost_commodity_per_unit[i] * inputs[i]
                                        / main_output_coefficient, 3)

                    input_name += ' (Input)'

                    components_and_emissions.loc[(index, 'Coefficient'), input_name] = in_coeff
                    components_and_emissions.loc[(index, 'Cost per Unit'), input_name] = prod_emissions
                    components_and_emissions.loc[(index, 'Total Emissions'), input_name] = input_emissions

                    total_emissions += input_emissions

                    if i in [*outputs.keys()]:
                        # Handle output earlier s.t. its close to input of same commodity in excel file
                        output_name = i
                        output_object = pm_object.get_commodity(output_name)
                        out_coeff = round(outputs[i] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces emissions because the commodity needs to be disposed, for example -> positive

                        if output_object.get_selling_revenue() > 0:  # Case 3
                            prod_emissions = round(production_cost_commodity_per_unit[i], 3)
                            output_emissions = round(production_cost_commodity_per_unit[i] * outputs[i]
                                                 / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_emissions = - round(production_cost_commodity_per_unit[i], 3)
                            output_emissions = - round(production_cost_commodity_per_unit[i] * outputs[i]
                                                   / main_output_coefficient, 3)

                        output_name += ' (Output)'

                        components_and_emissions.loc[(index, 'Coefficient'), output_name] = out_coeff
                        components_and_emissions.loc[(index, 'Cost per Unit'), output_name] = prod_emissions
                        components_and_emissions.loc[(index, 'Total Emissions'), output_name] = output_emissions

                        total_emissions += output_emissions

                        processed_outputs.append(i)

                for o in [*outputs.keys()]:
                    if o in processed_outputs:
                        continue

                    output_name = o
                    output_object = pm_object.get_commodity(output_name)

                    if o != component_object.get_main_output():
                        out_coeff = round(outputs[o] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces emissions because the commodity needs to be disposed, for example -> positive

                        if output_object.get_selling_revenue() > 0:  # Case 3: Disposal emissions exist
                            prod_emissions = round(production_cost_commodity_per_unit[o], 3)
                            output_emissions = round(production_cost_commodity_per_unit[o] * outputs[o]
                                                 / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_emissions = - round(production_cost_commodity_per_unit[o], 3)
                            output_emissions = - round(production_cost_commodity_per_unit[o] * outputs[o]
                                                   / main_output_coefficient, 3)

                        output_name += ' (Output)'

                        components_and_emissions.loc[(index, 'Coefficient'), output_name] = out_coeff
                        components_and_emissions.loc[(index, 'Cost per Unit'), output_name] = prod_emissions
                        components_and_emissions.loc[(index, 'Total Emissions'), output_name] = output_emissions

                        total_emissions += output_emissions

                # Further emissions, which are not yet in commodity, need to be associated
                # In case that several components have same main output, emissions are matched regarding share of production
                component_object = pm_object.get_component(component_name)
                ratio = (component_object.get_specific_produced_commodity(commodity)
                         / main_output_object.get_produced_quantity())

                if main_output in pm_object.get_final_storage_components_names():
                    column_name = 'Storage Emissions'
                    components_and_emissions.loc[(index, 'Coefficient'), column_name] = ratio
                    prod_emissions = (main_output_object.get_total_co2_emissions_storage() / main_output_object.get_produced_quantity())
                    components_and_emissions.loc[(index, 'Cost per Unit'), column_name] = prod_emissions
                    components_and_emissions.loc[(index, 'Total Emissions'), column_name] = prod_emissions * ratio

                    total_emissions += prod_emissions * ratio

                if commodity_object.is_demanded():
                    for commodity in pm_object.get_final_commodities_names():
                        if (commodity not in all_inputs) & (commodity in main_outputs) & (commodity != main_output):

                            column_name = commodity + ' (Associated Emissions)'
                            components_and_emissions.loc[(index, 'Coefficient'), column_name] = ratio
                            prod_emissions = (production_cost_commodity_per_unit[commodity]
                                          * commodity_object.get_produced_quantity()
                                          / main_output_object.get_produced_quantity())
                            components_and_emissions.loc[(index, 'Cost per Unit'), column_name] = prod_emissions
                            components_and_emissions.loc[(index, 'Total Emissions'), column_name] = prod_emissions * ratio

                            total_emissions += prod_emissions * ratio

                prod_emissions = round(total_emissions, 3)
                components_and_emissions.loc[(index, 'Coefficient'), 'Final'] = ''
                components_and_emissions.loc[(index, 'Cost per Unit'), 'Final'] = ''
                components_and_emissions.loc[(index, 'Total Emissions'), 'Final'] = prod_emissions

                dataframe_dict[component_name] = components_and_emissions

            # Save dataframes in multi-sheet excel file
            if True:
                with pd.ExcelWriter(new_result_folder + '/main_output_emissions.xlsx', engine="xlsxwriter") as writer:
                    for df in [*dataframe_dict.keys()]:
                        sheet_name = df.replace("Parallel Unit", "PU")
                        dataframe_dict[df].to_excel(writer, sheet_name)
