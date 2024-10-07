import itertools
import gurobipy as gp
from _helper_optimization import anticipate_bigM
import math


class OptimizationGurobiModel:

    def attach_technical_variables(self):

        # Component variables
        self.nominal_cap = self.model.addVars(self.all_components, lb=0)

        self.status_on = self.model.addVars(list(itertools.product(self.conversion_components, self.time)),
                                            vtype='B')
        self.status_off = self.model.addVars(list(itertools.product(self.conversion_components, self.time)),
                                             vtype='B')
        self.status_off_switch_on = self.model.addVars(list(itertools.product(self.conversion_components, self.time)),
                                                       vtype='B')
        self.status_off_switch_off = self.model.addVars(list(itertools.product(self.conversion_components, self.time)),
                                                        vtype='B')
        self.status_standby_switch_on = self.model.addVars(list(itertools.product(self.conversion_components, self.time)),
                                                           vtype='B')
        self.status_standby_switch_off = self.model.addVars(list(itertools.product(self.conversion_components, self.time)),
                                                            vtype='B')
        self.status_standby = self.model.addVars(list(itertools.product(self.conversion_components, self.time)),
                                                 vtype='B')

        # STORAGE binaries (charging and discharging)
        self.storage_charge_binary = self.model.addVars(list(itertools.product(self.storage_components, self.time)),
                                                        vtype='B')
        self.storage_discharge_binary = self.model.addVars(list(itertools.product(self.storage_components, self.time)),
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
                                   self.all_inputs, self.time)),
            lb=0)
        self.mass_energy_component_out_commodities \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.all_outputs, self.time)),
                                 lb=0)

        # Freely available commodities
        self.mass_energy_available = self.model.addVars(list(itertools.product(self.available_commodities, self.time)),
                                                        lb=0)
        self.mass_energy_emitted = self.model.addVars(list(itertools.product(self.emittable_commodities, self.time)),
                                                      lb=0)

        # Charged and discharged commodities
        self.mass_energy_storage_in_commodities = self.model.addVars(list(itertools.product(self.storage_components, self.time)),
                                                                     lb=0)
        self.mass_energy_storage_out_commodities = self.model.addVars(list(itertools.product(self.storage_components, self.time)),
                                                                      lb=0)
        self.soc = self.model.addVars(list(itertools.product(self.storage_components, self.time)),
                                      lb=0)

        # sold and purchased commodities
        self.mass_energy_sell_commodity \
            = self.model.addVars(list(itertools.product(self.saleable_commodities, self.time)), lb=0)
        self.mass_energy_purchase_commodity \
            = self.model.addVars(list(itertools.product(self.purchasable_commodities, self.time)), lb=0)

        # generated commodities
        self.mass_energy_generation\
            = self.model.addVars(list(itertools.product(self.generator_components,
                                                        self.generated_commodities, self.time)),
                                 lb=0)

        # Demanded commodities
        self.mass_energy_demand \
            = self.model.addVars(list(itertools.product(self.demanded_commodities, self.time)),
                                 lb=0)

        # Hot standby demand
        self.mass_energy_hot_standby_demand \
            = self.model.addVars(list(itertools.product(self.standby_components, self.final_commodities,
                                                        self.time)), lb=0)

        self.weekly_production = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                           self.demand_periods)), lb=-math.inf, ub=math.inf)

        self.weekly_surplus = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                        self.demand_periods)), lb=0)

        self.weekly_deficit = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                        self.demand_periods)), lb=-math.inf, ub=0)

        self.objective_economic = self.model.addVar(lb=-math.inf, ub=math.inf)

    def attach_economic_variables(self):

        self.investment = self.model.addVars(self.all_components, lb=0)

        self.restart_costs = self.model.addVars(list(itertools.product(self.shut_down_components, self.time)))

    def attach_technical_constraints(self):

        pm_object = self.pm_object

        for t in self.time:

            for com in self.final_commodities:
                commodity_object = pm_object.get_commodity(com)
                equation_lhs = []
                equation_rhs = []

                name_adding = com + '_' + str(t) + '_constraint'

                # mass energy balance constraint
                # Sets mass energy balance for all components
                # produced (out), generated, discharged, available and purchased commodities
                #   = emitted, sold, demanded, charged and used (in) commodities

                if commodity_object.is_available():
                    equation_lhs.append(self.mass_energy_available[com, t])
                if commodity_object.is_emittable():
                    equation_lhs.append(-self.mass_energy_emitted[com, t])
                if commodity_object.is_purchasable():
                    equation_lhs.append(self.mass_energy_purchase_commodity[com, t])
                if commodity_object.is_saleable():
                    equation_lhs.append(-self.mass_energy_sell_commodity[com, t])
                if commodity_object.is_demanded():
                    equation_lhs.append(-self.mass_energy_demand[com, t])
                if com in self.storage_components:
                    equation_lhs.append(
                        self.mass_energy_storage_out_commodities[com, t]
                        - self.mass_energy_storage_in_commodities[com, t])
                if com in self.generated_commodities:
                    equation_lhs.append(sum(self.mass_energy_generation[g, com, t]
                                            for g in self.generator_components
                                            if pm_object.get_component(g).get_generated_commodity() == com))

                for c in self.conversion_components:
                    if (c, com) in self.output_tuples:
                        equation_lhs.append(self.mass_energy_component_out_commodities[c, com, t])

                    if (c, com) in self.input_tuples:
                        equation_rhs.append(self.mass_energy_component_in_commodities[c, com, t])

                self.model.addConstr(sum(equation_lhs) == sum(equation_rhs),
                                     name='balancing_' + name_adding)

                # # Sets commodities, which are demanded
                # if com in self.demanded_commodities:
                #     if com not in self.total_demand_commodities:  # Case where demand needs to be satisfied in every t
                #         self.model.addConstr(self.mass_energy_demand[com, t] >= self.hourly_demand_dict[com, t],
                #                              name='hourly_demand_satisfaction_' + name_adding)

            # output commodities
            for c in self.all_components:

                component_object = pm_object.get_component(c)

                name_adding = c + '_' + str(t) + '_constraint'

                if component_object.get_component_type() == 'conversion':

                    for oc in self.all_outputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        outputs = self.pm_object.get_component(c).get_outputs()

                        if oc in [*outputs.keys()]:
                            self.model.addConstr(self.mass_energy_component_out_commodities[c, oc, t] ==
                                                 self.mass_energy_component_in_commodities[c, main_input, t]
                                                 * self.output_conversion_tuples_dict[c, main_input, oc],
                                                 name='commodity_conversion_output_' + oc + '_' + str(t)
                                                      + '_constraint')
                        else:
                            self.model.addConstr(self.mass_energy_component_out_commodities[c, oc, t] == 0,
                                                 name='commodity_conversion_output_' + oc + '_' + str(t)
                                                      + '_constraint')

                    main_input = pm_object.get_component(c).get_main_input()
                    # Set upper bound conversion
                    self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, t]
                                         <= self.nominal_cap[c] * self.maximal_power_dict[c],
                                         name='set_upper_bound_conversion' + name_adding)

                    # Set lower bound conversion
                    self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, t]
                                         >= self.nominal_cap[c] * self.minimal_power_dict[c],
                                         name='set_lower_bound_conversion' + name_adding)

                    if t > 0:
                        # ramp up limitations
                        self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, t]
                                             - self.mass_energy_component_in_commodities[c, main_input, t - 1]
                                             <= self.nominal_cap[c] * self.ramp_up_dict[c],
                                             name='set_ramp_up_limitations' + name_adding)

                        # ramp down limitations
                        self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, t]
                                             - self.mass_energy_component_in_commodities[c, main_input, t - 1]
                                             >= - self.nominal_cap[c] * self.ramp_down_dict[c],
                                             name='set_ramp_down_limitations' + name_adding)

                    for ic in self.all_inputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        inputs = pm_object.get_component(c).get_inputs()
                        if ic in [*inputs.keys()]:
                            if ic != main_input:
                                self.model.addConstr(self.mass_energy_component_in_commodities[c, ic, t] ==
                                                     self.mass_energy_component_in_commodities[c, main_input, t]
                                                     * self.input_conversion_tuples_dict[c, main_input, ic],
                                                     name='commodity_conversion_input_' + ic + '_' + str(t) + '_constraint')
                        else:
                            self.model.addConstr(self.mass_energy_component_in_commodities[c, ic, t] == 0,
                                                 name='commodity_conversion_input_' + ic + '_' + str(t)
                                                      + '_constraint')

                if component_object.get_component_type() == 'generator':

                    gc = pm_object.get_component(c).get_generated_commodity()

                    if pm_object.get_component(c).get_curtailment_possible():
                        # with curtailment
                        self.model.addConstr(self.mass_energy_generation[c, gc, t]
                                             <= self.generation_profiles_dict[c, 0, t] * self.nominal_cap[c],
                                             name='define_generation' + name_adding)
                    else:
                        # without curtailment
                        self.model.addConstr(self.mass_energy_generation[c, gc, t]
                                             == self.generation_profiles_dict[c, 0, t] * self.nominal_cap[c],
                                             name='define_generation' + name_adding)

                if component_object.get_component_type() == 'storage':

                    # storage balance
                    if t != 0:
                        self.model.addConstr(self.soc[c, t] == self.soc[c, t - 1]
                                             + self.mass_energy_storage_in_commodities[c, t - 1]
                                             * self.charging_efficiency_dict[c]
                                             - self.mass_energy_storage_out_commodities[c, t - 1]
                                             / self.discharging_efficiency_dict[c],
                                             name='storage_balance' + name_adding)

                    # first soc = last soc
                    if True:
                        if t == max(self.time):
                            self.model.addConstr(self.soc[c, 0] == self.soc[c, t]
                                                 + self.mass_energy_storage_in_commodities[c, t]
                                                 * self.charging_efficiency_dict[c]
                                                 - self.mass_energy_storage_out_commodities[c, t]
                                                 / self.discharging_efficiency_dict[c],
                                                 name='last_soc_equals_first_soc' + name_adding)

                    # min max soc
                    self.model.addConstr(self.soc[c, t] <= self.maximal_soc_dict[c] * self.nominal_cap[c],
                                         name='max_soc' + name_adding)

                    self.model.addConstr(self.soc[c, t] >= self.minimal_soc_dict[c] * self.nominal_cap[c],
                                         name='min_soc' + name_adding)

                    # upper and lower bounds charging
                    self.model.addConstr(self.mass_energy_storage_in_commodities[c, t]
                                         <= self.nominal_cap[c] / self.ratio_capacity_power_dict[c],
                                         name='max_soc' + name_adding)

                    self.model.addConstr(self.mass_energy_storage_out_commodities[c, t]
                                         / self.discharging_efficiency_dict[c]
                                         <= self.nominal_cap[c]
                                         / self.ratio_capacity_power_dict[c],
                                         name='min_soc' + name_adding)

                    # storage binary --> don't allow charge and discharge at same time
                    self.model.addConstr(
                        self.storage_charge_binary[c, t] + self.storage_discharge_binary[c, t] <= 1,
                        name='balance_storage_binaries' + name_adding)

                    self.model.addConstr(self.mass_energy_storage_in_commodities[c, t]
                                         - self.storage_charge_binary[c, t] * self.bigM[c] <= 0,
                                         name='activate_charging_binary' + name_adding)

                    self.model.addConstr(self.mass_energy_storage_out_commodities[c, t]
                                         - self.storage_discharge_binary[c, t] * self.bigM[c] <= 0,
                                         name='deactivate_charging_binary' + name_adding)

        # instead of first soc = last soc we can also say total in = total out
        if False:
            for c in self.storage_components:
                self.model.addConstr(sum(self.mass_energy_storage_in_commodities[c, t]
                                         for t in self.time) * self.charging_efficiency_dict[c] ==
                                     sum(self.mass_energy_storage_out_commodities[c, t]
                                         for t in self.time) / self.discharging_efficiency_dict[c],
                                     name='in_storage_equals_out_storage')

        for c in self.all_components:

            component_object = pm_object.get_component(c)

            # Applied if capacity is fixed
            name_adding = '_' + c + '_constraint'

            if component_object.get_has_fixed_capacity():
                self.model.addConstr(self.nominal_cap[c] == self.fixed_capacity_dict[c],
                                     name='fixed_capacity_of' + name_adding)

        if self.demand_type == 'relaxed_weekly':  # case relaxed weekly demand where we have to pay penalty if not satisfied
            for dt in self.demand_periods:
                for com in self.demanded_commodities:
                    self.model.addConstr(self.weekly_production[com, dt]
                                         == sum(self.mass_energy_demand[com, t]
                                                for t in range(dt * self.length_period, (dt + 1) * self.length_period))
                                         - self.total_demand_dict[com] / (8760 / self.length_period),
                                         name='weekly_demand_statisfaction' + com + '_' + str(dt) + '_constraint')

                    self.model.addConstr(self.weekly_production[com, dt]
                                         == self.weekly_surplus[com, dt] + self.weekly_deficit[com, dt],
                                         name='balance_production' + com + '_' + str(dt) + '_constraint')

        elif self.demand_type == 'fixed_weekly':  # case fixed weekly demand
            for dt in self.demand_periods:
                for com in self.demanded_commodities:
                    # the production in each week needs to be equal
                    self.model.addConstr(sum(self.mass_energy_demand[com, t]
                                             for t in range(dt * self.length_period, (dt + 1) * self.length_period))
                                         >= self.total_demand_dict[com] / (8760 / self.length_period),
                                         name='weekly_demand_statisfaction' + com + '_constraint')

    def attach_economic_constraints(self):
        pm_object = self.pm_object

        for c in self.all_components:

            name_adding = '_' + c + '_constraint'

            # calculate investment (used to simplify constraint)
            if c in self.all_components:
                self.model.addConstr(self.investment[c]
                                     == self.nominal_cap[c] * self.capex_var_dict[c] + self.capex_fix_dict[c],
                                     name='calculate_investment' + name_adding)

        self.model.addConstr(self.objective_economic ==
            - sum(self.investment[c] * (self.annuity_factor_dict[c] + self.fixed_om_dict[c]) for c in self.all_components)
            - sum(self.mass_energy_storage_in_commodities[s, t] * self.variable_om_dict[s]
                  for t in self.time for s in self.storage_components)
            - sum(self.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), t]
                  * self.variable_om_dict[c] for t in self.time for c in self.conversion_components)
            - sum(self.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), t]
                  * self.variable_om_dict[g] for t in self.time for g in self.generator_components)
            - sum(self.mass_energy_purchase_commodity[me, t] * self.purchase_price_dict[me, 0, t]
                  for t in self.time for me in self.purchasable_commodities)
            - sum(self.mass_energy_sell_commodity[me, t] * self.sell_price_dict[me, 0, t]
                  for t in self.time for me in self.saleable_commodities)
            + sum(self.mass_energy_demand[me, t] * self.price_selling
                  for me in self.total_demand_commodities for t in self.time)
            + sum(self.weekly_deficit[com, dt] * self.price_missing
                  for com in self.total_demand_commodities for dt in self.demand_periods)
            , name='calculate_economic_objective_function')

        if False:
            self.model.addConstr(self.objective_economic ==
                                 - sum(
                                     self.investment[c] * (self.annuity_factor_dict[c] + self.fixed_om_dict[c]) for c in
                                     self.all_components)
                                 - sum(self.mass_energy_storage_in_commodities[s, t] * self.variable_om_dict[s]
                                       for t in self.time for s in self.storage_components)
                                 - sum(
                self.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), t]
                * self.variable_om_dict[c] for t in self.time for c in self.conversion_components)
                                 - sum(
                self.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), t]
                * self.variable_om_dict[g] for t in self.time for g in self.generator_components)
                                 - sum(self.mass_energy_purchase_commodity[me, t] * self.purchase_price_dict[me, 0, t]
                                       for t in self.time for me in self.purchasable_commodities)
                                 - sum(self.mass_energy_sell_commodity[me, t] * self.sell_price_dict[me, 0, t]
                                       for t in self.time for me in self.saleable_commodities)
                                 + sum(self.mass_energy_demand[me, t] * self.price_selling
                                       for me in self.total_demand_commodities for t in self.time)
                                 , name='calculate_economic_objective_function')

    def attach_economic_objective_function(self):

        # minimize total costs
        self.model.setObjective(self.objective_economic, gp.GRB.MAXIMIZE)

    def prepare(self):

        self.attach_technical_variables()
        self.attach_economic_variables()

        self.attach_technical_constraints()
        self.attach_economic_constraints()

        self.attach_economic_objective_function()

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
                                         {'mass_energy_hot_standby_demand': self.mass_energy_hot_standby_demand},
                                         {'weekly_production': self.weekly_production},
                                         {'weekly_surplus': self.weekly_surplus},
                                         {'weekly_deficit': self.weekly_deficit}]

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

        self.model.Params.LogToConsole = 0
        self.model.Params.Threads = 120
        self.model.optimize()
        self.instance = self

        self.status = self.model.status

        if self.status == 2:

            self.objective_function_value = self.model.objVal

            save_results()

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, length_period, price_selling, price_missing, demand_type):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.status = None
        self.pm_object = pm_object
        self.length_period = length_period
        self.demand_type = demand_type

        self.price_selling = price_selling
        self.price_missing = price_missing

        self.objective_function_value = None

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
        self.integer_steps = range(0, self.pm_object.integer_steps)
        self.demand_periods = range(0, math.floor(self.pm_object.get_covered_period() / length_period))

        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.bigM = anticipate_bigM(self.pm_object)

        # predefine variables --> todo: there has to be a better way
        self.mass_energy_component_in_commodities = self.mass_energy_component_out_commodities = \
            self.mass_energy_available = self.mass_energy_emitted = self.mass_energy_storage_in_commodities = \
            self.mass_energy_storage_out_commodities = self.soc = self.mass_energy_sell_commodity = \
            self.mass_energy_purchase_commodity = self.mass_energy_generation = self.mass_energy_demand = \
            self.mass_energy_hot_standby_demand = self.investment = self.restart_costs = self.slack_economical = \
            self.slack_ecological = self.objective_economic = self.weekly_production = \
            self.weekly_surplus = self.weekly_deficit = None

        self.continuous_variables = None
        self.binary_variables = None
