from pyomo.core import *
from pyomo.core import Binary
import pyomo.environ as pyo

from ptx_now._helper_optimization import anticipate_bigM


class OptimizationPyomoModel:

    def attach_sets(self):

        def attach_component_sets_to_optimization_problem():
            self.model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
            self.model.STORAGES = Set(initialize=self.storage_components)
            self.model.GENERATORS = Set(initialize=self.generator_components)
            self.model.COMPONENTS = Set(initialize=self.all_components)

        attach_component_sets_to_optimization_problem()

        def attach_scalable_component_sets_to_optimization_problem():
            self.model.SCALABLE_COMPONENTS = Set(initialize=self.scalable_components)

        attach_scalable_component_sets_to_optimization_problem()

        def attach_shut_down_component_sets_to_optimization_problem():
            self.model.SHUT_DOWN_COMPONENTS = Set(initialize=self.shut_down_components)

        attach_shut_down_component_sets_to_optimization_problem()

        def attach_standby_component_sets_to_optimization_problem():
            self.model.STANDBY_COMPONENTS = Set(initialize=self.standby_components)

        attach_standby_component_sets_to_optimization_problem()

        def attach_commodity_sets_to_optimization_problem():
            self.model.COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
            self.model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
            self.model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
            self.model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
            self.model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
            self.model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
            self.model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
            self.model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)
            self.model.INPUT_COMMODITIES = Set(initialize=self.all_inputs)
            self.model.OUTPUT_COMMODITIES = Set(initialize=self.all_outputs)

        attach_commodity_sets_to_optimization_problem()

    def attach_technical_parameters(self):

        def attach_component_parameters_to_optimization_problem():
            self.model.min_p = Param(self.model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
            self.model.max_p = Param(self.model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)

            self.model.ramp_up = Param(self.model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
            self.model.ramp_down = Param(self.model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

            self.model.charging_efficiency = Param(self.model.STORAGES, initialize=self.charging_efficiency_dict)
            self.model.discharging_efficiency = Param(self.model.STORAGES, initialize=self.discharging_efficiency_dict)

            self.model.minimal_soc = Param(self.model.STORAGES, initialize=self.minimal_soc_dict)
            self.model.maximal_soc = Param(self.model.STORAGES, initialize=self.maximal_soc_dict)

            self.model.ratio_capacity_p = Param(self.model.STORAGES, initialize=self.ratio_capacity_power_dict)

            self.model.fixed_capacity = Param(self.model.COMPONENTS, initialize=self.fixed_capacity_dict)

        attach_component_parameters_to_optimization_problem()

        def attach_shut_down_component_parameters_to_optimization_problem():
            self.model.down_time = Param(self.model.SHUT_DOWN_COMPONENTS, initialize=self.shut_down_down_time_dict)

        attach_shut_down_component_parameters_to_optimization_problem()

        def attach_standby_component_parameters_to_optimization_problem():
            self.model.standby_time = Param(self.model.STANDBY_COMPONENTS, initialize=self.standby_down_time_dict)

        attach_standby_component_parameters_to_optimization_problem()

        def attach_demand_time_series_to_optimization_problem():
            self.model.hourly_commodity_demand = Param(self.model.DEMANDED_COMMODITIES, self.model.CLUSTERS,
                                                       self.model.TIME,
                                                       initialize=self.hourly_demand_dict)
            self.model.total_commodity_demand = Param(self.model.TOTAL_DEMANDED_COMMODITIES,
                                                      initialize=self.total_demand_dict)

        attach_demand_time_series_to_optimization_problem()

        def attach_generation_time_series_to_optimization_problem():
            self.model.generation_profiles = Param(self.model.GENERATORS, self.model.CLUSTERS, self.model.TIME,
                                                   initialize=self.generation_profiles_dict)

        attach_generation_time_series_to_optimization_problem()

        def attach_weightings_time_series_to_optimization_problem():
            self.model.weightings = Param(self.model.CLUSTERS, initialize=self.weightings_dict)

        attach_weightings_time_series_to_optimization_problem()

    def attach_technical_variables(self):

        def attach_component_variables_to_optimization_problem():
            # Component variables
            self.model.nominal_cap = Var(self.model.COMPONENTS, bounds=(0, None))

            self.model.status_on = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME,
                                       within=Binary)
            self.model.status_off = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME,
                                        within=Binary)
            self.model.status_off_switch_on = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                  self.model.TIME, within=Binary)
            self.model.status_off_switch_off = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                   self.model.TIME, within=Binary)
            self.model.status_standby_switch_on = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                      self.model.TIME, within=Binary)
            self.model.status_standby_switch_off = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                       self.model.TIME,
                                                       within=Binary)
            self.model.status_standby = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME,
                                            within=Binary)

            # STORAGE binaries (charging and discharging)
            self.model.storage_charge_binary = Var(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                                   within=Binary)
            self.model.storage_discharge_binary = Var(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                                      within=Binary)

        attach_component_variables_to_optimization_problem()

        def attach_scalable_component_variables_to_optimization_problem():
            def set_scalable_component_capacity_bound_rule(model, s, i):
                return 0, self.scaling_capex_upper_bound_dict[(s, i)]

            self.model.nominal_cap_pre = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                             bounds=set_scalable_component_capacity_bound_rule)
            self.model.capacity_binary = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS, within=Binary)

        attach_scalable_component_variables_to_optimization_problem()

        def attach_commodity_variables_to_optimization_problem():
            self.model.mass_energy_component_in_commodities = Var(self.model.CONVERSION_COMPONENTS,
                                                                  self.model.INPUT_COMMODITIES,
                                                                  self.model.CLUSTERS, self.model.TIME,
                                                                  bounds=(0, None))
            self.model.mass_energy_component_out_commodities = Var(self.model.CONVERSION_COMPONENTS,
                                                                   self.model.OUTPUT_COMMODITIES,
                                                                   self.model.CLUSTERS, self.model.TIME,
                                                                   bounds=(0, None))

            # Freely available commodities
            self.model.mass_energy_available = Var(self.model.AVAILABLE_COMMODITIES, self.model.CLUSTERS,
                                                   self.model.TIME, bounds=(0, None))
            self.model.mass_energy_emitted = Var(self.model.EMITTED_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                                 bounds=(0, None))

            # Charged and discharged commodities
            self.model.mass_energy_storage_in_commodities = Var(self.model.STORAGES, self.model.CLUSTERS,
                                                                self.model.TIME,
                                                                bounds=(0, None))
            self.model.mass_energy_storage_out_commodities = Var(self.model.STORAGES, self.model.CLUSTERS,
                                                                 self.model.TIME,
                                                                 bounds=(0, None))
            self.model.soc = Var(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME, bounds=(0, None))

            # sold and purchased commodities
            self.model.mass_energy_sell_commodity = Var(self.model.SALEABLE_COMMODITIES, self.model.CLUSTERS,
                                                        self.model.TIME,
                                                        bounds=(0, None))
            self.model.mass_energy_purchase_commodity = Var(self.model.PURCHASABLE_COMMODITIES, self.model.CLUSTERS,
                                                            self.model.TIME,
                                                            bounds=(0, None))

            # generated commodities
            self.model.mass_energy_generation = Var(self.model.GENERATORS, self.model.GENERATED_COMMODITIES,
                                                    self.model.CLUSTERS,
                                                    self.model.TIME,
                                                    bounds=(0, None))

            # Demanded commodities
            self.model.mass_energy_demand = Var(self.model.DEMANDED_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                                bounds=(0, None))

            # Hot standby demand
            self.model.mass_energy_hot_standby_demand = Var(self.model.STANDBY_COMPONENTS, self.model.COMMODITIES,
                                                            self.model.CLUSTERS,
                                                            self.model.TIME, bounds=(0, None))

        attach_commodity_variables_to_optimization_problem()

    def attach_economic_parameters(self):

        def attach_annuity_to_optimization_problem():
            self.model.ANF = Param(self.model.COMPONENTS, initialize=self.annuity_factor_dict)

        attach_annuity_to_optimization_problem()

        def attach_component_parameters_to_optimization_problem():
            self.model.lifetime = Param(self.model.COMPONENTS, initialize=self.lifetime_dict)
            self.model.fixed_om = Param(self.model.COMPONENTS, initialize=self.fixed_om_dict)
            self.model.variable_om = Param(self.model.COMPONENTS, initialize=self.variable_om_dict)

            self.model.capex_var = Param(self.model.COMPONENTS, initialize=self.capex_var_dict)
            self.model.capex_fix = Param(self.model.COMPONENTS, initialize=self.capex_fix_dict)

        attach_component_parameters_to_optimization_problem()

        def attach_scalable_component_parameters_to_optimization_problem():
            # Investment linearized: Investment = capex var * capacity + capex fix
            # Variable part of investment -> capex var * capacity

            self.model.capex_pre_var = Param(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                             initialize=self.scaling_capex_var_dict)
            # fix part of investment
            self.model.capex_pre_fix = Param(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                             initialize=self.scaling_capex_fix_dict)

        attach_scalable_component_parameters_to_optimization_problem()

        def attach_shut_down_component_parameters_to_optimization_problem():
            self.model.start_up_costs = Param(self.model.SHUT_DOWN_COMPONENTS, initialize=self.shut_down_start_up_costs)

        attach_shut_down_component_parameters_to_optimization_problem()

        def attach_commodity_price_parameters_to_optimization_problem():
            self.model.purchase_price = Param(self.model.PURCHASABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                              initialize=self.purchase_price_dict)
            self.model.selling_price = Param(self.model.SALEABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                             initialize=self.sell_price_dict)

        attach_commodity_price_parameters_to_optimization_problem()

    def attach_economic_variables(self):

        # Investment of each component
        self.model.investment = Var(self.model.COMPONENTS, bounds=(0, None))

        # Restart costs
        self.model.restart_costs = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.CLUSTERS, self.model.TIME,
                                       bounds=(0, None))

    def attach_ecologic_parameters(self):

        def attach_purchase_specific_co2_emissions_time_series_to_optimization_problem():
            self.model.purchase_specific_co2_emissions \
                = Param(self.model.PURCHASABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                        initialize=self.purchase_specific_CO2_emissions_dict)
        attach_purchase_specific_co2_emissions_time_series_to_optimization_problem()

        def attach_sale_specific_co2_emissions_time_series_to_optimization_problem():
            self.model.sale_specific_co2_emissions \
                = Param(self.model.SALEABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                        initialize=self.sale_specific_CO2_emissions_dict)
        attach_sale_specific_co2_emissions_time_series_to_optimization_problem()

        def attach_available_specific_co2_emissions_time_series_to_optimization_problem():
            self.model.available_specific_co2_emissions \
                = Param(self.model.AVAILABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                        initialize=self.available_specific_CO2_emissions_dict)
        attach_available_specific_co2_emissions_time_series_to_optimization_problem()

        def attach_emitted_specific_co2_emissions_time_series_to_optimization_problem():
            self.model.emitted_specific_co2_emissions \
                = Param(self.model.EMITTED_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                        initialize=self.emitted_specific_CO2_emissions_dict)
        attach_emitted_specific_co2_emissions_time_series_to_optimization_problem()

        def attach_component_parameters_to_optimization_problem():
            self.model.installation_co2_emissions_per_capacity = Param(self.model.COMPONENTS,
                                                                       initialize=self.installation_co2_emissions_dict)
            self.model.fixed_co2_emissions = Param(self.model.COMPONENTS,
                                                   initialize=self.fixed_co2_emissions_dict)
            self.model.variable_co2_emissions = Param(self.model.COMPONENTS,
                                                      initialize=self.variable_co2_emissions_dict)
            self.model.disposal_co2_emissions = Param(self.model.COMPONENTS,
                                                      initialize=self.disposal_co2_emissions_dict)
        attach_component_parameters_to_optimization_problem()

    def attach_multi_objective_variables(self):

        def attach_slack_economical():
            self.model.slack_economical = Var(bounds=(0, None))
        attach_slack_economical()

        def attach_slack_ecological():
            self.model.slack_ecological = Var(bounds=(0, None))
        attach_slack_ecological()

    def attach_technical_constraints(self):

        def _mass_energy_balance_rule(m, cl, com, t):
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased commodities
            #   = emitted, sold, demanded, charged and used (in) commodities
            commodity_object = self.pm_object.get_commodity(com)
            equation_lhs = []
            equation_rhs = []

            if commodity_object.is_available():
                equation_lhs.append(m.mass_energy_available[com, cl, t])
            if commodity_object.is_emittable():
                equation_lhs.append(-m.mass_energy_emitted[com, cl, t])
            if commodity_object.is_purchasable():
                equation_lhs.append(m.mass_energy_purchase_commodity[com, cl, t])
            if commodity_object.is_saleable():
                equation_lhs.append(-m.mass_energy_sell_commodity[com, cl, t])
            if commodity_object.is_demanded():
                equation_lhs.append(-m.mass_energy_demand[com, cl, t])
            if com in m.STORAGES:
                equation_lhs.append(
                    m.mass_energy_storage_out_commodities[com, cl, t] - m.mass_energy_storage_in_commodities[
                        com, cl, t])
            if com in m.GENERATED_COMMODITIES:
                equation_lhs.append(sum(m.mass_energy_generation[g, com, cl, t]
                                        for g in m.GENERATORS
                                        if self.pm_object.get_component(g).get_generated_commodity() == com))

            for c in m.CONVERSION_COMPONENTS:
                if (c, com) in self.output_tuples:
                    equation_lhs.append(m.mass_energy_component_out_commodities[c, com, cl, t])

                if (c, com) in self.input_tuples:
                    equation_rhs.append(m.mass_energy_component_in_commodities[c, com, cl, t])

                # hot standby demand
                if c in m.STANDBY_COMPONENTS:
                    hot_standby_commodity = [*self.pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                    if com == hot_standby_commodity:
                        equation_rhs.append(m.mass_energy_hot_standby_demand[c, com, cl, t])

            return sum(equation_lhs) == sum(equation_rhs)

        self.model._mass_energy_balance_con = Constraint(self.model.CLUSTERS, self.model.COMMODITIES, self.model.TIME,
                                                         rule=_mass_energy_balance_rule)

        def demand_satisfaction_rule(m, me, cl, t):
            # Sets commodities, which are demanded
            if me not in m.TOTAL_DEMANDED_COMMODITIES:  # Case where demand needs to be satisfied in every t
                return m.mass_energy_demand[me, cl, t] >= m.hourly_commodity_demand[me, cl, t]
            else:  # case covering demand over all time steps
                return Constraint.Skip

        self.model.demand_satisfaction_con = Constraint(self.model.DEMANDED_COMMODITIES, self.model.CLUSTERS,
                                                        self.model.TIME,
                                                        rule=demand_satisfaction_rule)

        def total_demand_satisfaction_rule(m, me):
            # Sets commodities, which are demanded
            if me not in m.TOTAL_DEMANDED_COMMODITIES:  # Case where demand needs to be satisfied in every t
                return Constraint.Skip
            else:  # case covering demand over all time steps
                return sum(m.mass_energy_demand[me, cl, t] * m.weightings[cl]
                           for cl in m.CLUSTERS for t in m.TIME) >= m.total_commodity_demand[me]

        self.model.total_demand_satisfaction_con = Constraint(self.model.DEMANDED_COMMODITIES,
                                                              rule=total_demand_satisfaction_rule)

        def capacity_binary_sum_rule(m, c):
            # For each component, only one capacity over all integer steps can be 1
            return sum(m.capacity_binary[c, i] for i in m.INTEGER_STEPS) <= 1  # todo: == 1?

        self.model.capacity_binary_sum_con = Constraint(self.model.SCALABLE_COMPONENTS, rule=capacity_binary_sum_rule)

        def capacity_binary_activation_rule(m, c, i):
            # Capacity binary will be 1 if the capacity of the integer step is higher than 0
            return m.capacity_binary[c, i] >= m.nominal_cap_pre[c, i] / m.M[c]

        self.model.capacity_binary_activation_con = Constraint(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                                               rule=capacity_binary_activation_rule)

        def set_lower_bound_rule(m, c, i):
            # capacity binary sets lower bound. Lower bound is not predefined as each capacity step can be 0
            # if capacity binary = 0 -> nominal_cap_pre has no lower bound
            # if capacity binary = 1 -> nominal_cap_pre needs to be at least lower bound

            return m.nominal_cap_pre[c, i] >= self.scaling_capex_lower_bound_dict[c, i] * m.capacity_binary[c, i]

        self.model.set_lower_bound_con = Constraint(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                                    rule=set_lower_bound_rule)

        def final_capacity_rule(m, c):
            # Final capacity of component is sum of capacity over all integer steps
            return m.nominal_cap[c] == sum(m.nominal_cap_pre[c, i] for i in m.INTEGER_STEPS)

        self.model.final_capacity_con = Constraint(self.model.SCALABLE_COMPONENTS, rule=final_capacity_rule)

        def _commodity_conversion_output_rule(m, c, oc, cl, t):
            # Define ratio between main input and output commodities for all conversion tuples
            main_input = self.pm_object.get_component(c).get_main_input()
            outputs = self.pm_object.get_component(c).get_outputs()
            if oc in [*outputs.keys()]:
                return m.mass_energy_component_out_commodities[c, oc, cl, t] == \
                       m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                       * self.output_conversion_tuples_dict[c, main_input, oc]
            else:
                return m.mass_energy_component_out_commodities[c, oc, cl, t] == 0

        self.model._commodity_conversion_output_con = Constraint(self.model.CONVERSION_COMPONENTS,
                                                                 self.model.OUTPUT_COMMODITIES,
                                                                 self.model.CLUSTERS, self.model.TIME,
                                                                 rule=_commodity_conversion_output_rule)

        def _commodity_conversion_input_rule(m, c, ic, cl, t):
            # Define ratio between main input and other input commodities for all conversion tuples
            main_input = self.pm_object.get_component(c).get_main_input()
            inputs = self.pm_object.get_component(c).get_inputs()
            if ic in [*inputs.keys()]:
                if ic != main_input:
                    return m.mass_energy_component_in_commodities[c, ic, cl, t] == \
                           m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                           * self.input_conversion_tuples_dict[c, main_input, ic]
                else:
                    return Constraint.Skip
            else:
                return m.mass_energy_component_in_commodities[c, ic, cl, t] == 0

        self.model._commodity_conversion_input_con = Constraint(self.model.CONVERSION_COMPONENTS,
                                                                self.model.INPUT_COMMODITIES,
                                                                self.model.CLUSTERS, self.model.TIME,
                                                                rule=_commodity_conversion_input_rule)

        def balance_component_status_rule(m, c, cl, t):
            # The component is either on, off or in hot standby
            return m.status_on[c, cl, t] + m.status_off[c, cl, t] + m.status_standby[c, cl, t] == 1

        self.model.balance_component_status_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                             self.model.TIME,
                                                             rule=balance_component_status_rule)

        def component_no_shutdown_or_standby_rule(m, c, cl, t):
            # If component can not be shut off or put in hot standby, the status is always on
            if (c not in m.SHUT_DOWN_COMPONENTS) & (c not in m.STANDBY_COMPONENTS):
                return m.status_on[c, cl, t] == 1
            elif c not in m.SHUT_DOWN_COMPONENTS:
                return m.status_off[c, cl, t] == 0
            elif c not in m.STANDBY_COMPONENTS:
                return m.status_standby[c, cl, t] == 0
            else:
                return Constraint.Skip

        self.model.component_no_shutdown_or_standby_con = Constraint(self.model.CONVERSION_COMPONENTS,
                                                                     self.model.CLUSTERS, self.model.TIME,
                                                                     rule=component_no_shutdown_or_standby_rule)

        def _active_component_rule(m, c, cl, t):
            # Set binary to 1 if component is active
            main_input = self.pm_object.get_component(c).get_main_input()
            return m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                   - m.status_on[c, cl, t] * m.M[c] <= 0

        self.model._active_component_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                      self.model.TIME,
                                                      rule=_active_component_rule)

        def balance_status_off_switch_rule(m, c, cl, t):
            return m.status_off_switch_on[c, cl, t] + m.status_off_switch_off[c, cl, t] <= 1

        self.model.balance_status_off_switch_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                              self.model.TIME,
                                                              rule=balance_status_off_switch_rule)

        def status_off_switch_rule(m, c, cl, t):
            if t > 0:
                return m.status_off[c, cl, t] == m.status_off[c, cl, t - 1] + m.status_off_switch_on[c, cl, t] \
                       - m.status_off_switch_off[c, cl, t]
            else:
                return Constraint.Skip

        self.model.status_off_switch_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                      self.model.TIME,
                                                      rule=status_off_switch_rule)

        def balance_status_standby_switch_rule(m, c, cl, t):
            return m.status_standby_switch_on[c, cl, t] + m.status_standby_switch_off[c, cl, t] <= 1

        self.model.balance_status_standby_switch_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                                  self.model.TIME,
                                                                  rule=balance_status_standby_switch_rule)

        def status_standby_switch_rule(m, c, cl, t):
            if t > 0:
                return m.status_standby[c, cl, t] == m.status_standby[c, cl, t - 1] \
                       + m.status_standby_switch_on[c, cl, t] \
                       - m.status_standby_switch_off[c, cl, t]
            else:
                return Constraint.Skip

        self.model.status_standby_switch_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS,
                                                          self.model.TIME,
                                                          rule=status_standby_switch_rule)

        def _conversion_maximal_component_capacity_rule(m, c, cl, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            main_input = self.pm_object.get_component(c).get_main_input()
            return m.mass_energy_component_in_commodities[c, main_input, cl, t] <= m.nominal_cap[c] * m.max_p[c]

        self.model._conversion_maximal_component_capacity_con = Constraint(self.model.CONVERSION_COMPONENTS,
                                                                           self.model.CLUSTERS, self.model.TIME,
                                                                           rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(m, c, cl, t):
            main_input = self.pm_object.get_component(c).get_main_input()
            return m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                   >= m.nominal_cap[c] * m.min_p[c] + (m.status_on[c, cl, t] - 1) * m.M[c]

        self.model._conversion_minimal_component_capacity_con = Constraint(self.model.CONVERSION_COMPONENTS,
                                                                           self.model.CLUSTERS,
                                                                           self.model.TIME,
                                                                           rule=_conversion_minimal_component_capacity_rule)

        def _ramp_up_rule(m, c, cl, t):
            main_input = self.pm_object.get_component(c).get_main_input()
            if t > 0:
                return (m.mass_energy_component_in_commodities[c, main_input, cl, t]
                        - m.mass_energy_component_in_commodities[c, main_input, cl, t - 1]) <= \
                       m.nominal_cap[c] * m.ramp_up[c] + (m.status_off_switch_off[c, cl, t]
                                                          + m.status_standby_switch_off[c, cl, t]) * m.M[c]
            else:
                return Constraint.Skip

        self.model._ramp_up_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME,
                                             rule=_ramp_up_rule)

        def _ramp_down_rule(m, c, cl, t):
            main_input = self.pm_object.get_component(c).get_main_input()
            if t > 0:
                return (m.mass_energy_component_in_commodities[c, main_input, cl, t]
                        - m.mass_energy_component_in_commodities[c, main_input, cl, t - 1]) >= \
                       - (m.nominal_cap[c] * m.ramp_down[c] +
                          (m.status_off_switch_on[c, cl, t] + m.status_standby_switch_on[c, cl, t]) * m.M[c])
            else:
                return Constraint.Skip

        self.model._ramp_down_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME,
                                               rule=_ramp_down_rule)

        def shut_off_downtime_adherence_rule(m, c, cl, t):
            if m.down_time[c] + t > max(m.TIME):
                dt = max(m.TIME) - t + 1
            else:
                dt = m.down_time[c]

            if t > 0:
                return (m.status_off[c, cl, t] - m.status_off[c, cl, t - 1]) - sum(m.status_off[c, cl, t + i]
                                                                                   for i in range(dt)) / dt <= 0
            else:
                return Constraint.Skip

        self.model.shut_off_downtime_adherence_con = Constraint(self.model.SHUT_DOWN_COMPONENTS, self.model.CLUSTERS,
                                                                self.model.TIME,
                                                                rule=shut_off_downtime_adherence_rule)

        def hot_standby_downtime_adherence_rule(m, c, cl, t):
            if m.standby_time[c] + t > max(m.TIME):
                st = max(m.TIME) - t + 1
            else:
                st = m.standby_time[c]

            if t > 0:
                return (m.status_standby[c, cl, t] - m.status_standby[c, cl, t - 1]) - sum(
                    m.status_standby[c, cl, t + i]
                    for i in range(st)) / st <= 0
            else:
                return Constraint.Skip

        self.model.hot_standby_downtime_adherence_con = Constraint(self.model.STANDBY_COMPONENTS, self.model.CLUSTERS,
                                                                   self.model.TIME,
                                                                   rule=hot_standby_downtime_adherence_rule)

        def lower_limit_hot_standby_demand_rule(m, c, me, cl, t):
            # Defines demand for hot standby
            hot_standby_commodity = [*self.pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            hot_standby_demand = self.pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
            if me == hot_standby_commodity:
                return m.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t] \
                       >= m.nominal_cap[c] * hot_standby_demand + (m.status_standby[c, cl, t] - 1) * m.M[c]
            else:
                return m.mass_energy_hot_standby_demand[c, me, cl, t] == 0

        self.model.lower_limit_hot_standby_demand_con = Constraint(self.model.STANDBY_COMPONENTS,
                                                                   self.model.COMMODITIES,
                                                                   self.model.CLUSTERS, self.model.TIME,
                                                                   rule=lower_limit_hot_standby_demand_rule)

        def upper_limit_hot_standby_demand_rule(m, c, cl, t):
            # Define that the hot standby demand is not higher than the capacity * demand per capacity
            hot_standby_commodity = [*self.pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            hot_standby_demand = self.pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
            return m.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t] \
                <= m.nominal_cap[c] * hot_standby_demand

        self.model.upper_limit_hot_standby_demand_con = Constraint(self.model.STANDBY_COMPONENTS, self.model.CLUSTERS,
                                                                   self.model.TIME,
                                                                   rule=upper_limit_hot_standby_demand_rule)

        def hot_standby_binary_activation_rule(m, c, cl, t):
            # activates hot standby demand binary if component goes into hot standby
            hot_standby_commodity = [*self.pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            return m.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t] \
                <= m.status_standby[c, cl, t] * m.M[c]

        self.model.hot_standby_binary_activation_con = Constraint(self.model.STANDBY_COMPONENTS, self.model.CLUSTERS,
                                                                  self.model.TIME,
                                                                  rule=hot_standby_binary_activation_rule)

        """ Generation constraints """

        def power_generation_rule(m, g, gc, cl, t):
            generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
            if gc == generated_commodity:
                if self.pm_object.get_component(g).get_curtailment_possible():
                    return m.mass_energy_generation[g, generated_commodity, cl, t] \
                           <= m.generation_profiles[g, cl, t] * m.nominal_cap[g]
                else:
                    return m.mass_energy_generation[g, generated_commodity, cl, t] \
                           == m.generation_profiles[g, cl, t] * m.nominal_cap[g]
            else:
                return m.mass_energy_generation[g, generated_commodity, cl, t] == 0

        self.model.power_generation_con = Constraint(self.model.GENERATORS, self.model.GENERATED_COMMODITIES,
                                                     self.model.CLUSTERS, self.model.TIME,
                                                     rule=power_generation_rule)

        def attach_fixed_capacity_rule(m, c):
            if self.pm_object.get_component(c).get_has_fixed_capacity():
                return m.nominal_cap[c] == m.fixed_capacity[c]
            else:
                return Constraint.Skip

        self.model.attach_fixed_capacity_con = Constraint(self.model.COMPONENTS, rule=attach_fixed_capacity_rule)

        def storage_balance_rule(m, s, cl, t):
            if t == 0:
                return Constraint.Skip
            else:
                return m.soc[s, cl, t] == m.soc[s, cl, t - 1] \
                       + m.mass_energy_storage_in_commodities[s, cl, t - 1] * m.charging_efficiency[s] \
                       - m.mass_energy_storage_out_commodities[s, cl, t - 1] / m.discharging_efficiency[s]

        self.model.storage_balance_con = Constraint(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                                    rule=storage_balance_rule)

        if False:
            def last_soc_rule(m, s, cl, t):
                # first SOC is last SOC + storage activities
                if t == max(m.TIME):
                    return m.soc[s, cl, 0] == m.soc[s, cl, t] \
                           + m.mass_energy_storage_in_commodities[s, cl, t] * m.charging_efficiency[s] \
                           - m.mass_energy_storage_out_commodities[s, cl, t] / m.discharging_efficiency[s]
                else:
                    return Constraint.Skip

            self.model.last_soc_con = Constraint(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                                 rule=last_soc_rule)
        else:
            def total_storage_balance_rule(m, s):
                # all goes in = all goes out
                return sum(m.mass_energy_storage_in_commodities[s, cl, t] * m.weightings[cl]
                           for cl in m.CLUSTERS for t in m.TIME) \
                    * m.charging_efficiency[s] \
                    == sum(m.mass_energy_storage_out_commodities[s, cl, t] * m.weightings[cl]
                           for cl in m.CLUSTERS for t in m.TIME) \
                    / m.discharging_efficiency[s]

            self.model.total_storage_balance_con = Constraint(self.model.STORAGES, rule=total_storage_balance_rule)

        def soc_max_bound_rule(m, s, cl, t):
            return m.soc[s, cl, t] <= m.maximal_soc[s] * m.nominal_cap[s]

        self.model.soc_max = Constraint(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                        rule=soc_max_bound_rule)

        def soc_min_bound_rule(m, s, cl, t):
            return m.soc[s, cl, t] >= m.minimal_soc[s] * m.nominal_cap[s]

        self.model.soc_min = Constraint(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                        rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(m, s, cl, t):
            return m.mass_energy_storage_in_commodities[s, cl, t] <= m.nominal_cap[s] / \
                   m.ratio_capacity_p[s]

        self.model.storage_charge_upper_bound_con = Constraint(self.model.STORAGES, self.model.CLUSTERS,
                                                               self.model.TIME,
                                                               rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(m, s, cl, t):
            return m.mass_energy_storage_out_commodities[s, cl, t] / m.discharging_efficiency[s] \
                   <= m.nominal_cap[s] / m.ratio_capacity_p[s]

        self.model.storage_discharge_upper_bound_con = Constraint(self.model.STORAGES, self.model.CLUSTERS,
                                                                  self.model.TIME,
                                                                  rule=storage_discharge_upper_bound_rule)

        # storage binaries can be deactivated in certain cases to speed up calculations. This is possible
        # if excess commodities can be emitted for free. Then, storage activities to "destroy" commodities are not
        # necessary
        def storage_binary_sum_rule(m, s, cl, t):
            return m.storage_charge_binary[s, cl, t] + m.storage_discharge_binary[s, cl, t] <= 1

        self.model.storage_binary_sum_con = Constraint(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                                       rule=storage_binary_sum_rule)

        def charge_binary_activation_rule(m, s, cl, t):
            return m.mass_energy_storage_in_commodities[s, cl, t] - m.storage_charge_binary[s, cl, t] * m.M[s] <= 0

        self.model.charge_binary_activation_con = Constraint(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME,
                                                             rule=charge_binary_activation_rule)

        def discharge_binary_activation_rule(m, s, cl, t):
            return m.mass_energy_storage_out_commodities[s, cl, t] - m.storage_discharge_binary[s, cl, t] * m.M[s] <= 0

        self.model.discharge_binary_activation_con = Constraint(self.model.STORAGES, self.model.CLUSTERS,
                                                                self.model.TIME,
                                                                rule=discharge_binary_activation_rule)

    def attach_economic_constraints(self):

        def restart_costs_rule(m, c, cl, t):
            if t < max(m.TIME):  # costs when restarting
                return m.restart_costs[c, cl, t] >= m.nominal_cap[c] * m.weightings[cl] * m.start_up_costs[c] \
                       - (1 - m.status_off_switch_off[c, cl, t]) * m.M[c] * m.weightings[cl] * m.start_up_costs[c]
            else:
                # costs when restarting --> specific case as otherwise component would stay off to avoid restarting
                # costs
                return m.restart_costs[c, cl, t] >= m.nominal_cap[c] * m.weightings[cl] * m.start_up_costs[c] \
                       - (m.status_on[c, cl, t] - m.status_off_switch_off[c, cl, t]) * m.M[c] * m.weightings[cl] \
                       * m.start_up_costs[c]

        self.model.restart_costs_con = Constraint(self.model.SHUT_DOWN_COMPONENTS, self.model.CLUSTERS, self.model.TIME,
                                                  rule=restart_costs_rule)

        def calculate_investment_components_rule(m, c):
            if c not in m.GENERATORS:
                if c not in m.SCALABLE_COMPONENTS:
                    return m.investment[c] == m.nominal_cap[c] * m.capex_var[c] + m.capex_fix[c]
                else:
                    return m.investment[c] == sum(m.nominal_cap_pre[c, i] * m.capex_pre_var[c, i]
                                                  + m.capex_pre_fix[c, i] * m.capacity_binary[c, i]
                                                  for i in m.INTEGER_STEPS)
            else:
                generator_component = self.pm_object.get_component(c)
                if generator_component.get_uses_ppa():
                    return m.investment[c] == 0
                else:
                    return m.investment[c] == m.nominal_cap[c] * m.capex_var[c] + m.capex_fix[c]

        self.model.calculate_investment_components_con = Constraint(self.model.COMPONENTS,
                                                                    rule=calculate_investment_components_rule)

        return self

    def attach_economic_objective_function(self):

        def objective_function(m):
            return (sum(m.investment[c] * (m.ANF[c] + m.fixed_om[c]) for c in m.COMPONENTS)
                    + sum(m.mass_energy_storage_in_commodities[s, cl, t] * m.variable_om[s] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for s in m.STORAGES)
                    + sum(m.mass_energy_component_out_commodities[c, self.pm_object.get_component(c).get_main_output(), cl, t]
                        * m.variable_om[c] * m.weightings[cl] for t in m.TIME
                        for cl in m.CLUSTERS for c in m.CONVERSION_COMPONENTS)
                    + sum(m.mass_energy_generation[g, self.pm_object.get_component(g).get_generated_commodity(), cl, t]
                          * m.variable_om[g] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for g in m.GENERATORS)
                    + sum(m.mass_energy_purchase_commodity[me, cl, t] * m.purchase_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.PURCHASABLE_COMMODITIES)
                    + sum(m.mass_energy_sell_commodity[me, cl, t] * m.selling_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.SALEABLE_COMMODITIES)
                    + sum(m.nominal_cap[g] * m.generation_profiles[g, cl, t] * m.weightings[cl] * self.pm_object.get_component(g).get_ppa_price()
                          for g in m.GENERATORS if self.pm_object.get_component(g).get_uses_ppa()
                          for t in m.TIME for cl in m.CLUSTERS)
                    + sum(m.restart_costs[c, cl, t] for t in m.TIME for cl in m.CLUSTERS
                          for c in m.SHUT_DOWN_COMPONENTS))

        self.model.obj = Objective(rule=objective_function, sense=minimize)

    def attach_ecologic_objective_function(self):

        def objective_function(m):
            return (sum(m.nominal_cap[c]
                        * (m.installation_co2_emissions_per_capacity[c] + m.disposal_co2_emissions[c]) / 20  # m.lifetime[c]
                        for c in m.COMPONENTS)
                    + sum(m.nominal_cap[c] * m.fixed_co2_emissions[c] for c in m.COMPONENTS)
                    + sum(
                        m.mass_energy_storage_in_commodities[s, cl, t] * m.variable_co2_emissions[s] * m.weightings[cl]
                        for t in m.TIME for cl in m.CLUSTERS for s in m.STORAGES)
                    + sum(
                        m.mass_energy_component_out_commodities[
                            c, self.pm_object.get_component(c).get_main_output(), cl, t]
                        * m.variable_co2_emissions[c] * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                        for c in m.CONVERSION_COMPONENTS)
                    + sum(m.mass_energy_generation[g, self.pm_object.get_component(g).get_generated_commodity(), cl, t]
                          * m.variable_co2_emissions[g] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for g in m.GENERATORS)
                    + sum(m.mass_energy_purchase[me, cl, t] * m.purchase_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.PURCHASABLE_COMMODITIES)
                    + sum(m.mass_energy_available[me, cl, t] * m.available_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.AVAILABLE_COMMODITIES)
                    - sum(m.mass_energy_sell[me, cl, t] * m.sale_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.SALEABLE_COMMODITIES)
                    - sum(m.mass_energy_emitted[me, cl, t] * m.emitted_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.EMITTED_COMMODITIES))

        self.model.obj = Objective(rule=objective_function, sense=minimize)

    def attach_multi_objective_economic_objective_adherence_constraint(self, eps_value_economic):

        def economical_eps_rule(m):
            return (sum(m.investment[c] * m.ANF[c] for c in m.COMPONENTS)
                    + sum(m.investment[c] * m.fixed_om[c] for c in m.COMPONENTS)
                    + sum(m.mass_energy_storage_in_commodities[s, cl, t] * m.variable_om[s] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for s in m.STORAGES)
                    + sum(m.mass_energy_component_out_commodities[
                              c, self.pm_object.get_component(c).get_main_output(), cl, t]
                          * m.variable_om[c] * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS for c in
                          m.CONVERSION_COMPONENTS)
                    + sum(m.mass_energy_generation[g, self.pm_object.get_component(g).get_generated_commodity(), cl, t]
                          * m.variable_om[g] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for g in m.GENERATORS)
                    + sum(m.mass_energy_purchase[me, cl, t] * m.purchase_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.PURCHASABLE_COMMODITIES if
                          me in self.purchasable_commodities)
                    - sum(m.mass_energy_sell[me, cl, t] * m.selling_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.SALEABLE_COMMODITIES if
                          me in self.saleable_commodities)
                    + sum(m.status_off_switch_off[c, cl, t] * m.weightings[cl] * m.start_up_costs[c]
                          for t in m.TIME for cl in m.CLUSTERS for c in m.SHUT_DOWN_COMPONENTS)) \
                   + m.slack_economical == eps_value_economic

        self.model.economical_eps_con = Constraint(rule=economical_eps_rule)

    def attach_multi_objective_economic_objective_function(self):

        def objective_function(m):
            return (sum(m.investment[c] * m.ANF[c] for c in m.COMPONENTS)
                    + sum(m.investment[c] * m.fixed_om[c] for c in m.COMPONENTS)
                    + sum(m.mass_energy_storage_in_commodities[s, cl, t] * m.variable_om[s] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for s in m.STORAGES)
                    + sum(
                        m.mass_energy_component_out_commodities[
                            c, self.pm_object.get_component(c).get_main_output(), cl, t]
                        * m.variable_om[c] * m.weightings[cl] for t in m.TIME
                        for cl in m.CLUSTERS for c in m.CONVERSION_COMPONENTS)
                    + sum(m.mass_energy_generation[g, self.pm_object.get_component(g).get_generated_commodity(), cl, t]
                          * m.variable_om[g] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for g in m.GENERATORS)
                    + sum(m.mass_energy_purchase[me, cl, t] * m.purchase_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.PURCHASABLE_COMMODITIES if
                          me in self.purchasable_commodities)
                    - sum(m.mass_energy_sell[me, cl, t] * m.selling_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.SALEABLE_COMMODITIES if
                          me in self.saleable_commodities)
                    + sum(m.status_off_switch_off[c, cl, t] * m.weightings[cl] * m.start_up_costs[c]
                          for t in m.TIME for cl in m.CLUSTERS for c in m.SHUT_DOWN_COMPONENTS)
                    - m.slack_ecological * 0.0001)

        self.model.obj = Objective(rule=objective_function, sense=minimize)

    def attach_multi_objective_ecologic_objective_adherence_constraint(self, eps_value_ecologic):

        def ecological_eps_rule(m):
            return \
                (sum(m.nominal_cap[c]
                     * (m.installation_co2_emissions_per_capacity[c] + m.disposal_co2_emissions[c]) / 20  # todo: Adjust
                     for c in m.COMPONENTS)
                 + sum(m.nominal_cap[c] * m.fixed_co2_emissions[c] for c in m.COMPONENTS)
                 + sum(m.mass_energy_storage_in_commodities[s, cl, t] * m.variable_co2_emissions[s] * m.weightings[cl]
                       for t in m.TIME for cl in m.CLUSTERS for s in m.STORAGES)
                 + sum(m.mass_energy_component_out_commodities[c, self.pm_object.get_component(c).get_main_output(), cl, t]
                       * m.variable_co2_emissions[c] * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                       for c in m.CONVERSION_COMPONENTS)
                 + sum(m.mass_energy_generation[g, self.pm_object.get_component(g).get_generated_commodity(), cl, t]
                       * m.variable_co2_emissions[g] * m.weightings[cl]
                       for t in m.TIME for cl in m.CLUSTERS for g in m.GENERATORS)
                 + sum(m.mass_energy_purchase[me, cl, t] * m.purchase_specific_co2_emissions[me, cl, t]
                       * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS for me in m.PURCHASABLE_COMMODITIES)
                 + sum(m.mass_energy_available[me, cl, t] * m.available_specific_co2_emissions[me, cl, t]
                       * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS for me in m.AVAILABLE_COMMODITIES)
                 - sum(m.mass_energy_sell[me, cl, t] * m.sale_specific_co2_emissions[me, cl, t]
                       * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS for me in m.SALEABLE_COMMODITIES)
                 - sum(m.mass_energy_emitted[me, cl, t] * m.emitted_specific_co2_emissions[me, cl, t]
                       * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS for me in m.EMITTED_COMMODITIES)) \
                + m.slack_ecological == eps_value_ecologic
        self.model.ecological_eps_con = Constraint(rule=ecological_eps_rule)

    def attach_multi_objective_ecologic_objective_function(self):

        def objective_function(m):
            return (sum(m.nominal_cap[c]
                        * (m.installation_co2_emissions_per_capacity[c] + m.disposal_co2_emissions[c]) / 20  # m.lifetime[c]
                        for c in m.COMPONENTS)
                    + sum(m.nominal_cap[c] * m.fixed_co2_emissions[c] for c in m.COMPONENTS)
                    + sum(m.mass_energy_storage_in_commodities[s, cl, t] * m.variable_co2_emissions[s] * m.weightings[cl]
                        for t in m.TIME for cl in m.CLUSTERS for s in m.STORAGES)
                    + sum(m.mass_energy_component_out_commodities[c, self.pm_object.get_component(c).get_main_output(), cl, t]
                        * m.variable_co2_emissions[c] * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                        for c in m.CONVERSION_COMPONENTS)
                    + sum(m.mass_energy_generation[g, self.pm_object.get_component(g).get_generated_commodity(), cl, t]
                          * m.variable_co2_emissions[g] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for g in m.GENERATORS)
                    + sum(m.mass_energy_purchase[me, cl, t] * m.purchase_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.PURCHASABLE_COMMODITIES)
                    + sum(m.mass_energy_available[me, cl, t] * m.available_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.AVAILABLE_COMMODITIES)
                    - sum(m.mass_energy_sell[me, cl, t] * m.sale_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.SALEABLE_COMMODITIES)
                    - sum(m.mass_energy_emitted[me, cl, t] * m.emitted_specific_co2_emissions[me, cl, t]
                          * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS
                          for me in m.EMITTED_COMMODITIES)
                    - m.slack_economical * 0.0001)

        self.model.obj = Objective(rule=objective_function, sense=minimize)

    def prepare(self, optimization_type, eps_value_economic=None, eps_value_ecologic=None):
        if optimization_type == 'economical':
            self.attach_sets()
            self.attach_technical_parameters()
            self.attach_technical_variables()
            self.attach_economic_parameters()
            self.attach_economic_variables()

            self.attach_technical_constraints()
            self.attach_economic_constraints()

            if eps_value_ecologic is not None:
                self.attach_multi_objective_variables()
                self.attach_multi_objective_ecologic_objective_adherence_constraint(eps_value_ecologic)

            self.attach_economic_objective_function()

        elif optimization_type == 'ecological':

            self.attach_sets()

            self.attach_technical_parameters()
            self.attach_technical_variables()
            self.attach_economic_parameters()
            self.attach_economic_variables()
            self.attach_ecologic_parameters()

            self.attach_technical_constraints()
            self.attach_economic_constraints()

            if eps_value_economic is not None:
                self.attach_multi_objective_variables()
                self.attach_multi_objective_economic_objective_adherence_constraint(eps_value_economic)

            self.attach_ecologic_objective_function()

        else:  # multi objective
            self.attach_sets()
            self.attach_technical_parameters()
            self.attach_technical_variables()
            self.attach_economic_parameters()
            self.attach_economic_variables()
            self.attach_ecologic_parameters()

            self.attach_multi_objective_variables()

            self.attach_technical_constraints()
            self.attach_economic_constraints()

            self.attach_multi_objective_ecologic_objective_adherence_constraint(eps_value_ecologic)
            self.attach_multi_objective_economic_objective_function()

    def optimize(self, instance=None):

        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        if instance is None:
            self.instance = self.model.create_instance()
            self.results = opt.solve(self.instance, tee=False)
        else:
            self.results = opt.solve(self.instance, tee=False, warmstart=True)

        self.objective_function_value = self.instance.obj()

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.objective_function_value = None

        self.model_type = 'pyomo'

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        # technical and economical parameters
        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, \
            self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
            self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, \
            self.shut_down_down_time_dict, self.shut_down_start_up_costs, self.standby_down_time_dict, \
            self.charging_efficiency_dict, self.discharging_efficiency_dict, \
            self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_technical_component_parameters()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        # ecological parameters
        self.installation_co2_emissions_dict, self.fixed_co2_emissions_dict, \
            self.variable_co2_emissions_dict, self.disposal_co2_emissions_dict \
            = self.pm_object.get_co2_emission_data()

        self.available_specific_CO2_emissions_dict = self.pm_object.get_available_specific_co2_emissions_time_series()
        self.emitted_specific_CO2_emissions_dict = self.pm_object.get_emitted_specific_co2_emissions_time_series()
        self.purchase_specific_CO2_emissions_dict = self.pm_object.get_purchase_specific_co2_emissions_time_series()
        self.sale_specific_CO2_emissions_dict = self.pm_object.get_sale_specific_co2_emissions_time_series()

        # time series data
        self.generation_profiles_dict = self.pm_object.get_generation_time_series()
        self.hourly_demand_dict, self.total_demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        # sets
        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()
        self.scalable_components = self.pm_object.get_final_scalable_conversion_components_names()
        self.shut_down_components = self.pm_object.get_final_shut_down_conversion_components_names()
        self.standby_components = self.pm_object.get_final_standby_conversion_components_names()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities,\
            self.generated_commodities, self.all_inputs, self.all_outputs = self.pm_object.get_commodity_sets()

        # Create optimization program
        self.model = ConcreteModel()
        self.model.TIME = RangeSet(0, self.pm_object.get_covered_period() - 1)
        self.model.CLUSTERS = RangeSet(0, self.pm_object.get_number_clusters() - 1)
        self.model.INTEGER_STEPS = RangeSet(0, self.pm_object.integer_steps - 1)

        bigM_capacity = anticipate_bigM(self.pm_object)
        self.model.M = Param(self.all_components, initialize=bigM_capacity)
