import pandas as pd
import copy

from ptx_now_robust.helpers.object_commodity import Commodity
from ptx_now_robust.helpers.object_component import ConversionComponent

import numpy as np

from sklearn.linear_model import LinearRegression
from copy import deepcopy

import math

# from ptx_now_robust.archive.transfer_results_to_parameter_object import _transfer_results_to_parameter_object
# from ptx_now_robust.archive._create_result_files2 import _create_result_files

idx = pd.IndexSlice


class ParameterObject:

    def set_optimization_type(self, optimization_type):
        self.optimization_type = optimization_type

    def get_optimization_type(self):
        return self.optimization_type

    def set_wacc(self, wacc):
        self.wacc = float(wacc)

    def get_wacc(self):
        return self.wacc

    def get_annuity_factor(self):
        """ Setting time-dependent parameters"""

        # Calculate annuity factor of each component
        wacc = self.get_wacc()
        annuity_factor_dict = {}
        for c in self.get_final_components_objects():
            lifetime = c.get_lifetime()
            if lifetime != 0:
                anf_component = (1 + wacc) ** lifetime * wacc \
                                / ((1 + wacc) ** lifetime - 1)
                annuity_factor_dict.update({c.get_name(): anf_component})
            else:
                annuity_factor_dict.update({c.get_name(): 0})

        return annuity_factor_dict

    def add_component(self, name, component):
        self.components.update({name: component})

    def get_all_component_names(self):
        return [*self.components.keys()]

    def get_all_components(self):
        components = []
        for c in self.get_all_component_names():
            components.append(self.get_component(c))
        return components

    def get_component(self, name):
        return self.components[name]

    def remove_component_entirely(self, name):
        self.components.pop(name)

    def get_final_components_names(self):
        final_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).is_final():
                final_components_names.append(self.get_component(c).get_name())

        return final_components_names

    def get_final_components_objects(self):
        final_components = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).is_final():
                final_components.append(self.get_component(c))

        return final_components

    def get_conversion_components_names(self):
        conversion_components_names = []
        for c in self.get_all_component_names():
            if self.get_component(c).get_component_type() == 'conversion':
                conversion_components_names.append(self.get_component(c).get_name())

        return conversion_components_names

    def get_conversion_components_objects(self):
        conversion_components_objects = []
        for c in self.get_all_component_names():
            if self.get_component(c).get_component_type() == 'conversion':
                conversion_components_objects.append(self.get_component(c))

        return conversion_components_objects

    def get_storage_components_names(self):
        storage_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'storage':
                storage_components_names.append(self.get_component(c).get_name())

        return storage_components_names

    def get_storage_components_objects(self):
        storage_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'storage':
                storage_components_objects.append(self.get_component(c))

        return storage_components_objects

    def get_generator_components_names(self):
        generator_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'generator':
                generator_components_names.append(self.get_component(c).get_name())

        return generator_components_names

    def get_generator_components_objects(self):
        generator_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'generator':
                generator_components_objects.append(self.get_component(c))

        return generator_components_objects

    def get_final_conversion_components_names(self):
        final_components = self.get_final_components_names()
        conversion_components = self.get_conversion_components_names()

        final_components_as_set = set(final_components)
        final_conversion_components = final_components_as_set.intersection(conversion_components)
        final_conversion_components = list(final_conversion_components)

        return final_conversion_components

    def get_final_conversion_components_objects(self):

        final_conversion_components_objects = []
        for c in self.get_final_conversion_components_names():
            final_conversion_components_objects.append(self.get_component(c))

        return final_conversion_components_objects

    def get_final_scalable_conversion_components_names(self):
        final_scalable_conversion_components_names = []
        for c in self.get_final_conversion_components_objects():
            if c.is_scalable():
                final_scalable_conversion_components_names.append(c.get_name())

        return final_scalable_conversion_components_names

    def get_final_scalable_conversion_components_objects(self):
        final_scalable_conversion_components_objects = []
        for c in self.get_final_conversion_components_objects():
            if c.is_scalable():
                final_scalable_conversion_components_objects.append(c)

        return final_scalable_conversion_components_objects

    def get_final_shut_down_conversion_components_names(self):
        final_shutdown_conversion_components_names = []
        for c in self.get_final_conversion_components_objects():
            if c.get_shut_down_ability():
                final_shutdown_conversion_components_names.append(c.get_name())

        return final_shutdown_conversion_components_names

    def get_final_shut_down_conversion_components_objects(self):
        final_shutdown_conversion_components_objects = []
        for c in self.get_final_conversion_components_objects():
            if c.get_shut_down_ability():
                final_shutdown_conversion_components_objects.append(c)

        return final_shutdown_conversion_components_objects

    def get_final_standby_conversion_components_names(self):
        final_standby_conversion_components_names = []
        for c in self.get_final_conversion_components_objects():
            if c.get_hot_standby_ability():
                final_standby_conversion_components_names.append(c.get_name())

        return final_standby_conversion_components_names

    def get_final_standby_conversion_components_objects(self):
        final_standby_conversion_components_objects = []
        for c in self.get_final_conversion_components_objects():
            if c.get_hot_standby_ability():
                final_standby_conversion_components_objects.append(c)

        return final_standby_conversion_components_objects

    def get_final_storage_components_names(self):
        final_components = self.get_final_components_names()
        storage_components = self.get_storage_components_names()

        final_components_as_set = set(final_components)
        final_storage_components = final_components_as_set.intersection(storage_components)
        final_storage_components = list(final_storage_components)

        return final_storage_components

    def get_final_storage_components_objects(self):

        final_storage_components_objects = []
        for c in self.get_final_storage_components_names():
            final_storage_components_objects.append(self.get_component(c))

        return final_storage_components_objects

    def get_final_generator_components_names(self):
        final_components = self.get_final_components_names()
        generator_components = self.get_generator_components_names()

        generator_components_as_set = set(final_components)
        final_generator_components = generator_components_as_set.intersection(generator_components)
        final_generator_components = list(final_generator_components)

        return final_generator_components

    def get_final_generator_components_objects(self):

        final_generator_components_objects = []
        for c in self.get_final_generator_components_names():
            final_generator_components_objects.append(self.get_component(c))

        return final_generator_components_objects

    def get_final_commodities_names(self):
        final_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_final():
                final_commodities.append(self.get_commodity(commodity).get_name())

        return final_commodities

    def get_final_commodities_objects(self):
        final_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_final():
                final_commodities.append(self.get_commodity(commodity))

        return final_commodities

    def get_not_used_commodities_names(self):
        not_used_commodities = []
        for commodity in self.get_all_commodities():
            if not self.get_commodity(commodity).is_final():
                not_used_commodities.append(self.get_commodity(commodity).get_name())

        return not_used_commodities

    def get_not_used_commodities_objects(self):
        not_used_commodities = []
        for commodity in self.get_all_commodities():
            if not self.get_commodity(commodity).is_final():
                not_used_commodities.append(self.get_commodity(commodity))

        return not_used_commodities

    def get_custom_commodities_names(self):
        custom_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_custom():
                custom_commodities.append(self.get_commodity(commodity).get_name())

        return custom_commodities

    def get_custom_commodities_objects(self):
        custom_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_custom():
                custom_commodities.append(self.get_commodity(commodity))

        return custom_commodities

    def add_commodity(self, name, commodity):
        self.commodities.update({name: commodity})

    def remove_commodity_entirely(self, name):
        self.commodities.pop(name)

    def get_all_commodities(self):
        return self.commodities

    def get_all_commodity_names(self):  # checked
        all_commodities = []
        for s in [*self.get_all_commodities().keys()]:
            if s not in all_commodities:
                all_commodities.append(s)
        return all_commodities

    def get_commodity(self, name):  # checked
        return self.commodities[name]

    def get_commodity_by_component(self, component):  # checked
        return self.components[component].get_commodities()

    def get_component_by_commodity(self, commodity):  # checked
        components = []

        for c in self.components:
            if self.get_component(c).get_component_type() == 'conversion':
                if commodity in self.get_commodity_by_component(c):
                    components.append(c)

        return components

    def remove_commodity(self, commodity):
        self.get_commodity(commodity).set_final(False)

        for g in self.get_final_generator_components_objects():
            if commodity == g.get_generated_commodity():
                g.set_generated_commodity(self.get_final_commodities_names()[0])

    def activate_commodity(self, commodity):
        self.get_commodity(commodity).set_final(True)

    def adjust_commodity(self, name, commodity_object):
        components = self.get_component_by_commodity(name)
        for c in components:
            inputs = self.get_component(c).get_inputs()
            inputs[commodity_object.get_name()] = inputs.pop(name)
            self.get_component(c).set_inputs(inputs)

            if name == self.get_component(c).get_main_input():
                self.get_component(c).set_main_input(commodity_object.get_name())

            outputs = self.get_component(c).get_outputs()
            outputs[commodity_object.get_name()] = outputs.pop(name)
            self.get_component(c).set_outputs(outputs)

            if name == self.get_component(c).get_main_output():
                self.get_component(c).set_main_output(commodity_object.get_name())

        for g in self.get_final_generator_components_objects():
            if g.get_generated_commodity() == name:
                g.set_generated_commodity(commodity_object.get_name())

        for s in self.get_storage_components_objects():
            if s.get_name() == name:
                new_storage = deepcopy(s)
                new_storage.set_name(commodity_object.get_name())
                self.remove_component_entirely(name)
                self.add_component(commodity_object.get_name(), new_storage)

        self.add_commodity(commodity_object.get_name(), commodity_object)

    def set_integer_steps(self, integer_steps):
        self.integer_steps = integer_steps

    def get_integer_steps(self):
        return self.integer_steps

    def set_uses_representative_periods(self, uses_representative_periods):
        self.uses_representative_periods = bool(uses_representative_periods)

    def get_uses_representative_periods(self):
        return self.uses_representative_periods

    def get_number_clusters(self):

        if self.get_uses_representative_periods():

            path = self.get_path_data() + self.get_profile_data()
            if path.split('.')[-1] == 'xlsx':
                generation_profile = pd.read_excel(path, index_col=0)
            else:
                generation_profile = pd.read_csv(path, index_col=0)

            if self.get_uses_representative_periods():
                return int(len(generation_profile.index) / self.get_covered_period())
            else:
                return 1

        else:
            return 1

    def set_covered_period(self, covered_period):
        self.covered_period = int(covered_period)

    def get_covered_period(self):
        return self.covered_period

    def set_single_or_multiple_profiles(self, status):
        self.single_or_multiple_profiles = status

    def get_single_or_multiple_profiles(self):
        return self.single_or_multiple_profiles

    def set_profile_data(self, profile_data):
        self.profile_data = profile_data

    def get_profile_data(self):
        return self.profile_data

    def set_path_data(self, path_data):
        self.path_data = path_data

    def get_path_data(self):
        return self.path_data

    def check_commodity_data_needed(self):
        commodity_data_needed = False
        for s in self.get_all_commodities():
            if self.get_commodity(s).is_purchasable():
                if self.get_commodity(s).get_purchase_price_type() == 'variable':
                    commodity_data_needed = True
                    break

            elif self.get_commodity(s).is_saleable():
                if self.get_commodity(s).get_sale_price_type() == 'variable':
                    commodity_data_needed = True
                    break

            elif self.get_commodity(s).is_demanded():
                if self.get_commodity(s).get_demand_type() == 'variable':
                    commodity_data_needed = True
                    break

        self.commodity_data_needed = commodity_data_needed

    def get_commodity_data_needed(self):
        return self.commodity_data_needed

    def get_project_name(self):
        return self.project_name

    def set_project_name(self, project_name):
        self.project_name = project_name

    def set_monetary_unit(self, monetary_unit):
        self.monetary_unit = monetary_unit

    def get_monetary_unit(self):
        return self.monetary_unit

    def get_component_lifetime_parameters(self):
        lifetime_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()

            lifetime_dict[component_name] = component_object.get_lifetime()

        return lifetime_dict

    def get_component_fixed_om_parameters(self):
        fixed_om_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            fixed_om_dict[component_name] = component_object.get_fixed_OM()

        return fixed_om_dict

    def get_component_variable_om_parameters(self):
        variable_om = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            variable_om[component_name] = component_object.get_variable_OM()

        return variable_om

    def get_component_variable_capex_parameters(self):
        capex_var_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            capex_var_dict[component_name] = component_object.get_capex()

            if component_object.get_component_type() == 'conversion':

                if component_object.get_capex_basis() == 'output':
                    i = component_object.get_main_input()
                    i_coefficient = component_object.get_inputs()[i]
                    o = component_object.get_main_output()
                    o_coefficient = component_object.get_outputs()[o]
                    ratio = o_coefficient / i_coefficient
                else:
                    ratio = 1

                capex_var_dict[component_name] = capex_var_dict[component_name] * ratio

        return capex_var_dict

    def get_component_fixed_capex_parameters(self):
        capex_fix_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            capex_fix_dict[component_name] = 0

        return capex_fix_dict

    def get_scaling_component_variable_capex_parameters(self):
        capex_var_pre_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                capex_var_pre_dict.update(coefficient)

        return capex_var_pre_dict

    def get_scaling_component_fixed_capex_parameters(self):
        capex_fix_pre_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                capex_fix_pre_dict.update(intercept)

        return capex_fix_pre_dict

    def get_scaling_component_capex_upper_bound_parameters(self):
        upper_bound_dict = {}

        for component_object in self.get_final_conversion_components_objects():

            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                upper_bound_dict.update(upper_bound)

        return upper_bound_dict

    def get_scaling_component_capex_lower_bound_parameters(self):
        lower_bound_dict = {}

        for component_object in self.get_final_conversion_components_objects():

            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                lower_bound_dict.update(lower_bound)

        return lower_bound_dict

    def get_component_minimal_power_parameters(self):
        min_p_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            min_p_dict[component_name] = component_object.get_min_p()

        return min_p_dict

    def get_component_maximal_power_parameters(self):
        max_p_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            max_p_dict[component_name] = component_object.get_max_p()

        return max_p_dict

    def get_component_ramp_up_parameters(self):
        ramp_up_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            ramp_up_dict[component_name] = component_object.get_ramp_up()

        return ramp_up_dict

    def get_component_ramp_down_parameters(self):
        ramp_down_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            ramp_down_dict[component_name] = component_object.get_ramp_down()

        return ramp_down_dict

    def get_shut_down_component_down_time_parameters(self):
        down_time_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            if component_object.get_shut_down_ability():
                if int(component_object.get_start_up_time()) == 0:
                    # shut down time of 0 is not possible (division). Therefore, set it to 1
                    down_time_dict[component_name] = 1
                else:
                    down_time_dict[component_name] = int(component_object.get_start_up_time())

        return down_time_dict

    def get_shut_down_component_start_up_costs_parameters(self):
        start_up_costs_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()

            if component_object.get_capex_basis() == 'output':
                i = component_object.get_main_input()
                i_coefficient = component_object.get_inputs()[i]
                o = component_object.get_main_output()
                o_coefficient = component_object.get_outputs()[o]
                ratio = o_coefficient / i_coefficient
            else:
                ratio = 1

            if component_object.get_shut_down_ability():
                start_up_costs_dict[component_name] = component_object.get_start_up_costs() * ratio

        return start_up_costs_dict

    def get_standby_component_down_time_parameters(self):
        standby_time_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()

            if component_object.get_hot_standby_ability():
                if int(component_object.get_hot_standby_startup_time()) == 0:
                    # shut down time of 0 is not possible (division). Therefore, set it to 1
                    standby_time_dict[component_name] = 1
                else:
                    standby_time_dict[component_name] = int(component_object.get_hot_standby_startup_time())

        return standby_time_dict

    def get_storage_component_charging_efficiency(self):

        charging_efficiency_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            charging_efficiency_dict[component_name] = component_object.get_charging_efficiency()

        return charging_efficiency_dict

    def get_storage_component_discharging_efficiency(self):

        discharging_efficiency_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            discharging_efficiency_dict[component_name] = component_object.get_discharging_efficiency()

        return discharging_efficiency_dict

    def get_storage_component_minimal_soc(self):

        min_soc_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            min_soc_dict[component_name] = component_object.get_min_soc()

        return min_soc_dict

    def get_storage_component_maximal_soc(self):

        max_soc_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            max_soc_dict[component_name] = component_object.get_max_soc()

        return max_soc_dict

    def get_storage_component_ratio_capacity_power(self):

        ratio_capacity_power_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            ratio_capacity_power_dict[component_name] = component_object.get_ratio_capacity_p()

        return ratio_capacity_power_dict

    def get_fixed_capacities(self):
        fixed_capacities_dict = {}
        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            fixed_capacities_dict[component_name] = component_object.get_fixed_capacity()

        return fixed_capacities_dict

    def get_co2_emission_data(self):
        specific_co2_emissions_per_capacity = {}
        fixed_yearly_co2_emissions = {}
        variable_co2_emissions = {}
        disposal_co2_emissions = {}
        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()

            # in case of capex we need to consider the capex basis
            if component_object.get_component_type() == 'conversion':
                if component_object.get_capex_basis() == 'output':
                    i = component_object.get_main_input()
                    i_coefficient = component_object.get_inputs()[i]
                    o = component_object.get_main_output()
                    o_coefficient = component_object.get_outputs()[o]
                    ratio = o_coefficient / i_coefficient
                else:
                    ratio = 1

                specific_co2_emissions_per_capacity[component_name] = component_object.get_installation_co2_emissions() * ratio
                disposal_co2_emissions[component_name] = component_object.get_disposal_co2_emissions() * ratio
            else:
                specific_co2_emissions_per_capacity[component_name] = component_object.get_installation_co2_emissions()
                disposal_co2_emissions[component_name] = component_object.get_disposal_co2_emissions()

            fixed_yearly_co2_emissions[component_name] = component_object.get_fixed_co2_emissions()
            variable_co2_emissions[component_name] = component_object.get_variable_co2_emissions()

        return specific_co2_emissions_per_capacity, fixed_yearly_co2_emissions,\
            variable_co2_emissions, disposal_co2_emissions

    def calculate_economies_of_scale_steps(self, component_object):

        component_name = component_object.get_name()

        base_capacity = component_object.get_base_capacity()
        economies_of_scale = component_object.get_economies_of_scale()
        max_capacity_economies_of_scale = component_object.get_max_capacity_economies_of_scale()
        base_investment = component_object.get_base_investment()

        if component_object.get_capex_basis() == 'output':
            # If the investment is based on the output, the investment curve has to be transformed

            i = component_object.get_main_input()
            i_coefficient = component_object.get_inputs()[i]
            o = component_object.get_main_output()
            o_coefficient = component_object.get_outputs()[o]
            ratio = o_coefficient / i_coefficient

            base_capacity = base_capacity / ratio
            max_capacity_economies_of_scale = max_capacity_economies_of_scale / ratio

        # First, calculate the investment curve based on the economies of scale

        # If max_capacity is higher than calculating every step would increase calculation time
        # Therefore, the approach uses 1000 capacities to calculate the investment

        integer_steps = self.get_integer_steps()

        max_invest = base_investment * (max_capacity_economies_of_scale / base_capacity) ** economies_of_scale
        delta_investment_per_step = max_invest / (integer_steps - 1)

        lower_bound = {(component_name, 0): 0}
        upper_bound = {(component_name, 0): 0}
        coefficient = {(component_name, 0): 0}
        intercept = {(component_name, 0): 0}

        # Find capacities at beginning/end of steps
        capacity_scaling_factor = 1
        if base_capacity <= 100:
            capacity_scaling_factor = 10

        capacities = {}
        investments = {}
        for i in range(integer_steps):
            investment = i * delta_investment_per_step
            investments[i] = investment
            capacity = (investment / base_investment) ** (1 / economies_of_scale) * base_capacity

            capacities[i] = capacity * capacity_scaling_factor

        for i in range(integer_steps):
            if i == integer_steps - 1:
                continue

            upper_bound[(component_name, i + 1)] = capacities[i + 1] / capacity_scaling_factor
            lower_bound[(component_name, i + 1)] = capacities[i] / capacity_scaling_factor

            y_value = np.zeros([len(range(int(capacities[i]), int(capacities[i + 1])))])
            x_value = np.zeros([len(range(int(capacities[i]), int(capacities[i + 1])))]).reshape((-1, 1))

            k = 0
            for j in range(int(capacities[i]), int(capacities[i + 1])):
                x_value[k] = j / capacity_scaling_factor
                if x_value[k] != 0:
                    y_value[k] = base_investment * (j / capacity_scaling_factor / base_capacity) ** economies_of_scale
                else:
                    y_value[k] = 0
                k += 1

            model = LinearRegression().fit(x_value, y_value)
            coefficient[(component_name, i + 1)] = model.coef_[0]
            intercept[(component_name, i + 1)] = model.intercept_

        # Calculate coefficient, intercept, lower bound and upper bound for step without upper bound
        investment = integer_steps * delta_investment_per_step
        capacity = (investment / base_investment) ** (1 / economies_of_scale) * base_capacity
        upper_bound[(component_name, integer_steps)] = math.inf
        lower_bound[(component_name, integer_steps)] = capacities[integer_steps - 1] / capacity_scaling_factor

        y_value = np.zeros([len(range(int(capacities[integer_steps - 1]), int(capacity)))])
        x_value = np.zeros([len(range(int(capacities[integer_steps - 1]), int(capacity)))]).reshape((-1, 1))
        k = 0
        for j in range(int(capacities[integer_steps - 1]), int(capacity)):
            x_value[k] = j / capacity_scaling_factor
            if x_value[k] != 0:
                y_value[k] = base_investment * (j / capacity_scaling_factor / base_capacity) ** economies_of_scale
            else:
                y_value[k] = 0
            k += 1

            model = LinearRegression().fit(x_value, y_value)
            coefficient[(component_name, integer_steps)] = model.coef_[0]
            intercept[(component_name, integer_steps)] = model.intercept_

        return lower_bound, upper_bound, coefficient, intercept

    def get_all_technical_component_parameters(self):

        lifetime_dict = self.get_component_lifetime_parameters()
        fixed_om_dict = self.get_component_fixed_om_parameters()
        variable_om_dict = self.get_component_variable_om_parameters()
        capex_var_dict = self.get_component_variable_capex_parameters()
        capex_fix_dict = self.get_component_fixed_capex_parameters()

        minimal_power_dict = self.get_component_minimal_power_parameters()
        maximal_power_dict = self.get_component_maximal_power_parameters()
        ramp_up_dict = self.get_component_ramp_up_parameters()
        ramp_down_dict = self.get_component_ramp_down_parameters()

        scaling_capex_var_dict = self.get_scaling_component_variable_capex_parameters()
        scaling_capex_fix_dict = self.get_scaling_component_fixed_capex_parameters()
        scaling_capex_upper_bound_dict = self.get_scaling_component_capex_upper_bound_parameters()
        scaling_capex_lower_bound_dict = self.get_scaling_component_capex_lower_bound_parameters()

        shut_down_down_time_dict = self.get_shut_down_component_down_time_parameters()
        shut_down_start_up_costs = self.get_shut_down_component_start_up_costs_parameters()

        standby_down_time_dict = self.get_standby_component_down_time_parameters()

        charging_efficiency_dict = self.get_storage_component_charging_efficiency()
        discharging_efficiency_dict = self.get_storage_component_discharging_efficiency()

        minimal_soc_dict = self.get_storage_component_minimal_soc()
        maximal_soc_dict = self.get_storage_component_maximal_soc()

        ratio_capacity_power_dict = self.get_storage_component_ratio_capacity_power()

        fixed_capacity_dict = self.get_fixed_capacities()

        return lifetime_dict, fixed_om_dict, variable_om_dict, capex_var_dict, capex_fix_dict, minimal_power_dict, maximal_power_dict,\
            ramp_up_dict, ramp_down_dict, scaling_capex_var_dict, scaling_capex_fix_dict,\
            scaling_capex_upper_bound_dict, scaling_capex_lower_bound_dict,\
            shut_down_down_time_dict, shut_down_start_up_costs, standby_down_time_dict,\
            charging_efficiency_dict, discharging_efficiency_dict, minimal_soc_dict, maximal_soc_dict, \
            ratio_capacity_power_dict, fixed_capacity_dict

    def get_all_financial_component_parameters(self):

        fixed_om_dict = self.get_component_fixed_om_parameters()
        variable_om_dict = self.get_component_variable_om_parameters()
        capex_var_dict = self.get_component_variable_capex_parameters()
        capex_fix_dict = self.get_component_fixed_capex_parameters()

        return fixed_om_dict, variable_om_dict, capex_var_dict, capex_fix_dict

    def get_conversion_component_sub_sets(self):

        scalable_components = []
        not_scalable_components = []

        shut_down_components = []
        no_shut_down_components = []

        standby_components = []
        no_standby_components = []

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()

            if component_object.get_component_type() == 'conversion':

                if not component_object.is_scalable():
                    not_scalable_components.append(component_name)
                else:
                    scalable_components.append(component_name)

                if component_object.get_shut_down_ability():
                    shut_down_components.append(component_name)
                else:
                    no_shut_down_components.append(component_name)

                if component_object.get_hot_standby_ability():
                    standby_components.append(component_name)
                else:
                    no_standby_components.append(component_name)

        return scalable_components, not_scalable_components, shut_down_components, no_shut_down_components,\
            standby_components, no_standby_components

    def get_commodity_sets(self):
        final_commodities = []
        available_commodities = []
        emittable_commodities = []
        purchasable_commodities = []
        saleable_commodities = []
        demanded_commodities = []
        total_demand_commodities = []

        for commodity in self.get_final_commodities_objects():

            commodity_name = commodity.get_name()

            final_commodities.append(commodity_name)

            if commodity.is_available():
                available_commodities.append(commodity_name)
            if commodity.is_emittable():
                emittable_commodities.append(commodity_name)
            if commodity.is_purchasable():
                purchasable_commodities.append(commodity_name)
            if commodity.is_saleable():
                saleable_commodities.append(commodity_name)
            if commodity.is_demanded():
                demanded_commodities.append(commodity_name)
                if commodity.is_total_demand():
                    total_demand_commodities.append(commodity_name)

        generated_commodities = []
        for generator in self.get_final_generator_components_objects():
            if generator.get_generated_commodity() not in generated_commodities:
                generated_commodities.append(generator.get_generated_commodity())

        all_inputs = []
        all_outputs = []
        for component in self.get_final_conversion_components_objects():
            inputs = component.get_inputs()
            outputs = component.get_outputs()

            for i in inputs:
                if i not in all_inputs:
                    all_inputs.append(i)

            for o in outputs:
                if o not in all_outputs:
                    all_outputs.append(o)

        return final_commodities, available_commodities, emittable_commodities, purchasable_commodities, \
            saleable_commodities, demanded_commodities, total_demand_commodities, generated_commodities, \
            all_inputs, all_outputs

    def get_main_input_to_input_conversions(self):
        # main input to other inputs

        input_tuples = []
        main_input_to_input_conversion_tuples = []
        main_input_to_input_conversion_tuples_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            inputs = component_object.get_inputs()
            main_input = component_object.get_main_input()

            for current_input in [*inputs.keys()]:
                input_tuples.append((component_name, current_input))
                if current_input != main_input:
                    main_input_to_input_conversion_tuples.append((component_name, main_input, current_input))
                    main_input_to_input_conversion_tuples_dict.update(
                        {(component_name, main_input, current_input): float(inputs[current_input]) / float(inputs[main_input])})

        return input_tuples, main_input_to_input_conversion_tuples, main_input_to_input_conversion_tuples_dict

    def get_main_input_to_output_conversions(self):
        output_tuples = []
        main_input_to_output_conversion_tuples = []
        main_input_to_output_conversion_tuples_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            inputs = component_object.get_inputs()
            outputs = component_object.get_outputs()

            main_input = component_object.get_main_input()
            for current_output in [*outputs.keys()]:
                main_input_to_output_conversion_tuples.append((component_name, main_input, current_output))
                main_input_to_output_conversion_tuples_dict.update(
                    {(component_name, main_input, current_output): float(outputs[current_output]) / float(inputs[main_input])})

                output_tuples.append((component_name, current_output))

        return output_tuples, main_input_to_output_conversion_tuples, main_input_to_output_conversion_tuples_dict

    def get_all_conversions(self):

        input_tuples, main_input_to_input_conversion_tuples, main_input_to_input_conversion_tuples_dict\
            = self.get_main_input_to_input_conversions()
        output_tuples, input_to_output_conversion_tuples, input_to_output_conversion_tuples_dict\
            = self.get_main_input_to_output_conversions()

        return input_tuples, main_input_to_input_conversion_tuples, main_input_to_input_conversion_tuples_dict,\
            output_tuples, input_to_output_conversion_tuples, input_to_output_conversion_tuples_dict

    def get_generation_time_series(self):
        generation_profiles_dict = {}

        if len(self.get_final_generator_components_objects()) > 0:

            path = self.get_path_data() + self.get_profile_data()
            if path.split('.')[-1] == 'xlsx':
                profile = pd.read_excel(path, index_col=0)

            else:
                profile = pd.read_csv(path, index_col=0)

            for generator in self.get_final_generator_components_objects():
                generator_name = generator.get_name()
                ind = 0
                for cl in range(self.get_number_clusters()):
                    for t in range(self.get_covered_period()):
                        generation_profiles_dict.update({(generator_name, cl, t):
                                                         float(profile.loc[profile.index[ind], generator.get_name()])})
                        ind += 1

        return generation_profiles_dict

    def get_demand_time_series(self):
        hourly_demand_dict = {}
        total_demand_dict = {}

        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()

            if commodity.is_demanded():
                if commodity.get_demand_type() == 'fixed':
                    if not commodity.is_total_demand():
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                hourly_demand_dict.update({(commodity_name, cl, t): float(commodity.get_demand())})
                    else:
                        total_demand_dict.update({commodity_name: float(commodity.get_demand())})

                else:

                    path = self.get_path_data() + self.get_profile_data()

                    if path.split('.')[-1] == 'xlsx':
                        profile = pd.read_excel(path, index_col=0)

                    else:
                        profile = pd.read_csv(path, index_col=0)

                    demand_curve = profile.loc[:, commodity_name + '_Demand']

                    ind = 0
                    for cl in range(self.get_number_clusters()):
                        for t in range(self.get_covered_period()):
                            hourly_demand_dict.update({(commodity_name, cl, t): float(demand_curve.loc[demand_curve.index[ind]])})

                            ind += 1

        return hourly_demand_dict, total_demand_dict

    def get_purchase_price_time_series(self):
        purchase_price_dict = {}

        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            if commodity.is_purchasable():
                if commodity.get_purchase_price_type() == 'fixed':
                    for cl in range(self.get_number_clusters()):
                        for t in range(self.get_covered_period()):
                            purchase_price_dict.update({(commodity_name, cl, t): float(commodity.get_purchase_price())})

                else:

                    path = self.get_path_data() + self.get_profile_data()

                    if path.split('.')[-1] == 'xlsx':
                        profile = pd.read_excel(path, index_col=0)

                    else:
                        profile = pd.read_csv(path, index_col=0)

                    if commodity_name + '_Purchase_Price' in profile.columns:
                        purchase_price_curve = profile.loc[:, commodity_name + '_Purchase_Price']

                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                purchase_price_dict.update({(commodity_name, cl, t): float(purchase_price_curve.loc[purchase_price_curve.index[ind]])})
                                ind += 1
                    else:
                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                purchase_price_dict.update({(commodity_name, cl, t): 0})
                                ind += 1

        return purchase_price_dict

    def get_purchase_specific_co2_emissions_time_series(self):
        purchase_specific_co2_emissions_dict = {}

        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            if commodity.is_purchasable():
                if commodity.get_purchase_price_type() == 'fixed':
                    for cl in range(self.get_number_clusters()):
                        for t in range(self.get_covered_period()):
                            purchase_specific_co2_emissions_dict.update({(commodity_name, cl, t): float(commodity.get_specific_co2_emissions_purchase())})

                else:
                    path = self.get_path_data() + self.get_profile_data()

                    if path.split('.')[-1] == 'xlsx':
                        profile = pd.read_excel(path, index_col=0)

                    else:
                        profile = pd.read_csv(path, index_col=0)

                    if commodity_name + '_Purchase_Specific_CO2_Emissions' in profile.columns:

                        purchase_specific_co2_emissions_curve = profile.loc[:, commodity_name + '_Purchase_Specific_CO2_Emissions']

                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                purchase_specific_co2_emissions_dict.update({(commodity_name, cl, t): float(purchase_specific_co2_emissions_curve.loc[purchase_specific_co2_emissions_curve.index[ind]])})
                                ind += 1

                    else:
                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                purchase_specific_co2_emissions_dict.update({(commodity_name, cl, t): 0})
                                ind += 1

        return purchase_specific_co2_emissions_dict

    def get_sale_price_time_series(self):
        sell_price_dict = {}
        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            if commodity.is_saleable():
                if commodity.get_sale_price_type() == 'fixed':
                    for cl in range(self.get_number_clusters()):
                        for t in range(self.get_covered_period()):
                            sell_price_dict.update({(commodity_name, cl, t): float(commodity.get_sale_price())})
                else:

                    path = self.get_path_data() + self.get_profile_data()

                    if path.split('.')[-1] == 'xlsx':
                        profile = pd.read_excel(path, index_col=0)

                    else:
                        profile = pd.read_csv(path, index_col=0)

                    if commodity_name + '_Selling_Price' in profile.columns:

                        sale_price_curve = profile.loc[:, commodity_name + '_Selling_Price']

                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                sell_price_dict.update({(commodity_name, cl, t): float(sale_price_curve.loc[sale_price_curve.index[ind]])})
                                ind += 1

                    else:
                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                sell_price_dict.update({(commodity_name, cl, t): 0})
                                ind += 1

        return sell_price_dict

    def get_sale_specific_co2_emissions_time_series(self):
        sale_specific_co2_emissions_dict = {}
        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            if commodity.is_saleable():
                if commodity.get_sale_price_type() == 'fixed':
                    for cl in range(self.get_number_clusters()):
                        for t in range(self.get_covered_period()):
                            sale_specific_co2_emissions_dict.update({(commodity_name, cl, t): float(commodity.get_specific_co2_emissions_sale())})
                else:

                    path = self.get_path_data() + self.get_profile_data()

                    if path.split('.')[-1] == 'xlsx':
                        profile = pd.read_excel(path, index_col=0)

                    else:
                        profile = pd.read_csv(path, index_col=0)

                    if commodity_name + '_Selling_Specific_CO2_Emissions' in profile.columns:
                        # If this would be necessary, it would have been caught already when checking the optimizaton problem

                        sale_specific_co2_emissions_curve = profile.loc[:, commodity_name + '_Selling_Specific_CO2_Emissions']

                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                sale_specific_co2_emissions_dict.update({(commodity_name, cl, t): float(sale_specific_co2_emissions_curve.loc[sale_specific_co2_emissions_curve.index[ind]])})
                                ind += 1

                    else:
                        ind = 0
                        for cl in range(self.get_number_clusters()):
                            for t in range(self.get_covered_period()):
                                sale_specific_co2_emissions_dict.update({(commodity_name, cl, t): 0})
                                ind += 1

        return sale_specific_co2_emissions_dict

    def get_available_specific_co2_emissions_time_series(self):
        available_specific_co2_emissions_dict = {}
        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            if commodity.is_available():
                for cl in range(self.get_number_clusters()):
                    for t in range(self.get_covered_period()):
                        available_specific_co2_emissions_dict.update({(commodity_name, cl, t): float(commodity.get_specific_co2_emissions_available())})

        return available_specific_co2_emissions_dict

    def get_emitted_specific_co2_emissions_time_series(self):
        emitted_specific_co2_emissions_dict = {}
        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            if commodity.is_emittable():
                for cl in range(self.get_number_clusters()):
                    for t in range(self.get_covered_period()):
                        emitted_specific_co2_emissions_dict.update({(commodity_name, cl, t): float(commodity.get_specific_co2_emissions_emitted())})

        return emitted_specific_co2_emissions_dict

    def get_weightings_time_series(self):
        weightings_dict = {}
        if self.get_uses_representative_periods():

            path = self.get_path_data() + self.get_profile_data()

            if path.split('.')[-1] == 'xlsx':
                weightings = pd.read_excel(path, index_col=0)
            else:
                weightings = pd.read_csv(path, index_col=0)

            j = 0
            for i in weightings.index:
                cl = math.floor(j / self.get_covered_period())
                weightings_dict[cl] = weightings.at[i, 'Weighting']
                j += 1
        else:
            weightings_dict[0] = 1

        return weightings_dict

    def create_new_project(self):
        """ Create new project """

        # Set general parameters
        self.set_wacc(0.07)

        c = 'dummy'
        conversion_component = ConversionComponent(name=c, final_unit=True)
        self.add_component(c, conversion_component)

        input_commodity = 'Electricity'
        output_commodity = 'Electricity'

        self.get_component(c).add_input(input_commodity, 1)
        self.get_component(c).add_output(output_commodity, 1)

        self.get_component(c).set_main_input(input_commodity)
        self.get_component(c).set_main_output(output_commodity)

        s = Commodity('Electricity', 'MWh', final_commodity=True)
        self.add_commodity('Electricity', s)

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

    def set_operation_time_series(self, operation_time_series):
        self.operation_time_series = operation_time_series

    def get_operation_time_series(self):
        return self.operation_time_series

    # def process_results(self, path_results, model_type, create_results=True):
    #
    #     _transfer_results_to_parameter_object(self, model_type)
    #
    #     if create_results:
    #         _create_result_files(self, path_results)

    def set_objective_function_value(self, objective_function_value):
        self.objective_function_value = objective_function_value

    def get_objective_function_value(self):
        return self.objective_function_value

    def __copy__(self):

        # deepcopy mutable objects
        names_dict = copy.deepcopy(self.names_dict)
        components = copy.deepcopy(self.components)
        commodities = copy.deepcopy(self.commodities)
        instance = copy.deepcopy(self.instance)
        operation_time_series = copy.deepcopy(self.operation_time_series)

        return ParameterObject(project_name=self.project_name,
                               integer_steps=self.integer_steps, wacc=self.wacc,
                               names_dict=names_dict,
                               commodities=commodities,
                               components=components, profile_data=self.profile_data,
                               single_or_multiple_profiles=self.single_or_multiple_profiles,
                               uses_representative_periods=self.uses_representative_periods,
                               representative_periods_length=self.representative_periods_length,
                               covered_period=self.covered_period,
                               monetary_unit=self.monetary_unit, optimization_type=self.optimization_type,
                               instance=instance,
                               operation_time_series=operation_time_series,
                               copy_object=True)

    def __init__(self, project_name='', integer_steps=5,
                 wacc=0.07, names_dict=None, commodities=None, components=None,
                 profile_data=False, single_or_multiple_profiles='single',
                 uses_representative_periods=False, representative_periods_length=0,
                 covered_period=8760, monetary_unit='€', path_data=None, optimization_type='economical',
                 instance=None, operation_time_series=None,
                 copy_object=False):

        """
        Object, which stores all components, commodities, settings etc.
        :param project_name: [string] - name of parameter object
        :param integer_steps: [int] - number of integer steps (used to split capacity)
        :param wacc: [float] - Weighted Average Cost of Capital
        :param names_dict: [dict] - List of abbreviations of components, commodities etc.
        :param commodities: [dict] - Dictionary with abbreviations as keys and commodity objects as values
        :param components: [dict] - Dictionary with abbreviations as keys and component objects as values
        :param copy_object: [boolean] - Boolean if object is copy
        """
        self.project_name = project_name

        self.optimization_type = optimization_type

        if not copy_object:

            # Initiate as default values
            self.wacc = wacc

            self.names_dict = {}

            self.commodities = {}
            self.components = {}

        else:
            # Object is copied if components have parallel units.
            # It is copied so that the original pm_object is not changed
            self.names_dict = names_dict

            self.commodities = commodities
            self.components = components

        self.covered_period = covered_period
        self.uses_representative_periods = uses_representative_periods
        self.representative_periods_length = representative_periods_length
        self.integer_steps = integer_steps
        self.monetary_unit = str(monetary_unit)

        self.single_or_multiple_profiles = single_or_multiple_profiles
        self.profile_data = profile_data
        self.path_data = path_data

        self.commodity_data_needed = False
        self.check_commodity_data_needed()

        self.instance = instance
        self.operation_time_series = operation_time_series

        self.objective_function_value = None


ParameterObjectCopy = type('CopyOfB', ParameterObject.__bases__, dict(ParameterObject.__dict__))
