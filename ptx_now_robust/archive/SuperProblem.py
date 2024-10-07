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

    def attach_auxiliary_variables_to_optimization_problem(self, model):
        # Component variables
        model.auxiliary_variable = Var()
        return model

    def attach_commodity_variables_to_optimization_problem(self, model):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        model.mass_energy_component_in_commodities = Var(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                         model.TIME, model.ITERATION, bounds=(0, None))
        model.mass_energy_component_out_commodities = Var(model.CONVERSION_COMPONENTS, model.ME_COMMODITIES,
                                                          model.TIME, model.ITERATION, bounds=(0, None))

        # Freely available commodities
        model.mass_energy_available = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION, bounds=(0, None))
        model.mass_energy_emitted = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION, bounds=(0, None))

        # Charged and discharged commodities
        model.mass_energy_storage_in_commodities = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                       bounds=(0, None))
        model.mass_energy_storage_out_commodities = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                                        bounds=(0, None))
        model.soc = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION, bounds=(0, None))

        # sold and purchased commodities
        model.mass_energy_sell_commodity = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION, bounds=(0, None))
        model.mass_energy_purchase_commodity = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION, bounds=(0, None))

        # generated commodities
        model.mass_energy_generation = Var(model.GENERATORS, model.ME_COMMODITIES, model.TIME, model.ITERATION,
                                           bounds=(0, None))
        model.mass_energy_total_generation = Var(model.ME_COMMODITIES, model.TIME, model.ITERATION, bounds=(0, None))

        # Demanded commodities
        model.mass_energy_demand = Var(model.TOTAL_DEMANDED_COMMODITIES, model.TIME, model.ITERATION, bounds=(0, None))
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
        for k in [*self.nominal.keys()]:
            if not isinstance(self.nominal[k], dict):
                for ind in range(self.nominal[k].shape[0]):
                    for c in range(self.nominal[k].shape[1]):

                        if c == 0:
                            g = 'Wind'
                        else:
                            g = 'Solar'

                        generation_profiles_dict[(g, ind, k)] = self.nominal[k][ind, c]

                    if ind == max(model.TIME):
                        break
            else:
                for ind in [*self.nominal[k].keys()]:
                    generation_profiles_dict[(ind[0], ind[1], k)] = self.nominal[k][ind]

        model.generation_profiles = Param(model.GENERATORS, model.TIME, model.ITERATION,
                                          initialize=generation_profiles_dict)
        return model

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

    def __init__(self, pm_object, solver, nominal, iteration):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.nominal = nominal

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