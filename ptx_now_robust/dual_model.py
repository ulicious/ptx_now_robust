import pyomo.environ as pyo
# from copy import deepcopy

from pyomo.core import *
# import pandas as pd
# from dualization_from_model import dualize_from_model
# from pyomo.core.expr.numeric_expr import LinearExpression
# from old_code import get_dual_model_data_from_gurobi
from pyomo.core import Binary

import numpy as np

import os


class ExtremeCaseBilinear:

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
                                                              dual_model.TIME, dual_model.CLUSTER, bounds=(0, None))

        dual_model.y_purchase_constraint_variable = Var(dual_model.PURCHASABLE_COMMODITIES,
                                                        dual_model.TIME, dual_model.CLUSTER, bounds=(0, None))

        dual_model.y_emit_constraint_variable = Var(dual_model.EMITTED_COMMODITIES,
                                                    dual_model.TIME, dual_model.CLUSTER, bounds=(0, None))

        dual_model.y_sell_constraint_variable = Var(dual_model.SALEABLE_COMMODITIES,
                                                    dual_model.TIME, dual_model.CLUSTER, bounds=(0, None))

        dual_model.y_balance_constraint_variable = Var(dual_model.ME_COMMODITIES, dual_model.TIME, dual_model.CLUSTER,
                                                       bounds=(None, None))

        # # dual_model.y_demand_constraint_variable = Var(dual_model.DEMANDED_COMMODITIES, bounds=(None, 0))
        # # todo: Check if right bounds. Normally should be None, 0

        dual_model.y_demand_constraint_variable = Var(dual_model.DEMANDED_COMMODITIES,
                                                      bounds=(None, None)) # todo: None, None
        # dual_model.y_weekly_production_balance_variable = Var(dual_model.DEMANDED_COMMODITIES, dual_model.CLUSTER,
        #                                                       bounds=(None, None))

        dual_model.y_out_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                   dual_model.ME_COMMODITIES, dual_model.TIME, dual_model.CLUSTER,
                                                   bounds=(None, None))
        dual_model.y_in_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                  dual_model.ME_COMMODITIES, dual_model.TIME, dual_model.CLUSTER,
                                                  bounds=(None, None))
        dual_model.y_conv_cap_ub_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, dual_model.CLUSTER, bounds=(None, 0))
        dual_model.y_conv_cap_lb_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.TIME, dual_model.CLUSTER, bounds=(0, None))
        dual_model.y_conv_cap_ramp_up_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                dual_model.TIME, dual_model.CLUSTER, bounds=(None, 0))
        dual_model.y_conv_cap_ramp_down_constraint_variable = Var(dual_model.CONVERSION_COMPONENTS,
                                                                  dual_model.TIME, dual_model.CLUSTER, bounds=(None, 0))

        dual_model.y_generation_constraint_variable_active = Var(dual_model.GENERATORS,
                                                                 dual_model.GENERATED_COMMODITIES,
                                                                 dual_model.TIME, dual_model.CLUSTER, bounds=(None, 0))

        dual_model.y_soc_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                   bounds=(None, None))
        dual_model.y_soc_ub_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                      bounds=(None, 0))
        dual_model.y_soc_lb_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                      bounds=(0, None))
        dual_model.y_soc_charge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                dual_model.CLUSTER, bounds=(None, 0))
        dual_model.y_soc_discharge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME,
                                                                   dual_model.CLUSTER, bounds=(None, 0))

        dual_model.auxiliary_variable = Var(dual_model.GENERATORS, dual_model.GENERATED_COMMODITIES,
                                            dual_model.TIME, dual_model.PROFILES, bounds=(None, 0))

        dual_model.weighting_profiles_binary = Var(dual_model.PROFILES, within=Binary)
        dual_model.chosen_profile_variable = Var(dual_model.GENERATORS, dual_model.TIME)

        return dual_model

    def attach_purchase_price_time_series_to_optimization_problem(self, dual_model):
        dual_model.purchase_price = Param(dual_model.PURCHASABLE_COMMODITIES,
                                          dual_model.CLUSTER, dual_model.TIME, initialize=self.purchase_price_dict)
        return dual_model

    def attach_sale_price_time_series_to_optimization_problem(self, dual_model):
        dual_model.selling_price = Param(dual_model.SALEABLE_COMMODITIES,
                                         dual_model.CLUSTER, dual_model.TIME, initialize=self.sell_price_dict)
        return dual_model

    def attach_demand_time_series_to_optimization_problem(self, dual_model):

        dual_model.hourly_commodity_demand = Param(dual_model.DEMANDED_COMMODITIES, dual_model.CLUSTER,
                                                   dual_model.TIME, initialize=self.hourly_demand_dict)

        dual_model.total_commodity_demand = Param(dual_model.TOTAL_DEMANDED_COMMODITIES,
                                                  initialize=self.total_demand_dict)

        return dual_model

    def attach_weightings_time_series_to_optimization_problem(self, dual_model):

        dual_model.weightings = Param(dual_model.CLUSTER, initialize=self.weightings)
        return dual_model

    def attach_nominal_generation(self, dual_model):

        generation_profiles_certain_dict = {}
        for g in [*self.nominal.keys()]:
            if g not in self.generator_components:
                continue

            for n in [*self.nominal[g].keys()]:
                for t in dual_model.TIME:

                    generation_profiles_certain_dict[(g, t, n)] = self.nominal[g][n][t]

        dual_model.generation_profiles_certain = Param(self.dual_model.GENERATORS, self.dual_model.TIME,
                                                       self.dual_model.CLUSTER,
                                                       initialize=generation_profiles_certain_dict)

        generation_profiles_uncertain_dict = {}
        profile_counter = {'Wind': 0,
                           'Solar': 0}
        for c in self.data.columns:
            if c not in self.generator_components:
                continue

            if 'Wind' in c:
                g = 'Wind'
            else:
                g = 'Solar'

            for t in dual_model.TIME:
                ind = self.data.index[t]
                generation_profiles_uncertain_dict[(g, profile_counter[g], t)] = self.data.loc[ind, c]

            profile_counter[g] = profile_counter[g] + 1

        dual_model.generation_profile_uncertain = Param(self.dual_model.GENERATORS, dual_model.PROFILES,
                                                        dual_model.TIME,
                                                        initialize=generation_profiles_uncertain_dict)

        return dual_model

    def attach_uncertainty_set(self, dual_model):

        if True:

            if True:

                def balance_profile_binaries(dm):
                    return sum(dm.weighting_profiles_binary[p] for p in dm.PROFILES) == 1
                dual_model.balance_profile_binaries_con = Constraint(rule=balance_profile_binaries)

                if False:

                    def define_chosen_profile(dm, g, t):
                        return dm.chosen_profile_variable[g, t] == sum(dm.generation_profile_uncertain[g, p, t]
                                                                       * dm.weighting_profiles_binary[p] for p in dm.PROFILES)
                    dual_model.define_chosen_profile_con = Constraint(dual_model.GENERATORS, dual_model.TIME,
                                                                      rule=define_chosen_profile)

            if True:

                def define_relation_auxiliary_to_generation_variable(dm, g, t, p):
                    com = self.pm_object.get_component(g).get_generated_commodity()
                    return dm.auxiliary_variable[g, com, t, p] \
                        <= dm.y_generation_constraint_variable_active[g, com, t, max(dm.CLUSTER)] \
                        * dm.generation_profile_uncertain[g, p, t] * self.optimal_capacities[g] \
                        + (1 - dm.weighting_profiles_binary[p]) * 10000000
                dual_model.define_relation_auxiliary_to_generation_variable_con\
                    = Constraint(dual_model.GENERATORS, dual_model.TIME, dual_model.PROFILES,
                                 rule=define_relation_auxiliary_to_generation_variable)

            if True:
                def min_renewable_generation_solar_rule(dm):
                    return sum(dm.generation_profile_uncertain['Solar', p, t] * dm.weighting_profiles_binary[p]
                               for t in dm.TIME for p in dm.PROFILES) >= 65
                dual_model.min_renewable_generation_solar_con = Constraint(rule=min_renewable_generation_solar_rule)

                def min_renewable_generation_wind_rule(dm):
                    return sum(dm.generation_profile_uncertain['Wind', p, t] * dm.weighting_profiles_binary[p]
                               for t in dm.TIME for p in dm.PROFILES) >= 79
                dual_model.min_renewable_generation_wind_con = Constraint(rule=min_renewable_generation_wind_rule)

        return dual_model

    def attach_constraints(self, model):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

        def x_free_rule(dm, s, t, n):  # x_free >= 0 --> constraint is <=
            if s in self.available_commodities:
                return dm.y_balance_constraint_variable[s, t, n] + self.dual_model.y_free_available_constraint_variable[s, t, n] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_free_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                self.dual_model.CLUSTER, rule=x_free_rule)

        def x_emit_rule(dm, s, t, n):
            if s in self.emittable_commodities:
                return - dm.y_balance_constraint_variable[s, t, n] + self.dual_model.y_emit_constraint_variable[s, t, n] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_emit_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER, rule=x_emit_rule)

        def x_buy_rule(dm, s, t, n):
            if s in self.purchasable_commodities:
                return dm.y_balance_constraint_variable[s, t, n] + dm.y_purchase_constraint_variable[s, t, n] \
                       <= self.purchase_price_dict[s, n, t] * dm.weightings[n]
            else:
                return Constraint.Skip

        self.dual_model.x_buy_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                               self.dual_model.CLUSTER, rule=x_buy_rule)

        def x_sell_rule(dm, s, t, n):
            if s in self.saleable_commodities:
                return - dm.y_balance_constraint_variable[s, t, n] + dm.y_sell_constraint_variable[s, t, n] \
                       <= - self.sell_price_dict[s, n, t] * dm.weightings[n]
            else:
                return Constraint.Skip

        self.dual_model.x_sell_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                self.dual_model.CLUSTER, rule=x_sell_rule)

        # def x_demand_rule(dm, s, t, n):
        #     if s in self.demanded_commodities:
        #         return - dm.y_balance_constraint_variable[s, t, n] \
        #                - dm.y_demand_constraint_variable[s] <= 0
        #     else:
        #         return Constraint.Skip
        #
        # self.dual_model.x_demand_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
        #                                           self.dual_model.CLUSTER,
        #                                           rule=x_demand_rule)

        def x_total_demand_rule(dm, s, t, n):
            if s in self.demanded_commodities:
                return - dm.y_balance_constraint_variable[s, t, n] \
                       + dm.y_demand_constraint_variable[s] * self.weightings[n] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_demand_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                  self.dual_model.CLUSTER,
                                                  rule=x_total_demand_rule)

        # def x_weekly_production_rule(dm, s, n):
        #     if s in self.demanded_commodities:
        #         return dm.y_demand_constraint_variable[s, n] + dm.y_weekly_production_balance_variable[s, n] <= 0
        #     else:
        #         return Constraint.Skip
        # self.dual_model.x_weekly_production_con = Constraint(self.dual_model.ME_COMMODITIES,
        #                                                      self.dual_model.CLUSTER,
        #                                                      rule=x_weekly_production_rule)
        #
        # def x_production_surplus_rule(dm, s, n):
        #     if s in self.demanded_commodities:
        #         return - dm.y_weekly_production_balance_variable[s, n] <= 0
        #     else:
        #         return Constraint.Skip
        # self.dual_model.x_production_surplus_con = Constraint(self.dual_model.ME_COMMODITIES,
        #                                                       self.dual_model.CLUSTER,
        #                                                       rule=x_production_surplus_rule)
        #
        # def x_production_deficit_rule(dm, s, n):
        #     if s in self.demanded_commodities:
        #         return - dm.y_weekly_production_balance_variable[s, n] >= - dm.weightings[n] * self.costs_missing_product
        #     else:
        #         return Constraint.Skip
        # self.dual_model.x_production_deficit_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.CLUSTER,
        #                                                       rule=x_production_deficit_rule)

        def x_generation_rule(dm, g, s, t, n):
            generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
            if s == generated_commodity:
                return dm.y_balance_constraint_variable[s, t, n] \
                       + dm.y_generation_constraint_variable_active[g, s, t, n] <= dm.variable_om[g] * dm.weightings[n]
            else:
                return Constraint.Skip
        self.dual_model.x_generation_con = Constraint(self.dual_model.GENERATORS, self.dual_model.ME_COMMODITIES,
                                                      self.dual_model.TIME, self.dual_model.CLUSTER,
                                                      rule=x_generation_rule)

        # def x_curtailment_rule(dm, s, t, n): # todo: Only if set as possible & adjust when more generators
        #     return - dm.y_balance_constraint_variable[s, t, n] <= 0
        # self.dual_model.x_curtailment_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
        #                                                self.dual_model.CLUSTER, rule=x_curtailment_rule)

        def x_in_rule(dm, c, s, t, n):
            main_input = pm_object.get_component(c).get_main_input()
            inputs = pm_object.get_component(c).get_inputs()

            if s in inputs:

                # balance and bounds
                if s == main_input:
                    lhs = [- dm.y_balance_constraint_variable[s, t, n]
                           + dm.y_conv_cap_ub_constraint_variable[c, t, n]
                           + dm.y_conv_cap_lb_constraint_variable[c, t, n]]

                    if t > 0:
                        lhs.append(+ dm.y_conv_cap_ramp_up_constraint_variable[c, t, n])
                        lhs.append(+ dm.y_conv_cap_ramp_down_constraint_variable[c, t, n])

                    if t < max(dm.TIME):  # consider ramping
                        lhs.append(- dm.y_conv_cap_ramp_up_constraint_variable[c, t + 1, n])
                        lhs.append(- dm.y_conv_cap_ramp_down_constraint_variable[c, t + 1, n])

                    for conversion in self.output_conversion_tuples:
                        if conversion[0] == c:
                            output_commodity = conversion[2]
                            lhs.append(- dm.y_out_constraint_variable[c, output_commodity, t, n]
                                       * self.output_conversion_tuples_dict[c, main_input, output_commodity])

                    for conversion in self.input_conversion_tuples:
                        if conversion[0] == c:
                            other_input_commodity = conversion[2]
                            lhs.append(- dm.y_in_constraint_variable[c, other_input_commodity, t, n]
                                       * self.input_conversion_tuples_dict[c, main_input, other_input_commodity])

                else:
                    lhs = [- dm.y_balance_constraint_variable[s, t, n]]

                    for conversion in self.input_conversion_tuples:
                        # input to input conversions only possible if s != main input
                        if s == conversion[2]:
                            lhs.append(+ dm.y_in_constraint_variable[c, s, t, n])

                return sum(lhs) <= 0

            else:
                return Constraint.Skip

        self.dual_model.x_in_con = Constraint(self.dual_model.CONVERSION_COMPONENTS, self.dual_model.ME_COMMODITIES,
                                              self.dual_model.TIME, self.dual_model.CLUSTER, rule=x_in_rule)

        def x_out_rule(dm, c, s, t, n):
            main_input = pm_object.get_component(c).get_main_input()

            if (c, main_input, s) in self.output_conversion_tuples:

                return dm.y_balance_constraint_variable[s, t, n] \
                       + dm.y_out_constraint_variable[c, s, t, n] <= dm.variable_om[c] * dm.weightings[n]
            else:
                return Constraint.Skip

        self.dual_model.x_out_con = Constraint(self.dual_model.CONVERSION_COMPONENTS,
                                               self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER,
                                               rule=x_out_rule)

        def x_charge_rule(dm, s, t, n):
            if s in self.storage_components:

                lhs = [- dm.y_balance_constraint_variable[s, t, n] + dm.y_soc_charge_limit_constraint_variable[s, t, n]]

                if t < max(dm.TIME):
                    lhs.append(- dm.y_soc_constraint_variable[s, t + 1, n] * self.charging_efficiency_dict[s])
                else:
                    lhs.append(- dm.y_soc_constraint_variable[s, t, n] * self.charging_efficiency_dict[s])

                return sum(lhs) <= dm.variable_om[s] * dm.weightings[n]
            else:
                return Constraint.Skip

        self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER,
                                                  rule=x_charge_rule)

        def x_discharge_variable_rule(dm, s, t, n):

            if s in self.storage_components:

                lhs = [dm.y_balance_constraint_variable[s, t, n] + dm.y_soc_discharge_limit_constraint_variable[s, t, n]]

                if t < max(dm.TIME):
                    lhs.append(dm.y_soc_constraint_variable[s, t + 1, n] / self.discharging_efficiency_dict[s])
                else:
                    lhs.append(dm.y_soc_constraint_variable[s, t, n] / self.discharging_efficiency_dict[s])

                return sum(lhs) <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_discharge_variable_con = Constraint(self.dual_model.ME_COMMODITIES,
                                                              self.dual_model.TIME, self.dual_model.CLUSTER,
                                                              rule=x_discharge_variable_rule)

        def soc_rule(dm, s, t, n):
            if s in self.storage_components:

                lhs = []
                if t == max(dm.TIME):
                    lhs.append(- dm.y_soc_constraint_variable[s, 0, n]
                               + dm.y_soc_constraint_variable[s, t, n]
                               + dm.y_soc_ub_constraint_variable[s, t, n]
                               - dm.y_soc_lb_constraint_variable[s, t, n])
                else:
                    lhs.append(+ dm.y_soc_constraint_variable[s, t, n]
                               - dm.y_soc_constraint_variable[s, t + 1, n]
                               + dm.y_soc_ub_constraint_variable[s, t, n]
                               - dm.y_soc_lb_constraint_variable[s, t, n])
                return sum(lhs) <= 0
            else:
                return Constraint.Skip

        self.dual_model.soc_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER,
                                             rule=soc_rule)

        def objective_function(dm):
            if False:
                return sum(dm.y_demand_constraint_variable[s] * dm.total_commodity_demand[s]
                           for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                              - dm.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                              + dm.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                              + dm.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS for n in dm.CLUSTER) \
                       + sum(dm.y_generation_constraint_variable_active[g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                             * self.optimal_capacities[g]
                             * dm.generation_profiles_certain[g, t, n]
                             for n in dm.CLUSTER if n < max(dm.CLUSTER) for t in dm.TIME for g in dm.GENERATORS) \
                       + sum(dm.y_generation_constraint_variable_active[g,
                                                                        self.pm_object.get_component(g).get_generated_commodity(),
                                                                        t,
                                                                        max(dm.CLUSTER)]
                             * self.optimal_capacities[g]
                             * dm.chosen_profile_variable[g, t] for t in dm.TIME for g in dm.GENERATORS) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                              - dm.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                              + dm.y_soc_charge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]
                              + dm.y_soc_discharge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[
                                  s]) * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components for n in dm.CLUSTER)
            elif False:
                return sum(dm.y_demand_constraint_variable[s] * dm.total_commodity_demand[s]
                           for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                              - dm.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                              + dm.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                              + dm.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS for n in dm.CLUSTER) \
                       + sum(dm.y_generation_constraint_variable_active[
                                 g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                             * self.optimal_capacities[g]
                             * dm.generation_profiles_certain[g, t, n]
                             for n in dm.CLUSTER if n < max(dm.CLUSTER) for t in dm.TIME for g in dm.GENERATORS) \
                       + sum(dm.auxiliary_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t, p]
                             for g in dm.GENERATORS for t in dm.TIME for p in dm.PROFILES) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                              - dm.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                              + dm.y_soc_charge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]
                              + dm.y_soc_discharge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[
                                  s]) * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components for n in dm.CLUSTER)
            if False:
                return sum(- dm.y_demand_constraint_variable[s, n] * dm.total_commodity_demand[s] / (8760 / len(dm.TIME))
                           for s in dm.DEMANDED_COMMODITIES for n in dm.CLUSTER) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                              - dm.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                              + dm.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                              + dm.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS for n in dm.CLUSTER) \
                       + sum(dm.y_generation_constraint_variable_active[g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                             * self.optimal_capacities[g] * dm.generation_profiles_certain[g, t, n]
                             for n in dm.CLUSTER if n < max(dm.CLUSTER) for t in dm.TIME for g in dm.GENERATORS) \
                       + sum(dm.auxiliary_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t, p]
                             for g in dm.GENERATORS for t in dm.TIME for p in dm.PROFILES) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                              - dm.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                              + dm.y_soc_charge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]
                              + dm.y_soc_discharge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[
                                  s]) * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components for n in dm.CLUSTER)

            if True:
                return sum(- dm.y_demand_constraint_variable[s] * dm.total_commodity_demand[s]
                           for s in dm.DEMANDED_COMMODITIES) \
                    + sum((dm.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                           - dm.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                           + dm.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                           + dm.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                          * self.optimal_capacities[c]
                          for t in dm.TIME for c in dm.CONVERSION_COMPONENTS for n in dm.CLUSTER) \
                    + sum(dm.y_generation_constraint_variable_active[
                              g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                          * self.optimal_capacities[g] * dm.generation_profiles_certain[g, t, n]
                          for n in dm.CLUSTER if n < max(dm.CLUSTER) for t in dm.TIME for g in dm.GENERATORS) \
                    + sum(dm.auxiliary_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t, p]
                          for g in dm.GENERATORS for t in dm.TIME for p in dm.PROFILES) \
                    + sum((dm.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                           - dm.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                           + dm.y_soc_charge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]
                           + dm.y_soc_discharge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[
                               s]) * self.optimal_capacities[s]
                          for t in dm.TIME for s in dm.STORAGES if s in self.storage_components for n in dm.CLUSTER)

        self.dual_model.obj = Objective(rule=objective_function, sense=maximize)

        return model

    def optimize(self):
        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        # opt.options["mipgap"] = 0.05
        # opt.options["NonConvex"] = 2
        # opt.options['Threads'] = 120
        instance = self.dual_model.create_instance()

        print(self.dual_model)

        results = opt.solve(instance, tee=True)

        print(results)

        # print(self.dual_model.pprint())
        # results.write()
        # instance.solutions.load_from(results)
        # instance.pprint(filename='P:/Group_TE/GM_Uwe/PtL Robust/pyomo.txt')

        # import sys
        # f = open('P:/Group_TE/GM_Uwe/PtL Robust/pyomo.txt', 'w')
        # sys.stdout = f
        # instance.pprint()
        # f.close()

        # for v in instance.component_objects(Var):
        #     variable_dict = v.extract_values()
        #     if str(v) == 'weighting_profiles_binary':
        #         for i in v.index_set():
        #             if round(variable_dict[i]) == 1:
        #
        #                 chosen_profiles = {'Wind': self.data['Wind_' + str(i)],
        #                                    'Solar': self.data['Solar_' + str(i)]}
        #
        #                 if False:
        #                     chosen_profiles = {}
        #                     for g in [*self.data.keys()]:
        #                         index_new = self.data[g].index[:-1]
        #                         chosen_profiles[g] = self.data[g].loc[
        #                             index_new, self.data[g].columns[int(self.number_clusters) + profile]].array

        # self.chosen_profiles = chosen_profiles
        self.obj_value = instance.obj()

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, optimal_capacities, nominal, data, number_clusters, weightings, number_profiles, costs_missing_product, **kwargs):
        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.optimal_capacities = optimal_capacities
        self.nominal = nominal
        self.data = data
        self.number_clusters = number_clusters
        self.weightings = weightings
        self.number_profiles = number_profiles
        self.costs_missing_product = costs_missing_product
        self.kwargs = kwargs

        self.obj_value = None
        self.chosen_profiles = None

        self.generation_profile = None

        # Create optimization program
        self.dual_model = ConcreteModel()
        self.dual_model.TIME = RangeSet(0, self.pm_object.get_covered_period() - 1)
        self.dual_model.CLUSTER = RangeSet(0, number_clusters)  # don't reduce cluster as extreme cluster is added
        self.dual_model.PROFILES = RangeSet(0, number_profiles - 1)

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict,\
            self.scaling_capex_var_dict, self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict,\
            self.scaling_capex_lower_bound_dict, self.shut_down_down_time_dict, self.shut_down_start_up_costs,\
            self.standby_down_time_dict, self.charging_efficiency_dict, self.discharging_efficiency_dict, \
            self.minimal_soc_dict, self.maximal_soc_dict, self.ratio_capacity_power_dict, \
            self.fixed_capacity_dict = self.pm_object.get_all_technical_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components, \
            self.no_shut_down_components, self.standby_components, \
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities, \
            self.all_inputs, self.all_outputs = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        self.hourly_demand_dict, self.total_demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        """ Adjust parameters to include extreme cluster """
        # todo: adjust regarding data --> maybe prices are also uncertain

        if number_clusters > 0:
            for t in range(self.pm_object.get_covered_period()):
                for me in self.purchasable_commodities:
                    self.purchase_price_dict[(me, number_clusters, t)]\
                        = self.purchase_price_dict[(me, number_clusters - 1, t)]

                for me in self.saleable_commodities:
                    self.sell_price_dict[(me, number_clusters, t)]\
                        = self.sell_price_dict[(me, number_clusters - 1, t)]

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
        self.dual_model = self.attach_nominal_generation(self.dual_model)

        self.dual_model = self.attach_constraints(self.dual_model)
        # self.dual_model = self.attach_uncertainty_set(self.dual_model)

        # print(self.instance.pprint())