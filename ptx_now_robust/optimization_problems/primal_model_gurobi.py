import itertools
import gurobipy as gp
from ptx_now_robust.helpers.helper_optimization import anticipate_bigM


class GurobiPrimalProblem:

    def attach_technical_variables(self):

        # Component variables
        self.nominal_cap = self.model.addVars(self.all_components, lb=0)

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component

        self.mass_energy_component_in_commodities = self.model.addVars(
            list(itertools.product(self.conversion_components,
                                   self.all_inputs,
                                   self.clusters,
                                   self.time,
                                   self.iteration)),
            lb=0)
        self.mass_energy_component_out_commodities \
            = self.model.addVars(list(itertools.product(self.conversion_components, self.all_outputs, self.clusters,
                                                        self.time, self.iteration)),
                                 lb=0)

        # Freely available commodities
        self.mass_energy_available = self.model.addVars(list(itertools.product(self.available_commodities,
                                                                               self.clusters,
                                                                               self.time,
                                                                               self.iteration)),
                                                        lb=0)
        self.mass_energy_emitted = self.model.addVars(list(itertools.product(self.emittable_commodities,
                                                                             self.clusters,
                                                                             self.time,
                                                                             self.iteration)),
                                                      lb=0)

        # Charged and discharged commodities
        self.mass_energy_storage_in_commodities = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                            self.clusters,
                                                                                            self.time,
                                                                                            self.iteration)),
                                                                     lb=0)
        self.mass_energy_storage_out_commodities = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                             self.clusters,
                                                                                             self.time,
                                                                                             self.iteration)),
                                                                      lb=0)
        self.soc = self.model.addVars(list(itertools.product(self.storage_components,
                                                             self.clusters,
                                                             self.time,
                                                             self.iteration)), lb=0)

        # sold and purchased commodities
        self.mass_energy_sell_commodity = self.model.addVars(list(itertools.product(self.saleable_commodities,
                                                                                    self.clusters,
                                                                                    self.time,
                                                                                    self.iteration)),lb=0)
        self.mass_energy_purchase_commodity = self.model.addVars(list(itertools.product(self.purchasable_commodities,
                                                                                        self.clusters,
                                                                                        self.time,
                                                                                        self.iteration)), lb=0)

        # generated commodities
        self.mass_energy_generation = self.model.addVars(list(itertools.product(self.generator_components,
                                                                                self.generated_commodities,
                                                                                self.clusters,
                                                                                self.time,
                                                                                self.iteration)), lb=0)

        # Demanded commodities
        self.mass_energy_demand = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                            self.clusters,
                                                                            self.time,
                                                                            self.iteration)), lb=0)

        self.weekly_production = self.model.addVars(list(itertools.product(self.demanded_commodities, self.clusters, self.iteration)), lb=0)

        self.weekly_surplus = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                        self.clusters,
                                                                        self.iteration)), lb=0)

        self.weekly_deficit = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                        self.clusters,
                                                                        self.iteration)), ub=0)

        self.auxiliary_variable = self.model.addVar()

        self.objective_economic = self.model.addVar()

    def attach_economic_variables(self):

        self.investment = self.model.addVars(self.all_components, lb=0)

    def attach_technical_constraints(self):

        pm_object = self.pm_object

        combinations = list(itertools.product(self.clusters, self.time, self.iteration))

        for combi in combinations:

            cl = combi[0]
            t = combi[1]
            i = combi[2]

            for com in self.final_commodities:
                commodity_object = pm_object.get_commodity(com)
                equation_lhs = []
                equation_rhs = []

                name_adding = com + '_' + str(cl) + '_' + str(t) + '_' + str(i) + '_constraint'

                # mass energy balance constraint
                # Sets mass energy balance for all components
                # produced (out), generated, discharged, available and purchased commodities
                #   = emitted, sold, demanded, charged and used (in) commodities

                if commodity_object.is_available():
                    equation_lhs.append(self.mass_energy_available[com, cl, t, i])
                if commodity_object.is_emittable():
                    equation_lhs.append(-self.mass_energy_emitted[com, cl, t, i])
                if commodity_object.is_purchasable():
                    equation_lhs.append(self.mass_energy_purchase_commodity[com, cl, t, i])
                if commodity_object.is_saleable():
                    equation_lhs.append(-self.mass_energy_sell_commodity[com, cl, t, i])
                if commodity_object.is_demanded():
                    equation_lhs.append(-self.mass_energy_demand[com, cl, t, i])
                if com in self.storage_components:
                    equation_lhs.append(self.mass_energy_storage_out_commodities[com, cl, t, i]
                                        - self.mass_energy_storage_in_commodities[com, cl, t, i])
                if com in self.generated_commodities:
                    equation_lhs.append(sum(self.mass_energy_generation[g, com, cl, t, i]
                                            for g in self.generator_components
                                            if pm_object.get_component(g).get_generated_commodity() == com))

                for c in self.conversion_components:
                    if (c, com) in self.output_tuples:
                        equation_lhs.append(self.mass_energy_component_out_commodities[c, com, cl, t, i])

                    if (c, com) in self.input_tuples:
                        equation_rhs.append(self.mass_energy_component_in_commodities[c, com, cl, t, i])

                self.model.addConstr(sum(equation_lhs) == sum(equation_rhs), name='balancing_' + name_adding)

            # output commodities
            for c in self.all_components:

                component_object = pm_object.get_component(c)

                name_adding = c + '_' + str(cl) + '_' + str(t) + '_' + str(i) + '_constraint'

                if component_object.get_component_type() == 'conversion':

                    for oc in self.all_outputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        outputs = self.pm_object.get_component(c).get_outputs()

                        if oc in [*outputs.keys()]:
                            self.model.addConstr(self.mass_energy_component_out_commodities[c, oc, cl, t, i] ==
                                                 self.mass_energy_component_in_commodities[c, main_input, cl, t, i]
                                                 * self.output_conversion_tuples_dict[c, main_input, oc],
                                                 name='commodity_conversion_output_' + oc + '_' + str(cl) + '_' + str(t) + '_' + str(i)
                                                      + '_constraint')
                        else:
                            self.model.addConstr(self.mass_energy_component_out_commodities[c, oc, cl, t, i] == 0,
                                                 name='commodity_conversion_output_' + oc + '_' + str(cl) + '_' + str(t) + '_' + str(i)
                                                      + '_constraint')

                    for ic in self.all_inputs:
                        main_input = pm_object.get_component(c).get_main_input()
                        inputs = pm_object.get_component(c).get_inputs()
                        if ic in [*inputs.keys()]:
                            if ic != main_input:
                                self.model.addConstr(self.mass_energy_component_in_commodities[c, ic, cl, t, i] ==
                                                     self.mass_energy_component_in_commodities[c, main_input, cl, t, i]
                                                     * self.input_conversion_tuples_dict[c, main_input, ic],
                                                     name='commodity_conversion_input_' + ic + '_' + str(
                                                         cl) + '_' + str(t) + '_' + str(i) + '_constraint')
                        else:
                            self.model.addConstr(self.mass_energy_component_in_commodities[c, ic, cl, t, i] == 0,
                                                 name='commodity_conversion_input_' + ic + '_' + str(cl) + '_' + str(t) + '_' + str(i)
                                                      + '_constraint')

                    main_input = pm_object.get_component(c).get_main_input()

                    # Set upper bound conversion
                    self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t, i]
                                         <= self.nominal_cap[c] * self.maximal_power_dict[c],
                                         name='set_upper_bound_conversion' + name_adding)

                    # Set lower bound conversion
                    self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t, i]
                                         >= self.nominal_cap[c] * self.minimal_power_dict[c],
                                         name='set_lower_bound_conversion' + name_adding)

                    if t > 0:
                        # ramp up limitations
                        self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t, i]
                                             - self.mass_energy_component_in_commodities[c, main_input, cl, t - 1, i]
                                             <= self.nominal_cap[c] * self.ramp_up_dict[c],
                                             name='set_ramp_up_limitations' + name_adding)

                        # ramp down limitations
                        self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t, i]
                                             - self.mass_energy_component_in_commodities[c, main_input, cl, t - 1, i]
                                             >= - self.nominal_cap[c] * self.ramp_down_dict[c],
                                             name='set_ramp_down_limitations' + name_adding)

                if component_object.get_component_type() == 'generator':

                    gc = pm_object.get_component(c).get_generated_commodity()

                    self.model.addConstr(self.mass_energy_generation[c, gc, cl, t, i] <= self.nominal[i][c][cl][t] * self.nominal_cap[c],
                                         name='define_generation' + name_adding)

                if component_object.get_component_type() == 'storage':

                    # storage balance
                    if t != 0:
                        self.model.addConstr(self.soc[c, cl, t, i] == self.soc[c, cl, t - 1, i]
                                             + self.mass_energy_storage_in_commodities[c, cl, t - 1, i]
                                             * self.charging_efficiency_dict[c]
                                             - self.mass_energy_storage_out_commodities[c, cl, t - 1, i]
                                             / self.discharging_efficiency_dict[c],
                                             name='storage_balance' + name_adding)

                    # first soc = last soc
                    if True:
                        if t == max(self.time):
                            self.model.addConstr(self.soc[c, cl, 0, i] == self.soc[c, cl, t, i]
                                                 + self.mass_energy_storage_in_commodities[c, cl, t, i]
                                                 * self.charging_efficiency_dict[c]
                                                 - self.mass_energy_storage_out_commodities[c, cl, t, i]
                                                 / self.discharging_efficiency_dict[c],
                                                 name='last_soc_equals_first_soc' + name_adding)

                    # min max soc
                    self.model.addConstr(self.soc[c, cl, t, i] <= self.maximal_soc_dict[c] * self.nominal_cap[c],
                                         name='max_soc' + name_adding)

                    self.model.addConstr(self.soc[c, cl, t, i] >= self.minimal_soc_dict[c] * self.nominal_cap[c],
                                         name='min_soc' + name_adding)

        # instead of first soc = last soc we can also say total in = total out
        if False:
            for c in self.storage_components:
                self.model.addConstr(sum(self.mass_energy_storage_in_commodities[c, cl, t, i] * self.weightings_dict[cl]
                                         for cl in self.clusters for t in self.time for i in self.iteration) * self.charging_efficiency_dict[c] ==
                                     sum(self.mass_energy_storage_out_commodities[c, cl, t, i] * self.weightings_dict[cl]
                                         for cl in self.clusters for t in self.time for i in self.iteration) / self.discharging_efficiency_dict[c],
                                     name='in_storage_equals_out_storage')

        if self.demand_type == 'relaxed_weekly':  # case relaxed weekly demand where we have to pay penalty if not satisfied
            for cl in self.clusters:
                for i in self.iteration:
                    # the production in each week needs to be equal
                    for com in self.demanded_commodities:
                        self.model.addConstr(self.weekly_production[com, cl, i]
                                             == sum(self.mass_energy_demand[com, cl, t, i] for t in self.time)
                                             - self.total_demand_dict[com] / (8760 / len(self.time)),
                                             name='weekly_demand_statisfaction' + com + str(cl) + str(i) + '_constraint')

                        self.model.addConstr(self.weekly_production[com, cl, i]
                                             == self.weekly_surplus[com, cl, i] + self.weekly_deficit[com, cl, i],
                                             name='balance_production' + com + str(cl) + str(i) + '_constraint')

        elif self.demand_type == 'fixed_weekly':  # case fixed weekly demand
            for cl in self.clusters:
                for i in self.iteration:
                    # the production in each week needs to be equal
                    for com in self.demanded_commodities:
                        self.model.addConstr(sum(self.mass_energy_demand[com, cl, t, i] for t in self.time)
                                             >= self.total_demand_dict[com] / (8760 / len(self.time)),  # todo: do the same in dual
                                             name='weekly_demand_statisfaction' + com + str(cl) + str(
                                                 i) + '_constraint')

        else:
            for i in self.iteration:
                # production over all cluster and time steps needs to be equal to the total demand
                for com in self.demanded_commodities:
                    self.model.addConstr(sum(self.mass_energy_demand[com, cl, t, i] * self.weightings[cl]
                                             for t in self.time for cl in self.clusters) == self.total_demand_dict[com],
                                         name='total_demand_statisfaction_' + com + str(i) + '_constraint')

    def attach_economic_constraints(self):

        pm_object = self.pm_object

        for c in self.all_components:

            name_adding = '_' + c + '_constraint'

            self.model.addConstr(self.investment[c] == self.nominal_cap[c] * self.capex_var_dict[c],
                                 name='calculate_investment' + name_adding)

        for i in self.iteration:
            if self.demand_type == 'relaxed_weekly':
                self.model.addConstr(self.auxiliary_variable >=
                                     sum(self.mass_energy_storage_in_commodities[s, cl, t, i] * self.variable_om_dict[s]
                                         * self.weightings_dict[cl]
                                         for t in self.time for cl in self.clusters for s in self.storage_components)
                                     + sum(self.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), cl, t, i]
                                           * self.variable_om_dict[c] * self.weightings_dict[cl]
                                           for t in self.time for cl in self.clusters for c in self.conversion_components)
                                     + sum(self.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), cl, t, i]
                                           * self.variable_om_dict[g] * self.weightings_dict[cl]
                                           for t in self.time for cl in self.clusters
                                           for g in self.generator_components)
                                     + sum(self.mass_energy_purchase_commodity[me, cl, t, i] * self.purchase_price_dict[me, cl, t]
                                           * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                                           for me in self.purchasable_commodities if me in self.purchasable_commodities)
                                     + sum(self.mass_energy_sell_commodity[me, cl, t, i] * self.sell_price_dict[me, cl, t]
                                           * self.weightings_dict[cl]
                                           for t in self.time for cl in self.clusters for me in self.saleable_commodities)
                                     + sum(self.weekly_deficit[me, cl, i] * self.weightings[cl] * self.costs_missing_product for me in self.total_demand_commodities for cl in self.clusters),
                                     name='auxiliary_variable_constraint')
            elif self.demand_type in ['fixed_weekly', 'total']:
                self.model.addConstr(self.auxiliary_variable >=
                                     sum(self.mass_energy_storage_in_commodities[s, cl, t, i] * self.variable_om_dict[s]
                                         * self.weightings_dict[cl]
                                         for t in self.time for cl in self.clusters for s in self.storage_components)
                                     + sum(self.mass_energy_component_out_commodities[
                                               c, pm_object.get_component(c).get_main_output(), cl, t, i]
                                           * self.variable_om_dict[c] * self.weightings_dict[cl]
                                           for t in self.time for cl in self.clusters for c in self.conversion_components)
                                     + sum(self.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), cl, t, i]
                                           * self.variable_om_dict[g] * self.weightings_dict[cl]
                                           for t in self.time for cl in self.clusters for g in self.generator_components)
                                     + sum(self.mass_energy_purchase_commodity[me, cl, t, i] * self.purchase_price_dict[me, cl, t]
                                           * self.weightings_dict[cl] for t in self.time for cl in self.clusters
                                           for me in self.purchasable_commodities if me in self.purchasable_commodities)
                                     + sum(self.mass_energy_sell_commodity[me, cl, t, i] * self.sell_price_dict[me, cl, t]
                                           * self.weightings_dict[cl] for t in self.time
                                           for cl in self.clusters for me in self.saleable_commodities),
                                     name='auxiliary_variable_constraint')

        self.model.addConstr(self.objective_economic ==
                             sum(self.investment[c] * (self.annuity_factor_dict[c] + self.fixed_om_dict[c])
                                 for c in self.all_components) + self.auxiliary_variable,
                             name='calculate_economic_objective_function')

    def attach_economic_objective_function(self):

        # minimize total costs
        self.model.setObjective(self.objective_economic, gp.GRB.MINIMIZE)

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
                                         {'mass_energy_demand': self.mass_energy_demand}]

            self.num_cont_vars = self.model.NumVars

        self.model.Params.LogToConsole = 0
        self.model.Params.Threads = 120
        self.model.optimize()
        self.instance = self

        self.objective_function_value = self.model.objVal
        self.auxiliary_variable_value = self.auxiliary_variable.X

        save_results()

    def get_results(self):

        capacity = {}

        for k in self.all_components:

            capacity[k] = self.nominal_cap[k].X

        return capacity

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver, nominal, number_clusters, weightings, iteration, costs_missing_product,
                 demand_type):

        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object
        self.nominal = nominal
        self.weightings = weightings
        self.costs_missing_product = costs_missing_product
        self.demand_type = demand_type

        self.objective_function_value = None
        self.auxiliary_variable_value = None

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

        # Adjust purchase & selling price
        if self.pm_object.get_covered_period() != 8760:
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

        if self.pm_object.get_covered_period() != 8760:
            self.clusters = range(0, self.pm_object.get_number_clusters() + 1)
        else:
            self.clusters = [0]

        self.iteration = range(0, iteration+1)
        self.integer_steps = range(0, self.pm_object.integer_steps)
        self.weightings_dict = weightings

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
            self.weekly_production = self.weekly_surplus = self.weekly_deficit = self.auxiliary_variable = \
            self.mass_energy_hot_standby_demand = self.investment = self.objective_economic = None

        self.continuous_variables = None

        self.num_cont_vars = 0
