import pyomo.environ as pyo
from copy import deepcopy

from pyomo.core import *
import pandas as pd
from dualization_from_model import dualize_from_model
from pyomo.core.expr.numeric_expr import LinearExpression
from old_code import get_dual_model_data_from_gurobi

import numpy as np

import os


class SuperOptimizationProblem:

    def attach_component_sets_to_optimization_problem(self, model):
        model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
        model.STORAGES = Set(initialize=self.storage_components)
        model.GENERATORS = Set(initialize=self.generator_components)
        model.COMPONENTS = Set(initialize=self.all_components)
        return model

    def attach_commodity_sets_to_optimization_problem(self, model):
        model.ME_COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
        model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
        model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
        model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
        model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
        model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
        model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
        model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)
        return model

    def attach_commodity_sets_to_optimization_problem(self):
        self.model.ME_STREAMS = Set(initialize=self.final_commodities)  # Mass energy commodity
        self.model.AVAILABLE_STREAMS = Set(initialize=self.available_commodities)
        self.model.EMITTED_STREAMS = Set(initialize=self.emittable_commodities)
        self.model.PURCHASABLE_STREAMS = Set(initialize=self.purchasable_commodities)
        self.model.SALEABLE_STREAMS = Set(initialize=self.saleable_commodities)
        self.model.DEMANDED_STREAMS = Set(initialize=self.demanded_commodities)
        self.model.TOTAL_DEMANDED_STREAMS = Set(initialize=self.total_demand_commodities)
        self.model.GENERATED_STREAMS = Set(initialize=self.generated_commodities)

    def attach_component_parameters_to_optimization_problem(self, model):
        model.lifetime = Param(model.COMPONENTS, initialize=self.lifetime_dict)
        model.fixed_om = Param(model.COMPONENTS, initialize=self.fixed_om_dict)
        model.variable_om = Param(model.COMPONENTS, initialize=self.variable_om_dict)

        model.capex_var = Param(model.COMPONENTS, initialize=self.capex_var_dict)
        model.capex_fix = Param(model.COMPONENTS, initialize=self.capex_fix_dict)

        model.min_p = Param(model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
        model.max_p = Param(model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)

        model.ramp_up = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
        model.ramp_down = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

        model.charging_efficiency = Param(model.STORAGES, initialize=self.charging_efficiency_dict)
        model.discharging_efficiency = Param(model.STORAGES, initialize=self.discharging_efficiency_dict)

        model.minimal_soc = Param(model.STORAGES, initialize=self.minimal_soc_dict)
        model.maximal_soc = Param(model.STORAGES, initialize=self.maximal_soc_dict)

        model.ratio_capacity_p = Param(model.STORAGES, initialize=self.ratio_capacity_power_dict)

        model.generator_fixed_capacity = Param(model.GENERATORS, initialize=self.fixed_capacity_dict)
        return model

    def attach_component_variables_to_optimization_problem(self, model):
        # Component variables
        model.nominal_cap = Var(model.COMPONENTS, bounds=(0, None))
        return model

    def attach_auxiliary_variables_to_optimization_problem(self, model):
        # Component variables
        self.model.nominal_cap = Var(self.model.COMPONENTS, bounds=(0, None))

        self.model.status_on = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)

        self.model.status_off = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.status_off_switch_on = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.status_off_switch_off = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.status_standby_switch_on = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.status_standby_switch_off = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.start_up_costs_component = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, bounds=(0, None))
        self.model.total_start_up_costs_component = Var(self.model.CONVERSION_COMPONENTS, bounds=(0, None))
        self.model.total_start_up_costs = Var(bounds=(0, None))

        self.model.status_standby = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)

        # STORAGE binaries (charging and discharging)
        self.model.storage_charge_binary = Var(self.model.STORAGES, self.model.TIME, within=Binary)
        self.model.storage_discharge_binary = Var(self.model.STORAGES, self.model.TIME, within=Binary)

        self.model.investment = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.annuity = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_annuity = Var(bounds=(0, None))
        self.model.fixed_om_costs = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_fixed_om_costs = Var(bounds=(0, None))
        self.model.variable_om_costs = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_variable_om_costs = Var(bounds=(0, None))
        self.model.purchase_costs = Var(self.model.PURCHASABLE_STREAMS, bounds=(0, None))
        self.model.total_purchase_costs = Var(bounds=(0, None))
        self.model.revenue = Var(self.model.SALEABLE_STREAMS, bounds=(None, None))
        self.model.total_revenue = Var(bounds=(None, None))

    def attach_scalable_component_variables_to_optimization_problem(self):

        def set_scalable_component_capacity_bound_rule(model, s, i):
            return 0, self.scaling_capex_upper_bound_dict[(s, i)]

    def attach_commodity_variables_to_optimization_problem(self, model):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        self.model.mass_energy_component_in_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                                              self.model.TIME, bounds=(0, None))
        self.model.mass_energy_component_out_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                                               self.model.TIME, bounds=(0, None))

        # Freely available commodities
        self.model.mass_energy_available = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_emitted = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Charged and discharged commodities
        self.model.mass_energy_storage_in_commodities = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_storage_out_commodities = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.soc = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # sold and purchased commodities
        self.model.mass_energy_sell_commodity = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_purchase_commodity = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # generated commodities
        self.model.mass_energy_generation = Var(self.model.GENERATORS, self.model.ME_STREAMS, self.model.TIME,
                                                bounds=(0, None))
        self.model.mass_energy_total_generation = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Demanded commodities
        self.model.mass_energy_demand = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Hot standby demand
        self.model.mass_energy_hot_standby_demand = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                                        self.model.TIME, bounds=(0, None))

    def attach_purchase_price_time_series_to_optimization_problem(self):
        self.model.purchase_price = Param(self.model.PURCHASABLE_STREAMS, self.model.TIME,
                                          initialize=self.purchase_price_dict)

    def attach_sale_price_time_series_to_optimization_problem(self):
        self.model.selling_price = Param(self.model.SALEABLE_STREAMS, self.model.TIME, initialize=self.sell_price_dict)

    def attach_demand_time_series_to_optimization_problem(self):
        self.model.commodity_demand = Param(self.model.DEMANDED_STREAMS, self.model.TIME, initialize=self.demand_dict)

    def attach_generation_time_series_to_optimization_problem(self):
        self.model.generation_profiles = Param(self.model.GENERATORS, self.model.TIME,
                                               initialize=self.generation_profiles_dict)

    def attach_weightings_time_series_to_optimization_problem(self):
        self.model.weightings = Param(self.model.TIME, initialize=self.weightings_dict)

    def attach_weightings_time_series_to_optimization_problem(self, model):
        model.weightings = Param(model.TIME, initialize=self.weightings_dict)
        return model

    def attach_constraints(self, model):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

        def _mass_energy_balance_rule(m, me_out, t, i):
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased commodities
            #   = emitted, sold, demanded, charged and used (in) commodities
            commodity_object = pm_object.get_commodity(me_out)
            equation_lhs = []
            equation_rhs = []

            if commodity_object.is_available():
                equation_lhs.append(m.mass_energy_available[me_out, t, i])
            if commodity_object.is_emittable():
                equation_lhs.append(-m.mass_energy_emitted[me_out, t, i])
            if commodity_object.is_purchasable():
                equation_lhs.append(m.mass_energy_purchase_commodity[me_out, t, i])
            if commodity_object.is_saleable():
                equation_lhs.append(-m.mass_energy_sell_commodity[me_out, t, i])
            if commodity_object.is_demanded():
                equation_lhs.append(-m.mass_energy_demand[me_out, t, i])
            if me_out in m.STORAGES:
                equation_lhs.append(
                    m.mass_energy_storage_out_commodities[me_out, t, i] - m.mass_energy_storage_in_commodities[
                        me_out, t, i])
            if me_out in m.GENERATED_COMMODITIES:
                equation_lhs.append(m.mass_energy_total_generation[me_out, t, i])

            for c in m.CONVERSION_COMPONENTS:
                if (c, me_out) in self.output_tuples:
                    equation_lhs.append(m.mass_energy_component_out_commodities[c, me_out, t, i])

                if (c, me_out) in self.input_tuples:
                    equation_rhs.append(m.mass_energy_component_in_commodities[c, me_out, t, i])

            return sum(equation_lhs) == sum(equation_rhs)

        model._mass_energy_balance_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                    rule=_mass_energy_balance_rule)

        def _set_available_commodities_rule(m, me, t, i):
            # Sets commodities, which are available without limit and price
            if me in m.AVAILABLE_COMMODITIES:
                return m.mass_energy_available[me, t, i] >= 0
            else:
                return m.mass_energy_available[me, t, i] == 0

        model.set_available_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                         rule=_set_available_commodities_rule)

        def _set_emitted_commodities_rule(m, me, t, i):
            # Sets commodities, which are emitted without limit and price
            if me in m.EMITTED_COMMODITIES:
                return m.mass_energy_emitted[me, t, i] >= 0
            else:
                return m.mass_energy_emitted[me, t, i] == 0

        model.set_emitted_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                       rule=_set_emitted_commodities_rule)

        def _set_saleable_commodities_rule(m, me, t, i):
            # Sets commodities, which are sold without limit but for a certain price
            if me in m.SALEABLE_COMMODITIES:
                return m.mass_energy_sell_commodity[me, t, i] >= 0
            else:
                return m.mass_energy_sell_commodity[me, t, i] == 0

        model.set_saleable_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                        rule=_set_saleable_commodities_rule)

        def _set_purchasable_commodities_rule(m, me, t, i):
            # Sets commodities, which are purchased without limit but for a certain price
            if me in m.PURCHASABLE_COMMODITIES:
                return m.mass_energy_purchase_commodity[me, t, i] >= 0
            else:
                return m.mass_energy_purchase_commodity[me, t, i] == 0

        model.set_purchasable_commodities_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                           rule=_set_purchasable_commodities_rule)

        def _total_demand_satisfaction_rule(m, me, i):
            if me in m.TOTAL_DEMANDED_COMMODITIES:
                return sum(m.mass_energy_demand[me, t, i] * m.weightings[t] for t in m.TIME) \
                       >= m.commodity_demand[me, 0]
            else:
                return Constraint.Skip

        model.total_demand_satisfaction_con = Constraint(model.TOTAL_DEMANDED_COMMODITIES, model.ITERATION,
                                                         rule=_total_demand_satisfaction_rule)

        def _commodity_conversion_output_rule(m, c, me_out, t, i):
            # Define ratio between main input and output commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, me_out) in self.output_conversion_tuples:
                return m.mass_energy_component_out_commodities[c, me_out, t, i] == \
                       m.mass_energy_component_in_commodities[c, main_input, t, i] \
                       * self.output_conversion_tuples_dict[c, main_input, me_out]
            else:
                return m.mass_energy_component_out_commodities[c, me_out, t, i] == 0

        model._commodity_conversion_output_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                            model.TIME, model.ITERATION,
                                                            rule=_commodity_conversion_output_rule)

        def _commodity_conversion_input_rule(m, c, me_in, t, i):
            # Define ratio between main input and other input commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return Constraint.Skip
            else:
                if (c, main_input, me_in) in self.input_conversion_tuples:
                    return m.mass_energy_component_in_commodities[c, me_in, t, i] == \
                           m.mass_energy_component_in_commodities[c, main_input, t, i] \
                           * self.input_conversion_tuples_dict[c, main_input, me_in]
                else:
                    return m.mass_energy_component_in_commodities[c, me_in, t, i] == 0

        model._commodity_conversion_input_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                           model.TIME, model.ITERATION,
                                                           rule=_commodity_conversion_input_rule)

        def _conversion_maximal_component_capacity_rule(m, c, me_in, t, i):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t, i] <= m.nominal_cap[c] * m.max_p[c]
            else:
                return Constraint.Skip

        model._conversion_maximal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                                      model.TIME, model.ITERATION,
                                                                      rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(m, c, me_in, t, i):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t, i] \
                       >= m.nominal_cap[c] * m.min_p[c]
            else:
                return Constraint.Skip

        model._conversion_minimal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                                      model.TIME, model.ITERATION,
                                                                      rule=_conversion_minimal_component_capacity_rule)

        def _ramp_up_rule(m, c, me_in, t, i):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t, i]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1, i]) <= \
                           m.nominal_cap[c] * m.ramp_up[c]
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip

        model._ramp_up_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                        rule=_ramp_up_rule)

        def _ramp_down_rule(m, c, me_in, t, i):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t, i]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1, i]) >= \
                           - (m.nominal_cap[c] * m.ramp_down[c])
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip

        model._ramp_down_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES, model.TIME,
                                          model.ITERATION,
                                          rule=_ramp_down_rule)

        """ Generation constraints """

        def power_generation_rule(m, g, me, t, i):
            if me == pm_object.get_component(g).get_generated_commodity():
                if pm_object.get_component(g).get_curtailment_possible():
                    return m.mass_energy_generation[g, me, t, i] <= m.generation_profiles[g, t, i] * m.nominal_cap[g]
                else:
                    return m.mass_energy_generation[g, me, t, i] == m.generation_profiles[g, t, i] * m.nominal_cap[g]
            else:
                return m.mass_energy_generation[g, me, t, i] == 0

        model.power_generation_con = Constraint(model.GENERATORS, model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                rule=power_generation_rule)

        def attach_fixed_capacity_rule(m, g):
            if pm_object.get_component(g).get_has_fixed_capacity():
                return m.nominal_cap[g] == m.generator_fixed_capacity[g]
            else:
                return Constraint.Skip

        model.attach_fixed_capacity_con = Constraint(model.GENERATORS, rule=attach_fixed_capacity_rule)

        def total_power_generation_rule(m, me, t, i):
            return m.mass_energy_total_generation[me, t, i] == sum(m.mass_energy_generation[g, me, t, i]
                                                                   for g in m.GENERATORS)

        model.total_power_generation_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                      rule=total_power_generation_rule)

        def storage_balance_rule(m, me, t, i):
            if me in m.STORAGES:
                if t == 0:
                    return Constraint.Skip
                else:
                    return m.soc[me, t, i] == m.soc[me, t - 1, i] \
                           + m.mass_energy_storage_in_commodities[me, t - 1, i] * m.charging_efficiency[me] \
                           - m.mass_energy_storage_out_commodities[me, t - 1, i] / m.discharging_efficiency[me]
            else:
                return m.soc[me, t, i] == 0

        model.storage_balance_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                               rule=storage_balance_rule)

        def last_soc_rule(m, me, t, i):
            if t == max(m.TIME):
                return m.soc[me, 0, i] == m.soc[me, t, i] \
                       + m.mass_energy_storage_in_commodities[me, t, i] * m.charging_efficiency[me] \
                       - m.mass_energy_storage_out_commodities[me, t, i] / m.discharging_efficiency[me]
            else:
                return Constraint.Skip

        model.last_soc_con = Constraint(model.STORAGES, model.TIME, model.ITERATION, rule=last_soc_rule)

        def soc_max_bound_rule(m, me, t, i):
            return m.soc[me, t, i] <= m.maximal_soc[me] * m.nominal_cap[me]

        model.soc_max = Constraint(model.STORAGES, model.TIME, model.ITERATION, rule=soc_max_bound_rule)

        def soc_min_bound_rule(m, me, t, i):
            return m.soc[me, t, i] >= m.minimal_soc[me] * m.nominal_cap[me]

        model.soc_min = Constraint(model.STORAGES, model.TIME, model.ITERATION, rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(m, me, t, i):
            if me in m.STORAGES:
                return m.mass_energy_storage_in_commodities[me, t, i] <= m.nominal_cap[me] / \
                       m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_in_commodities[me, t, i] == 0

        model.storage_charge_upper_bound_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                          rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(m, me, t, i):
            if me in m.STORAGES:
                return m.mass_energy_storage_out_commodities[me, t, i] / m.discharging_efficiency[me] \
                       <= m.nominal_cap[me] / m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_out_commodities[me, t, i] == 0

        model.storage_discharge_upper_bound_con = Constraint(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                             rule=storage_discharge_upper_bound_rule)

        def define_upper_limit_mu_rule(m, i):
            return m.auxiliary_variable >= \
                   + sum(m.mass_energy_storage_in_commodities[c, t, i] * m.variable_om[c]
                         for t in m.TIME for c in m.STORAGES) \
                   + sum(m.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), t, i]
                         * m.variable_om[c] for t in m.TIME for c in m.CONVERSION_COMPONENTS) \
                   + sum(m.mass_energy_generation[c, pm_object.get_component(c).get_generated_commodity(), t, i]
                         * m.variable_om[c]
                         for t in m.TIME for c in m.GENERATORS) \
                   + sum(m.mass_energy_purchase_commodity[me, t, i] * m.purchase_price[me, t] * m.weightings[t]
                         for t in m.TIME for me in m.ME_COMMODITIES if me in self.purchasable_commodities) \
                   - sum(m.mass_energy_sell_commodity[me, t, i] * m.selling_price[me, t] * m.weightings[t]
                         for t in m.TIME for me in m.ME_COMMODITIES if me in self.saleable_commodities)

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

        opt.options["mipgap"] = 0.01
        if instance is None:
            instance = self.model.create_instance()
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

        return self.model

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
        self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, uncertainty, iteration):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.uncertainty = uncertainty

        self.optimal_capacities = None
        self.obj_value = None
        self.auxiliary_variable = None

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
        self.minimal_power_dict, \
        self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
        self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, \
        self.shut_down_down_time_dict, self.shut_down_start_up_costs, self.standby_down_time_dict, \
        self.charging_efficiency_dict, self.discharging_efficiency_dict, \
        self.minimal_soc_dict, self.maximal_soc_dict, \
        self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components, \
        self.no_shut_down_components, self.standby_components, \
        self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
        self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities \
            = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
        self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        # Create optimization program
        self.model = ConcreteModel()
        self.model.TIME = RangeSet(0, self.pm_object.get_time_steps() - 1)
        self.model.ITERATION = RangeSet(0, iteration)
        self.model = self.attach_weightings_time_series_to_optimization_problem(self.model)
        self.model.INTEGER_STEPS = RangeSet(0, self.pm_object.integer_steps)
        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.model.M = Param(initialize=1000000000)

        # Attach Sets
        self.model = self.attach_component_sets_to_optimization_problem(self.model)
        self.model = self.attach_commodity_sets_to_optimization_problem(self.model)

        # Attach Parameters
        self.model = self.attach_component_parameters_to_optimization_problem(self.model)
        self.model = self.attach_annuity_to_optimization_problem(self.model)

        # Attach Variables
        self.model = self.attach_component_variables_to_optimization_problem(self.model)
        self.model = self.attach_auxiliary_variables_to_optimization_problem(self.model)
        self.model = self.attach_commodity_variables_to_optimization_problem(self.model)
        self.model = self.attach_purchase_price_time_series_to_optimization_problem(self.model)
        self.model = self.attach_sale_price_time_series_to_optimization_problem(self.model)
        self.model = self.attach_demand_time_series_to_optimization_problem(self.model)
        self.model = self.attach_generation_time_series_to_optimization_problem(self.model)

        self.model = self.attach_constraints(self.model)


class SubOptimizationProblem:

    def attach_component_sets_to_optimization_problem(self, model):

        model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
        model.STORAGES = Set(initialize=self.storage_components)
        model.GENERATORS = Set(initialize=self.generator_components)
        model.COMPONENTS = Set(initialize=self.all_components)
        return model

    def attach_commodity_sets_to_optimization_problem(self, model):
        model.ME_COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
        model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
        model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
        model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
        model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
        model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
        model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
        model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)
        return model

    def attach_component_parameters_to_optimization_problem(self, model):
        model.variable_om = Param(model.COMPONENTS, initialize=self.variable_om_dict)

        model.min_p = Param(model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
        model.max_p = Param(model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)
        model.ramp_up = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
        model.ramp_down = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

        model.charging_efficiency = Param(model.STORAGES, initialize=self.charging_efficiency_dict)
        model.discharging_efficiency = Param(model.STORAGES, initialize=self.discharging_efficiency_dict)
        model.minimal_soc = Param(model.STORAGES, initialize=self.minimal_soc_dict)
        model.maximal_soc = Param(model.STORAGES, initialize=self.maximal_soc_dict)
        model.ratio_capacity_p = Param(model.STORAGES, initialize=self.ratio_capacity_power_dict)

        model.generator_fixed_capacity = Param(model.GENERATORS, initialize=self.fixed_capacity_dict)

        return model

    def attach_commodity_variables_to_optimization_problem(self, dual_model):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        dual_model.y_free_available_constraint_variable = Var(dual_model.AVAILABLE_COMMODITIES,
                                                              dual_model.TIME, bounds=(0, None))

        dual_model.y_purchase_constraint_variable = Var(dual_model.PURCHASABLE_COMMODITIES,
                                                        dual_model.TIME, bounds=(0, None))

        dual_model.y_emit_constraint_variable = Var(dual_model.EMITTED_COMMODITIES,
                                                    dual_model.TIME, bounds=(0, None))

        dual_model.y_sell_constraint_variable = Var(dual_model.SALEABLE_COMMODITIES,
                                                    dual_model.TIME, bounds=(0, None))

        dual_model.y_balance_constraint_variable = Var(dual_model.ME_COMMODITIES, dual_model.TIME,
                                                       bounds=(None, None))

        dual_model.y_demand_constraint_variable = Var(dual_model.DEMANDED_COMMODITIES, bounds=(None, None))

        dual_model.y_out_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                   dual_model.ME_COMMODITIES, dual_model.TIME,
                                                   bounds=(None, None))
        dual_model.y_in_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                  dual_model.ME_COMMODITIES, dual_model.TIME,
                                                  bounds=(None, None))
        dual_model.y_conv_cap_ub_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, bounds=(None, 0))
        dual_model.y_conv_cap_lb_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, bounds=(0, None))
        dual_model.y_conv_cap_ramp_up_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                dual_model.TIME, bounds=(None, 0))
        dual_model.y_conv_cap_ramp_down_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                  dual_model.TIME, bounds=(None, 0))

        dual_model.y_generation_constraint_variable = Var(dual_model.GENERATORS,
                                                          dual_model.ME_COMMODITIES,
                                                          dual_model.TIME, bounds=(None, 0))

        dual_model.y_soc_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                   bounds=(None, None))
        dual_model.y_soc_ub_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                      bounds=(None, 0))
        dual_model.y_soc_lb_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                      bounds=(None, 0))
        dual_model.y_soc_charge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                bounds=(None, 0))
        dual_model.y_soc_discharge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                   bounds=(None, 0))

        dual_model.uncertainty = Var(['Wind', 'Solar'], dual_model.TIME, bounds=(0, 1))

        return dual_model

    def attach_purchase_price_time_series_to_optimization_problem(self, model):
        model.purchase_price = Param(model.PURCHASABLE_COMMODITIES, model.TIME, initialize=self.purchase_price_dict)
        return model

    def attach_sale_price_time_series_to_optimization_problem(self, model):
        model.selling_price = Param(model.SALEABLE_COMMODITIES, model.TIME, initialize=self.sell_price_dict)
        return model

    def attach_demand_time_series_to_optimization_problem(self, model):
        model.commodity_demand = Param(model.DEMANDED_COMMODITIES, model.TIME, initialize=self.demand_dict)
        return model

    def attach_weightings_time_series_to_optimization_problem(self, model):
        model.weightings = Param(model.TIME, initialize=self.weightings_dict)
        return model

    def attach_uncertainty_set(self, model):

        if True:
            def overall_both_min_rule(dm):
                return sum(dm.uncertainty[g, t] for g in dm.GENERATORS for t in dm.TIME) \
                       >= self.kwargs['min_overall_value_both']

            model.overall_both_min_con = Constraint(rule=overall_both_min_rule)

            def overall_both_max_rule(dm):
                return sum(dm.uncertainty[g, t] for g in dm.GENERATORS for t in dm.TIME) \
                       <= self.kwargs['max_overall_value_both']

            model.overall_both_max_con = Constraint(rule=overall_both_max_rule)

            def overall_wind_min_rule(dm):
                return sum(dm.uncertainty['Wind', t] for t in dm.TIME) \
                       >= self.kwargs['min_overall_value_wind']

            model.overall_wind_min_con = Constraint(rule=overall_wind_min_rule)

            def overall_wind_max_rule(dm):
                return sum(dm.uncertainty['Wind', t] for t in dm.TIME) \
                       <= self.kwargs['max_overall_value_wind']

            model.overall_wind_max_con = Constraint(rule=overall_wind_max_rule)

            def overall_solar_min_rule(dm):
                return sum(dm.uncertainty['Solar', t] for t in dm.TIME) \
                       >= self.kwargs['min_overall_value_solar']

            model.overall_solar_min_con = Constraint(rule=overall_solar_min_rule)

            def overall_solar_max_rule(dm):
                return sum(dm.uncertainty['Solar', t] for t in dm.TIME) \
                       <= self.kwargs['max_overall_value_solar']

            model.overall_solar_max_con = Constraint(rule=overall_solar_max_rule)

        if True:
            def weekly_both_min_rule(dm):
                return sum(dm.uncertainty[g, t] for g in dm.GENERATORS for t in dm.TIME) / 168 \
                       >= self.kwargs['min_weekly_value_both']

            model.weekly_both_min_con = Constraint(rule=weekly_both_min_rule)

            def weekly_both_max_rule(dm):
                return sum(dm.uncertainty[g, t] for g in dm.GENERATORS for t in dm.TIME) / 168 \
                       <= self.kwargs['max_weekly_value_both']

            model.weekly_both_max_con = Constraint(rule=weekly_both_max_rule)

            def weekly_wind_min_rule(dm):
                return sum(dm.uncertainty['Wind', t] for t in dm.TIME) / 168 \
                       >= self.kwargs['min_weekly_value_wind']

            model.weekly_wind_min_con = Constraint(rule=weekly_wind_min_rule)

            def weekly_wind_max_rule(dm):
                return sum(dm.uncertainty['Wind', t] for t in dm.TIME) / 168 \
                       <= self.kwargs['max_weekly_value_wind']

            model.weekly_wind_max_con = Constraint(rule=weekly_wind_max_rule)

            def weekly_solar_min_rule(dm):
                return sum(dm.uncertainty['Solar', t] for t in dm.TIME) / 168 \
                       >= self.kwargs['min_weekly_value_solar']

            model.weekly_solar_min_con = Constraint(rule=weekly_solar_min_rule)

            def weekly_solar_max_rule(dm):
                return sum(dm.uncertainty['Solar', t] for t in dm.TIME) / 168 \
                       <= self.kwargs['max_weekly_value_solar']

            model.weekly_solar_max_con = Constraint(rule=weekly_solar_max_rule)

        return model

    def attach_constraints(self, model):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

        def x_free_rule(dm, s, t):  # x_free >= 0 --> constraint is <=
            if s in self.available_commodities:
                return dm.y_balance_constraint_variable[s, t] + self.dual_model.y_free_available_constraint_variable[
                    s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_free_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_free_rule)

        def x_emit_rule(dm, s, t):
            if s in self.emittable_commodities:
                return - dm.y_balance_constraint_variable[s, t] + self.dual_model.y_emit_constraint_variable[s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_emit_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_emit_rule)

        def x_buy_rule(dm, s, t):
            if s in self.purchasable_commodities:
                return dm.y_balance_constraint_variable[s, t] + dm.y_purchase_constraint_variable[s, t] \
                       <= self.purchase_price_dict[s, t] * self.weightings_dict[t]
            else:
                return Constraint.Skip

        self.dual_model.x_buy_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_buy_rule)

        def x_sell_rule(dm, s, t):
            if s in self.saleable_commodities:
                return - dm.y_balance_constraint_variable[s, t] + dm.y_sell_constraint_variable[s, t] \
                       <= - self.sell_price_dict[s, t] * self.weightings_dict[t]
            else:
                return Constraint.Skip

        self.dual_model.x_sell_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_sell_rule)

        def x_demand_rule(dm, s, t):
            if s in self.demanded_commodities:
                return - dm.y_balance_constraint_variable[s, t] \
                       + dm.y_demand_constraint_variable[s] * self.weightings_dict[t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_demand_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                  rule=x_demand_rule)

        def x_generation_rule(dm, g, s, t):
            generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
            if s == generated_commodity:
                return dm.y_balance_constraint_variable[s, t] \
                       + dm.y_generation_constraint_variable[g, s, t] <= dm.variable_om[g]
            else:
                return Constraint.Skip

        self.dual_model.x_generation_con = Constraint(self.dual_model.GENERATORS, self.dual_model.ME_COMMODITIES,
                                                      self.dual_model.TIME, rule=x_generation_rule)

        def x_in_rule(dm, c, s, t):
            main_input = pm_object.get_component(c).get_main_input()
            inputs = pm_object.get_component(c).get_inputs()

            if s in inputs:

                # balance and bounds
                if s == main_input:
                    lhs = [- dm.y_balance_constraint_variable[s, t]
                           + dm.y_conv_cap_ub_constraint_variable[c, t]
                           + dm.y_conv_cap_lb_constraint_variable[c, t]]

                    if t > 0:
                        lhs.append(+ dm.y_conv_cap_ramp_up_constraint_variable[c, t])
                        lhs.append(+ dm.y_conv_cap_ramp_down_constraint_variable[c, t])

                    if t < max(dm.TIME):  # consider ramping
                        lhs.append(- dm.y_conv_cap_ramp_up_constraint_variable[c, t + 1])
                        lhs.append(- dm.y_conv_cap_ramp_down_constraint_variable[c, t + 1])

                    for conversion in self.output_conversion_tuples:
                        output_commodity = conversion[2]
                        lhs.append(- dm.y_out_constraint_variable[c, output_commodity, t]
                                   * self.output_conversion_tuples_dict[c, main_input, output_commodity])

                    for conversion in self.input_conversion_tuples:
                        other_input_commodity = conversion[2]
                        lhs.append(- dm.y_in_constraint_variable[c, other_input_commodity, t]
                                   * self.input_conversion_tuples_dict[c, main_input, other_input_commodity])

                else:
                    lhs = [- dm.y_balance_constraint_variable[s, t]]

                    for conversion in self.input_conversion_tuples:
                        # input to input conversions only possible if s != main input
                        if s == conversion[2]:
                            lhs.append(+ dm.y_in_constraint_variable[c, s, t])

                return sum(lhs) <= dm.variable_om[c]

            else:
                return Constraint.Skip

        self.dual_model.x_in_con = Constraint(self.dual_model.CONVERSION_COMPONENTS, self.dual_model.ME_COMMODITIES,
                                              self.dual_model.TIME, rule=x_in_rule)

        def x_out_rule(dm, c, s, t):
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, s) in self.output_conversion_tuples:
                return dm.y_balance_constraint_variable[s, t] \
                       + dm.y_out_constraint_variable[c, s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_out_con = Constraint(self.dual_model.CONVERSION_COMPONENTS,
                                               self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                               rule=x_out_rule)

        if True:
            def x_charge_rule(dm, s, t):
                if s in self.storage_components:

                    lhs = [- dm.y_balance_constraint_variable[s, t] + dm.y_soc_charge_limit_constraint_variable[s, t]]

                    if t < max(dm.TIME):
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])
                    else:
                        lhs.append(- dm.y_soc_constraint_variable[s, t] * self.charging_efficiency_dict[s])

                    return sum(lhs) <= dm.variable_om[s]
                else:
                    return Constraint.Skip

            self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                      rule=x_charge_rule)

            def x_discharge_variable_rule(dm, s, t):

                if s in self.storage_components:

                    lhs = [
                        dm.y_balance_constraint_variable[s, t] + dm.y_soc_discharge_limit_constraint_variable[s, t]]

                    if t < max(dm.TIME):
                        lhs.append(dm.y_soc_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[s])
                    else:
                        lhs.append(dm.y_soc_constraint_variable[s, t] / self.discharging_efficiency_dict[s])

                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.x_discharge_variable_con = Constraint(self.dual_model.ME_COMMODITIES,
                                                                  self.dual_model.TIME,
                                                                  rule=x_discharge_variable_rule)

            def soc_rule(dm, s, t):
                if s in self.storage_components:

                    lhs = []
                    if t == max(dm.TIME):
                        lhs.append(- dm.y_soc_constraint_variable[s, 0]
                                   + dm.y_soc_constraint_variable[s, t]
                                   + dm.y_soc_ub_constraint_variable[s, t]
                                   - dm.y_soc_lb_constraint_variable[s, t])
                    else:
                        lhs.append(+ dm.y_soc_constraint_variable[s, t]
                                   - dm.y_soc_constraint_variable[s, t + 1]
                                   + dm.y_soc_ub_constraint_variable[s, t]
                                   - dm.y_soc_lb_constraint_variable[s, t])
                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.soc_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                 rule=soc_rule)

        if False:
            def objective_function(dm):
                return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t] * self.maximal_power_dict[c]
                             - dm.y_conv_cap_lb_constraint_variable[c, t] * self.minimal_power_dict[c]
                             + dm.y_conv_cap_ramp_up_constraint_variable[c, t] * self.ramp_up_dict[c]
                             + dm.y_conv_cap_ramp_down_constraint_variable[c, t] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS) \
                       + sum(dm.y_generation_constraint_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t]
                             * 1 * self.optimal_capacities[g] for t in dm.TIME for g in dm.GENERATORS) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t] * self.maximal_soc_dict[s]
                             - dm.y_soc_lb_constraint_variable[s, t] * self.minimal_soc_dict[s]
                             + dm.y_soc_charge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                             + dm.y_soc_discharge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s])
                             * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components)

        elif True:
            def objective_function(dm):

                return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t] * self.maximal_power_dict[c]
                              - dm.y_conv_cap_lb_constraint_variable[c, t] * self.minimal_power_dict[c]
                              + dm.y_conv_cap_ramp_up_constraint_variable[c, t] * self.ramp_up_dict[c]
                              + dm.y_conv_cap_ramp_down_constraint_variable[c, t] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS) \
                       + sum(dm.y_generation_constraint_variable[
                                 g, self.pm_object.get_component(g).get_generated_commodity(), t]
                             * dm.uncertainty[g, t] * self.optimal_capacities[g] for t in dm.TIME for g in dm.GENERATORS) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t] * self.maximal_soc_dict[s]
                              - dm.y_soc_lb_constraint_variable[s, t] * self.minimal_soc_dict[s]
                              + dm.y_soc_charge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                              + dm.y_soc_discharge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[
                                  s]) * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components)

        else:
            def objective_function(dm):
                return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t] * self.maximal_power_dict[c]
                             - dm.y_conv_cap_lb_constraint_variable[c, t] * self.minimal_power_dict[c]
                             + dm.y_conv_cap_ramp_up_constraint_variable[c, t] * self.ramp_up_dict[c]
                             + dm.y_conv_cap_ramp_down_constraint_variable[c, t] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t] * self.maximal_soc_dict[s]
                             - dm.y_soc_lb_constraint_variable[s, t] * self.minimal_soc_dict[s]
                             + dm.y_soc_charge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                             + dm.y_soc_discharge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s])
                             * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components)

        self.dual_model.obj = Objective(rule=objective_function, sense=maximize)

        return model

    def optimize(self):

        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        opt.options["mipgap"] = 0.05
        opt.options["NonConvex"] = 2
        instance = self.dual_model.create_instance()

        results = opt.solve(instance, tee=True)
        uncertainty_array = np.zeros([max(self.dual_model.TIME) + 1, 2])
        for v in instance.component_objects(Var):
            if str(v) == 'uncertainty':
                variable_dict = v.extract_values()
                for i in v.index_set():
                    if i[0] == 'Wind':
                        n = 0
                    else:
                        n = 1
                    uncertainty_array[i[1], n] = variable_dict[i]

        self.optimal_uncertainties = uncertainty_array
        self.obj_value = instance.obj()

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, optimal_capacities, **kwargs):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.optimal_capacities = optimal_capacities
        self.kwargs = kwargs

        self.obj_value = None
        self.optimal_uncertainties = None

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, self.maximal_power_dict, self.ramp_up_dict, \
            self.ramp_down_dict, self.scaling_capex_var_dict, self.scaling_capex_fix_dict, \
            self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, self.shut_down_down_time_dict, \
            self.shut_down_start_up_costs, self.standby_down_time_dict, self.charging_efficiency_dict, \
            self.discharging_efficiency_dict, self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components, \
            self.no_shut_down_components, self.standby_components, \
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities \
            = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        """ Update sets and parameters as not all components are used anymore """
        conversion_components_new = []
        for c in self.conversion_components:
            if self.optimal_capacities[c] > 0:
                conversion_components_new.append(c)
        self.conversion_components = conversion_components_new

        storage_components_new = []
        for s in self.storage_components:
            if self.optimal_capacities[s] > 0:
                storage_components_new.append(s)
        self.storage_components = storage_components_new

        generators_components_new = []
        for g in self.generator_components:
            if self.optimal_capacities[g] > 0:
                generators_components_new.append(g)
        self.generator_components = generators_components_new

        components_new = []
        variable_om_new = {}
        for c in self.all_components:
            if self.optimal_capacities[c] > 0:
                components_new.append(c)
                variable_om_new[c] = self.variable_om_dict[c]
        self.all_components = components_new
        self.variable_om_dict = variable_om_new

        minimal_power_new = {}
        maximal_power_new = {}
        ramp_up_new = {}
        ramp_down_new = {}
        for c in self.conversion_components:
            if self.optimal_capacities[c] > 0:
                minimal_power_new[c] = self.minimal_power_dict[c]
                maximal_power_new[c] = self.maximal_power_dict[c]
                ramp_up_new[c] = self.ramp_up_dict[c]
                ramp_down_new[c] = self.ramp_down_dict[c]
        self.minimal_power_dict = minimal_power_new
        self.maximal_power_dict = maximal_power_new
        self.ramp_up_dict = ramp_up_new
        self.ramp_down_dict = ramp_down_new

        charging_efficiency_new = {}
        discharging_efficiency_new = {}
        minimal_soc_new = {}
        maximal_soc_new = {}
        ratio_capacity_p_new = {}
        for s in self.storage_components:
            if self.optimal_capacities[s] > 0:
                charging_efficiency_new[s] = self.charging_efficiency_dict[s]
                discharging_efficiency_new[s] = self.discharging_efficiency_dict[s]
                minimal_soc_new[s] = self.minimal_soc_dict[s]
                maximal_soc_new[s] = self.maximal_soc_dict[s]
                ratio_capacity_p_new[s] = self.ratio_capacity_power_dict[s]
        self.charging_efficiency_dict = charging_efficiency_new
        self.discharging_efficiency_dict = discharging_efficiency_new
        self.minimal_soc_dict = minimal_soc_new
        self.maximal_soc_dict = maximal_soc_new
        self.ratio_capacity_power_dict = ratio_capacity_p_new

        fixed_capacities_new = {}
        for g in self.generator_components:
            if self.optimal_capacities[g] > 0:
                fixed_capacities_new[g] = self.fixed_capacity_dict[g]
        self.fixed_capacity_dict = fixed_capacities_new

        # Create optimization program
        self.dual_model = ConcreteModel()
        self.dual_model.TIME = RangeSet(0, self.pm_object.get_time_steps() - 1)
        self.dual_model = self.attach_weightings_time_series_to_optimization_problem(self.dual_model)

        # Attach Sets
        self.dual_model = self.attach_component_sets_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_commodity_sets_to_optimization_problem(self.dual_model)

        # Attach Parameters
        self.dual_model = self.attach_component_parameters_to_optimization_problem(self.dual_model)

        # Attach Variables
        self.dual_model = self.attach_purchase_price_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_sale_price_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_demand_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_commodity_variables_to_optimization_problem(self.dual_model)

        self.dual_model = self.attach_constraints(self.dual_model)
        self.dual_model = self.attach_uncertainty_set(self.dual_model)

        # print(self.instance.pprint())


class PrimalDispatch:

    def attach_component_sets_to_optimization_problem(self, model):
        model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
        model.STORAGES = Set(initialize=self.storage_components)
        model.GENERATORS = Set(initialize=self.generator_components)
        model.COMPONENTS = Set(initialize=self.all_components)
        return model

    def attach_commodity_sets_to_optimization_problem(self, model):
        model.ME_COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
        model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
        model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
        model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
        model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
        model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
        model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
        model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)
        return model

    def attach_component_parameters_to_optimization_problem(self, model):
        model.variable_om = Param(model.COMPONENTS, initialize=self.variable_om_dict)

        model.min_p = Param(model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
        model.max_p = Param(model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)

        model.ramp_up = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
        model.ramp_down = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

        model.charging_efficiency = Param(model.STORAGES, initialize=self.charging_efficiency_dict)
        model.discharging_efficiency = Param(model.STORAGES, initialize=self.discharging_efficiency_dict)

        model.minimal_soc = Param(model.STORAGES, initialize=self.minimal_soc_dict)
        model.maximal_soc = Param(model.STORAGES, initialize=self.maximal_soc_dict)

        model.ratio_capacity_p = Param(model.STORAGES, initialize=self.ratio_capacity_power_dict)

        model.generator_fixed_capacity = Param(model.GENERATORS, initialize=self.fixed_capacity_dict)
        return model

    def attach_component_variables_to_optimization_problem(self, model):
        # Component variables
        model.nominal_cap = Param(model.COMPONENTS, initialize=self.optimal_capacities)
        return model

    def attach_auxiliary_variables_to_optimization_problem(self, model):
        # Component variables
        model.auxiliary_variable = Var()
        return model

    def attach_commodity_variables_to_optimization_problem(self, model):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        model.mass_energy_component_in_commodities = Var(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                         model.TIME, bounds=(0, None))
        model.mass_energy_component_out_commodities = Var(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                          model.TIME, bounds=(0, None))

        # Freely available commodities
        model.mass_energy_available = Var(model.ME_COMMODITIES, model.TIME, bounds=(0, None))
        model.mass_energy_emitted = Var(model.ME_COMMODITIES, model.TIME, bounds=(0, None))

        # Charged and discharged commodities
        model.mass_energy_storage_in_commodities = Var(model.ME_COMMODITIES, model.TIME,
                                                       bounds=(0, None))
        model.mass_energy_storage_out_commodities = Var(model.ME_COMMODITIES, model.TIME,
                                                        bounds=(0, None))
        model.soc = Var(model.ME_COMMODITIES, model.TIME, bounds=(0, None))

        # sold and purchased commodities
        model.mass_energy_sell_commodity = Var(model.ME_COMMODITIES, model.TIME, bounds=(0, None))
        model.mass_energy_purchase_commodity = Var(model.ME_COMMODITIES, model.TIME, bounds=(0, None))

        # generated commodities
        model.mass_energy_generation = Var(model.GENERATORS, model.ME_COMMODITIES, model.TIME,
                                           bounds=(0, None))
        model.mass_energy_total_generation = Var(model.ME_COMMODITIES, model.TIME, bounds=(0, None))

        # Demanded commodities
        model.mass_energy_demand = Var(model.TOTAL_DEMANDED_COMMODITIES, model.TIME, bounds=(0, None))
        return model

    def attach_purchase_price_time_series_to_optimization_problem(self, model):
        model.purchase_price = Param(model.PURCHASABLE_COMMODITIES, model.TIME, initialize=self.purchase_price_dict)
        return model

    def attach_sale_price_time_series_to_optimization_problem(self, model):
        model.selling_price = Param(model.SALEABLE_COMMODITIES, model.TIME, initialize=self.sell_price_dict)
        return model

    def attach_demand_time_series_to_optimization_problem(self, model):
        model.commodity_demand = Param(model.DEMANDED_COMMODITIES, model.TIME, initialize=self.demand_dict)
        return model

    def attach_generation_time_series_to_optimization_problem(self, model):

        generation_profiles_dict = {}
        for k in [*self.uncertainty.keys()]:
            for ind in range(self.uncertainty[k].shape[0]):
                for c in range(self.uncertainty[k].shape[1]):

                    if c == 0:
                        g = 'Wind'
                    else:
                        g = 'Solar'

                    generation_profiles_dict[(g, ind)] = self.uncertainty[k][ind, c]

                if ind == max(model.TIME):
                    break

        model.generation_profiles = Param(model.GENERATORS, model.TIME,
                                          initialize=generation_profiles_dict)
        return model

    def attach_weightings_time_series_to_optimization_problem(self, model):
        model.weightings = Param(model.TIME, initialize=self.weightings_dict)
        return model

    def attach_constraints(self, model):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

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
            if me_out in m.GENERATED_STREAMS:
                equation_lhs.append(m.mass_energy_total_generation[me_out, t])

            for c in m.CONVERSION_COMPONENTS:
                if (c, me_out) in self.output_tuples:
                    equation_lhs.append(m.mass_energy_component_out_commodities[c, me_out, t])

                if (c, me_out) in self.input_tuples:
                    equation_rhs.append(m.mass_energy_component_in_commodities[c, me_out, t])

                # hot standby demand
                if c in m.STANDBY_COMPONENTS:
                    hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                    if me_out == hot_standby_commodity:
                        equation_rhs.append(m.mass_energy_hot_standby_demand[c, me_out, t])

            return sum(equation_lhs) == sum(equation_rhs)
        model._mass_energy_balance_con = Constraint(model.ME_STREAMS, model.TIME, rule=_mass_energy_balance_rule)

        def _set_available_commodities_rule(m, me, t):
            # Sets commodities, which are available without limit and price
            if me in m.AVAILABLE_STREAMS:
                return m.mass_energy_available[me, t] >= 0
            else:
                return m.mass_energy_available[me, t] == 0
        model.set_available_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_available_commodities_rule)

        def _set_emitted_commodities_rule(m, me, t):
            # Sets commodities, which are emitted without limit and price
            if me in m.EMITTED_STREAMS:
                return m.mass_energy_emitted[me, t] >= 0
            else:
                return m.mass_energy_emitted[me, t] == 0

        model.set_emitted_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_emitted_commodities_rule)

        def _set_saleable_commodities_rule(m, me, t):
            # Sets commodities, which are sold without limit but for a certain price
            if me in m.SALEABLE_STREAMS:
                return m.mass_energy_sell_commodity[me, t] >= 0
            else:
                return m.mass_energy_sell_commodity[me, t] == 0
        model.set_saleable_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_saleable_commodities_rule)

        def _set_purchasable_commodities_rule(m, me, t):
            # Sets commodities, which are purchased without limit but for a certain price
            if me in m.PURCHASABLE_STREAMS:
                return m.mass_energy_purchase_commodity[me, t] >= 0
            else:
                return m.mass_energy_purchase_commodity[me, t] == 0
        model.set_purchasable_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_purchasable_commodities_rule)

        def _demand_satisfaction_rule(m, me, t):
            # Sets commodities, which are demanded
            if me in m.DEMANDED_STREAMS:  # Case with demand
                if me not in m.TOTAL_DEMANDED_STREAMS:  # Case where demand needs to be satisfied in every t
                    return m.mass_energy_demand[me, t] >= m.commodity_demand[me, t]
                else:
                    return Constraint.Skip
            else:  # Case without demand
                return m.mass_energy_demand[me, t] == 0
        model.demand_satisfaction_con = Constraint(model.ME_STREAMS, model.TIME, rule=_demand_satisfaction_rule)

        def _total_demand_satisfaction_rule(m, me):
            return sum(m.mass_energy_demand[me, t] * m.weightings[t] for t in m.TIME) \
                       >= m.commodity_demand[me, 0]
        model.total_demand_satisfaction_con = Constraint(model.TOTAL_DEMANDED_STREAMS,
                                                         rule=_total_demand_satisfaction_rule)

        def capacity_binary_sum_rule(m, c):
            # For each component, only one capacity over all integer steps can be 1
            return sum(m.capacity_binary[c, i] for i in m.INTEGER_STEPS) <= 1  # todo: == 1?
        model.capacity_binary_sum_con = Constraint(model.SCALABLE_COMPONENTS, rule=capacity_binary_sum_rule)

        def capacity_binary_activation_rule(m, c, i):
            # Capacity binary will be 1 if the capacity of the integer step is higher than 0
            return m.capacity_binary[c, i] >= m.nominal_cap_pre[c, i] / 1000000  # big M
        model.capacity_binary_activation_con = Constraint(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                                          rule=capacity_binary_activation_rule)

        def set_lower_bound_rule(m, c, i):
            # capacity binary sets lower bound. Lower bound is not predefined as each capacity step can be 0
            # if capacity binary = 0 -> nominal_cap_pre has no lower bound
            # if capacity binary = 1 -> nominal_cap_pre needs to be at least lower bound

            return m.nominal_cap_pre[c, i] >= self.scaling_capex_lower_bound_dict[c, i] * m.capacity_binary[c, i]
        model.set_lower_bound_con = Constraint(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                               rule=set_lower_bound_rule)

        def final_capacity_rule(m, c):
            # Final capacity of component is sum of capacity over all integer steps
            return m.nominal_cap[c] == sum(m.nominal_cap_pre[c, i] for i in m.INTEGER_STEPS)
        model.final_capacity_con = Constraint(model.SCALABLE_COMPONENTS, rule=final_capacity_rule)

        def _commodity_conversion_output_rule(m, c, me_out, t):
            # Define ratio between main input and output commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, me_out) in self.output_conversion_tuples:
                return m.mass_energy_component_out_commodities[c, me_out, t] == \
                       m.mass_energy_component_in_commodities[c, main_input, t] \
                       * self.output_conversion_tuples_dict[c, main_input, me_out]
            else:
                return m.mass_energy_component_out_commodities[c, me_out, t] == 0
        model._commodity_conversion_output_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
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
        model._commodity_conversion_input_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                        rule=_commodity_conversion_input_rule)

        def balance_component_status_rule(m, c, t):
            # The component is either on, off or in hot standby
            return m.status_on[c, t] + m.status_off[c, t] + m.status_standby[c, t] == 1
        model.balance_component_status_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                        rule=balance_component_status_rule)

        def component_no_shutdown_or_standby_rule(m, c, t):
            # If component can not be shut off or put in hot standby, the status is always on
            if (c not in m.SHUT_DOWN_COMPONENTS) & (c not in m.STANDBY_COMPONENTS):
                return m.status_on[c, t] == 1
            elif c not in m.SHUT_DOWN_COMPONENTS:
                return m.status_off[c, t] == 0
            elif c not in m.STANDBY_COMPONENTS:
                return m.status_standby[c, t] == 0
            else:
                return Constraint.Skip
        model.component_no_shutdown_or_standby_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                                rule=component_no_shutdown_or_standby_rule)

        def _active_component_rule(m, c, me_in, t):
            # Set binary to 1 if component is active
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] \
                       - m.status_on[c, t] * 1000000 <= 0
            else:
                return Constraint.Skip
        model._active_component_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                 rule=_active_component_rule)

        def status_off_switch_rule(m, c, t):
            if t > 0:
                return m.status_off[c, t] == m.status_off[c, t - 1] + m.status_off_switch_on[c, t] \
                       - m.status_off_switch_off[c, t]
            else:
                return Constraint.Skip
        model.status_off_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                 rule=status_off_switch_rule)

        def balance_status_standby_switch_rule(m, c, t):
            return m.status_standby_switch_on[c, t] + m.status_standby_switch_off[c, t] <= 1
        model.balance_status_standby_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                             rule=balance_status_standby_switch_rule)

        def status_standby_switch_rule(m, c, t):
            if t > 0:
                return m.status_standby[c, t] == m.status_standby[c, t - 1] + m.status_standby_switch_on[c, t] \
                       - m.status_standby_switch_off[c, t]
            else:
                return Constraint.Skip
        model.status_standby_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                     rule=status_standby_switch_rule)

        def balance_status_off_switch_rule(m, c, t):
            return m.status_off_switch_on[c, t] + m.status_off_switch_off[c, t] <= 1
        model.balance_status_off_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                         rule=balance_status_off_switch_rule)

        def _conversion_maximal_component_capacity_rule(m, c, me_in, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] <= m.nominal_cap[c] * m.max_p[c]
            else:
                return Constraint.Skip
        model._conversion_maximal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS,
                                                                      model.TIME,
                                                                      rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] \
                       >= m.nominal_cap[c] * m.min_p[c] + (m.status_on[c, t] - 1) * 1000000
            else:
                return Constraint.Skip
        model._conversion_minimal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS,
                                                                      model.TIME,
                                                                      rule=_conversion_minimal_component_capacity_rule)

        def _ramp_up_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1]) <= \
                           m.nominal_cap[c] * m.ramp_up[c] + (m.status_off_switch_off[c, t] + m.status_standby_switch_off[c, t]) * 1000000
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip
        model._ramp_up_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME, rule=_ramp_up_rule)

        def _ramp_down_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1]) >= \
                           - (m.nominal_cap[c] * m.ramp_down[c] +
                              (m.status_off_switch_on[c, t] + m.status_standby_switch_on[c, t]) * 1000000)
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip
        model._ramp_down_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                          rule=_ramp_down_rule)

        if not self.pm_object.get_uses_representative_periods():

            def shut_off_downtime_adherence_rule(m, c, t):
                if m.down_time[c] + t > max(m.TIME):
                    dt = max(m.TIME) - t + 1
                else:
                    dt = m.down_time[c]

                if t > 0:
                    return (m.status_off[c, t] - m.status_off[c, t - 1]) - sum(m.status_off[c, t + i]
                                                                               for i in range(dt)) / dt <= 0
                else:
                    return Constraint.Skip

            model.shut_off_downtime_adherence_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
                                                               rule=shut_off_downtime_adherence_rule)

            def hot_standby_downtime_adherence_rule(m, c, t):
                if m.standby_time[c] + t > max(m.TIME):
                    st = max(m.TIME) - t + 1
                else:
                    st = m.standby_time[c]

                if t > 0:
                    return (m.status_standby[c, t] - m.status_standby[c, t - 1]) - sum(m.status_stanby[c, t + i]
                                                                                       for i in range(st)) / st <= 0

            model.hot_standby_downtime_adherence_con = Constraint(model.STANDBY_COMPONENTS, model.TIME,
                                                                  rule=hot_standby_downtime_adherence_rule)

        else:

            def shut_off_downtime_adherence_with_representative_periods_rule(m, c, t):
                period_length = self.pm_object.get_representative_periods_length()
                past_periods = floor(t / period_length)
                if period_length - (t - past_periods * period_length) < m.down_time[c]:
                    dt = int(period_length - (t - past_periods * period_length))
                else:
                    dt = int(m.down_time[c])

                if t > 0:
                    return (m.status_off[c, t] - m.status_off[c, t - 1]) - sum(m.status_off[c, t + i]
                                                                               for i in range(dt)) / dt <= 0
                else:
                    return Constraint.Skip

            model.shut_off_downtime_adherence_with_representative_periods_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                                                           model.TIME,
                                                                                           rule=shut_off_downtime_adherence_with_representative_periods_rule)

            def hot_standby_downtime_adherence_with_representative_periods_rule(m, c, t):
                # In case of representative periods, the component is in standby maximal until end of week
                period_length = self.pm_object.get_representative_periods_length()
                past_periods = floor(t / period_length)
                if period_length - (t - past_periods * period_length) < m.standby_time[c]:
                    st = int(period_length - (t - past_periods * period_length))
                else:
                    st = int(m.standby_time[c])

                return (st - m.status_standby_switch_on[c, t] * st) >= sum(m.status_on_switch_on[c, t + i]
                                                                           for i in range(0, st))
            model.hot_standby_downtime_adherence_with_representative_rule = Constraint(model.STANDBY_COMPONENTS,
                                                                                       model.TIME,
                                                                                       rule=hot_standby_downtime_adherence_with_representative_periods_rule)

        def lower_limit_hot_standby_demand_rule(m, c, me, t):
            # Defines demand for hot standby
            if c in m.STANDBY_COMPONENTS:
                hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
                if me == hot_standby_commodity:
                    return m.mass_energy_hot_standby_demand[c, me, t] \
                           >= m.nominal_cap[c] * hot_standby_demand + (m.status_standby[c, t] - 1) * 1000000
                else:
                    return m.mass_energy_hot_standby_demand[c, me, t] == 0
            else:
                return m.mass_energy_hot_standby_demand[c, me, t] == 0
        model.lower_limit_hot_standby_demand_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                  rule=lower_limit_hot_standby_demand_rule)

        def upper_limit_hot_standby_demand_rule(m, c, me, t):
            # Define that the hot standby demand is not higher than the capacity * demand per capacity
            hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
            if me == hot_standby_commodity:
                return m.mass_energy_hot_standby_demand[c, me, t] <= m.nominal_cap[c] * hot_standby_demand
            else:
                return Constraint.Skip
        model.upper_limit_hot_standby_demand_con = Constraint(model.STANDBY_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                              rule=upper_limit_hot_standby_demand_rule)

        def hot_standby_binary_activation_rule(m, c, me, t):
            # activates hot standby demand binary if component goes into hot standby
            hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            if me == hot_standby_commodity:
                return m.mass_energy_hot_standby_demand[c, me, t] <= m.status_standby[c, t] * 1000000
            else:
                return Constraint.Skip
        model.hot_standby_binary_activation_con = Constraint(model.STANDBY_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                             rule=hot_standby_binary_activation_rule)

        """ Generation constraints """
        def power_generation_rule(m, g, me, t):
            if me == pm_object.get_component(g).get_generated_commodity():
                if pm_object.get_component(g).get_curtailment_possible():
                    return m.mass_energy_generation[g, me, t] <= m.generation_profiles[g, t] * m.nominal_cap[g]
                else:
                    return m.mass_energy_generation[g, me, t] == m.generation_profiles[g, t] * m.nominal_cap[g]
            else:
                return m.mass_energy_generation[g, me, t] == 0
        model.power_generation_con = Constraint(model.GENERATORS, model.ME_STREAMS, model.TIME,
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
        model.total_power_generation_con = Constraint(model.ME_STREAMS, model.TIME, rule=total_power_generation_rule)

        if not self.pm_object.get_uses_representative_periods():

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

            model.storage_balance_con = Constraint(model.ME_STREAMS, model.TIME, rule=storage_balance_rule)

            def last_soc_rule(m, me, t):
                if t == max(m.TIME):
                    return m.soc[me, 0] == m.soc[me, t] \
                           + m.mass_energy_storage_in_commodities[me, t] * m.charging_efficiency[me] \
                           - m.mass_energy_storage_out_commodities[me, t] / m.discharging_efficiency[me]
                else:
                    return Constraint.Skip

            model.last_soc_con = Constraint(model.STORAGES, model.TIME, rule=last_soc_rule)

        else:
            def storage_balance_with_representative_periods_rule(m, me, t):
                # Defines the SOC of the storage unit
                if me in m.STORAGES:
                    period_length = self.pm_object.get_representative_periods_length()
                    if t % period_length == 0:  # First hours SOC are not defined
                        return Constraint.Skip
                    else:
                        return m.soc[me, t] == m.soc[me, t - 1] \
                               + m.mass_energy_storage_in_commodities[me, t - 1] * m.charging_efficiency[me] \
                               - m.mass_energy_storage_out_commodities[me, t - 1] / m.discharging_efficiency[me]
                else:
                    return m.soc[me, t] == 0

            model.storage_balance_with_representative_periods_con = Constraint(model.ME_STREAMS, model.TIME,
                                                                               rule=storage_balance_with_representative_periods_rule)

            def discharging_with_representative_periods_rule(m, me, t):
                # This constraint defines the discharging at time steps from the last hour in the previous repr. period
                # to the first hour of the following repr. period
                period_length = self.pm_object.get_representative_periods_length()
                if t > 0:
                    if t % period_length == 0:
                        return m.soc[me, t - 1] - m.minimal_soc[me] * m.nominal_cap[me] >= \
                               m.mass_energy_storage_out_commodities[me, t - 1] / m.discharging_efficiency[me]
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip

            model.discharging_with_representative_periods_con = Constraint(model.STORAGES, model.TIME,
                                                                           rule=discharging_with_representative_periods_rule)

            def charging_with_representative_periods_rule(m, me, t):
                # This constraint defines the charging at time steps from the last hour in the previous repr. period
                # to the first hour of the following repr. period
                period_length = self.pm_object.get_representative_periods_length()
                if t > 0:
                    if t % period_length == 0:
                        return m.maximal_soc[me] * m.nominal_cap[me] - m.soc[me, t - 1] >= \
                               m.mass_energy_storage_in_commodities[me, t - 1] * m.charging_efficiency[me]
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip

            model.charging_with_representative_periods_con = Constraint(model.STORAGES, model.TIME,
                                                                        rule=charging_with_representative_periods_rule)

            def last_soc_representative_periods_rule(m, me, t):
                period_length = self.pm_object.get_representative_periods_length()
                if t % period_length == 0:
                    return m.soc[me, t] == m.soc[me, t + period_length - 1] \
                           + m.mass_energy_storage_in_commodities[me, t + period_length - 1] * m.charging_efficiency[me] \
                           - m.mass_energy_storage_out_commodities[me, t + period_length - 1] / m.discharging_efficiency[me]
                else:
                    return Constraint.Skip

            model.last_soc_representative_periods_con = Constraint(model.STORAGES, model.TIME, rule=last_soc_representative_periods_rule)

        def soc_max_bound_rule(m, me, t):
            return m.soc[me, t] <= m.maximal_soc[me] * m.nominal_cap[me]

        model.soc_max = Constraint(model.STORAGES, model.TIME, rule=soc_max_bound_rule)

        def soc_min_bound_rule(m, me, t):
            return m.soc[me, t] >= m.minimal_soc[me] * m.nominal_cap[me]

        model.soc_min = Constraint(model.STORAGES, model.TIME, rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(m, me, t):
            if me in m.STORAGES:
                return m.mass_energy_storage_in_commodities[me, t] <= m.nominal_cap[me] / \
                           m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_in_commodities[me, t] == 0

        model.storage_charge_upper_bound_con = Constraint(model.ME_STREAMS, model.TIME,
                                                          rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(m, me, t):
            if me in m.STORAGES:
                return m.mass_energy_storage_out_commodities[me, t] / m.discharging_efficiency[me] \
                           <= m.nominal_cap[me] / m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_out_commodities[me, t] == 0

        model.storage_discharge_upper_bound_con = Constraint(model.ME_STREAMS, model.TIME,
                                                             rule=storage_discharge_upper_bound_rule)

        def storage_binary_sum_rule(m, s, t):
            return m.storage_charge_binary[s, t] + m.storage_discharge_binary[s, t] <= 1
        model.storage_binary_sum_con = Constraint(model.STORAGES, model.TIME, rule=storage_binary_sum_rule)

        def charge_binary_activation_rule(m, s, t):
            return m.mass_energy_storage_in_commodities[s, t] - m.storage_charge_binary[s, t] * 1000000 <= 0
        model.charge_binary_activation_con = Constraint(model.STORAGES, model.TIME, rule=charge_binary_activation_rule)

        def discharge_binary_activation_rule(m, s, t):
            return m.mass_energy_storage_out_commodities[s, t] - m.storage_discharge_binary[s, t] * 1000000 <= 0

        model.discharge_binary_activation_con = Constraint(model.STORAGES, model.TIME,
                                                           rule=discharge_binary_activation_rule)

        """ Financial constraints """
        def calculate_investment_scalable_components_rule(m, c):
            return m.investment[c] == sum(m.nominal_cap_pre[c, i] * m.capex_pre_var[c, i]
                                          + m.capex_pre_fix[c, i] * m.capacity_binary[c, i]
                                          for i in m.INTEGER_STEPS)
        model.calculate_investment_scalable_components_con = Constraint(model.SCALABLE_COMPONENTS,
                                                                        rule=calculate_investment_scalable_components_rule)

        def calculate_investment_not_scalable_components_rule(m, c):
            if c not in m.SCALABLE_COMPONENTS:
                return m.investment[c] == m.nominal_cap[c] * m.capex_var[c] + m.capex_fix[c]
            else:
                return Constraint.Skip
        model.calculate_investment_not_scalable_components_con = Constraint(model.COMPONENTS,
                                                                            rule=calculate_investment_not_scalable_components_rule)

        def calculate_annuity_of_component_rule(m, c):
            return m.annuity[c] == m.investment[c] * m.ANF[c]
        model.calculate_annuity_of_component_con = Constraint(model.COMPONENTS, rule=calculate_annuity_of_component_rule)

        def calculate_total_annuity_rule(m):
            return m.total_annuity == sum(m.annuity[c] for c in m.COMPONENTS)
        model.calculate_total_annuity_con = Constraint(rule=calculate_total_annuity_rule)

        def calculate_fixed_om_costs_of_component_rule(m, c):
            return m.fixed_om_costs[c] == m.investment[c] * m.fixed_om[c]
        model.calculate_fixed_om_costs_of_component_con = Constraint(model.COMPONENTS,
                                                                     rule=calculate_fixed_om_costs_of_component_rule)

        def calculate_total_fixed_om_cost_rule(m):
            return m.total_fixed_om_costs == sum(m.fixed_om_costs[c] for c in m.COMPONENTS)
        model.calculate_total_fixed_om_cost_con = Constraint(rule=calculate_total_fixed_om_cost_rule)

        def calculate_variable_om_costs_of_component_rule(m, c):
            # todo: Check how it is implemented for storages
            component = self.pm_object.get_component(c)
            if component.get_component_type() == 'storage':
                return m.variable_om_costs[c] == sum(
                    m.mass_energy_storage_in_commodities[c, t] * m.variable_om[c] for t in m.TIME)
            elif component.get_component_type() == 'conversion':
                commodity = component.get_main_output()
                return m.variable_om_costs[c] == sum(
                    m.mass_energy_component_out_commodities[c, commodity, t] * m.variable_om[c] for t in m.TIME)
            else:
                commodity = component.get_generated_commodity()
                return m.variable_om_costs[c] == sum(
                    m.mass_energy_generation[c, commodity, t] * m.variable_om[c] for t in m.TIME)

        model.calculate_variable_om_costs_of_component_con = Constraint(model.COMPONENTS,
                                                                     rule=calculate_variable_om_costs_of_component_rule)

        def calculate_total_variable_om_cost_rule(m):
            return m.total_variable_om_costs == sum(m.variable_om_costs[c] for c in m.COMPONENTS)
        model.calculate_total_variable_om_cost_con = Constraint(rule=calculate_total_variable_om_cost_rule)

        def calculate_purchase_costs_of_commodity_rule(m, me):
            return m.purchase_costs[me] == sum(m.mass_energy_purchase_commodity[me, t] * m.weightings[t]
                                               * m.purchase_price[me, t] for t in m.TIME)
        model.calculate_purchase_costs_of_commodity_con = Constraint(model.PURCHASABLE_STREAMS,
                                                                  rule=calculate_purchase_costs_of_commodity_rule)

        def calculate_total_purchase_costs_rule(m):
            return m.total_purchase_costs == sum(m.purchase_costs[me] for me in m.PURCHASABLE_STREAMS)
        model.calculate_total_purchase_costs_con = Constraint(rule=calculate_total_purchase_costs_rule)

        def calculate_revenue_of_commodity_rule(m, me):
            return m.revenue[me] == sum(m.mass_energy_sell_commodity[me, t] * m.weightings[t]
                                        * m.selling_price[me, t] for t in m.TIME)
        model.calculate_revenue_of_commodity_con = Constraint(model.SALEABLE_STREAMS,
                                                           rule=calculate_revenue_of_commodity_rule)

        def calculate_total_revenue_rule(m):
            return m.total_revenue == sum(m.revenue[me] for me in m.SALEABLE_STREAMS)
        model.calculate_total_revenue_con = Constraint(rule=calculate_total_revenue_rule)

        if not self.pm_object.get_uses_representative_periods():

            def set_start_up_costs_component_rule(m, c, t):
                return m.start_up_costs_component[c, t] >= m.start_up_costs[c] * m.nominal_cap[c] * m.weightings[t] \
                       + (m.status_off_switch_off[c, t] - 1) * 1000000
            model.set_start_up_costs_component_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
                                                                rule=set_start_up_costs_component_rule)

        else:
            def set_start_up_costs_component_using_representative_periods_rule(m, c, t):
                period_length = self.pm_object.get_representative_periods_length()
                if t % period_length != 0:
                    return m.start_up_costs_component[c, t] >= m.start_up_costs[c] * m.nominal_cap[c] * m.weightings[t] \
                           + (m.status_off_switch_off[c, t] - 1) * 1000000
                else:
                    return Constraint.Skip
            model.set_start_up_costs_component_using_representative_periods_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                                                             model.TIME,
                                                                                             rule=set_start_up_costs_component_using_representative_periods_rule)

        def calculate_total_start_up_costs_of_component_rule(m, c):
            return m.total_start_up_costs_component[c] == sum(m.start_up_costs_component[c, t] for t in m.TIME)
        model.calculate_total_start_up_costs_of_component_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                                           rule=calculate_total_start_up_costs_of_component_rule)

        def calculate_total_start_up_costs_rule(m):
            return m.total_start_up_costs == sum(m.total_start_up_costs_component[c] for c in m.SHUT_DOWN_COMPONENTS)
        model.calculate_total_start_up_costs_con = Constraint(rule=calculate_total_start_up_costs_rule)

        def objective_function(m):
            return (m.total_annuity
                    + m.total_fixed_om_costs
                    + m.total_variable_om_costs
                    + m.total_purchase_costs
                    - m.total_revenue
                    + m.total_start_up_costs)
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
        self.obj_value = instance.obj()

        return self.model

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
        self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, uncertainty, optimal_capacities):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.uncertainty = uncertainty
        self.optimal_capacities = optimal_capacities
        self.obj_value = None

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, \
            self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
            self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, \
            self.shut_down_down_time_dict, self.shut_down_start_up_costs, self.standby_down_time_dict, \
            self.charging_efficiency_dict, self.discharging_efficiency_dict, \
            self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components, \
            self.no_shut_down_components, self.standby_components, \
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities,\
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities\
            = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        # Create optimization program
        self.model = ConcreteModel()
        self.model.TIME = RangeSet(0, self.pm_object.get_time_steps() - 1)
        self.attach_weightings_time_series_to_optimization_problem()
        self.model.INTEGER_STEPS = RangeSet(0, self.pm_object.integer_steps)
        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.model.M = Param(initialize=1000000000)

        # Attach Sets
        self.model = self.attach_component_sets_to_optimization_problem(self.model)
        self.model = self.attach_commodity_sets_to_optimization_problem(self.model)

        # Attach Parameters
        self.model = self.attach_component_parameters_to_optimization_problem(self.model)

        # Attach Variables
        self.model = self.attach_component_variables_to_optimization_problem(self.model)
        self.model = self.attach_auxiliary_variables_to_optimization_problem(self.model)
        self.model = self.attach_commodity_variables_to_optimization_problem(self.model)
        self.model = self.attach_purchase_price_time_series_to_optimization_problem(self.model)
        self.model = self.attach_sale_price_time_series_to_optimization_problem(self.model)
        self.model = self.attach_demand_time_series_to_optimization_problem(self.model)
        self.model = self.attach_generation_time_series_to_optimization_problem(self.model)

        self.model = self.attach_constraints(self.model)


class FullDualModel:

    def attach_component_sets_to_optimization_problem(self, model):
        model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
        model.STORAGES = Set(initialize=self.storage_components)
        model.GENERATORS = Set(initialize=self.generator_components)
        model.COMPONENTS = Set(initialize=self.all_components)
        return model

    def attach_commodity_sets_to_optimization_problem(self, model):
        model.ME_COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
        model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
        model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
        model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
        model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
        model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
        model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
        model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)
        return model

    def attach_annuity_to_optimization_problem(self, model):
        model.ANF = Param(model.COMPONENTS, initialize=self.annuity_factor_dict)
        return model

    def attach_component_parameters_to_optimization_problem(self, model):
        model.lifetime = Param(model.COMPONENTS, initialize=self.lifetime_dict)
        model.fixed_om = Param(model.COMPONENTS, initialize=self.fixed_om_dict)
        model.variable_om = Param(model.COMPONENTS, initialize=self.variable_om_dict)

        model.capex_var = Param(model.COMPONENTS, initialize=self.capex_var_dict)
        model.capex_fix = Param(model.COMPONENTS, initialize=self.capex_fix_dict)

        model.min_p = Param(model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
        model.max_p = Param(model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)

        model.ramp_up = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
        model.ramp_down = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

        model.charging_efficiency = Param(model.STORAGES, initialize=self.charging_efficiency_dict)
        model.discharging_efficiency = Param(model.STORAGES, initialize=self.discharging_efficiency_dict)

        model.minimal_soc = Param(model.STORAGES, initialize=self.minimal_soc_dict)
        model.maximal_soc = Param(model.STORAGES, initialize=self.maximal_soc_dict)

        model.ratio_capacity_p = Param(model.STORAGES, initialize=self.ratio_capacity_power_dict)

        model.generator_fixed_capacity = Param(model.GENERATORS, initialize=self.fixed_capacity_dict)
        return model

    def attach_component_variables_to_optimization_problem(self, model):
        # Component variables
        model.nominal_cap = Var(model.COMPONENTS, bounds=(0, None))
        return model
    def attach_commodity_variables_to_optimization_problem(self, dual_model):
        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        dual_model.y_free_available_constraint_variable = Var(dual_model.AVAILABLE_COMMODITIES,
                                                              dual_model.TIME, bounds=(0, None))

        dual_model.y_purchase_constraint_variable = Var(dual_model.PURCHASABLE_COMMODITIES,
                                                        dual_model.TIME, bounds=(0, None))

        dual_model.y_emit_constraint_variable = Var(dual_model.EMITTED_COMMODITIES,
                                                    dual_model.TIME, bounds=(0, None))

        dual_model.y_sell_constraint_variable = Var(dual_model.SALEABLE_COMMODITIES,
                                                    dual_model.TIME, bounds=(0, None))

        dual_model.y_balance_constraint_variable = Var(dual_model.ME_COMMODITIES, dual_model.TIME,
                                                       bounds=(None, None))

        dual_model.y_demand_constraint_variable = Var(dual_model.DEMANDED_COMMODITIES, bounds=(None, None))

        dual_model.y_out_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                   dual_model.ME_COMMODITIES, dual_model.TIME,
                                                   bounds=(None, None))
        dual_model.y_in_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                  dual_model.ME_COMMODITIES, dual_model.TIME,
                                                  bounds=(None, None))
        dual_model.y_conv_cap_ub_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, bounds=(None, 0))
        dual_model.y_conv_cap_lb_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, bounds=(None, 0))
        dual_model.y_conv_cap_ramp_up_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                dual_model.TIME, bounds=(None, 0))
        dual_model.y_conv_cap_ramp_down_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                  dual_model.TIME, bounds=(None, 0))

        dual_model.y_generation_constraint_variable = Var(dual_model.GENERATORS,
                                                          dual_model.ME_COMMODITIES,
                                                          dual_model.TIME, bounds=(None, 0))

        dual_model.y_soc_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                   bounds=(None, None))
        dual_model.y_soc_ub_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                      bounds=(None, 0))
        dual_model.y_soc_lb_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                      bounds=(None, 0))
        dual_model.y_soc_charge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                bounds=(None, 0))
        dual_model.y_soc_discharge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                   bounds=(None, 0))

        return dual_model

    def attach_purchase_price_time_series_to_optimization_problem(self, model):
        model.purchase_price = Param(model.PURCHASABLE_COMMODITIES, model.TIME, initialize=self.purchase_price_dict)
        return model

    def attach_sale_price_time_series_to_optimization_problem(self, model):
        model.selling_price = Param(model.SALEABLE_COMMODITIES, model.TIME, initialize=self.sell_price_dict)
        return model

    def attach_demand_time_series_to_optimization_problem(self, model):
        model.commodity_demand = Param(model.DEMANDED_COMMODITIES, model.TIME, initialize=self.demand_dict)
        return model

    def attach_generation_time_series_to_optimization_problem(self, model):
        generation_profiles_dict = {}
        for k in [*self.uncertainty.keys()]:
            for ind in range(self.uncertainty[k].shape[0]):
                for c in range(self.uncertainty[k].shape[1]):

                    if c == 0:
                        g = 'Wind'
                    else:
                        g = 'Solar'

                    generation_profiles_dict[(g, ind)] = self.uncertainty[k][ind, c]

                if ind == max(model.TIME):
                    break

        model.generation_profiles = Param(model.GENERATORS, model.TIME,
                                          initialize=generation_profiles_dict)
        return model

    def attach_weightings_time_series_to_optimization_problem(self, model):
        model.weightings = Param(model.TIME, initialize=self.weightings_dict)
        return model

    def attach_constraints(self, model):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

        def x_free_rule(dm, s, t):  # x_free >= 0 --> constraint is <=
            if s in self.available_commodities:
                return dm.y_balance_constraint_variable[s, t] + self.dual_model.y_free_available_constraint_variable[
                    s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_free_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_free_rule)

        def x_emit_rule(dm, s, t):
            if s in self.emittable_commodities:
                return - dm.y_balance_constraint_variable[s, t] + self.dual_model.y_emit_constraint_variable[s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_emit_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_emit_rule)

        def x_buy_rule(dm, s, t):
            if s in self.purchasable_commodities:
                return dm.y_balance_constraint_variable[s, t] + dm.y_purchase_constraint_variable[s, t] \
                       <= self.purchase_price_dict[s, t] * self.weightings_dict[t]
            else:
                return Constraint.Skip

        self.dual_model.x_buy_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_buy_rule)

        def x_sell_rule(dm, s, t):
            if s in self.saleable_commodities:
                return - dm.y_balance_constraint_variable[s, t] + dm.y_sell_constraint_variable[s, t] \
                       <= - self.sell_price_dict[s, t] * self.weightings_dict[t]
            else:
                return Constraint.Skip

        self.dual_model.x_sell_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_sell_rule)

        def x_demand_rule(dm, s, t):
            if s in self.demanded_commodities:
                return - dm.y_balance_constraint_variable[s, t] \
                       + dm.y_demand_constraint_variable[s] * self.weightings_dict[t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_demand_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                  rule=x_demand_rule)

        def x_generation_rule(dm, g, s, t):
            generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
            if s == generated_commodity:
                return dm.y_balance_constraint_variable[s, t] \
                       + dm.y_generation_constraint_variable[g, s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_generation_con = Constraint(self.dual_model.GENERATORS, self.dual_model.ME_COMMODITIES,
                                                      self.dual_model.TIME, rule=x_generation_rule)

        def x_in_rule(dm, c, s, t):
            main_input = pm_object.get_component(c).get_main_input()
            inputs = pm_object.get_component(c).get_inputs()

            if s in inputs:

                # balance and bounds
                if s == main_input:
                    lhs = [- dm.y_balance_constraint_variable[s, t]
                           + dm.y_conv_cap_ub_constraint_variable[c, t]
                           - dm.y_conv_cap_lb_constraint_variable[c, t]]

                    if t > 0:  # consider ramping
                        lhs.append(+ dm.y_conv_cap_ramp_up_constraint_variable[c, t])
                        lhs.append(- dm.y_conv_cap_ramp_up_constraint_variable[c, t - 1])
                        lhs.append(- dm.y_conv_cap_ramp_down_constraint_variable[c, t])
                        lhs.append(+ dm.y_conv_cap_ramp_down_constraint_variable[c, t - 1])

                    for conversion in self.output_conversion_tuples:
                        output_commodity = conversion[2]
                        lhs.append(- dm.y_out_constraint_variable[c, output_commodity, t]
                                   * self.output_conversion_tuples_dict[c, main_input, output_commodity])

                    for conversion in self.input_conversion_tuples:
                        other_input_commodity = conversion[2]
                        lhs.append(- dm.y_in_constraint_variable[c, other_input_commodity, t]
                                   * self.input_conversion_tuples_dict[c, main_input, other_input_commodity])

                else:
                    lhs = [- dm.y_balance_constraint_variable[s, t]]

                    for conversion in self.input_conversion_tuples:
                        # input to input conversions only possible if s != main input
                        if s == conversion[2]:
                            lhs.append(+ dm.y_in_constraint_variable[c, s, t])

                return sum(lhs) <= 0

            else:
                return Constraint.Skip

        self.dual_model.x_in_con = Constraint(self.dual_model.CONVERSION_COMPONENTS, self.dual_model.ME_COMMODITIES,
                                              self.dual_model.TIME, rule=x_in_rule)

        def x_out_rule(dm, c, s, t):
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, s) in self.output_conversion_tuples:
                return dm.y_balance_constraint_variable[s, t] \
                       + dm.y_out_constraint_variable[c, s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_out_con = Constraint(self.dual_model.CONVERSION_COMPONENTS,
                                               self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                               rule=x_out_rule)

        if True:
            def x_charge_rule(dm, s, t):
                if s in self.storage_components:

                    lhs = [- dm.y_balance_constraint_variable[s, t] + dm.y_soc_charge_limit_constraint_variable[s, t]]

                    if t < max(dm.TIME):
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])
                    else:
                        lhs.append(- dm.y_soc_constraint_variable[s, t] * self.charging_efficiency_dict[s])

                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                      rule=x_charge_rule)

            if True:
                def x_discharge_variable_rule(dm, s, t):

                    if s in self.storage_components:

                        lhs = [
                            dm.y_balance_constraint_variable[s, t] + dm.y_soc_discharge_limit_constraint_variable[s, t]]

                        if t < max(dm.TIME):
                            lhs.append(dm.y_soc_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[s])
                        else:
                            lhs.append(dm.y_soc_constraint_variable[s, t] / self.discharging_efficiency_dict[s])

                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.x_discharge_variable_con = Constraint(self.dual_model.ME_COMMODITIES,
                                                                      self.dual_model.TIME,
                                                                      rule=x_discharge_variable_rule)

                def soc_rule(dm, s, t):
                    if s in self.storage_components:

                        lhs = []
                        if t == max(dm.TIME):
                            lhs.append(- dm.y_soc_constraint_variable[s, 0]
                                       + dm.y_soc_constraint_variable[s, t]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        else:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t]
                                       - dm.y_soc_constraint_variable[s, t + 1]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.soc_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                     rule=soc_rule)

        else:
            def x_charge_rule(dm, s, t):
                if s in self.storage_components:

                    period_length = self.pm_object.get_representative_periods_length() - 1
                    lhs = [- dm.y_balance_constraint_variable[s, t]
                           + dm.y_soc_charge_limit_constraint_variable[s, t]]

                    if (t % (period_length - 1) == 0) & (t > 0):
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s]
                                   + dm.y_soc_ub_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])
                    elif (t % period_length == 0) & (t > 0):
                        pass
                    else:
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])

                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                      rule=x_charge_rule)

            if True:
                def x_discharge_variable_rule(dm, s, t):
                    if s in self.storage_components:

                        period_length = self.pm_object.get_representative_periods_length() - 1
                        lhs = [+ dm.y_balance_constraint_variable[s, t]
                               + dm.y_soc_charge_limit_constraint_variable[s, t]]

                        if (t % (period_length - 1) == 0) & (t > 0):
                            lhs.append(+ dm.y_soc_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[s]
                                       + dm.y_soc_lb_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[
                                           s])
                        elif (t % period_length == 0) & (t > 0):
                            pass
                        else:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t + 1])

                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.x_discharge_variable_con = Constraint(self.dual_model.ME_COMMODITIES,
                                                                      self.dual_model.TIME,
                                                                      rule=x_discharge_variable_rule)

                def soc_rule(dm, s, t):
                    if s in self.storage_components:

                        lhs = []

                        period_length = self.pm_object.get_representative_periods_length() - 1
                        if t == 0:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t + period_length]
                                       - dm.y_soc_constraint_variable[s, t + 1]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        elif t % period_length != 0:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t]
                                       - dm.y_soc_constraint_variable[s, t + 1]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        else:
                            lhs.append(+ dm.y_soc_ub_constraint_variable[s, t - 1]
                                       - dm.y_soc_lb_constraint_variable[s, t - 1])
                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.soc_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                     rule=soc_rule)

        def cap_conv_rule(dm, c):
            return sum(- dm.y_conv_cap_ub_constraint_variable[c, t] * self.maximal_power_dict[c]
                       + dm.y_conv_cap_lb_constraint_variable[c, t] * self.minimal_power_dict[c]
                       - dm.y_conv_cap_ramp_up_constraint_variable[c, t] * self.ramp_up_dict[c]
                       - dm.y_conv_cap_ramp_down_constraint_variable[c, t] * self.ramp_down_dict[c]
                       for t in dm.TIME) <= (dm.ANF[c] + dm.fixed_om[c]) * dm.capex_var[c]

        self.dual_model.cap_conv_con = Constraint(self.dual_model.CONVERSION_COMPONENTS, rule=cap_conv_rule)

        def cap_gen_rule(dm, g, s):
            generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
            if s == generated_commodity:
                return - sum(dm.y_generation_constraint_variable[g, s, t]
                             * dm.generation_profiles[g, t]
                             for t in dm.TIME) <= (dm.ANF[g] + dm.fixed_om[g]) * dm.capex_var[g]
            else:
                return Constraint.Skip

        self.dual_model.cap_gen_con = Constraint(self.dual_model.GENERATORS, self.dual_model.ME_COMMODITIES,
                                                 rule=cap_gen_rule)

        def cap_storage_rule(dm, s):
            if s in self.storage_components:
                return sum(- dm.y_soc_ub_constraint_variable[s, t] * self.maximal_soc_dict[s]
                           + dm.y_soc_lb_constraint_variable[s, t] * self.minimal_soc_dict[s]
                           - dm.y_soc_charge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                           - dm.y_soc_discharge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                           for t in dm.TIME) <= (dm.ANF[s] + dm.fixed_om[s]) * dm.capex_var[s]
            else:
                return Constraint.Skip

        self.dual_model.cap_storage_con = Constraint(self.dual_model.ME_COMMODITIES, rule=cap_storage_rule)

        def objective_function(dm):
            return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES)

        self.dual_model.obj = Objective(rule=objective_function, sense=maximize)

        return model

    def optimize(self):
        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        opt.options["mipgap"] = 0.01
        instance = self.dual_model.create_instance()
        results = opt.solve(instance, tee=True)
        print(results)

        if False:

            print(self.dual_model.pprint())

            results.write()
            instance.solutions.load_from(results)

            for v in instance.component_objects(Var, active=True):
                print("Variable", v)
                varobject = getattr(instance, str(v))
                for index in varobject:
                    print("   ", index, varobject[index].value)

    def __init__(self, pm_object, solver, uncertainty, **kwargs):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.uncertainty = uncertainty
        self.kwargs = kwargs

        self.obj_value = None
        self.optimal_uncertainties = None

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, self.maximal_power_dict, self.ramp_up_dict, \
            self.ramp_down_dict, self.scaling_capex_var_dict, self.scaling_capex_fix_dict, \
            self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, self.shut_down_down_time_dict, \
            self.shut_down_start_up_costs, self.standby_down_time_dict, self.charging_efficiency_dict, \
            self.discharging_efficiency_dict, self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components, \
            self.no_shut_down_components, self.standby_components, \
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities \
            = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        # Create optimization program
        self.dual_model = ConcreteModel()
        self.dual_model.TIME = RangeSet(0, self.pm_object.get_time_steps() - 1)
        self.dual_model = self.attach_weightings_time_series_to_optimization_problem(self.dual_model)

        # Attach Sets
        self.dual_model = self.attach_component_sets_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_commodity_sets_to_optimization_problem(self.dual_model)

        # Attach Parameters
        self.dual_model = self.attach_component_parameters_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_annuity_to_optimization_problem(self.dual_model)

        # Attach Variables
        self.dual_model = self.attach_component_variables_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_commodity_variables_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_purchase_price_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_sale_price_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_demand_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_generation_time_series_to_optimization_problem(self.dual_model)

        self.dual_model = self.attach_constraints(self.dual_model)


class DualDispatch:

    def attach_component_sets_to_optimization_problem(self, model):
        model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
        model.STORAGES = Set(initialize=self.storage_components)
        model.GENERATORS = Set(initialize=self.generator_components)
        model.COMPONENTS = Set(initialize=self.all_components)
        return model

    def attach_commodity_sets_to_optimization_problem(self, model):
        model.ME_COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
        model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
        model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
        model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
        model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
        model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
        model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
        model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)
        return model

    def attach_annuity_to_optimization_problem(self, model):
        model.ANF = Param(model.COMPONENTS, initialize=self.annuity_factor_dict)
        return model

    def attach_component_parameters_to_optimization_problem(self, model):
        model.variable_om = Param(model.COMPONENTS, initialize=self.variable_om_dict)

        model.min_p = Param(model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
        model.max_p = Param(model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)

        model.ramp_up = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
        model.ramp_down = Param(model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

        model.charging_efficiency = Param(model.STORAGES, initialize=self.charging_efficiency_dict)
        model.discharging_efficiency = Param(model.STORAGES, initialize=self.discharging_efficiency_dict)

        model.minimal_soc = Param(model.STORAGES, initialize=self.minimal_soc_dict)
        model.maximal_soc = Param(model.STORAGES, initialize=self.maximal_soc_dict)

        model.ratio_capacity_p = Param(model.STORAGES, initialize=self.ratio_capacity_power_dict)

        model.generator_fixed_capacity = Param(model.GENERATORS, initialize=self.fixed_capacity_dict)
        return model

    def attach_component_variables_to_optimization_problem(self, model):
        # Component variables
        model.nominal_cap = Var(model.COMPONENTS, bounds=(0, None))
        return model
    def attach_commodity_variables_to_optimization_problem(self, dual_model):
        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        dual_model.y_free_available_constraint_variable = Var(dual_model.AVAILABLE_COMMODITIES,
                                                              dual_model.TIME, bounds=(0, None))

        dual_model.y_purchase_constraint_variable = Var(dual_model.PURCHASABLE_COMMODITIES,
                                                        dual_model.TIME, bounds=(0, None))

        dual_model.y_emit_constraint_variable = Var(dual_model.EMITTED_COMMODITIES,
                                                    dual_model.TIME, bounds=(0, None))

        dual_model.y_sell_constraint_variable = Var(dual_model.SALEABLE_COMMODITIES,
                                                    dual_model.TIME, bounds=(0, None))

        dual_model.y_balance_constraint_variable = Var(dual_model.ME_COMMODITIES, dual_model.TIME,
                                                       bounds=(None, None))

        dual_model.y_demand_constraint_variable = Var(dual_model.DEMANDED_COMMODITIES, bounds=(None, None))

        dual_model.y_out_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                   dual_model.ME_COMMODITIES, dual_model.TIME,
                                                   bounds=(None, None))
        dual_model.y_in_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                  dual_model.ME_COMMODITIES, dual_model.TIME,
                                                  bounds=(None, None))
        dual_model.y_conv_cap_ub_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, bounds=(None, 0))
        dual_model.y_conv_cap_lb_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, bounds=(0, None))
        dual_model.y_conv_cap_ramp_up_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                dual_model.TIME, bounds=(None, 0))
        dual_model.y_conv_cap_ramp_down_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                  dual_model.TIME, bounds=(None, 0))

        dual_model.y_generation_constraint_variable = Var(dual_model.GENERATORS,
                                                          dual_model.ME_COMMODITIES,
                                                          dual_model.TIME, bounds=(None, 0))

        dual_model.y_soc_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                   bounds=(None, None))
        dual_model.y_soc_ub_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                      bounds=(None, 0))
        dual_model.y_soc_lb_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                      bounds=(None, 0))
        dual_model.y_soc_charge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                bounds=(None, 0))
        dual_model.y_soc_discharge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                   bounds=(None, 0))

        return dual_model

    def attach_purchase_price_time_series_to_optimization_problem(self, model):
        model.purchase_price = Param(model.PURCHASABLE_COMMODITIES, model.TIME, initialize=self.purchase_price_dict)
        return model

    def attach_sale_price_time_series_to_optimization_problem(self, model):
        model.selling_price = Param(model.SALEABLE_COMMODITIES, model.TIME, initialize=self.sell_price_dict)
        return model

    def attach_demand_time_series_to_optimization_problem(self, model):
        model.commodity_demand = Param(model.DEMANDED_COMMODITIES, model.TIME, initialize=self.demand_dict)
        return model

    def attach_generation_time_series_to_optimization_problem(self, model):
        generation_profiles_dict = {}
        for k in [*self.uncertainty.keys()]:
            for ind in range(self.uncertainty[k].shape[0]):
                for c in range(self.uncertainty[k].shape[1]):

                    if c == 0:
                        g = 'Wind'
                    else:
                        g = 'Solar'

                    if self.optimal_capacities[g] > 0:

                        generation_profiles_dict[(g, ind)] = self.uncertainty[k][ind, c]

                if ind == max(model.TIME):
                    break

        model.generation_profiles = Param(model.GENERATORS, model.TIME,
                                          initialize=generation_profiles_dict)
        return model

    def attach_weightings_time_series_to_optimization_problem(self, model):
        model.weightings = Param(model.TIME, initialize=self.weightings_dict)
        return model

    def attach_constraints(self, model):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

        def x_free_rule(dm, s, t):  # x_free >= 0 --> constraint is <=
            if s in self.available_commodities:
                return dm.y_balance_constraint_variable[s, t] + self.dual_model.y_free_available_constraint_variable[
                    s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_free_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_free_rule)

        def x_emit_rule(dm, s, t):
            if s in self.emittable_commodities:
                return - dm.y_balance_constraint_variable[s, t] + self.dual_model.y_emit_constraint_variable[s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_emit_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_emit_rule)

        def x_buy_rule(dm, s, t):
            if s in self.purchasable_commodities:
                return dm.y_balance_constraint_variable[s, t] + dm.y_purchase_constraint_variable[s, t] \
                       <= self.purchase_price_dict[s, t] * self.weightings_dict[t]
            else:
                return Constraint.Skip

        self.dual_model.x_buy_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_buy_rule)

        def x_sell_rule(dm, s, t):
            if s in self.saleable_commodities:
                return - dm.y_balance_constraint_variable[s, t] + dm.y_sell_constraint_variable[s, t] \
                       <= - self.sell_price_dict[s, t] * self.weightings_dict[t]
            else:
                return Constraint.Skip

        self.dual_model.x_sell_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, rule=x_sell_rule)

        def x_demand_rule(dm, s, t):
            if s in self.demanded_commodities:
                return - dm.y_balance_constraint_variable[s, t] \
                       + dm.y_demand_constraint_variable[s] * self.weightings_dict[t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_demand_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                  rule=x_demand_rule)

        def x_generation_rule(dm, g, s, t):
            generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
            if s == generated_commodity:
                return dm.y_balance_constraint_variable[s, t] \
                       + dm.y_generation_constraint_variable[g, s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_generation_con = Constraint(self.dual_model.GENERATORS, self.dual_model.ME_COMMODITIES,
                                                      self.dual_model.TIME, rule=x_generation_rule)

        def x_in_rule(dm, c, s, t):
            main_input = pm_object.get_component(c).get_main_input()
            inputs = pm_object.get_component(c).get_inputs()

            if s in inputs:

                # balance and bounds
                if s == main_input:
                    lhs = [- dm.y_balance_constraint_variable[s, t]
                           + dm.y_conv_cap_ub_constraint_variable[c, t]
                           + dm.y_conv_cap_lb_constraint_variable[c, t]]

                    if t > 0:
                        lhs.append(+ dm.y_conv_cap_ramp_up_constraint_variable[c, t])
                        lhs.append(+ dm.y_conv_cap_ramp_down_constraint_variable[c, t])

                    if t < max(dm.TIME):  # consider ramping
                        lhs.append(- dm.y_conv_cap_ramp_up_constraint_variable[c, t + 1])
                        lhs.append(- dm.y_conv_cap_ramp_down_constraint_variable[c, t + 1])

                    for conversion in self.output_conversion_tuples:
                        output_commodity = conversion[2]
                        lhs.append(- dm.y_out_constraint_variable[c, output_commodity, t]
                                   * self.output_conversion_tuples_dict[c, main_input, output_commodity])

                    for conversion in self.input_conversion_tuples:
                        other_input_commodity = conversion[2]
                        lhs.append(- dm.y_in_constraint_variable[c, other_input_commodity, t]
                                   * self.input_conversion_tuples_dict[c, main_input, other_input_commodity])

                else:
                    lhs = [- dm.y_balance_constraint_variable[s, t]]

                    for conversion in self.input_conversion_tuples:
                        # input to input conversions only possible if s != main input
                        if s == conversion[2]:
                            lhs.append(+ dm.y_in_constraint_variable[c, s, t])

                return sum(lhs) <= 0

            else:
                return Constraint.Skip

        self.dual_model.x_in_con = Constraint(self.dual_model.CONVERSION_COMPONENTS, self.dual_model.ME_COMMODITIES,
                                              self.dual_model.TIME, rule=x_in_rule)

        def x_out_rule(dm, c, s, t):
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, s) in self.output_conversion_tuples:
                return dm.y_balance_constraint_variable[s, t] \
                       + dm.y_out_constraint_variable[c, s, t] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_out_con = Constraint(self.dual_model.CONVERSION_COMPONENTS,
                                               self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                               rule=x_out_rule)

        if True:
            def x_charge_rule(dm, s, t):
                if s in self.storage_components:

                    lhs = [- dm.y_balance_constraint_variable[s, t] + dm.y_soc_charge_limit_constraint_variable[s, t]]

                    if t < max(dm.TIME):
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])
                    else:
                        lhs.append(- dm.y_soc_constraint_variable[s, t] * self.charging_efficiency_dict[s])

                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                      rule=x_charge_rule)

            if True:
                def x_discharge_variable_rule(dm, s, t):

                    if s in self.storage_components:

                        lhs = [
                            dm.y_balance_constraint_variable[s, t] + dm.y_soc_discharge_limit_constraint_variable[s, t]]

                        if t < max(dm.TIME):
                            lhs.append(dm.y_soc_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[s])
                        else:
                            lhs.append(dm.y_soc_constraint_variable[s, t] / self.discharging_efficiency_dict[s])

                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.x_discharge_variable_con = Constraint(self.dual_model.ME_COMMODITIES,
                                                                      self.dual_model.TIME,
                                                                      rule=x_discharge_variable_rule)

                def soc_rule(dm, s, t):
                    if s in self.storage_components:

                        lhs = []
                        if t == max(dm.TIME):
                            lhs.append(- dm.y_soc_constraint_variable[s, 0]
                                       + dm.y_soc_constraint_variable[s, t]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        else:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t]
                                       - dm.y_soc_constraint_variable[s, t + 1]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.soc_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                     rule=soc_rule)

        else:
            def x_charge_rule(dm, s, t):
                if s in self.storage_components:

                    period_length = self.pm_object.get_representative_periods_length() - 1
                    lhs = [- dm.y_balance_constraint_variable[s, t]
                           + dm.y_soc_charge_limit_constraint_variable[s, t]]

                    if (t % (period_length - 1) == 0) & (t > 0):
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s]
                                   + dm.y_soc_ub_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])
                    elif (t % period_length == 0) & (t > 0):
                        pass
                    else:
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])

                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                      rule=x_charge_rule)

            if True:
                def x_discharge_variable_rule(dm, s, t):
                    if s in self.storage_components:

                        period_length = self.pm_object.get_representative_periods_length() - 1
                        lhs = [+ dm.y_balance_constraint_variable[s, t]
                               + dm.y_soc_charge_limit_constraint_variable[s, t]]

                        if (t % (period_length - 1) == 0) & (t > 0):
                            lhs.append(+ dm.y_soc_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[s]
                                       + dm.y_soc_lb_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[
                                           s])
                        elif (t % period_length == 0) & (t > 0):
                            pass
                        else:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t + 1])

                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.x_discharge_variable_con = Constraint(self.dual_model.ME_COMMODITIES,
                                                                      self.dual_model.TIME,
                                                                      rule=x_discharge_variable_rule)

                def soc_rule(dm, s, t):
                    if s in self.storage_components:

                        lhs = []

                        period_length = self.pm_object.get_representative_periods_length() - 1
                        if t == 0:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t + period_length]
                                       - dm.y_soc_constraint_variable[s, t + 1]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        elif t % period_length != 0:
                            lhs.append(+ dm.y_soc_constraint_variable[s, t]
                                       - dm.y_soc_constraint_variable[s, t + 1]
                                       + dm.y_soc_ub_constraint_variable[s, t]
                                       - dm.y_soc_lb_constraint_variable[s, t])
                        else:
                            lhs.append(+ dm.y_soc_ub_constraint_variable[s, t - 1]
                                       - dm.y_soc_lb_constraint_variable[s, t - 1])
                        return sum(lhs) <= 0
                    else:
                        return Constraint.Skip

                self.dual_model.soc_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                     rule=soc_rule)

        def objective_function(dm):
            return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES) \
                   + sum((dm.y_conv_cap_ub_constraint_variable[c, t] * self.maximal_power_dict[c]
                          - dm.y_conv_cap_lb_constraint_variable[c, t] * self.minimal_power_dict[c]
                          + dm.y_conv_cap_ramp_up_constraint_variable[c, t] * self.ramp_up_dict[c]
                          + dm.y_conv_cap_ramp_down_constraint_variable[c, t] * self.ramp_down_dict[c])
                         * self.optimal_capacities[c]
                         for t in dm.TIME for c in dm.CONVERSION_COMPONENTS) \
                   + sum(
                dm.y_generation_constraint_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t]
                * model.generation_profiles[g, t] * self.optimal_capacities[g] for t in dm.TIME for g in dm.GENERATORS) \
                   + sum((dm.y_soc_ub_constraint_variable[s, t] * self.maximal_soc_dict[s]
                          - dm.y_soc_lb_constraint_variable[s, t] * self.minimal_soc_dict[s]
                          + dm.y_soc_charge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                          + dm.y_soc_discharge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s])
                         * self.optimal_capacities[s]
                         for t in dm.TIME for s in dm.STORAGES if s in self.storage_components)

        self.dual_model.obj = Objective(rule=objective_function, sense=maximize)

        return model

    def optimize(self):
        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        opt.options["mipgap"] = 0.01
        instance = self.dual_model.create_instance()
        results = opt.solve(instance, tee=True)
        print(results)

        if False:

            print(self.dual_model.pprint())

            results.write()
            instance.solutions.load_from(results)

            for v in instance.component_objects(Var, active=True):
                print("Variable", v)
                varobject = getattr(instance, str(v))
                for index in varobject:
                    print("   ", index, varobject[index].value)

    def __init__(self, pm_object, solver, uncertainty, optimal_capacities, **kwargs):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.uncertainty = uncertainty
        self.kwargs = kwargs

        self.obj_value = None
        self.optimal_capacities = optimal_capacities

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, self.maximal_power_dict, self.ramp_up_dict, \
            self.ramp_down_dict, self.scaling_capex_var_dict, self.scaling_capex_fix_dict, \
            self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, self.shut_down_down_time_dict, \
            self.shut_down_start_up_costs, self.standby_down_time_dict, self.charging_efficiency_dict, \
            self.discharging_efficiency_dict, self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components, \
            self.no_shut_down_components, self.standby_components, \
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities \
            = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        # Create optimization program
        self.dual_model = ConcreteModel()
        self.dual_model.TIME = RangeSet(0, self.pm_object.get_time_steps() - 1)
        self.dual_model = self.attach_weightings_time_series_to_optimization_problem(self.dual_model)

        conversion_components_new = []
        for c in self.conversion_components:
            if self.optimal_capacities[c] > 0:
                conversion_components_new.append(c)
        self.conversion_components = conversion_components_new

        storage_components_new = []
        for s in self.storage_components:
            if self.optimal_capacities[s] > 0:
                storage_components_new.append(s)
        self.storage_components = storage_components_new

        generators_components_new = []
        for g in self.generator_components:
            if self.optimal_capacities[g] > 0:
                generators_components_new.append(g)
        self.generator_components = generators_components_new

        components_new = []
        variable_om_new = {}
        for c in self.all_components:
            if self.optimal_capacities[c] > 0:
                components_new.append(c)
                variable_om_new[c] = self.variable_om_dict[c]
        self.all_components = components_new
        self.variable_om_dict = variable_om_new

        minimal_power_new = {}
        maximal_power_new = {}
        ramp_up_new = {}
        ramp_down_new = {}
        for c in self.conversion_components:
            if self.optimal_capacities[c] > 0:
                minimal_power_new[c] = self.minimal_power_dict[c]
                maximal_power_new[c] = self.maximal_power_dict[c]
                ramp_up_new[c] = self.ramp_up_dict[c]
                ramp_down_new[c] = self.ramp_down_dict[c]
        self.minimal_power_dict = minimal_power_new
        self.maximal_power_dict = maximal_power_new
        self.ramp_up_dict = ramp_up_new
        self.ramp_down_dict = ramp_down_new

        charging_efficiency_new = {}
        discharging_efficiency_new = {}
        minimal_soc_new = {}
        maximal_soc_new = {}
        ratio_capacity_p_new = {}
        for s in self.storage_components:
            if self.optimal_capacities[s] > 0:
                charging_efficiency_new[s] = self.charging_efficiency_dict[s]
                discharging_efficiency_new[s] = self.discharging_efficiency_dict[s]
                minimal_soc_new[s] = self.minimal_soc_dict[s]
                maximal_soc_new[s] = self.maximal_soc_dict[s]
                ratio_capacity_p_new[s] = self.ratio_capacity_power_dict[s]
        self.charging_efficiency_dict = charging_efficiency_new
        self.discharging_efficiency_dict = discharging_efficiency_new
        self.minimal_soc_dict = minimal_soc_new
        self.maximal_soc_dict = maximal_soc_new
        self.ratio_capacity_power_dict = ratio_capacity_p_new

        fixed_capacities_new = {}
        for g in self.generator_components:
            if self.optimal_capacities[g] > 0:
                fixed_capacities_new[g] = self.fixed_capacity_dict[g]
        self.fixed_capacity_dict = fixed_capacities_new

        # Attach Sets
        self.dual_model = self.attach_component_sets_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_commodity_sets_to_optimization_problem(self.dual_model)

        # Attach Parameters
        self.dual_model = self.attach_component_parameters_to_optimization_problem(self.dual_model)

        # Attach Variables
        self.dual_model = self.attach_component_variables_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_commodity_variables_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_purchase_price_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_sale_price_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_demand_time_series_to_optimization_problem(self.dual_model)
        self.dual_model = self.attach_generation_time_series_to_optimization_problem(self.dual_model)

        self.dual_model = self.attach_constraints(self.dual_model)

