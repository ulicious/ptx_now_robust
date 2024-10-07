import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd

from itertools import cycle

import webbrowser
from threading import Timer

import os
import numpy as np

import plotly.figure_factory as ff

import yaml


def create_visualization(path):
    def check_visualization_type():

        scenarios = []
        results_per_scenario = {}

        if '0_assumptions.xlsx' in os.listdir(path=path):
            visualization_type_str = 'single_result'

        else:
            # Check structure of folder
            if len([f for f in os.listdir(path=path + '/' + os.listdir(path=path)[0]) if
                    os.path.isdir(path + '/' + os.listdir(path=path)[0] + '/' + f)]) > 0:
                visualization_type_str = 'multiple_results_with_different_scenarios'

                for sc in os.listdir(path=path):
                    if not os.path.isdir(path + '/' + sc):
                        continue

                    scenarios.append(sc)
                    results_per_scenario[sc] = []
                    for res in os.listdir(path=path + '/' + sc):
                        results_per_scenario[sc].append(res)

            else:
                visualization_type_str = 'multiple_results_with_single_scenario'
                sc = path.split('/')[-2]
                results_per_scenario[sc] = []
                scenarios.append(sc)
                for res in os.listdir(path=path):
                    results_per_scenario[sc].append(res)

        return visualization_type_str, scenarios, results_per_scenario

    def extract_data_single_results(p):

        def load_data_single_result():
            assumptions_file = pd.read_excel(p + '0_assumptions.xlsx', index_col=0)
            overview_file = pd.read_excel(p + '1_results_overview.xlsx', index_col=0)
            components_file = pd.read_excel(p + '2_components.xlsx', index_col=0)
            cost_distribution_file = pd.read_excel(p + '3_cost_distribution.xlsx', index_col=0)

            commodities_file = pd.read_excel(p + '5_commodities.xlsx', index_col=0)
            time_series_file = pd.read_excel(p + '4_operations_time_series.xlsx', index_col=(0, 1, 2))

            time_series_file = time_series_file.iloc[1:, :]

            try:
                generation_file = pd.read_excel(p + '6_generation.xlsx', index_col=0)
            except:
                generation_file = None

            yaml_file = open(p + '7_settings.yaml')
            settings_file = yaml.load(yaml_file, Loader=yaml.FullLoader)

            try:
                try:
                    generation_profile = pd.read_excel(p + '8_profile_data.xlsx',
                        index_col=0).fillna('')
                except:
                    generation_profile= pd.read_csv(p + '8_profile_data.csv',
                        index_col=0).fillna('')
            except:
                generation_profile = None

            return assumptions_file, overview_file, components_file, cost_distribution_file, \
                   commodities_file, time_series_file, generation_file, settings_file, generation_profile

        def create_overview_table():

            total_investment = "%.2f" % overview_df.iloc[1].values[0]
            total_fix_costs = "%.2f" % overview_df.iloc[2].values[0]
            total_variable_costs = "%.2f" % overview_df.iloc[3].values[0]
            annual_costs = "%.2f" % overview_df.iloc[4].values[0]
            cost_per_unit = "%.2f" % overview_df.iloc[5].values[0]
            efficiency = "%.2f" % (overview_df.iloc[10].values[0] * 100)

            # Table Overview
            tab_overview = pd.DataFrame({
                '': ('Annual production', 'Total investment', 'Total Fix Costs', 'Total Variable Costs',
                     'Annual costs', 'Production cost per unit', 'Efficiency'),
                'Value':
                    (str(round(annual_production)) + " " + annual_production_unit,
                     str(total_investment) + " " + monetary_unit,
                     str(total_fix_costs) + " " + monetary_unit,
                     str(total_variable_costs) + " " + monetary_unit,
                     str(annual_costs) + " " + monetary_unit,
                     str(cost_per_unit) + " " + monetary_unit + "/" + annual_production_unit,
                     str(efficiency) + ' %')})

            return tab_overview

        def create_conversion_components_table():
            # Create table which contains information on the different components

            component_list = []
            capacity = []
            capacity_unit = []
            CAPEX = []
            total_investment = []
            annuity = []
            fixed_om = []
            variable_om = []
            full_load_hours = []

            for component in components_df.index:

                # only consider conversion components
                if components_df.loc[component, 'Capacity Basis'] == 'input':
                    component_list.append(component)

                    capacity.append("%.3f" % components_df.loc[component, 'Capacity [input]'])
                    capacity_unit.append(components_df.loc[component, 'Capacity Unit [input]'])
                    CAPEX.append("%.2f" % components_df.loc[component, 'Investment [per input]'])
                elif components_df.loc[component, 'Capacity Basis'] == 'output':
                    component_list.append(component)
                    capacity.append("%.3f" % components_df.loc[component, 'Capacity [output]'])
                    capacity_unit.append(components_df.loc[component, 'Capacity Unit [output]'])
                    CAPEX.append("%.2f" % components_df.loc[component, 'Investment [per output]'])
                else:
                    # All non-conversion components have no Capacity Basis
                    continue

                total_investment.append("%.2f" % components_df.loc[component, 'Total Investment'])
                annuity.append("%.2f" % components_df.loc[component, 'Annuity'])
                fixed_om.append("%.2f" % components_df.loc[component, 'Fixed Operation and Maintenance'])
                variable_om.append("%.2f" % components_df.loc[component, 'Variable Operation and Maintenance'])
                full_load_hours.append("%.2f" % components_df.loc[component, 'Capacity Factor'])

            local_conversion_components_tab = pd.DataFrame({'': component_list,
                                                      'Capacity': capacity,
                                                      'Capacity Unit': capacity_unit,
                                                      'Capex': CAPEX,
                                                      'Total Investment': total_investment,
                                                      'Annuity': annuity,
                                                      'Fixed OM': fixed_om,
                                                      'Variable OM': variable_om,
                                                      'Full-load Hours': full_load_hours})

            return local_conversion_components_tab

        def create_cost_structure_graph():
            # Cost structure

            bar_list = []
            bar_share_list = []
            matter_of_expense = []
            value_absolute = []
            value_absolute_unit = []
            value_relative = []
            value_relative_list_unit = []
            for i in cost_distribution_df.index:

                matter_of_expense.append(i)

                value = cost_distribution_df.loc[i, 'Per Output']
                p_dict = {'name': i, 'width': [0.4], 'x': [''], 'y': [value]}
                value_absolute_unit.append("%.2f" % value + ' ' + monetary_unit + ' /' + annual_production_unit)
                value_absolute.append(value)
                if i != 'Total':
                    bar_list.append(go.Bar(p_dict))

                value = cost_distribution_df.loc[i, '%']
                p_share_dict = {'name': i, 'width': [0.4], 'x': [''], 'y': [value * 100]}
                value_relative_list_unit.append("%.2f" % (value * 100) + ' %')
                value_relative.append(value * 100)
                if i != 'Total':
                    bar_share_list.append(go.Bar(p_share_dict))

            cost_structure_df_with_unit = pd.DataFrame()
            cost_structure_df_with_unit[''] = matter_of_expense
            cost_structure_df_with_unit['Absolute'] = value_absolute_unit
            cost_structure_df_with_unit['Relative'] = value_relative_list_unit

            cost_structure_df = pd.DataFrame()
            cost_structure_df[''] = matter_of_expense
            cost_structure_df['Absolute'] = value_absolute
            cost_structure_df['Relative'] = value_relative

            layout = go.Layout(title='Bar Chart', yaxis=dict(ticksuffix=' %'), barmode='stack',
                               colorway=px.colors.qualitative.Pastel)

            cost_fig = go.Figure(data=bar_list, layout=layout)

            cost_share_fig = px.pie(cost_structure_df[cost_structure_df[''] != 'Total'],
                                    values='Relative', names='')

            return cost_fig, cost_share_fig, cost_structure_df_with_unit

        def create_assumptions_table():
            columns = ['Fixed Operation and Maintenance', 'Variable Operation and Maintenance']
            local_assumptions_tab = pd.DataFrame(index=assumptions_df.index)
            local_assumptions_tab[''] = assumptions_df.index
            local_assumptions_tab['Capex Unit'] = assumptions_df['Capex Unit']

            for i in assumptions_df.index:

                local_assumptions_tab.loc[i, 'Capex'] = "%.2f" % assumptions_df.loc[i, 'Capex']

                for col in columns:
                    local_assumptions_tab.loc[i, col] = "%.2f" % (assumptions_df.loc[i, col] * 100) + ' %'

            local_assumptions_tab['Lifetime'] = assumptions_df['Lifetime']

            return local_assumptions_tab

        def create_generation_table():
            local_generation_tab = pd.DataFrame(index=generation_df.index)
            for i in generation_df.index:

                if generation_df.loc[i, 'Capacity'] != 0:
                    local_generation_tab.loc[i, ''] = i
                    local_generation_tab.loc[i, 'Generated Commodity'] = generation_df.loc[i, 'Generated Commodity']
                    local_generation_tab.loc[i, 'Capacity'] = "%.2f" % generation_df.loc[i, 'Capacity']
                    local_generation_tab.loc[i, 'Investment'] = "%.2f" % generation_df.loc[i, 'Investment']
                    local_generation_tab.loc[i, 'Annuity'] = "%.2f" % generation_df.loc[i, 'Annuity']
                    local_generation_tab.loc[i, 'Fixed OM'] = "%.2f" % generation_df.loc[i, 'Fixed Operation and Maintenance']
                    local_generation_tab.loc[i, 'Variable OM'] = "%.2f" % generation_df.loc[i, 'Variable Operation and Maintenance']
                    local_generation_tab.loc[i, 'Potential Generation'] = "%.0f" % generation_df.loc[
                        i, 'Potential Generation']
                    local_generation_tab.loc[i, 'Potential FLH'] = "%.2f" % generation_df.loc[i, 'Potential Full-load Hours']
                    local_generation_tab.loc[i, 'LCOE pre Curtailment'] = "%.4f" % generation_df.loc[
                        i, 'LCOE before Curtailment']
                    local_generation_tab.loc[i, 'Actual Generation'] = "%.0f" % generation_df.loc[i, 'Actual Generation']
                    local_generation_tab.loc[i, 'Actual FLH'] = "%.2f" % generation_df.loc[i, 'Actual Full-load Hours']
                    local_generation_tab.loc[i, 'Curtailment'] = "%.0f" % generation_df.loc[i, 'Curtailment']
                    local_generation_tab.loc[i, 'LCOE post Curtailment'] = "%.4f" % generation_df.loc[
                        i, 'LCOE after Curtailment']

            return local_generation_tab

        def create_storage_table():
            # Create table which contains information on the different components

            component_list = []
            capacity = []
            capacity_unit = []
            CAPEX = []
            total_investment = []
            annuity = []
            fixed_om = []
            variable_om = []
            for component in components_df.index:

                if generation_df is not None:

                    if component in generation_df.index:
                        continue

                # only consider conversion components
                if not (components_df.loc[component, 'Capacity Basis'] == 'input'
                        or components_df.loc[component, 'Capacity Basis'] == 'output'):
                    component_list.append(component)

                    capacity.append("%.3f" % components_df.loc[component, 'Capacity [input]'])
                    capacity_unit.append(components_df.loc[component, 'Capacity Unit [input]'])
                    CAPEX.append("%.2f" % components_df.loc[component, 'Investment [per input]'])

                    total_investment.append("%.2f" % components_df.loc[component, 'Total Investment'])
                    annuity.append("%.2f" % components_df.loc[component, 'Annuity'])
                    fixed_om.append("%.2f" % components_df.loc[component, 'Fixed Operation and Maintenance'])
                    variable_om.append("%.2f" % components_df.loc[component, 'Variable Operation and Maintenance'])

            local_storage_components_tab = pd.DataFrame({'': component_list,
                                                   'Capacity': capacity,
                                                   'Capacity Unit': capacity_unit,
                                                   'Capex': CAPEX,
                                                   'Total Investment': total_investment,
                                                   'Annuity': annuity,
                                                   'Fixed Operation and Maintenance': fixed_om,
                                                   'Variable Operation and Maintenance': variable_om})

            return local_storage_components_tab

        def create_commodity_table():
            local_commodity_tab = pd.DataFrame(index=commodities_df.index)

            for i in local_commodity_tab.index:
                local_commodity_tab.loc[i, ''] = i
                local_commodity_tab.loc[i, 'Unit'] = commodities_df.loc[i, 'unit']
                local_commodity_tab.loc[i, 'Freely Available'] = "%.0f" % commodities_df.loc[i, 'Available Commodity']
                local_commodity_tab.loc[i, 'Purchased'] = "%.0f" % commodities_df.loc[i, 'Purchased Commodity']
                local_commodity_tab.loc[i, 'Sold'] = "%.0f" % commodities_df.loc[i, 'Sold Commodity']
                local_commodity_tab.loc[i, 'Generated'] = "%.0f" % commodities_df.loc[i, 'Generated Commodity']
                local_commodity_tab.loc[i, 'Stored'] = "%.0f" % commodities_df.loc[i, 'Stored Commodity']
                local_commodity_tab.loc[i, 'From Conversion'] = "%.0f" % commodities_df.loc[i, 'Produced Commodity']
                local_commodity_tab.loc[i, 'Total Fixed Costs'] = "%.2f" % commodities_df.loc[i, 'Total Fix Costs'] \
                                                            + monetary_unit
                local_commodity_tab.loc[i, 'Total Variable Costs'] = "%.2f" % commodities_df.loc[i, 'Total Variable Costs'] \
                                                               + monetary_unit
                local_commodity_tab.loc[i, 'Intrinsic Costs per Unit'] = "%.2f" % commodities_df.loc[
                    i, 'Total Costs per Unit'] + monetary_unit + '/' + commodities_df.loc[i, 'unit']
                local_commodity_tab.loc[i, 'Costs from other Commodities per Unit'] = \
                    "%.2f" % (commodities_df.loc[i, 'Production Costs per Unit']
                              - commodities_df.loc[i, 'Total Costs per Unit']) + ' ' + monetary_unit + '/' + \
                    commodities_df.loc[i, 'unit']
                local_commodity_tab.loc[i, 'Total Costs per Unit'] = "%.2f" % commodities_df.loc[
                    i, 'Production Costs per Unit'] + ' ' \
                                                               + monetary_unit + '/' + commodities_df.loc[i, 'unit']

            return local_commodity_tab

        assumptions_df, overview_df, components_df, cost_distribution_df, commodities_df, time_series_df, generation_df, \
        settings_df, generation_prof = load_data_single_result()

        assumptions_tab = create_assumptions_table()
        assumptions_tab_columns = assumptions_tab.columns[1:]

        monetary_unit = settings_df['monetary_unit']

        create_assumptions_table()

        annual_production = overview_df.iloc[0].values[0]
        annual_production_unit = time_series_df.loc[['Demand']].loc[:, 'unit'].values[0].split(' / ')[0]

        if annual_production_unit in ['kW', 'MW', 'GW', 'TW']:
            annual_production_unit = annual_production_unit + 'h'

        overview_tab = create_overview_table()

        conversion_components_tab = create_conversion_components_table()
        conversion_components_tab_columns = conversion_components_tab.columns[1:]

        storage_components_tab = create_storage_table()
        storage_components_tab_columns = storage_components_tab.columns[1:]

        cost_fig, cost_share_fig, cost_structure_df = create_cost_structure_graph()

        if generation_df is not None:
            generation_tab = create_generation_table()
            generation_tab = generation_tab.astype(float, errors='ignore')
        else:
            generation_tab = pd.DataFrame()

        commodity_tab = create_commodity_table()

        return monetary_unit, assumptions_tab, assumptions_tab_columns, annual_production, annual_production_unit, \
               overview_df, overview_tab, components_df, conversion_components_tab, conversion_components_tab_columns, \
               storage_components_tab, storage_components_tab_columns, \
               cost_fig, cost_share_fig, cost_structure_df, generation_df, generation_tab,\
               commodities_df, commodity_tab, time_series_df, generation_prof

    def create_browser_visualization_single_result():

        # prepare time series for graph plot
        time_series_unit = time_series_dataframe.iloc[:, 0]
        time_series_data = time_series_dataframe.iloc[:, 1:]

        # Dictionary to get index-triple from str(i)
        index_dictionary = dict([(str(i), i) for i in time_series_dataframe.index])

        # Readable names for checklist
        def merge_tuples(*t):
            return tuple(j for i in t for j in (i if isinstance(i, tuple) else (i,)))

        first_column_index = ['Charging', 'Discharging', 'Demand', 'Emitting', 'Freely Available', 'Generation', 'Potential Generation',
                              'Purchase', 'Selling', 'Input', 'Output', 'State of Charge', 'Total Potential Generation',
                              'Total Generation', 'Hot Standby Demand']

        time_series_dataframe['Name'] = time_series_dataframe.index.tolist()
        for c in first_column_index:
            if c in time_series_dataframe.index.get_level_values(0):
                for i in time_series_dataframe.loc[c].index:
                    if str(i[0]) == 'nan':
                        name = str(i[1]) + ' ' + c
                    else:
                        name = str(i[1]) + ' ' + c + ' ' + str(i[0])

                    time_series_dataframe.at[merge_tuples(c, i), 'Name'] = name

        # Implement web application
        app = dash.Dash(__name__)

        app.title = name_scenario
        app.layout = html.Div([
            html.Div(
                [
                    html.H2(
                        ["PtX-Results"], className="subtitle padded", style={'font-family': 'Arial'}
                    ),
                    html.Div(children='This website is a tool to visualize and display model results.',
                             style={'margin-bottom': '20px'}),
                ]
            ),
            dcc.Tabs([
                dcc.Tab(label='Assumptions',
                        children=[
                            html.Div([
                                html.H2(
                                    ["Assumptions"],
                                    className="subtitle padded",
                                    style={'font-family': 'Calibri'}),
                                dash_table.DataTable(
                                    id='assumptions',
                                    columns=[{"name": i, "id": i} for i in assumptions_table.columns],
                                    data=assumptions_table.to_dict('records'),
                                    style_as_list_view=True,
                                    style_cell_conditional=[
                                        {'if': {'column_id': assumptions_table_columns},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%'},
                                        {'if': {'column_id': ''},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%',
                                         'background-color': '#f5f2f2'}],
                                    style_data_conditional=[
                                        {'if': {'column_id': ''},
                                         'fontWeight': 'bold'}],
                                    style_header={
                                        'fontWeight': 'bold',
                                        'background-color': '#edebeb'})],
                                style={'width': '50%'}
                            )
                        ]
                        ),
                dcc.Tab(label='Overview Results',
                        children=[
                            html.Div([
                                html.H2(
                                    ["Results"],
                                    className="subtitle padded",
                                    style={'font-family': 'Calibri'}),
                                dash_table.DataTable(
                                    id='overview_table',
                                    columns=[{"name": i, "id": i} for i in overview_table.columns],
                                    data=overview_table.to_dict('records'),
                                    style_as_list_view=True,
                                    style_cell_conditional=[
                                        {'if': {'column_id': 'Value'},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%'},
                                        {'if': {'column_id': ''},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%',
                                         'background-color': '#f5f2f2'}],
                                    style_data_conditional=[
                                        {'if': {'column_id': ''},
                                         'fontWeight': 'bold', }],
                                    style_header={
                                        'fontWeight': 'bold',
                                        'background-color': '#edebeb'}
                                )
                            ],
                                style={'width': '50%'}
                            )
                        ]
                        ),
                dcc.Tab(label='Conversion Components',
                        children=[
                            html.Div([
                                html.H2(
                                    ["Conversion Components"],
                                    className="subtitle padded",
                                    style={'font-family': 'Calibri'}),
                                dash_table.DataTable(
                                    id='conversion_components_table',
                                    columns=[{"name": i, "id": i} for i in conversion_components_table.columns],
                                    data=conversion_components_table.to_dict('records'),
                                    style_as_list_view=True,
                                    style_cell_conditional=[
                                        {'if': {'column_id': conversion_components_table_columns},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%'},
                                        {'if': {'column_id': ''},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%',
                                         'background-color': '#f5f2f2'}],
                                    style_data_conditional=[
                                        {'if': {'column_id': ''},
                                         'fontWeight': 'bold'}],
                                    style_header={
                                        'fontWeight': 'bold',
                                        'background-color': '#edebeb'}
                                )
                            ])
                        ]
                        ),
                dcc.Tab(label='Storage Components',
                        children=[
                            html.Div([
                                html.H2(
                                    ["Storage Components"],
                                    className="subtitle padded",
                                    style={'font-family': 'Calibri'}),
                                dash_table.DataTable(
                                    id='storage_components_table',
                                    columns=[{"name": i, "id": i} for i in storage_components_table.columns],
                                    data=storage_components_table.to_dict('records'),
                                    style_as_list_view=True,
                                    style_cell_conditional=[
                                        {'if': {'column_id': storage_components_table_columns},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%'},
                                        {'if': {'column_id': ''},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%',
                                         'background-color': '#f5f2f2'}],
                                    style_data_conditional=[
                                        {'if': {'column_id': ''},
                                         'fontWeight': 'bold'}],
                                    style_header={
                                        'fontWeight': 'bold',
                                        'background-color': '#edebeb'},
                                )
                            ])
                        ]
                        ),
                dcc.Tab(
                    label='Generation Components',
                    children=[
                        html.Div([
                            html.H2(
                                ["Generation Components"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='generation_table',
                                columns=[{"name": i, "id": i} for i in generation_table.columns],
                                data=generation_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'})
                        ],
                            style={'width': '100%'}
                        )
                    ]
                ),
                dcc.Tab(
                    label='Commodities',
                    children=[
                        html.Div([
                            html.H2(
                                ["Commodities"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='commodity_table',
                                columns=[{"name": i, "id": i} for i in commodity_table.columns],
                                data=commodity_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'})
                        ],
                            style={'width': '100%'}
                        )
                    ]
                ),
                dcc.Tab(
                    label='Cost Distribution',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div(
                                    children=dcc.Graph(figure=cost_share_figure),
                                    style={
                                        'height': '100px',
                                        'margin-left': '10px',
                                        'width': '45%',
                                        'text-align': 'center',
                                        'display': 'inline-block'}),
                                html.Div(
                                    children=[
                                        dash_table.DataTable(
                                            id='cost_structure_table',
                                            columns=[{"name": i, "id": i} for i in cost_structure_dataframe.columns],
                                            data=cost_structure_dataframe.to_dict('records'),
                                            style_as_list_view=True,
                                            style_cell_conditional=[
                                                {'if': {'column_id': ''},
                                                 'textAlign': 'left',
                                                 'font-family': 'Calibri',
                                                 'width': '10%'},
                                                {'if': {'column_id': ''},
                                                 'textAlign': 'left',
                                                 'font-family': 'Calibri',
                                                 'width': '10%',
                                                 'background-color': '#f5f2f2'}],
                                            style_data_conditional=[
                                                {'if': {'column_id': ''},
                                                 'fontWeight': 'bold'}],
                                            style_header={
                                                'fontWeight': 'bold',
                                                'background-color': '#edebeb'})
                                    ],
                                    style={'width': '50%', 'float': 'right'}
                                )
                            ])
                        ])
                    ]
                ),
                dcc.Tab(label='Graph',
                        children=[
                            html.Div([
                                html.Div(dcc.Graph(id='indicator_graphic')),
                                html.Div([
                                    html.Div([
                                        "left Y-axis",
                                        dcc.Dropdown(
                                            className='Y-axis left',
                                            id='yaxis_main',
                                            options=[{'label': str(i), 'value': str(i)} for i in
                                                     time_series_unit.unique()]),
                                        dcc.Checklist(
                                            id='checklist_left',
                                            labelStyle={'display': 'block'})],
                                        style={'width': '48%', 'display': 'inline-block'}),
                                    html.Div([
                                        "right Y-axis",
                                        dcc.Dropdown(
                                            className='Y-axis right',
                                            id='yaxis_right',
                                            options=[{'label': str(i), 'value': str(i)} for i in
                                                     time_series_unit.unique()]),
                                        dcc.Checklist(
                                            id='checklist_right',
                                            labelStyle={'display': 'block'})],
                                        style={'width': '48%', 'float': 'right', 'display': 'inline-block'}
                                    )
                                ])
                            ])
                        ]
                        )
            ])
        ])

        @app.callback(
            Output('checklist_left', 'options'),
            Input('yaxis_main', 'value'),
        )
        def update_dropdown_left(selection):
            t = time_series_unit == str(selection)
            return [{'label': str(time_series_dataframe.at[i, 'Name']), 'value': str(i)} for i in t.index[t.tolist()]]

        @app.callback(
            Output('checklist_right', 'options'),
            Input('yaxis_right', 'value'),
        )
        def update_dropdown_right(selection):
            t = time_series_unit == str(selection)
            return [{'label': str(time_series_dataframe.at[i, 'Name']), 'value': str(i)} for i in t.index[t.tolist()]]

        @app.callback(
            Output('indicator_graphic', 'figure'),
            Input('checklist_left', 'value'),
            Input('checklist_right', 'value'),
            Input('yaxis_main', 'value'),
            Input('yaxis_right', 'value')
        )
        def update_graph(left_checklist, right_checklist, unit_left, unit_right):
            color_left = cycle(px.colors.qualitative.Plotly)
            color_right = cycle(px.colors.qualitative.Plotly[::-1])
            if unit_right is None:
                data_graph = []
                if left_checklist is not None:
                    for i in range(0, len(left_checklist)):
                        globals()['right_trace%s' % i] = \
                            go.Scatter(
                                x=time_series_data.columns,
                                y=time_series_data.loc[index_dictionary[left_checklist[i]]],
                                name=time_series_dataframe.at[index_dictionary[left_checklist[i]], 'Name'] + ', '
                                     + time_series_unit.loc[index_dictionary[left_checklist[i]]],
                                line=dict(color=next(color_left))
                            )
                        data_graph.append(globals()['right_trace%s' % i])
                layout = go.Layout(
                    title="PtX-Model: Commodity Visualization",
                    xaxis=dict(
                        title='h',
                        range=[0, time_series_data.shape[1] + 10]
                    ),
                    yaxis=dict(
                        title=unit_left,
                        rangemode="tozero",
                        showgrid=True
                    ),
                    legend=dict(
                        # orientation='h',
                        # x=0,
                        # y=-1,
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    ),
                    showlegend=True,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='#f7f7f7'
                )
                fig = go.Figure(data=data_graph, layout=layout)
                return fig
            elif unit_right is not None:
                data_graph = []
                for i in range(0, len(left_checklist)):
                    globals()['left_trace%s' % i] = go.Scatter(
                        x=time_series_data.columns,
                        y=time_series_data.loc[index_dictionary[left_checklist[i]]],
                        name=time_series_dataframe.at[index_dictionary[left_checklist[i]], 'Name'],
                        legendgroup='left',
                        legendgrouptitle=dict(
                            text=str(time_series_unit.loc[index_dictionary[left_checklist[i]]]) + ':'
                        ),
                        line=dict(color=next(color_left)),
                    )
                    data_graph.append(globals()['left_trace%s' % i])
                if right_checklist is not None:
                    for i in range(0, len(right_checklist)):
                        globals()['right_trace%s' % i] = go.Scatter(
                            x=time_series_data.columns,
                            y=time_series_data.loc[index_dictionary[right_checklist[i]]],
                            name=time_series_dataframe.at[index_dictionary[right_checklist[i]], 'Name'],
                            yaxis='y2',
                            legendgroup='right',
                            legendgrouptitle=dict(
                                text=str(time_series_unit.loc[index_dictionary[right_checklist[i]]]) + ':'
                            ),
                            line=dict(color=next(color_right)))
                        data_graph.append(globals()['right_trace%s' % i])
                layout = go.Layout(
                    title="PtX-Model: Commodity Visualization",
                    xaxis=dict(
                        title='h',
                        domain=[0, 0.95]
                    ),
                    yaxis=dict(
                        title=unit_left,
                        rangemode='tozero'
                    ),
                    yaxis2=dict(
                        title=unit_right,
                        rangemode='tozero',
                        overlaying='y',
                        side='right',
                    ),
                    legend=dict(
                        # orientation='h',
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    ),
                    legend_tracegroupgap=25,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='#f7f7f7'
                )
                fig = go.Figure(data=data_graph, layout=layout)
                return fig

        @app.callback(
            Output('load_profile', 'figure'),
            Output('load_profile', 'style'),
            Input('load_profile_checklist', 'value'))
        def update_load_profile(check):
            load_profile_data = []
            if check is not None:
                for i in range(0, len(check)):
                    cache = time_series_data.sort_values(axis=1, by=index_dictionary[check[i]],
                                                         ignore_index=True, ascending=False).loc[
                        index_dictionary[check[i]]]
                    load_profile_data.append(
                        go.Bar(
                            x=cache.index,
                            y=cache,
                            name=time_series_dataframe.at[index_dictionary[check[i]], 'Name'],
                            width=1,
                            marker=dict(line=dict(width=0))
                        )
                    )
                layout = go.Layout(
                    title="Load profile",
                    xaxis=dict(
                        title='h',
                        categoryorder='category descending'
                    ),
                    yaxis=dict(
                        title='kW',
                        rangemode='tozero'
                    ),
                    barmode='stack',
                    legend=dict(
                        orientation='h',
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    ),
                    paper_bgcolor='rgba(255, 255, 255, 255)',
                    plot_bgcolor='#f7f7f7',
                )
                fig = go.Figure(data=load_profile_data, layout=layout)
                style = {'width': '80%', 'display': 'inline-block'}
                return fig, style

        def open_page():
            return webbrowser.open('http://127.0.0.1:8050/')

        Timer(1.0, open_page()).start(),
        app.run_server(debug=False, use_reloader=False)

    def calculate_maximal_full_load_hours(generator_profiles):

        def create_combinations(initial_values=None, scale=10, direction_up=True):

            capacities = {}
            if initial_values is None:
                for g in generators:
                    capacities[g] = np.array([round(i / scale, 3) for i in range(11)])
            else:
                if direction_up:
                    for ind, g in enumerate(generators):
                        if initial_values[ind] == 1:
                            capacities[g] = np.array([initial_values[ind]])
                        else:
                            capacities[g] = np.array([round(initial_values[ind] + (i / scale), 3) for i in range(11)])
                else:
                    for ind, g in enumerate(generators):
                        if initial_values[ind] == 0:
                            capacities[g] = np.array([initial_values[ind]])
                        else:
                            capacities[g] = np.array(
                                [round(initial_values[ind] - (1 / scale * 10) + (i / scale), 3) for i in range(11)])

            import itertools

            capacities_combinations = itertools.product(capacities[[*capacities.keys()][0]],
                                                        capacities[[*capacities.keys()][1]])

            if len(generators) > 2:
                combinations = []
                for i in range(2, len([*capacities.keys()])):
                    sub_list = []
                    for c in capacities_combinations:
                        sub_list.append(list(c))

                    b = itertools.product(sub_list, capacities[[*capacities.keys()][i]])

                    for c in b:
                        sub_sub_list = c[0].copy()
                        sub_sub_list.append(c[1])
                        combinations.append(sub_sub_list)
            else:
                combinations = []
                for c in capacities_combinations:
                    combinations.append(list(c))

            return combinations

        def calculate_flh(flh=0):

            max_value = None
            for c in all_combinations:
                all_zeros = True
                for c_value in c:
                    if c_value != float(0):
                        all_zeros = False
                        break

                if not all_zeros:

                    length_array = len(generators_with_s_profiles[[*generators_with_s_profiles.keys()][0]])

                    flh_array = np.zeros(length_array)
                    capacity = 0
                    for i, key in enumerate(generators_with_s_profiles):
                        flh_array = np.add(flh_array, generators_with_s_profiles[key] * c[i])
                        capacity += c[i]

                    if round(flh_array.sum() / capacity, 3) >= flh:
                        flh = round(flh_array.sum() / capacity, 3)
                        max_value = c

            return flh, max_value

        generators_with_s_profiles = {}
        generators = []
        for g in generator_profiles.columns:
            generators_with_s_profiles[g] = np.array(generator_profiles.loc[:, g].values)
            generators.append(g)

        all_combinations = create_combinations()
        highest_flh, highest_flh_combination = calculate_flh()

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=100)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=100, direction_up=False)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=1000)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=1000, direction_up=False)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        return highest_flh

    def create_web_page_multiple_results():

        entries = results_dataframe.columns.tolist()
        if 'Scenario' in entries:
            entries.remove('Scenario')

        # Implement web application
        app = dash.Dash(__name__)
        app.title = 'Result comparison'
        app.layout = html.Div([
            html.Div([
                html.H2(["PtX-Results"], className="subtitle padded", style={'font-family': 'Arial'}),
                html.Div([
                    html.Div([
                        'Select Case',
                        dcc.Dropdown(
                            className='Cases',
                            id='case',
                            options=[{'label': str(i), 'value': str(i)} for i in results_dataframe.index],
                            value=results_dataframe.index[0])
                    ])
                ])
            ]),
            dcc.Tabs([
                dcc.Tab(
                    label='Assumptions',
                    children=[
                        html.Div([
                            html.Div(id='assumptions_table')
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Overview Results',
                    children=[
                        html.Div([
                            html.Div(id='overview_table')
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Conversion Components',
                    children=[
                        html.Div([
                            html.Div(id='conversion_components_table')
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Storage',
                    children=[
                        html.Div([
                            html.Div(id='storage_table')
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Generators',
                    children=[
                        html.Div([
                            html.Div(id='generation_table')
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Commodities',
                    children=[
                        html.Div([
                            html.Div(id='commodity_table')
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Cost Overview',
                    children=[
                        html.Div(children=[
                            html.Div(id='cost_structure_figure', style={'width': '48%', 'display': 'inline-block',
                                                                        "verticalAlign": "top"}),
                            html.Div(id='cost_structure_table', style={'width': '48%', 'display': 'inline-block',
                                                                       "verticalAlign": "top"}),
                        ], style={'width': '100%', 'display': 'inline-block'})
                    ]
                ),
                dcc.Tab(
                    label='Time Series',
                    children=[
                        html.Div([
                            html.Div(id='time_series_figure'),
                            html.Div(
                                children=[
                                    html.Div(id='dropdown_menu_left', style={'width': '48%', 'display': 'inline-block',
                                                                             "verticalAlign": "top"}),
                                    html.Div(id='dropdown_menu_right', style={'width': '48%', 'display': 'inline-block',
                                                                              "verticalAlign": "top"})
                                ], style={'width': '100%', 'display': 'inline-block'})
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Features',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div([
                                    "Feature",
                                    dcc.Dropdown(
                                        className='Feature',
                                        id='feature',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'display': 'inline-block'}),
                            ]),
                            html.Div(
                                dcc.Graph(id='bar_plot')),
                        ]),
                    ]
                ),
                dcc.Tab(
                    label='Parameter Correlation',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div([
                                    "X-axis",
                                    dcc.Dropdown(
                                        className='X-axis',
                                        id='x_axis',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'display': 'inline-block'}),
                                html.Div([
                                    "Y-axis",
                                    dcc.Dropdown(
                                        className='Y-axis',
                                        id='y_axis',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
                            ]),
                            html.Div([
                                dcc.RadioItems(
                                    className='Show Trendline',
                                    id='radioitem_trendline',
                                    options=[
                                        {'label': 'None', 'value': 'None'},
                                        {'label': 'Linear', 'value': 'Linear'},
                                        {'label': 'Logarithmic', 'value': 'Logarithmic'}
                                    ],
                                    value='None',
                                    labelStyle={'display': 'inline-block'}),
                            ]),
                            html.Div(
                                dcc.Graph(id='scatter_plot')),
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Parameter Distribution',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div([
                                    "parameter",
                                    dcc.Dropdown(
                                        className='Parameter',
                                        id='parameter',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'display': 'inline-block'}),
                            ]),
                            html.Div(
                                dcc.Graph(id='histogram_plot')),
                            html.Div(
                                dcc.Graph(id='pdf_plot'))
                        ])
                    ]
                )
            ])
        ])

        if True:
            @app.callback([Output('assumptions_table', 'children'),
                           Output('overview_table', 'children'),
                           Output('conversion_components_table', 'children'),
                           Output('storage_table', 'children'),
                           Output('generation_table', 'children'),
                           Output('commodity_table', 'children'),
                           Output('cost_structure_figure', 'children'),
                           Output('cost_structure_table', 'children'),
                           Output('time_series_figure', 'children'),
                           Output('dropdown_menu_left', 'children'),
                           Output('dropdown_menu_right', 'children')],
                          Input('case', 'value'))
            def display_result_selection(selected_case):
                assumptions_tab = results_dict[selected_case]['assumptions_table']
                overview_tab = results_dict[selected_case]['overview_table']
                conversion_tab = results_dict[selected_case]['conversion_components_table']
                storage_tab = results_dict[selected_case]['storage_components_table']
                generator_tab = results_dict[selected_case]['generation_table']
                commodity_tab = results_dict[selected_case]['commodity_table']
                cost_structure_tab = results_dict[selected_case]['cost_structure_dataframe']
                cost_structure_fig = results_dict[selected_case]['cost_share_figure']
                time_series_units = results_dict[selected_case]['time_series_df'].iloc[:, 0]

                assumption_dt = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in assumptions_tab.columns],
                    data=assumptions_tab.to_dict('records'),
                    style_as_list_view=True,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'fontWeight': 'bold',
                        'background-color': '#edebeb'}
                )

                overview_dt = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in overview_tab.columns],
                    data=overview_tab.to_dict('records'),
                    style_as_list_view=True,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'fontWeight': 'bold',
                        'background-color': '#edebeb'}
                )

                conversion_dt = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in conversion_tab.columns],
                    data=conversion_tab.to_dict('records'),
                    style_as_list_view=True,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'fontWeight': 'bold',
                        'background-color': '#edebeb'}
                )

                storage_dt = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in storage_tab.columns],
                    data=storage_tab.to_dict('records'),
                    style_as_list_view=True,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'fontWeight': 'bold',
                        'background-color': '#edebeb'}
                )

                generator_dt = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in generator_tab.columns],
                    data=generator_tab.to_dict('records'),
                    style_as_list_view=True,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'fontWeight': 'bold',
                        'background-color': '#edebeb'}
                )

                commodity_dt = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in commodity_tab.columns],
                    data=commodity_tab.to_dict('records'),
                    style_as_list_view=True,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'fontWeight': 'bold',
                        'background-color': '#edebeb'}
                )

                cost_structure_dt = dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in cost_structure_tab.columns],
                    data=cost_structure_tab.to_dict('records'),
                    style_as_list_view=True,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'fontWeight': 'bold',
                        'background-color': '#edebeb'}
                )

                cost_structure_graph = dcc.Graph(id='cost_share_figure', figure=cost_structure_fig)

                time_series_graph = dcc.Graph(id='time_series_graphic')
                dropdown_left = html.Div([
                    "left Y-axis",
                    dcc.Dropdown(
                        className='Y-axis left',
                        id='yaxis_main',
                        options=[{'label': str(i), 'value': str(i)} for i in
                                 time_series_units.unique()]),
                    dcc.Checklist(
                        id='checklist_left',
                        labelStyle={'display': 'block'})]),
                dropdown_right = html.Div([
                    "right Y-axis",
                    dcc.Dropdown(
                        className='Y-axis right',
                        id='yaxis_right',
                        options=[{'label': str(i), 'value': str(i)} for i in
                                 time_series_units.unique()]),
                    dcc.Checklist(
                        id='checklist_right',
                        labelStyle={'display': 'block'})])

                return [assumption_dt, overview_dt, conversion_dt, storage_dt, generator_dt, commodity_dt,
                        cost_structure_graph, cost_structure_dt, time_series_graph, dropdown_left, dropdown_right]

            @app.callback(
                Output('checklist_left', 'options'),
                [Input('yaxis_main', 'value'), Input('case', 'value')]
            )
            def update_dropdown_left(y_axis, selected_case):
                time_series_dataframe = results_dict[selected_case]['time_series_df']
                time_series_units = time_series_dataframe.iloc[:, 0]
                t = time_series_units == str(y_axis)
                return [{'label': str(time_series_dataframe.at[i, 'Name']), 'value': str(i)}
                        for i in t.index[t.tolist()]]

            @app.callback(
                Output('checklist_right', 'options'),
                [Input('yaxis_right', 'value'), Input('case', 'value')]
            )
            def update_dropdown_right(y_axis_right, selected_case):
                time_series_dataframe = results_dict[selected_case]['time_series_df']
                time_series_units = time_series_dataframe.iloc[:, 0]
                t = time_series_units == str(y_axis_right)
                return [{'label': str(time_series_dataframe.at[i, 'Name']), 'value': str(i)}
                        for i in t.index[t.tolist()]]

            @app.callback(
                Output('time_series_graphic', 'figure'),
                Input('checklist_left', 'value'),
                Input('checklist_right', 'value'),
                Input('yaxis_main', 'value'),
                Input('yaxis_right', 'value'),
                Input("case", "value")
            )
            def update_graph(left_checklist, right_checklist, unit_left, unit_right, case):

                time_series = results_dict[case]['time_series_df']

                units = time_series.iloc[:, 0]
                data = time_series.iloc[:, 1:]

                # Dictionary to get index-triple from str(i)
                index = dict([(str(i), i) for i in time_series.index])

                def merge_tuples(*t):
                    return tuple(j for i in t for j in (i if isinstance(i, tuple) else (i,)))

                first_column_index = ['Charging', 'Discharging', 'Demand', 'Emitting', 'Freely Available', 'Potential Generation', 'Generation',
                                      'Purchase', 'Selling', 'Input', 'Output', 'State of Charge',
                                      'Total Potential Generation', 'Total Generation', 'Hot Standby Demand']

                time_series['Name'] = time_series.index.tolist()
                for c in first_column_index:
                    if c in time_series.index.get_level_values(0):
                        for i in time_series.loc[c].index:
                            if str(i[0]) == 'nan':
                                name = str(i[1]) + ' ' + c
                            else:
                                name = str(i[1]) + ' ' + c + ' ' + str(i[0])

                            time_series.at[merge_tuples(c, i), 'Name'] = name

                color_left = cycle(px.colors.qualitative.Plotly)
                color_right = cycle(px.colors.qualitative.Plotly[::-1])
                if unit_right is None:
                    data_graph = []
                    if left_checklist is not None:
                        for i in range(0, len(left_checklist)):
                            globals()['right_trace%s' % i] = \
                                go.Scatter(
                                    x=data.columns,
                                    y=data.loc[index[left_checklist[i]]],
                                    name=time_series.at[index[left_checklist[i]], 'Name'] + ', '
                                         + units.loc[index[left_checklist[i]]],
                                    line=dict(color=next(color_left))
                                )
                            data_graph.append(globals()['right_trace%s' % i])
                    layout = go.Layout(
                        title="PtX-Model: Commodity Visualization",
                        xaxis=dict(
                            title='h',
                            range=[0, data.shape[1] + 10]
                        ),
                        yaxis=dict(
                            title=unit_left,
                            rangemode="tozero",
                            showgrid=True
                        ),
                        legend=dict(
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        showlegend=True,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='#f7f7f7'
                    )
                    fig = go.Figure(data=data_graph, layout=layout)
                    return fig
                elif unit_right is not None:
                    data_graph = []
                    for i in range(0, len(left_checklist)):
                        globals()['left_trace%s' % i] = go.Scatter(
                            x=data.columns,
                            y=data.loc[index[left_checklist[i]]],
                            name=time_series.at[index[left_checklist[i]], 'Name'],
                            legendgroup='left',
                            legendgrouptitle=dict(
                                text=str(units.loc[index[left_checklist[i]]]) + ':'
                            ),
                            line=dict(color=next(color_left)),
                        )
                        data_graph.append(globals()['left_trace%s' % i])
                    if right_checklist is not None:
                        for i in range(0, len(right_checklist)):
                            globals()['right_trace%s' % i] = go.Scatter(
                                x=data.columns,
                                y=data.loc[index[right_checklist[i]]],
                                name=time_series.at[index[right_checklist[i]], 'Name'],
                                yaxis='y2',
                                legendgroup='right',
                                legendgrouptitle=dict(
                                    text=str(units.loc[index[right_checklist[i]]]) + ':'
                                ),
                                line=dict(color=next(color_right)))
                            data_graph.append(globals()['right_trace%s' % i])
                    layout = go.Layout(
                        title="PtX-Model: Commodity Visualization",
                        xaxis=dict(
                            title='h',
                            domain=[0, 0.95]
                        ),
                        yaxis=dict(
                            title=unit_left,
                            rangemode='tozero'
                        ),
                        yaxis2=dict(
                            title=unit_right,
                            rangemode='tozero',
                            overlaying='y',
                            side='right',
                        ),
                        legend=dict(
                            # orientation='h',
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        legend_tracegroupgap=25,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='#f7f7f7'
                    )
                    fig = go.Figure(data=data_graph, layout=layout)
                    return fig

            @app.callback(
                Output('load_profile', 'figure'),
                Output('load_profile', 'style'),
                Input('load_profile_checklist', 'value'),
                Input("case", "value"))
            def update_load_profile(check, case):

                time_series_dataframe = results_dataframe[case]['time_series_df']
                data = time_series_dataframe.iloc[:, 1:]

                # Dictionary to get index-triple from str(i)
                index = dict([(str(i), i) for i in time_series_dataframe.index])

                load_profile_data = []
                if check is not None:
                    for i in range(0, len(check)):
                        cache = data.sort_values(axis=1, by=index[check[i]],
                                                 ignore_index=True, ascending=False).loc[index[check[i]]]
                        load_profile_data.append(
                            go.Bar(
                                x=cache.index,
                                y=cache,
                                name=time_series_dataframe.at[index[check[i]], 'Name'],
                                width=1,
                                marker=dict(line=dict(width=0))
                            )
                        )
                    layout = go.Layout(
                        title="Load profile",
                        xaxis=dict(
                            title='h',
                            categoryorder='category descending'
                        ),
                        yaxis=dict(
                            title='kW',
                            rangemode='tozero'
                        ),
                        barmode='stack',
                        legend=dict(
                            orientation='h',
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        paper_bgcolor='rgba(255, 255, 255, 255)',
                        plot_bgcolor='#f7f7f7',
                    )
                    fig = go.Figure(data=load_profile_data, layout=layout)
                    style = {'width': '80%', 'display': 'inline-block'}
                    return fig, style

        @app.callback(
            Output("bar_plot", "figure"),
            Input("feature", "value"))
        def update_bar_chart(feature):

            sub_df = results_dataframe.copy()

            color_discrete_map = {}
            i = 0
            for sc in sub_df['Scenario'].unique():
                color_discrete_map[sc] = colors[i]
                i += 1

            sub_df = sub_df.fillna(0)
            sub_df.sort_values(by=[feature], inplace=True)

            if 'Scenario' not in sub_df.columns:

                sub_df['Case Name'] = sub_df.index

                fig = px.bar(sub_df, x='Case Name', y=feature)
                fig.update_layout(
                    yaxis_title=feature + ' [' + units_dict[feature] + ']',
                    xaxis_showticklabels=False)

            else:

                index = []
                for c in sub_df.index:
                    index.append(sub_df.loc[c, 'Scenario'] + ' ' + c)

                sub_df['Case Name'] = index

                fig = px.bar(sub_df, x='Case Name', y=feature, color='Scenario',
                             color_discrete_map=color_discrete_map)
                fig.update_layout(
                    yaxis_title=feature + ' [' + units_dict[feature] + ']',
                    xaxis_showticklabels=False,
                    xaxis_categoryorder='total ascending',
                    legend_title="Scenario")

            return fig

        @app.callback(
            Output("scatter_plot", "figure"),
            [Input("x_axis", "value"),
             Input("y_axis", "value"),
             Input('radioitem_trendline', 'value')])
        def update_scatter_chart(x_axis, y_axis, ri_value):

            sub_df = results_dataframe.copy()
            sub_df = sub_df.fillna(0)

            if 'Scenario' not in sub_df.columns:
                if ri_value == 'None':
                    fig = px.scatter(sub_df, x=x_axis, y=y_axis)
                elif ri_value == 'Linear':
                    fig = px.scatter(sub_df, x=x_axis, y=y_axis, trendline="ols")
                else:
                    fig = px.scatter(sub_df, x=x_axis, y=y_axis, trendline="ols",
                                     trendline_options=dict(log_x=True))

                fig.update_layout(
                    xaxis_title=x_axis + ' [' + units_dict[x_axis] + ']',
                    yaxis_title=y_axis + ' [' + units_dict[y_axis] + ']')

            else:
                color_discrete_map = {}
                i = 0
                for sc in sub_df['Scenario'].unique():
                    color_discrete_map[sc] = colors[i]
                    i += 1

                if ri_value == 'None':
                    fig = px.scatter(sub_df, x=x_axis, y=y_axis, color='Scenario',
                                     color_discrete_map=color_discrete_map)
                elif ri_value == 'Linear':
                    fig = px.scatter(sub_df, x=x_axis, y=y_axis, color='Scenario',
                                     color_discrete_map=color_discrete_map, trendline="ols")
                else:
                    fig = px.scatter(sub_df, x=x_axis, y=y_axis, color='Scenario',
                                     color_discrete_map=color_discrete_map, trendline="ols",
                                     trendline_options=dict(log_x=True))

                fig.update_layout(
                    xaxis_title=x_axis + ' [' + units_dict[x_axis] + ']',
                    yaxis_title=y_axis + ' [' + units_dict[y_axis] + ']',
                    legend_title="Scenario")

            return fig

        @app.callback(
            [Output("histogram_plot", "figure"),
             Output("pdf_plot", "figure")],
            Input("parameter", "value"))
        def update_dist_charts(parameter):

            sub_df = results_dataframe.copy()
            sub_df = sub_df.fillna(0)

            # Kick out values which are strings
            rows_to_keep = []
            for r in sub_df.index:
                if not (isinstance(sub_df.loc[r, parameter], str)):
                    rows_to_keep.append(r)

            sub_df = sub_df.loc[rows_to_keep, :]

            # Kick out values which are just 0
            for scenario in sub_df['Scenario'].unique():
                ind = sub_df[sub_df['Scenario'] == scenario].index

                if sub_df.loc[ind, parameter].sum() == 0:
                    sub_df.drop(ind, inplace=True)

            sub_df[parameter] = sub_df[parameter].astype(float)

            if 'Scenario' in sub_df.columns:

                hist_data = []
                group_labels = []
                colors_applied = []
                color_discrete_map = {}
                i = 0
                for scenario in sub_df['Scenario'].unique():
                    ind = sub_df[sub_df['Scenario'] == scenario].index

                    if len(ind) <= 1:
                        continue

                    hist_data.append(sub_df.loc[ind, parameter].values)
                    group_labels.append(scenario)  # name of the dataset

                    color_discrete_map[scenario] = colors[i]
                    colors_applied.append(colors[i])
                    i += 1

                fig1 = px.histogram(sub_df, x=parameter, color='Scenario', marginal="box",
                                    barmode='group', color_discrete_map=color_discrete_map)
                fig1.update_layout(
                    xaxis_title=parameter + ' [' + units_dict[parameter] + ']',
                    yaxis_title="Amount",
                    legend_title="Scenario")

                fig2 = ff.create_distplot(hist_data, group_labels, colors=colors_applied, show_hist=False)
                fig2.update_layout(
                    xaxis_title=parameter + ' [' + units_dict[parameter] + ']',
                    yaxis_title="Probability",
                    legend_title="Scenario")

            else:
                hist_data = [sub_df[parameter].values]
                group_labels = [parameter]  # name of the dataset

                fig1 = px.histogram(sub_df[parameter], marginal="box")
                fig1.update_layout(
                    xaxis_title=parameter + ' [' + units_dict[parameter] + ']',
                    yaxis_title="Amount")

                fig2 = ff.create_distplot(hist_data, group_labels, show_hist=False)
                fig2.update_layout(
                    xaxis_title=parameter + ' [' + units_dict[parameter] + ']',
                    yaxis_title="Probability")

            return fig1, fig2

        def open_page():
            return webbrowser.open('http://127.0.0.1:8050/')

        Timer(1.0, open_page()).start(),
        app.run_server(debug=False, use_reloader=False)

    colors = ['darkgreen', 'mediumblue', 'maroon', 'goldenrod', 'purple', 'darkgrey', 'orangered',
              'lawngreen', 'royalblue', 'slategrey', 'sienna', 'springgreen', 'teal', 'indigo', 'khaki', 'brown',
              'dodgerblue', 'lightgreen', 'crimson']

    visualization_type, scenarios, results_per_scenario = check_visualization_type()

    if visualization_type == 'single_result':

        name_scenario = path.split('/')[-1]

        monetary_unit_str, assumptions_table, assumptions_table_columns, \
            annual_production_value, annual_production_unit_str, \
            overview_dataframe, overview_table, components_dataframe,\
            conversion_components_table, conversion_components_table_columns,\
            storage_components_table, storage_components_table_columns, \
            cost_figure, cost_share_figure, cost_structure_dataframe, \
            generation_dataframe, generation_table, commodity_dataframe, commodity_table, \
            time_series_dataframe, generation_profile = extract_data_single_results(path)

        create_browser_visualization_single_result()

    else:

        results_dataframe = pd.DataFrame()

        results_dict = {}
        units_dict = {}
        for scenario in scenarios:
            results_dict[scenario] = {}
            for result in results_per_scenario[scenario]:

                if result == 'results.csv':
                    continue

                if visualization_type == 'multiple_results_with_single_scenario':
                    results_path = path + result + '/'
                else:
                    results_path = path + '/' + scenario + '/' + result + '/'

                monetary_unit_str, assumptions_table, assumptions_table_columns, \
                    annual_production_value, annual_production_unit_str, \
                    overview_dataframe, overview_table, components_dataframe,\
                    conversion_components_table, conversion_components_table_columns, \
                    storage_components_table, storage_components_table_columns, \
                    cost_figure, cost_share_figure, cost_structure_dataframe, \
                    generation_dataframe, generation_table, commodity_dataframe, commodity_table, \
                    time_series_dataframe, generation_profile = extract_data_single_results(results_path)

                results_dict[result] = {'monetary_unit_str': monetary_unit_str,
                                    'assumptions_table': assumptions_table,
                                    'assumptions_table_columns': assumptions_table_columns,
                                    'annual_production_value': annual_production_value,
                                    'annual_production_unit_str': annual_production_unit_str,
                                    'overview_table': overview_table,
                                    'conversion_components_table': conversion_components_table,
                                    'conversion_components_table_columns': conversion_components_table_columns,
                                    'storage_components_table': storage_components_table,
                                    'storage_components_table_columns': storage_components_table_columns,
                                    'cost_figure': cost_figure,
                                    'cost_share_figure': cost_share_figure,
                                    'cost_structure_dataframe': cost_structure_dataframe,
                                    'generation_table': generation_table,
                                    'commodity_table': commodity_table,
                                    'time_series_df': time_series_dataframe}

                folder_df = pd.DataFrame(index=[result])
                folder_df.loc[result, 'Scenario'] = scenario

                if generation_dataframe is not None:

                    covered_commodities = []

                    for s in generation_dataframe['Generated Commodity'].unique():

                        generators_with_s = generation_dataframe[generation_dataframe['Generated Commodity'] == s].index

                        if len(generators_with_s) > 0:

                            covered_commodities.append(s)

                            potential_generation_s = 0
                            total_capacity_s = 0
                            actual_generation_s = 0
                            curtailment_s = 0

                            unit = commodity_dataframe.loc[s, 'unit']
                            if unit in ['kWh', 'MWh', 'GWh']:
                                unit_capacity = unit.split('h')[0] + ' ' + s
                            else:
                                unit_capacity = unit + ' ' + s + '/h'

                            for g in generators_with_s:
                                folder_df.loc[result, g + ' Capacity'] = generation_dataframe.loc[g, 'Capacity']
                                units_dict[g + ' Capacity'] = unit_capacity

                                folder_df.loc[result, g + ' Potential Full-load Hours'] = generation_dataframe.loc[
                                    g, 'Potential Full-load Hours']
                                units_dict[g + ' Potential Full-load Hours'] = 'h'

                                folder_df.loc[result, g + ' Potential LCOE'] = generation_dataframe.loc[
                                    g, 'LCOE before Curtailment']
                                units_dict[g + ' Potential LCOE'] = monetary_unit_str + '/' + unit + ' ' + s

                                folder_df.loc[result, g + ' Absolute Curtailment'] = generation_dataframe.loc[
                                    g, 'Curtailment']
                                units_dict[g + ' Absolute Curtailment'] = unit + ' ' + s

                                folder_df.loc[result, g + ' Relative Curtailment'] = generation_dataframe.loc[
                                                                                    g, 'Curtailment'] \
                                                                                / (folder_df.loc[
                                                                                       result, g + ' Capacity']
                                                                                   * folder_df.loc[
                                                                                       result, g + ' Potential Full-load Hours']) * 100
                                units_dict[g + ' Relative Curtailment'] = '% of Potential Generation'

                                folder_df.loc[result, g + ' Actual Full-load Hours'] = generation_dataframe.loc[
                                    g, 'Actual Full-load Hours']
                                units_dict[g + ' Actual Full-load Hours'] = 'h'

                                folder_df.loc[result, g + ' Actual LCOE'] = generation_dataframe.loc[
                                    g, 'LCOE after Curtailment']
                                units_dict[g + ' Actual LCOE'] = monetary_unit_str + '/' + unit + ' ' + s

                                potential_generation_s += generation_dataframe.loc[g, 'Potential Generation']
                                units_dict[g + ' Potential Generation'] = unit + ' ' + s

                                total_capacity_s += generation_dataframe.loc[g, 'Capacity']
                                actual_generation_s += generation_dataframe.loc[g, 'Actual Generation']
                                curtailment_s += generation_dataframe.loc[g, 'Curtailment']

                            folder_df.loc[result, s + ' Generation Capacity'] = total_capacity_s
                            units_dict[s + ' Generation Capacity'] = unit_capacity

                            folder_df.loc[result, s + ' Potential Full-load Hours'] = potential_generation_s / (
                                    total_capacity_s * 8760) * 8760
                            units_dict[s + ' Potential Full-load Hours'] = 'h'

                            folder_df.loc[result, s + ' Potential LCOE'] = commodity_dataframe.loc[s, 'Total Generation Fix Costs'] / potential_generation_s
                            units_dict[s + ' Potential LCOE'] = monetary_unit_str + '/' + unit + ' ' + s

                            folder_df.loc[result, s + ' Actual Full-load Hours'] = actual_generation_s / (
                                    total_capacity_s * 8760) * 8760
                            units_dict[s + ' Actual Full-load Hours'] = 'h'

                            folder_df.loc[result, s + ' Actual LCOE'] = commodity_dataframe.loc[
                                                                       s, 'Total Generation Fix Costs'] / actual_generation_s
                            units_dict[s + ' Actual LCOE'] = monetary_unit_str + '/' + unit + ' ' + s

                            folder_df.loc[result, s + ' Absolute Curtailment'] = curtailment_s
                            units_dict[s + ' Absolute Curtailment'] = unit + ' ' + s

                            folder_df.loc[result, s + ' Relative Curtailment'] = curtailment_s / potential_generation_s
                            units_dict[s + ' Relative Curtailment'] = unit + ' ' + s

                            folder_df.loc[result, s + ' Generation Costs'] = commodity_dataframe.loc[
                                s, 'Production Costs per Unit']
                            units_dict[s + ' Generation Costs'] = monetary_unit_str + '/' + unit + ' ' + s

                    for c in commodity_dataframe.index:
                        if c not in covered_commodities:
                            folder_df.loc[result, c + ' Production Costs per Unit'] = commodity_dataframe.loc[
                                c, 'Production Costs per Unit']
                            unit = commodity_dataframe.loc[c, 'unit']
                            units_dict[c + ' Production Costs per Unit'] = monetary_unit_str + '/' + unit + ' ' + c

                            folder_df.loc[result, c + ' Total Production Costs'] = \
                                (commodity_dataframe.loc[c, 'Production Costs per Unit']
                                 * commodity_dataframe.loc[c, 'Total Commodity'])
                            units_dict[c + ' Total Production Costs'] = monetary_unit_str

                    for c in components_dataframe.index:

                        if components_dataframe.loc[c, 'Capacity Basis'] == 'input':
                            folder_df.loc[result, c + ' Capacity'] = components_dataframe.loc[c, 'Capacity [input]']
                            capacity_unit = components_dataframe.loc[c, 'Capacity Unit [input]']

                            folder_df.loc[result, c + ' Full-load Hours'] = components_dataframe.loc[
                                c, 'Full-load Hours']
                            units_dict[c + ' Full-load Hours'] = 'h'
                        elif components_dataframe.loc[c, 'Capacity Basis'] == 'output':
                            folder_df.loc[result, c + ' Capacity'] = components_dataframe.loc[c, 'Capacity [output]']
                            capacity_unit = components_dataframe.loc[c, 'Capacity Unit [output]']

                            folder_df.loc[result, c + ' Full-load Hours'] = components_dataframe.loc[
                                c, 'Full-load Hours']
                            units_dict[c + ' Full-load Hours'] = 'h'

                        else:
                            if isinstance(components_dataframe.loc[c, 'Capacity Unit [input]'], float):
                                folder_df.loc[result, c + ' Capacity'] = components_dataframe.loc[c, 'Capacity [output]']
                                capacity_unit = components_dataframe.loc[c, 'Capacity Unit [output]']
                            else:
                                folder_df.loc[result, c + ' Capacity'] = components_dataframe.loc[c, 'Capacity [input]']
                                capacity_unit = components_dataframe.loc[c, 'Capacity Unit [input]']

                        if c + ' Capacity' not in [*units_dict.keys()]:
                            units_dict[c + ' Capacity'] = capacity_unit

                    folder_df.loc[result, 'Production Costs'] = overview_dataframe.loc[
                        'Production Costs per Unit', 0]
                    units_dict['Production Costs'] = monetary_unit_str + '/' + annual_production_unit_str

                results_dataframe = pd.concat([results_dataframe, folder_df], axis=0)

        column_names = {}
        for c in results_dataframe.columns:
            if c == 'Scenario':
                continue
            column_names[c] = c + ' [' + units_dict[c] + ']'
        results_dataframe.rename(column_names, axis='columns').to_csv(path + '/results.csv', encoding='cp1252')

        create_web_page_multiple_results()
