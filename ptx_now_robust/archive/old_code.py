import pandas as pd


def get_dual_model_data_from_gurobi(A, sense, rhs, cons_name_pyomo, var_ub, var_lb, var_name_pyomo, objective,
                                   optimize_dual=False):
    A_transpose = A.transpose().toarray()
    matrix = pd.DataFrame(A_transpose,
                          index=var_name_pyomo,
                          columns=cons_name_pyomo)

    # From bounds of primal variables to sense of dual constraints --> turn around
    new_sense_constraints = []
    for i, lb in enumerate(var_lb):
        ub = var_ub[i]

        if (lb == float('-inf')) & (ub == float('inf')):
            new_sense_constraints.append('==')
        elif (lb == 0.) & (ub == float('inf')):
            new_sense_constraints.append('<=')
        else:
            new_sense_constraints.append('>=')

    matrix['sense'] = new_sense_constraints
    matrix['rhs'] = objective

    # From sense of primal constraints to bounds of dual variables --> stay same
    bounds = pd.DataFrame(index=cons_name_pyomo, columns=['LB', 'UB'])
    for i, s in enumerate(sense):
        if s == '=':
            bounds.loc[cons_name_pyomo[i], 'LB'] = float('-inf')
            bounds.loc[cons_name_pyomo[i], 'UB'] = float('inf')
        elif s == '<=':
            bounds.loc[cons_name_pyomo[i], 'LB'] = float('-inf')
            bounds.loc[cons_name_pyomo[i], 'UB'] = 0
        else:
            bounds.loc[cons_name_pyomo[i], 'LB'] = 0
            bounds.loc[cons_name_pyomo[i], 'UB'] = float('inf')

    index = [i for i, c in enumerate(rhs) if c != 0]
    short_rhs = [rhs[n] for n in index]
    short_vars = [cons_name_pyomo[n] for n in index]

    objective = pd.DataFrame(index=['Coeffs'], columns=short_vars)
    objective.loc['Coeffs', :] = short_rhs

    path = 'C:/Users/mt5285/Desktop/matrix.xlsx'
    writer = pd.ExcelWriter(path, engine='xlsxwriter')
    matrix.to_excel(writer, sheet_name='matrix')
    bounds.to_excel(writer, sheet_name='bounds')
    objective.to_excel(writer, sheet_name='objective')
    writer.save()
    writer.close()


def build_dual_problem_from_gurobi(self, optimize_dual=False):

    A_transpose = model.A.transpose()
    coefficients = {}
    for i in range(A_transpose.shape[0]):
        coefficients[i] = A_transpose[i, :].toarray().tolist()[0]

    # import pandas as pd
    # pd.DataFrame(A_transpose, index=self.var_name_pyomo, columns=self.cons_name_pyomo).to_excel('C:/Users/mt5285/Desktop/matrix.xlsx')

    # From bounds of primal variables to sense of dual constraints --> turn around
    new_sense_constraints = []
    for i, lb in enumerate(self.var_lb):
        ub = self.var_ub[i]

        if (lb == float('-inf')) & (ub == float('inf')):
            new_sense_constraints.append('==')
        elif (lb == 0.) & (ub == float('inf')):
            new_sense_constraints.append('<=')
        else:
            new_sense_constraints.append('>=')

    # From sense of primal constraints to bounds of dual variables --> stay same
    bounds_vars = {}
    for i, s in enumerate(self.sense):
        if s == '=':
            bounds_vars[self.cons_name_pyomo[i]] = (float('-inf'), float('inf'))
        elif s == '>=':
            bounds_vars[self.cons_name_pyomo[i]] = (float('-inf'), float(0))
        else:
            bounds_vars[self.cons_name_pyomo[i]] = (float(0), float('inf'))

    self.dual_model = ConcreteModel()

    self.dual_model.N = Set(initialize=self.cons_name_pyomo)
    self.dual_model.v = Var(self.dual_model.N, bounds=bounds_vars)

    # Split constraints in 3 types: =, <=, >=
    self.dual_model.constraints = Constraint(pyo.Any)
    for i, s in enumerate(new_sense_constraints):
        coeffs_list = coefficients[i]
        index = [i for i, c in enumerate(coeffs_list) if c != 0]
        vars_list = [self.dual_model.v[n] for n in self.dual_model.N]
        constraint_expression = LinearExpression(constant=0,
                                                 linear_coefs=[coeffs_list[i] for i in index],
                                                 linear_vars=[vars_list[i] for i in index])

        if True:
            if s == '==':
                self.dual_model.constraints[self.var_name_pyomo[i]] = constraint_expression == self.objective[i]
            elif s == '<=':
                self.dual_model.constraints[self.var_name_pyomo[i]] = constraint_expression <= self.objective[i]
            else:
                self.dual_model.constraints[self.var_name_pyomo[i]] = constraint_expression >= self.objective[i]

    index = [i for i, c in enumerate(self.rhs) if c != 0]
    short_rhs = [self.rhs[n] for n in index]
    vars_list = [self.dual_model.v[self.cons_name_pyomo[n]] for n in index]
    objective_expression = LinearExpression(constant=0,
                                            linear_coefs=short_rhs,
                                            linear_vars=vars_list)

    def objective_function(dm):
        return objective_expression
    self.dual_model.obj = Objective(rule=objective_function, sense=maximize)

    if optimize_dual:
        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        opt.options["mipgap"] = 0.01
        instance = self.dual_model.create_instance()
        results = opt.solve(instance, tee=True)
        print(results)
        # print(self.dual_model.pprint())


def attach_commodity_variables_to_optimization_problem(self, dual_model):
    # -------------------------------------
    # Commodity variables
    # Input and output commodity of component
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
                                                       dual_model.TIME, bounds=(None, 0))
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

    dual_model.uncertainty = Var(dual_model.GENERATORS, dual_model.TIME, bounds=(0, 1))

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


def attach_generation_time_series_to_optimization_problem(self, model):
    model.generation_profiles = Param(model.GENERATORS, model.TIME,
                                      initialize=self.generation_profiles_dict)
    return model


def attach_weightings_time_series_to_optimization_problem(self, model):
    model.weightings = Param(model.TIME, initialize=self.weightings_dict)
    return model


def attach_constraints(self, model):
    """ Method attaches all constraints to optimization problem """

    pm_object = self.pm_object

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
                   + dm.y_generation_constraint_variable[g, s, t] <= 0
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
                       - dm.y_conv_cap_lb_constraint_variable[c, t]]

                if t > 0:  # consider ramping
                    lhs.append(+ dm.y_conv_cap_ramp_up_constraint_variable[c, t])
                    lhs.append(- dm.y_conv_cap_ramp_up_constraint_variable[c, t - 1])
                    lhs.append(- dm.y_conv_cap_ramp_down_constraint_variable[c, t])
                    lhs.append(+ dm.y_conv_cap_ramp_down_constraint_variable[c, t - 1])

                for conversion in self.output_conversion_tuples:
                    output_commodity = conversion[2]
                    lhs.append(- dm.y_out_constraint_variable[c, output_commodity, t]
                               * self.output_conversion_tuples_dict[c, main_input, output_commodity])

                for conversion in self.input_conversion_tuples:
                    other_input_commodity = conversion[2]
                    lhs.append(- dm.y_in_constraint_variable[c, other_input_commodity, t]
                               * self.input_conversion_tuples_dict[c, main_input, other_input_commodity])

            else:
                lhs = [- dm.y_balance_constraint_variable[s, t]]

                for conversion in self.input_conversion_tuples:
                    # input to input conversions only possible if s != main input
                    if s == conversion[2]:
                        lhs.append(+ dm.y_in_constraint_variable[c, s, t])

            return sum(lhs) <= 0

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

                return sum(lhs) <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                  rule=x_charge_rule)

        if True:
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

    else:
        def x_charge_rule(dm, s, t):
            if s in self.storage_components:

                period_length = self.pm_object.get_representative_periods_length() - 1
                lhs = [- dm.y_balance_constraint_variable[s, t]
                       + dm.y_soc_charge_limit_constraint_variable[s, t]]

                if (t % (period_length - 1) == 0) & (t > 0):
                    lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s]
                               + dm.y_soc_ub_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])
                elif (t % period_length == 0) & (t > 0):
                    pass
                else:
                    lhs.append(- dm.y_soc_constraint_variable[s, t + 1] * self.charging_efficiency_dict[s])

                return sum(lhs) <= 0
            else:
                return Constraint.Skip

        self.dual_model.x_charge_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                  rule=x_charge_rule)

        if True:
            def x_discharge_variable_rule(dm, s, t):
                if s in self.storage_components:

                    period_length = self.pm_object.get_representative_periods_length() - 1
                    lhs = [+ dm.y_balance_constraint_variable[s, t]
                           + dm.y_soc_charge_limit_constraint_variable[s, t]]

                    if (t % (period_length - 1) == 0) & (t > 0):
                        lhs.append(+ dm.y_soc_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[s]
                                   + dm.y_soc_lb_constraint_variable[s, t + 1] / self.discharging_efficiency_dict[
                                       s])
                    elif (t % period_length == 0) & (t > 0):
                        pass
                    else:
                        lhs.append(+ dm.y_soc_constraint_variable[s, t + 1])

                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.x_discharge_variable_con = Constraint(self.dual_model.ME_COMMODITIES,
                                                                  self.dual_model.TIME,
                                                                  rule=x_discharge_variable_rule)

            def soc_rule(dm, s, t):
                if s in self.storage_components:

                    lhs = []

                    period_length = self.pm_object.get_representative_periods_length() - 1
                    if t == 0:
                        lhs.append(+ dm.y_soc_constraint_variable[s, t + period_length]
                                   - dm.y_soc_constraint_variable[s, t + 1]
                                   + dm.y_soc_ub_constraint_variable[s, t]
                                   - dm.y_soc_lb_constraint_variable[s, t])
                    elif t % period_length != 0:
                        lhs.append(+ dm.y_soc_constraint_variable[s, t]
                                   - dm.y_soc_constraint_variable[s, t + 1]
                                   + dm.y_soc_ub_constraint_variable[s, t]
                                   - dm.y_soc_lb_constraint_variable[s, t])
                    else:
                        lhs.append(+ dm.y_soc_ub_constraint_variable[s, t - 1]
                                   - dm.y_soc_lb_constraint_variable[s, t - 1])
                    return sum(lhs) <= 0
                else:
                    return Constraint.Skip

            self.dual_model.soc_con = Constraint(self.dual_model.ME_COMMODITIES, self.dual_model.TIME,
                                                 rule=soc_rule)

    def cap_conv_rule(dm, c):
        return sum(- dm.y_conv_cap_ub_constraint_variable[c, t] * self.maximal_power_dict[c]
                   + dm.y_conv_cap_lb_constraint_variable[c, t] * self.minimal_power_dict[c]
                   - dm.y_conv_cap_ramp_up_constraint_variable[c, t] * self.ramp_up_dict[c]
                   - dm.y_conv_cap_ramp_down_constraint_variable[c, t] * self.ramp_down_dict[c]
                   for t in dm.TIME) <= (dm.ANF[c] + dm.fixed_om[c]) * dm.capex_var[c]

    self.dual_model.cap_conv_con = Constraint(self.dual_model.CONVERSION_COMPONENTS, rule=cap_conv_rule)

    def cap_gen_rule(dm, g, s):
        generated_commodity = self.pm_object.get_component(g).get_generated_commodity()
        if s == generated_commodity:
            return - sum(dm.y_generation_constraint_variable[g, s, t]
                         * self.generation_profiles_dict[g, t]
                         for t in dm.TIME) <= (dm.ANF[g] + dm.fixed_om[g]) * dm.capex_var[g]
        else:
            return Constraint.Skip

    self.dual_model.cap_gen_con = Constraint(self.dual_model.GENERATORS, self.dual_model.ME_COMMODITIES,
                                             rule=cap_gen_rule)

    def cap_storage_rule(dm, s):
        if s in self.storage_components:
            return sum(- dm.y_soc_ub_constraint_variable[s, t] * self.maximal_soc_dict[s]
                       + dm.y_soc_lb_constraint_variable[s, t] * self.minimal_soc_dict[s]
                       - dm.y_soc_charge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                       - dm.y_soc_discharge_limit_constraint_variable[s, t] * self.ratio_capacity_power_dict[s]
                       for t in dm.TIME) <= (dm.ANF[s] + dm.fixed_om[s]) * dm.capex_var[s]
        else:
            return Constraint.Skip

    self.dual_model.cap_storage_con = Constraint(self.dual_model.ME_COMMODITIES, rule=cap_storage_rule)

    def objective_function(dm):
        return sum(dm.y_demand_constraint_variable[s] * self.demand_dict[s, 0] for s in dm.DEMANDED_COMMODITIES)

    self.dual_model.obj = Objective(rule=objective_function, sense=maximize)

    return model


def optimize(self, instance=None):
    if (self.solver == 'cbc') | (self.solver == 'glpk'):
        opt = pyo.SolverFactory(self.solver)
    else:
        opt = pyo.SolverFactory(self.solver, solver_io="python")

    opt.options["mipgap"] = 0.01
    instance = self.dual_model.create_instance()
    results = opt.solve(instance, tee=True)
    print(results)
    # print(self.dual_model.pprint())

    if False:

        results.write()
        instance.solutions.load_from(results)

        for v in instance.component_objects(Var, active=True):
            print("Variable", v)
            varobject = getattr(instance, str(v))
            for index in varobject:
                print("   ", index, varobject[index].value)

    return instance, results