import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

import pandas as pd

from gui_general_settings_and_assumptions import GeneralAssumptionsFrame
from gui_component import ComponentFrame, AddNewComponentWindow
from gui_commodities import CommodityFrame
from gui_storages import StorageFrame
from gui_generators import GeneratorFrame

from object_component import GenerationComponent, StorageComponent

import random

import os

from datetime import datetime

import yaml


class AssumptionsInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately
        self.parameter_frame.frame.destroy()
        self.parameter_frame = GeneralAssumptionsFrame(self, self.parent, self.general_assumptions_frame,
                                                       self.pm_object_copy)

    def set_general_assumptions_to_default(self):
        # Set general assumption parameters to default

        self.pm_object_copy.set_wacc(self.pm_object_original.get_wacc())

        if self.pm_object_original.get_uses_representative_periods():
            self.pm_object_copy.set_uses_representative_periods(True)
            representative_periods = self.pm_object_original.get_representative_periods_length()
            self.pm_object_copy.set_representative_periods_length(representative_periods)

        else:
            self.pm_object_copy.set_uses_representative_periods(False)
            covered_period = self.pm_object_original.get_covered_period()
            self.pm_object_copy.set_covered_period(covered_period)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.general_assumptions_frame = ttk.Frame(self)
        self.parameter_frame = GeneralAssumptionsFrame(self, self.parent,
                                                       self.general_assumptions_frame, self.pm_object_copy)
        self.general_assumptions_frame.pack(expand=True, fill='both')


class ComponentInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def show_disclaimer_no_conversion(self):
        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel()
        newWindow.title('')
        newWindow.grab_set()

        ttk.Label(newWindow, text='No Conversions in System. Without Conversions,').grid(row=0, column=0, sticky='ew')
        ttk.Label(newWindow, text='other Components and Commodities cannot be adjusted').grid(row=1, column=0, sticky='ew')

        ttk.Button(newWindow, text='OK', command=kill_only).grid(row=2, sticky='ew')

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        entries = []
        for c in self.pm_object_copy.get_final_conversion_components_objects():
            entries.append(c.get_name())
        self.components_combo.config(values=entries)

        if self.pm_object_copy.get_final_conversion_components_names():
            state = NORMAL
        else:
            state = DISABLED
            self.show_disclaimer_no_conversion()

        self.delete_components_button.config(state=state)

        if self.parameter_frame is not None:

            self.parameter_frame.frame.destroy()

            if self.component != '':
                if entries:
                    for c in self.pm_object_copy.get_final_conversion_components_objects():
                        if self.component == c.get_name():
                            component = self.pm_object_copy.get_component(self.component)
                            component_name = component.get_name()
                            self.components_combo.set(component_name)
                            self.parameter_frame = ComponentFrame(self, self.component_frame, self.component,
                                                                  self.pm_object_copy, self.pm_object_original)
                            self.parameter_frame.frame.grid(row=1, sticky='ew')
                            break
                        else:
                            self.components_combo.set('Choose component')
                else:
                    self.components_combo.set('Choose component')
            else:
                self.components_combo.set('Choose component')

    def callbackFuncDecideComponent(self, event=None):
        # Function of component combo box
        # Destroy old frame (if exist) and create new frame

        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        name = self.components_combo.get()
        self.component = name

        self.parameter_frame = ComponentFrame(self, self.component_frame, self.component,
                                              self.pm_object_copy, self.pm_object_original)
        self.parameter_frame.frame.grid(row=1, sticky='ew')

    def set_components_to_default(self):  # todo: Wenn commodity gelöscht wird aber als storage angewählt war, ist er immer noch final
        # Set all component parameters and commodities to default

        for component in self.pm_object_copy.get_conversion_components_objects():
            self.pm_object_copy.remove_component_entirely(component.get_name())

        for component in self.pm_object_original.get_conversion_components_objects():
            copied_component = component.__copy__()
            self.pm_object_copy.add_component(component.get_name(), copied_component)

        for commodity in self.pm_object_original.get_final_commodities_objects():
            if commodity not in self.pm_object_copy.get_final_commodities_objects():
                self.pm_object_copy.add_commodity(commodity.get_name(), commodity)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def create_new_component_window(self):
        # Adds dummy component which then can be adjusted
        AddNewComponentWindow(self.parent, self.pm_object_copy)

    def delete_components(self):
        # Deletes components based on choice

        def set_component(component, index):
            delete_component_dict[component] = var_list[index].get()

        def kill_only():
            delete_component_window.destroy()

        def delete_and_kill():

            for component in [*delete_component_dict]:
                if delete_component_dict[component]:

                    component.set_final(False)

                    # Set commodity to not final if commodity is not used anymore
                    dummy_commodity = None
                    for commodity in self.pm_object_copy.get_final_commodities_objects():
                        commodity_used_elsewhere = False
                        for other_component in self.pm_object_copy.get_final_conversion_components_objects():
                            if other_component != component:
                                if commodity.get_name() in [*other_component.get_inputs().keys()]:
                                    commodity_used_elsewhere = True
                                    dummy_commodity = commodity
                                    break
                                if commodity.get_name() in [*other_component.get_outputs().keys()]:
                                    commodity_used_elsewhere = True
                                    dummy_commodity = commodity
                                    break

                        if not commodity_used_elsewhere:
                            self.pm_object_copy.remove_commodity(commodity.get_name())

                            # Check if commodity storage exists and remove if so
                            for storage in self.pm_object_copy.get_final_storage_components_objects():
                                if storage.get_name() == commodity.get_name():
                                    storage.set_final(False)

                            # Check if generator produces this commodity and change to null
                            for generator in self.pm_object_copy.get_generator_components_objects():
                                if generator.get_generated_commodity() == commodity.get_name():

                                    if dummy_commodity is not None:
                                        generator.set_generated_commodity(dummy_commodity.get_name())
                                        generator.set_final(False)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            delete_component_window.destroy()

        delete_component_window = Toplevel()
        delete_component_window.grab_set()

        delete_component_dict = {}

        var_list = []
        i = 0

        for c in self.pm_object_copy.get_final_conversion_components_objects():
            delete_component_dict.update({c: False})
            var_list.append(tk.IntVar())
            tk.Checkbutton(delete_component_window, text=c.get_name(),
                           variable=var_list[i], onvalue=1, offvalue=0,
                           command=lambda c=c, i=i: set_component(c, i)).grid(row=i, column=0, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_component_window, text='Delete components', command=delete_and_kill).grid(row=i + 1,
                                                                                                    column=0,
                                                                                                    sticky='we')
        ttk.Button(delete_component_window, text='Cancel', command=kill_only).grid(row=i + 1, column=1, sticky='we')

        delete_component_window.grid_columnconfigure(0, weight=1, uniform='a')
        delete_component_window.grid_columnconfigure(1, weight=1, uniform='a')

        delete_component_window.mainloop()

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.component = ''

        self.component_frame = ttk.Frame(self)
        widget_frame = ttk.Frame(self.component_frame)
        self.parameter_frame = None

        button_frame = ttk.Frame(widget_frame)

        ttk.Button(button_frame, text='Add component', command=self.create_new_component_window)\
            .grid(row=0, column=0, sticky='ew')

        if self.pm_object_copy.get_final_conversion_components_names():
            state = NORMAL
        else:
            state = DISABLED

        self.delete_components_button = ttk.Button(button_frame, text='Delete components',
                                                   command=self.delete_components, state=state)
        self.delete_components_button.grid(row=0, column=1, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        button_frame.grid(row=0, sticky='ew')

        entries = []
        for c in self.pm_object_copy.get_final_conversion_components_objects():
            entries.append(c.get_name())

        self.components_combo = ttk.Combobox(widget_frame, values=entries, state='readonly')
        self.components_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideComponent)
        self.components_combo.set('Choose component')
        self.components_combo.delete(0, 'end')

        self.components_combo.grid(row=1, sticky='ew')

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')

        self.component_frame.grid_columnconfigure(0, weight=1)
        self.component_frame.pack(fill="both", expand=True)


class CommodityInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        unused_commodities = self.pm_object_copy.get_not_used_commodities_names()
        if unused_commodities:
            self.delete_commodity_button.config(state=NORMAL)
        else:
            self.delete_commodity_button.config(state=DISABLED)

        self.names = []
        for commodity in self.pm_object_copy.get_final_commodities_objects():
            self.names.append(commodity.get_name())
        self.combobox_commodity.config(values=self.names)

        if self.combobox_commodity.get() != 'Choose commodity':

            name = self.combobox_commodity.get()
            self.commodity = name

            if name not in self.names:
                self.commodity = ''
                self.combobox_commodity.set('Choose commodity')

            if self.parameter_frame is not None:
                self.parameter_frame.frame.destroy()

            if self.combobox_commodity.get() != 'Choose commodity':

                self.parameter_frame = CommodityFrame(self, self.commodity_frame, self.commodity, self.pm_object_copy,
                                                   self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew')

    def callbackFuncDecideCommodity(self, event=None):
        # Function of commodity combo box
        # Destroy old frame (if exist) and create new frame

        name = self.combobox_commodity.get()
        self.commodity = name

        if name not in self.names:
            self.commodity = ''
            self.combobox_commodity.set('Choose commodity')

        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        if self.combobox_commodity.get() != 'Choose commodity':
            self.parameter_frame = CommodityFrame(self, self.commodity_frame, self.commodity, self.pm_object_copy,
                                               self.pm_object_original)
            self.parameter_frame.frame.grid(row=1, sticky='ew')

    def delete_unused_commodities(self):

        def delete_chosen_commodities():
            for s in [*check_commodity.keys()]:
                if check_commodity[s].get():
                    self.pm_object_copy.remove_commodity_entirely(s)
            delete_commodities.destroy()

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

        def kill_only():
            delete_commodities.destroy()

        delete_commodities = Toplevel()
        delete_commodities.title('')
        delete_commodities.grab_set()

        unused_commodities = self.pm_object_copy.get_not_used_commodities_names()
        i = 0
        check_commodity = {}
        for commodity in unused_commodities:
            check_commodity[commodity] = BooleanVar()
            ttk.Checkbutton(delete_commodities, text=commodity, variable=check_commodity[commodity])\
                .grid(row=i, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_commodities, text='Delete', command=delete_chosen_commodities).grid(row=i, column=0, sticky='ew')
        ttk.Button(delete_commodities, text='Cancel', command=kill_only).grid(row=i, column=1, sticky='ew')

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.commodity = ''

        self.commodity_frame = ttk.Frame(self)
        widget_frame = ttk.Frame(self.commodity_frame)
        self.parameter_frame = None

        unused_commodities = self.pm_object_copy.get_not_used_commodities_names()
        if unused_commodities:
            self.delete_commodity_button = ttk.Button(widget_frame, text='Delete unused commodities',
                                                   command=self.delete_unused_commodities)
        else:
            self.delete_commodity_button = ttk.Button(widget_frame, text='Delete unused commodities',
                                                   command=self.delete_unused_commodities, state=DISABLED)
        self.delete_commodity_button.grid(row=0, sticky='ew')

        self.names = []
        for commodity in self.pm_object_copy.get_final_commodities_objects():
            self.names.append(commodity.get_name())

        self.combobox_commodity = ttk.Combobox(widget_frame, values=self.names, state='readonly')
        self.combobox_commodity.grid(row=1, sticky='ew')
        self.combobox_commodity.bind("<<ComboboxSelected>>", self.callbackFuncDecideCommodity)
        self.combobox_commodity.set('Choose commodity')

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')

        self.commodity_frame.grid_columnconfigure(0, weight=1)
        self.commodity_frame.pack(expand=True, fill='both')


class StorageInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        # Add dummy storages for not yet existing storages
        self.storages_names = []
        for s in self.pm_object_copy.get_final_commodities_names():
            self.storages_names.append(s)
            if s not in self.pm_object_copy.get_storage_components_names():
                storage = StorageComponent(s, final_unit=False, custom_unit=True)
                self.pm_object_copy.add_component(s, storage)

        self.combobox_storage.config(values=self.storages_names)

        # Check if commodity still in system and set combobox to commodity or to "choose storage"
        if self.parameter_frame is not None:

            self.parameter_frame.frame.destroy()

            if self.storage in self.storages_names:

                self.combobox_storage.set(self.storage)

                self.parameter_frame = StorageFrame(self, self.storage_frame, self.storage,
                                      self.pm_object_copy, self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew')

            else:
                self.combobox_storage.set('Choose Storage')

    def callbackFuncStorage(self, event=None):
        # Function of storage combo box
        # Destroy old frame (if exist) and create new frame
        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        self.storage = self.combobox_storage.get()

        self.parameter_frame = StorageFrame(self, self.storage_frame, self.storage,
                                          self.pm_object_copy, self.pm_object_original)
        self.parameter_frame.frame.grid(row=1, sticky='ew')

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.storage = ''

        self.storage_frame = ttk.Frame(self)
        widget_frame = ttk.Frame(self.storage_frame)
        self.parameter_frame = None

        # Add storages to collection of existing storages
        self.storages_names = []
        for s in self.pm_object_copy.get_final_commodities_names():
            self.storages_names.append(s)
            if s not in self.pm_object_copy.get_storage_components_names():
                storage = StorageComponent(s, final_unit=False, custom_unit=True)
                self.pm_object_copy.add_component(s, storage)

        self.combobox_storage = ttk.Combobox(widget_frame, values=self.storages_names, state='readonly')
        self.combobox_storage.grid(sticky='ew')
        self.combobox_storage.set('Choose storage')
        self.combobox_storage.bind("<<ComboboxSelected>>", self.callbackFuncStorage)

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')

        self.storage_frame.grid_columnconfigure(0, weight=1)
        self.storage_frame.pack(fill='both', expand=True)


class GeneratorInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def callbackFuncDecideGenerator(self, event=None):
        # Function of generator combo box
        # Destroy old frame (if exist) and create new frame

        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        self.generator = self.components_generator_combo.get()

        self.parameter_frame = GeneratorFrame(self, self.generator_frame, self.generator,
                                              self.pm_object_copy, self.pm_object_original)
        self.parameter_frame.frame.grid(row=1, sticky='ew')  # pack(fill="both", expand=True)

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        # Update combobox with new values
        generators = []
        for generator in self.pm_object_copy.get_generator_components_objects():
            generators.append(generator.get_name())
        self.components_generator_combo.config(values=generators)

        # Check if commodity exists which can be generated
        if self.pm_object_copy.get_final_commodities_names():
            state = NORMAL
        else:
            state = DISABLED
        self.add_generator_button.config(state=state)

        # Enable / Disable delete generator button
        if len(generators) == 0:
            self.delete_generator_button.config(state=DISABLED)
        else:
            self.delete_generator_button.config(state=NORMAL)

        # Delete parameter frame
        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        if self.generator == '':  # Case no generator was chosen
            self.components_generator_combo.set('Choose generator')
        else:
            if self.generator not in generators:
                self.components_generator_combo.set('Choose generator')
            else:  # create new parameter frame if generator was chosen and exists
                self.parameter_frame = GeneratorFrame(self, self.generator_frame, self.generator,
                                                      self.pm_object_copy, self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew')  # pack(fill='both', expand=True)

    def add_generator(self):
        # Adds dummy generator, which then can be adjusted

        def get_generator_and_kill():
            name = name_entry.get()

            generator = GenerationComponent(name, final_unit=True, custom_unit=True)
            generator.set_generated_commodity(random.choice(self.pm_object_copy.get_final_commodities_names()))
            self.pm_object_copy.add_component(name, generator)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            newWindow.destroy()

        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel()
        newWindow.title('Add Generator')
        newWindow.grab_set()

        ttk.Label(newWindow, text='Name').grid(row=0, column=0, sticky='ew')
        name_entry = ttk.Entry(newWindow)
        name_entry.grid(row=0, column=1, sticky='ew')

        newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        newWindow.grid_columnconfigure(1, weight=1, uniform='a')

        button_frame = ttk.Frame(newWindow)

        ttk.Button(button_frame, text='OK', command=get_generator_and_kill).grid(row=0, column=0, sticky='ew')
        ttk.Button(button_frame, text='Cancel', command=kill_only).grid(row=0, column=1, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')
        button_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

    def delete_generator(self):

        def delete_checked_generators():
            for g in generators:
                if checked_generators[g].get():
                    self.pm_object_copy.remove_component_entirely(g)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            delete_generators_window.destroy()

        def kill_delete_generators():

            delete_generators_window.destroy()

        delete_generators_window = Toplevel()
        delete_generators_window.grab_set()
        delete_generators_window.title('Delete Generators')

        generators = []
        for gen in self.pm_object_copy.get_generator_components_objects():
            generators.append(gen.get_name())

        checked_generators = {}
        i = 0
        for gen in generators:
            checked_generators[gen] = BooleanVar()
            ttk.Checkbutton(delete_generators_window, text=gen,
                            variable=checked_generators[gen]).grid(row=i, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_generators_window, text='Delete', command=delete_checked_generators).grid(row=i, column=0)
        ttk.Button(delete_generators_window, text='Cancel', command=kill_delete_generators).grid(row=i, column=1)

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.generator = ''

        self.generator_frame = ttk.Frame(self)

        # Button frame contains button to add and delete generators
        widget_frame = ttk.Frame(self.generator_frame)
        self.parameter_frame = None

        if self.pm_object_copy.get_final_commodities_names():
            state = NORMAL
        else:
            state = DISABLED

        self.add_generator_button = ttk.Button(widget_frame, text='Add Generator', command=self.add_generator,
                                               state=state)
        self.add_generator_button.grid(row=0, column=0, sticky='ew')

        self.delete_generator_button = ttk.Button(widget_frame, text='Delete Generator',
                                                  command=self.delete_generator)
        self.delete_generator_button.grid(row=0, column=1, sticky='ew')

        # Create Combobox, which contains all generators and can be selected
        generators = []
        for generator in self.pm_object_copy.get_generator_components_objects():
            generators.append(generator.get_name())

        if len(generators) == 0:
            self.delete_generator_button.config(state=DISABLED)
        else:
            self.delete_generator_button.config(state=NORMAL)

        self.components_generator_combo = ttk.Combobox(widget_frame, values=generators, state='readonly')
        self.components_generator_combo.grid(row=1, columnspan=2, sticky='ew')
        self.components_generator_combo.set('Choose generator')
        self.components_generator_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideGenerator)

        widget_frame.grid_columnconfigure(0, weight=1, uniform='a')
        widget_frame.grid_columnconfigure(1, weight=1, uniform='a')
        widget_frame.grid(row=0, sticky='ew')  # pack(fill='both', expand=True)

        self.generator_frame.grid_columnconfigure(0, weight=1)
        self.generator_frame.pack(fill='both', expand=True)


class DataInterface(ttk.Frame):

    def set_single_or_multiple_profiles(self):
        if self.single_or_multiple_profiles_var.get() == 'single':
            self.pm_object_copy.set_single_or_multiple_profiles('single')
        else:
            self.pm_object_copy.set_single_or_multiple_profiles('multiple')

    def set_data_path(self):
        if self.single_or_multiple_profiles_var.get() == 'single':
            path = filedialog.askopenfilename()
            file_name = path.split('/')[-1]

            if file_name != '':
                if (file_name.split('.')[-1] == 'xlsx') or (file_name.split('.')[-1] == 'csv'):
                    self.pm_object_copy.set_profile_data(file_name)
                    self.pm_object_copy.set_single_or_multiple_profiles('single')

                    self.parent.pm_object_copy = self.pm_object_copy
                    self.parent.update_widgets()

                else:
                    wrong_file_window = Toplevel()
                    wrong_file_window.title('')
                    wrong_file_window.grab_set()

                    ttk.Label(wrong_file_window, text='File is not xlsx/csv format').pack(fill='both', expand=True)

                    ttk.Button(wrong_file_window, text='OK', command=wrong_file_window.destroy).pack(fill='both',
                                                                                                     expand=True)
        else:
            path = filedialog.askdirectory()
            folder_name = path.split('/')[-1]

            self.pm_object_copy.set_profile_data(folder_name)
            self.pm_object_copy.set_single_or_multiple_profiles('multiple')

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

    def create_data_template(self):

        if self.pm_object_copy.get_project_name() is None:
            project_name = ''
        else:
            project_name = self.pm_object_copy.get_project_name()

        columns = []
        for g in self.pm_object_copy.get_final_generator_components_objects():
            columns.append((g.get_name()))

        for s in self.pm_object_copy.get_all_commodities():
            commodity_object = self.pm_object_copy.get_commodity(s)
            if commodity_object.is_purchasable():
                if commodity_object.get_purchase_price_type() == 'variable':
                    columns.append(commodity_object.get_name() + '_Purchase_Price')
            if commodity_object.is_saleable():
                if commodity_object.get_sale_price_type() == 'variable':
                    columns.append(commodity_object.get_name() + '_Selling_Price')
            if commodity_object.is_demanded():
                if commodity_object.get_demand_type() == 'variable':
                    columns.append(commodity_object.get_name() + '_Demand')

        if self.pm_object_copy.get_uses_representative_periods():
            columns.append('Weighting')

        if self.pm_object_copy.get_uses_representative_periods():
            covered_period = len(pd.read_excel(self.pm_object_copy.get_path_data() + self.pm_object_copy.get_profile_data(),
                                             index_col=0).index)
        else:
            covered_period = self.pm_object_copy.get_covered_period()

        now = datetime.now()
        dt_string = now.strftime("%d%m%Y_%H%M%S")

        path = self.pm_object_copy.get_path_data() + dt_string + '_' + project_name + '_profile_data.xlsx'
        pd.DataFrame(index=[i for i in range(int(covered_period))], columns=columns).to_excel(path)

        os.system('start excel.exe "%s"' % (path,))

        self.pm_object_copy.set_profile_data(dt_string + '_' + project_name + '_profile_data.xlsx')
        self.pm_object_copy.set_single_or_multiple_profiles('single')

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        if self.data_frame is not None:
            self.data_frame.destroy()
        self.data_frame = ttk.Frame(self)

        if (len(self.pm_object_copy.get_final_generator_components_names()) > 0) \
                | self.pm_object_copy.get_commodity_data_needed() \
                | self.pm_object_copy.get_uses_representative_periods():

            profiles_data_frame = ttk.Frame(self.data_frame)

            self.single_or_multiple_profiles_var = StringVar()
            if self.pm_object_copy.get_single_or_multiple_profiles() == 'single':
                self.single_or_multiple_profiles_var.set('single')
            else:
                self.single_or_multiple_profiles_var.set('multiple')

            self.rb_single = ttk.Radiobutton(profiles_data_frame, text='Use single profile', value='single',
                                             variable=self.single_or_multiple_profiles_var,
                                             command=self.set_single_or_multiple_profiles)
            self.rb_single.grid(row=1, column=0, sticky='ew')

            self.rb_several = ttk.Radiobutton(profiles_data_frame, text='Use multiple profiles', value='multiple',
                                              variable=self.single_or_multiple_profiles_var,
                                              command=self.set_single_or_multiple_profiles)
            self.rb_several.grid(row=1, column=1, sticky='ew')

            self.data_textvar = StringVar()
            try:
                path_data = self.pm_object_copy.get_profile_data()
                file_name_generation = path_data.split('/')[-1]
                self.data_textvar.set(file_name_generation)
            except:
                self.data_textvar.set('')

            ttk.Label(profiles_data_frame, text='File/Folder').grid(row=2, column=0, sticky='w')
            ttk.Label(profiles_data_frame, text=self.data_textvar.get()).grid(row=2, column=1, sticky='ew')

            ttk.Button(profiles_data_frame, text='Select profile(s)', command=self.set_data_path).grid(row=3,
                                                                                                       column=0,
                                                                                                       sticky='ew')

            ttk.Button(profiles_data_frame, text='Create new data template',
                       command=self.create_data_template).grid(row=3, column=1, sticky='ew')

            profiles_data_frame.grid_columnconfigure(0, weight=1, uniform='a')
            profiles_data_frame.grid_columnconfigure(1, weight=1, uniform='a')
            profiles_data_frame.grid(row=0, sticky='ew')

        self.data_frame.grid_columnconfigure(0, weight=1)
        self.data_frame.pack(fill='both', expand=True)

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains data

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.data_frame = ttk.Frame(self)

        self.update_frame()


class SettingWindow:

    def getFolderData(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_data = folder_path
            self.choose_data_folder_var.set(folder_path.split('/')[-2])

    def getFolderResult(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_result = folder_path
            self.choose_result_folder_var.set(folder_path.split('/')[-2])

    def getFolderProjects(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_projects = folder_path
            self.choose_projects_folder_var.set(folder_path.split('/')[-2])

    def getFolderPathOptimize(self):

        if self.optimize_variable.get() == 'custom':
            folder_path = filedialog.askopenfilename()
            if folder_path != '/':
                self.path_optimize = folder_path.split('/')[-1]
                self.choose_optimization_var.set(self.path_optimize)
        else:
            folder_path = filedialog.askdirectory() + '/'
            if folder_path != '/':
                self.path_optimize = folder_path.split('/')[-2]
                self.choose_optimization_var.set(self.path_optimize)

        self.radiobutton_optimization_or_visualization_command()

    def getFolderPathResultVisualization(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_visualization = folder_path.split('/')[-2]
            self.choose_visualize_folder_var.set(self.path_visualization)

            self.radiobutton_optimization_or_visualization_command()

    def radiobutton_optimization_or_visualization_command(self):

        self.optimize_or_visualize_frame.destroy()
        self.optimize_or_visualize_frame = self.create_optimization_or_visualization_frame()
        self.optimize_or_visualize_frame.grid(row=1, columnspan=2, sticky='ew')

    def create_optimization_or_visualization_frame(self):
        frame = ttk.Frame(self.frame)

        if self.optimize_or_visualize_projects_variable.get() == 'optimize':

            def radiobutton_optimize_command():
                if self.optimize_variable.get() == 'new':
                    profile_button.config(state=DISABLED)
                    profile_label.config(state=DISABLED)
                else:
                    profile_button.config(state=NORMAL)
                    profile_label.config(state=NORMAL)

            frame.grid_columnconfigure(0, weight=1, uniform='a')
            frame.grid_columnconfigure(1, weight=1, uniform='a')

            ttk.Radiobutton(frame, text='New Project', variable=self.optimize_variable,
                            value='new', command=radiobutton_optimize_command).grid(row=2, columnspan=2)

            ttk.Radiobutton(frame, text='Load existing Project', variable=self.optimize_variable,
                            value='custom', command=radiobutton_optimize_command).grid(row=3, column=0, sticky='ew')

            ttk.Radiobutton(frame, text='Optimize ready Projects', variable=self.optimize_variable,
                            value='optimize_only', command=radiobutton_optimize_command).grid(row=3, column=1,
                                                                                             sticky='ew')

            profile_button = ttk.Button(frame, text='Select Project(s)', command=self.getFolderPathOptimize)
            profile_button.grid(row=4, column=0, sticky='ew')
            profile_label = ttk.Label(frame, textvariable=self.choose_optimization_var)
            profile_label.grid(row=4, column=1, columnspan=2, sticky='w')

            ttk.Label(frame, text='Solver').grid(row=5, column=0, sticky='w')
            solvers = ['gurobi', 'cplex', 'glpk', 'cbc']
            self.solver_combobox = ttk.Combobox(frame, values=solvers, state='readonly')
            self.solver_combobox.set(self.choose_solver_var.get())
            self.solver_combobox.grid(row=5, column=1, sticky='ew')

            radiobutton_optimize_command()

        else:

            frame.grid_columnconfigure(0, weight=1, uniform='a')
            frame.grid_columnconfigure(1, weight=1, uniform='a')

            visualize_only_path_button = ttk.Button(frame, text='Select Result(s) for Visualization',
                                                    command=self.getFolderPathResultVisualization)
            visualize_only_path_button.grid(row=1, column=0, sticky='ew')
            visualize_only_path_label = ttk.Label(frame, textvariable=self.choose_visualize_folder_var)
            visualize_only_path_label.grid(row=1, column=1, sticky='w')

        return frame

    def kill_window(self):

        def check_empty(path):
            empty = False

            if type(path) != str:
                empty = True
            elif path == '':
                empty = True
            elif path == '/':
                empty = True

            return empty

        def kill_no_paths_window():
            window_no_paths.destroy()

        if (check_empty(self.path_data)) | (check_empty(self.path_result)) | (check_empty(self.path_projects)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths,
                      text='Please choose data folder, result folder and location for saved projects').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        elif ((self.optimize_variable.get() == 'custom') | (self.optimize_variable.get() == 'optimize_only')) & (check_empty(self.path_optimize)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths, text='Please choose Optimization Project(s)').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        elif (self.optimize_or_visualize_projects_variable.get() == 'visualize') & (check_empty(self.path_visualization)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths, text='Please choose result folder').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        else:

            config = {'path_data': self.path_data,
                      'path_result': self.path_result,
                      'path_projects': self.path_projects,
                      'optimization_or_visualization': self.optimize_or_visualize_projects_variable.get()}

            if self.optimize_or_visualize_projects_variable.get() == 'optimize':
                config['chosen_optimization_setting'] = self.optimize_variable.get()
                config['path_optimize'] = self.path_optimize
                config['solver'] = self.solver_combobox.get()
                config['path_visualization'] = self.path_visualization

                self.solver = self.solver_combobox.get()

            else:
                config['chosen_optimization_setting'] = self.config_yaml.get("chosen_optimization_setting")
                config['path_optimize'] = self.path_optimize
                config['solver'] = self.solver
                config['path_visualization'] = self.path_visualization

            file = open(self.path_config, "w")

            yaml.dump(config, file)

            file.close()

            self.go_on = True
            self.window.destroy()

    def kill_window_without(self):
        self.go_on = False
        self.window.destroy()

    def __init__(self):

        self.window = Tk()
        self.window.title('')
        self.frame = Frame(self.window)
        self.frame.pack()
        self.go_on = False

        self.path_config = os.getcwd() + '/config.yaml'
        yaml_file = open(self.path_config)
        self.config_yaml = yaml.load(yaml_file, Loader=yaml.FullLoader)

        self.path_data = self.config_yaml.get("path_data")
        self.path_result = self.config_yaml.get("path_result")
        self.path_projects = self.config_yaml.get("path_projects")
        self.path_optimize = self.config_yaml.get("path_optimize")
        self.solver = self.config_yaml.get("solver")
        self.path_visualization = self.config_yaml.get("path_visualization")

        self.optimize_or_visualize_projects_variable = StringVar()
        self.optimize_or_visualize_projects_variable.set(self.config_yaml.get("optimization_or_visualization"))

        self.optimize_variable = StringVar()
        self.optimize_variable.set(self.config_yaml.get("chosen_optimization_setting"))

        self.choose_data_folder_var = StringVar()
        self.choose_result_folder_var = StringVar()
        self.choose_projects_folder_var = StringVar()
        self.choose_optimization_var = StringVar()
        self.choose_solver_var = StringVar()
        self.choose_visualize_folder_var = StringVar()

        if type(self.path_result) == str:

            self.choose_data_folder_var.set(self.path_data.split('/')[-2])

            self.choose_result_folder_var.set(self.path_result.split('/')[-2])

            self.choose_projects_folder_var.set(self.path_projects.split('/')[-2])

            self.choose_optimization_var.set(self.path_optimize)

            self.choose_solver_var.set(self.solver)

            self.choose_visualize_folder_var.set(self.path_visualization)

        else:
            self.choose_data_folder_var.set('')
            self.choose_result_folder_var.set('')
            self.choose_projects_folder_var.set('')
            self.choose_optimization_var.set('')
            self.choose_solver_var.set('')
            self.choose_visualize_folder_var.set('')

        base_setting_frame = ttk.Frame(self.frame)
        base_setting_frame.grid_columnconfigure(0, weight=1, uniform='a')
        base_setting_frame.grid_columnconfigure(1, weight=1, uniform='a')

        ttk.Label(base_setting_frame, text='Folder Structure').grid(row=0, columnspan=2, sticky='w')

        self.choose_data_folder_button = ttk.Button(base_setting_frame, text='Select Data Folder',
                                                    command=self.getFolderData)
        self.choose_data_folder_button.grid(row=1, column=0, sticky='ew')

        self.choose_data_folder_label = tk.Label(base_setting_frame, textvariable=self.choose_data_folder_var)
        self.choose_data_folder_label.grid(row=1, column=1, sticky='w')

        self.choose_result_folder_button = ttk.Button(base_setting_frame, text='Select Result Folder',
                                                      command=self.getFolderResult)
        self.choose_result_folder_button.grid(row=2, column=0, sticky='ew')

        self.choose_result_folder_label = tk.Label(base_setting_frame, textvariable=self.choose_result_folder_var)
        self.choose_result_folder_label.grid(row=2, column=1, sticky='w')

        self.choose_projects_folder_button = ttk.Button(base_setting_frame, text='Select Project Folder',
                                                        command=self.getFolderProjects)
        self.choose_projects_folder_button.grid(row=3, column=0, sticky='ew')

        self.choose_projects_folder_label = tk.Label(base_setting_frame, textvariable=self.choose_projects_folder_var)
        self.choose_projects_folder_label.grid(row=3, column=1, sticky='w')

        ttk.Separator(base_setting_frame).grid(row=4, columnspan=2, sticky='ew')

        ttk.Label(base_setting_frame, text='Choose Application').grid(row=5, columnspan=2, sticky='w')

        ttk.Radiobutton(base_setting_frame, text='Create and Optimize Projects',
                        variable=self.optimize_or_visualize_projects_variable, value='optimize',
                        command=self.radiobutton_optimization_or_visualization_command).grid(row=6, column=0,
                                                                                             sticky='ew')

        ttk.Radiobutton(base_setting_frame, text='Visualize Projects',
                        variable=self.optimize_or_visualize_projects_variable, value='visualize',
                        command=self.radiobutton_optimization_or_visualization_command).grid(row=6, column=1,
                                                                                             sticky='ew')

        ttk.Separator(base_setting_frame).grid(row=7, columnspan=2, sticky='ew')

        base_setting_frame.grid(row=0, columnspan=2, sticky='ew')

        self.optimize_or_visualize_frame = self.create_optimization_or_visualization_frame()
        self.optimize_or_visualize_frame.grid(row=1, columnspan=2, sticky='ew')

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        self.button_ok = ttk.Button(button_frame, text='Ok', command=self.kill_window)
        self.button_ok.grid(row=0, column=0, sticky='ew')
        self.button_ok = ttk.Button(button_frame, text='Cancel', command=self.kill_window_without)
        self.button_ok.grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=4, columnspan=2, sticky='ew')

        self.window.mainloop()


def save_current_parameters_and_options(pm_object, path_name, fixed_capacities=None):

    case_data = {}
    case_data['version'] = '0.1.1'
    case_data['project_name'] = pm_object.get_project_name()
    case_data['optimization_type'] = pm_object.get_optimization_type()

    case_data['wacc'] = pm_object.get_wacc()

    case_data['representative_periods'] = {}
    case_data['representative_periods']['uses_representative_periods'] = pm_object.get_uses_representative_periods()
    case_data['representative_periods']['covered_period'] = pm_object.get_covered_period()

    case_data['monetary_unit'] = pm_object.get_monetary_unit()

    case_data['data'] = {}
    case_data['data']['single_or_multiple_profiles'] = pm_object.get_single_or_multiple_profiles()
    case_data['data']['profile_data'] = pm_object.get_profile_data()

    case_data['component'] = {}

    for component in pm_object.get_all_components():

        if not component.is_final():
            continue

        case_data['component'][component.get_name()] = {}

        case_data['component'][component.get_name()]['component_type'] = component.get_component_type()
        case_data['component'][component.get_name()]['final'] = component.is_final()
        case_data['component'][component.get_name()]['name'] = component.get_name()
        case_data['component'][component.get_name()]['capex'] = component.get_capex()
        case_data['component'][component.get_name()]['lifetime'] = component.get_lifetime()
        case_data['component'][component.get_name()]['fixed_om'] = component.get_fixed_OM()
        case_data['component'][component.get_name()]['variable_om'] = component.get_variable_OM()
        case_data['component'][component.get_name()]['has_fixed_capacity'] = component.get_has_fixed_capacity()

        if fixed_capacities is not None:
            case_data['component'][component.get_name()]['fixed_capacity'] = fixed_capacities[component.get_name()]
        else:
            case_data['component'][component.get_name()]['fixed_capacity'] = component.get_fixed_capacity()

        case_data['component'][component.get_name()]['installation_co2_emissions'] = component.get_installation_co2_emissions()
        case_data['component'][component.get_name()]['fixed_co2_emissions'] = component.get_fixed_co2_emissions()
        case_data['component'][component.get_name()]['variable_co2_emissions'] = component.get_variable_co2_emissions()
        case_data['component'][component.get_name()]['disposal_co2_emissions'] = component.get_disposal_co2_emissions()

        if component.get_component_type() == 'conversion':

            case_data['component'][component.get_name()]['capex_basis'] = component.get_capex_basis()
            case_data['component'][component.get_name()]['scalable'] = component.is_scalable()
            case_data['component'][component.get_name()]['base_investment'] = component.get_base_investment()
            case_data['component'][component.get_name()]['base_capacity'] = component.get_base_capacity()
            case_data['component'][component.get_name()]['economies_of_scale'] = component.get_economies_of_scale()
            case_data['component'][component.get_name()]['max_capacity_economies_of_scale'] = component.get_max_capacity_economies_of_scale()

            case_data['component'][component.get_name()]['min_p'] = component.get_min_p()
            case_data['component'][component.get_name()]['max_p'] = component.get_max_p()

            case_data['component'][component.get_name()]['ramp_up'] = component.get_ramp_up()
            case_data['component'][component.get_name()]['ramp_down'] = component.get_ramp_down()

            case_data['component'][component.get_name()]['shut_down_ability'] = component.get_shut_down_ability()
            if component.get_shut_down_ability():
                case_data['component'][component.get_name()]['start_up_time'] = component.get_start_up_time()
                case_data['component'][component.get_name()]['start_up_costs'] = component.get_start_up_costs()
            else:
                case_data['component'][component.get_name()]['start_up_time'] = 0
                case_data['component'][component.get_name()]['start_up_costs'] = 0

            case_data['component'][component.get_name()]['hot_standby_ability'] = component.get_hot_standby_ability()
            if component.get_hot_standby_ability():
                case_data['component'][component.get_name()]['hot_standby_commodity'] = [*component.get_hot_standby_demand().keys()][0]
                case_data['component'][component.get_name()]['hot_standby_demand'] = component.get_hot_standby_demand()[
                    [*component.get_hot_standby_demand().keys()][0]]
                case_data['component'][component.get_name()]['hot_standby_startup_time'] = component.get_hot_standby_startup_time()
            else:
                case_data['component'][component.get_name()]['hot_standby_commodity'] = ''
                case_data['component'][component.get_name()]['hot_standby_demand'] = 0
                case_data['component'][component.get_name()]['hot_standby_startup_time'] = 0

            case_data['component'][component.get_name()]['number_parallel_units'] = component.get_number_parallel_units()

        elif component.get_component_type() == 'generator':

            case_data['component'][component.get_name()]['generated_commodity'] = component.get_generated_commodity()
            case_data['component'][component.get_name()]['curtailment_possible'] = component.get_curtailment_possible()
            case_data['component'][component.get_name()]['uses_ppa'] = component.get_uses_ppa()
            case_data['component'][component.get_name()]['ppa_price'] = component.get_ppa_price()

        elif component.get_component_type() == 'storage':

            case_data['component'][component.get_name()]['min_soc'] = component.get_min_soc()
            case_data['component'][component.get_name()]['max_soc'] = component.get_max_soc()
            case_data['component'][component.get_name()]['charging_efficiency'] = component.get_charging_efficiency()
            case_data['component'][component.get_name()]['discharging_efficiency'] = component.get_discharging_efficiency()
            case_data['component'][component.get_name()]['ratio_capacity_p'] = component.get_ratio_capacity_p()

    case_data['conversions'] = {}
    for component in pm_object.get_final_conversion_components_objects():

        case_data['conversions'][component.get_name()] = {}
        case_data['conversions'][component.get_name()]['input'] = {}
        case_data['conversions'][component.get_name()]['output'] = {}

        inputs = component.get_inputs()
        inputs_dict = {}
        for i in [*inputs.keys()]:

            inputs_dict[i] = inputs[i]

            if i == component.get_main_input():
                case_data['conversions'][component.get_name()]['main_input'] = i

        case_data['conversions'][component.get_name()]['input'] = inputs_dict

        outputs = component.get_outputs()
        outputs_dict = {}
        for o in [*outputs.keys()]:

            outputs_dict[o] = outputs[o]

            if o == component.get_main_output():
                case_data['conversions'][component.get_name()]['main_output'] = o

        case_data['conversions'][component.get_name()]['output'] = outputs_dict

    case_data['commodity'] = {}
    for commodity in pm_object.get_final_commodities_objects():
        case_data['commodity'][commodity.get_name()] = {}

        case_data['commodity'][commodity.get_name()]['name'] = commodity.get_name()
        case_data['commodity'][commodity.get_name()]['unit'] = commodity.get_unit()

        case_data['commodity'][commodity.get_name()]['available'] = commodity.is_available()
        case_data['commodity'][commodity.get_name()]['emitted'] = commodity.is_emittable()
        case_data['commodity'][commodity.get_name()]['purchasable'] = commodity.is_purchasable()
        case_data['commodity'][commodity.get_name()]['saleable'] = commodity.is_saleable()
        case_data['commodity'][commodity.get_name()]['demanded'] = commodity.is_demanded()
        case_data['commodity'][commodity.get_name()]['total_demand'] = commodity.is_total_demand()
        case_data['commodity'][commodity.get_name()]['final'] = commodity.is_final()

        # Purchasable commodities
        case_data['commodity'][commodity.get_name()]['purchase_price_type'] = commodity.get_purchase_price_type()
        case_data['commodity'][commodity.get_name()]['purchase_price'] = commodity.get_purchase_price()

        # Saleable commodities
        case_data['commodity'][commodity.get_name()]['selling_price_type'] = commodity.get_sale_price_type()
        case_data['commodity'][commodity.get_name()]['selling_price'] = commodity.get_sale_price()

        # Demand
        case_data['commodity'][commodity.get_name()]['demand'] = commodity.get_demand()
        case_data['commodity'][commodity.get_name()]['demand_type'] = commodity.get_demand_type()

        case_data['commodity'][commodity.get_name()]['energy_content'] = commodity.get_energy_content()

        # Specific CO2 emissions
        case_data['commodity'][commodity.get_name()]['specific_co2_emissions_available'] = commodity.get_specific_co2_emissions_available()
        case_data['commodity'][commodity.get_name()]['specific_co2_emissions_emitted'] = commodity.get_specific_co2_emissions_emitted()
        case_data['commodity'][commodity.get_name()]['specific_co2_emissions_purchase'] = commodity.get_specific_co2_emissions_purchase()
        case_data['commodity'][commodity.get_name()]['specific_co2_emissions_sale'] = commodity.get_specific_co2_emissions_sale()

    file = open(path_name, "w")
    yaml.dump(case_data, file)
    file.close()
