import pyomo.environ as pyo
from copy import deepcopy

from pyomo.core import *
import pandas as pd
from dualization_from_model import dualize_from_model
from pyomo.core.expr.numeric_expr import LinearExpression
from old_code import get_dual_model_data_from_gurobi

import numpy as np

import os


class AlternatingDual:


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

        if self.fixed == 'duals':

            if 'y_free_available_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_free_available_constraint_variable = Param(dual_model.AVAILABLE_COMMODITIES,
                                                                      dual_model.TIME, initialize=self.duals['y_free_available_constraint_variable'])
            else:
                dual_model.y_free_available_constraint_variable = Param(dual_model.AVAILABLE_COMMODITIES,
                                                                        dual_model.TIME, initialize=0)
            if 'y_purchase_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_purchase_constraint_variable = Param(dual_model.PURCHASABLE_COMMODITIES,
                                                                dual_model.TIME, initialize=self.duals['y_purchase_constraint_variable'])
            else:
                dual_model.y_purchase_constraint_variable = Param(dual_model.PURCHASABLE_COMMODITIES,
                                                                  dual_model.TIME, initialize=0)

            if 'y_emit_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_emit_constraint_variable = Param(dual_model.EMITTED_COMMODITIES,
                                                            dual_model.TIME, initialize=self.duals['y_emit_constraint_variable'])
            else:
                dual_model.y_emit_constraint_variable = Param(dual_model.EMITTED_COMMODITIES,
                                                              dual_model.TIME,
                                                              initialize=0)

            if 'y_sell_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_sell_constraint_variable = Param(dual_model.SALEABLE_COMMODITIES,
                                                            dual_model.TIME, initialize=self.duals['y_sell_constraint_variable'])
            else:
                dual_model.y_sell_constraint_variable = Param(dual_model.SALEABLE_COMMODITIES,
                                                              dual_model.TIME,
                                                              initialize=0)

            if 'y_balance_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_balance_constraint_variable = Param(dual_model.ME_COMMODITIES, dual_model.TIME,
                                                               initialize=self.duals['y_balance_constraint_variable'])
            else:
                dual_model.y_balance_constraint_variable = Param(dual_model.ME_COMMODITIES, dual_model.TIME,
                                                                 initialize=0)

            if 'y_demand_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_demand_constraint_variable = Param(dual_model.DEMANDED_COMMODITIES, initialize=self.duals['y_demand_constraint_variable'])
            else:
                dual_model.y_demand_constraint_variable = Param(dual_model.DEMANDED_COMMODITIES,
                                                                initialize=0)

            if 'y_out_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_out_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                           dual_model.ME_COMMODITIES, dual_model.TIME,
                                                           initialize=self.duals['y_out_constraint_variable'])
            else:
                dual_model.y_out_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                             dual_model.ME_COMMODITIES, dual_model.TIME,
                                                             initialize=0)

            if 'y_in_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_in_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                          dual_model.ME_COMMODITIES, dual_model.TIME,
                                                          initialize=self.duals['y_in_constraint_variable'])
            else:
                dual_model.y_in_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                            dual_model.ME_COMMODITIES, dual_model.TIME,
                                                            initialize=0)

            if 'y_conv_cap_ub_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_conv_cap_ub_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                   dual_model.TIME, initialize=self.duals['y_conv_cap_ub_constraint_variable'])
            else:
                dual_model.y_conv_cap_ub_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                     dual_model.TIME, initialize=0)

            if 'y_conv_cap_lb_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_conv_cap_lb_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                   dual_model.TIME, initialize=self.duals['y_conv_cap_lb_constraint_variable'])
            else:
                dual_model.y_conv_cap_lb_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                     dual_model.TIME, initialize=0)

            if 'y_conv_cap_ramp_up_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_conv_cap_ramp_up_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                        dual_model.TIME, initialize=self.duals['y_conv_cap_ramp_up_constraint_variable'])
            else:
                dual_model.y_conv_cap_ramp_up_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                          dual_model.TIME, initialize=0)

            if 'y_conv_cap_ramp_down_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_conv_cap_ramp_down_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                          dual_model.TIME, initialize=self.duals['y_conv_cap_ramp_down_constraint_variable'])
            else:
                dual_model.y_conv_cap_ramp_down_constraint_variable = Param(dual_model.CONVERSION_COMPONENTS,
                                                                            dual_model.TIME, initialize=0)

            if 'y_generation_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_generation_constraint_variable = Param(dual_model.GENERATORS,
                                                                  dual_model.ME_COMMODITIES,
                                                                  dual_model.TIME, initialize=self.duals['y_generation_constraint_variable'])
            else:
                dual_model.y_generation_constraint_variable = Param(dual_model.GENERATORS,
                                                                    dual_model.ME_COMMODITIES,
                                                                    dual_model.TIME, initialize=0)

            if 'y_soc_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_soc_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                           initialize=self.duals['y_soc_constraint_variable'])
            else:
                dual_model.y_soc_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                             initialize=0)

            if 'y_soc_ub_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_soc_ub_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                              initialize=self.duals['y_soc_ub_constraint_variable'])
            else:
                dual_model.y_soc_ub_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                                initialize=0)

            if 'y_soc_lb_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_soc_lb_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                              initialize=self.duals['y_soc_lb_constraint_variable'])
            else:
                dual_model.y_soc_lb_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                                initialize=0)

            if 'y_soc_charge_limit_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_soc_charge_limit_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                                        initialize=self.duals['y_soc_charge_limit_constraint_variable'])
            else:
                dual_model.y_soc_charge_limit_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                                          initialize=0)

            if 'y_soc_discharge_limit_constraint_variable' in [*self.duals.keys()]:
                dual_model.y_soc_discharge_limit_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                                           initialize=self.duals['y_soc_discharge_limit_constraint_variable'])
            else:
                dual_model.y_soc_discharge_limit_constraint_variable = Param(dual_model.STORAGES, dual_model.TIME,
                                                                             initialize=0)

            dual_model.uncertainty = Var(['Wind', 'Solar'], dual_model.TIME, bounds=(0, 1))

        else:
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
            uncertainty_new = {}
            if isinstance(self.uncertainty, dict):
                for k in [*self.uncertainty.keys()]:
                    uncertainty_new[k] = self.uncertainty[k]
            else:
                for i in range(self.uncertainty.shape[0]):
                    if i > max(dual_model.TIME):
                        break

                    if self.optimal_capacities['Wind'] > 0:
                        uncertainty_new[('Wind', i)] = self.uncertainty[i, 0]
                    if self.optimal_capacities['Solar'] > 0:
                        uncertainty_new[('Solar', i)] = self.uncertainty[i, 0]

            dual_model.uncertainty = Param(dual_model.GENERATORS, dual_model.TIME, initialize=uncertainty_new)

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
        if False:
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

        if self.fixed == 'uncertainty':

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
                            if conversion[0] == c:
                                output_commodity = conversion[2]
                                lhs.append(- dm.y_out_constraint_variable[c, output_commodity, t]
                                           * self.output_conversion_tuples_dict[c, main_input, output_commodity])

                        for conversion in self.input_conversion_tuples:
                            if conversion[0] == c:
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
                       + sum(
                    dm.y_generation_constraint_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t]
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
        instance = self.dual_model.create_instance()

        results = opt.solve(instance, tee=True)

        for v in instance.component_objects(Var):
            variable_dict = v.extract_values()
            if variable_dict:
                self.duals[str(v)] = {}
            else:
                continue

            if self.fixed == 'duals':
                uncertainty_array = np.zeros([max(self.dual_model.TIME)+1, 2])

            for i in v.index_set():
                if self.fixed == 'duals':
                    if str(v) == 'uncertainty':
                        if i[0] == 'Wind':
                            n = 0
                        else:
                            n = 1
                        uncertainty_array[i[1], n] = variable_dict[i]

                else:
                    self.duals[str(v)][i] = variable_dict[i]

            if self.fixed == 'duals':
                self.uncertainty = uncertainty_array
        self.obj_value = instance.obj()

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, optimal_capacities, uncertainty=None, duals=None, fixed='duals', **kwargs):
        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.optimal_capacities = optimal_capacities
        self.kwargs = kwargs

        if uncertainty is None:
            self.uncertainty = {}
        else:
            self.uncertainty = uncertainty

        if duals is None:
            self.duals = {}
        else:
            self.duals = duals

        self.fixed = fixed

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

        if self.fixed == 'duals':
            self.dual_model = self.attach_uncertainty_set(self.dual_model)

        # print(self.instance.pprint())