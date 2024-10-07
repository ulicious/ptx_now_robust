import itertools
import highspy

import gurobipy as gp

from ptx_now._helper_optimization import anticipate_bigM

inf = highspy.kHighsInf
integer_type = highspy.HighsVarType.kInteger


class OptimizationHighsModel:

    def attach_technical_variables(self):

        # Component variables
        self.index_identifier['nominal_cap'] = {}
        for c in self.all_components:
            self.index_identifier['nominal_cap'][c] = self.var_index
            self.model.addVar(0, inf)
            self.var_index += 1

        self.index_identifier['mass_energy_available'] = {}
        self.index_identifier['mass_energy_emitted'] = {}
        self.index_identifier['mass_energy_sell_commodity'] = {}
        self.index_identifier['mass_energy_purchase_commodity'] = {}
        self.index_identifier['mass_energy_demand'] = {}

        self.index_identifier['status_on'] = {}
        self.index_identifier['status_off'] = {}
        self.index_identifier['status_off_switch_on'] = {}
        self.index_identifier['status_off_switch_off'] = {}
        self.index_identifier['status_standby'] = {}
        self.index_identifier['status_standby_switch_on'] = {}
        self.index_identifier['status_standby_switch_off'] = {}

        self.index_identifier['mass_energy_component_in_commodities'] = {}
        self.index_identifier['mass_energy_component_out_commodities'] = {}
        self.index_identifier['mass_energy_hot_standby_demand'] = {}

        self.index_identifier['storage_charge_binary'] = {}
        self.index_identifier['storage_discharge_binary'] = {}

        self.index_identifier['mass_energy_storage_in_commodities'] = {}
        self.index_identifier['mass_energy_storage_out_commodities'] = {}
        self.index_identifier['soc'] = {}

        self.index_identifier['mass_energy_generation'] = {}

        for i in list(itertools.product(self.clusters, self.time)):
            cluster = i[0]
            time = i[1]

            for commodity in self.available_commodities:
                self.index_identifier['mass_energy_available'][(commodity, cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

            for commodity in self.emittable_commodities:
                self.index_identifier['mass_energy_emitted'][(commodity, cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

            for commodity in self.purchasable_commodities:
                self.index_identifier['mass_energy_purchase_commodity'][(commodity, cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

            for commodity in self.saleable_commodities:
                self.index_identifier['mass_energy_sell_commodity'][(commodity, cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

            for commodity in self.demanded_commodities:
                self.index_identifier['mass_energy_demand'][(commodity, cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

            for conversion_component in self.conversion_components:

                self.index_identifier['status_on'][(conversion_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['status_off'][(conversion_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['status_off_switch_on'][(conversion_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['status_off_switch_off'][(conversion_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['status_standby'][(conversion_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['status_standby_switch_on'][(conversion_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['status_standby_switch_off'][(conversion_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                for input_commodity in self.all_inputs:
                    self.index_identifier['mass_energy_component_in_commodities'][(conversion_component,
                                                                                   input_commodity,
                                                                                   cluster, time)] = self.var_index
                    self.model.addVar(0, inf)
                    self.var_index += 1

                for output_commodity in self.all_outputs:

                    self.index_identifier['mass_energy_component_out_commodities'][(conversion_component,
                                                                                    output_commodity,
                                                                                    cluster, time)] = self.var_index
                    self.model.addVar(0, inf)
                    self.var_index += 1

                if conversion_component in self.standby_components:
                    for commodity in self.final_commodities:
                        self.index_identifier['mass_energy_hot_standby_demand'][(conversion_component,
                                                                                        commodity,
                                                                                        cluster, time)] = self.var_index
                        self.model.addVar(0, inf)
                        self.var_index += 1

            for storage_component in self.storage_components:
                self.index_identifier['storage_charge_binary'][(storage_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['storage_discharge_binary'][(storage_component, cluster, time)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

                self.index_identifier['mass_energy_storage_in_commodities'][(storage_component,
                                                                             cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

                self.index_identifier['mass_energy_storage_out_commodities'][(storage_component,
                                                                              cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

                self.index_identifier['soc'][(storage_component, cluster, time)] = self.var_index
                self.model.addVar(0, inf)
                self.var_index += 1

            for generator_component in self.generator_components:
                for generated_commodity in self.generated_commodities:
                    self.index_identifier['mass_energy_generation'][(generator_component, generated_commodity,
                                                                     cluster, time)] = self.var_index
                    self.model.addVar(0, inf)
                    self.var_index += 1

        self.index_identifier['nominal_cap_pre'] = {}
        self.index_identifier['capacity_binary'] = {}
        for conversion_component in self.scalable_components:
            for integer_step in self.integer_steps:
                self.index_identifier['nominal_cap_pre'][(conversion_component, integer_step)] = self.var_index
                self.model.addVar(0, self.scaling_capex_upper_bound_dict[(conversion_component, integer_step)])
                self.var_index += 1

                self.index_identifier['capacity_binary'][(conversion_component, integer_step)] = self.var_index
                self.model.addVar(0, 1)
                self.model.changeColIntegrality(self.var_index, integer_type)
                self.var_index += 1

    def attach_economic_variables(self):
        self.index_identifier['investment'] = {}
        for c in self.all_components:
            self.index_identifier['investment'][c] = self.var_index
            self.model.addVar(0, inf)
            self.var_index += 1

        self.index_identifier['restart_costs'] = {}
        for cluster in self.clusters:
            for time in self.time:
                for conversion_component in self.shut_down_components:
                    self.index_identifier['restart_costs'][(conversion_component, cluster, time)] = self.var_index
                    self.model.addVar(0, inf)
                    self.var_index += 1

    def attach_multi_objective_variables(self):

        self.index_identifier['slack_economical'] = self.var_index
        self.model.addVar(0, inf)
        self.var_index += 1

        self.index_identifier['slack_ecological'] = self.var_index
        self.model.addVar(0, inf)
        self.var_index += 1

    def attach_technical_constraints(self):

        pm_object = self.pm_object

        for combi in itertools.product(self.clusters, self.time):

            cl = combi[0]
            t = combi[1]

            for com in self.final_commodities:
                commodity_object = pm_object.get_commodity(com)
                equation_lhs = []
                values_lhs = []

                # mass energy balance constraint
                # Sets mass energy balance for all components
                # produced (out), generated, discharged, available and purchased commodities
                #   = emitted, sold, demanded, charged and used (in) commodities

                not_zero_values = 0

                if commodity_object.is_available():
                    equation_lhs.append(self.index_identifier['mass_energy_available'][(com, cl, t)])
                    values_lhs.append(1)
                    not_zero_values += 1

                if commodity_object.is_emittable():
                    equation_lhs.append(self.index_identifier['mass_energy_emitted'][(com, cl, t)])
                    values_lhs.append(-1)
                    not_zero_values += 1

                if commodity_object.is_purchasable():
                    equation_lhs.append(self.index_identifier['mass_energy_purchase_commodity'][(com, cl, t)])
                    values_lhs.append(1)
                    not_zero_values += 1

                if commodity_object.is_saleable():
                    equation_lhs.append(self.index_identifier['mass_energy_sell_commodity'][(com, cl, t)])
                    values_lhs.append(-1)
                    not_zero_values += 1

                if commodity_object.is_demanded():
                    equation_lhs.append(self.index_identifier['mass_energy_demand'][(com, cl, t)])
                    values_lhs.append(-1)
                    not_zero_values += 1

                if com in self.storage_components:
                    equation_lhs.append(self.index_identifier['mass_energy_storage_out_commodities'][(com, cl, t)])
                    values_lhs.append(1)
                    not_zero_values += 1

                    equation_lhs.append(self.index_identifier['mass_energy_storage_in_commodities'][(com, cl, t)])
                    values_lhs.append(-1)
                    not_zero_values += 1

                if com in self.generated_commodities:

                    for g in self.generator_components:
                        if pm_object.get_component(g).get_generated_commodity() == com:
                            equation_lhs.append(self.index_identifier['mass_energy_generation'][(g, com, cl, t)])
                            values_lhs.append(1)
                            not_zero_values += 1

                for c in self.conversion_components:
                    if (c, com) in self.output_tuples:
                        equation_lhs.append(self.index_identifier['mass_energy_component_out_commodities'][(c, com, cl, t)])
                        values_lhs.append(1)
                        not_zero_values += 1

                    if (c, com) in self.input_tuples:
                        equation_lhs.append(self.index_identifier['mass_energy_component_in_commodities'][(c, com, cl, t)])
                        values_lhs.append(-1)
                        not_zero_values += 1

                    # hot standby demand
                    if c in self.standby_components:
                        hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                        if com == hot_standby_commodity:
                            equation_lhs.append(self.index_identifier['mass_energy_hot_standby_demand'][(c, com, cl, t)])
                            values_lhs.append(-1)
                            not_zero_values += 1

                self.model.addRow(0, 0, not_zero_values, equation_lhs, values_lhs)

                # Sets commodities, which are demanded
                if com in self.demanded_commodities:
                    if com not in self.total_demand_commodities:  # Case where demand needs to be satisfied in every t

                        self.model.addRow(self.hourly_demand_dict[com, cl, t], inf, 1, self.index_identifier['mass_energy_demand'][(com, cl, t)], 1)

            # output commodities
            for c in self.all_components:

                component_object = pm_object.get_component(c)

                if component_object.get_component_type() == 'conversion':

                    for oc in self.all_outputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        outputs = self.pm_object.get_component(c).get_outputs()

                        if oc in [*outputs.keys()]:
                            not_zero_values = 2
                            variable_index = [self.index_identifier['mass_energy_component_out_commodities'][(c, oc, cl, t)],
                                              self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t)]]
                            values = [-1, self.output_conversion_tuples_dict[c, main_input, oc]]

                            self.model.addRow(0, 0, not_zero_values, variable_index, values)
                        else:
                            not_zero_values = 1
                            variable_index = [self.index_identifier['mass_energy_component_out_commodities'][(c, oc, cl, t)]]
                            values = [1]

                            self.model.addRow(0, 0, not_zero_values, variable_index, values)

                    for ic in self.all_inputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        inputs = pm_object.get_component(c).get_inputs()
                        if ic in [*inputs.keys()]:
                            if ic != main_input:
                                not_zero_values = 2
                                variable_index = [self.index_identifier['mass_energy_component_in_commodities'][(c, ic, cl, t)],
                                                  self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t)]]
                                values = [-1, self.input_conversion_tuples_dict[c, main_input, ic]]

                                self.model.addRow(0, 0, not_zero_values, variable_index, values)
                        else:
                            not_zero_values = 1
                            variable_index = [self.index_identifier['mass_energy_component_in_commodities'][(c, ic, cl, t)]]
                            values = [1]

                            self.model.addRow(0, 0, not_zero_values, variable_index, values)

                    main_input = pm_object.get_component(c).get_main_input()

                    if True:

                        not_zero_values = 3
                        variable_index = [self.index_identifier['status_on'][(c, cl, t)],
                                          self.index_identifier['status_off'][(c, cl, t)],
                                          self.index_identifier['status_standby'][(c, cl, t)]]
                        values = [1, 1, 1]

                        self.model.addRow(1, 1, not_zero_values, variable_index, values)

                        # If component can not be shut off or put in hot standby, the status is always on
                        if (c not in self.shut_down_components) & (c not in self.standby_components):
                            not_zero_values = 1
                            variable_index = [self.index_identifier['status_on'][(c, cl, t)]]
                            values = [1]

                            self.model.addRow(0, 1, not_zero_values, variable_index, values)
                        elif c not in self.shut_down_components:
                            not_zero_values = 1
                            variable_index = [self.index_identifier['status_off'][(c, cl, t)]]
                            values = [1]

                            self.model.addRow(1, 1, not_zero_values, variable_index, values)

                        elif c not in self.standby_components:
                            not_zero_values = 1
                            variable_index = [self.index_identifier['status_standby'][(c, cl, t)]]
                            values = [1]

                            self.model.addRow(1, 1, not_zero_values, variable_index, values)

                        # Set binary to 1 if component is active
                        not_zero_values = 2
                        variable_index = [self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t)],
                                          self.index_identifier['status_on'][(c, cl, t)]]
                        values = [1, -self.bigM[c]]

                        self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                        # Balance switch off
                        not_zero_values = 2
                        variable_index = [self.index_identifier['status_off_switch_on'][(c, cl, t)],
                                          self.index_identifier['status_off_switch_off'][(c, cl, t)]]
                        values = [1, 1]

                        self.model.addRow(0, 1, not_zero_values, variable_index, values)

                        # Define switch on / off constraint
                        if t > 0:
                            not_zero_values = 4
                            variable_index = [self.index_identifier['status_off'][(c, cl, t)],
                                              self.index_identifier['status_off'][(c, cl, t - 1)],
                                              self.index_identifier['status_off_switch_on'][(c, cl, t)],
                                              self.index_identifier['status_off_switch_off'][(c, cl, t)]]
                            values = [-1, 1, 1, -1]

                            self.model.addRow(0, 0, not_zero_values, variable_index, values)

                        # Balance switch standby
                        not_zero_values = 2
                        variable_index = [self.index_identifier['status_standby_switch_on'][(c, cl, t)],
                                          self.index_identifier['status_standby_switch_off'][(c, cl, t)]]
                        values = [1, 1]

                        self.model.addRow(0, 1, not_zero_values, variable_index, values)

                        # Define switch on / standby constraint
                        if t > 0:
                            not_zero_values = 4
                            variable_index = [self.index_identifier['status_standby'][(c, cl, t)],
                                              self.index_identifier['status_standby'][(c, cl, t - 1)],
                                              self.index_identifier['status_standby_switch_on'][(c, cl, t)],
                                              self.index_identifier['status_standby_switch_off'][(c, cl, t)]]
                            values = [-1, 1, 1, -1]

                            self.model.addRow(0, 0, not_zero_values, variable_index, values)

                    # Set upper bound conversion
                    not_zero_values = 2
                    variable_index = [self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t)],
                                      self.index_identifier['nominal_cap'][c]]
                    values = [1, -self.maximal_power_dict[c]]

                    self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                    # Set lower bound conversion
                    not_zero_values = 3
                    variable_index = [self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t)],
                                      self.index_identifier['nominal_cap'][c],
                                      self.index_identifier['status_on'][(c, cl, t)]]
                    values = [1, -self.minimal_power_dict[c], -self.bigM[c]]

                    # todo: hier entsteht Fehlermeldung
                    self.model.addRow(-self.bigM[c], inf, not_zero_values, variable_index, values)

                    if t > 0:

                        # ramp up limitations
                        not_zero_values = 5
                        variable_index = [self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t)],
                                          self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t-1)],
                                          self.index_identifier['nominal_cap'][c],
                                          self.index_identifier['status_off_switch_off'][(c, cl, t)],
                                          self.index_identifier['status_standby_switch_off'][(c, cl, t)]]
                        values = [-1, 1, -self.ramp_up_dict[c], self.bigM[c], self.bigM[c]]

                        self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                        # ramp down limitations
                        not_zero_values = 5
                        variable_index = [
                            self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t)],
                            self.index_identifier['mass_energy_component_in_commodities'][(c, main_input, cl, t - 1)],
                            self.index_identifier['nominal_cap'][c],
                            self.index_identifier['status_off_switch_off'][(c, cl, t)],
                            self.index_identifier['status_standby_switch_off'][(c, cl, t)]]
                        values = [1, -1, self.ramp_down_dict[c], self.bigM[c], self.bigM[c]]

                        self.model.addRow(0, inf, not_zero_values, variable_index, values)

                    if c in self.shut_down_components:

                        # set minimal downtime after shut down
                        if self.shut_down_down_time_dict[c] + t > max(self.time):
                            dt = max(self.time) - t + 1
                        else:
                            dt = self.shut_down_down_time_dict[c]

                        if True:

                            if t > 0:

                                variable_index = [self.index_identifier['status_off'][(c, cl, t)],
                                                  self.index_identifier['status_off'][(c, cl, t - 1)]]
                                not_zero_values = 2
                                values = [1, -1]

                                for i in range(dt):
                                    variable_index.append(self.index_identifier['status_off'][(c, cl, t+i)])
                                    not_zero_values += 1
                                    values.append(-1 / dt)

                                self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                    # lower limit hot standby (don't create energy / commodity
                    if c in self.standby_components:

                        hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                        hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]

                        for com in self.final_commodities:
                            if com == hot_standby_commodity:

                                not_zero_values = 3
                                variable_index = [self.index_identifier['mass_energy_hot_standby_demand'][(c, hot_standby_commodity, cl, t)],
                                                  self.index_identifier['nominal_cap'][c],
                                                  self.index_identifier['status_standby'][(c, cl, t)]]
                                values = [-1, hot_standby_demand, self.bigM[c] * hot_standby_demand]

                                self.model.addRow(-inf, self.bigM[c] * hot_standby_demand, not_zero_values, variable_index, values)
                            else:
                                not_zero_values = 1
                                variable_index = [self.index_identifier['mass_energy_hot_standby_demand'][(c, com, cl, t)]]
                                values = [1]

                                self.model.addRow(0, 0, not_zero_values, variable_index, values)

                        # upper limit got standby (don't destroy energy / commodity)
                        not_zero_values = 2
                        variable_index = [self.index_identifier['mass_energy_hot_standby_demand'][(c, hot_standby_commodity, cl, t)],
                                          self.index_identifier['nominal_cap'][c]]
                        values = [1, -hot_standby_demand]

                        self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                        # activate if in hot standby
                        not_zero_values = 2
                        variable_index = [self.index_identifier['mass_energy_hot_standby_demand'][(c, hot_standby_commodity, cl, t)],
                                          self.index_identifier['status_standby'][(c, cl, t)]]
                        values = [1, -self.bigM[c]]

                        self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                        # set minimal standby time after standby
                        if self.standby_down_time_dict[c] + t > max(self.time):
                            st = max(self.time) - t + 1
                        else:
                            st = self.standby_down_time_dict[c]

                        if t > 0:

                            variable_index = [self.index_identifier['status_standby'][(c, cl, t)],
                                              self.index_identifier['status_standby'][(c, cl, t - 1)]]
                            not_zero_values = 2
                            values = [1, -1]

                            for i in range(st):
                                variable_index.append(self.index_identifier['status_standby'][(c, cl, t + i)])
                                not_zero_values += 1
                                values.append(-1 / st)

                            self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                if component_object.get_component_type() == 'generator':

                    gc = pm_object.get_component(c).get_generated_commodity()

                    if pm_object.get_component(c).get_curtailment_possible():
                        # with curtailment
                        not_zero_values = 2
                        variable_index = [self.index_identifier['mass_energy_generation'][(c, gc, cl, t)],
                                          self.index_identifier['nominal_cap'][c]]
                        values = [1, -self.generation_profiles_dict[c, cl, t]]

                        self.model.addRow(-inf, 0, not_zero_values, variable_index, values)
                    else:
                        # without curtailment
                        not_zero_values = 2
                        variable_index = [self.index_identifier['mass_energy_generation'][(c, gc, cl, t)],
                                          self.index_identifier['nominal_cap'][c]]
                        values = [1, -self.generation_profiles_dict[c, cl, t]]

                        self.model.addRow(0, 0, not_zero_values, variable_index, values)

                if component_object.get_component_type() == 'storage':

                    # storage balance
                    if t != 0:
                        not_zero_values = 4
                        variable_index = [self.index_identifier['soc'][(c, cl, t)],
                                          self.index_identifier['soc'][(c, cl, t-1)],
                                          self.index_identifier['mass_energy_storage_in_commodities'][(c, cl, t-1)],
                                          self.index_identifier['mass_energy_storage_out_commodities'][(c, cl, t-1)]]
                        values = [-1, 1, self.charging_efficiency_dict[c], -1/self.discharging_efficiency_dict[c]]

                        self.model.addRow(0, 0, not_zero_values, variable_index, values)

                    if t == max(self.time):
                        not_zero_values = 4
                        variable_index = [self.index_identifier['soc'][(c, cl, 0)],
                                          self.index_identifier['soc'][(c, cl, t)],
                                          self.index_identifier['mass_energy_storage_in_commodities'][(c, cl, t)],
                                          self.index_identifier['mass_energy_storage_out_commodities'][(c, cl, t)]]
                        values = [-1, 1, self.charging_efficiency_dict[c], -1 / self.discharging_efficiency_dict[c]]

                        self.model.addRow(0, 0, not_zero_values, variable_index, values)

                    # min max soc
                    not_zero_values = 2
                    variable_index = [self.index_identifier['soc'][(c, cl, t)],
                                      self.index_identifier['nominal_cap'][c]]
                    values = [1, -self.minimal_soc_dict[c]]

                    self.model.addRow(0, inf, not_zero_values, variable_index, values)

                    # min max soc
                    not_zero_values = 2
                    variable_index = [self.index_identifier['soc'][(c, cl, t)],
                                      self.index_identifier['nominal_cap'][c]]
                    values = [1, -self.maximal_soc_dict[c]]

                    self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                    # upper and lower bounds charging
                    not_zero_values = 2
                    variable_index = [self.index_identifier['mass_energy_storage_in_commodities'][(c, cl, t)],
                                      self.index_identifier['nominal_cap'][c]]
                    values = [1, -1/self.ratio_capacity_power_dict[c]]

                    self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                    not_zero_values = 2
                    variable_index = [self.index_identifier['mass_energy_storage_out_commodities'][(c, cl, t)],
                                      self.index_identifier['nominal_cap'][c]]
                    values = [1/self.discharging_efficiency_dict[c], -1/self.ratio_capacity_power_dict[c]]

                    self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                    # storage binary --> don't allow charge and discharge at same time
                    if True:
                        not_zero_values = 2
                        variable_index = [self.index_identifier['storage_charge_binary'][(c, cl, t)],
                                          self.index_identifier['storage_discharge_binary'][(c, cl, t)]]
                        values = [1, 1]

                        self.model.addRow(0, 1, not_zero_values, variable_index, values)

                        # activate charging binary
                        not_zero_values = 2
                        variable_index = [self.index_identifier['mass_energy_storage_in_commodities'][(c, cl, t)],
                                          self.index_identifier['storage_charge_binary'][(c, cl, t)]]
                        values = [1, -self.bigM[c]]

                        self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                        # activate discharging binary
                        not_zero_values = 2
                        variable_index = [self.index_identifier['mass_energy_storage_out_commodities'][(c, cl, t)],
                                          self.index_identifier['storage_discharge_binary'][(c, cl, t)]]
                        values = [1, -self.bigM[c]]

                        self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

        # commodities with total demand
        for com in self.demanded_commodities:
            if com in self.total_demand_commodities:

                variable_index = []
                not_zero_values = 0
                values = []
                for cl in self.clusters:
                    for t in self.time:
                        variable_index.append(self.index_identifier['mass_energy_demand'][(com, cl, t)])
                        values.append(self.weightings_dict[cl])
                        not_zero_values += 1

                self.model.addRow(self.total_demand_dict[com], inf, not_zero_values, variable_index, values)

        for sc in self.scalable_components:

            variable_index_binary_balance = []
            not_zero_values_binary_balance = 0
            values_binary_balance = []

            variable_index_final_capacity = []
            not_zero_values_final_capacity = 0
            values_final_capacity = []

            for i in self.integer_steps:
                # activate capacity binary

                not_zero_values = 2
                variable_index = [self.index_identifier['capacity_binary'][(sc, i)],
                                  self.index_identifier['nominal_cap_pre'][(sc, i)]]
                values = [self.bigM[sc], -1]

                self.model.addRow(0, inf, not_zero_values, variable_index, values)

                # Set lower bound of capacity segment
                not_zero_values = 2
                variable_index = [self.index_identifier['capacity_binary'][(sc, i)],
                                  self.index_identifier['nominal_cap_pre'][(sc, i)]]
                values = [self.scaling_capex_lower_bound_dict[sc, i], -1]

                self.model.addRow(-inf, 0, not_zero_values, variable_index, values)

                variable_index_binary_balance.append(self.index_identifier['capacity_binary'][(sc, i)])
                values_binary_balance.append(1)
                not_zero_values_binary_balance += 1

                variable_index_final_capacity.append(self.index_identifier['nominal_cap_pre'][(sc, i)])
                values_final_capacity.append(1)
                not_zero_values_final_capacity += 1

            # capacity binary balance rule
            self.model.addRow(1, 1, not_zero_values_binary_balance, variable_index_binary_balance, values_binary_balance)

            # final capacity rule
            not_zero_values_final_capacity += 1
            variable_index_final_capacity.append(self.index_identifier['nominal_cap'][sc])
            values_final_capacity.append(-1)

            self.model.addRow(0, 0, not_zero_values_final_capacity, variable_index_final_capacity, values_final_capacity)

        for c in self.all_components:

            component_object = pm_object.get_component(c)

            # Applied if capacity is fixed
            if component_object.get_has_fixed_capacity():
                not_zero_values = 1
                variable_index = [self.index_identifier['nominal_cap'][c]]
                values = [1]

                self.model.addRow(self.fixed_capacity_dict[c], self.fixed_capacity_dict[c], not_zero_values, variable_index, values)

    def attach_economic_constraints(self):

        pm_object = self.pm_object

        for combi in itertools.product(self.clusters, self.time):

            cl = combi[0]
            t = combi[1]

            # output commodities
            for c in self.all_components:

                component_object = pm_object.get_component(c)

                if component_object.get_component_type() == 'conversion':

                    if c in self.shut_down_components:

                        if t < max(self.time):

                            not_zero_values = 3
                            variable_index = [self.index_identifier['restart_costs'][(c, cl, t)],
                                              self.index_identifier['nominal_cap'][c],
                                              self.index_identifier['status_off_switch_off'][(c, cl, t)]]
                            values = [1, -self.weightings_dict[cl] * self.shut_down_start_up_costs[c],
                                      -self.bigM[c] * self.weightings_dict[cl] * self.shut_down_start_up_costs[c]]

                            self.model.addRow(
                                -self.bigM[c] * self.weightings_dict[cl] * self.shut_down_start_up_costs[c],
                                inf, not_zero_values, variable_index, values)
                        else:

                            not_zero_values = 4
                            variable_index = [self.index_identifier['restart_costs'][(c, cl, t)],
                                              self.index_identifier['nominal_cap'][c],
                                              self.index_identifier['status_on'][(c, cl, t)],
                                              self.index_identifier['status_off_switch_off'][(c, cl, t)]]
                            values = [1, -self.weightings_dict[cl] * self.shut_down_start_up_costs[c],
                                      self.bigM[c] * self.weightings_dict[cl] * self.shut_down_start_up_costs[c],
                                      -self.bigM[c] * self.weightings_dict[cl] * self.shut_down_start_up_costs[c]]

                            self.model.addRow(0, inf, not_zero_values, variable_index, values)

        for c in self.all_components:

            # calculate investment (used to simplify constraint)
            if c not in self.scalable_components:
                if c not in self.generator_components:
                    not_zero_values = 2
                    variable_index = [self.index_identifier['investment'][c],
                                      self.index_identifier['nominal_cap'][c]]
                    values = [1, -self.capex_var_dict[c]]

                    self.model.addRow(self.capex_fix_dict[c], self.capex_fix_dict[c], not_zero_values, variable_index, values)
                else:
                    if not self.pm_object.get_component(c).get_uses_ppa():
                        not_zero_values = 2
                        variable_index = [self.index_identifier['investment'][c],
                                          self.index_identifier['nominal_cap'][c]]
                        values = [1, -self.capex_var_dict[c]]

                        self.model.addRow(self.capex_fix_dict[c], self.capex_fix_dict[c], not_zero_values,
                                          variable_index, values)
                    else:
                        # if uses ppa then investment is 0
                        not_zero_values = 1
                        variable_index = [self.index_identifier['investment'][c]]
                        values = [1]

                        self.model.addRow(0, 0, not_zero_values, variable_index, values)
            else:

                variable_index = [self.index_identifier['investment'][c]]
                not_zero_values = 1
                values = [1]

                for i in self.integer_steps:
                    variable_index.append(self.index_identifier['nominal_cap_pre'][(c, i)])
                    values.append(-self.scaling_capex_var_dict[c, i])
                    not_zero_values += 1

                    variable_index.append(self.index_identifier['capacity_binary'][(c, i)])
                    values.append(-self.scaling_capex_fix_dict[c, i])
                    not_zero_values += 1

                self.model.addRow(0, 0, not_zero_values, variable_index,
                                  values)

    def attach_economic_objective_function(self):

        pm_object = self.pm_object

        for c in self.all_components:
            self.model.changeColCost(self.index_identifier['investment'][c], self.annuity_factor_dict[c] + self.fixed_om_dict[c])

        for cl in self.clusters:
            for t in self.time:

                for g in self.generator_components:
                    if not pm_object.get_component(g).get_uses_ppa():
                        self.model.changeColCost(
                            self.index_identifier['mass_energy_generation'][(g, pm_object.get_component(g).get_generated_commodity(), cl, t)],
                            self.variable_om_dict[g] * self.weightings_dict[cl])

                for s in self.storage_components:
                    self.model.changeColCost(
                        self.index_identifier['mass_energy_storage_in_commodities'][(s, cl, t)],
                        self.variable_om_dict[s] * self.weightings_dict[cl])

                for c in self.conversion_components:
                    self.model.changeColCost(
                        self.index_identifier['mass_energy_component_out_commodities'][(c, pm_object.get_component(c).get_main_output(), cl, t)],
                        self.variable_om_dict[c] * self.weightings_dict[cl])

                    if c in self.shut_down_components:
                        self.model.changeColCost(
                            self.index_identifier['restart_costs'][(c, cl, t)], 1)

                for me in self.purchasable_commodities:
                    self.model.changeColCost(
                        self.index_identifier['mass_energy_purchase_commodity'][(me, cl, t)],
                        self.purchase_price_dict[me, cl, t] * self.weightings_dict[cl])

                for me in self.saleable_commodities:
                    self.model.changeColCost(
                        self.index_identifier['mass_energy_sell_commodity'][(me, cl, t)],
                        self.sell_price_dict[me, cl, t] * self.weightings_dict[cl])

        for g in self.generator_components:
            if pm_object.get_component(g).get_uses_ppa():
                ppa_price = pm_object.get_component(g).get_ppa_price()
                total_ppa_costs = 0
                for cl in self.clusters:
                    for t in self.time:
                        total_ppa_costs += self.generation_profiles_dict[g, cl, t] * ppa_price * self.weightings_dict[cl]

                self.model.changeColCost(
                    self.index_identifier['nominal_cap'][g], total_ppa_costs)

    def attach_ecologic_objective_function(self):

        # minimize total emissions
        self.model.setObjective(
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
                   for me in self.emittable_commodities)),
            gp.GRB.MINIMIZE)

    def attach_multi_objective_economic_objective_adherence_constraint(self, eps_value_economic):

        pm_object = self.pm_object

        # minimize total costs
        self.model.addConstr(
            sum(self.investment[c] * (self.annuity_factor_dict[c] + self.fixed_om_dict[c]) for c in self.all_components)
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
            - sum(self.mass_energy_sell_commodity[me, cl, t] * self.sell_price_dict[me, cl, t]
                  * self.weightings_dict[cl]
                  for t in self.time for cl in self.clusters for me in self.saleable_commodities
                  if me in self.saleable_commodities)
            + sum(self.restart_costs[c, cl, t]
                  for t in self.time for cl in self.clusters
                  for c in self.shut_down_components) + self.slack_economical == eps_value_economic,
            name='economic_value_adherence')

    def attach_multi_objective_economic_objective_function(self):

        pm_object = self.pm_object

        # minimize total costs
        self.model.setObjective(
            sum(self.investment[c] * (self.annuity_factor_dict[c] + self.fixed_om_dict[c]) for c in self.all_components)
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
            - sum(self.mass_energy_sell_commodity[me, cl, t] * self.sell_price_dict[me, cl, t]
                  * self.weightings_dict[cl]
                  for t in self.time for cl in self.clusters for me in self.saleable_commodities
                  if me in self.saleable_commodities)
            + sum(self.restart_costs[c, cl, t]
                  for t in self.time for cl in self.clusters
                  for c in self.shut_down_components) - self.slack_ecological * 0.0001,
            gp.GRB.MINIMIZE)

    def attach_multi_objective_ecologic_objective_adherence_constraint(self, eps_value_ecologic):

        # minimize total costs
        self.model.addConstr(
            (sum(self.nominal_cap[c]
                 * (self.installation_co2_emissions_dict[c] + self.disposal_co2_emissions_dict[c]) / 20  # m.lifetime[c]
                 for c in self.all_components)
             + sum(self.nominal_cap[c] * self.fixed_yearly_co2_emissions_dict[c] for c in self.all_components)
             + sum(self.mass_energy_storage_in_commodities[s, cl, t] * self.variable_co2_emissions_dict[s]
                   * self.weightings_dict[cl]
                   for t in self.time for cl in self.clusters for s in self.storage_components)
             + sum(self.mass_energy_component_out_commodities[
                       c, self.pm_object.get_component(c).get_main_output(), cl, t]
                   * self.variable_co2_emissions_dict[c] * self.weightings_dict[cl] for t in self.time for cl in
                   self.clusters
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
                   for me in self.emittable_commodities)) + self.slack_ecological == eps_value_ecologic,
            name='ecologic')

    def attach_multi_objective_ecologic_objective_function(self):

        # minimize total emissions
        self.model.setObjective(
            (sum(self.nominal_cap[c]
                 * (self.installation_co2_emissions_dict[c] + self.disposal_co2_emissions_dict[c]) / 20  # m.lifetime[c]
                 for c in self.all_components)
             + sum(self.nominal_cap[c] * self.fixed_yearly_co2_emissions_dict[c] for c in self.all_components)
             + sum(self.mass_energy_storage_in_commodities[s, cl, t] * self.variable_co2_emissions_dict[s]
                   * self.weightings_dict[cl]
                   for t in self.time for cl in self.clusters for s in self.storage_components)
             + sum(self.mass_energy_component_out_commodities[
                       c, self.pm_object.get_component(c).get_main_output(), cl, t]
                   * self.variable_co2_emissions_dict[c] * self.weightings_dict[cl] for t in self.time for cl in
                   self.clusters
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
                   for me in self.emittable_commodities)) - self.slack_economical * 0.0001,
            gp.GRB.MINIMIZE)

    def prepare(self, optimization_type, eps_value_economic=None, eps_value_ecologic=None):
        if optimization_type == 'economical':
            self.attach_technical_variables()
            self.attach_economic_variables()

            self.attach_technical_constraints()
            self.attach_economic_constraints()

            if eps_value_ecologic is not None:
                self.attach_multi_objective_variables()
                self.attach_multi_objective_ecologic_objective_adherence_constraint(eps_value_ecologic)

            self.attach_economic_objective_function()

        elif optimization_type == 'ecological':
            self.attach_technical_variables()
            self.attach_economic_variables()

            self.attach_technical_constraints()
            self.attach_economic_constraints()

            if eps_value_economic is not None:
                self.attach_multi_objective_variables()
                self.attach_multi_objective_economic_objective_adherence_constraint(eps_value_economic)

            self.attach_ecologic_objective_function()

        else:  # multi objective
            self.attach_technical_variables()
            self.attach_economic_variables()

            self.attach_multi_objective_variables()

            self.attach_technical_constraints()
            self.attach_economic_constraints()

            self.attach_multi_objective_ecologic_objective_adherence_constraint(eps_value_ecologic)
            self.attach_multi_objective_economic_objective_function()

    def optimize(self):

        # self.model.Params.LogToConsole = 0
        self.model.run()

        self.objective_function_value = self.model.getInfo().objective_function_value

        self.solution = self.model.getSolution()

        self.instance = self

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.solution = None
        self.pm_object = pm_object
        self.objective_function_value = None

        self.model_type = 'highs'

        self.index_identifier = {}
        self.var_index = 0

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
        self.model = highspy.Highs()
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
            self.slack_ecological = None

        self.continuous_variables = None
        self.binary_variables = None
