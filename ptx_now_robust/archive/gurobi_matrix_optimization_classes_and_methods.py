import itertools
from copy import deepcopy
import gurobipy as gp
import numpy as np


class GurobiMatrixOptimizationProblem:

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

    def attach_constraints(self):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object

        if False:

            self.model.addConstrs(self.available_coefficient_matrix[i, cl, :] @ self.mass_energy_available[i, cl, :]
                                  - self.emitted_coefficient_matrix[i, cl, :] @ self.mass_energy_emitted[i, cl, :]
                                  + self.purchase_coefficient_matrix[i, cl, :]
                                  @ self.mass_energy_purchase_commodity[i, cl, :]
                                  - self.sale_coefficient_matrix[i, cl, :] @ self.mass_energy_sell_commodity[i, cl, :]
                                  + self.storage_out_coefficient_matrix[i, cl, :]
                                  @ self.mass_energy_storage_out_commodities[i, cl, :]
                                  - self.storage_in_coefficient_matrix[i, cl, :]
                                  @ self.mass_energy_storage_in_commodities[i, cl, :]
                                  + self.generation_coefficient_matrix[i, cl, :] @ self.mass_energy_generation[i, cl, :]
                                  - self.component_in_coefficient_matrix[i, cl, :]
                                  @ self.mass_energy_component_in_commodities[i, cl, :]
                                  + self.component_out_coefficient_matrix[i, cl, :]
                                  @ self.mass_energy_component_out_commodities[i, cl, :]
                                  - self.standby_coefficient_matrix[i, cl, :]
                                  @ self.mass_energy_hot_standby_demand[i, cl, :]
                                  - self.demand_coefficient_matrix[i, cl, :] @ self.mass_energy_demand[i, cl, :] == 0
                                  for i, com in enumerate(self.final_commodities) for cl in self.clusters)

        self.model.addConstrs(sum(self.demand_coefficient_matrix[i, cl, :] @ self.mass_energy_demand[i, cl, :]
                                  for cl in self.clusters)
                              >= self.total_demand_dict[com]
                              for i, com in enumerate(self.final_commodities)
                              if com in self.total_demand_commodities)

        self.model.addConstrs(self.demand_coefficient_matrix[i, cl, :] @ self.mass_energy_demand[i, cl, :]
                              >= self.hourly_demand_dict[i, cl, :]
                              for i, com in enumerate(self.final_commodities)
                              if ((com in self.demanded_commodities) & (com not in self.total_demand_commodities))
                              for cl in self.clusters)

        self.model.addConstrs(
            np.full((len(self.time)), self.output_conversion_coefficients[i, self.final_commodities.index(pm_object.get_component(c).get_main_input()), j])
            @ self.mass_energy_component_out_commodities_per_component[i, j, cl, :]
            == np.ones((len(self.time))) @ self.mass_energy_component_out_commodities_per_component[i, j, cl, :]
            for i, c in enumerate(self.conversion_components)
            for j, com in enumerate(self.final_commodities)
            for cl in self.clusters)

        self.model.addConstrs(sum(self.mass_energy_component_out_commodities_per_component[i, j, cl, t]
                                  for i, c in enumerate(self.conversion_components)) ==
                              self.mass_energy_component_out_commodities[j, cl, t]
                              for j, com in enumerate(self.final_commodities)
                              for cl in self.clusters for t in self.time)

        self.model.addConstrs(
            np.ones((len(self.time))) @ self.mass_energy_component_in_commodities_per_component[i, j, cl, :] ==
            np.full((len(self.time)), self.input_conversion_coefficients[i, self.final_commodities.index(pm_object.get_component(c).get_main_input()), j])
            @ self.mass_energy_component_in_commodities_per_component[i, self.final_commodities.index(pm_object.get_component(c).get_main_input()), cl, :]
            for i, c in enumerate(self.conversion_components)
            for j, com in enumerate(self.final_commodities)
            if com != self.final_commodities.index(com)
            for cl in self.clusters)

        self.model.addConstrs(sum(self.mass_energy_component_in_commodities_per_component[i, j, cl, t]
                                  for i, c in enumerate(self.conversion_components)) ==
                              self.mass_energy_component_in_commodities[j, cl, t]
                              for j, com in enumerate(self.final_commodities)
                              for cl in self.clusters for t in self.time)

        for sc in self.conversion_components:

            if sc in self.scalable_components:

                for i in self.integer_steps:

                    self.model.addConstr(self.capacity_binary[sc, i] >= self.nominal_cap_pre[sc, i] / 1000000,
                                         name='binary_activation' + '_' + str(i) + '_constraint')

                    self.model.addConstr(self.nominal_cap_pre[sc, i]
                                         >= self.scaling_capex_lower_bound_dict[sc, i] * self.capacity_binary[sc, i],
                                         name='capacity_lower_bound' + '_' + str(i) + '_constraint')

                self.model.addConstr(sum(self.capacity_binary[sc, i] for i in self.integer_steps) <= 1,
                                     name='capacity_binary_sum' + '_' + sc + '_constraint')

                self.model.addConstr(sum(self.nominal_cap_pre[sc, i] for i in self.integer_steps) == self.nominal_cap[sc],
                                     name='final_capacity' + '_' + sc + '_constraint')

        self.model.addConstrs(self.status_on[i, cl, :] + self.status_off[i, cl, :] + self.status_standby[i, cl, :] == 1
                              for i, c in enumerate(self.conversion_components) for cl in self.clusters)

        self.model.addConstrs(self.status_on[i, cl, :] == 1
                              for i, c in enumerate(self.conversion_components)
                              if ((c not in self.shut_down_components) & (c not in self.standby_components))
                              for cl in self.clusters)

        self.model.addConstrs(self.status_off[i, cl, :] == 0
                              for i, c in enumerate(self.conversion_components)
                              if c not in self.shut_down_components
                              for cl in self.clusters)

        self.model.addConstrs(self.status_standby[i, cl, :] == 1
                              for i, c in enumerate(self.conversion_components)
                              if c not in self.standby_components
                              for cl in self.clusters)

        self.model.addConstrs(np.ones((len(self.time)))
                              @ self.mass_energy_component_in_commodities_per_component[i, j, cl, :]
                              - np.full((len(self.time)), self.M) @ self.status_on[i, cl, :] <= 0
                              for i, c in enumerate(self.conversion_components)
                              for j, com in enumerate(self.final_commodities)
                              for cl in self.clusters)

        self.model.addConstrs(self.status_off_switch_on[i, cl, :] + self.status_off_switch_off[i, cl, :] <= 1
                              for i, c in enumerate(self.conversion_components)
                              for cl in self.clusters)

        self.model.addConstrs(self.status_off[i, cl, 1:]
                              == self.status_off[i, cl, :-1]
                              + self.status_off_switch_on[i, cl, 1:]
                              - self.status_off_switch_off[i, cl, 1:]
                              for i, c in enumerate(self.conversion_components)
                              for cl in self.clusters)

        self.model.addConstrs(self.status_standby_switch_on[i, cl, :]
                             + self.status_standby_switch_off[i, cl, :] <= 1
                              for i, c in enumerate(self.conversion_components)
                              for cl in self.clusters)

        self.model.addConstrs(self.status_standby[i, cl, 1:]
                              == self.status_standby[i, cl, :-1]
                              + self.status_standby_switch_on[i, cl, 1:]
                              - self.status_standby_switch_off[i, cl, 1:]
                              for i, c in enumerate(self.conversion_components)
                              for cl in self.clusters)

        #todo: ich glaube das problem ist, dass man nicht nur einen skalar da einfügen darf sondern immer ganze Matrizen miteinander multiplizieren muss

        print(np.full((len(self.time), 1), 4).flatten().shape)
        print(self.nominal_cap.shape)

        self.model.addConstrs(
            np.ones((len(self.time)))
            @ self.mass_energy_component_in_commodities_per_component[i,
              self.final_commodities.index(pm_object.get_component(c).get_main_input()), cl, :]
            - np.full((len(self.time), 1), self.minimal_power_dict[c]).flatten() @ self.nominal_cap[i]
            >= 0
            for i, c in enumerate(self.all_components) if c in self.conversion_components
            for cl in self.clusters)

        self.model.addConstrs(
            np.ones((len(self.time)))
            @ self.mass_energy_component_in_commodities_per_component[i, j, cl, :]
            == 0
            for i, c in enumerate(self.all_components) if c not in self.conversion_components
            for j, f in enumerate(self.final_commodities)
            for cl in self.clusters)

        self.model.addConstrs(
            np.ones((len(self.time)))
            @ self.mass_energy_component_in_commodities_per_component[i, self.final_commodities.index(pm_object.get_component(c).get_main_input()), cl, :]
            >= self.nominal_cap[c] @ np.full((len(self.time)), self.minimal_power_dict[c])
            + (self.status_on[i, cl, :] - np.ones((len(self.time)))) @ np.full((len(self.time)), self.M)
            for i, c in enumerate(self.all_components) if c in self.conversion_components
            for cl in self.clusters)

        self.model.addConstrs(
            np.ones((len(self.time)))
            @ self.mass_energy_component_in_commodities_per_component[i, self.final_commodities.index(pm_object.get_component(c).get_main_input()), cl, 1:]
            - np.ones((len(self.time)))
            @ self.mass_energy_component_in_commodities[c, main_input, cl, :-2]
            >= self.nominal_cap[c] @ np.full((len(self.time)), self.ramp_up_dict[i])
            + (self.status_off_switch_off[i, cl, :] - self.status_standby_switch_off[i, cl, :])
            @ np.full((len(self.time)), self.M)
            for i, c in enumerate(self.conversion_components)
            for cl in self.clusters)

        self.model.addConstrs(
            np.ones((len(self.time)))
            @ self.mass_energy_component_in_commodities_per_component[i, self.final_commodities.index(pm_object.get_component(c).get_main_input()), cl, 1:]
            - np.ones((len(self.time)))
            @ self.mass_energy_component_in_commodities[c, main_input, cl, :-2]
            <= - self.nominal_cap[c] @ np.full((len(self.time)), self.ramp_down_dict[i])
            + (self.status_off_switch_on[i, cl, :] - self.status_standby_switch_on[i, cl, :])
            @ np.full((len(self.time)), self.M)
            for i, c in enumerate(self.conversion_components)
            for cl in self.clusters)

        dt_array = np.zeros((len(self.time)))
        st_array = np.zeros((len(self.time)))
        for t in self.time:
            for i, c in enumerate(self.shut_down_components):
                # set minimal down time after shut down

                if self.shut_down_down_time_dict[c] + t > max(self.time):
                    dt_array[i] = max(self.time) - t + 1
                else:
                    dt_array[i] = self.shut_down_down_time_dict[c]

            for i, c in enumerate(self.standby_components):

                # set minimal standby time after standby
                if self.standby_down_time_dict[c] + t > max(self.time):
                    st_array[i] = max(self.time) - t + 1
                else:
                    st_array[i] = self.standby_down_time_dict[c]

        if False:

            self.model.addConstrs((self.status_off[i, cl, 1:] - self.status_off[i, cl, :-2])
                                  - sum(self.status_off[i, cl, t + i]
                                        for i in range(dt_array[1:])) / dt_array[1:] <= 0
                                  for i, c in enumerate(self.shut_down_components)
                                  for cl in self.clusters)

            self.model.addConstrs((self.status_standby[i, cl, 1:] - self.status_standby[i, cl, :-2])
                                  - sum(self.status_standby[i, cl, t + i]
                                        for i in range(st_array[1:])) / st_array[1:] <= 0
                                  for i, c in enumerate(self.shut_down_components)
                                  for cl in self.clusters)

        # lower limit hot standby (don't create energy / commodity

        if False:
            if c in self.standby_components:

                hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]

                for com in self.final_commodities:
                    if com == hot_standby_commodity:
                        self.model.addConstr(self.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t]
                                             >= self.nominal_cap[c] * hot_standby_demand
                                             + (self.status_standby[c, t] - 1) * 1000000,
                                             name='define_lower_limit_hot_standby_demand' + name_adding)
                    else:
                        self.model.addConstr(self.mass_energy_hot_standby_demand[c, com, cl, t] == 0,
                                             name='define_lower_limit_hot_standby_demand' + name_adding)

                # upper limit got standby (don't destroy energy / commodity)
                self.model.addConstr(self.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t]
                                     <= self.nominal_cap[c] * hot_standby_demand,
                                     name='define_upper_limit_hot_standby_demand' + name_adding)

                # activate if in hot standby
                self.model.addConstr(self.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t]
                                     <= self.status_standby[c, cl, t] * 1000000,
                                     name='define_hot_standby_activation' + name_adding)

        for g in self.generator_components:

            for combi in itertools.product(self.generated_commodities, self.clusters, self.time):
                gc = combi[0]
                cl = combi[1]
                t = combi[2]

                name_adding = g + '_' + str(cl) + '_' + str(t) + '_constraint'

                generated_commodity = pm_object.get_component(g).get_generated_commodity()

                if gc == generated_commodity:
                    if pm_object.get_component(g).get_curtailment_possible():
                        # with curtailment
                        self.model.addConstr(self.mass_energy_generation[g, generated_commodity, cl, t]
                                             <= self.generation_profiles_dict[g, cl, t] * self.nominal_cap[g],
                                             name='define_generation' + name_adding)
                    else:
                        # without curtailment
                        self.model.addConstr(self.mass_energy_generation[g, generated_commodity, cl, t]
                                             == self.generation_profiles_dict[g, cl, t] * self.nominal_cap[g],
                                             name='define_generation' + name_adding)
                else:
                    # no generation
                    self.model.addConstr(self.mass_energy_generation[g, generated_commodity, cl, t] == 0,
                                         name='define_generation' + name_adding)

            name_adding = g + '_constraint'

            # Applied if generator capacity is fixed
            if pm_object.get_component(g).get_has_fixed_capacity():
                self.model.addConstr(self.nominal_cap[g] == self.fixed_capacity_dict[g],
                                     name='fixed_capacity_of_generation' + name_adding)

        for combi in itertools.product(self.storage_components, self.clusters, self.time):
            s = combi[0]
            cl = combi[1]
            t = combi[2]

            name_adding = s + '_' + str(cl) + '_' + str(t) + '_constraint'

            # storage balance
            if t != 0:
                self.model.addConstr(self.soc[s, cl, t] == self.soc[s, cl, t - 1]
                                     + self.mass_energy_storage_in_commodities[s, cl, t - 1]
                                     * self.charging_efficiency_dict[s]
                                     - self.mass_energy_storage_out_commodities[s, cl, t - 1]
                                     / self.discharging_efficiency_dict[s],
                                     name='storage_balance' + name_adding)

            if t == max(self.time):
                self.model.addConstr(self.soc[s, cl, 0] == self.soc[s, cl, t]
                                     + self.mass_energy_storage_in_commodities[s, cl, t]
                                     * self.charging_efficiency_dict[s]
                                     - self.mass_energy_storage_out_commodities[s, cl, t]
                                     / self.discharging_efficiency_dict[s],
                                     name='last_soc_equals_first_soc' + name_adding)

            # min max soc
            self.model.addConstr(self.soc[s, cl, t] <= self.maximal_soc_dict[s] * self.nominal_cap[s],
                                 name='max_soc' + name_adding)

            self.model.addConstr(self.soc[s, cl, t] >= self.minimal_soc_dict[s] * self.nominal_cap[s],
                                 name='min_soc' + name_adding)

            # upper and lower bounds charging
            self.model.addConstr(self.mass_energy_storage_in_commodities[s, cl, t]
                                 <= self.nominal_cap[s] / self.ratio_capacity_power_dict[s],
                                 name='max_soc' + name_adding)

            self.model.addConstr(self.mass_energy_storage_out_commodities[s, cl, t]
                                 / self.discharging_efficiency_dict[s]
                                 <= self.nominal_cap[s]
                                 / self.ratio_capacity_power_dict[s],
                                 name='min_soc' + name_adding)

            # storage binary --> don't allow charge and discharge at same time
            self.model.addConstr(self.storage_charge_binary[s, cl, t] + self.storage_discharge_binary[s, cl, t] <= 1,
                                 name='balance_storage_binaries' + name_adding)

            self.model.addConstr(self.mass_energy_storage_in_commodities[s, cl, t]
                                 - self.storage_charge_binary[s, cl, t] * 1000000 <= 0,
                                 name='activate_charging_binary' + name_adding)

            self.model.addConstr(self.mass_energy_storage_out_commodities[s, cl, t]
                                 - self.storage_discharge_binary[s, cl, t] * 1000000 <= 0,
                                 name='deactivate_charging_binary' + name_adding)

        # calculate investment (used to simplify constraint)
        for c in self.all_components:
            if c not in self.scalable_components:
                self.model.addConstr(self.investment[c]
                                     == self.nominal_cap[c] * self.capex_var_dict[c]
                                     + self.capex_fix_dict[c],
                                     name='calculate_investment' + c + '_constraint')
            else:
                self.model.addConstr(self.investment[c]
                                     == sum(self.nominal_cap_pre[c, i] * self.scaling_capex_var_dict[c, i]
                                            + self.scaling_capex_fix_dict[c, i] * self.capacity_binary[c, i]
                                            for i in self.integer_steps),
                                     name='calculate_investment' + c + '_constraint')

        # minimize total costs
        self.model.setObjective(sum(self.investment[c] * self.annuity_factor_dict[c] for c in self.all_components)
                                + sum(self.investment[c] * self.fixed_om_dict[c] for c in self.all_components)
                                + sum(self.mass_energy_storage_in_commodities[s, cl, t] * self.variable_om_dict[s] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters
                                      for s in self.storage_components)
                                + sum(self.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), cl, t]
                                      * self.variable_om_dict[c] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters
                                      for c in self.conversion_components)
                                + sum(self.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), cl, t]
                                      * self.variable_om_dict[g] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters for g in self.generator_components)
                                + sum(self.mass_energy_purchase_commodity[me, cl, t]
                                      * self.purchase_price_dict[me, cl, t] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters
                                      for me in self.purchasable_commodities if me in self.purchasable_commodities)
                                - sum(self.mass_energy_sell_commodity[me, cl, t] * self.sell_price_dict[me, cl, t]
                                      * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters for me in self.saleable_commodities
                                      if me in self.saleable_commodities)
                                + sum(self.status_off_switch_off[c, cl, t] * self.weightings_dict[cl]
                                      * self.shut_down_start_up_costs[c]
                                      for t in self.time for cl in self.clusters for c in self.shut_down_components),
                                gp.GRB.MINIMIZE)

    def optimize(self):

        self.model.optimize()

        print(f"Optimal objective value: {self.model.objVal}")

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

        self.pm_object = self.clone_components_which_use_parallelization()

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict,\
            self.minimal_power_dict, \
            self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
            self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, \
            self.shut_down_down_time_dict, self.shut_down_start_up_costs, self.standby_down_time_dict, \
            self.charging_efficiency_dict, self.discharging_efficiency_dict, \
            self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_technical_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components,\
            self.no_shut_down_components, self.standby_components,\
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities,\
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities, \
            self.all_inputs, self.all_outputs = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict\
            = self.pm_object.get_all_conversions()

        self.generation_profiles_dict = self.pm_object.get_generation_time_series()
        self.hourly_demand_dict, self.total_demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        self.scalable_components = self.pm_object.get_final_scalable_conversion_components_names()
        self.shut_down_components = self.pm_object.get_final_shut_down_conversion_components_names()
        self.standby_components = self.pm_object.get_final_standby_conversion_components_names()

        self.standby_commodities = []
        for c in self.standby_components:
            self.standby_commodities.append([c.get_hot_standby_demand().keys()][0])

        # Create optimization program
        self.model = gp.Model()
        self.time = range(0, self.pm_object.get_covered_period())  # no -1 because of for
        self.clusters = range(0, self.pm_object.get_number_clusters())  # no -1 because of for
        self.integer_steps = range(0, self.pm_object.integer_steps)
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.M = 1000000

        self.output_conversion_coefficients = np.zeros((len(self.conversion_components),
                                                        len(self.final_commodities),
                                                        len(self.final_commodities)))

        for k in [*self.output_conversion_tuples_dict.keys()]:
            pos_c = self.conversion_components.index(k[0])
            pos_com_1 = self.final_commodities.index(k[1])
            pos_com_2 = self.final_commodities.index(k[2])

            self.output_conversion_coefficients[pos_c, pos_com_1, pos_com_2] = self.output_conversion_tuples_dict[k]

        self.input_conversion_coefficients = np.zeros((len(self.conversion_components),
                                                       len(self.final_commodities),
                                                       len(self.final_commodities)))

        for k in [*self.input_conversion_tuples_dict.keys()]:
            pos_c = self.conversion_components.index(k[0])
            pos_com_1 = self.final_commodities.index(k[1])
            pos_com_2 = self.final_commodities.index(k[2])

            self.input_conversion_coefficients[pos_c, pos_com_1, pos_com_2] = self.input_conversion_tuples_dict[k]



        # Attach Variables

        import itertools

        self.components_index_dictionary = {}
        self.components_no_scale = []
        self.components_scale = []
        self.components_storage = []
        self.components_generators = []
        for c in self.all_components:

            if (c in self.conversion_components) & (c not in self.scalable_components):
                self.components_no_scale.append(c)
            elif (c in self.conversion_components) & (c in self.scalable_components):
                self.components_scale.append(c)
            elif c in self.storage_components:
                self.components_storage.append(c)
            elif c in self.generator_components:
                self.components_generators.append(c)

        i = 0
        for c in self.components_no_scale:
            self.components_index_dictionary[i] = c
            i += 1

        # Component variables
        self.nominal_cap = self.model.addMVar((len(self.all_components), ), lb=0)

        self.status_on = self.model.addMVar((len(self.all_components), len(self.clusters),
                                             len(self.time)),
                                            vtype='B')
        self.status_off = self.model.addMVar((len(self.all_components), len(self.clusters),
                                              len(self.time)),
                                            vtype='B')
        self.status_off_switch_on = self.model.addMVar((len(self.all_components), len(self.clusters),
                                                        len(self.time)),
                                            vtype='B')
        self.status_off_switch_off = self.model.addMVar((len(self.all_components), len(self.clusters),
                                                         len(self.time)),
                                            vtype='B')
        self.status_standby_switch_on = self.model.addMVar((len(self.all_components), len(self.clusters),
                                                            len(self.time)),
                                            vtype='B')
        self.status_standby_switch_off = self.model.addMVar((len(self.all_components), len(self.clusters),
                                                             len(self.time)),
                                            vtype='B')
        self.status_standby = self.model.addMVar((len(self.all_components), len(self.clusters),
                                                  len(self.time)),
                                            vtype='B')

        # STORAGE binaries (charging and discharging)
        self.storage_charge_binary = self.model.addMVar((len(self.all_components), len(self.clusters),
                                                         len(self.time)),
                                            vtype='B')
        self.storage_discharge_binary = self.model.addMVar((len(self.all_components), len(self.clusters),
                                                            len(self.time)),
                                            vtype='B')

        self.investment = self.model.addMVar((len(self.all_components)), lb=0)

        self.nominal_cap_pre = self.model.addVars(list(itertools.product(self.scalable_components,
                                                                         self.integer_steps)),
                                                  lb=0,
                                                  ub=[self.scaling_capex_upper_bound_dict[(s, i)]
                                                      for s in self.scalable_components
                                                      for i in self.integer_steps])
        self.capacity_binary = self.model.addVars(list(itertools.product(self.scalable_components,
                                                                         self.integer_steps)),
                                                  vtype='B')
        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component

        self.mass_energy_component_in_commodities \
            = self.model.addMVar((len(self.final_commodities),
                                  len(self.clusters), len(self.time)), lb=0)

        self.mass_energy_component_in_commodities_per_component \
            = self.model.addMVar((len(self.all_components), len(self.final_commodities),
                                  len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.all_inputs:

                if first:
                    self.component_in_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.component_in_coefficient_matrix = np.concatenate((self.component_in_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.component_in_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.component_in_coefficient_matrix = np.concatenate((self.component_in_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        self.mass_energy_component_out_commodities \
            = self.model.addMVar((len(self.final_commodities), len(self.clusters), len(self.time)), lb=0)

        self.mass_energy_component_out_commodities_per_component \
            = self.model.addMVar((len(self.conversion_components), len(self.final_commodities),
                                  len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.all_outputs:

                if first:
                    self.component_out_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.component_out_coefficient_matrix = np.concatenate((self.component_out_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.component_out_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.component_out_coefficient_matrix = np.concatenate((self.component_out_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        # Freely available commodities
        self.mass_energy_available = self.model.addMVar((len(self.final_commodities),
                                                         len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.available_commodities:

                if first:
                    self.available_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.available_coefficient_matrix = np.concatenate((self.available_coefficient_matrix,
                                                                       np.ones((1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.available_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.available_coefficient_matrix = np.concatenate((self.available_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        self.mass_energy_emitted = self.model.addMVar((len(self.final_commodities),
                                                       len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.emittable_commodities:

                if first:
                    self.emitted_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.emitted_coefficient_matrix = np.concatenate((self.emitted_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.emitted_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.emitted_coefficient_matrix = np.concatenate((self.emitted_coefficient_matrix,
                                                                      np.zeros((1, len(self.clusters),
                                                                                len(self.time)))))

            first = False

        # Charged and discharged commodities
        self.mass_energy_storage_in_commodities = self.model.addMVar((len(self.final_commodities),
                                                                      len(self.clusters), len(self.time)), lb=0)

        self.mass_energy_storage_out_commodities = self.model.addMVar((len(self.final_commodities),
                                                                       len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.storage_components:

                if first:
                    self.storage_in_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.storage_in_coefficient_matrix = np.concatenate((self.storage_in_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.storage_in_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.storage_in_coefficient_matrix = np.concatenate((self.storage_in_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        first = True
        for com in self.final_commodities:
            if com in self.storage_components:

                if first:
                    self.storage_out_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.storage_out_coefficient_matrix = np.concatenate((self.storage_out_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.storage_out_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.storage_out_coefficient_matrix = np.concatenate((self.storage_out_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        # sold and purchased commodities
        self.mass_energy_sell_commodity = self.model.addMVar((len(self.final_commodities),
                                                              len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.saleable_commodities:

                if first:
                    self.sale_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.sale_coefficient_matrix = np.concatenate((self.sale_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.sale_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.sale_coefficient_matrix = np.concatenate((self.sale_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        self.mass_energy_purchase_commodity = self.model.addMVar((len(self.final_commodities),
                                                                  len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.purchasable_commodities:

                if first:
                    self.purchase_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.purchase_coefficient_matrix = np.concatenate((self.purchase_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.purchase_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.purchase_coefficient_matrix = np.concatenate((self.purchase_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        # generated commodities
        self.mass_energy_generation = self.model.addMVar((len(self.final_commodities),
                                                          len(self.clusters), len(self.time)), lb=0)

        self.mass_energy_generation_per_generator = self.model.addMVar((len(self.generator_components),
                                                                        len(self.final_commodities),
                                                                        len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.generated_commodities:

                if first:
                    self.generation_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.generation_coefficient_matrix = np.concatenate((self.generation_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.generation_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.generation_coefficient_matrix = np.concatenate((self.generation_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        # Demanded commodities
        self.mass_energy_demand = self.model.addMVar((len(self.final_commodities),
                                                      len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.demanded_commodities:

                if first:
                    self.demand_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.demand_coefficient_matrix = np.concatenate((self.demand_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.demand_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.demand_coefficient_matrix = np.concatenate((self.demand_coefficient_matrix,
                                                                     np.zeros((1, len(self.clusters),
                                                                               len(self.time)))))

            first = False

        # Hot standby demand
        self.mass_energy_hot_standby_demand = self.model.addMVar((len(self.final_commodities),
                                                                  len(self.clusters), len(self.time)), lb=0)

        self.mass_energy_hot_standby_demand_per_component \
            = self.model.addMVar((len(self.conversion_components), len(self.final_commodities),
                                  len(self.clusters), len(self.time)), lb=0)

        first = True
        for com in self.final_commodities:
            if com in self.standby_commodities:

                if first:
                    self.standby_coefficient_matrix = np.ones((1, len(self.clusters), len(self.time)))
                else:
                    self.standby_coefficient_matrix = np.concatenate((self.standby_coefficient_matrix,
                                                                        np.ones(
                                                                            (1, len(self.clusters), len(self.time)))))
            else:
                if first:
                    self.standby_coefficient_matrix = np.zeros((1, len(self.clusters), len(self.time)))
                else:
                    self.standby_coefficient_matrix = np.concatenate((self.standby_coefficient_matrix,
                                                                        np.zeros((1, len(self.clusters),
                                                                                  len(self.time)))))

            first = False

        self.soc = self.model.addVars(list(itertools.product(self.storage_components, self.clusters, self.time)), lb=0)

        self.attach_constraints()

        self.optimize()

        # print(self.instance.pprint())
