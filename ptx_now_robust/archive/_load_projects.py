from object_component import ConversionComponent, StorageComponent, GenerationComponent
from object_commodity import Commodity


def load_project(pm_object, case_data):

    version = str(case_data['version'])
    if version == '0.0.9':
        pm_object = load_009(pm_object, case_data)
    elif version == '0.1.1':
        pm_object = load_011(pm_object, case_data)

    pm_object.check_commodity_data_needed()

    return pm_object


def load_011(pm_object, case_data):
    """ Set general parameters """

    pm_object.set_project_name(case_data['project_name'])
    pm_object.set_optimization_type(case_data['optimization_type'])

    pm_object.set_wacc(case_data['wacc'])

    pm_object.set_uses_representative_periods(case_data['representative_periods']['uses_representative_periods'])
    pm_object.set_covered_period(case_data['representative_periods']['covered_period'])

    pm_object.set_monetary_unit(case_data['monetary_unit'])

    """ Add generation data """
    pm_object.set_single_or_multiple_profiles(case_data['data']['single_or_multiple_profiles'])
    pm_object.set_profile_data(case_data['data']['profile_data'])

    """Allocate components and parameters"""
    for component in [*case_data['component'].keys()]:

        name = case_data['component'][component]['name']
        capex = case_data['component'][component]['capex']
        lifetime = case_data['component'][component]['lifetime']
        fixed_om = case_data['component'][component]['fixed_om']
        variable_om = case_data['component'][component]['variable_om']
        final_unit = case_data['component'][component]['final']
        has_fixed_capacity = case_data['component'][component]['has_fixed_capacity']
        fixed_capacity = case_data['component'][component]['fixed_capacity']
        installation_co2_emissions = case_data['component'][component]['installation_co2_emissions']
        fixed_co2_emissions = case_data['component'][component]['fixed_co2_emissions']
        variable_co2_emissions = case_data['component'][component]['variable_co2_emissions']
        disposal_co2_emissions = case_data['component'][component]['disposal_co2_emissions']

        if case_data['component'][component]['component_type'] == 'conversion':

            min_p = case_data['component'][component]['min_p']
            max_p = case_data['component'][component]['max_p']
            scalable = case_data['component'][component]['scalable']
            capex_basis = case_data['component'][component]['capex_basis']
            base_investment = case_data['component'][component]['base_investment']
            base_capacity = case_data['component'][component]['base_capacity']
            economies_of_scale = case_data['component'][component]['economies_of_scale']
            max_capacity_economies_of_scale = case_data['component'][component]['max_capacity_economies_of_scale']
            number_parallel_units = case_data['component'][component]['number_parallel_units']

            ramp_up = case_data['component'][component]['ramp_up']
            ramp_down = case_data['component'][component]['ramp_down']

            shut_down_ability = case_data['component'][component]['shut_down_ability']
            start_up_time = case_data['component'][component]['start_up_time']
            start_up_costs = case_data['component'][component]['start_up_costs']

            hot_standby_ability = case_data['component'][component]['hot_standby_ability']
            hot_standby_demand = {
                case_data['component'][component]['hot_standby_commodity']:
                case_data['component'][component]['hot_standby_demand']}
            hot_standby_startup_time = case_data['component'][component]['hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, lifetime=lifetime,
                                                       fixed_om=fixed_om, variable_om=variable_om,
                                                       base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time, start_up_costs=start_up_costs,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       has_fixed_capacity=has_fixed_capacity, fixed_capacity=fixed_capacity,
                                                       installation_co2_emissions=installation_co2_emissions,
                                                       fixed_co2_emissions=fixed_co2_emissions,
                                                       variable_co2_emissions=variable_co2_emissions,
                                                       disposal_co2_emissions=disposal_co2_emissions,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif case_data['component'][component]['component_type'] == 'storage':

            min_soc = case_data['component'][component]['min_soc']
            max_soc = case_data['component'][component]['max_soc']
            charging_efficiency = case_data['component'][component]['charging_efficiency']
            discharging_efficiency = case_data['component'][component]['discharging_efficiency']
            ratio_capacity_p = case_data['component'][component]['ratio_capacity_p']

            storage_component = StorageComponent(name=name, lifetime=lifetime,
                                                 fixed_om=fixed_om, variable_om=variable_om, capex=capex,
                                                 charging_efficiency=charging_efficiency,
                                                 discharging_efficiency=discharging_efficiency,
                                                 min_soc=min_soc, max_soc=max_soc, ratio_capacity_p=ratio_capacity_p,
                                                 has_fixed_capacity=has_fixed_capacity, fixed_capacity=fixed_capacity,
                                                 installation_co2_emissions=installation_co2_emissions,
                                                 fixed_co2_emissions=fixed_co2_emissions,
                                                 variable_co2_emissions=variable_co2_emissions,
                                                 disposal_co2_emissions=disposal_co2_emissions,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif case_data['component'][component]['component_type'] == 'generator':
            generated_commodity = case_data['component'][component]['generated_commodity']

            curtailment_possible = case_data['component'][component]['curtailment_possible']
            uses_ppa = case_data['component'][component]['uses_ppa']
            ppa_price = case_data['component'][component]['ppa_price']

            generator = GenerationComponent(name=name, lifetime=lifetime, fixed_om=fixed_om, variable_om=variable_om,
                                            capex=capex,
                                            generated_commodity=generated_commodity,
                                            curtailment_possible=curtailment_possible,
                                            has_fixed_capacity=has_fixed_capacity,
                                            fixed_capacity=fixed_capacity,
                                            uses_ppa=uses_ppa, ppa_price=ppa_price,
                                            installation_co2_emissions=installation_co2_emissions,
                                            fixed_co2_emissions=fixed_co2_emissions,
                                            variable_co2_emissions=variable_co2_emissions,
                                            disposal_co2_emissions=disposal_co2_emissions,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

    """ Conversions """
    for c in [*case_data['conversions'].keys()]:
        component = pm_object.get_component(c)
        for i in [*case_data['conversions'][c]['input'].keys()]:
            component.add_input(i, case_data['conversions'][c]['input'][i])

        for o in [*case_data['conversions'][c]['output'].keys()]:
            component.add_output(o, case_data['conversions'][c]['output'][o])

        component.set_main_input(case_data['conversions'][c]['main_input'])
        component.set_main_output(case_data['conversions'][c]['main_output'])

    """ Commodities """
    for c in [*case_data['commodity'].keys()]:
        name = case_data['commodity'][c]['name']
        commodity_unit = case_data['commodity'][c]['unit']

        available = case_data['commodity'][c]['available']
        emittable = case_data['commodity'][c]['emitted']
        purchasable = case_data['commodity'][c]['purchasable']
        saleable = case_data['commodity'][c]['saleable']
        demanded = case_data['commodity'][c]['demanded']
        total_demand = case_data['commodity'][c]['total_demand']
        final_commodity = case_data['commodity'][c]['final']

        # Purchasable commodities
        purchase_price_type = case_data['commodity'][c]['purchase_price_type']
        purchase_price = case_data['commodity'][c]['purchase_price']

        # Saleable commodities
        selling_price_type = case_data['commodity'][c]['selling_price_type']
        selling_price = case_data['commodity'][c]['selling_price']

        # Demand
        demand = case_data['commodity'][c]['demand']
        demand_type = case_data['commodity'][c]['demand_type']

        specific_co2_emissions_available = case_data['commodity'][c]['specific_co2_emissions_available']
        specific_co2_emissions_emitted = case_data['commodity'][c]['specific_co2_emissions_emitted']
        specific_co2_emissions_purchase = case_data['commodity'][c]['specific_co2_emissions_purchase']
        specific_co2_emissions_sale = case_data['commodity'][c]['specific_co2_emissions_sale']

        energy_content = case_data['commodity'][c]['energy_content']

        commodity = Commodity(name=name, commodity_unit=commodity_unit, energy_content=energy_content,
                              final_commodity=final_commodity,
                              available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                              demanded=demanded, total_demand=total_demand, demand_type=demand_type, demand=demand,
                              purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                              sale_price=selling_price, sale_price_type=selling_price_type,
                              specific_co2_emissions_available=specific_co2_emissions_available,
                              specific_co2_emissions_emitted=specific_co2_emissions_emitted,
                              specific_co2_emissions_purchase=specific_co2_emissions_purchase,
                              specific_co2_emissions_sale=specific_co2_emissions_sale
                              )
        pm_object.add_commodity(name, commodity)

    return pm_object


def load_009(pm_object, case_data):
    """ Set general parameters """

    pm_object.set_uses_representative_periods(case_data['representative_periods']['uses_representative_periods'])
    pm_object.set_covered_period(case_data['representative_periods']['covered_period'])

    pm_object.set_monetary_unit(case_data['monetary_unit'])

    """ Add generation data """
    pm_object.set_single_or_multiple_profiles(case_data['data']['single_or_multiple_profiles'])
    pm_object.set_profile_data(case_data['data']['profile_data'])

    """Allocate components and parameters"""
    for component in [*case_data['component'].keys()]:

        name = case_data['component'][component]['name']
        capex = case_data['component'][component]['capex']
        lifetime = case_data['component'][component]['lifetime']
        fixed_om = case_data['component'][component]['maintenance']
        final_unit = case_data['component'][component]['final']

        if case_data['component'][component]['component_type'] == 'conversion':

            min_p = case_data['component'][component]['min_p']
            max_p = case_data['component'][component]['max_p']
            scalable = case_data['component'][component]['scalable']
            capex_basis = case_data['component'][component]['capex_basis']
            base_investment = case_data['component'][component]['base_investment']
            base_capacity = case_data['component'][component]['base_capacity']
            economies_of_scale = case_data['component'][component]['economies_of_scale']
            max_capacity_economies_of_scale = case_data['component'][component]['max_capacity_economies_of_scale']
            number_parallel_units = case_data['component'][component]['number_parallel_units']

            ramp_up = case_data['component'][component]['ramp_up']
            ramp_down = case_data['component'][component]['ramp_down']

            shut_down_ability = case_data['component'][component]['shut_down_ability']
            start_up_time = case_data['component'][component]['start_up_time']
            start_up_costs = case_data['component'][component]['start_up_costs']

            hot_standby_ability = case_data['component'][component]['hot_standby_ability']
            hot_standby_demand = {
                case_data['component'][component]['hot_standby_commodity']:
                case_data['component'][component]['hot_standby_demand']}
            hot_standby_startup_time = case_data['component'][component]['hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, lifetime=lifetime,
                                                       fixed_om=fixed_om, variable_om=0,
                                                       base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time, start_up_costs=start_up_costs,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif case_data['component'][component]['component_type'] == 'storage':

            min_soc = case_data['component'][component]['min_soc']
            max_soc = case_data['component'][component]['max_soc']
            initial_soc = case_data['component'][component]['initial_soc']
            charging_efficiency = case_data['component'][component]['charging_efficiency']
            discharging_efficiency = case_data['component'][component]['discharging_efficiency']
            leakage = case_data['component'][component]['leakage']
            ratio_capacity_p = case_data['component'][component]['ratio_capacity_p']

            storage_component = StorageComponent(name=name, lifetime=lifetime, fixed_om=fixed_om, variable_om=0,
                                                 capex=capex, charging_efficiency=charging_efficiency,
                                                 discharging_efficiency=discharging_efficiency, min_soc=min_soc,
                                                 max_soc=max_soc, initial_soc=initial_soc, leakage=leakage,
                                                 ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif case_data['component'][component]['component_type'] == 'generator':
            generated_commodity = case_data['component'][component]['generated_commodity']

            curtailment_possible = case_data['component'][component]['curtailment_possible']

            has_fixed_capacity = case_data['component'][component]['has_fixed_capacity']
            fixed_capacity = case_data['component'][component]['fixed_capacity']

            generator = GenerationComponent(name=name, lifetime=lifetime, fixed_om=fixed_om, variable_om=0, capex=capex,
                                            generated_commodity=generated_commodity,
                                            curtailment_possible=curtailment_possible,
                                            has_fixed_capacity=has_fixed_capacity,
                                            fixed_capacity=fixed_capacity,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

    """ Conversions """
    for c in [*case_data['conversions'].keys()]:
        component = pm_object.get_component(c)
        for i in [*case_data['conversions'][c]['input'].keys()]:
            component.add_input(i, case_data['conversions'][c]['input'][i])

        for o in [*case_data['conversions'][c]['output'].keys()]:
            component.add_output(o, case_data['conversions'][c]['output'][o])

        component.set_main_input(case_data['conversions'][c]['main_input'])
        component.set_main_output(case_data['conversions'][c]['main_output'])

    """ Commodities """
    for c in [*case_data['commodity'].keys()]:
        name = case_data['commodity'][c]['name']
        commodity_unit = case_data['commodity'][c]['unit']

        available = case_data['commodity'][c]['available']
        emittable = case_data['commodity'][c]['emitted']
        purchasable = case_data['commodity'][c]['purchasable']
        saleable = case_data['commodity'][c]['saleable']
        demanded = case_data['commodity'][c]['demanded']
        total_demand = case_data['commodity'][c]['total_demand']
        final_commodity = case_data['commodity'][c]['final']

        # Purchasable commodities
        purchase_price_type = case_data['commodity'][c]['purchase_price_type']
        purchase_price = case_data['commodity'][c]['purchase_price']

        # Saleable commodities
        selling_price_type = case_data['commodity'][c]['selling_price_type']
        selling_price = case_data['commodity'][c]['selling_price']

        # Demand
        demand = case_data['commodity'][c]['demand']
        demand_type = case_data['commodity'][c]['demand_type']

        energy_content = case_data['commodity'][c]['energy_content']

        commodity = Commodity(name=name, commodity_unit=commodity_unit, energy_content=energy_content,
                        final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand, demand_type=demand_type, demand=demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type)
        pm_object.add_commodity(name, commodity)

    return pm_object
