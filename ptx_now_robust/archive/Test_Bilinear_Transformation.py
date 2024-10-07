import pyomo.environ as pyo
from copy import deepcopy

from pyomo.core import *
import pandas as pd
from dualization_from_model import dualize_from_model
from pyomo.core.expr.numeric_expr import LinearExpression
from old_code import get_dual_model_data_from_gurobi
from pyomo.core import Binary

import numpy as np

import os


class MixedIntDualRepresentative_v1:

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

        dual_model.y_demand_constraint_variable = Var(dual_model.DEMANDED_COMMODITIES, bounds=(None, None))

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

        dual_model.y_generation_constraint_variable_inactive = Var(dual_model.GENERATORS,
                                                                   dual_model.GENERATED_COMMODITIES,
                                                                   dual_model.TIME, dual_model.CLUSTER,
                                                                   bounds=(None, 0))

        dual_model.y_soc_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                   bounds=(None, None))
        dual_model.y_soc_ub_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                      bounds=(None, 0))
        dual_model.y_soc_lb_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                      bounds=(None, 0))
        dual_model.y_soc_charge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                                bounds=(None, 0))
        dual_model.y_soc_discharge_limit_constraint_variable = Var(dual_model.STORAGES, dual_model.TIME, dual_model.CLUSTER,
                                                                   bounds=(None, 0))

        # dual_model.weighting_profiles_binary = Var(dual_model.CLUSTER, dual_model.PROFILES, bounds=(0, 1))
        dual_model.weighting_profiles_binary = Var(dual_model.CLUSTER, dual_model.PROFILES, within=Binary)
        dual_model.weighting_profiles_perT_binary = Var(dual_model.CLUSTER, dual_model.PROFILES, dual_model.TIME, within=Binary)

        return dual_model

    def attach_purchase_price_time_series_to_optimization_problem(self, dual_model):
        dual_model.purchase_price = Param(dual_model.PURCHASABLE_COMMODITIES, dual_model.TIME, initialize=self.purchase_price_dict)
        return dual_model

    def attach_sale_price_time_series_to_optimization_problem(self, dual_model):
        dual_model.selling_price = Param(dual_model.SALEABLE_COMMODITIES, dual_model.TIME, initialize=self.sell_price_dict)
        return dual_model

    def attach_demand_time_series_to_optimization_problem(self, dual_model):
        dual_model.commodity_demand = Param(dual_model.DEMANDED_COMMODITIES, dual_model.TIME, initialize=self.demand_dict)
        return dual_model

    def attach_weightings_time_series_to_optimization_problem(self, dual_model):
        dual_model.weightings = Param(dual_model.CLUSTER, initialize=self.weightings)
        return dual_model

    def attach_nominal_generation(self, dual_model):

        generation_profiles_dict = {}

        cluster_profile = {}
        for n in range(int(self.number_clusters + 1)):
            cluster_profile[n] = 0

        for c in self.data.columns:
            n = int(self.data.loc['cluster', c])

            for ind in self.data.index:
                if ind != 'cluster':
                    if ind == max(dual_model.TIME):
                        break
                    generation_profiles_dict[('Wind', n, cluster_profile[n], int(ind))] = self.data.loc[ind, c]

            cluster_profile[n] = cluster_profile[n] + 1

        dual_model.generation_profile = Param(['Wind'], dual_model.CLUSTER, dual_model.PROFILES, dual_model.TIME,
                                              initialize=generation_profiles_dict)

        self.generation_profile = generation_profiles_dict
        return dual_model

    def attach_uncertainty_set(self, dual_model):

        if True:

            def balance_profile_binaries(dm, n):
                return sum(dm.weighting_profiles_binary[n, p] for p in dm.PROFILES) == 1
            dual_model.balance_profile_binaries_con = Constraint(dual_model.CLUSTER, rule=balance_profile_binaries)

            def balance_profile_binaries_perT(dm, n, p, t):
                return dm.weighting_profiles_binary[n, p] == dm.weighting_profiles_perT_binary[n, p, t]
            dual_model.balance_profile_binaries_perT_con = Constraint(dual_model.CLUSTER, dual_model.PROFILES,
                                                                      dual_model.TIME,
                                                                      rule=balance_profile_binaries_perT)

            def activate_active_generation(dm, g, n, p, t):
                generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
                return 0 <= dm.y_generation_constraint_variable_active[g, generated_commodity, t, n] \
                       + dm.weighting_profiles_perT_binary[n, p, t] * dm.generation_profile[g, n, p, t] \
                                                                  * self.optimal_capacities[g]
            dual_model.activate_active_generation_con = Constraint(dual_model.GENERATORS, dual_model.CLUSTER,
                                                                   dual_model.PROFILES, dual_model.TIME,
                                                                   rule=activate_active_generation)

            if True:
                def min_renewable_generation_rule(dm, g):
                    return sum(dm.generation_profile[g, n, p, t] * dm.weighting_profiles_binary[n, p] * dm.weightings[n]
                               for t in dm.TIME for n in dm.CLUSTER for p in dm.PROFILES) >= 0.3 * 8760
                dual_model.min_renewable_generation_con = Constraint(dual_model.GENERATORS,
                                                                     rule=min_renewable_generation_rule)

        if False:

            def limit_hourly_min_generation(dm, g, t):
                return dm.generation_nominal[g, t] + dm.uncertainty_negative[g, t] >= self.kwargs['min_hourly_utilization'][g][t]
            dual_model.limit_hourly_min_generation_con = Constraint(dual_model.GENERATORS, dual_model.TIME,
                                                                    rule=limit_hourly_min_generation)

            def limit_hourly_max_generation(dm, g, t):
                return dm.generation_nominal[g, t] + dm.uncertainty_positive[g, t] <= self.kwargs['max_hourly_utilization'][g][t]
            dual_model.limit_hourly_max_generation_con = Constraint(dual_model.GENERATORS, dual_model.TIME,
                                                                    rule=limit_hourly_max_generation)

        if False:
            def overall_both_min_rule(dm):
                return sum(dm.uncertainty[g, t] for g in dm.GENERATORS for t in dm.TIME) \
                       >= self.kwargs['min_overall_value_both']

            model.overall_both_min_con = Constraint(rule=overall_both_min_rule)

            def overall_both_max_rule(dm):
                return sum(dm.uncertainty[g, t] for g in dm.GENERATORS for t in dm.TIME) \
                       <= self.kwargs['max_overall_value_both']

            model.overall_both_max_con = Constraint(rule=overall_both_max_rule)

        if False:

            def overall_wind_min_rule(dm):
                return sum(dm.generation_nominal['Wind', t] + dm.uncertainty_negative_binary['Wind', t]
                           * self.kwargs['min_hourly_utilization']['Wind'][t] for t in dm.TIME) / (max(dm.TIME) + 1) \
                       >= self.kwargs['min_overall_value_wind']

            dual_model.overall_wind_min_con = Constraint(rule=overall_wind_min_rule)

            def overall_wind_max_rule(dm):
                return sum(dm.generation_nominal['Wind', t] + dm.uncertainty_positive_binary['Wind', t]
                           * self.kwargs['max_hourly_utilization']['Wind'][t] for t in dm.TIME) / (max(dm.TIME) + 1) \
                       <= self.kwargs['max_overall_value_wind']

            dual_model.overall_wind_max_con = Constraint(rule=overall_wind_max_rule)

            def overall_solar_min_rule(dm):
                return sum(dm.generation_nominal['Solar', t] + dm.uncertainty_negative_binary['Solar', t]
                           * self.kwargs['min_hourly_utilization']['Solar'][t] for t in dm.TIME) / (max(dm.TIME) + 1) \
                       >= self.kwargs['min_overall_value_solar']

            dual_model.overall_solar_min_con = Constraint(rule=overall_solar_min_rule)

            def overall_solar_max_rule(dm):
                return sum(dm.generation_nominal['Solar', t] + dm.uncertainty_positive_binary['Solar', t]
                           * self.kwargs['max_hourly_utilization']['Solar'][t] for t in dm.TIME) / (max(dm.TIME) + 1) \
                       <= self.kwargs['max_overall_value_solar']

            dual_model.overall_solar_max_con = Constraint(rule=overall_solar_max_rule)

        if False:
            def weekly_both_min_rule(dm):
                return sum(dm.generation_nominal[g, t] + dm.uncertainty_negative_binary[g, t]
                           * self.kwargs['min_hourly_utilization'][g][t]
                           for g in dm.GENERATORS for t in dm.TIME) \
                       >= self.kwargs['min_weekly_value_both']
            dual_model.weekly_both_min_con = Constraint(rule=weekly_both_min_rule)

            def weekly_both_max_rule(dm):
                return sum(dm.generation_nominal[g, t] + dm.uncertainty_positive_binary[g, t]
                           * self.kwargs['max_hourly_utilization'][g][t]
                           for g in dm.GENERATORS for t in dm.TIME) \
                       <= self.kwargs['max_weekly_value_both']

            dual_model.weekly_both_max_con = Constraint(rule=weekly_both_max_rule)

        if False:

            def weekly_wind_min_rule(dm, t):
                if t <= max(dm.TIME) - 167:
                    return sum(dm.generation_nominal['Wind', n] + dm.uncertainty_negative_binary['Wind', n]
                               * self.kwargs['min_hourly_utilization']['Wind'][n] for n in range(t, t+168)) / 168 \
                           >= self.kwargs['min_weekly_value_wind']
                else:
                    return Constraint.Skip
            dual_model.weekly_wind_min_con = Constraint(dual_model.TIME, rule=weekly_wind_min_rule)

            def weekly_wind_max_rule(dm, t):
                if t <= max(dm.TIME) - 167:
                    return sum(dm.generation_nominal['Wind', n] + dm.uncertainty_positive_binary['Wind', n]
                               * self.kwargs['max_hourly_utilization']['Wind'][n] for n in range(t, t+168)) / 168 \
                           <= self.kwargs['max_weekly_value_wind']
                else:
                    return Constraint.Skip
            dual_model.weekly_wind_max_con = Constraint(dual_model.TIME, rule=weekly_wind_max_rule)

            def weekly_solar_min_rule(dm, t):
                if t <= max(dm.TIME) - 167:
                    return sum(dm.generation_nominal['Solar', n] + dm.uncertainty_negative_binary['Solar', n]
                               * self.kwargs['min_hourly_utilization']['Solar'][n] for n in range(t, t+168)) / 168 \
                           >= self.kwargs['min_weekly_value_solar']
                else:
                    return Constraint.Skip
            dual_model.weekly_solar_min_con = Constraint(dual_model.TIME, rule=weekly_solar_min_rule)

            def weekly_solar_max_rule(dm, t):
                if t <= max(dm.TIME) - 167:
                    return sum(dm.generation_nominal['Solar', n] + dm.uncertainty_positive_binary['Solar', n]
                               * self.kwargs['max_hourly_utilization']['Solar'][n] for n in range(t, t+168)) / 168 \
                           <= self.kwargs['max_weekly_value_solar']
                else:
                    return Constraint.Skip
            dual_model.weekly_solar_max_con = Constraint(dual_model.TIME, rule=weekly_solar_max_rule)

        return dual_model

    def attach_constraints(self, model):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

        def x_free_rule(dm, s, t, n):  # x_free >= 0 --> constraint is <=
            if s in self.available_commodities:
                return dm.y_balance_constraint_variable[s, t, n] + self.dual_model.y_free_available_constraint_variable[
                    s, t, n] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_free_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER, rule=x_free_rule)

        def x_emit_rule(dm, s, t, n):
            if s in self.emittable_commodities:
                return - dm.y_balance_constraint_variable[s, t, n] + self.dual_model.y_emit_constraint_variable[s, t, n] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_emit_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER, rule=x_emit_rule)

        def x_buy_rule(dm, s, t, n):
            if s in self.purchasable_commodities:
                return dm.y_balance_constraint_variable[s, t, n] + dm.y_purchase_constraint_variable[s, t, n] \
                       <= self.purchase_price_dict[s, t] * dm.weightings[n]
            else:
                return Constraint.Skip

        self.dual_model.x_buy_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER, rule=x_buy_rule)

        def x_sell_rule(dm, s, t, n):
            if s in self.saleable_commodities:
                return - dm.y_balance_constraint_variable[s, t, n] + dm.y_sell_constraint_variable[s, t, n] \
                       <= - self.sell_price_dict[s, t] * dm.weightings[n]
            else:
                return Constraint.Skip

        self.dual_model.x_sell_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER, rule=x_sell_rule)

        def x_demand_rule(dm, s, t, n):
            if s in self.demanded_commodities:
                return - dm.y_balance_constraint_variable[s, t, n] \
                       + dm.y_demand_constraint_variable[s] * dm.weightings[n] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_demand_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER,
                                                  rule=x_demand_rule)

        def x_generation_rule(dm, g, s, t, n):
            generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
            if s == generated_commodity:
                return dm.y_balance_constraint_variable[s, t, n] \
                       + dm.y_generation_constraint_variable_active[g, s, t, n] <= dm.variable_om[g]
            else:
                return Constraint.Skip
        self.dual_model.x_generation_con = Constraint(self.dual_model.GENERATORS, self.dual_model.ME_COMMODITIES,
                                                      self.dual_model.TIME, self.dual_model.CLUSTER,
                                                      rule=x_generation_rule)

        def x_curtailment_rule(dm, s, t, n): # todo: Only if set as possible & adjust when more generators
            return - dm.y_balance_constraint_variable[s, t, n] <= 0
        self.dual_model.x_curtailment_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                       self.dual_model.CLUSTER, rule=x_curtailment_rule)

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

                return sum(lhs) <= dm.variable_om[c]

            else:
                return Constraint.Skip

        self.dual_model.x_in_con = Constraint(self.dual_model.CONVERSION_COMPONENTS, self.dual_model.ME_COMMODITIES,
                                              self.dual_model.TIME, self.dual_model.CLUSTER, rule=x_in_rule)

        def x_out_rule(dm, c, s, t, n):
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, s) in self.output_conversion_tuples:
                return dm.y_balance_constraint_variable[s, t, n] \
                       + dm.y_out_constraint_variable[c, s, t, n] <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_out_con = Constraint(self.dual_model.CONVERSION_COMPONENTS,
                                               self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER,
                                               rule=x_out_rule)

        if True:
            def x_charge_rule(dm, s, t, n):
                if s in self.storage_components:

                    lhs = [- dm.y_balance_constraint_variable[s, t, n] + dm.y_soc_charge_limit_constraint_variable[s, t, n]]

                    if t < max(dm.TIME):
                        lhs.append(- dm.y_soc_constraint_variable[s, t + 1, n] * self.charging_efficiency_dict[s])
                    else:
                        lhs.append(- dm.y_soc_constraint_variable[s, t, n] * self.charging_efficiency_dict[s])

                    return sum(lhs) <= dm.variable_om[s]
                else:
                    return Constraint.Skip

            self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME, self.dual_model.CLUSTER,
                                                      rule=x_charge_rule)

            def x_discharge_variable_rule(dm, s, t, n):

                if s in self.storage_components:

                    lhs = [
                        dm.y_balance_constraint_variable[s, t, n] + dm.y_soc_discharge_limit_constraint_variable[s, t, n]]

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
                return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                              - dm.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                              + dm.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                              + dm.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS for n in dm.CLUSTER) \
                       + sum(dm.y_generation_constraint_variable_positive[g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                             * self.optimal_capacities[g]
                             * sum(dm.generation_profile[g, n, p, t] for p in dm.PROFILES)
                             for n in dm.CLUSTER for t in dm.TIME for g in dm.GENERATORS) * 0 \
                       + sum(dm.y_generation_constraint_variable_negative[
                                 g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                             * self.optimal_capacities[g]
                             * sum(dm.generation_profile[g, n, p, t] for p in dm.PROFILES) * (-1)
                             for n in dm.CLUSTER for t in dm.TIME for g in dm.GENERATORS) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                              - dm.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                              + dm.y_soc_charge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]
                              + dm.y_soc_discharge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[
                                  s]) * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components for n in dm.CLUSTER)

            if False:
                return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                              - dm.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                              + dm.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                              + dm.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS for n in dm.CLUSTER) \
                       + sum(dm.y_generation_constraint_variable_positive[g, self.pm_object.get_component(g).get_generated_commodity(), t, n, p]
                             * self.optimal_capacities[g]
                             * (dm.generation_profile[g, n, 0, t] + (dm.generation_profile[g, n, 0, t] - dm.generation_profile[g, n, p, t]) * 1) for p in dm.PROFILES
                             for n in dm.CLUSTER for t in dm.TIME for g in dm.GENERATORS) \
                       + sum(dm.y_generation_constraint_variable_negative[g, self.pm_object.get_component(g).get_generated_commodity(), t, n, p]
                             * self.optimal_capacities[g]
                             * (dm.generation_profile[g, n, 0, t] + (dm.generation_profile[g, n, 0, t] - dm.generation_profile[g, n, p, t]) * 0) for p in dm.PROFILES
                             for n in dm.CLUSTER for t in dm.TIME for g in dm.GENERATORS) \
                       + sum((dm.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                              - dm.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                              + dm.y_soc_charge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]
                              + dm.y_soc_discharge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[
                                  s]) * self.optimal_capacities[s]
                             for t in dm.TIME for s in dm.STORAGES if s in self.storage_components for n in dm.CLUSTER)
            if True:
                return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES) \
                       + sum((dm.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                              - dm.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                              + dm.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                              + dm.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                             * self.optimal_capacities[c]
                             for t in dm.TIME for c in dm.CONVERSION_COMPONENTS for n in dm.CLUSTER) \
                       + sum(dm.y_generation_constraint_variable_active[g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                             * self.optimal_capacities[g]
                             * sum(dm.generation_profile[g, n, p, t] for p in dm.PROFILES)
                             for n in dm.CLUSTER for t in dm.TIME for g in dm.GENERATORS) \
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

        opt.options["mipgap"] = 0.05
        opt.options["NonConvex"] = 2
        instance = self.dual_model.create_instance()

        results = opt.solve(instance, tee=True)
        print(results)

        # print(self.dual_model.pprint())
        # results.write()
        # instance.solutions.load_from(results)

        chosen_profiles = {}
        chosen_profiles['Wind'] = {}
        for v in instance.component_objects(Var):
            variable_dict = v.extract_values()
            if str(v) == 'weighting_profiles_binary':
                print(variable_dict)
                for i in v.index_set():
                    if round(variable_dict[i]) == 1:
                        cluster = i[0]
                        profile = i[1]

                        index_new = self.data.index[:-1]
                        chosen_profiles['Wind'][cluster] = self.data.loc[index_new, self.data.columns[cluster*self.number_profiles + profile]].array

            if str(v) == 'y_generation_constraint_variable_active':
                print('')

            if str(v) == 'y_generation_constraint_variable_inactive':
                print('')

            if str(v) == 'y_out_constraint_variable':
                print('')

            if str(v) == 'y_balance_constraint_variable':
                print('')

            if str(v) == 'y_demand_constraint_variable':
                print('')

        self.chosen_profiles = chosen_profiles
        self.obj_value = instance.obj()

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, optimal_capacities, data, number_clusters, weightings, number_profiles, **kwargs):
        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.optimal_capacities = optimal_capacities
        self.data = data
        self.number_clusters = number_clusters
        self.weightings = weightings
        self.number_profiles = number_profiles
        self.kwargs = kwargs

        self.obj_value = None
        self.chosen_profiles = None

        self.generation_profile = None

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, self.maximal_power_dict, self.ramp_up_dict, \
            self.ramp_down_dict, self.scaling_capex_var_dict, self.scaling_capex_fix_dict, \
            self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, self.shut_down_down_time_dict, \
            self.shut_down_start_up_costs, self.standby_down_time_dict, self.charging_efficiency_dict, \
            self.discharging_efficiency_dict, self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities \
            = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()

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
        self.dual_model.CLUSTER = RangeSet(0, number_clusters)
        self.dual_model.PROFILES = RangeSet(0, number_profiles - 1)
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
        self.dual_model = self.attach_uncertainty_set(self.dual_model)

        # print(self.instance.pprint())