from tkinter import ttk
from tkinter import *
import random

from object_commodity import Commodity
from object_component import ConversionComponent


class ComponentFrame:

    def __init__(self, parent, frame, component, pm_object, pm_object_original):

        """
        Component base frame
        Builds basis for component parameters frame and component commodities frame

        Input:
        - parent: to access function of parents (e.g., update whole interface)
        - component: name of component
        - pm_object_copy: Has stored all information and will be changed if adjustments conducted
        - pm_object_original: To restore default settings
        """

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component

        self.frame = ttk.Frame(frame)

        if self.component != '':

            # Create frame for parameters, main conversion and side conversions
            self.parameter_frame = ComponentParametersFrame(self.parent, self.frame, self.component,
                                                            self.pm_object, self.pm_object_original)
            self.conversion_frame = ConversionFrame(self, self.frame, self.component,
                                                    self.pm_object, self.pm_object_original)

            # Attach frames to interface and separate with separators
            ttk.Separator(self.frame, orient='horizontal').pack(fill="both", expand=True)
            self.parameter_frame.frame.pack(fill="both", expand=True)
            ttk.Separator(self.frame, orient='horizontal').pack(fill="both", expand=True)
            self.conversion_frame.frame.pack(fill="both", expand=True)


class ComponentParametersFrame:

    def adjust_component_value(self):
        def get_value_and_kill_window():

            self.capex_basis_var.set(capex_basis_var.get())
            self.component_object.set_capex_basis(capex_basis_var.get())

            if not self.scalable_var.get():
                self.component_object.set_scalable(False)
                self.component_object.set_capex(float(self.label_capex_value_str.get()))
            else:
                self.component_object.set_scalable(True)
                self.component_object.set_base_investment(float(self.label_base_investment_value_str.get()))
                self.component_object.set_base_capacity(self.label_base_capacity_value_str.get())
                self.component_object.set_economies_of_scale(float(self.label_scaling_factor_value_str.get()))
                self.component_object.set_max_capacity_economies_of_scale(float(self.label_max_capacity_eoc_value_str.get()))

            self.component_object.set_lifetime(float(self.label_lifetime_value_str.get()))
            self.component_object.set_fixed_OM(float(self.label_fixed_om.get()) / 100)
            self.component_object.set_variable_OM(float(self.label_variable_om.get()))
            self.component_object.set_min_p(float(self.label_min_capacity_value_str.get()) / 100)
            self.component_object.set_max_p(float(self.label_max_capacity_value_str.get()) / 100)
            self.component_object.set_ramp_down(float(self.label_ramp_down_value_str.get()) / 100)
            self.component_object.set_ramp_up(float(self.label_ramp_up_value_str.get()) / 100)

            if not self.shut_down_ability_var.get():
                self.component_object.set_shut_down_ability(False)
            else:
                self.component_object.set_shut_down_ability(True)
                self.component_object.set_start_up_time(float(self.label_start_up_time_value_str.get()))
                self.component_object.set_start_up_costs(float(self.label_start_up_costs_value_str.get()))

            if not self.hot_standby_ability_var.get():
                self.component_object.set_hot_standby_ability(False)
            else:
                self.component_object.set_hot_standby_ability(True)
                self.component_object.set_hot_standby_demand(hot_standby_combobox.get(), float(hot_standby_entry.get()))
                self.component_object.set_hot_standby_startup_time(int(hot_standby_startup_time_entry.get()))

            self.component_object.set_number_parallel_units(float(self.label_number_parallel_units_str.get()))

            if self.has_fixed_capacity_var.get():
                self.component_object.set_has_fixed_capacity(True)
                self.component_object.set_fixed_capacity(self.fixed_capacity_var.get())
            else:
                self.component_object.set_has_fixed_capacity(False)

            self.component_object.set_installation_co2_emissions(float(self.label_installation_co2_emissions.get()))
            self.component_object.set_fixed_co2_emissions(float(self.label_fixed_co2_emissions.get()))
            self.component_object.set_variable_co2_emissions(float(self.label_variable_co2_emissions.get()))
            self.component_object.set_disposal_co2_emissions(float(self.label_disposal_co2_emissions.get()))

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            newWindow.destroy()

        def activate_scale_no_scale():
            if self.scalable_var.get():
                entry_capex_var.config(state=DISABLED)

                label_base_investment_value.config(state=NORMAL)
                label_base_capacity_value.config(state=NORMAL)
                label_scaling_factor_value.config(state=NORMAL)
                label_max_capacity_eoc_value.config(state=NORMAL)

            else:
                entry_capex_var.config(state=NORMAL)

                label_base_investment_value.config(state=DISABLED)
                label_base_capacity_value.config(state=DISABLED)
                label_scaling_factor_value.config(state=DISABLED)
                label_max_capacity_eoc_value.config(state=DISABLED)

        def activate_shut_down():
            if self.shut_down_ability_var.get():
                entry_start_up_time.config(state=NORMAL)
                entry_start_up_costs.config(state=NORMAL)

            else:
                entry_start_up_time.config(state=DISABLED)
                entry_start_up_costs.config(state=DISABLED)

        def activate_hot_standby():
            if self.hot_standby_ability_var.get():
                hot_standby_combobox.config(state='readonly')
                hot_standby_entry.config(state=NORMAL)
                hot_standby_startup_time_entry.config(state=NORMAL)
            else:
                hot_standby_combobox.config(state=DISABLED)
                hot_standby_entry.config(state=DISABLED)
                hot_standby_startup_time_entry.config(state=DISABLED)

        def activate_fixed_capacity():
            if self.has_fixed_capacity_var.get():
                entry_fixed_capacity.config(state=NORMAL)
            else:
                entry_fixed_capacity.config(state=DISABLED)

        def change_capex_basis():

            if capex_basis_var.get() == 'input':
                name_new = self.component_object.get_main_input()
                unit_new = self.pm_object.get_commodity(name_new).get_unit()
            else:
                name_new = self.component_object.get_main_output()
                unit_new = self.pm_object.get_commodity(name_new).get_unit()

            output_commodity_new = self.component_object.get_main_output()
            unit_output_new = self.pm_object.get_commodity(self.component_object.get_main_output()).get_unit()

            if unit_new == 'GWh':
                unit_new = 'GW'
                capex_unit_new = self.monetary_unit + '/' + unit_new + ' ' + name_new
                capacity_unit_new = 'GW ' + name_new
            elif unit_new == 'MWh':
                unit_new = 'MW'
                capex_unit_new = self.monetary_unit + '/' + unit_new + ' ' + name_new
                capacity_unit_new = 'MW ' + name_new
            elif unit_new == 'kWh':
                unit_new = 'kW'
                capex_unit_new = self.monetary_unit + '/' + unit_new + ' ' + name_new
                capacity_unit_new = 'kW ' + name_new
            else:
                capex_unit_new = self.monetary_unit + '/' + unit_new + '*h ' + name_new
                capacity_unit_new = unit_new + '/h ' + name_new

            capex_unit_var.set('Capex [' + capex_unit_new + ']')
            base_capacity_var.set('Base Capacity [' + capacity_unit_new + ']')
            max_capacity_var.set('Maximal Capacity [' + capacity_unit_new + ']')
            fixed_capacity_var.set('Fixed Capacity [' + capacity_unit_new + ']')
            cold_start_up_var.set('Cold Start up Costs [' + self.monetary_unit + '/' + capacity_unit_new + ']')
            variable_om_var.set(
                'Variable O&M [' + self.monetary_unit + ' / ' + unit_output_new + output_commodity_new + ']')
            installation_co2_var.set('Installation CO2 emissions [t CO2 / ' + capacity_unit_new + ']')
            fixed_co2_var.set('Fixed CO2 emissions [t CO2 / ' + capacity_unit_new + ' / a]')
            variable_co2_var.set(
                'Variable CO2 emissions [t CO2 / ' + unit_output_new + ' ' + output_commodity_new + ']')
            disposal_co2_var.set('Disposal CO2 emissions [t CO2 / ' + capacity_unit_new + ']')

        # Toplevel object which will
        # be treated as a new window
        newWindow = Toplevel()
        newWindow.grid_columnconfigure(0, weight=1)
        newWindow.grid_columnconfigure(1, weight=1)
        newWindow.grab_set()

        # sets the title of the
        # Toplevel widget
        newWindow.title('Adjust Component Parameters')

        ttk.Checkbutton(newWindow, text='Scalable?',
                        variable=self.scalable_var,
                        command=activate_scale_no_scale).grid(row=0, column=0, columnspan=2, sticky='w')

        if self.component_object.is_scalable():
            status_scale = NORMAL
            status_no_scale = DISABLED
        else:
            status_scale = DISABLED
            status_no_scale = NORMAL

        ttk.Label(newWindow, text='Investment Basis').grid(row=1, column=0, sticky='w')

        capex_basis_frame = ttk.Frame(newWindow)

        capex_basis_var = StringVar()
        capex_basis_var.set(self.capex_basis_var.get())

        capex_basis_input_rb = ttk.Radiobutton(capex_basis_frame, text='Main Input', value='input',
                                               variable=capex_basis_var, state=NORMAL, command=change_capex_basis)
        capex_basis_input_rb.grid(row=0, column=0)
        capex_basis_output_rb = ttk.Radiobutton(capex_basis_frame, text='Main Output', value='output',
                                                variable=capex_basis_var, state=NORMAL, command=change_capex_basis)
        capex_basis_output_rb.grid(row=0, column=1)

        capex_basis_frame.grid(row=1, column=1, sticky='ew')

        if self.capex_basis_var.get() == 'input':
            commodity_name = self.component_object.get_main_input()
            unit = self.pm_object.get_commodity(self.component_object.get_main_input()).get_unit()
        else:
            commodity_name = self.component_object.get_main_output()
            unit = self.pm_object.get_commodity(self.component_object.get_main_output()).get_unit()
        commodity_output = self.component_object.get_main_output()
        unit_output = self.pm_object.get_commodity(self.component_object.get_main_output()).get_unit()

        if unit == 'GWh':
            unit = 'GW'
            capex_unit = self.monetary_unit + '/' + unit + ' ' + commodity_name
            capacity_unit = 'GW ' + commodity_name
        elif unit == 'MWh':
            unit = 'MW'
            capex_unit = self.monetary_unit + '/' + unit + ' ' + commodity_name
            capacity_unit = 'MW ' + commodity_name
        elif unit == 'kWh':
            unit = 'kW'
            capex_unit = self.monetary_unit + '/' + unit + ' ' + commodity_name
            capacity_unit = 'kW ' + commodity_name
        else:
            capex_unit = self.monetary_unit + '/' + unit + '*h ' + commodity_name
            capacity_unit = unit + '/h ' + commodity_name

        capex_unit_var = StringVar()
        capex_unit_var.set('Capex [' + capex_unit + ']')

        base_capacity_var = StringVar()
        base_capacity_var.set('Base Capacity [' + capacity_unit + ']')

        max_capacity_var = StringVar()
        max_capacity_var.set('Maximal Capacity [' + capacity_unit + ']')

        variable_om_var = DoubleVar()
        variable_om_var.set('Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + unit_output + commodity_output + ']')

        installation_co2_var = StringVar()
        installation_co2_var.set('Installation CO2 emissions [t CO2 / ' + capacity_unit + ']')

        fixed_co2_var = StringVar()
        fixed_co2_var.set('Fixed CO2 emissions [t CO2 / ' + capacity_unit + ' / a]')

        variable_co2_var = StringVar()
        variable_co2_var.set('Variable CO2 emissions [t CO2 / ' + unit_output + ' ' + commodity_output + ']')

        disposal_co2_var = StringVar()
        disposal_co2_var.set('Disposal CO2 emissions [t CO2 / ' + capacity_unit + ']')

        ttk.Label(newWindow, textvariable=capex_unit_var).grid(row=2, column=0, sticky='w')
        entry_capex_var = ttk.Entry(newWindow, textvariable=self.label_capex_value_str, state=status_no_scale)
        entry_capex_var.grid(row=2, column=1, sticky='ew')

        label_base_investment = ttk.Label(newWindow, text='Base Investment [' + self.monetary_unit + ']')
        label_base_investment.grid(column=0, row=3, sticky='w')
        label_base_investment_value = ttk.Entry(newWindow,
                                                textvariable=self.label_base_investment_value_str,
                                                state=status_scale)
        label_base_investment_value.grid(column=1, row=3, sticky='ew')

        label_base_capacity = ttk.Label(newWindow, textvariable=base_capacity_var)
        label_base_capacity.grid(column=0, row=4, sticky='w')
        label_base_capacity_value = ttk.Entry(newWindow, textvariable=self.label_base_capacity_value_str, state=status_scale)
        label_base_capacity_value.grid(column=1, row=4, sticky='ew')

        label_scaling_factor = ttk.Label(newWindow, text='Scaling factor')
        label_scaling_factor.grid(column=0, row=5, sticky='w')
        label_scaling_factor_value = ttk.Entry(newWindow,
                                               textvariable=self.label_scaling_factor_value_str,
                                               state=status_scale)
        label_scaling_factor_value.grid(column=1, row=5, sticky='ew')

        label_max_capacity_eoc = ttk.Label(newWindow, textvariable=max_capacity_var)
        label_max_capacity_eoc.grid(column=0, row=6, sticky='w')
        label_max_capacity_eoc_value = ttk.Entry(newWindow,
                                                 textvariable=self.label_max_capacity_eoc_value_str,
                                                 state=status_scale)
        label_max_capacity_eoc_value.grid(column=1, row=6, sticky='ew')

        ttk.Label(newWindow, text='Lifetime [Years]').grid(row=7, column=0, sticky='w')
        entry_lifetime = ttk.Entry(newWindow, textvariable=self.label_lifetime_value_str)
        entry_lifetime.grid(row=7, column=1, sticky='ew')

        ttk.Label(newWindow, text='Fixed O&M [%]').grid(row=8, column=0, sticky='w')
        entry_fixed_om = ttk.Entry(newWindow, textvariable=self.label_fixed_om)
        entry_fixed_om.grid(row=8, column=1, sticky='ew')

        text_variable_om = 'Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + unit_output \
                           + ' ' + self.component_object.get_main_output() + ']'
        ttk.Label(newWindow, text=text_variable_om).grid(row=9, column=0, sticky='w')
        entry_variable_om = ttk.Entry(newWindow, textvariable=self.label_variable_om)
        entry_variable_om.grid(row=9, column=1, sticky='ew')

        ttk.Label(newWindow, text='Minimal power [%]').grid(row=10, column=0, sticky='w')
        entry_min_capacity = ttk.Entry(newWindow, textvariable=self.label_min_capacity_value_str)
        entry_min_capacity.grid(row=10, column=1, sticky='ew')

        ttk.Label(newWindow, text='Maximal power [%]').grid(row=11, column=0, sticky='w')
        entry_max_capacity = ttk.Entry(newWindow, textvariable=self.label_max_capacity_value_str)
        entry_max_capacity.grid(row=11, column=1, sticky='ew')

        ttk.Label(newWindow, text='Ramp down [%/h]').grid(row=12, column=0, sticky='w')
        entry_ramp_down = ttk.Entry(newWindow, textvariable=self.label_ramp_down_value_str)
        entry_ramp_down.grid(row=12, column=1, sticky='ew')

        ttk.Label(newWindow, text='Ramp up [%/h]').grid(row=13, column=0, sticky='w')
        entry_ramp_up = ttk.Entry(newWindow, textvariable=self.label_ramp_up_value_str)
        entry_ramp_up.grid(row=13, column=1, sticky='ew')

        ttk.Checkbutton(newWindow, text='Shut down possible?',
                       variable=self.shut_down_ability_var,
                       command=activate_shut_down).grid(row=14, column=0, columnspan=2, sticky='w')

        if self.component_object.get_shut_down_ability():
            shut_down_state = NORMAL
        else:
            shut_down_state = DISABLED

        ttk.Label(newWindow, text='Cold Start up Time [h]').grid(row=15, column=0, sticky='w')
        entry_start_up_time = ttk.Entry(newWindow, textvariable=self.label_start_up_time_value_str, state=shut_down_state)
        entry_start_up_time.grid(row=15, column=1, sticky='ew')

        cold_start_up_var = StringVar()
        cold_start_up_var.set('Cold Start up Costs [' + self.monetary_unit + '/' + capacity_unit + ']')
        ttk.Label(newWindow, textvariable=cold_start_up_var).grid(row=16, column=0, sticky='w')
        entry_start_up_costs = ttk.Entry(newWindow, textvariable=self.label_start_up_costs_value_str, state=shut_down_state)
        entry_start_up_costs.grid(row=16, column=1, sticky='ew')

        # Hot standby ability
        if self.hot_standby_ability_var.get():
            state_hot_standby = NORMAL
            state_hot_standby_combobox = 'readonly'
        else:
            state_hot_standby = DISABLED
            state_hot_standby_combobox = DISABLED

        ttk.Checkbutton(newWindow, text='Hot Standby possible?', variable=self.hot_standby_ability_var,
                        command=activate_hot_standby).grid(row=17, column=0, columnspan=2, sticky='w')

        commodities = []
        for s in self.pm_object.get_final_commodities_objects():
            commodities.append(s.get_name())

        ttk.Label(newWindow, text='Hot Standby Input Commodity').grid(row=18, column=0, sticky='w')
        hot_standby_combobox = ttk.Combobox(newWindow, textvariable='', values=commodities, state=state_hot_standby_combobox)
        hot_standby_combobox.set(self.hot_standby_commodity_var.get())
        hot_standby_combobox.grid(row=18, column=1, sticky='ew')

        ttk.Label(newWindow, text='Hot Standby Hourly Demand').grid(row=19, column=0, sticky='w')
        hot_standby_entry = ttk.Entry(newWindow, textvariable=self.hot_standby_demand_var, state=state_hot_standby)
        hot_standby_entry.grid(row=19, column=1, sticky='ew')

        ttk.Label(newWindow, text='Hot Standby Startup Time [h]').grid(row=20, column=0, sticky='w')
        hot_standby_startup_time_entry = ttk.Entry(newWindow, textvariable=self.hot_standby_demand_startup_time,
                                                   state=state_hot_standby)
        hot_standby_startup_time_entry.grid(row=20, column=1, sticky='ew')

        # Number of units of same type in system
        ttk.Label(newWindow, text='Number of units in system').grid(row=21, column=0, sticky='w')
        entry_number_units = ttk.Entry(newWindow, textvariable=self.label_number_parallel_units_str)
        entry_number_units.grid(row=21, column=1, sticky='ew')

        if self.has_fixed_capacity_var.get():
            state_fixed_capacity = NORMAL
        else:
            state_fixed_capacity = DISABLED

        fixed_capacity_var = StringVar()
        fixed_capacity_var.set('Fixed Capacity [' + capacity_unit + ']')

        ttk.Checkbutton(newWindow, textvariable=fixed_capacity_var, variable=self.has_fixed_capacity_var,
                        command=activate_fixed_capacity).grid(row=22, column=0, columnspan=2, sticky='w')
        entry_fixed_capacity = ttk.Entry(newWindow, textvariable=self.fixed_capacity_var, state=state_fixed_capacity)
        entry_fixed_capacity.grid(row=22, column=1, sticky='ew')

        ttk.Label(newWindow, textvariable=installation_co2_var).grid(row=23, column=0, sticky='w')
        entry_installation_co2 = ttk.Entry(newWindow, textvariable=self.label_installation_co2_emissions)
        entry_installation_co2.grid(row=23, column=1, sticky='ew')

        ttk.Label(newWindow, textvariable=fixed_co2_var).grid(row=25, column=0, sticky='w')
        entry_fixed_co2 = ttk.Entry(newWindow, textvariable=self.label_fixed_co2_emissions)
        entry_fixed_co2.grid(row=25, column=1, sticky='ew')

        ttk.Label(newWindow, textvariable=variable_co2_var).grid(row=26, column=0, sticky='w')
        entry_variable_co2 = ttk.Entry(newWindow, textvariable=self.label_variable_co2_emissions)
        entry_variable_co2.grid(row=26, column=1, sticky='ew')

        ttk.Label(newWindow, textvariable=disposal_co2_var).grid(row=27, column=0, sticky='w')
        entry_disposal_co2 = ttk.Entry(newWindow, textvariable=self.label_disposal_co2_emissions)
        entry_disposal_co2.grid(row=27, column=1, sticky='ew')

        button_frame = ttk.Frame(newWindow)

        button = ttk.Button(button_frame, text='Adjust values', command=get_value_and_kill_window)
        button.grid(row=0, column=0, sticky='ew')

        button = ttk.Button(button_frame, text='Cancel', command=newWindow.destroy)
        button.grid(row=0, column=1, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        button_frame.grid(row=28, columnspan=2, sticky='ew')

        newWindow.mainloop()

    def set_component_parameters_to_default(self):

        # Important: Not only delete component and get copy of pm_object_original
        # because conversions should not be deleted

        component_original = self.pm_object_original.get_component(self.component)
        component_copy = self.pm_object.get_component(self.component)

        component_copy.set_scalable(component_original.is_scalable())
        component_copy.set_capex_basis(component_original.get_capex_basis())
        component_copy.set_capex(component_original.get_capex())
        component_copy.set_base_investment(component_original.get_base_investment())
        component_copy.set_base_capacity(component_original.get_base_capacity())
        component_copy.set_economies_of_scale(component_original.get_economies_of_scale())
        component_copy.set_max_capacity_economies_of_scale(component_original.get_max_capacity_economies_of_scale())
        component_copy.set_number_parallel_units(component_original.get_number_parallel_units())
        component_copy.set_installation_co2_emissions(component_original.get_installation_co2_emissions())
        component_copy.set_fixed_co2_emissions(component_original.get_fixed_co2_emissions())
        component_copy.set_variable_co2_emissions(component_original.get_variable_co2_emissions())
        component_copy.set_disposal_co2_emissions(component_original.get_disposal_co2_emissions())

        component_copy.set_lifetime(component_original.get_lifetime())
        component_copy.set_fixed_OM(float(component_original.get_fixed_OM()))
        component_copy.set_variable_OM(float(component_original.get_variable_OM()))
        component_copy.set_min_p(float(component_original.get_min_p()))
        component_copy.set_max_p(float(component_original.get_max_p()))
        component_copy.set_ramp_down(component_original.get_ramp_down())
        component_copy.set_ramp_up(component_original.get_ramp_up())

        component_copy.set_shut_down_ability(component_original.get_shut_down_ability())
        component_copy.set_start_up_time(component_original.get_start_up_time())
        component_copy.set_start_up_costs(component_original.get_start_up_costs())

        if component_original.get_hot_standby_ability():
            component_copy.set_hot_standby_ability(component_original.get_hot_standby_ability())
            component_copy.set_hot_standby_startup_time(component_original.get_hot_standby_startup_time())
            component_copy.set_hot_standby_demand(component_original.get_hot_standby_demand())

        component_copy.set_has_fixed_capacity(component_original.get_has_fixed_capacity())
        component_copy.set_fixed_capacity(component_original.get_fixed_capacity())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def __init__(self, parent, super_frame, component, pm_object, pm_object_original):

        """
        Frame which contains all financial and technical parameters as well as the ability to change these

        Input
        - parent: Interface object - To access functions of Interface class
        - root: Tk.root - To add new windows
        - super_frame: tk.Frame - Frame of component, which contains this frame
        - component: string - Name of component
        - pm_object: Parameter object - Contains all information
        - pm_object_original: Parameter object - Contains all information (to set default values)

        Function
        - Creates parameter frame and shows all parameters
        - Has functions to change, store and reset parameters
        """

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component
        self.component_object = self.pm_object.get_component(component)
        self.monetary_unit = self.pm_object.get_monetary_unit()

        self.frame = ttk.Frame(super_frame)

        if self.component != '':

            # Initiate values for different parameters

            self.parameter_label = ttk.Label(self.frame, text='Parameter', font='Helvetica 10 bold')
            self.parameter_label.grid(column=0, row=0, sticky='w')
            self.value_label = ttk.Label(self.frame, text='Value', font='Helvetica 10 bold')
            self.value_label.grid(column=1, row=0, sticky='w')

            capex_basis = self.component_object.get_capex_basis()
            lifetime = self.component_object.get_lifetime()
            fixed_om = round(float(self.component_object.get_fixed_OM() * 100), 2)
            variable_om = round(float(self.component_object.get_variable_OM()), 2)

            min_p = round(float(self.component_object.get_min_p() * 100), 2)
            max_p = round(float(self.component_object.get_max_p() * 100), 2)
            ramp_down = round(float(self.component_object.get_ramp_down() * 100), 2)
            ramp_up = round(float(self.component_object.get_ramp_up() * 100), 2)

            shut_down_ability = bool(self.component_object.get_shut_down_ability())
            self.shut_down_ability_var = BooleanVar()
            self.shut_down_ability_var.set(shut_down_ability)
            self.label_start_up_time_value_str = IntVar()
            self.label_start_up_costs_value_str = IntVar()
            if shut_down_ability:
                start_up_time = self.component_object.get_start_up_time()
                self.label_start_up_time_value_str.set(start_up_time)
                start_up_costs = self.component_object.get_start_up_costs()
                self.label_start_up_costs_value_str.set(start_up_costs)
            else:
                self.label_start_up_time_value_str.set(0)
                self.label_start_up_costs_value_str.set(0)

            hot_standby_ability = bool(self.component_object.get_hot_standby_ability())
            self.hot_standby_ability_var = BooleanVar()
            self.hot_standby_ability_var.set(hot_standby_ability)
            self.hot_standby_commodity_var = StringVar()
            self.hot_standby_demand_var = DoubleVar()
            self.hot_standby_demand_startup_time = IntVar()
            if hot_standby_ability:
                hot_standby_demand = self.component_object.get_hot_standby_demand()
                commodity = [*hot_standby_demand.keys()][0]
                hot_standby_unit = self.pm_object.get_commodity(commodity).get_unit()
                hot_standby_startup_time = self.component_object.get_hot_standby_startup_time()

                self.hot_standby_ability_var.set(hot_standby_ability)
                self.hot_standby_commodity_var.set(commodity)
                self.hot_standby_demand_var.set(hot_standby_demand[commodity])
                self.hot_standby_demand_startup_time.set(hot_standby_startup_time)
            else:
                self.hot_standby_commodity_var.set('')
                self.hot_standby_demand_var.set(0)
                self.hot_standby_demand_startup_time.set(0)

            number_parallel_units = int(self.component_object.get_number_parallel_units())

            has_fixed_capacity = self.component_object.get_has_fixed_capacity()
            fixed_capacity = self.component_object.get_fixed_capacity()

            installation_co2_emissions = self.component_object.get_installation_co2_emissions()
            fixed_co2_emissions = self.component_object.get_fixed_co2_emissions()
            variable_co2_emissions = self.component_object.get_variable_co2_emissions()
            disposal_co2_emissions = self.component_object.get_disposal_co2_emissions()

            self.label_capex_value_str = DoubleVar()
            self.capex_basis_var = StringVar()
            self.capex_basis_var.set(capex_basis)

            self.scalable_var = BooleanVar()
            self.scalable_var.set(False)
            self.label_base_investment_value_str = DoubleVar()
            self.label_base_capacity_value_str = DoubleVar()
            self.label_scaling_factor_value_str = DoubleVar()
            self.label_max_capacity_eoc_value_str = DoubleVar()

            self.label_lifetime_value_str = IntVar()
            self.label_lifetime_value_str.set(int(lifetime))
            self.label_fixed_om = DoubleVar()
            self.label_fixed_om.set(fixed_om)
            self.label_variable_om = DoubleVar()
            self.label_variable_om.set(variable_om)
            self.label_min_capacity_value_str = DoubleVar()
            self.label_min_capacity_value_str.set(min_p)
            self.label_max_capacity_value_str = DoubleVar()
            self.label_max_capacity_value_str.set(max_p)
            self.label_ramp_down_value_str = DoubleVar()
            self.label_ramp_down_value_str.set(ramp_down)
            self.label_ramp_up_value_str = DoubleVar()
            self.label_ramp_up_value_str.set(ramp_up)

            self.label_number_parallel_units_str = IntVar()
            self.label_number_parallel_units_str.set(number_parallel_units)

            self.has_fixed_capacity_var = BooleanVar()
            self.has_fixed_capacity_var.set(has_fixed_capacity)
            self.fixed_capacity_var = DoubleVar()
            self.fixed_capacity_var.set(fixed_capacity)

            self.label_installation_co2_emissions = DoubleVar()
            self.label_installation_co2_emissions.set(installation_co2_emissions)
            self.label_fixed_co2_emissions = DoubleVar()
            self.label_fixed_co2_emissions.set(fixed_co2_emissions)
            self.label_variable_co2_emissions = DoubleVar()
            self.label_variable_co2_emissions.set(variable_co2_emissions)
            self.label_disposal_co2_emissions = DoubleVar()
            self.label_disposal_co2_emissions.set(disposal_co2_emissions)

            # Capex Basis
            ttk.Label(self.frame, text='Investment Basis').grid(row=1, column=0, sticky='ew')

            capex_basis_frame = ttk.Frame(self.frame)

            ttk.Radiobutton(capex_basis_frame, text='Main Input', value='input',
                            variable=self.capex_basis_var, state=DISABLED).grid(row=0, column=0)
            ttk.Radiobutton(capex_basis_frame, text='Main Output', value='output',
                            variable=self.capex_basis_var, state=DISABLED).grid(row=0, column=1)

            capex_basis_frame.grid(row=1, column=1, sticky='ew')

            i = 2

            if self.capex_basis_var.get() == 'input':
                name = self.component_object.get_main_input()
                unit = self.pm_object.get_commodity(self.component_object.get_main_input()).get_unit()
            else:
                name = self.component_object.get_main_output()
                unit = self.pm_object.get_commodity(self.component_object.get_main_output()).get_unit()
            main_output = self.component_object.get_main_output()
            unit_output = self.pm_object.get_commodity(main_output).get_unit()

            if unit == 'GWh':
                unit = 'GW'
                capex_unit = self.monetary_unit + '/' + unit + ' ' + name
                capacity_unit = 'GW ' + name
            elif unit == 'MWh':
                unit = 'MW'
                capex_unit = self.monetary_unit + '/' + unit + ' ' + name
                capacity_unit = 'MW ' + name
            elif unit == 'kWh':
                unit = 'kW'
                capex_unit = self.monetary_unit + '/' + unit + ' ' + name
                capacity_unit = 'kW ' + name
            else:
                capex_unit = self.monetary_unit + '/' + unit + '*h ' + name
                capacity_unit = unit + '/h ' + name

            if not self.component_object.is_scalable():

                # The parameters below only exist if component is not scalable

                capex = self.component_object.get_capex()
                self.label_capex_value_str.set(capex)

                ttk.Label(self.frame, text='CAPEX [' + capex_unit + ']').grid(column=0,
                                                                              row=i, sticky='w')
                ttk.Label(self.frame, text=self.label_capex_value_str.get()).grid(column=1, row=i, sticky='w')

                i += 1

            else:

                # The parameters below only exist if component is scalable

                self.scalable_var.set(True)
                base_investment = self.component_object.get_base_investment()
                base_capacity = self.component_object.get_base_capacity()
                scaling_factor = self.component_object.get_economies_of_scale()
                max_capacity_eoc = self.component_object.get_max_capacity_economies_of_scale()

                self.label_base_investment_value_str.set(base_investment)
                self.label_base_capacity_value_str.set(base_capacity)
                self.label_scaling_factor_value_str.set(scaling_factor)
                self.label_max_capacity_eoc_value_str.set(max_capacity_eoc)

                self.label_base_investment = ttk.Label(self.frame, text='Base investment [' + self.monetary_unit + ']')
                self.label_base_investment.grid(column=0, row=i+1, sticky='w')
                self.label_base_investment_value = ttk.Label(self.frame,
                                                             text=self.label_base_investment_value_str.get())
                self.label_base_investment_value.grid(column=1, row=i+1, sticky='w')

                self.label_base_capacity = ttk.Label(self.frame, text='Base capacity [' + capacity_unit + ']')
                self.label_base_capacity.grid(column=0, row=i+2, sticky='w')
                self.label_base_capacity_value = ttk.Label(self.frame, text=self.label_base_capacity_value_str.get())
                self.label_base_capacity_value.grid(column=1, row=i+2, sticky='w')

                self.label_scaling_factor = ttk.Label(self.frame, text='Scaling factor')
                self.label_scaling_factor.grid(column=0, row=i+3, sticky='w')
                self.label_scaling_factor_value = ttk.Label(self.frame,
                                                            text=self.label_scaling_factor_value_str.get())
                self.label_scaling_factor_value.grid(column=1, row=i+3, sticky='w')

                self.label_max_capacity_eoc = ttk.Label(self.frame, text='Max capacity [' + capacity_unit + ']')
                self.label_max_capacity_eoc.grid(column=0, row=i+4, sticky='w')
                self.label_max_capacity_eoc_value = ttk.Label(self.frame,
                                                              text=self.label_max_capacity_eoc_value_str.get())
                self.label_max_capacity_eoc_value.grid(column=1, row=i+4, sticky='w')

                i += 4

            ttk.Label(self.frame, text='Lifetime [Years]').grid(column=0, row=i+1, sticky='w')
            ttk.Label(self.frame, text=self.label_lifetime_value_str.get()).grid(column=1, row=i+1, sticky='w')

            ttk.Label(self.frame, text='Fixed O&M [%]').grid(column=0, row=i+2, sticky='w')
            ttk.Label(self.frame, text=self.label_fixed_om.get()).grid(column=1, row=i + 2, sticky='w')

            ttk.Label(self.frame,
                      text='Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + unit_output + ' '
                           + main_output + ']').grid(
                column=0, row=i + 3, sticky='w')
            ttk.Label(self.frame, text=self.label_variable_om.get()).grid(column=1, row=i + 3, sticky='w')

            ttk.Label(self.frame, text='Minimal power [%]').grid(column=0, row=i+4, sticky='w')
            ttk.Label(self.frame, text=self.label_min_capacity_value_str.get()).grid(column=1, row=i+4, sticky='w')

            ttk.Label(self.frame, text='Maximal power [%]').grid(column=0, row=i+5, sticky='w')
            ttk.Label(self.frame, text=self.label_max_capacity_value_str.get()).grid(column=1, row=i+5, sticky='w')

            ttk.Label(self.frame, text='Ramp down time [%/h]').grid(column=0, row=i+6, sticky='w')
            ttk.Label(self.frame, text=self.label_ramp_down_value_str.get()).grid(column=1, row=i+6, sticky='w')

            ttk.Label(self.frame, text='Ramp up time [%/h]').grid(column=0, row=i+7, sticky='w')
            ttk.Label(self.frame, text=self.label_ramp_up_value_str.get()).grid(column=1, row=i+7, sticky='w')

            i += 7

            if self.component_object.get_shut_down_ability():
                ttk.Label(self.frame, text='Cold Start up time [h]').grid(column=0, row=i+1, sticky='w')
                ttk.Label(self.frame, text=self.label_start_up_time_value_str.get()).grid(column=1, row=i+1, sticky='w')
                ttk.Label(self.frame, text='Cold Start up costs [' + self.monetary_unit + ']').grid(column=0,
                                                                                                    row=i + 2,
                                                                                                    sticky='w')
                ttk.Label(self.frame, text=self.label_start_up_costs_value_str.get()).grid(column=1, row=i + 2,
                                                                                          sticky='w')

                i += 2

            if hot_standby_ability:

                ttk.Label(self.frame, text='Hot Standby Input Commodity').grid(row=i+1, column=0, sticky='w')
                ttk.Label(self.frame, text=self.hot_standby_commodity_var.get()).grid(row=i + 1, column=1, sticky='w')

                if hot_standby_unit == 'MWh':
                    hot_standby_unit = 'MW'
                elif hot_standby_unit == 'kWh':
                    hot_standby_unit = 'kW'
                elif hot_standby_unit == 'GWh':
                    hot_standby_unit = 'GW'
                else:
                    hot_standby_unit = hot_standby_unit + ' / h'

                ttk.Label(self.frame, text='Hot Standby Input Demand [' + hot_standby_unit + ']').grid(row=i + 2,
                                                                                                       column=0,
                                                                                                       sticky='w')
                ttk.Label(self.frame, text=self.hot_standby_demand_var.get()).grid(row=i + 2, column=1, sticky='w')

                ttk.Label(self.frame, text='Hot Standby Start up Time [h]').grid(row=i + 3, column=0, sticky='w')
                ttk.Label(self.frame, text=self.hot_standby_demand_startup_time.get()).grid(row=i + 3, column=1,
                                                                                            sticky='w')

                i += 3

            ttk.Label(self.frame, text='Number of units in system').grid(column=0, row=i + 1, sticky='w')
            ttk.Label(self.frame, text=self.label_number_parallel_units_str.get()).grid(column=1, row=i + 1, sticky='w')

            i += 1

            if self.has_fixed_capacity_var.get():
                ttk.Label(self.frame, text='Fixed Capacity [' + capacity_unit + ']').grid(column=0, row=i + 1, sticky='w')
                ttk.Label(self.frame, text=self.fixed_capacity_var.get()).grid(column=1, row=i + 1, sticky='w')

                i += 1

            ttk.Label(self.frame, text='Installation CO2 emissions [t CO2 / ' + capacity_unit + ']').grid(column=0,
                                                                                                          row=i + 1,
                                                                                                          sticky='w')
            ttk.Label(self.frame, text=self.label_installation_co2_emissions.get()).grid(column=1, row=i + 1,
                                                                                         sticky='w')

            ttk.Label(self.frame, text='Fixed CO2 emissions [t CO2 / ' + capacity_unit + ' / a]').grid(column=0,
                                                                                                       row=i + 2,
                                                                                                       sticky='w')
            ttk.Label(self.frame, text=self.label_fixed_co2_emissions.get()).grid(column=1, row=i + 2,
                                                                                  sticky='w')

            ttk.Label(self.frame, text='Variable CO2 emissions [t CO2 / ' + unit_output + ' '
                                       + main_output + ']').grid(column=0, row=i + 3, sticky='w')
            ttk.Label(self.frame, text=self.label_variable_co2_emissions.get()).grid(column=1, row=i + 3, sticky='w')

            ttk.Label(self.frame, text='Disposal CO2 emissions [t CO2 / ' + capacity_unit + ']').grid(column=0,
                                                                                                      row=i + 4,
                                                                                                      sticky='w')
            ttk.Label(self.frame, text=self.label_disposal_co2_emissions.get()).grid(column=1, row=i + 4, sticky='w')

            i += 5

            self.delete_component_dict = {}

            ttk.Button(self.frame, text='Adjust Conversion Parameters',
                       command=self.adjust_component_value).grid(columnspan=2, row=i, sticky='ew')

            self.frame.grid_columnconfigure(0, weight=1, uniform="a")
            self.frame.grid_columnconfigure(1, weight=1, uniform="a")


class AddNewComponentWindow:

    def add_component_and_kill_window(self):

        def destroy_windows_after_error():
            self.newWindow.destroy()
            self.newWindowWrongName.destroy()

        if (self.name.get() in self.pm_object.get_all_component_names()) \
                | (self.name.get() in self.pm_object.get_all_commodity_names()):

            self.newWindowWrongName = Toplevel()
            self.newWindowWrongName.grab_set()
            self.newWindowWrongName.title('Error')

            self.name = StringVar()

            ttk.Label(self.newWindowWrongName,
                      text='Please choose other name as component or commodities with this name exists').grid(row=0,
                                                                                                              column=0,
                                                                                                              sticky='ew')

            ttk.Button(self.newWindowWrongName, text='Ok',
                       command=destroy_windows_after_error).grid(row=1, column=0, sticky='ew')

            self.newWindowWrongName.grid_columnconfigure(0, weight=1, uniform='a')

        else:

            # Creates component with dummy parameters and random main conversion

            new_component = ConversionComponent(self.name.get(), final_unit=True, custom_unit=True)

            if len([*self.pm_object.get_all_commodities().keys()]) > 0:

                input_random = random.choice([*self.pm_object.get_all_commodities().keys()])
                new_component.add_input(input_random, 1)
                new_component.set_main_input(input_random)
                self.pm_object.get_commodity(input_random).set_final(True)

                output_random = random.choice([*self.pm_object.get_all_commodities().keys()])
                new_component.add_output(output_random, 1)
                new_component.set_main_output(output_random)
                self.pm_object.get_commodity(output_random).set_final(True)

                self.pm_object.add_component(self.name.get(), new_component)

            else:

                input_commodity = 'Electricity'
                output_commodity = 'Electricity'

                new_component.add_input(input_commodity, 1)
                new_component.add_output(output_commodity, 1)

                new_component.set_main_input(input_commodity)
                new_component.set_main_output(output_commodity)

                s = Commodity('Electricity', 'kWh', final_commodity=True)
                self.pm_object.add_commodity('Electricity', s)

                self.pm_object.add_component(self.name.get(), new_component)

            self.parent.pm_object_copy = self.pm_object
            self.parent.update_widgets()

            self.newWindow.destroy()

    def __init__(self, parent, pm_object):

        """
        Window to add new component

        :param parent: Interface object - needed to access Interface functions
        :param pm_object: Parameter object - needed to access and store information
        """

        self.parent = parent
        self.pm_object = pm_object

        self.newWindow = Toplevel()
        self.newWindow.grab_set()
        self.newWindow.title('Add New Component')

        self.name = StringVar()

        ttk.Label(self.newWindow, text='Name').grid(row=0, column=0, sticky='ew')
        ttk.Entry(self.newWindow, text=self.name).grid(row=0, column=1, sticky='ew')

        ttk.Button(self.newWindow, text='Add component',
                   command=self.add_component_and_kill_window).grid(row=1, column=0, sticky='ew')
        ttk.Button(self.newWindow, text='Cancel',
                   command=self.newWindow.destroy).grid(row=1, column=1, sticky='ew')

        self.newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        self.newWindow.grid_columnconfigure(1, weight=1, uniform='a')


class ConversionFrame:

    def set_component_conversions_to_default(self):

        # Remove all inputs and outputs from component
        all_inputs = dict(self.component_object.get_inputs())

        for comp_input in all_inputs:
            self.component_object.remove_input(comp_input)

        all_outputs = dict(self.component_object.get_outputs())

        for comp_output in all_outputs:
            self.component_object.remove_output(comp_output)

        # get inputs and outputs from original parameter object
        original_component = self.pm_object_original.get_component(self.component_object.get_name())

        all_inputs = dict(original_component.get_inputs())
        all_outputs = dict(original_component.get_outputs())

        # add inputs and outputs to component
        for comp_input in all_inputs:
            self.component_object.add_input(comp_input, original_component.get_inputs()[comp_input])

        for comp_output in all_outputs:
            self.component_object.add_output(comp_output, original_component.get_outputs()[comp_output])

        # set main input and output
        main_input = original_component.get_main_input()
        main_output = original_component.get_main_output()

        self.component_object.set_main_input(main_input)
        self.component_object.set_main_output(main_output)

        self.parent.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.parent.update_widgets()

    def create_me_balance_window(self):

        def get_values_and_kill_me_balance_window():

            def main_input_or_output_problem():

                def kill_main_i_o_window():
                    missing_main_i_o_window.destroy()

                missing_main_i_o_window = Toplevel()
                missing_main_i_o_window.title('')
                missing_main_i_o_window.grab_set()

                ttk.Label(missing_main_i_o_window, text=text).pack()
                ttk.Button(missing_main_i_o_window, text='Ok', command=kill_main_i_o_window).pack()

            # Check if main input and output are chosen and inform user if not
            main_input_exists = False
            for inp in current_inputs:
                if inp == current_main_input_var.get():
                    main_input_exists = True

            main_output_exists = False
            for inp in current_outputs:
                if inp == current_main_output_var.get():
                    main_output_exists = True

            if (not main_input_exists) & (not main_output_exists):
                text = 'Please choose main input and output'
                main_input_or_output_problem()
            elif main_input_exists & (not main_output_exists):
                text = 'Please choose main output'
                main_input_or_output_problem()
            elif (not main_input_exists) & main_output_exists:
                text = 'Please choose main input'
                main_input_or_output_problem()
            else:  # case main input and output are chosen

                # Delete all inputs and outputs from component
                all_inputs = dict(self.component_object.get_inputs())

                for comp_input in all_inputs:
                    self.component_object.remove_input(comp_input)

                all_outputs = dict(self.component_object.get_outputs())

                for comp_output in all_outputs:
                    self.component_object.remove_output(comp_output)

                # Add adjusted inputs and outputs to component
                main_input = current_main_input_var.get()
                main_output = current_main_output_var.get()

                for comp_input in current_inputs:
                    self.component_object.add_input(comp_input, current_input_coefficients[comp_input])

                    if comp_input not in self.pm_object.get_all_commodities():
                        s = Commodity(comp_input, self.current_units[comp_input],
                                      final_commodity=True, custom_commodity=True)
                        self.pm_object.add_commodity(comp_input, s)

                for comp_output in current_outputs:
                    self.component_object.add_output(comp_output, current_output_coefficients[comp_output])

                    if comp_output not in self.pm_object.get_all_commodities():
                        s = Commodity(comp_output, self.current_units[comp_output],
                                      final_commodity=True, custom_commodity=True)
                        self.pm_object.add_commodity(comp_output, s)

                # set main input and output, and adjust capex unit depending on main input
                self.component_object.set_main_input(main_input)
                self.component_object.set_main_output(main_output)

                # Check if commodities are not used anymore and delete them from all commodities
                for commodity in self.pm_object.get_all_commodities():
                    commodity_used = False
                    for c in self.pm_object.get_final_conversion_components_objects():
                        inputs = c.get_inputs()
                        for inp in [*inputs.keys()]:
                            if inp == commodity:
                                commodity_used = True
                                break

                        outputs = c.get_outputs()
                        for outp in [*outputs.keys()]:
                            if outp == commodity:
                                commodity_used = True
                                break

                    if not commodity_used:
                        self.pm_object.remove_commodity(commodity)

                # Check if commodity is used again and add it to all commodities
                used_commodities = []
                for c in self.pm_object.get_final_conversion_components_objects():
                    inputs = c.get_inputs()
                    for inp in [*inputs.keys()]:
                        if inp not in used_commodities:
                            used_commodities.append(inp)

                    outputs = c.get_outputs()
                    for outp in [*outputs.keys()]:
                        if outp not in used_commodities:
                            used_commodities.append(outp)

                for commodity in used_commodities:
                    if commodity not in self.pm_object.get_final_commodities_names():
                        self.pm_object.activate_commodity(commodity)

                me_balance_window.destroy()

                self.parent.parent.parent.pm_object_copy = self.pm_object
                self.parent.parent.parent.update_widgets()

        def kill_only_me_balance_window():
            me_balance_window.destroy()

        def adjust_input(number_to_adjust):

            input_commodity_to_adjust = input_commodities[number_to_adjust]
            coefficient_to_adjust = input_coefficients[number_to_adjust]

            def change_input_entry():
                if input_radiobutton_var.get() == 'existing':
                    combobox_existing_commodity_input.config(state=NORMAL)

                    input_commodity_name_entry.config(state=DISABLED)
                    input_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_commodity_input.config(state=DISABLED)
                    input_commodity_name_entry.config(state=NORMAL)
                    input_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                if input_radiobutton_var.get() == 'existing':

                    if combobox_existing_commodity_input.get() in self.current_names:
                        for name in self.current_names:
                            if name == combobox_existing_commodity_input.get():
                                commodity = name

                        for n, commodity_n in enumerate(current_inputs):
                            if commodity_n == input_commodity_to_adjust:
                                current_inputs[n] = commodity
                    else:  # Case that commodity does not exist yet
                        commodity = combobox_existing_commodity_input.get()

                        for n, commodity_n in enumerate(current_inputs):
                            if commodity_n == input_commodity_to_adjust:
                                current_inputs[n] = commodity

                        self.current_names.append(commodity)
                        self.current_units[commodity] = self.pm_object.get_commodity(commodity).get_unit()

                    for n, commodity_n in enumerate(current_inputs):
                        if commodity_n == input_commodity_to_adjust:
                            current_inputs[n] = commodity

                else:
                    commodity = input_commodity_name_entry.get()
                    for n, commodity_n in enumerate(current_inputs):
                        if commodity_n == input_commodity_to_adjust:
                            current_inputs[n] = commodity

                    self.current_names.append(input_commodity_name_entry.get())
                    self.current_units[commodity] = input_unit_entry.get()

                    self.commodities_add_conversion_names.append(input_commodity_name_entry.get())

                current_input_coefficients[commodity] = coefficient_entry_var.get()

                adjust_input_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if input_radiobutton_var.get() == 'new':
                    if input_commodity_name_entry.get() in self.commodities_add_conversion_names:
                        self.commodities_add_conversion_names.remove(input_commodity_name_entry.get())

                adjust_input_window.destroy()
                me_balance_window.grab_set()

            adjust_input_window = Toplevel()
            adjust_input_window.title('Adjust Input')
            adjust_input_window.grab_set()

            input_radiobutton_var = StringVar()
            input_radiobutton_var.set('existing')
            input_radiobutton_existing = ttk.Radiobutton(adjust_input_window, text='Existing commodity',
                                                         variable=input_radiobutton_var,
                                                         value='existing', command=change_input_entry)
            input_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_commodity_input = ttk.Combobox(adjust_input_window,
                                                             values=self.commodities_add_conversion_names,
                                                             state='readonly')
            combobox_existing_commodity_input.grid(row=2, column=0, sticky='ew')
            combobox_existing_commodity_input.set(input_commodity_to_adjust)

            input_radiobutton_new = ttk.Radiobutton(adjust_input_window, text='New commodity',
                                                    variable=input_radiobutton_var, value='new',
                                                    command=change_input_entry)
            input_radiobutton_new.grid(row=3, column=0, sticky='ew')

            input_commodity_name_entry = ttk.Entry(
                adjust_input_window)  # todo: make sure that new commodities have not the name of components or other commodities
            input_commodity_name_entry.insert(END, 'Name')
            input_commodity_name_entry.config(state=DISABLED)
            input_commodity_name_entry.grid(row=4, column=0, sticky='ew')

            input_unit_entry = ttk.Entry(adjust_input_window)
            input_unit_entry.insert(END, 'Unit')
            input_unit_entry.config(state=DISABLED)
            input_unit_entry.grid(row=5, column=0, sticky='ew')

            coefficient_entry_var = DoubleVar()
            coefficient_entry_var.set(coefficient_to_adjust)
            ttk.Label(adjust_input_window, text='Coefficient').grid(row=6, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(adjust_input_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=7, column=0, columnspan=3, sticky='ew')

            adjust_input_button_frame = ttk.Frame(adjust_input_window)

            ttk.Button(adjust_input_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(adjust_input_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            adjust_input_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            adjust_input_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            adjust_input_button_frame.grid(row=8, column=0, sticky='ew')

        def adjust_output(number_to_adjust):

            output_commodity_to_adjust = output_commodities[number_to_adjust]
            coefficient_to_adjust = output_coefficients[number_to_adjust]

            def change_output_entry():
                if output_radiobutton_var.get() == 'existing':
                    combobox_existing_commodity_output.config(state=NORMAL)

                    output_commodity_name_entry.config(state=DISABLED)
                    output_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_commodity_output.config(state=DISABLED)
                    output_commodity_name_entry.config(state=NORMAL)
                    output_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                if output_radiobutton_var.get() == 'existing':
                    if combobox_existing_commodity_output.get() in self.current_names:
                        for name in self.current_names:
                            if name == combobox_existing_commodity_output.get():
                                commodity = name

                        for n, commodity_n in enumerate(current_outputs):
                            if commodity_n == output_commodity_to_adjust:
                                current_outputs[n] = commodity
                    else:
                        commodity = self.pm_object.get_abbreviation(combobox_existing_commodity_output.get())

                        for n, commodity_n in enumerate(current_outputs):
                            if commodity_n == output_commodity_to_adjust:
                                current_outputs[n] = commodity

                        self.current_names.append(self.pm_object.get_name(commodity))
                        self.current_units[commodity] = self.pm_object.get_commodity(commodity).get_unit()

                else:
                    commodity = output_commodity_name_entry.get()
                    for n, commodity_n in enumerate(current_outputs):
                        if commodity_n == output_commodity_to_adjust:
                            current_outputs[n] = commodity

                    self.current_names.append(output_commodity_name_entry.get())
                    self.current_units[commodity] = output_unit_entry.get()

                    self.commodities_add_conversion_names.append(output_commodity_name_entry.get())

                current_output_coefficients[commodity] = coefficient_entry_var.get()

                adjust_output_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if output_radiobutton_var.get() == 'new':
                    if output_commodity_name_entry.get() in self.commodities_add_conversion_names:
                        self.commodities_add_conversion_names.remove(output_commodity_name_entry.get())

                adjust_output_window.destroy()
                me_balance_window.grab_set()

            adjust_output_window = Toplevel()
            adjust_output_window.title('Adjust Output')
            adjust_output_window.grab_set()

            output_radiobutton_var = StringVar()
            output_radiobutton_var.set('existing')
            output_radiobutton_existing = ttk.Radiobutton(adjust_output_window, text='Existing commodity',
                                                          variable=output_radiobutton_var,
                                                          value='existing', command=change_output_entry)
            output_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_commodity_output = ttk.Combobox(adjust_output_window,
                                                              values=self.commodities_add_conversion_names,
                                                              state='readonly')
            combobox_existing_commodity_output.grid(row=2, column=0, sticky='ew')
            combobox_existing_commodity_output.set(output_commodity_to_adjust)

            output_radiobutton_new = ttk.Radiobutton(adjust_output_window, text='New commodity',
                                                     variable=output_radiobutton_var, value='new',
                                                     command=change_output_entry)
            output_radiobutton_new.grid(row=3, column=0, sticky='ew')

            output_commodity_name_entry = ttk.Entry(adjust_output_window)
            output_commodity_name_entry.insert(END, 'Name')
            output_commodity_name_entry.config(state=DISABLED)
            output_commodity_name_entry.grid(row=4, column=0, sticky='ew')

            output_unit_entry = ttk.Entry(adjust_output_window)
            output_unit_entry.insert(END, 'Unit')
            output_unit_entry.config(state=DISABLED)
            output_unit_entry.grid(row=5, column=0, sticky='ew')

            coefficient_entry_var = DoubleVar()
            coefficient_entry_var.set(coefficient_to_adjust)
            ttk.Label(adjust_output_window, text='Coefficient').grid(row=6, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(adjust_output_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=7, column=0, columnspan=3, sticky='ew')

            adjust_output_button_frame = ttk.Frame(adjust_output_window)

            ttk.Button(adjust_output_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(adjust_output_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            adjust_output_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            adjust_output_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            adjust_output_button_frame.grid(row=8, column=0, sticky='ew')

        def delete_input():

            def delete_and_kill():

                for ind_choice in [*choice.keys()]:
                    if choice[ind_choice].get():
                        current_inputs.remove(input_commodities[ind_choice])

                delete_input_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():
                delete_input_window.destroy()
                me_balance_window.grab_set()

            delete_input_window = Toplevel()
            delete_input_window.title('Delete Input')
            delete_input_window.grab_set()

            choice = {}

            d = 0
            for ind in [*input_commodities.keys()]:
                choice[ind] = BooleanVar()
                ttk.Checkbutton(delete_input_window, text=input_commodities[ind],
                                variable=choice[ind]).grid(row=d, columnspan=2, sticky='ew')

                d += 1

            ttk.Button(delete_input_window, text='Delete', command=delete_and_kill).grid(row=d, column=0)
            ttk.Button(delete_input_window, text='Cancel', command=kill_only).grid(row=d, column=1)

        def delete_output():

            def delete_and_kill():

                for ind_choice in [*choice.keys()]:
                    if choice[ind_choice].get():
                        current_outputs.remove(output_commodities[ind_choice])

                delete_output_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():
                delete_output_window.destroy()
                me_balance_window.grab_set()

            delete_output_window = Toplevel()
            delete_output_window.title('Delete Output')
            delete_output_window.grab_set()

            choice = {}

            d = 0
            for ind in [*output_commodities.keys()]:
                choice[ind] = BooleanVar()
                ttk.Checkbutton(delete_output_window, text=output_commodities[ind],
                                variable=choice[ind]).grid(row=d, columnspan=2, sticky='ew')

                d += 1

            ttk.Button(delete_output_window, text='Delete', command=delete_and_kill).grid(row=d, column=0)
            ttk.Button(delete_output_window, text='Cancel', command=kill_only).grid(row=d, column=1)

        def add_input():

            def change_input_entry():
                if input_radiobutton_var.get() == 'existing':
                    combobox_existing_commodity_input.config(state=NORMAL)

                    input_commodity_name_entry.config(state=DISABLED)
                    input_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_commodity_input.config(state=DISABLED)
                    input_commodity_name_entry.config(state=NORMAL)
                    input_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                if input_radiobutton_var.get() == 'existing':

                    commodity = None
                    if combobox_existing_commodity_input.get() in self.current_names:
                        for name in self.current_names:
                            if name == combobox_existing_commodity_input.get():
                                commodity = name
                    else:
                        commodity = self.pm_object.get_abbreviation(combobox_existing_commodity_input.get())

                        self.current_units[commodity] = self.pm_object.get_commodity(commodity).get_unit()
                        self.current_names.append(commodity)

                    current_inputs.append(commodity)

                else:
                    commodity = input_commodity_name_entry.get()
                    current_inputs.append(commodity)
                    self.current_units[commodity] = input_unit_entry.get()
                    self.current_names.append(input_commodity_name_entry.get())
                    self.commodities_add_conversion_names.append(input_commodity_name_entry.get())

                current_input_coefficients[commodity] = coefficient_entry_var.get()

                add_input_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if input_radiobutton_var.get() == 'new':
                    if input_commodity_name_entry.get() in self.commodities_add_conversion_names:
                        self.commodities_add_conversion_names.remove(input_commodity_name_entry.get())

                add_input_window.destroy()
                me_balance_window.grab_set()

            add_input_window = Toplevel()
            add_input_window.title('Add Input')
            add_input_window.grab_set()

            input_radiobutton_var = StringVar()
            input_radiobutton_var.set('existing')
            input_radiobutton_existing = ttk.Radiobutton(add_input_window, text='Existing commodity',
                                                         variable=input_radiobutton_var,
                                                         value='existing', command=change_input_entry)
            input_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_commodity_input = ttk.Combobox(add_input_window,
                                                             values=self.commodities_add_conversion_names,
                                                             state='readonly')
            combobox_existing_commodity_input.grid(row=2, column=0, sticky='ew')
            combobox_existing_commodity_input.set('')

            input_radiobutton_new = ttk.Radiobutton(add_input_window, text='New commodity',
                                                    variable=input_radiobutton_var, value='new',
                                                    command=change_input_entry)
            input_radiobutton_new.grid(row=3, column=0, sticky='ew')

            input_commodity_name_entry = ttk.Entry(add_input_window)
            input_commodity_name_entry.insert(END, 'Nice Name')
            input_commodity_name_entry.config(state=DISABLED)
            input_commodity_name_entry.grid(row=4, column=0, sticky='ew')

            input_unit_entry = ttk.Entry(add_input_window)
            input_unit_entry.insert(END, 'Unit')
            input_unit_entry.config(state=DISABLED)
            input_unit_entry.grid(row=5, column=0, sticky='ew')

            coefficient_entry_var = DoubleVar()
            coefficient_entry_var.set(1.0)
            ttk.Label(add_input_window, text='Coefficient').grid(row=6, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(add_input_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=7, column=0, columnspan=1, sticky='ew')

            add_input_button_frame = ttk.Frame(add_input_window)

            ttk.Button(add_input_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(add_input_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            add_input_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            add_input_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            add_input_button_frame.grid(row=8, column=0, sticky='ew')

        def add_output():

            def change_output_entry():
                if output_radiobutton_var.get() == 'existing':
                    combobox_existing_commodity_output.config(state=NORMAL)

                    output_commodity_name_entry.config(state=DISABLED)
                    output_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_commodity_output.config(state=DISABLED)
                    output_commodity_name_entry.config(state=NORMAL)
                    output_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                commodity = None
                if output_radiobutton_var.get() == 'existing':
                    if combobox_existing_commodity_output.get() in self.current_names:
                        for name in self.current_names:
                            if name == combobox_existing_commodity_output.get():
                                commodity = name
                    else:
                        commodity = self.pm_object.get_abbreviation(combobox_existing_commodity_output.get())

                        self.current_units[commodity] = self.pm_object.get_commodity(commodity).get_unit()
                        self.current_names.append(commodity)

                    current_outputs.append(commodity)

                else:
                    commodity = output_commodity_name_entry.get()
                    current_outputs.append(commodity)
                    self.current_units[commodity] = output_unit_entry.get()
                    self.current_names.append(output_commodity_name_entry.get())
                    self.commodities_add_conversion_names.append(output_commodity_name_entry.get())

                current_output_coefficients[commodity] = coefficient_entry_var.get()

                add_output_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if output_radiobutton_var.get() == 'new':
                    if output_commodity_name_entry.get() in self.commodities_add_conversion_names:
                        self.commodities_add_conversion_names.remove(output_commodity_name_entry.get())

                add_output_window.destroy()
                me_balance_window.grab_set()

            add_output_window = Toplevel()
            add_output_window.title('Add Output')
            add_output_window.grab_set()

            output_radiobutton_var = StringVar()
            output_radiobutton_var.set('existing')
            output_radiobutton_existing = ttk.Radiobutton(add_output_window, text='Existing commodity',
                                                          variable=output_radiobutton_var,
                                                          value='existing', command=change_output_entry)
            output_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_commodity_output = ttk.Combobox(add_output_window,
                                                              values=self.commodities_add_conversion_names,
                                                              state='readonly')
            combobox_existing_commodity_output.grid(row=2, column=0, sticky='ew')
            combobox_existing_commodity_output.set('')

            output_radiobutton_new = ttk.Radiobutton(add_output_window, text='New commodity',
                                                     variable=output_radiobutton_var, value='new',
                                                     command=change_output_entry)
            output_radiobutton_new.grid(row=3, column=0, sticky='ew')

            output_commodity_name_entry = ttk.Entry(add_output_window)
            output_commodity_name_entry.insert(END, 'Name')
            output_commodity_name_entry.config(state=DISABLED)
            output_commodity_name_entry.grid(row=4, column=0, sticky='ew')

            output_unit_entry = ttk.Entry(add_output_window)
            output_unit_entry.insert(END, 'Unit')
            output_unit_entry.config(state=DISABLED)
            output_unit_entry.grid(row=5, column=0, sticky='ew')

            coefficient_entry_var = DoubleVar()
            coefficient_entry_var.set(1.0)
            ttk.Label(add_output_window, text='Coefficient').grid(row=6, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(add_output_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=7, column=0, columnspan=3, sticky='ew')

            add_output_button_frame = ttk.Frame(add_output_window)

            ttk.Button(add_output_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(add_output_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            add_output_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            add_output_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            add_output_button_frame.grid(row=8, column=0, sticky='ew')

        def update_me_balance_window():

            # delete widgets
            for child in me_balance_window.winfo_children():
                child.destroy()

            update_input_frame = ttk.Frame(me_balance_window)

            ''' Create ME balance which is adjusted '''
            # Inputs
            ttk.Label(update_input_frame, text='Inputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5,
                                                                                        sticky='ew')

            ttk.Label(update_input_frame, text='Main').grid(row=1, column=1, sticky='ew')
            ttk.Label(update_input_frame, text='Coefficient').grid(row=1, column=2, sticky='ew')
            ttk.Label(update_input_frame, text='Unit').grid(row=1, column=3, sticky='ew')
            ttk.Label(update_input_frame, text='Commodity').grid(row=1, column=4, sticky='ew')

            ui = 2
            for update_input_commodity in current_inputs:
                input_commodities[ui] = update_input_commodity

                ttk.Button(update_input_frame, text='Adjust',
                           command=lambda ui=ui: adjust_input(ui)).grid(row=ui, column=0, sticky='ew')

                update_coefficient = current_input_coefficients[update_input_commodity]
                input_coefficients[ui] = update_coefficient

                update_unit = self.current_units[update_input_commodity]
                input_commodities[ui] = update_input_commodity

                ttk.Radiobutton(update_input_frame, variable=current_main_input_var, value=update_input_commodity).grid(
                    row=ui, column=1, sticky='ew')
                ttk.Label(update_input_frame, text=update_coefficient).grid(row=ui, column=2, sticky='ew')
                ttk.Label(update_input_frame, text=update_unit).grid(row=ui, column=3, sticky='ew')
                ttk.Label(update_input_frame, text=update_input_commodity).grid(row=ui, column=4, sticky='ew')

                ui += 1

            update_input_frame.grid(row=0, column=0, sticky='new')

            update_output_frame = ttk.Frame(me_balance_window)

            # Outputs
            ttk.Label(update_output_frame, text='Outputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5,
                                                                                          sticky='ew')

            ttk.Label(update_output_frame, text='Main').grid(row=1, column=1, sticky='ew')
            ttk.Label(update_output_frame, text='Coefficient').grid(row=1, column=2, sticky='ew')
            ttk.Label(update_output_frame, text='Unit').grid(row=1, column=3, sticky='ew')
            ttk.Label(update_output_frame, text='Commodity').grid(row=1, column=4, sticky='ew')

            uj = 2
            for update_output_commodity in current_outputs:
                output_commodities[uj] = update_output_commodity

                ttk.Button(update_output_frame, text='Adjust',
                           command=lambda uj=uj: adjust_output(uj)).grid(row=uj, column=0, sticky='ew')

                update_coefficient = current_output_coefficients[update_output_commodity]
                output_coefficients[uj] = update_coefficient

                update_unit = self.current_units[update_output_commodity]
                output_commodities[uj] = update_output_commodity

                update_rb = ttk.Radiobutton(update_output_frame, variable=current_main_output_var,
                                            value=update_output_commodity)
                update_rb.grid(row=uj, column=1, sticky='ew')
                ttk.Label(update_output_frame, text=update_coefficient).grid(row=uj, column=2, sticky='ew')
                ttk.Label(update_output_frame, text=update_unit).grid(row=uj, column=3, sticky='ew')
                ttk.Label(update_output_frame, text=update_output_commodity).grid(row=uj, column=4, sticky='ew')

                uj += 1

            update_output_frame.grid(row=0, column=2, sticky='new')

            if ui >= uj:
                ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=i + 1, column=1, sticky=N + S)
            else:
                ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=j + 1, column=1, sticky=N + S)

            me_balance_window.grid_columnconfigure(0, weight=1, uniform='a')
            me_balance_window.grid_columnconfigure(1, weight=0)
            me_balance_window.grid_columnconfigure(2, weight=1, uniform='a')

            update_button_frame = ttk.Frame(me_balance_window)

            update_button_frame.grid_columnconfigure(0, weight=1)
            update_button_frame.grid_columnconfigure(1, weight=1)

            ttk.Button(update_button_frame, text='Add Input',
                       command=add_input).grid(row=0, column=0, sticky=W + E)
            ttk.Button(update_button_frame, text='Add Output',
                       command=add_output).grid(row=0, column=1, sticky=W + E)

            ttk.Button(update_button_frame, text='Delete Input',
                       command=delete_input).grid(row=1, column=0, sticky=W + E)
            ttk.Button(update_button_frame, text='Delete Output',
                       command=delete_output).grid(row=1, column=1, sticky=W + E)
            ttk.Button(update_button_frame, text='Ok',
                       command=get_values_and_kill_me_balance_window).grid(row=2, column=0, sticky=W + E)
            ttk.Button(update_button_frame, text='Cancel',
                       command=kill_only_me_balance_window).grid(row=2, column=1, sticky=W + E)

            if ui >= uj:
                update_button_frame.grid(row=ui, column=0, columnspan=3, sticky='ew')
            else:
                update_button_frame.grid(row=uj, column=0, columnspan=3, sticky='ew')

        me_balance_window = Toplevel()
        me_balance_window.title('Adjust Mass Energy Balance')
        me_balance_window.grab_set()

        input_frame = ttk.Frame(me_balance_window)

        """ Recreate exact ME balance as in conversion unit frame """

        # Get the information from main conversion ME balance
        main_input_var = StringVar()
        current_inputs = []
        current_input_main = str
        current_input_coefficients = {}

        main_output_var = StringVar()
        current_outputs = []
        current_output_main = str
        current_output_coefficients = {}

        i = 2
        inputs = self.component_object.get_inputs()
        for input_commodity in [*inputs.keys()]:

            coefficient = inputs[input_commodity]

            if input_commodity == self.component_object.get_main_input():
                main_input_var.set(input_commodity)
                current_input_main = input_commodity

            current_inputs.append(input_commodity)
            current_input_coefficients.update({input_commodity: coefficient})

            i += 1

        j = 2
        outputs = self.component_object.get_outputs()
        for output_commodity in [*outputs.keys()]:

            coefficient = outputs[output_commodity]

            if output_commodity == self.component_object.get_main_output():
                main_output_var.set(output_commodity)
                current_output_main = output_commodity

            current_outputs.append(output_commodity)
            current_output_coefficients.update({output_commodity: coefficient})

            j += 1

        # Inputs
        ttk.Label(input_frame, text='Inputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5)

        ttk.Label(input_frame, text='Main').grid(row=1, column=1)
        ttk.Label(input_frame, text='Coefficient').grid(row=1, column=2)
        ttk.Label(input_frame, text='Unit').grid(row=1, column=3)
        ttk.Label(input_frame, text='Commodity').grid(row=1, column=4)

        input_commodities = {}
        input_coefficients = {}

        current_main_input_var = StringVar()
        current_main_input_var.set(current_input_main)

        i = 2
        for input_commodity in current_inputs:
            input_commodities[i] = input_commodity

            ttk.Button(input_frame, text='Adjust',
                       command=lambda i=i: adjust_input(i)).grid(row=i, column=0)

            coefficient = current_input_coefficients[input_commodity]
            input_coefficients[i] = coefficient

            unit = self.current_units[input_commodity]

            ttk.Radiobutton(input_frame, variable=current_main_input_var, value=input_commodity).grid(row=i, column=1)
            ttk.Label(input_frame, text=coefficient).grid(row=i, column=2)
            ttk.Label(input_frame, text=unit).grid(row=i, column=3)
            ttk.Label(input_frame, text=input_commodity).grid(row=i, column=4)

            i += 1

        input_frame.grid(row=0, column=0, sticky='new')

        output_frame = ttk.Frame(me_balance_window)

        # Outputs
        ttk.Label(output_frame, text='Outputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5)

        ttk.Label(output_frame, text='Main').grid(row=1, column=1)
        ttk.Label(output_frame, text='Coefficient').grid(row=1, column=2)
        ttk.Label(output_frame, text='Unit').grid(row=1, column=3)
        ttk.Label(output_frame, text='Commodity').grid(row=1, column=4)

        output_commodities = {}
        output_coefficients = {}

        current_main_output_var = StringVar()
        current_main_output_var.set(current_output_main)

        j = 2
        for output_commodity in current_outputs:
            output_commodities[j] = output_commodity

            ttk.Button(output_frame, text='Adjust',
                       command=lambda j=j: adjust_output(j)).grid(row=j, column=0)

            coefficient = current_output_coefficients[output_commodity]
            output_coefficients[j] = coefficient

            unit = self.current_units[output_commodity]

            rb = ttk.Radiobutton(output_frame, variable=current_main_output_var, value=output_commodity)
            rb.grid(row=j, column=1)
            ttk.Label(output_frame, text=coefficient).grid(row=j, column=2)
            ttk.Label(output_frame, text=unit).grid(row=j, column=3)
            ttk.Label(output_frame, text=output_commodity).grid(row=j, column=4)

            j += 1

        output_frame.grid(row=0, column=2, sticky='new')

        if i >= j:
            ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=i + 1, column=1, sticky=N + S)
        else:
            ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=j + 1, column=1, sticky=N + S)

        me_balance_window.grid_columnconfigure(0, weight=1, uniform='a')
        me_balance_window.grid_columnconfigure(1, weight=0)
        me_balance_window.grid_columnconfigure(2, weight=1, uniform='a')

        button_frame = ttk.Frame(me_balance_window)

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        ttk.Button(button_frame, text='Add Input',
                   command=add_input).grid(row=0, column=0, sticky=W + E)
        ttk.Button(button_frame, text='Add Output',
                   command=add_output).grid(row=0, column=1, sticky=W + E)

        ttk.Button(button_frame, text='Delete Input',
                   command=delete_input).grid(row=1, column=0, sticky=W + E)
        ttk.Button(button_frame, text='Delete Output',
                   command=delete_output).grid(row=1, column=1, sticky=W + E)
        ttk.Button(button_frame, text='Ok',
                   command=get_values_and_kill_me_balance_window).grid(row=2, column=0, sticky=W + E)
        ttk.Button(button_frame, text='Cancel',
                   command=kill_only_me_balance_window).grid(row=2, column=1, sticky=W + E)

        if i >= j:
            button_frame.grid(row=i, column=0, columnspan=3, sticky='ew')
        else:
            button_frame.grid(row=j, column=0, columnspan=3, sticky='ew')

        me_balance_window.mainloop()

    def __init__(self, parent, super_frame, component, pm_object, pm_object_original):

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component

        self.frame = ttk.Frame(super_frame)

        self.component_object = self.pm_object.get_component(self.component)

        self.commodities_add_conversion_names = []
        for s in self.pm_object.get_all_commodities():
            self.commodities_add_conversion_names.append(s)

        self.input_frame = ttk.Frame(self.frame)

        # Inputs
        ttk.Label(self.input_frame, text='Inputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=4,
                                                                                  sticky='ew')

        ttk.Label(self.input_frame, text='Main').grid(row=1, column=0, sticky='ew')
        ttk.Label(self.input_frame, text='Coefficient').grid(row=1, column=1, sticky='ew')
        ttk.Label(self.input_frame, text='Unit').grid(row=1, column=2, sticky='ew')
        ttk.Label(self.input_frame, text='Commodity').grid(row=1, column=3, sticky='ew')

        self.current_names = []
        self.current_units = {}

        for s in [*self.pm_object.get_all_commodities().values()]:
            self.current_names.append(s.get_name())
            self.current_units.update({s.get_name(): s.get_unit()})

        i = 2
        inputs = self.component_object.get_inputs()
        for input_commodity in [*inputs.keys()]:

            coefficient = inputs[input_commodity]
            unit = self.pm_object.get_commodity(input_commodity).get_unit()
            commodity_name = input_commodity

            if input_commodity == self.component_object.get_main_input():
                ttk.Label(self.input_frame, text='X').grid(row=i, column=0)
            else:
                ttk.Label(self.input_frame, text='').grid(row=i, column=0)

            ttk.Label(self.input_frame, text=coefficient).grid(row=i, column=1, sticky='ew')
            ttk.Label(self.input_frame, text=unit).grid(row=i, column=2, sticky='ew')
            ttk.Label(self.input_frame, text=commodity_name).grid(row=i, column=3, sticky='ew')

            i += 1

        # Outputs
        self.output_frame = ttk.Frame(self.frame)

        ttk.Label(self.output_frame, text='Outputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=4,
                                                                                    sticky='ew')

        ttk.Label(self.output_frame, text='Main').grid(row=1, column=0, sticky='ew')
        ttk.Label(self.output_frame, text='Coefficient').grid(row=1, column=1, sticky='ew')
        ttk.Label(self.output_frame, text='Unit').grid(row=1, column=2, sticky='ew')
        ttk.Label(self.output_frame, text='Commodity').grid(row=1, column=3, sticky='ew')

        j = 2
        outputs = self.component_object.get_outputs()
        for output_commodity in [*outputs.keys()]:

            coefficient = outputs[output_commodity]
            unit = self.pm_object.get_commodity(output_commodity).get_unit()
            commodity_name = output_commodity

            if output_commodity == self.component_object.get_main_output():
                ttk.Label(self.output_frame, text='X').grid(row=j, column=0)
            else:
                ttk.Label(self.output_frame, text='').grid(row=j, column=0)

            ttk.Label(self.output_frame, text=coefficient).grid(row=j, column=1, sticky='ew')
            ttk.Label(self.output_frame, text=unit).grid(row=j, column=2, sticky='ew')
            ttk.Label(self.output_frame, text=commodity_name).grid(row=j, column=3, sticky='ew')

            j += 1

        self.frame.grid_columnconfigure(0, weight=1, uniform="a")
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1, uniform="a")

        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.input_frame.grid_columnconfigure(2, weight=1)
        self.input_frame.grid_columnconfigure(3, weight=1)

        self.input_frame.grid(row=0, column=0, sticky='new')

        if i >= j:
            ttk.Separator(self.frame, orient='vertical').grid(row=0, rowspan=2, column=1, sticky=N + S)
        else:
            ttk.Separator(self.frame, orient='vertical').grid(row=0, rowspan=2, column=1, sticky=N + S)

        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(2, weight=1)
        self.output_frame.grid_columnconfigure(3, weight=1)

        self.output_frame.grid(row=0, column=2, sticky='new')

        button_frame = ttk.Frame(self.frame)

        button_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(button_frame, text='Adjust Inputs/Outputs',
                   command=self.create_me_balance_window).grid(row=0, column=0, sticky=W + E)

        if i >= j:
            button_frame.grid(row=2, column=0, columnspan=3, sticky='ew')
        else:
            button_frame.grid(row=2, column=0, columnspan=3, sticky='ew')
