import pandas as pd

from _helpers_gui import SettingWindow
from _helpers_visualization import create_visualization

import tkinter as tk
from tkinter import *
from tkinter import ttk
from datetime import datetime

from _helpers_gui import AssumptionsInterface, ComponentInterface, CommodityInterface, StorageInterface,\
    GeneratorInterface, DataInterface, save_current_parameters_and_options
from ptx_now._helper_optimization import optimize
from parameter_object import ParameterObject
from load_projects import load_project

import os
from os import walk
import yaml


def run_main():
    setting_window = SettingWindow()

    # todo: adjust this file --> check settings necessary

    if setting_window.go_on:

        path_data = setting_window.path_data
        path_result = setting_window.path_result
        path_projects = setting_window.path_projects
        path_optimize = setting_window.path_optimize
        solver = setting_window.solver
        path_visualization = setting_window.path_visualization

        if setting_window.optimize_or_visualize_projects_variable.get() == 'optimize':

            if setting_window.optimize_variable.get() == 'new':

                GUI(path_data=path_data, path_result=path_result, path_projects=path_projects, solver=solver)

            elif setting_window.optimize_variable.get() == 'custom':
                GUI(path_data=path_data, path_result=path_result, path_projects=path_projects,
                    path_optimize=path_optimize, solver=solver)

            else:

                path_to_settings = path_projects + path_optimize

                # Get path of every object in folder
                _, _, filenames = next(walk(path_to_settings))

                for file in filenames:
                    file = file.split('/')[0]

                    print('Currently optimized: ' + file)

                    path = path_to_settings + '/' + file
                    file_without_ending = file.split('.')[0]

                    pm_object = ParameterObject('parameter', integer_steps=10, path_data=path_data)
                    if 'xlsx' in path:
                        case_data = pd.read_excel(path, index_col=0)
                    else:
                        yaml_file = open(path)
                        case_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
                    pm_object = load_project(pm_object, case_data)
                    pm_object.set_project_name(file_without_ending)

                    optimize(pm_object, path_data, path_result, solver)

        else:

            path_visualization = path_result + path_visualization + '/'
            create_visualization(path_visualization)


class GUI:

    def widgets(self):

        self.overall_notebook = ttk.Notebook(self.root)

        self.general_assumptions = AssumptionsInterface(self, self.overall_notebook,
                                                pm_object_original=self.pm_object_original,
                                                pm_object_copy=self.pm_object_copy,)
        self.general_assumptions.pack(fill='both', expand=True)

        self.components = ComponentInterface(self, self.overall_notebook,
                                             pm_object_original=self.pm_object_original,
                                             pm_object_copy=self.pm_object_copy)
        self.components.pack(fill='both', expand=True)

        self.commodities = CommodityInterface(self, self.overall_notebook,
                                       pm_object_original=self.pm_object_original,
                                       pm_object_copy=self.pm_object_copy)
        self.commodities.pack(fill='both', expand=True)

        self.storages = StorageInterface(self, self.overall_notebook,
                                         pm_object_original=self.pm_object_original,
                                         pm_object_copy=self.pm_object_copy)
        self.storages.pack(fill='both', expand=True)

        self.generators = GeneratorInterface(self, self.overall_notebook,
                                             pm_object_original=self.pm_object_original,
                                             pm_object_copy=self.pm_object_copy)
        self.generators.pack(fill='both', expand=True)

        self.data = DataInterface(self, self.overall_notebook,
                                  pm_object_original=self.pm_object_original,
                                  pm_object_copy=self.pm_object_copy)
        self.data.pack(fill='both', expand=True)

        self.overall_notebook.add(self.general_assumptions, text='General Assumptions')
        self.overall_notebook.add(self.components, text='Conversions')
        self.overall_notebook.add(self.commodities, text='Commodities')
        self.overall_notebook.add(self.storages, text='Storages')
        self.overall_notebook.add(self.generators, text='Generators')
        self.overall_notebook.add(self.data, text='Data')

        self.overall_notebook.pack(pady=10, expand=True, anchor='n')

        button_frame = ttk.Frame(self.root)

        check_commodities_button = ttk.Button(button_frame, text='Check Project', command=self.check_all_settings)
        check_commodities_button.grid(row=0, column=0, sticky='ew')

        self.optimize_button = ttk.Button(button_frame, text='Optimize', state=DISABLED, command=self.optimize_now)
        self.optimize_button.grid(row=0, column=1, sticky='ew')

        save_settings = ttk.Button(button_frame, text='Save Project', command=self.save_setting_window)
        save_settings.grid(row=1, column=0, sticky='ew')

        return_to_start = ttk.Button(button_frame, text='Cancel', command=self.cancel)
        return_to_start.grid(row=1, column=1, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        button_frame.pack(fill="both", expand=True)

        self.root.mainloop()

    def update_widgets(self):
        # Simply recreate the frames with the new pm object

        self.general_assumptions.update_self_pm_object(self.pm_object_copy)
        self.general_assumptions.update_frame()

        self.components.update_self_pm_object(self.pm_object_copy)
        self.components.update_frame()

        self.commodities.update_self_pm_object(self.pm_object_copy)
        self.commodities.update_frame()

        self.storages.update_self_pm_object(self.pm_object_copy)
        self.storages.update_frame()

        self.generators.update_self_pm_object(self.pm_object_copy)
        self.generators.update_frame()

        self.data.update_self_pm_object(self.pm_object_copy)
        self.data.update_frame()

        self.optimize_button.config(state=DISABLED)

    def check_all_settings(self):

        if False:

            def kill_window():
                alert_window.destroy()

            valid_me_for_commodity = {}
            commodities_without_well = []
            commodities_without_sink = []
            profile_not_exist = []

            for commodity in self.pm_object_copy.get_final_commodities_objects():

                well_existing = False
                sink_existing = False

                # Check if commodity has a well
                if commodity.is_available():
                    well_existing = True
                elif commodity.is_purchasable():
                    well_existing = True

                # If no well exists, the commodity has to be generated or converted from other commodity
                if not well_existing:
                    for component in self.pm_object_copy.get_final_conversion_components_objects():
                        outputs = component.get_outputs()
                        for o in [*outputs.keys()]:
                            if o == commodity.get_name():
                                well_existing = True
                                break

                if not well_existing:
                    for component in self.pm_object_copy.get_final_generator_components_objects():
                        if commodity.get_name() == component.get_generated_commodity():
                            well_existing = True
                            break

                if not well_existing:
                    commodities_without_well.append(commodity.get_name())

                # Check if commodity has a sink
                if commodity.is_emittable():
                    sink_existing = True
                elif commodity.is_saleable():
                    sink_existing = True
                elif commodity.is_demanded():
                    sink_existing = True

                for component in self.pm_object_copy.get_final_conversion_components_objects():
                    inputs = component.get_inputs()
                    for i in [*inputs.keys()]:
                        if i == commodity.get_name():
                            sink_existing = True
                            break

                if not sink_existing:
                    commodities_without_sink.append(commodity.get_name())

                if well_existing & sink_existing:
                    valid_me_for_commodity.update({commodity.get_name(): True})
                else:
                    valid_me_for_commodity.update({commodity.get_name(): False})

            all_commodities_valid = True
            for commodity in self.pm_object_copy.get_final_commodities_objects():
                if not valid_me_for_commodity[commodity.get_name()]:
                    all_commodities_valid = False

            # Check if a profile for the generation unit exists, if generation unit is enabled
            if len(self.pm_object_copy.get_final_generator_components_names()) > 0:
                if self.pm_object_copy.get_single_or_multiple_profiles() == 'single':
                    if self.pm_object_copy.get_profile_data().split('.')[-1] == 'csv':
                        generation_profile = pd.read_csv(self.path_data + self.pm_object_copy.get_profile_data(), index_col=0)
                    else:
                        generation_profile = pd.read_excel(self.path_data + self.pm_object_copy.get_profile_data(), index_col=0)

                    for generator in self.pm_object_copy.get_final_generator_components_objects():
                        if generator.get_name() not in generation_profile.columns:
                            profile_not_exist.append(generator.get_name())
                else:
                    path_to_generation_files = self.path_data + '/' + self.pm_object_copy.get_profile_data()
                    _, _, filenames = next(walk(path_to_generation_files))

                    for f in filenames:
                        path = path_to_generation_files + '/' + f
                        if path.split('.')[-1] == 'xlsx':
                            generation_profile = pd.read_excel(path, index_col=0)
                        else:
                            generation_profile = pd.read_csv(path, index_col=0)

                        for generator in self.pm_object_copy.get_final_generator_components_objects():
                            if generator.get_name() not in generation_profile.columns:
                                profile_not_exist.append(generator.get_name())

                        break

            # Check if a profile for the commodity unit exists
            for commodity in self.pm_object_copy.get_final_commodities_objects():
                if commodity.is_saleable():
                    if commodity.get_sale_price_type() == 'variable':

                        column_name = commodity.get_name() + '_Selling_Price'

                        if self.pm_object_copy.get_single_or_multiple_commodity_profiles() == 'single':
                            if self.pm_object_copy.get_profile_data().split('.')[-1] == 'xlsx':
                                commodity_profile = pd.read_excel(self.path_data + self.pm_object_copy.get_profile_data(),
                                                                  index_col=0)
                            else:
                                commodity_profile = pd.read_csv(self.path_data + self.pm_object_copy.get_profile_data(),
                                                                index_col=0)

                            if column_name not in commodity_profile.columns:
                                profile_not_exist.append(commodity.get_name() + ' Selling Price')
                        else:
                            path_to_commodity_files = self.path_data + '/' + self.pm_object_copy.get_profile_data()
                            _, _, filenames = next(walk(path_to_commodity_files))

                            for f in filenames:
                                path = path_to_commodity_files + '/' + f
                                if path.split('.')[-1] == 'xlsx':
                                    commodity_profile = pd.read_excel(path, index_col=0)
                                else:
                                    commodity_profile = pd.read_csv(path, index_col=0)

                                if column_name not in commodity_profile.columns:
                                    profile_not_exist.append(commodity.get_name() + ' Selling Price')

                                break

                if commodity.is_purchasable():
                    if commodity.get_purchase_price_type() == 'variable':
                        column_name = commodity.get_name() + '_Purchase_Price'

                        if self.pm_object_copy.get_single_or_multiple_commodity_profiles() == 'single':
                            if self.pm_object_copy.get_profile_data().split('.')[-1] == 'xlsx':
                                commodity_profile = pd.read_excel(self.path_data + self.pm_object_copy.get_profile_data(),
                                                                  index_col=0)
                            else:
                                commodity_profile = pd.read_csv(self.path_data + self.pm_object_copy.get_profile_data(),
                                                                index_col=0)

                            if column_name not in commodity_profile.columns:
                                profile_not_exist.append(commodity.get_name() + ' Purchase Price')
                        else:
                            path_to_commodity_files = self.path_data + '/' + self.pm_object_copy.get_profile_data()
                            _, _, filenames = next(walk(path_to_commodity_files))

                            for f in filenames:
                                path = path_to_commodity_files + '/' + f
                                if path.split('.')[-1] == 'xlsx':
                                    commodity_profile = pd.read_excel(path, index_col=0)
                                else:
                                    commodity_profile = pd.read_csv(path, index_col=0)

                                if column_name not in commodity_profile.columns:
                                    profile_not_exist.append(commodity.get_name() + ' Purchase Price')

                                break

                if commodity.is_demanded():
                    if commodity.get_purchase_price_type() == 'variable':
                        column_name = commodity.get_name() + '_Demand'

                        if self.pm_object_copy.get_single_or_multiple_commodity_profiles() == 'single':
                            if self.pm_object_copy.get_profile_data().split('.')[-1] == 'xlsx':
                                commodity_profile = pd.read_excel(self.path_data + self.pm_object_copy.get_profile_data(),
                                                                  index_col=0)
                            else:
                                commodity_profile = pd.read_csv(self.path_data + self.pm_object_copy.get_profile_data(),
                                                                index_col=0)

                            if column_name not in commodity_profile.columns:
                                profile_not_exist.append(commodity.get_name() + ' Demand')
                        else:
                            path_to_commodity_files = self.path_data + '/' + self.pm_object_copy.get_profile_data()
                            _, _, filenames = next(walk(path_to_commodity_files))

                            for f in filenames:
                                path = path_to_commodity_files + '/' + f
                                if path.split('.')[-1] == 'xlsx':
                                    commodity_profile = pd.read_excel(path, index_col=0)
                                else:
                                    commodity_profile = pd.read_csv(path, index_col=0)

                                if column_name not in commodity_profile.columns:
                                    profile_not_exist.append(commodity.get_name() + ' Demand')

                                break

            # Create alert if sink, well or profile is missing
            error_in_setting = False
            if (len(profile_not_exist) > 0) | (not all_commodities_valid):
                error_in_setting = True

            if error_in_setting:
                self.optimize_button.config(state=DISABLED)
                alert_window = Toplevel(self.root)
                alert_window.title('')

                if not all_commodities_valid:

                    no_well_text = ''
                    no_sink_text = ''

                    if len(commodities_without_well) > 0:

                        if len(commodities_without_well) == 1:
                            no_well_text = 'The following commodity has no well: '
                        else:
                            no_well_text = 'The following commodities have no well: '

                        for commodity in commodities_without_well:
                            if commodities_without_well.index(commodity) != len(commodities_without_well) - 1:
                                no_well_text += commodity + ', '
                            else:
                                no_well_text += commodity

                    if len(commodities_without_sink) > 0:

                        if len(commodities_without_well) == 1:
                            no_sink_text = 'The following commodity has no sink: '
                        else:
                            no_sink_text = 'The following commodities have no sink: '

                        for commodity in commodities_without_sink:
                            if commodities_without_sink.index(commodity) != len(commodities_without_sink) - 1:
                                no_sink_text += commodity + ', '
                            else:
                                no_sink_text += commodity

                    if no_well_text != '':

                        tk.Label(alert_window, text=no_well_text).pack()
                        tk.Label(alert_window,
                                 text='It is important that every commodity has a well. \n' +
                                      ' That means that it is either generated, converted from another commodity,' +
                                      ' freely available or purchasable. \n'
                                      ' Please adjust your inputs/outputs or the individual commodity').pack()
                        tk.Label(alert_window, text='').pack()

                    if no_sink_text != '':

                        tk.Label(alert_window, text=no_sink_text).pack()
                        tk.Label(alert_window,
                                 text='It is important that every commodity has a sink. \n'
                                      ' That means that it is either converted to another commodity,' +
                                      ' emitted, saleable or implemented as demand. \n' +
                                      ' Please adjust your inputs/outputs or the individual commodity').pack()
                        tk.Label(alert_window, text='').pack()

                if len(profile_not_exist) > 0:
                    no_profile_text = 'The following generators or commodities have no profile: '

                    for u in profile_not_exist:
                        if profile_not_exist.index(u) != len(profile_not_exist) - 1:
                            no_profile_text += u + ', '
                        else:
                            no_profile_text += u

                    tk.Label(alert_window, text=no_profile_text).pack()
                    tk.Label(alert_window,
                             text='It is important that every generator/commodity has a profile. \n'
                                  ' Please adjust your generators/commodities').pack()
                    tk.Label(alert_window, text='').pack()

                ttk.Button(alert_window, text='OK', command=kill_window).pack(fill='both', expand=True)
            else:
                self.optimize_button.config(state=NORMAL)
        else:
            self.optimize_button.config(state=NORMAL)

    def save_setting_window(self):

        def kill_window_and_save():

            if name_entry.get() is None:
                # dd/mm/YY H:M:S
                now = datetime.now()
                dt_string = now.strftime("%d%m%Y_%H%M%S")

                path_name = self.path_projects + "/" + dt_string + ".yaml"
            else:
                path_name = self.path_projects + "/" + name_entry.get() + ".yaml"

                self.root.title(name_entry.get())
                self.pm_object_copy.set_project_name(name_entry.get())

            save_current_parameters_and_options(self.pm_object_copy, path_name)
            newWindow.destroy()

        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel(self.root)
        newWindow.grab_set()

        Label(newWindow, text='Enter name of settings file').grid(row=0, column=0, sticky='ew')

        name_entry = Entry(newWindow)
        name_entry.grid(row=0, column=1, sticky='ew')

        ttk.Button(newWindow, text='Save', command=kill_window_and_save).grid(row=1, column=0, sticky='ew')
        ttk.Button(newWindow, text='Cancel', command=kill_only).grid(row=1, column=1, sticky='ew')

        newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        newWindow.grid_columnconfigure(1, weight=1, uniform='a')

    def optimize_now(self):

        optimize(self.pm_object_copy, self.path_data, self.path_result, self.solver)

    def cancel(self):

        self.root.destroy()
        run_main()

    def __init__(self, path_data, path_result, path_projects, solver, path_optimize=None):

        self.path_data = path_data
        self.path_result = path_result
        self.path_projects = path_projects
        self.path_optimize = path_optimize
        self.working_path = os.getcwd()
        self.solver = solver

        self.root = Tk()
        try:
            ttk.Style().theme_use('vista')
        except:
            pass

        if self.path_optimize is None:  # New project

            self.pm_object_original = ParameterObject('parameter', integer_steps=10, path_data=path_data)
            self.pm_object_original.create_new_project()

            self.pm_object_copy = ParameterObject('parameter2', integer_steps=10, path_data=path_data)
            self.pm_object_copy.create_new_project()

            self.root.title('New Project')
            self.project_name = None

        else:  # Custom project

            custom_title = self.path_optimize.split('/')[-1].split('.')[0]
            self.root.title(custom_title)
            self.project_name = custom_title

            self.pm_object_original = ParameterObject(custom_title, integer_steps=10,
                                                      path_data=path_data)
            self.pm_object_copy = ParameterObject(custom_title, integer_steps=10,
                                                  path_data=path_data)

            path = self.path_projects + '/' + self.path_optimize
            if 'xlsx' in path:
                case_data = pd.read_excel(path, index_col=0)
            else:
                yaml_file = open(path)
                case_data = yaml.load(yaml_file, Loader=yaml.FullLoader)

            self.pm_object_original = load_project(self.pm_object_original, case_data)
            self.pm_object_copy = load_project(self.pm_object_copy, case_data)

        self.me_checked = False  # boolean if mass energy balance was checked

        self.general_parameters_df = pd.DataFrame()
        self.components_df = pd.DataFrame()
        self.commodities_df = pd.DataFrame()
        self.storages_df = pd.DataFrame()
        self.generators_df = pd.DataFrame()

        self.widgets()


run_main()
