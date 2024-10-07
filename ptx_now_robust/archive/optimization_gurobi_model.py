import itertools
import gurobipy as gp
from ptx_now._helper_optimization import anticipate_bigM


class OptimizationGurobiModel:

    def attach_technical_variables(self):

        # Component variables
        self.nominal_cap = self.model.addVars(self.all_components, lb=0)

        self.status_on = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                   self.clusters,
                                                                   self.time)),
                                            vtype='B')
        self.status_off = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                    self.clusters,
                                                                    self.time)),
                                             vtype='B')
        self.status_off_switch_on = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                              self.clusters,
                                                                              self.time)),
                                                       vtype='B')
        self.status_off_switch_off = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                               self.clusters,
                                                                               self.time)),
                                                        vtype='B')
        self.status_standby_switch_on = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                                  self.clusters,
                                                                                  self.time)),
                                                           vtype='B')
        self.status_standby_switch_off = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                                   self.clusters,
                                                                                   self.time)),
                                                            vtype='B')
        self.status_standby = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                        self.clusters,
                                                                        self.time)),
                                                 vtype='B')

        # STORAGE binaries (charging and discharging)
        self.storage_charge_binary = self.model.addVars(list(itertools.product(self.storage_components,
                                                                               self.clusters,
                                                                               self.time)),
                                                        vtype='B')
        self.storage_discharge_binary = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                  self.clusters,
                                                                                  self.time)),
                                                           vtype='B')

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

        self.mass_energy_component_in_commodities = self.model.addVars(
            list(itertools.product(self.conversion_components,
                                   self.all_inputs,
                                   self.clusters,
                                   self.time)),
            lb=0)
        self.mass_energy_component_out_commodities \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.all_outputs, self.clusters,
                                                        self.time)),
                                 lb=0)

        # Freely available commodities
        self.mass_energy_available = self.model.addVars(list(itertools.product(self.available_commodities,
                                                                               self.clusters,
                                                                               self.time)),
                                                        lb=0)
        self.mass_energy_emitted = self.model.addVars(list(itertools.product(self.emittable_commodities,
                                                                             self.clusters,
                                                                             self.time)),
                                                      lb=0)

        # Charged and discharged commodities
        self.mass_energy_storage_in_commodities = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                            self.clusters,
                                                                                            self.time)),
                                                                     lb=0)
        self.mass_energy_storage_out_commodities = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                             self.clusters,
                                                                                             self.time)),
                                                                      lb=0)
        self.soc = self.model.addVars(list(itertools.product(self.storage_components,
                                                             self.clusters,
                                                             self.time)),
                                      lb=0)

        # sold and purchased commodities
        self.mass_energy_sell_commodity = self.model.addVars(list(itertools.product(self.saleable_commodities,
                                                                                    self.clusters,
                                                                                    self.time)),
                                                             lb=0)
        self.mass_energy_purchase_commodity = self.model.addVars(list(itertools.product(self.purchasable_commodities,
                                                                                        self.clusters,
                                                                                        self.time)), lb=0)

        # generated commodities
        self.mass_energy_generation = self.model.addVars(list(itertools.product(self.generator_components,
                                                                                self.generated_commodities,
                                                                                self.clusters,
                                                                                self.time)),
                                                         lb=0)

        # Demanded commodities
        self.mass_energy_demand = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                            self.clusters,
                                                                            self.time)),
                                                     lb=0)

        # Hot standby demand
        self.mass_energy_hot_standby_demand = self.model.addVars(list(itertools.product(self.standby_components,
                                                                                        self.final_commodities,
                                                                                        self.clusters,
                                                                                        self.time)),
                                                                 lb=0)

        self.objective_economic = self.model.addVar()
        self.objective_ecologic = self.model.addVar()

    def attach_economic_variables(self):

        self.investment = self.model.addVars(self.all_components, lb=0)

        self.restart_costs = self.model.addVars(list(itertools.product(self.shut_down_components, self.clusters,
                                                                       self.time)))

    def attach_multi_objective_variables(self):

        self.slack_economical = self.model.addVar(lb=0)
        self.slack_ecological = self.model.addVar(lb=0)

    def attach_technical_constraints(self):

        pm_object = self.pm_object

        for combi in itertools.product(self.clusters, self.time):

            cl = combi[0]
            t = combi[1]

            for com in self.final_commodities:
                commodity_object = pm_object.get_commodity(com)
                equation_lhs = []
                equation_rhs = []

                name_adding = com + '_' + str(cl) + '_' + str(t) + '_constraint'

                # mass energy balance constraint
                # Sets mass energy balance for all components
                # produced (out), generated, discharged, available and purchased commodities
                #   = emitted, sold, demanded, charged and used (in) commodities

                if commodity_object.is_available():
                    equation_lhs.append(self.mass_energy_available[com, cl, t])
                if commodity_object.is_emittable():
                    equation_lhs.append(-self.mass_energy_emitted[com, cl, t])
                if commodity_object.is_purchasable():
                    equation_lhs.append(self.mass_energy_purchase_commodity[com, cl, t])
                if commodity_object.is_saleable():
                    equation_lhs.append(-self.mass_energy_sell_commodity[com, cl, t])
                if commodity_object.is_demanded():
                    equation_lhs.append(-self.mass_energy_demand[com, cl, t])
                if com in self.storage_components:
                    equation_lhs.append(
                        self.mass_energy_storage_out_commodities[com, cl, t]
                        - self.mass_energy_storage_in_commodities[com, cl, t])
                if com in self.generated_commodities:
                    equation_lhs.append(sum(self.mass_energy_generation[g, com, cl, t]
                                            for g in self.generator_components
                                            if pm_object.get_component(g).get_generated_commodity() == com))

                for c in self.conversion_components:
                    if (c, com) in self.output_tuples:
                        equation_lhs.append(self.mass_energy_component_out_commodities[c, com, cl, t])

                    if (c, com) in self.input_tuples:
                        equation_rhs.append(self.mass_energy_component_in_commodities[c, com, cl, t])

                    # hot standby demand
                    if c in self.standby_components:
                        hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                        if com == hot_standby_commodity:
                            equation_rhs.append(self.mass_energy_hot_standby_demand[c, com, cl, t])

                self.model.addConstr(sum(equation_lhs) == sum(equation_rhs),
                                     name='balancing_' + name_adding)

                # Sets commodities, which are demanded
                if com in self.demanded_commodities:
                    if com not in self.total_demand_commodities:  # Case where demand needs to be satisfied in every t
                        self.model.addConstr(self.mass_energy_demand[com, cl, t] >= self.hourly_demand_dict[com, cl, t],
                                             name='hourly_demand_satisfaction_' + name_adding)

            # output commodities
            for c in self.all_components:

                component_object = pm_object.get_component(c)

                name_adding = c + '_' + str(cl) + '_' + str(t) + '_constraint'

                if component_object.get_component_type() == 'conversion':

                    for oc in self.all_outputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        outputs = self.pm_object.get_component(c).get_outputs()

                        if oc in [*outputs.keys()]:
                            self.model.addConstr(self.mass_energy_component_out_commodities[c, oc, cl, t] ==
                                                 self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                                 * self.output_conversion_tuples_dict[c, main_input, oc],
                                                 name='commodity_conversion_output_' + oc + '_' + str(cl) + '_' + str(t)
                                                      + '_constraint')
                        else:
                            self.model.addConstr(self.mass_energy_component_out_commodities[c, oc, cl, t] == 0,
                                                 name='commodity_conversion_output_' + oc + '_' + str(cl) + '_' + str(t)
                                                      + '_constraint')

                    for ic in self.all_inputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        inputs = pm_object.get_component(c).get_inputs()
                        if ic in [*inputs.keys()]:
                            if ic != main_input:
                                self.model.addConstr(self.mass_energy_component_in_commodities[c, ic, cl, t] ==
                                                     self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                                     * self.input_conversion_tuples_dict[c, main_input, ic],
                                                     name='commodity_conversion_input_' + ic + '_' + str(
                                                         cl) + '_' + str(t) + '_constraint')
                        else:
                            self.model.addConstr(self.mass_energy_component_in_commodities[c, ic, cl, t] == 0,
                                                 name='commodity_conversion_input_' + ic + '_' + str(cl) + '_' + str(t)
                                                      + '_constraint')

                    main_input = pm_object.get_component(c).get_main_input()

                    self.model.addConstr(
                        self.status_on[c, cl, t] + self.status_off[c, cl, t] + self.status_standby[c, cl, t] == 1,
                        name='balance_component_status' + name_adding)

                    # If component can not be shut off or put in hot standby, the status is always on
                    if (c not in self.shut_down_components) & (c not in self.standby_components):
                        self.model.addConstr(self.status_on[c, cl, t] == 1,
                                             name='no_shutdown_or_standby' + name_adding)
                    elif c not in self.shut_down_components:
                        self.model.addConstr(self.status_off[c, cl, t] == 0,
                                             name='no_shutdown' + name_adding)
                    elif c not in self.standby_components:
                        self.model.addConstr(self.status_standby[c, cl, t] == 0,
                                             name='no_standby' + name_adding)

                    # Set binary to 1 if component is active
                    self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                         - self.status_on[c, cl, t] * self.bigM[c] <= 0,
                                         name='active_component' + name_adding)

                    # Balance switch off
                    self.model.addConstr(self.status_off_switch_on[c, cl, t]
                                         + self.status_off_switch_off[c, cl, t] <= 1,
                                         name='balance_status_off_switch' + name_adding)

                    # Define switch on / off constraint
                    if t > 0:
                        self.model.addConstr(self.status_off[c, cl, t]
                                             == self.status_off[c, cl, t - 1]
                                             + self.status_off_switch_on[c, cl, t]
                                             - self.status_off_switch_off[c, cl, t],
                                             name='define_status_on_off_switch' + name_adding)

                    # Balance switch standby
                    self.model.addConstr(self.status_standby_switch_on[c, cl, t]
                                         + self.status_standby_switch_off[c, cl, t] <= 1,
                                         name='balance_status_standby_switch' + name_adding)

                    # Define switch on / standby constraint
                    if t > 0:
                        self.model.addConstr(self.status_standby[c, cl, t]
                                             == self.status_standby[c, cl, t - 1]
                                             + self.status_standby_switch_on[c, cl, t]
                                             - self.status_standby_switch_off[c, cl, t],
                                             name='define_status_on_standby_switch' + name_adding)

                    # Set upper bound conversion
                    self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                         <= self.nominal_cap[c] * self.maximal_power_dict[c],
                                         name='set_upper_bound_conversion' + name_adding)

                    # Set lower bound conversion
                    self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                         >= self.nominal_cap[c] * self.minimal_power_dict[c]
                                         + (self.status_on[c, cl, t] - 1) * self.bigM[c],
                                         name='set_lower_bound_conversion' + name_adding)

                    if t > 0:
                        # ramp up limitations
                        self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                             - self.mass_energy_component_in_commodities[c, main_input, cl, t - 1]
                                             <= self.nominal_cap[c] * self.ramp_up_dict[c]
                                             + (self.status_off_switch_off[c, cl, t]
                                                + self.status_standby_switch_off[c, cl, t]) * self.bigM[c],
                                             name='set_ramp_up_limitations' + name_adding)

                        # ramp down limitations
                        self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                             - self.mass_energy_component_in_commodities[c, main_input, cl, t - 1]
                                             >= - (self.nominal_cap[c] * self.ramp_down_dict[c]
                                                   + (self.status_off_switch_on[c, cl, t]
                                                      + self.status_standby_switch_on[c, cl, t]) * self.bigM[c]),
                                             name='set_ramp_down_limitations' + name_adding)

                    if c in self.shut_down_components:

                        # set minimal downtime after shut down
                        if self.shut_down_down_time_dict[c] + t > max(self.time):
                            dt = max(self.time) - t + 1
                        else:
                            dt = self.shut_down_down_time_dict[c]

                        if True:

                            if t > 0:
                                self.model.addConstr((self.status_off[c, cl, t] - self.status_off[c, cl, t - 1])
                                                     - sum(self.status_off[c, cl, t + i]
                                                           for i in range(dt)) / dt <= 0,
                                                     name='set_down_time' + name_adding)

                    # lower limit hot standby (don't create energy / commodity
                    if c in self.standby_components:

                        hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                        hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]

                        for com in self.final_commodities:
                            if com == hot_standby_commodity:
                                self.model.addConstr(
                                    self.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t]
                                    >= self.nominal_cap[c] * hot_standby_demand
                                    + (self.status_standby[c, cl, t] - 1) * self.bigM[c] * hot_standby_demand,
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
                                             <= self.status_standby[c, cl, t] * self.bigM[c],
                                             name='define_hot_standby_activation' + name_adding)

                        # set minimal standby time after standby
                        if self.standby_down_time_dict[c] + t > max(self.time):
                            st = max(self.time) - t + 1
                        else:
                            st = self.standby_down_time_dict[c]

                        if t > 0:
                            self.model.addConstr((self.status_standby[c, cl, t] - self.status_standby[c, cl, t - 1])
                                                 - sum(self.status_standby[c, cl, t + i]
                                                       for i in range(st)) / st <= 0,
                                                 name='set_standby_time' + name_adding)

                if component_object.get_component_type() == 'generator':

                    gc = pm_object.get_component(c).get_generated_commodity()

                    if pm_object.get_component(c).get_curtailment_possible():
                        # with curtailment
                        self.model.addConstr(self.mass_energy_generation[c, gc, cl, t]
                                             <= self.generation_profiles_dict[c, cl, t] * self.nominal_cap[c],
                                             name='define_generation' + name_adding)
                    else:
                        # without curtailment
                        self.model.addConstr(self.mass_energy_generation[c, gc, cl, t]
                                             == self.generation_profiles_dict[c, cl, t] * self.nominal_cap[c],
                                             name='define_generation' + name_adding)

                if component_object.get_component_type() == 'storage':

                    # storage balance
                    if t != 0:
                        self.model.addConstr(self.soc[c, cl, t] == self.soc[c, cl, t - 1]
                                             + self.mass_energy_storage_in_commodities[c, cl, t - 1]
                                             * self.charging_efficiency_dict[c]
                                             - self.mass_energy_storage_out_commodities[c, cl, t - 1]
                                             / self.discharging_efficiency_dict[c],
                                             name='storage_balance' + name_adding)

                    # first soc = last soc
                    if False:
                        if t == max(self.time):
                            self.model.addConstr(self.soc[c, cl, 0] == self.soc[c, cl, t]
                                                 + self.mass_energy_storage_in_commodities[c, cl, t]
                                                 * self.charging_efficiency_dict[c]
                                                 - self.mass_energy_storage_out_commodities[c, cl, t]
                                                 / self.discharging_efficiency_dict[c],
                                                 name='last_soc_equals_first_soc' + name_adding)

                    # min max soc
                    self.model.addConstr(self.soc[c, cl, t] <= self.maximal_soc_dict[c] * self.nominal_cap[c],
                                         name='max_soc' + name_adding)

                    self.model.addConstr(self.soc[c, cl, t] >= self.minimal_soc_dict[c] * self.nominal_cap[c],
                                         name='min_soc' + name_adding)

                    # upper and lower bounds charging
                    self.model.addConstr(self.mass_energy_storage_in_commodities[c, cl, t]
                                         <= self.nominal_cap[c] / self.ratio_capacity_power_dict[c],
                                         name='max_soc' + name_adding)

                    self.model.addConstr(self.mass_energy_storage_out_commodities[c, cl, t]
                                         / self.discharging_efficiency_dict[c]
                                         <= self.nominal_cap[c]
                                         / self.ratio_capacity_power_dict[c],
                                         name='min_soc' + name_adding)

                    # storage binary --> don't allow charge and discharge at same time
                    self.model.addConstr(
                        self.storage_charge_binary[c, cl, t] + self.storage_discharge_binary[c, cl, t] <= 1,
                        name='balance_storage_binaries' + name_adding)

                    self.model.addConstr(self.mass_energy_storage_in_commodities[c, cl, t]
                                         - self.storage_charge_binary[c, cl, t] * self.bigM[c] <= 0,
                                         name='activate_charging_binary' + name_adding)

                    self.model.addConstr(self.mass_energy_storage_out_commodities[c, cl, t]
                                         - self.storage_discharge_binary[c, cl, t] * self.bigM[c] <= 0,
                                         name='deactivate_charging_binary' + name_adding)

        # instead of first soc = last soc we can also say total in = total out
        for c in self.storage_components:
            self.model.addConstr(sum(self.mass_energy_storage_in_commodities[c, cl, t] * self.weightings_dict[cl]
                                     for cl in self.clusters for t in self.time) * self.charging_efficiency_dict[c] ==
                                 sum(self.mass_energy_storage_out_commodities[c, cl, t] * self.weightings_dict[cl]
                                     for cl in self.clusters for t in self.time) / self.discharging_efficiency_dict[c],
                                 name='in_storage_equals_out_storage')

        # commodities with total demand
        for com in self.demanded_commodities:
            if com in self.total_demand_commodities:
                self.model.addConstr(sum(self.mass_energy_demand[com, cl, t] * self.weightings_dict[cl]
                                         for cl in self.clusters
                                         for t in self.time)
                                     >= self.total_demand_dict[com],
                                     name='total_demand_satisfaction_' + com + '_constraint')

        for sc in self.scalable_components:
            for i in self.integer_steps:
                self.model.addConstr(self.capacity_binary[sc, i] >= self.nominal_cap_pre[sc, i] / self.bigM[sc],
                                     name='binary_activation' + '_' + str(i) + '_constraint')

                self.model.addConstr(self.nominal_cap_pre[sc, i]
                                     >= self.scaling_capex_lower_bound_dict[sc, i] * self.capacity_binary[sc, i],
                                     name='capacity_lower_bound' + '_' + str(i) + '_constraint')

            self.model.addConstr(sum(self.capacity_binary[sc, i] for i in self.integer_steps) <= 1,
                                 name='capacity_binary_sum' + '_' + sc + '_constraint')

            self.model.addConstr(sum(self.nominal_cap_pre[sc, i] for i in self.integer_steps) == self.nominal_cap[sc],
                                 name='final_capacity' + '_' + sc + '_constraint')

        for c in self.all_components:

            component_object = pm_object.get_component(c)

            # Applied if capacity is fixed
            name_adding = '_' + c + '_constraint'
            if component_object.get_has_fixed_capacity():
                self.model.addConstr(self.nominal_cap[c] == self.fixed_capacity_dict[c],
                                     name='fixed_capacity_of' + name_adding)

    def attach_economic_constraints(self):

        pm_object = self.pm_object

        for combi in itertools.product(self.clusters, self.time):

            cl = combi[0]
            t = combi[1]

            # output commodities
            for c in self.all_components:

                component_object = pm_object.get_component(c)

                name_adding = c + '_' + str(cl) + '_' + str(t) + '_constraint'

                if component_object.get_component_type() == 'conversion':

                    if c in self.shut_down_components:

                        if t < max(self.time):
                            self.model.addConstr(
                                self.restart_costs[c, cl, t] >= self.nominal_cap[c] * self.weightings_dict[cl]
                                * self.shut_down_start_up_costs[c]
                                - (1 - self.status_off_switch_off[c, cl, t]) * self.bigM[c] * self.weightings_dict[cl]
                                * self.shut_down_start_up_costs[c],
                                name='set_restart_costs' + name_adding)
                        else:
                            self.model.addConstr(
                                self.restart_costs[c, cl, t] >= self.nominal_cap[c] * self.weightings_dict[cl]
                                * self.shut_down_start_up_costs[c]
                                - (self.status_on[c, cl, t] - self.status_off_switch_off[c, cl, t]) * self.bigM[c]
                                * self.weightings_dict[cl] * self.shut_down_start_up_costs[c],
                                name='set_restart_costs' + name_adding)

        for c in self.all_components:

            name_adding = '_' + c + '_constraint'

            # calculate investment (used to simplify constraint)
            if c not in self.scalable_components:
                if c not in self.generator_components:
                    self.model.addConstr(self.investment[c]
                                         == self.nominal_cap[c] * self.capex_var_dict[c]
                                         + self.capex_fix_dict[c],
                                         name='calculate_investment' + name_adding)
                else:
                    if not self.pm_object.get_component(c).get_uses_ppa():
                        self.model.addConstr(self.investment[c]
                                             == self.nominal_cap[c] * self.capex_var_dict[c] + self.capex_fix_dict[c],
                                             name='calculate_investment' + name_adding)
                    else:
                        self.model.addConstr(self.investment[c] == 0,
                                             name='calculate_investment' + name_adding)
            else:
                self.model.addConstr(self.investment[c]
                                     == sum(self.nominal_cap_pre[c, i] * self.scaling_capex_var_dict[c, i]
                                            + self.scaling_capex_fix_dict[c, i] * self.capacity_binary[c, i]
                                            for i in self.integer_steps),
                                     name='calculate_investment' + name_adding)

        self.model.addConstr(self.objective_economic ==
            sum(self.investment[c] * (self.annuity_factor_dict[c] + self.fixed_om_dict[c]) for c in
                self.all_components)
            + sum(self.generation_profiles_dict[g, cl, t] * self.nominal_cap[g]
                  * pm_object.get_component(g).get_ppa_price() * self.weightings_dict[cl]
                  for g in self.generator_components if pm_object.get_component(g).get_uses_ppa()
                  for cl in self.clusters for t in self.time)
            + sum(self.mass_energy_storage_in_commodities[s, cl, t] * self.variable_om_dict[s]
                  * self.weightings_dict[cl]
                  for t in self.time for cl in self.clusters for s in self.storage_components)
            + sum(self.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), cl, t]
                  * self.variable_om_dict[c] * self.weightings_dict[cl]
                  for t in self.time for cl in self.clusters for c in self.conversion_components)
            + sum(self.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), cl, t]
                  * self.variable_om_dict[g] * self.weightings_dict[cl]
                  for t in self.time for cl in self.clusters
                  for g in self.generator_components if not pm_object.get_component(g).get_uses_ppa())
            + sum(self.mass_energy_purchase_commodity[me, cl, t] * self.purchase_price_dict[me, cl, t]
                  * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                  for me in self.purchasable_commodities if me in self.purchasable_commodities)
            + sum(self.mass_energy_sell_commodity[me, cl, t] * self.sell_price_dict[me, cl, t]
                  * self.weightings_dict[cl]
                  for t in self.time for cl in self.clusters for me in self.saleable_commodities
                  if me in self.saleable_commodities)
            + sum(self.restart_costs[c, cl, t]
                  for t in self.time for cl in self.clusters
                  for c in self.shut_down_components), name='calculate_economic_objective_function')

        self.model.addConstr(self.objective_ecologic ==
            (sum(self.nominal_cap[c]
                 * (self.installation_co2_emissions_dict[c] + self.disposal_co2_emissions_dict[c]) / 20  # m.lifetime[c]
                 for c in self.all_components)
             + sum(self.nominal_cap[c] * self.fixed_yearly_co2_emissions_dict[c] for c in self.all_components)
             + sum(self.mass_energy_storage_in_commodities[s, cl, t] * self.variable_co2_emissions_dict[s]
                   * self.weightings_dict[cl]
                   for t in self.time for cl in self.clusters for s in self.storage_components)
             + sum(self.mass_energy_component_out_commodities[c, self.pm_object.get_component(c).get_main_output(), cl, t]
                   * self.variable_co2_emissions_dict[c] * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                   for c in self.conversion_components)
             + sum(self.mass_energy_generation[g, self.pm_object.get_component(g).get_generated_commodity(), cl, t]
                   * self.variable_co2_emissions_dict[g] * self.weightings_dict[cl]
                   for t in self.time for cl in self.clusters for g in self.generator_components)
             + sum(self.mass_energy_purchase_commodity[me, cl, t] * self.purchase_specific_CO2_emissions_dict[me, cl, t]
                   * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                   for me in self.purchasable_commodities)
             + sum(self.mass_energy_available[me, cl, t] * self.available_specific_CO2_emissions_dict[me, cl, t]
                   * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                   for me in self.available_commodities)
             - sum(self.mass_energy_sell_commodity[me, cl, t] * self.sale_specific_CO2_emissions_dict[me, cl, t]
                   * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                   for me in self.saleable_commodities)
             - sum(self.mass_energy_emitted[me, cl, t] * self.emitted_specific_CO2_emissions_dict[me, cl, t]
                   * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                   for me in self.emittable_commodities)), name='calculate_ecologic_objective_function')

    def attach_economic_objective_function(self):

        # minimize total costs
        self.model.setObjective(self.objective_economic, gp.GRB.MINIMIZE)

    def attach_ecologic_objective_function(self):

        # minimize total emissions
        self.model.setObjective(self.objective_ecologic, gp.GRB.MINIMIZE)

    def attach_multi_objective_economic_objective_adherence_constraint(self, eps_value_economic):

        self.model.addConstr(self.objective_economic + self.slack_economical == eps_value_economic,
                             name='economic_value_adherence')

    def attach_multi_objective_economic_objective_function(self):

        # minimize total costs
        self.model.setObjective(self.objective_economic - self.slack_ecological * 0.0001, gp.GRB.MINIMIZE)

    def attach_multi_objective_ecologic_objective_adherence_constraint(self, eps_value_ecologic):

        # minimize total costs
        self.model.addConstr(self.objective_ecologic + self.slack_ecological == eps_value_ecologic, name='ecologic')

    def attach_multi_objective_ecologic_objective_function(self):

        # minimize total emissions
        self.model.setObjective(self.objective_ecologic - self.slack_economical * 0.0001, gp.GRB.MINIMIZE)

    def prepare(self, optimization_type, eps_value_economic=None, eps_value_ecologic=None):

        self.attach_technical_variables()
        self.attach_economic_variables()

        self.attach_technical_constraints()
        self.attach_economic_constraints()

        if optimization_type == 'economical':

            if eps_value_ecologic is not None:
                self.attach_multi_objective_variables()
                self.attach_multi_objective_ecologic_objective_adherence_constraint(eps_value_ecologic)

            self.attach_economic_objective_function()

        elif optimization_type == 'ecological':

            if eps_value_economic is not None:
                self.attach_multi_objective_variables()
                self.attach_multi_objective_economic_objective_adherence_constraint(eps_value_economic)

            self.attach_ecologic_objective_function()

        else:  # multi objective
            self.attach_multi_objective_variables()

            self.attach_multi_objective_ecologic_objective_adherence_constraint(eps_value_ecologic)
            self.attach_multi_objective_economic_objective_function()

    def optimize(self):

        def save_results():
            self.continuous_variables = [{'nominal_cap': self.nominal_cap},
                                         {'investment': self.investment},
                                         {'nominal_cap_pre': self.nominal_cap_pre},
                                         {'restart_costs': self.restart_costs},
                                         {'mass_energy_component_in_commodities': self.mass_energy_component_in_commodities},
                                         {'mass_energy_component_out_commodities': self.mass_energy_component_out_commodities},
                                         {'mass_energy_available': self.mass_energy_available},
                                         {'mass_energy_emitted': self.mass_energy_emitted},
                                         {'mass_energy_storage_in_commodities': self.mass_energy_storage_in_commodities},
                                         {'mass_energy_storage_out_commodities': self.mass_energy_storage_out_commodities},
                                         {'soc': self.soc},
                                         {'mass_energy_sell_commodity': self.mass_energy_sell_commodity},
                                         {'mass_energy_purchase_commodity': self.mass_energy_purchase_commodity},
                                         {'mass_energy_generation': self.mass_energy_generation},
                                         {'mass_energy_demand': self.mass_energy_demand},
                                         {'mass_energy_hot_standby_demand': self.mass_energy_hot_standby_demand}]

            self.binary_variables = [{'status_on': self.status_on},
                                     {'status_off': self.status_off},
                                     {'status_off_switch_on': self.status_off_switch_on},
                                     {'status_off_switch_off': self.status_off_switch_off},
                                     {'status_standby_switch_on': self.status_standby_switch_on},
                                     {'status_standby_switch_off': self.status_standby_switch_off},
                                     {'status_standby': self.status_standby},
                                     {'storage_charge_binary': self.storage_charge_binary},
                                     {'storage_discharge_binary': self.storage_discharge_binary},
                                     {'capacity_binary': self.capacity_binary}]

        # self.model.Params.LogToConsole = 0
        self.model.optimize()
        self.instance = self

        self.objective_function_value = self.model.objVal

        self.economic_objective_function_value = self.objective_economic.X
        self.ecologic_objective_function_value = self.objective_ecologic.X

        save_results()

    def get_multi_objective_results(self):
        specific_installation_emissions = {}
        installation_emissions = {}
        specific_disposal_emissions = {}
        disposal_emissions = {}
        capacity = {}

        utilization = {}
        sum_input = {}
        sum_output = {}

        specific_fixed_emissions = {}
        fixed_emissions = {}

        specific_variable_emissions = {}
        variable_emissions = {}

        for k in self.all_components:
            k_object = self.pm_object.get_component(k)

            specific_installation_emissions[k] = self.installation_co2_emissions_dict[k]
            specific_disposal_emissions[k] = self.disposal_co2_emissions_dict[k]
            specific_fixed_emissions[k] = self.fixed_yearly_co2_emissions_dict[k]
            specific_variable_emissions[k] = self.variable_co2_emissions_dict[k]

            for c in (self.weightings_dict.keys()):
                for t in self.time:

                    capacity[k] = self.nominal_cap[k].X

                    if k not in list(sum_input.keys()):
                        sum_input[k] = 0

                    if k not in list(sum_output.keys()):
                        sum_output[k] = 0

                    if k in self.conversion_components:
                        main_input = k_object.get_main_input()
                        sum_input[k] \
                            += self.mass_energy_component_in_commodities[(k, main_input, c, t)].X * \
                            self.weightings_dict[c]

                        main_output = k_object.get_main_output()
                        sum_output[k] \
                            += self.mass_energy_component_out_commodities[(k, main_output, c, t)].X \
                            * self.weightings_dict[c]

                    if k in self.generator_components:
                        produced_commodity = k_object.get_generated_commodity()
                        sum_output[k] \
                            += self.mass_energy_generation[(k, produced_commodity, c, t)].X * self.weightings_dict[c]

                    if k in self.storage_components:
                        sum_input[k] \
                            += self.mass_energy_storage_in_commodities[(k, c, t)].X * \
                            self.weightings_dict[c]

                        sum_output[k] \
                            += self.mass_energy_storage_out_commodities[(k, c, t)].X \
                            * self.weightings_dict[c]

            if self.nominal_cap[k].X != 0:
                if k in self.conversion_components:
                    utilization[k] = sum_input[k] / capacity[k]

                elif k in self.generator_components:
                    utilization[k] = sum_output[k] / capacity[k]

                else:
                    utilization[k] = 0
            else:
                utilization[k] = 0

            installation_emissions[k] = capacity[k] * specific_installation_emissions[k]
            disposal_emissions[k] = capacity[k] * specific_disposal_emissions[k]
            fixed_emissions[k] = capacity[k] * specific_fixed_emissions[k]
            variable_emissions[k] = sum_output[k] * specific_variable_emissions[k]

        return capacity, utilization, installation_emissions, disposal_emissions, fixed_emissions, variable_emissions

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
        self.economic_objective_function_value = None
        self.ecologic_objective_function_value = None

        self.model_type = 'gurobi'

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict,\
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
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict\
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

        # Create optimization program
        self.model = gp.Model()
        self.time = range(0, self.pm_object.get_covered_period())  # no -1 because of for
        self.clusters = range(0, self.pm_object.get_number_clusters())  # no -1 because of for
        self.integer_steps = range(0, self.pm_object.integer_steps)
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.bigM = anticipate_bigM(self.pm_object)

        # predefine variables --> todo: there has to be a better way
        self.nominal_cap = self.status_on = self.status_off = self.status_off_switch_on = self.status_off_switch_off = \
            self.status_standby_switch_on = self.status_standby_switch_off = self.status_standby = \
            self.storage_charge_binary = self.storage_discharge_binary = self.nominal_cap_pre = self.capacity_binary = \
            self.mass_energy_component_in_commodities = self.mass_energy_component_out_commodities = \
            self.mass_energy_available = self.mass_energy_emitted = self.mass_energy_storage_in_commodities = \
            self.mass_energy_storage_out_commodities = self.soc = self.mass_energy_sell_commodity = \
            self.mass_energy_purchase_commodity = self.mass_energy_generation = self.mass_energy_demand = \
            self.mass_energy_hot_standby_demand = self.investment = self.restart_costs = self.slack_economical = \
            self.slack_ecological = self.objective_economic = self.objective_ecologic = None

        self.continuous_variables = None
        self.binary_variables = None
