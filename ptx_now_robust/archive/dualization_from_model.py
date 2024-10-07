import pyomo.environ as pyo
from pyomo.core import *
# import pyomo.core.base.initializer
from pyomo.core.base.var import _GeneralVarData
from pyomo.core.expr.numeric_expr import SumExpression
from pyomo.core.expr.numeric_expr import MonomialTermExpression
from pyomo.core.expr.numeric_expr import LinearExpression
import pandas as pd
import numpy as np


def dualize_from_model(model, optimize_dual=False):

    def handel_expression(expression):
        variable_coefficient_local = {}
        if type(expression) == _GeneralVarData:
            variable_coefficient_local[expression.name] = 1
        elif type(expression) == MonomialTermExpression:
            variable_coefficient_local[expression.args[1].name] = expression.args[0]
        elif type(expression) == pyomo.core.base.var.ScalarVar:
            variable_coefficient_local[expression.name] = 1
        else:
            for variable in expression.args:
                if isinstance(variable, MonomialTermExpression):
                    variable_coefficient_local[variable.args[1].name] = variable.args[0]
                else:
                    variable_coefficient_local[variable.name] = 1

        return variable_coefficient_local

    variables = []
    primal_variable_bounds = {}
    for v in model.component_objects(Var):

        # Get bounds
        if not isinstance(v._rule_bounds, pyomo.core.base.initializer.ItemInitializer):
            bound = (v._rule_bounds.val[0], v._rule_bounds.val[1])
        else:
            bound = v._rule_bounds._dict

        if v.is_indexed():
            for i in v.index_set():
                variable_index = '['
                if isinstance(i, tuple):
                    for j in i:
                        if j == i[-1]:
                            variable_index = variable_index + str(j) + ']'
                        else:
                            variable_index = variable_index + str(j) + ','
                else:
                    variable_index = variable_index + str(i) + ']'
                variables.append(str(v) + variable_index)

                if isinstance(bound, list):
                    if (bound[i][0] is None) & (bound[i][1] is None):
                        primal_variable_bounds[str(v) + variable_index] = '=='
                    elif (bound[i][0] is None) & (bound[i][1] is not None):
                        primal_variable_bounds[str(v) + variable_index] = '>='
                    elif (bound[i][0] is not None) & (bound[i][1] is None):
                        primal_variable_bounds[str(v) + variable_index] = '<='
                    else:
                        primal_variable_bounds[str(v) + variable_index] = 'both'
                else:
                    if (bound[0] is None) & (bound[1] is None):
                        primal_variable_bounds[str(v) + variable_index] = '=='
                    elif (bound[0] is None) & (bound[1] is not None):
                        primal_variable_bounds[str(v) + variable_index] = '>='
                    elif (bound[0] is not None) & (bound[1] is None):
                        primal_variable_bounds[str(v) + variable_index] = '<='
                    else:
                        primal_variable_bounds[str(v) + variable_index] = 'both'

        else:
            variables.append(str(v))

            if (bound[0] is None) & (bound[1] is None):
                primal_variable_bounds[str(v)] = '=='
            elif (bound[0] is None) & (bound[1] is not None):
                primal_variable_bounds[str(v)] = '>='
            elif (bound[0] is not None) & (bound[1] is None):
                primal_variable_bounds[str(v)] = '<='
            else:
                primal_variable_bounds[str(v)] = 'both'

    index = []
    for c in model.component_objects(Constraint):
        for i in c.items():
            index.append(i[1].name)

    matrix = np.zeros([len(variables), len(index)])
    constants = []
    bounds = {}

    for c in model.component_objects(Constraint):
        for i in c.items():
            e = i[1].expr
            index_row = index.index(i[1].name)

            if not isinstance(e, pyomo.core.expr.logical_expr.RangedExpression):  # todo: RangedExpression

                if '==' in str(e):
                    bound = (None, None)
                elif '<=' in str(e):
                    bound = (0, None)
                else:
                    bound = (None, 0)
                bounds[i[1].name] = bound

                lhs = i[1].expr.args[0]
                rhs = i[1].expr.args[1]

                lhs_variables_exist = False
                if isinstance(lhs, float) \
                        | isinstance(lhs, int) \
                        | isinstance(lhs, np.float64):
                    constants.append(-float(lhs))
                else:
                    variables_coefficients_lhs = handel_expression(lhs)
                    for k in [*variables_coefficients_lhs.keys()]:
                        variable_col = variables.index(k)
                        matrix[variable_col, index_row] = variables_coefficients_lhs[k]
                    lhs_variables_exist = True

                rhs_variables_exist = False
                if isinstance(rhs, float) \
                        | isinstance(rhs, int) \
                        | isinstance(rhs, np.float64):
                    constants.append(float(rhs))
                else:
                    variables_coefficients_rhs = handel_expression(rhs)
                    for k in [*variables_coefficients_rhs.keys()]:
                        variable_col = variables.index(k)
                        matrix[variable_col, index_row] = - variables_coefficients_rhs[k]
                    rhs_variables_exist = True

                if lhs_variables_exist & rhs_variables_exist:
                    constants.append(float(0))

    obj_func = model.component_objects(Objective)
    obj_func_expression = obj_func.gi_frame.f_locals['self'].obj.expr
    obj_func_vars_coeffs = handel_expression(obj_func_expression)
    obj_func_sense = obj_func.gi_frame.f_locals['self'].obj.sense

    dual_model = ConcreteModel()

    # Sets
    time = 3
    dual_model.T = RangeSet(0, time)
    dual_model.dual_variables = Var(index, bounds=bounds)

    # Create new objective function -> dual variable * constants
    obj_func_lin_expression = LinearExpression(constant=0,
                                               linear_coefs=constants,
                                               linear_vars=[dual_model.dual_variables[i] for i in index])

    def dual_objective_function_rule(m):
        return obj_func_lin_expression

    if obj_func_sense == -1:
        dual_model.dual_objective_function = Objective(rule=dual_objective_function_rule, sense=minimize)
    else:
        dual_model.dual_objective_function = Objective(rule=dual_objective_function_rule, sense=maximize)

    # Create dual constraints
    dual_model.constraints = ConstraintList()
    for col in variables:
        coeffs = []
        dual_variables = []
        for ind in index:
            variable_col = variables.index(col)
            index_col = index.index(ind)
            coeffs.append(matrix[variable_col, index_col])
            dual_variables.append(ind)

        constraint_lin_expression = LinearExpression(constant=0,
                                                     linear_coefs=coeffs,
                                                     linear_vars=[dual_model.dual_variables[i] for i in dual_variables])

        if col in [*obj_func_vars_coeffs.keys()]:
            constant = obj_func_vars_coeffs[col]
        else:
            constant = 0

        if primal_variable_bounds[col] == '==':
            dual_model.constraints.add(constraint_lin_expression == constant)
        elif primal_variable_bounds[col] == '<=':
            dual_model.constraints.add(constraint_lin_expression <= constant)
        elif primal_variable_bounds[col] == '>=':
            dual_model.constraints.add(constraint_lin_expression >= constant)
        else:
            print('')

    # dual_model.pprint()

    if optimize_dual:
        opt = pyo.SolverFactory('gurobi')
        instance = dual_model.create_instance()
        results = opt.solve(instance, tee=True, warmstart=True)