import pyomo.environ as pyo
from pyomo.core import *
from copy import deepcopy

from old_code import get_dual_model_data_from_gurobi


class SuperProblemRepresentative:

    def clone_components_which_use_parallelization(self):
        pm_object_copy = deepcopy(self.pm_object)

        # Copy components if number of components in system is higher than 1
        for component_object in pm_object_copy.get_final_conversion_components_objects():
            if component_object.get_number_parallel_units() > 1:
                # Simply rename first component
                component_name = component_object.get_name()
                component_object.set_name(component_name + '_0')
                pm_object_copy.remove_component_entirely(component_name)
                pm_object_copy.add_component(component_name + '_0', component_object)

                for i in range(1, int(component_object.get_number_parallel_units())):
                    # Add other components as copy
                    parallel_unit_component_name = component_name + '_' + str(i)
                    component_copy = component_object.__copy__()
                    component_copy.set_name(parallel_unit_component_name)
                    pm_object_copy.add_component(parallel_unit_component_name, component_copy)

        return pm_object_copy

    def attach_component_sets_to_optimization_problem(self):
        self.model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
        self.model.STORAGES = Set(initialize=self.storage_components)
        self.model.GENERATORS = Set(initialize=self.generator_components)
        self.model.COMPONENTS = Set(initialize=self.all_components)

    def attach_scalable_component_sets_to_optimization_problem(self):
        self.model.SCALABLE_COMPONENTS = Set(initialize=self.scalable_components)

    def attach_shut_down_component_sets_to_optimization_problem(self):
        self.model.SHUT_DOWN_COMPONENTS = Set(initialize=self.shut_down_components)

    def attach_standby_component_sets_to_optimization_problem(self):
        self.model.STANDBY_COMPONENTS = Set(initialize=self.standby_components)

    def attach_commodity_sets_to_optimization_problem(self):
        self.model.ME_COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
        self.model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
        self.model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
        self.model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
        self.model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
        self.model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
        self.model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
        self.model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)

    def attach_annuity_to_optimization_problem(self):
        self.model.ANF = Param(self.model.COMPONENTS, initialize=self.annuity_factor_dict)

    def attach_auxiliary_variables_to_optimization_problem(self):
        # Component variables
        self.model.auxiliary_variable = Var()

    def attach_component_parameters_to_optimization_problem(self):
        self.model.lifetime = Param(self.model.COMPONENTS, initialize=self.lifetime_dict)
        self.model.fixed_om = Param(self.model.COMPONENTS, initialize=self.fixed_om_dict)
        self.model.variable_om = Param(self.model.COMPONENTS, initialize=self.variable_om_dict)

        self.model.capex_var = Param(self.model.COMPONENTS, initialize=self.capex_var_dict)
        self.model.capex_fix = Param(self.model.COMPONENTS, initialize=self.capex_fix_dict)

        self.model.min_p = Param(self.model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
        self.model.max_p = Param(self.model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)

        self.model.ramp_up = Param(self.model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
        self.model.ramp_down = Param(self.model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

        self.model.charging_efficiency = Param(self.model.STORAGES, initialize=self.charging_efficiency_dict)
        self.model.discharging_efficiency = Param(self.model.STORAGES, initialize=self.discharging_efficiency_dict)

        self.model.minimal_soc = Param(self.model.STORAGES, initialize=self.minimal_soc_dict)
        self.model.maximal_soc = Param(self.model.STORAGES, initialize=self.maximal_soc_dict)

        self.model.ratio_capacity_p = Param(self.model.STORAGES, initialize=self.ratio_capacity_power_dict)

        self.model.generator_fixed_capacity = Param(self.model.GENERATORS, initialize=self.fixed_capacity_dict)

    def attach_component_variables_to_optimization_problem(self):
        # Component variables
        self.model.nominal_cap = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.investment = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.annuity = Var(self.model.COMPONENTS, bounds=(0, None))

    def attach_commodity_variables_to_optimization_problem(self):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        self.model.mass_energy_component_in_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_COMMODITIES,
                                                              self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_component_out_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_COMMODITIES,
                                                               self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))

        # Freely available commodities
        self.model.mass_energy_available = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_emitted = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))

        # Charged and discharged commodities
        self.model.mass_energy_storage_in_commodities = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_storage_out_commodities = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.soc = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))

        # sold and purchased commodities
        self.model.mass_energy_sell_commodity = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_purchase_commodity = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))

        # generated commodities
        self.model.mass_energy_generation = Var(self.model.GENERATORS, self.model.ME_COMMODITIES, self.model.TIME,
                                                self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_total_generation = Var(self.model.ME_COMMODITIES, self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_curtailment = Var(self.model.ME_COMMODITIES, self.model.TIME,
                                                self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        # Demanded commodities
        self.model.mass_energy_demand = Var(self.model.ME_COMMODITIES, self.model.TIME,
                                            self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_weekly_production = Var(self.model.ME_COMMODITIES, self.model.CLUSTER, self.model.ITERATION,
                                                       bounds=(0, None))
        self.model.mass_energy_weekly_surplus = Var(self.model.ME_COMMODITIES, self.model.CLUSTER,
                                                    self.model.ITERATION, bounds=(0, None))
        self.model.mass_energy_weekly_deficit = Var(self.model.ME_COMMODITIES, self.model.CLUSTER, self.model.ITERATION,
                                                    bounds=(None, 0))

        # Hot standby demand
        self.model.mass_energy_hot_standby_demand = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_COMMODITIES,
                                                        self.model.TIME, self.model.CLUSTER, self.model.ITERATION, bounds=(0, None))

    def attach_auxiliary_variables_to_optimization_problem(self):
        # Component variables
        self.model.auxiliary_variable = Var()

    def attach_purchase_price_time_series_to_optimization_problem(self):
        self.model.purchase_price = Param(self.model.PURCHASABLE_COMMODITIES, self.model.CLUSTER, self.model.TIME,
                                          initialize=self.purchase_price_dict)

    def attach_sale_price_time_series_to_optimization_problem(self):
        self.model.selling_price = Param(self.model.SALEABLE_COMMODITIES, self.model.CLUSTER, self.model.TIME,
                                         initialize=self.sell_price_dict)

    def attach_demand_time_series_to_optimization_problem(self):
        self.model.hourly_commodity_demand = Param(self.model.DEMANDED_COMMODITIES, self.model.CLUSTER,
                                                   self.model.TIME, initialize=self.hourly_demand_dict)

        self.model.total_commodity_demand = Param(self.model.TOTAL_DEMANDED_COMMODITIES,
                                                  initialize=self.total_demand_dict)

    def attach_generation_time_series_to_optimization_problem(self):

        generation_profiles_dict = {}
        for k in [*self.nominal.keys()]:
            for g in [*self.nominal[k].keys()]:
                for i in [*self.nominal[k][g].keys()]:
                    for t in range(len(self.nominal[k][g][i])):

                        generation_profiles_dict[(g, t, i, k)] = self.nominal[k][g][i][t]

                        if t == max(self.model.TIME):
                            break

        self.model.generation_profiles = Param(self.model.GENERATORS, self.model.TIME, self.model.CLUSTER,
                                               self.model.ITERATION, initialize=generation_profiles_dict)

    def attach_weightings_time_series_to_optimization_problem(self):
        self.model.weightings = Param(self.model.CLUSTER, initialize=self.weightings)

    def attach_constraints(self):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object
        model = self.model

        def _mass_energy_balance_rule(m, me_out, t, n, i):
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased commodities
            #   = emitted, sold, demanded, charged and used (in) commodities
            commodity_object = pm_object.get_commodity(me_out)
            equation_lhs = []
            equation_rhs = []

            if commodity_object.is_available():
                equation_lhs.append(m.mass_energy_available[me_out, t, n, i])
            if commodity_object.is_emittable():
                equation_lhs.append(-m.mass_energy_emitted[me_out, t, n, i])
            if commodity_object.is_purchasable():
                equation_lhs.append(m.mass_energy_purchase_commodity[me_out, t, n, i])
            if commodity_object.is_saleable():
                equation_lhs.append(-m.mass_energy_sell_commodity[me_out, t, n, i])
            if commodity_object.is_demanded():
                equation_lhs.append(-m.mass_energy_demand[me_out, t, n, i])
            if me_out in m.STORAGES:
                equation_lhs.append(
                    m.mass_energy_storage_out_commodities[me_out, t, n, i] - m.mass_energy_storage_in_commodities[
                        me_out, t, n, i])
            if me_out in m.GENERATED_COMMODITIES:
                equation_lhs.append(m.mass_energy_total_generation[me_out, t, n, i])

            for c in m.CONVERSION_COMPONENTS:
                if (c, me_out) in self.output_tuples:
                    equation_lhs.append(m.mass_energy_component_out_commodities[c, me_out, t, n, i])

                if (c, me_out) in self.input_tuples:
                    equation_rhs.append(m.mass_energy_component_in_commodities[c, me_out, t, n, i])

            equation_lhs.append(-m.mass_energy_curtailment[me_out, t, n, i])

            return sum(equation_lhs) == sum(equation_rhs)

        model._mass_energy_balance_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                    rule=_mass_energy_balance_rule)

        def _set_available_commodities_rule(m, me, t, n, i):
            # Sets commodities, which are available without limit and price
            if me in m.AVAILABLE_COMMODITIES:
                return m.mass_energy_available[me, t, n, i] >= 0
            else:
                return m.mass_energy_available[me, t, n, i] == 0

        model.set_available_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                         rule=_set_available_commodities_rule)

        def _set_emitted_commodities_rule(m, me, t, n, i):
            # Sets commodities, which are emitted without limit and price
            if me in m.EMITTED_COMMODITIES:
                return m.mass_energy_emitted[me, t, n, i] >= 0
            else:
                return m.mass_energy_emitted[me, t, n, i] == 0

        model.set_emitted_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                       rule=_set_emitted_commodities_rule)

        def _set_saleable_commodities_rule(m, me, t, n, i):
            # Sets commodities, which are sold without limit but for a certain price
            if me in m.SALEABLE_COMMODITIES:
                return m.mass_energy_sell_commodity[me, t, n, i] >= 0
            else:
                return m.mass_energy_sell_commodity[me, t, n, i] == 0

        model.set_saleable_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                        rule=_set_saleable_commodities_rule)

        def _set_purchasable_commodities_rule(m, me, t, n, i):
            # Sets commodities, which are purchased without limit but for a certain price
            if me in m.PURCHASABLE_COMMODITIES:
                return m.mass_energy_purchase_commodity[me, t, n, i] >= 0
            else:
                return m.mass_energy_purchase_commodity[me, t, n, i] == 0

        model.set_purchasable_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                           rule=_set_purchasable_commodities_rule)

        if False:
            def demand_satisfaction_rule(m, me, cl, t, i):
                # Sets commodities, which are demanded
                if me not in m.TOTAL_DEMANDED_COMMODITIES:  # Case where demand needs to be satisfied in every t
                    return m.mass_energy_demand[me, t, cl, i] >= m.hourly_commodity_demand[me, cl, t]
                else:  # case covering demand over all time steps
                    return Constraint.Skip

            model.demand_satisfaction_con = Constraint(model.DEMANDED_COMMODITIES, model.CLUSTER, model.TIME,
                                                       model.ITERATION,
                                                       rule=demand_satisfaction_rule)

            def total_demand_satisfaction_rule(m, me, i):
                # Sets commodities, which are demanded
                if me not in m.TOTAL_DEMANDED_COMMODITIES:  # Case where demand needs to be satisfied in every t
                    return Constraint.Skip
                else:  # case covering demand over all time steps
                    return sum(m.mass_energy_demand[me, t, cl, i] * m.weightings[cl]
                               for cl in m.CLUSTER for t in m.TIME) >= m.total_commodity_demand[me]

            model.total_demand_satisfaction_con = Constraint(model.DEMANDED_COMMODITIES, model.ITERATION,
                                                             rule=total_demand_satisfaction_rule)

        if True:
            def weekly_demand_satisfaction_rule(m, me, cl, i):
                # Sets commodities, which are demanded
                return m.mass_energy_weekly_production[me, cl, i]  \
                    == sum(m.mass_energy_demand[me, t, cl, i] for t in m.TIME) \
                    - m.total_commodity_demand[me] / (8760 / len(m.TIME))
            model.weekly_demand_satisfaction_con = Constraint(model.DEMANDED_COMMODITIES, model.CLUSTER,
                                                              model.ITERATION,
                                                              rule=weekly_demand_satisfaction_rule)

            def balance_weekly_production_rule(m, me, cl, i):
                return m.mass_energy_weekly_production[me, cl, i] \
                       == m.mass_energy_weekly_surplus[me, cl, i] + m.mass_energy_weekly_deficit[me, cl, i]
            model.balance_weekly_production_con = Constraint(model.DEMANDED_COMMODITIES, model.CLUSTER,
                                                             model.ITERATION, rule=balance_weekly_production_rule)

        def _commodity_conversion_output_rule(m, c, me_out, t, n, i):
            # Define ratio between main input and output commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, me_out) in self.output_conversion_tuples:
                return m.mass_energy_component_out_commodities[c, me_out, t, n, i] == \
                       m.mass_energy_component_in_commodities[c, main_input, t, n, i] \
                       * self.output_conversion_tuples_dict[c, main_input, me_out]
            else:
                return m.mass_energy_component_out_commodities[c, me_out, t, n, i] == 0

        model._commodity_conversion_output_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                            model.TIME, model.CLUSTER, model.ITERATION,
                                                            rule=_commodity_conversion_output_rule)

        def _commodity_conversion_input_rule(m, c, me_in, t, n, i):
            # Define ratio between main input and other input commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return Constraint.Skip
            else:
                if (c, main_input, me_in) in self.input_conversion_tuples:
                    return m.mass_energy_component_in_commodities[c, me_in, t, n, i] == \
                           m.mass_energy_component_in_commodities[c, main_input, t, n, i] \
                           * self.input_conversion_tuples_dict[c, main_input, me_in]
                else:
                    return m.mass_energy_component_in_commodities[c, me_in, t, n, i] == 0

        model._commodity_conversion_input_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                           model.TIME, model.CLUSTER, model.ITERATION,
                                                           rule=_commodity_conversion_input_rule)

        def _conversion_maximal_component_capacity_rule(m, c, me_in, t, n, i):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t, n, i] <= m.nominal_cap[c] * m.max_p[c]
            else:
                return Constraint.Skip

        model._conversion_maximal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                                      model.TIME, model.CLUSTER, model.ITERATION,
                                                                      rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(m, c, me_in, t, n, i):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t, n, i] \
                       >= m.nominal_cap[c] * m.min_p[c]
            else:
                return Constraint.Skip

        model._conversion_minimal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                                      model.TIME, model.CLUSTER, model.ITERATION,
                                                                      rule=_conversion_minimal_component_capacity_rule)

        def _ramp_up_rule(m, c, me_in, t, n, i):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t, n, i]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1, n, i]) <= \
                           m.nominal_cap[c] * m.ramp_up[c]
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip

        model._ramp_up_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                        rule=_ramp_up_rule)

        def _ramp_down_rule(m, c, me_in, t, n, i):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t, n, i]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1, n, i]) >= \
                           - (m.nominal_cap[c] * m.ramp_down[c])
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip

        model._ramp_down_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES, model.TIME, model.CLUSTER,
                                          model.ITERATION,
                                          rule=_ramp_down_rule)

        """ Generation constraints """

        def power_generation_rule(m, g, me, t, n, i):
            if me == pm_object.get_component(g).get_generated_commodity():
                if pm_object.get_component(g).get_curtailment_possible():
                    return m.mass_energy_generation[g, me, t, n, i] <= m.generation_profiles[g, t, n, i] * m.nominal_cap[g]
                else:
                    return m.mass_energy_generation[g, me, t, n, i] == m.generation_profiles[g, t, n, i] * m.nominal_cap[g]
            else:
                return m.mass_energy_generation[g, me, t, n, i] == 0

        model.power_generation_con = Constraint(model.GENERATORS, model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                rule=power_generation_rule)

        def attach_fixed_capacity_rule(m, g):
            if pm_object.get_component(g).get_has_fixed_capacity():
                return m.nominal_cap[g] == m.generator_fixed_capacity[g]
            else:
                return Constraint.Skip

        model.attach_fixed_capacity_con = Constraint(model.GENERATORS, rule=attach_fixed_capacity_rule)

        def total_power_generation_rule(m, me, t, n, i):
            return m.mass_energy_total_generation[me, t, n, i] == sum(m.mass_energy_generation[g, me, t, n, i]
                                                                   for g in m.GENERATORS)

        model.total_power_generation_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                      rule=total_power_generation_rule)

        def storage_balance_rule(m, me, t, n, i):
            if me in m.STORAGES:
                if t == 0:
                    return Constraint.Skip
                else:
                    return m.soc[me, t, n, i] == m.soc[me, t - 1, n, i] \
                           + m.mass_energy_storage_in_commodities[me, t - 1, n, i] * m.charging_efficiency[me] \
                           - m.mass_energy_storage_out_commodities[me, t - 1, n, i] / m.discharging_efficiency[me]
            else:
                return m.soc[me, t, n, i] == 0

        model.storage_balance_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                               rule=storage_balance_rule)

        def last_soc_rule(m, me, t, n, i):
            if t == max(m.TIME):
                return m.soc[me, 0, n, i] == m.soc[me, t, n, i] \
                       + m.mass_energy_storage_in_commodities[me, t, n, i] * m.charging_efficiency[me] \
                       - m.mass_energy_storage_out_commodities[me, t, n, i] / m.discharging_efficiency[me]
            else:
                return Constraint.Skip

        model.last_soc_con = Constraint(model.STORAGES, model.TIME, model.CLUSTER, model.ITERATION, rule=last_soc_rule)

        def soc_max_bound_rule(m, me, t, n, i):
            return m.soc[me, t, n, i] <= m.maximal_soc[me] * m.nominal_cap[me]

        model.soc_max = Constraint(model.STORAGES, model.TIME, model.CLUSTER, model.ITERATION, rule=soc_max_bound_rule)

        def soc_min_bound_rule(m, me, t, n, i):
            return m.soc[me, t, n, i] >= m.minimal_soc[me] * m.nominal_cap[me]

        model.soc_min = Constraint(model.STORAGES, model.TIME, model.CLUSTER, model.ITERATION, rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(m, me, t, n, i):
            if me in m.STORAGES:
                return m.mass_energy_storage_in_commodities[me, t, n, i] <= m.nominal_cap[me] / \
                       m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_in_commodities[me, t, n, i] == 0

        model.storage_charge_upper_bound_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                          rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(m, me, t, n, i):
            if me in m.STORAGES:
                return m.mass_energy_storage_out_commodities[me, t, n, i] / m.discharging_efficiency[me] \
                       <= m.nominal_cap[me] / m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_out_commodities[me, t, n, i] == 0

        model.storage_discharge_upper_bound_con = Constraint(model.ME_COMMODITIES, model.TIME, model.CLUSTER, model.ITERATION,
                                                             rule=storage_discharge_upper_bound_rule)

        def define_upper_limit_mu_rule(m, i):
            if False:
                return m.auxiliary_variable >= \
                       + sum(m.mass_energy_storage_in_commodities[c, t, n, i] * m.variable_om[c] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER for c in m.STORAGES) \
                       + sum(m.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), t, n, i]
                             * m.variable_om[c] * m.weightings[n] for t in m.TIME
                             for n in m.CLUSTER for c in m.CONVERSION_COMPONENTS) \
                       + sum(m.mass_energy_generation[c, pm_object.get_component(c).get_generated_commodity(), t, n, i]
                             * m.variable_om[c] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER for c in m.GENERATORS) \
                       + sum(m.mass_energy_purchase_commodity[me, t, n, i] * m.purchase_price[me, n, t] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER
                             for me in m.ME_COMMODITIES if me in self.purchasable_commodities) \
                       - sum(m.mass_energy_sell_commodity[me, t, n, i] * m.selling_price[me, n, t] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER
                             for me in m.ME_COMMODITIES if me in self.saleable_commodities)
            else:
                return m.auxiliary_variable >= \
                       + sum(m.mass_energy_storage_in_commodities[c, t, n, i] * m.variable_om[c] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER for c in m.STORAGES) \
                       + sum(m.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), t, n, i]
                             * m.variable_om[c] * m.weightings[n] for t in m.TIME
                             for n in m.CLUSTER for c in m.CONVERSION_COMPONENTS) \
                       + sum(m.mass_energy_generation[c, pm_object.get_component(c).get_generated_commodity(), t, n, i]
                             * m.variable_om[c] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER for c in m.GENERATORS) \
                       + sum(m.mass_energy_purchase_commodity[me, t, n, i] * m.purchase_price[me, n, t] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER
                             for me in m.ME_COMMODITIES if me in self.purchasable_commodities) \
                       - sum(m.mass_energy_sell_commodity[me, t, n, i] * m.selling_price[me, n, t] * m.weightings[n]
                             for t in m.TIME for n in m.CLUSTER
                             for me in m.ME_COMMODITIES if me in self.saleable_commodities) \
                       - sum(m.mass_energy_weekly_deficit[me, cl, i] * m.weightings[cl] * 0.25
                             for me in m.TOTAL_DEMANDED_COMMODITIES for cl in m.CLUSTER)
        model.define_upper_limit_mu_con = Constraint(model.ITERATION, rule=define_upper_limit_mu_rule)

        def objective_function(m):
            return sum((m.nominal_cap[c] * m.capex_var[c] + m.capex_fix[c])
                       * (m.ANF[c] + m.fixed_om[c]) for c in m.COMPONENTS) \
                   + m.auxiliary_variable
        model.obj = Objective(rule=objective_function, sense=minimize)

        return model

    def optimize(self, instance=None):

        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        # opt.options["mipgap"] = 0.05
        # opt.options["NonConvex"] = 2
        opt.options['Threads'] = 120

        if instance is None:
            instance = self.model.create_instance()

            if False:

                if self.solver == 'gurobi':
                    gurobi_model, A, sense, rhs, constr_names, var_ub, var_lb, var_names, objective = opt.solve(
                        instance,
                        return_opt=True)

                    var_name_pyomo = []
                    for n in var_names:
                        var_name_pyomo.append(gurobi_model._solver_var_to_pyomo_var_map[n].local_name)

                    cons_name_pyomo = []
                    for n in constr_names:
                        cons_name_pyomo.append(gurobi_model._solver_con_to_pyomo_con_map[n].local_name)

                    get_dual_model_data_from_gurobi(A, sense, rhs, cons_name_pyomo, var_ub, var_lb, var_name_pyomo,
                                                   objective)

            results = opt.solve(instance, tee=True)
        else:
            results = opt.solve(instance, tee=True, warmstart=True)

        print(results)

        self.optimal_capacities = {}
        for v in instance.component_objects(Var):

            if str(v) == 'nominal_cap':

                variable_dict = v.extract_values()

                for i in v.index_set():
                    self.optimal_capacities[i] = variable_dict[i]

            elif str(v) == 'auxiliary_variable':

                self.auxiliary_variable = list(v.extract_values().values())[0]

        self.obj_value = instance.obj()

        return instance, results

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, nominal, number_clusters, weightings, iteration):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.nominal = nominal
        self.weightings = weightings

        self.optimal_capacities = None
        self.obj_value = None
        self.auxiliary_variable = None

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict,\
            self.minimal_power_dict, \
            self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
            self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, \
            self.shut_down_down_time_dict, self.shut_down_start_up_costs, self.standby_down_time_dict, \
            self.charging_efficiency_dict, self.discharging_efficiency_dict, \
            self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components,\
            self.no_shut_down_components, self.standby_components,\
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities, \
            self.all_inputs, self.all_outputs = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict\
            = self.pm_object.get_all_conversions()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        self.hourly_demand_dict, self.total_demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()

        # Adjust purchase & selling price
        if number_clusters > 0:
            for t in range(self.pm_object.get_time_steps()):
                for me in self.purchasable_commodities:
                    self.purchase_price_dict[(me, number_clusters, t)] \
                        = self.purchase_price_dict[(me, number_clusters - 1, t)]

                for me in self.saleable_commodities:
                    self.sell_price_dict[(me, number_clusters, t)] \
                        = self.sell_price_dict[(me, number_clusters - 1, t)]

        # Create optimization program
        self.model = ConcreteModel()
        self.model.TIME = RangeSet(0, self.pm_object.get_time_steps() - 1)
        self.model.CLUSTER = RangeSet(0, number_clusters)
        self.model.ITERATION = RangeSet(0, iteration)
        self.model.INTEGER_STEPS = RangeSet(0, self.pm_object.integer_steps)
        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.model.M = Param(initialize=1000000000)

        # Attach Sets
        self.attach_component_sets_to_optimization_problem()
        self.attach_commodity_sets_to_optimization_problem()

        # Attach Parameters
        self.attach_component_parameters_to_optimization_problem()
        self.attach_annuity_to_optimization_problem()
        self.attach_weightings_time_series_to_optimization_problem()

        # Attach Variables
        self.attach_component_variables_to_optimization_problem()
        self.attach_commodity_variables_to_optimization_problem()
        self.attach_purchase_price_time_series_to_optimization_problem()
        self.attach_sale_price_time_series_to_optimization_problem()
        self.attach_demand_time_series_to_optimization_problem()
        self.attach_generation_time_series_to_optimization_problem()
        self.attach_auxiliary_variables_to_optimization_problem()

        self.model = self.attach_constraints()

        # print(self.instance.pprint())
