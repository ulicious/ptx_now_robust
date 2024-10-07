import pyomo.environ as pyo
from pyomo.core import *
from pyomo.core import Binary
from copy import deepcopy

import os
from old_code import get_dual_model_data_from_gurobi


class FixedCapacityMaximization:

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

        self.model.nominal_cap = Param(self.model.COMPONENTS, initialize=self.optimal_capacities)

    def attach_component_variables_to_optimization_problem(self):
        # Component variables
        self.model.investment = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.annuity = Var(self.model.COMPONENTS, bounds=(0, None))

    def attach_commodity_variables_to_optimization_problem(self):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        self.model.mass_energy_component_in_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_COMMODITIES,
                                                              self.model.TIME, bounds=(0, None))
        self.model.mass_energy_component_out_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_COMMODITIES,
                                                               self.model.TIME, bounds=(0, None))

        # Freely available commodities
        self.model.mass_energy_available = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_emitted = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))

        # Charged and discharged commodities
        self.model.mass_energy_storage_in_commodities = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_storage_out_commodities = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))
        self.model.soc = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))

        # sold and purchased commodities
        self.model.mass_energy_sell_commodity = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_purchase_commodity = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))

        # generated commodities
        self.model.mass_energy_generation = Var(self.model.GENERATORS, self.model.ME_COMMODITIES, self.model.TIME,
                                                bounds=(0, None))
        self.model.mass_energy_total_generation = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_curtailment = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))
        # Demanded commodities
        self.model.mass_energy_demand = Var(self.model.ME_COMMODITIES, self.model.TIME, bounds=(0, None))

        # Hot standby demand
        self.model.mass_energy_hot_standby_demand = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_COMMODITIES,
                                                        self.model.TIME, bounds=(0, None))

        self.model.dispatch_costs = Var()

    def attach_purchase_price_time_series_to_optimization_problem(self):
        self.model.purchase_price = Param(self.model.PURCHASABLE_COMMODITIES, self.model.TIME,
                                          initialize=self.purchase_price_dict)

    def attach_sale_price_time_series_to_optimization_problem(self):
        self.model.selling_price = Param(self.model.SALEABLE_COMMODITIES, self.model.TIME, initialize=self.sell_price_dict)

    def attach_demand_time_series_to_optimization_problem(self):
        self.model.commodity_demand = Param(self.model.DEMANDED_COMMODITIES, self.model.TIME, initialize=self.demand_dict)

    def attach_generation_time_series_to_optimization_problem(self):

        generation_profiles_dict = {}
        for g in [*self.nominal.keys()]:
            for t in range(len(self.nominal[g])):

                generation_profiles_dict[(g, t)] = self.nominal[g][t]

                if t == max(self.model.TIME):
                    break

        self.model.generation_profiles = Param(self.model.GENERATORS, self.model.TIME,
                                          initialize=generation_profiles_dict)

    def attach_constraints(self):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object
        model = self.model

        def _mass_energy_balance_rule(m, me_out, t):
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased commodities
            #   = emitted, sold, demanded, charged and used (in) commodities
            commodity_object = pm_object.get_commodity(me_out)
            equation_lhs = []
            equation_rhs = []

            if commodity_object.is_available():
                equation_lhs.append(m.mass_energy_available[me_out, t])
            if commodity_object.is_emittable():
                equation_lhs.append(-m.mass_energy_emitted[me_out, t])
            if commodity_object.is_purchasable():
                equation_lhs.append(m.mass_energy_purchase_commodity[me_out, t])
            if commodity_object.is_saleable():
                equation_lhs.append(-m.mass_energy_sell_commodity[me_out, t])
            if commodity_object.is_demanded():
                equation_lhs.append(-m.mass_energy_demand[me_out, t])
            if me_out in m.STORAGES:
                equation_lhs.append(
                    m.mass_energy_storage_out_commodities[me_out, t] - m.mass_energy_storage_in_commodities[
                        me_out, t])
            if me_out in m.GENERATED_COMMODITIES:
                equation_lhs.append(m.mass_energy_total_generation[me_out, t])

            for c in m.CONVERSION_COMPONENTS:
                if (c, me_out) in self.output_tuples:
                    equation_lhs.append(m.mass_energy_component_out_commodities[c, me_out, t])

                if (c, me_out) in self.input_tuples:
                    equation_rhs.append(m.mass_energy_component_in_commodities[c, me_out, t])

            equation_lhs.append(-m.mass_energy_curtailment[me_out, t])

            return sum(equation_lhs) == sum(equation_rhs)

        model._mass_energy_balance_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                    rule=_mass_energy_balance_rule)

        def _set_available_commodities_rule(m, me, t):
            # Sets commodities, which are available without limit and price
            if me in m.AVAILABLE_COMMODITIES:
                return m.mass_energy_available[me, t] >= 0
            else:
                return m.mass_energy_available[me, t] == 0

        model.set_available_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                         rule=_set_available_commodities_rule)

        def _set_emitted_commodities_rule(m, me, t):
            # Sets commodities, which are emitted without limit and price
            if me in m.EMITTED_COMMODITIES:
                return m.mass_energy_emitted[me, t] >= 0
            else:
                return m.mass_energy_emitted[me, t] == 0

        model.set_emitted_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                       rule=_set_emitted_commodities_rule)

        def _set_saleable_commodities_rule(m, me, t):
            # Sets commodities, which are sold without limit but for a certain price
            if me in m.SALEABLE_COMMODITIES:
                return m.mass_energy_sell_commodity[me, t] >= 0
            else:
                return m.mass_energy_sell_commodity[me, t] == 0

        model.set_saleable_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                        rule=_set_saleable_commodities_rule)

        def _set_purchasable_commodities_rule(m, me, t):
            # Sets commodities, which are purchased without limit but for a certain price
            if me in m.PURCHASABLE_COMMODITIES:
                return m.mass_energy_purchase_commodity[me, t] >= 0
            else:
                return m.mass_energy_purchase_commodity[me, t] == 0

        model.set_purchasable_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                           rule=_set_purchasable_commodities_rule)

        def _total_demand_satisfaction_rule(m, me):
            if me in m.TOTAL_DEMANDED_COMMODITIES:
                return sum(m.mass_energy_demand[me, t] for t in m.TIME) \
                       >= m.commodity_demand[me, 0]
            else:
                return Constraint.Skip

        model.total_demand_satisfaction_con = Constraint(model.TOTAL_DEMANDED_COMMODITIES,
                                                         rule=_total_demand_satisfaction_rule)

        def _commodity_conversion_output_rule(m, c, me_out, t):
            # Define ratio between main input and output commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, me_out) in self.output_conversion_tuples:
                return m.mass_energy_component_out_commodities[c, me_out, t] == \
                       m.mass_energy_component_in_commodities[c, main_input, t] \
                       * self.output_conversion_tuples_dict[c, main_input, me_out]
            else:
                return m.mass_energy_component_out_commodities[c, me_out, t] == 0

        model._commodity_conversion_output_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                            model.TIME,
                                                            rule=_commodity_conversion_output_rule)

        def _commodity_conversion_input_rule(m, c, me_in, t):
            # Define ratio between main input and other input commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return Constraint.Skip
            else:
                if (c, main_input, me_in) in self.input_conversion_tuples:
                    return m.mass_energy_component_in_commodities[c, me_in, t] == \
                           m.mass_energy_component_in_commodities[c, main_input, t] \
                           * self.input_conversion_tuples_dict[c, main_input, me_in]
                else:
                    return m.mass_energy_component_in_commodities[c, me_in, t] == 0

        model._commodity_conversion_input_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                           model.TIME,
                                                           rule=_commodity_conversion_input_rule)

        def _conversion_maximal_component_capacity_rule(m, c, me_in, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] <= m.nominal_cap[c] * m.max_p[c]
            else:
                return Constraint.Skip

        model._conversion_maximal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                                      model.TIME,
                                                                      rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] \
                       >= m.nominal_cap[c] * m.min_p[c]
            else:
                return Constraint.Skip

        model._conversion_minimal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                                      model.TIME,
                                                                      rule=_conversion_minimal_component_capacity_rule)

        def _ramp_up_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1]) <= \
                           m.nominal_cap[c] * m.ramp_up[c]
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip

        model._ramp_up_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES, model.TIME,
                                        rule=_ramp_up_rule)

        def _ramp_down_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1]) >= \
                           - (m.nominal_cap[c] * m.ramp_down[c])
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip

        model._ramp_down_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES, model.TIME,
                                          rule=_ramp_down_rule)

        """ Generation constraints """

        def power_generation_rule(m, g, me, t):
            if me == pm_object.get_component(g).get_generated_commodity():
                if pm_object.get_component(g).get_curtailment_possible():
                    return m.mass_energy_generation[g, me, t] <= m.generation_profiles[g, t] * m.nominal_cap[g]
                else:
                    return m.mass_energy_generation[g, me, t] == m.generation_profiles[g, t] * m.nominal_cap[g]
            else:
                return m.mass_energy_generation[g, me, t] == 0

        model.power_generation_con = Constraint(model.GENERATORS, model.ME_COMMODITIES, model.TIME,
                                                rule=power_generation_rule)

        def attach_fixed_capacity_rule(m, g):
            if pm_object.get_component(g).get_has_fixed_capacity():
                return m.nominal_cap[g] == m.generator_fixed_capacity[g]
            else:
                return Constraint.Skip

        model.attach_fixed_capacity_con = Constraint(model.GENERATORS, rule=attach_fixed_capacity_rule)

        def total_power_generation_rule(m, me, t):
            return m.mass_energy_total_generation[me, t] == sum(m.mass_energy_generation[g, me, t]
                                                                   for g in m.GENERATORS)

        model.total_power_generation_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                      rule=total_power_generation_rule)

        def storage_balance_rule(m, me, t):
            if me in m.STORAGES:
                if t == 0:
                    return Constraint.Skip
                else:
                    return m.soc[me, t] == m.soc[me, t - 1] \
                           + m.mass_energy_storage_in_commodities[me, t - 1] * m.charging_efficiency[me] \
                           - m.mass_energy_storage_out_commodities[me, t - 1] / m.discharging_efficiency[me]
            else:
                return m.soc[me, t] == 0

        model.storage_balance_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                               rule=storage_balance_rule)

        def last_soc_rule(m, me, t):
            if t == max(m.TIME):
                return m.soc[me, 0] == m.soc[me, t] \
                       + m.mass_energy_storage_in_commodities[me, t] * m.charging_efficiency[me] \
                       - m.mass_energy_storage_out_commodities[me, t] / m.discharging_efficiency[me]
            else:
                return Constraint.Skip

        model.last_soc_con = Constraint(model.STORAGES, model.TIME, rule=last_soc_rule)

        def soc_max_bound_rule(m, me, t):
            return m.soc[me, t] <= m.maximal_soc[me] * m.nominal_cap[me]

        model.soc_max = Constraint(model.STORAGES, model.TIME, rule=soc_max_bound_rule)

        def soc_min_bound_rule(m, me, t):
            return m.soc[me, t] >= m.minimal_soc[me] * m.nominal_cap[me]

        model.soc_min = Constraint(model.STORAGES, model.TIME,rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(m, me, t):
            if me in m.STORAGES:
                return m.mass_energy_storage_in_commodities[me, t] <= m.nominal_cap[me] / \
                       m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_in_commodities[me, t] == 0

        model.storage_charge_upper_bound_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                          rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(m, me, t):
            if me in m.STORAGES:
                return m.mass_energy_storage_out_commodities[me, t] / m.discharging_efficiency[me] \
                       <= m.nominal_cap[me] / m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_out_commodities[me, t] == 0

        model.storage_discharge_upper_bound_con = Constraint(model.ME_COMMODITIES, model.TIME,
                                                             rule=storage_discharge_upper_bound_rule)

        def define_upper_limit_mu_rule(m):
            return m.dispatch_costs >= \
                   + sum(m.mass_energy_storage_in_commodities[c, t] * m.variable_om[c]
                         for t in m.TIME for c in m.STORAGES) \
                   + sum(m.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), t]
                         * m.variable_om[c] for t in m.TIME for c in m.CONVERSION_COMPONENTS) \
                   + sum(m.mass_energy_generation[c, pm_object.get_component(c).get_generated_commodity(), t]
                         * m.variable_om[c]
                         for t in m.TIME for c in m.GENERATORS) \
                   + sum(m.mass_energy_purchase_commodity[me, t] * m.purchase_price[me, t]
                         for t in m.TIME for me in m.ME_COMMODITIES if me in self.purchasable_commodities) \
                   - sum(m.mass_energy_sell_commodity[me, t] * m.selling_price[me, t]
                         for t in m.TIME for me in m.ME_COMMODITIES if me in self.saleable_commodities)
        model.define_upper_limit_mu_con = Constraint(rule=define_upper_limit_mu_rule)

        def objective_function(m):
            return sum(m.mass_energy_demand[me, t] for me in m.ME_COMMODITIES for t in m.TIME) \
                   + sum(m.mass_energy_purchase_commodity[me, t] * 0.6
                         for t in m.TIME for me in m.ME_COMMODITIES if me in self.purchasable_commodities)
        model.obj = Objective(rule=objective_function, sense=minimize)

        return model

    def optimize(self, instance=None):

        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        opt.options["mipgap"] = 0.01
        if instance is None:
            instance = self.model.create_instance()

            results = opt.solve(instance, tee=True)
        else:
            results = opt.solve(instance, tee=True, warmstart=True)

        print(results)

        self.optimal_capacities = {}
        for v in instance.component_objects(Var):
            if str(v) == 'dispatch_costs':

                variable_dict = v.extract_values()

                self.dispatch_costs = variable_dict

            elif str(v) == 'mass_energy_demand':

                self.production_volume = sum(list(v.extract_values().values()))

        return instance, results

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, optimal_capacities, nominal):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.optimal_capacities = optimal_capacities
        self.nominal = nominal

        self.dispatch_costs = None
        self.production_volume = None

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

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities,\
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities\
            = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict\
            = self.pm_object.get_all_conversions()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()

        # Create optimization program
        self.model = ConcreteModel()
        self.model.TIME = RangeSet(0, 8760-1)
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

        # Attach Variables
        self.attach_component_variables_to_optimization_problem()
        self.attach_commodity_variables_to_optimization_problem()
        self.attach_purchase_price_time_series_to_optimization_problem()
        self.attach_sale_price_time_series_to_optimization_problem()
        self.attach_demand_time_series_to_optimization_problem()
        self.attach_generation_time_series_to_optimization_problem()

        self.model = self.attach_constraints()

        # print(self.instance.pprint())
