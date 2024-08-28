import itertools
import gurobipy as gp
from ptx_now._helper_optimization import anticipate_bigM


class GurobiDualProblem:

    def attach_variables(self):

        self.y_free_available_constraint_variable \
            = self.model.addVars(list(itertools.product(self.available_commodities, self.time, self.clusters)),
                                 lb=0, name='free')

        self.y_purchase_constraint_variable \
            = self.model.addVars(list(itertools.product(self.purchasable_commodities, self.time, self.clusters)),
                                 lb=0, name='purchase')

        self.y_emit_constraint_variable \
            = self.model.addVars(list(itertools.product(self.emittable_commodities, self.time, self.clusters)),
                                 lb=0, name='emit')

        self.y_sell_constraint_variable \
            = self.model.addVars(list(itertools.product(self.saleable_commodities, self.time, self.clusters)),
                                 lb=0, name='sell')

        self.y_balance_constraint_variable \
            = self.model.addVars(list(itertools.product(self.final_commodities, self.time, self.clusters)),
                                 name='balance', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        self.y_weekly_production_balance_variable \
            = self.model.addVars(list(itertools.product(self.demanded_commodities, self.clusters)), name='weekly_production', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        self.y_out_constraint_variable \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.final_commodities, self.time, self.clusters)), name='x_out', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        self.y_in_constraint_variable \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.final_commodities, self.time, self.clusters)), name='x_in', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        self.y_conv_cap_ub_constraint_variable \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.time, self.clusters)), lb=-gp.GRB.INFINITY, ub=0, name='cap_ub')

        self.y_conv_cap_lb_constraint_variable \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.time, self.clusters)), lb=0, name='cap_lb')

        self.y_conv_cap_ramp_up_constraint_variable \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.time, self.clusters)), lb=-gp.GRB.INFINITY, ub=0, name='cap_ramp_up')

        self.y_conv_cap_ramp_down_constraint_variable \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.time, self.clusters)), lb=-gp.GRB.INFINITY, ub=0, name='cap_ramp_down')

        self.y_generation_constraint_variable_active \
            = self.model.addVars(list(itertools.product(self.generator_components, self.generated_commodities, self.time, self.clusters)), lb=-gp.GRB.INFINITY, ub=0, name='generation')

        self.y_soc_constraint_variable \
            = self.model.addVars(list(itertools.product(self.storage_components, self.time, self.clusters)), name='soc', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        self.y_last_soc_constraint_variable \
            = self.model.addVars(list(itertools.product(self.storage_components, self.clusters)),
                                 name='last_soc', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        self.y_soc_ub_constraint_variable \
            = self.model.addVars(list(itertools.product(self.storage_components, self.time, self.clusters)), lb=-gp.GRB.INFINITY, ub=0, name='soc_ub')

        self.y_soc_lb_constraint_variable \
            = self.model.addVars(list(itertools.product(self.storage_components, self.time, self.clusters)), lb=0, name='soc_lb')

        self.y_soc_charge_limit_constraint_variable \
            = self.model.addVars(list(itertools.product(self.storage_components, self.time, self.clusters)), lb=-gp.GRB.INFINITY, ub=0, name='soc_charge_limit')

        self.y_soc_discharge_limit_constraint_variable \
            = self.model.addVars(list(itertools.product(self.storage_components, self.time, self.clusters)), lb=-gp.GRB.INFINITY, ub=0, name='soc_discharge_limit')

        self.auxiliary_variable \
            = self.model.addVars(list(itertools.product(self.generator_components, self.generated_commodities, self.time, self.profiles)), lb=-gp.GRB.INFINITY, ub=0, name='auxiliary')

        self.weighting_profiles_binary \
            = self.model.addVars(self.profiles, vtype=gp.GRB.BINARY, name='profile_weighting')

        self.chosen_profile_variable \
            = self.model.addVars(list(itertools.product(self.generator_components, self.time)), name='chosen_profile', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        # self.objective = self.model.addVar(lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY, name='objective')

    def attach_generation(self):

        self.generation_profiles_certain_dict = {}
        for g in [*self.nominal.keys()]:
            if g not in self.generator_components:
                continue

            for n in [*self.nominal[g].keys()]:
                if n == max(self.clusters):
                    break
                for t in self.time:
                    self.generation_profiles_certain_dict[(g, t, n)] = self.nominal[g][n][t]

        self.generation_profiles_uncertain_dict = {}
        profile_counter = {'Wind': 0,
                           'Solar': 0}
        for c in self.data.columns:

            if c.split('_')[0] not in self.generator_components:
                continue

            if 'Wind' in c:
                g = 'Wind'
            else:
                g = 'Solar'

            for t in self.time:
                ind = self.data.index[t]
                self.generation_profiles_uncertain_dict[(g, profile_counter[g], t)] = self.data.loc[ind, c]

            profile_counter[g] = profile_counter[g] + 1

    def attach_constraints(self):

        combinations = itertools.product(self.final_commodities, self.time, self.clusters)
        for combi in combinations:
            com = combi[0]
            t = combi[1]
            cl = combi[2]

            if ' ' in com:
                com_name = com
                com_name = com_name.replace(' ', '_')
            else:
                com_name = com

            name_adding = str(com_name) + '_' + str(t) + '_' + str(cl)

            if com in self.available_commodities:
                self.model.addConstr(self.y_balance_constraint_variable[com, t, cl] <= 0,
                                     name='x_free_rule_' + name_adding)

            if com in self.emittable_commodities:
                self.model.addConstr(- self.y_balance_constraint_variable[com, t, cl] <= 0,
                                     name='x_emit_rule_' + name_adding)

            if com in self.purchasable_commodities:
                self.model.addConstr(self.y_balance_constraint_variable[com, t, cl]
                                     <= self.purchase_price_dict[com, cl, t] * self.weightings_dict[cl],
                                     name='x_buy_rule_' + name_adding)

            if com in self.saleable_commodities:
                self.model.addConstr(- self.y_balance_constraint_variable[com, t, cl]
                                     <= - self.sell_price_dict[com, cl, t] * self.weightings_dict[cl],
                                     name='x_sell_rule_' + name_adding)

            for g in self.generator_components:
                if com == self.pm_object.get_component(g).get_generated_commodity():
                    self.model.addConstr(self.y_balance_constraint_variable[com, t, cl] + self.y_generation_constraint_variable_active[g, com, t, cl]
                                         <= self.variable_om_dict[g] * self.weightings_dict[cl],
                                         name='x_generation_rule_' + name_adding + '_' + g)

            for c in self.conversion_components:
                main_input = self.pm_object.get_component(c).get_main_input()
                inputs = self.pm_object.get_component(c).get_inputs()

                if ' ' in c:
                    c_name = c
                    c_name = c_name.replace(' ', '_')
                else:
                    c_name = c

                if com in inputs:
                    if com == main_input:
                        lhs = [- self.y_balance_constraint_variable[com, t, cl]
                               + self.y_conv_cap_ub_constraint_variable[c, t, cl]
                               + self.y_conv_cap_lb_constraint_variable[c, t, cl]]

                        if t > 0:
                            lhs.append(self.y_conv_cap_ramp_up_constraint_variable[c, t, cl])
                            lhs.append(self.y_conv_cap_ramp_down_constraint_variable[c, t, cl])

                        if t < max(self.time):  # consider ramping
                            lhs.append(- self.y_conv_cap_ramp_up_constraint_variable[c, t + 1, cl])
                            lhs.append(- self.y_conv_cap_ramp_down_constraint_variable[c, t + 1, cl])

                        for conversion in self.output_conversion_tuples:
                            if conversion[0] == c:
                                output_commodity = conversion[2]
                                lhs.append(- self.y_out_constraint_variable[c, output_commodity, t, cl]
                                           * self.output_conversion_tuples_dict[c, main_input, output_commodity])

                        for conversion in self.input_conversion_tuples:
                            if conversion[0] == c:
                                other_input_commodity = conversion[2]
                                lhs.append(- self.y_in_constraint_variable[c, other_input_commodity, t, cl]
                                           * self.input_conversion_tuples_dict[c, main_input, other_input_commodity])
                    else:
                        lhs = [- self.y_balance_constraint_variable[com, t, cl]]

                        for conversion in self.input_conversion_tuples:
                            # input to input conversions only possible if s != main input
                            if com == conversion[2]:
                                lhs.append(self.y_in_constraint_variable[c, com, t, cl])

                    self.model.addConstr(sum(lhs) <= 0, name='x_in_rule_' + name_adding + '_' + c_name)

                if (c, main_input, com) in self.output_conversion_tuples:

                    self.model.addConstr(self.y_balance_constraint_variable[com, t, cl] + self.y_out_constraint_variable[c, com, t, cl]
                                         <= self.variable_om_dict[c] * self.weightings_dict[cl],
                                         name='x_out_rule_' + name_adding + '_' + c_name)

            if com in self.storage_components:
                lhs = [- self.y_balance_constraint_variable[com, t, cl]]
                if t < max(self.time):
                    lhs.append(- self.y_soc_constraint_variable[com, t + 1, cl] * self.charging_efficiency_dict[com])
                else:
                    lhs.append(- self.y_last_soc_constraint_variable[com, cl] * self.charging_efficiency_dict[com])

                self.model.addConstr(sum(lhs) <= self.variable_om_dict[com] * self.weightings_dict[cl],
                                     name='x_charge_rule_' + name_adding)

                lhs = [self.y_balance_constraint_variable[com, t, cl]]
                if t < max(self.time):
                    lhs.append(self.y_soc_constraint_variable[com, t + 1, cl] / self.discharging_efficiency_dict[com])
                else:
                    lhs.append(self.y_last_soc_constraint_variable[com, cl] / self.discharging_efficiency_dict[com])

                self.model.addConstr(sum(lhs) <= 0, name='x_discharge_rule_' + name_adding)

                lhs = [self.y_soc_ub_constraint_variable[com, t, cl] + self.y_soc_lb_constraint_variable[com, t, cl]]
                if t == max(self.time):
                    lhs.append(self.y_soc_constraint_variable[com, t, cl]
                               - self.y_last_soc_constraint_variable[com, cl])

                elif t == 0:
                    lhs.append(- self.y_soc_constraint_variable[com, t + 1, cl]
                               + self.y_last_soc_constraint_variable[com, cl])

                else:
                    lhs.append(self.y_soc_constraint_variable[com, t, cl]
                               - self.y_soc_constraint_variable[com, t + 1, cl])

                self.model.addConstr(sum(lhs) <= 0, name='x_soc_rule_' + name_adding)

    def attach_relaxed_weekly_demand(self):

        self.y_demand_constraint_variable \
            = self.model.addVars(list(itertools.product(self.demanded_commodities, self.clusters)), name='demand', lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        combinations = itertools.product(self.final_commodities, self.clusters)
        for combi in combinations:
            com = combi[0]
            cl = combi[1]

            name_adding = str(com) + '_' + str(cl)

            if com in self.demanded_commodities:

                self.model.addConstr(
                    self.y_demand_constraint_variable[com, cl] + self.y_weekly_production_balance_variable[
                        com, cl] <= 0,
                    name='x_weekly_demand_rule_' + name_adding)

                self.model.addConstr(- self.y_weekly_production_balance_variable[com, cl] <= 0,
                                     name='x_production_surplus_rule_' + name_adding)

                self.model.addConstr(- self.y_weekly_production_balance_variable[com, cl] >= - self.weightings_dict[
                    cl] * self.costs_missing_product,
                                     name='x_production_deficit_rule_' + name_adding)

                for t in self.time:
                    self.model.addConstr(
                        - self.y_balance_constraint_variable[com, t, cl] - self.y_demand_constraint_variable[
                            com, cl] <= 0,
                        name='x_demand_rule_' + name_adding + '_' + str(t))

    def attach_fixed_weekly_demand(self):

        self.y_demand_constraint_variable \
            = self.model.addVars(list(itertools.product(self.demanded_commodities, self.clusters)), name='demand',
                                 lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        combinations = itertools.product(self.final_commodities, self.clusters)
        for combi in combinations:
            com = combi[0]
            cl = combi[1]

            name_adding = str(com) + '_' + str(cl)

            if com in self.demanded_commodities:

                for t in self.time:
                    self.model.addConstr(- self.y_balance_constraint_variable[com, t, cl] + self.y_demand_constraint_variable[com, cl] <= 0,
                                         name='x_demand_rule_' + name_adding + '_' + str(t))

    def attach_total_demand(self):

        self.y_demand_constraint_variable \
            = self.model.addVars(self.demanded_commodities, name='demand',
                                 lb=-gp.GRB.INFINITY, ub=gp.GRB.INFINITY)

        combinations = itertools.product(self.final_commodities, self.clusters)
        for combi in combinations:
            com = combi[0]
            cl = combi[1]

            name_adding = str(com) + '_' + str(cl)

            if com in self.demanded_commodities:
                for t in self.time:
                    self.model.addConstr(
                        - self.y_balance_constraint_variable[com, t, cl] + self.y_demand_constraint_variable[com] * self.weightings[cl] <= 0,
                        name='x_demand_rule_' + name_adding + '_' + str(t))

    def attach_uncertainty_set(self):
        self.model.addConstr(sum(self.weighting_profiles_binary[p] for p in self.profiles) == 1, name='balance_profiles')

        for t in self.time:
            for p in self.profiles:
                for g in self.generator_components:

                    name_addition = str(t) + '_' + str(p) + '_' + g

                    com = self.pm_object.get_component(g).get_generated_commodity()
                    self.model.addConstr(self.auxiliary_variable[g, com, t, p]
                                         <= self.y_generation_constraint_variable_active[g, com, t, max(self.clusters)] * self.generation_profiles_uncertain_dict[g, p, t] * self.optimal_capacities[g]
                                         + (1 - self.weighting_profiles_binary[p]) * 10000000,
                                         name='auxiliary_activation_' + name_addition)

        self.model.addConstr(sum(self.generation_profiles_uncertain_dict['Solar', p, t] * self.weighting_profiles_binary[p]
                                 for t in self.time for p in self.profiles) >= 0,
                             name='minimal_capacity_factor_solar')

        self.model.addConstr(sum(self.generation_profiles_uncertain_dict['Wind', p, t] * self.weighting_profiles_binary[p]
                                 for t in self.time for p in self.profiles) >= 0,
                             name='minimal_capacity_factor_wind')

    def attach_objective_function(self):

        if self.demand_type == 'relaxed_weekly':
            self.model.setObjective(sum(- self.y_demand_constraint_variable[s, n] * self.total_demand_dict[s] / (8760 / len(self.time))
                                        for s in self.demanded_commodities for n in self.clusters)
                                    + sum((self.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                                        - self.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                                        + self.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                                        + self.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                                       * self.optimal_capacities[c]
                                       for t in self.time for c in self.conversion_components for n in self.clusters)
                                 + sum(self.y_generation_constraint_variable_active[g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                                       * self.optimal_capacities[g] * self.generation_profiles_certain_dict[g, t, n]
                                       for n in self.clusters if n < max(self.clusters) for t in self.time for g in self.generator_components)
                                 + sum(self.auxiliary_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t, p]
                                       for g in self.generator_components for t in self.time for p in self.profiles)
                                 + sum((self.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                                        - self.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                                        + self.y_soc_charge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]
                                        + self.y_soc_discharge_limit_constraint_variable[s, t, n] * self.ratio_capacity_power_dict[s]) * self.optimal_capacities[s]
                                       for t in self.time for s in self.storage_components for n in self.clusters),
                                    gp.GRB.MAXIMIZE)

        elif self.demand_type == 'fixed_weekly':
            self.model.setObjective(
                sum(self.y_demand_constraint_variable[s, n] * self.total_demand_dict[s] / (8760 / len(self.time))
                    for s in self.demanded_commodities for n in self.clusters)
                + sum((self.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                       - self.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                       + self.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                       + self.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                      * self.optimal_capacities[c]
                      for t in self.time for c in self.conversion_components for n in self.clusters)
                + sum(self.y_generation_constraint_variable_active[
                          g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                      * self.optimal_capacities[g] * self.generation_profiles_certain_dict[g, t, n]
                      for n in self.clusters if n < max(self.clusters) for t in self.time for g in
                      self.generator_components)
                + sum(self.auxiliary_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t, p]
                      for g in self.generator_components for t in self.time for p in self.profiles)
                + sum((self.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                       - self.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]
                       + self.y_soc_charge_limit_constraint_variable[s, t, n] / self.ratio_capacity_power_dict[s]
                       + self.y_soc_discharge_limit_constraint_variable[s, t, n] / self.ratio_capacity_power_dict[s]) *
                      self.optimal_capacities[s]
                      for t in self.time for s in self.storage_components for n in self.clusters),
                gp.GRB.MAXIMIZE)
        else:
            self.model.setObjective(
                sum(self.y_demand_constraint_variable[s] * self.total_demand_dict[s]
                    for s in self.demanded_commodities)
                + sum((self.y_conv_cap_ub_constraint_variable[c, t, n] * self.maximal_power_dict[c]
                       + self.y_conv_cap_lb_constraint_variable[c, t, n] * self.minimal_power_dict[c]
                       + self.y_conv_cap_ramp_up_constraint_variable[c, t, n] * self.ramp_up_dict[c]
                       + self.y_conv_cap_ramp_down_constraint_variable[c, t, n] * self.ramp_down_dict[c])
                      * self.optimal_capacities[c]
                      for t in self.time for c in self.conversion_components for n in self.clusters)
                + sum(self.y_generation_constraint_variable_active[
                          g, self.pm_object.get_component(g).get_generated_commodity(), t, n]
                      * self.optimal_capacities[g] * self.generation_profiles_certain_dict[g, t, n]
                      for n in self.clusters if n < max(self.clusters) for t in self.time for g in
                      self.generator_components)
                + sum(self.auxiliary_variable[g, self.pm_object.get_component(g).get_generated_commodity(), t, p]
                      for g in self.generator_components for t in self.time for p in self.profiles)
                + sum((self.y_soc_ub_constraint_variable[s, t, n] * self.maximal_soc_dict[s]
                       + self.y_soc_lb_constraint_variable[s, t, n] * self.minimal_soc_dict[s]) *
                      self.optimal_capacities[s]
                      for t in self.time for s in self.storage_components for n in self.clusters),
                gp.GRB.MAXIMIZE)

    def optimize(self):

        self.attach_variables()
        self.attach_generation()
        self.attach_constraints()

        if self.demand_type == 'relaxed_weekly':
            self.attach_relaxed_weekly_demand()

        elif self.demand_type == 'fixed_weekly':
            self.attach_fixed_weekly_demand()

        elif self.demand_type == 'total':
            self.attach_total_demand()

        self.attach_uncertainty_set()
        self.attach_objective_function()

        def save_results():
            self.continuous_variables = [{'y_free_available_constraint_variable': self.y_free_available_constraint_variable},
                                         {'y_purchase_constraint_variable': self.y_purchase_constraint_variable},
                                         {'y_emit_constraint_variable': self.y_emit_constraint_variable},
                                         {'y_sell_constraint_variable': self.y_sell_constraint_variable},
                                         {'y_balance_constraint_variable': self.y_balance_constraint_variable},
                                         {'y_demand_constraint_variable': self.y_demand_constraint_variable},
                                         {'y_weekly_production_balance_variable': self.y_weekly_production_balance_variable},
                                         {'y_in_constraint_variable': self.y_in_constraint_variable},
                                         {'y_in_constraint_variable': self.y_in_constraint_variable},
                                         {'y_conv_cap_ub_constraint_variable': self.y_conv_cap_ub_constraint_variable},
                                         {'y_conv_cap_lb_constraint_variable': self.y_conv_cap_lb_constraint_variable},
                                         {'y_conv_cap_ramp_up_constraint_variable': self.y_conv_cap_ramp_up_constraint_variable},
                                         {'y_soc_constraint_variable': self.y_soc_constraint_variable},
                                         {'y_soc_ub_constraint_variable': self.y_soc_ub_constraint_variable},
                                         {'y_soc_lb_constraint_variable': self.y_soc_lb_constraint_variable},
                                         {'y_soc_charge_limit_constraint_variable': self.y_soc_charge_limit_constraint_variable},
                                         {'y_soc_discharge_limit_constraint_variable': self.y_soc_discharge_limit_constraint_variable},
                                         {'auxiliary_variable': self.auxiliary_variable},
                                         {'weighting_profiles_binary': self.weighting_profiles_binary},
                                         {'chosen_profile_variable': self.chosen_profile_variable},
                                         {'objective': self.objective}]

            for p in self.profiles:
                if self.weighting_profiles_binary[p].X == 1:
                    pos_wind = self.data.columns[p*2]
                    pos_solar = self.data.columns[p*2+1]

                    print(p)
                    self.chosen_profiles = {'Wind': self.data[pos_wind],
                                            'Solar': self.data[pos_solar]}

        # self.model.Params.LogToConsole = 0
        self.model.Params.Threads = 120
        self.model.optimize()
        self.instance = self

        self.objective_function_value = self.model.objVal

        # print(self.model.getConstrs())
        self.model.write('/home/localadmin/Dokumente/gurobi.lp')

        save_results()

    def __init__(self, pm_object, solver, optimal_capacities, nominal, data, number_clusters, weightings,
                 number_profiles, costs_missing_product, demand_type, **kwargs):
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.nominal = nominal
        self.weightings = weightings
        self.optimal_capacities = optimal_capacities
        self.data = data
        self.costs_missing_product = costs_missing_product
        self.chosen_profiles = None
        self.demand_type = demand_type

        self.objective_function_value = None

        self.model_type = 'gurobi'

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict, \
            self.minimal_power_dict, \
            self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
            self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, \
            self.shut_down_down_time_dict, self.shut_down_start_up_costs, self.standby_down_time_dict, \
            self.charging_efficiency_dict, self.discharging_efficiency_dict, \
            self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_technical_component_parameters()

        # ecological parameters
        self.installation_co2_emissions_dict, self.fixed_yearly_co2_emissions_dict, \
            self.variable_co2_emissions_dict, self.disposal_co2_emissions_dict \
            = self.pm_object.get_co2_emission_data()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversions()

        # time series data
        self.generation_profiles_dict = self.pm_object.get_generation_time_series()
        self.hourly_demand_dict, self.total_demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.available_specific_CO2_emissions_dict = self.pm_object.get_available_specific_co2_emissions_time_series()
        self.emitted_specific_CO2_emissions_dict = self.pm_object.get_emitted_specific_co2_emissions_time_series()
        self.purchase_specific_CO2_emissions_dict = self.pm_object.get_purchase_specific_co2_emissions_time_series()
        self.sale_specific_CO2_emissions_dict = self.pm_object.get_sale_specific_co2_emissions_time_series()

        # sets
        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        self.scalable_components, self.not_scalable_components, self.shut_down_components, \
            self.no_shut_down_components, self.standby_components, \
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities, \
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities, \
            self.all_inputs, self.all_outputs = self.pm_object.get_commodity_sets()

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

        # Adjust purchase & selling price
        if number_clusters > 0:
            for t in range(self.pm_object.get_covered_period()):
                for me in self.purchasable_commodities:
                    self.purchase_price_dict[(me, number_clusters, t)] \
                        = self.purchase_price_dict[(me, number_clusters - 1, t)]

                for me in self.saleable_commodities:
                    self.sell_price_dict[(me, number_clusters, t)] \
                        = self.sell_price_dict[(me, number_clusters - 1, t)]

        # Create optimization program
        self.model = gp.Model()
        self.time = range(0, self.pm_object.get_covered_period())
        self.clusters = range(0, number_clusters + 1)
        self.weightings_dict = self.weightings

        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.bigM = anticipate_bigM(self.pm_object)

        self.profiles = range(0, number_profiles)

        self.y_free_available_constraint_variable = self.y_purchase_constraint_variable = self.y_emit_constraint_variable \
            = self.y_sell_constraint_variable = self.y_balance_constraint_variable = self.y_demand_constraint_variable \
            = self.y_weekly_production_balance_variable = self.y_out_constraint_variable = self.y_in_constraint_variable \
            = self.y_conv_cap_ub_constraint_variable = self.y_conv_cap_lb_constraint_variable = self.y_conv_cap_ramp_up_constraint_variable \
            = self.y_conv_cap_ramp_down_constraint_variable = self.y_generation_constraint_variable_active \
            = self.y_soc_constraint_variable = self.y_soc_ub_constraint_variable = self.y_soc_lb_constraint_variable \
            = self.y_soc_charge_limit_constraint_variable = self.y_soc_discharge_limit_constraint_variable \
            = self.auxiliary_variable = self.weighting_profiles_binary = self.chosen_profile_variable = self.objective = None
