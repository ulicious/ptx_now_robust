import tkinter as tk
from tkinter import ttk
from tkinter import *


class StorageFrame:

    def adjust_values(self):

        def safe_adjustments():

            self.storage_object.set_capex(self.capex_entry_var.get())
            self.storage_object.set_fixed_OM(str(float(self.fixed_om_entry_var.get()) / 100))
            self.storage_object.set_variable_OM(str(float(self.variable_om_entry_var.get())))
            self.storage_object.set_lifetime(self.lifetime_entry_var.get())
            self.storage_object.set_charging_efficiency(str(float(self.charging_entry_var.get()) / 100))
            self.storage_object.set_discharging_efficiency(str(float(self.discharging_entry_var.get()) / 100))
            self.storage_object.set_min_soc(str(float(self.min_soc_entry_var.get()) / 100))
            self.storage_object.set_max_soc(str(float(self.max_soc_entry_var.get()) / 100))
            self.storage_object.set_ratio_capacity_p(self.ratio_capacity_p_entry_var.get())
            self.storage_object.set_has_fixed_capacity(self.has_fixed_capacity_var.get())
            self.storage_object.set_fixed_capacity(self.fixed_capacity_var.get())
            self.storage_object.set_installation_co2_emissions(self.installation_co2_emissions_var.get())
            self.storage_object.set_fixed_co2_emissions(self.fixed_co2_emissions_var.get())
            self.storage_object.set_variable_co2_emissions(self.variable_co2_emissions_var.get())
            self.storage_object.set_disposal_co2_emissions(self.disposal_co2_emissions_var.get())

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            newWindow.destroy()

        def change_fixed_capacity():
            if self.has_fixed_capacity_var.get():
                fixed_capacity_entry.config(state=NORMAL)
            else:
                fixed_capacity_entry.config(state=DISABLED)

        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel()
        newWindow.title('Adjust Storage')
        newWindow.grab_set()

        newWindow.grid_columnconfigure(0, weight=1)
        newWindow.grid_columnconfigure(1, weight=1)
        newWindow.grid_columnconfigure(2, weight=1)

        commodity = self.pm_object.get_commodity(self.commodity)
        commodity_unit = commodity.get_unit()

        tk.Label(newWindow, text='CAPEX [' + self.monetary_unit + '/' + commodity_unit + ']').grid(row=0, column=0,
                                                                                                sticky='w')
        capex_entry = tk.Entry(newWindow, text=self.capex_entry_var)
        capex_entry.grid(row=0, column=1, sticky='ew')

        tk.Label(newWindow, text='Fixed O&M [%]').grid(row=1, column=0, sticky='w')
        fixed_om_entry = tk.Entry(newWindow, text=self.fixed_om_entry_var)
        fixed_om_entry.grid(row=1, column=1, sticky='ew')

        tk.Label(newWindow, text='Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + commodity_unit + ']').grid(row=2, column=0, sticky='w')
        variable_om_entry = tk.Entry(newWindow, text=self.variable_om_entry_var)
        variable_om_entry.grid(row=2, column=1, sticky='ew')

        tk.Label(newWindow, text='Lifetime [Years]').grid(row=3, column=0, sticky='w')
        lifetime_entry = tk.Entry(newWindow, text=self.lifetime_entry_var)
        lifetime_entry.grid(row=3, column=1, sticky='ew')

        tk.Label(newWindow, text='Charging efficiency [%]').grid(row=4, column=0, sticky='w')
        charging_entry = tk.Entry(newWindow, text=self.charging_entry_var)
        charging_entry.grid(row=4, column=1, sticky='ew')

        tk.Label(newWindow, text='Discharging efficiency [%]').grid(row=5, column=0, sticky='w')
        discharging_entry = tk.Entry(newWindow, text=self.discharging_entry_var)
        discharging_entry.grid(row=5, column=1, sticky='ew')

        tk.Label(newWindow, text='Minimal SOC [%]').grid(row=6, column=0, sticky='w')
        min_soc_entry = tk.Entry(newWindow, text=self.min_soc_entry_var)
        min_soc_entry.grid(row=6, column=1, sticky='ew')

        tk.Label(newWindow, text='Maximal SOC [%]').grid(row=7, column=0, sticky='w')
        max_soc_entry = tk.Entry(newWindow, text=self.max_soc_entry_var)
        max_soc_entry.grid(row=7, column=1, sticky='ew')

        ttk.Label(newWindow, text='Ratio between storage capacity and power [hours]').grid(row=8, column=0, sticky='w')
        ratio_capacity_p_entry = tk.Entry(newWindow, text=self.ratio_capacity_p_entry_var)
        ratio_capacity_p_entry.grid(row=8, column=1, sticky='ew')

        if self.has_fixed_capacity_var.get():
            fixed_capacity_state = NORMAL
        else:
            fixed_capacity_state = DISABLED

        ttk.Checkbutton(newWindow, text='Use fixed capacity?', variable=self.has_fixed_capacity_var,
                        command=change_fixed_capacity).grid(row=9, column=0, sticky='w')
        ttk.Label(newWindow, text='Fixed capacity [' + commodity_unit + ']').grid(row=10, column=0, sticky='w')
        fixed_capacity_entry = ttk.Entry(newWindow, text=self.fixed_capacity_var, state=fixed_capacity_state)
        fixed_capacity_entry.grid(row=10, column=1, sticky='w')

        ttk.Label(newWindow, text='Specific CO2 emissions [t CO2 / ' + commodity_unit + ']').grid(row=11, column=0,
                                                                                                  sticky='w')
        installation_co2_emissions_entry = tk.Entry(newWindow, text=self.installation_co2_emissions_var)
        installation_co2_emissions_entry.grid(row=11, column=1, sticky='ew')

        ttk.Label(newWindow, text='Fixed CO2 emissions [t CO2 / ' + commodity_unit + ' / a]').grid(row=12, column=0,
                                                                                                   sticky='w')
        fixed_co2_emissions_entry = tk.Entry(newWindow, text=self.fixed_co2_emissions_var)
        fixed_co2_emissions_entry.grid(row=12, column=1, sticky='ew')

        ttk.Label(newWindow, text='Variable CO2 emissions [t CO2 / ' + commodity_unit + ']').grid(row=13, column=0,
                                                                                                  sticky='w')
        variable_co2_emissions_entry = tk.Entry(newWindow, text=self.variable_co2_emissions_var)
        variable_co2_emissions_entry.grid(row=13, column=1, sticky='ew')

        ttk.Label(newWindow, text='Disposal CO2 emissions [t CO2 / ' + commodity_unit + ']').grid(row=14, column=0,
                                                                                                  sticky='w')
        disposal_co2_emissions_entry = tk.Entry(newWindow, text=self.disposal_co2_emissions_var)
        disposal_co2_emissions_entry.grid(row=14, column=1, sticky='ew')

        button_frame = ttk.Frame(newWindow)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(button_frame, text='Ok', command=safe_adjustments).grid(row=0, column=0, sticky='ew')
        ttk.Button(button_frame, text='Cancel', command=kill_only).grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=15, columnspan=2, sticky='ew')

    def set_storage_settings_to_default(self):

        self.pm_object.remove_component_entirely(self.commodity)
        storage_original = self.pm_object_original.get_component(self.commodity)
        self.pm_object.add_component(self.commodity, storage_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def create_storage(self):

        # Set storage settings
        # Check if storage object exits but is not set

        if self.storable_var.get():
            self.storage_object.set_final(True)
            self.state = NORMAL

        else:
            self.storage_object.set_final(False)
            self.state = DISABLED

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def initialize_storage_frame(self):

        self.storable_checkbox.config(text='Storage available?')
        self.storable_checkbox.grid(row=0, column=0, sticky='w')

        storage = self.pm_object.get_component(self.commodity)

        self.capex = storage.get_capex()
        self.fixed_om = round(100 * storage.get_fixed_OM(), 2)
        self.variable_om = storage.get_variable_OM()
        self.lifetime = storage.get_lifetime()
        self.charging_efficiency = 100 * float(storage.get_charging_efficiency())
        self.discharging_efficiency = 100 * float(storage.get_discharging_efficiency())
        self.min_soc = 100 * float(storage.get_min_soc())
        self.max_soc = 100 * float(storage.get_max_soc())
        self.ratio_capacity_p = storage.get_ratio_capacity_p()
        self.has_fixed_capacity = storage.get_has_fixed_capacity()
        self.fixed_capacity = storage.get_fixed_capacity()
        self.installation_co2_emissions = storage.get_installation_co2_emissions()
        self.fixed_co2_emissions = storage.get_fixed_co2_emissions()
        self.variable_co2_emissions = storage.get_variable_co2_emissions()
        self.disposal_co2_emissions = storage.get_disposal_co2_emissions()

        self.capex_entry_var.set(self.capex)
        self.fixed_om_entry_var.set(self.fixed_om)
        self.variable_om_entry_var.set(self.variable_om)
        self.lifetime_entry_var.set(self.lifetime)
        self.charging_entry_var.set(self.charging_efficiency)
        self.discharging_entry_var.set(self.discharging_efficiency)
        self.min_soc_entry_var.set(self.min_soc)
        self.max_soc_entry_var.set(self.max_soc)
        self.ratio_capacity_p_entry_var.set(self.ratio_capacity_p)
        self.has_fixed_capacity_var.set(self.has_fixed_capacity)
        self.fixed_capacity_var.set(self.fixed_capacity)
        self.installation_co2_emissions_var.set(self.installation_co2_emissions)
        self.fixed_co2_emissions_var.set(self.fixed_co2_emissions)
        self.variable_co2_emissions_var.set(self.variable_co2_emissions)
        self.disposal_co2_emissions_var.set(self.disposal_co2_emissions)

        commodity = self.pm_object.get_commodity(self.commodity)
        commodity_unit = commodity.get_unit()

        ttk.Label(self.frame, text='CAPEX [' + self.monetary_unit + '/' + commodity_unit + ']',
                  state=self.state).grid(row=1, column=0, sticky='w')
        self.capex_label.config(text=self.capex_entry_var.get(), state=self.state)
        self.capex_label.grid(row=1, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed O&M [%]', state=self.state).grid(row=2, column=0, sticky='w')
        self.fixed_om_label.config(text=self.fixed_om_entry_var.get(), state=self.state)
        self.fixed_om_label.grid(row=2, column=1, sticky='w')

        ttk.Label(self.frame, text='Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + commodity_unit + ']',
                 state=self.state).grid(row=3, column=0, sticky='w')
        self.variable_om_label.config(text=self.variable_om_entry_var.get(), state=self.state)
        self.variable_om_label.grid(row=3, column=1, sticky='w')

        ttk.Label(self.frame, text='Lifetime [years]', state=self.state).grid(row=4, column=0, sticky='w')
        self.lifetime_label.config(text=self.lifetime_entry_var.get(), state=self.state)
        self.lifetime_label.grid(row=4, column=1, sticky='w')

        ttk.Label(self.frame, text='Charging efficiency [%]', state=self.state).grid(row=5, column=0, sticky='w')
        self.charge_label.config(text=self.charging_entry_var.get(), state=self.state)
        self.charge_label.grid(row=5, column=1, sticky='w')

        ttk.Label(self.frame, text='Discharging efficiency [%]', state=self.state).grid(row=6, column=0, sticky='w')
        self.discharge_label.config(text=self.discharging_entry_var.get(), state=self.state)
        self.discharge_label.grid(row=6, column=1, sticky='w')

        ttk.Label(self.frame, text='Minimal SOC [%]', state=self.state).grid(row=7, column=0, sticky='w')
        self.min_soc_entry.config(text=self.min_soc_entry_var.get(), state=self.state)
        self.min_soc_entry.grid(row=7, column=1, sticky='w')

        ttk.Label(self.frame, text='Maximal SOC [%]', state=self.state).grid(row=8, column=0, sticky='w')
        self.max_soc_entry.config(text=self.max_soc_entry_var.get(), state=self.state)
        self.max_soc_entry.grid(row=8, column=1, sticky='w')

        ttk.Label(self.frame, text='Ratio between capacity and power [hours]', state=self.state).grid(row=9, column=0, sticky='w')
        self.ratio_capacity_p_entry.config(text=self.ratio_capacity_p_entry_var.get(), state=self.state)
        self.ratio_capacity_p_entry.grid(row=9, column=1, sticky='w')

        if self.has_fixed_capacity_var.get():
            ttk.Label(self.frame, text='Fixed capacity [' + commodity_unit + ']', state=self.state).grid(row=10, column=0, sticky='w')
            ttk.Label(self.frame, text=self.fixed_capacity_var.get(), state=self.state).grid(row=10, column=1, sticky='w')

        ttk.Label(self.frame, text='Installation CO2 emissions [t CO2 / ' + commodity_unit + ']',
                  state=self.state).grid(row=11, column=0, sticky='w')
        self.installation_co2_emissions_label.config(text=self.installation_co2_emissions_var.get(), state=self.state)
        self.installation_co2_emissions_label.grid(row=11, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed CO2 emissions [t CO2 / ' + commodity_unit + ' / a]',
                  state=self.state).grid(row=12, column=0, sticky='w')
        self.fixed_co2_emissions_label.config(text=self.fixed_co2_emissions_var.get(), state=self.state)
        self.fixed_co2_emissions_label.grid(row=12, column=1, sticky='w')

        ttk.Label(self.frame, text='Variable CO2 emissions [t CO2 / ' + commodity_unit + ']',
                  state=self.state).grid(row=13, column=0, sticky='w')
        self.variable_co2_emissions_label.config(text=self.variable_co2_emissions_var.get(), state=self.state)
        self.variable_co2_emissions_label.grid(row=13, column=1, sticky='w')

        ttk.Label(self.frame, text='Disposal CO2 emissions [t CO2 / ' + commodity_unit + ']',
                  state=self.state).grid(row=14, column=0, sticky='w')
        self.disposal_co2_emissions_label.config(text=self.disposal_co2_emissions_var.get(), state=self.state)
        self.disposal_co2_emissions_label.grid(row=14, column=1, sticky='w')

        row = 15

        self.button_frame.grid_columnconfigure(0, weight=1)

        self.adjust_value_button.config(text='Adjust Storage', command=self.adjust_values, state=self.state)
        self.adjust_value_button.grid(row=0, column=0, sticky='ew')

        self.button_frame.grid(row=row, columnspan=2, sticky='ew')

    def __init__(self, parent, frame, storage, pm_object, pm_object_original):

        self.parent = parent
        self.frame = frame
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original

        self.monetary_unit = self.pm_object.get_monetary_unit()

        self.frame = ttk.Frame(self.frame)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.storable_var = BooleanVar()
        self.storage_object = self.pm_object.get_component(storage)
        if self.storage_object.is_final():
            self.storable_var.set(True)
        else:
            self.storable_var.set(False)

        self.commodity = self.storage_object.get_name()
        self.commodity_object = self.pm_object.get_commodity(self.commodity)

        self.capex = None
        self.fixed_om = None
        self.variable_om = None
        self.lifetime = None
        self.charging_efficiency = None
        self.discharging_efficiency = None
        self.max_cap = None
        self.min_soc = None
        self.max_soc = None
        self.ratio_capacity_p = None
        self.has_fixed_capacity = None
        self.fixed_capacity = None
        self.installation_co2_emissions = None
        self.fixed_co2_emissions = None
        self.variable_co2_emissions = None
        self.disposal_co2_emissions = None

        self.capex_entry_var = DoubleVar()
        self.fixed_om_entry_var = DoubleVar()
        self.variable_om_entry_var = DoubleVar()
        self.lifetime_entry_var = IntVar()
        self.charging_entry_var = DoubleVar()
        self.discharging_entry_var = DoubleVar()
        self.ratio_capacity_p_entry_var = DoubleVar()
        self.min_soc_entry_var = DoubleVar()
        self.max_soc_entry_var = DoubleVar()
        self.has_fixed_capacity_var = BooleanVar()
        self.fixed_capacity_var = DoubleVar()
        self.installation_co2_emissions_var = DoubleVar()
        self.fixed_co2_emissions_var = DoubleVar()
        self.variable_co2_emissions_var = DoubleVar()
        self.disposal_co2_emissions_var = DoubleVar()

        self.storable_checkbox = ttk.Checkbutton(self.frame, command=self.create_storage, variable=self.storable_var)
        self.capex_label = ttk.Label(self.frame)
        self.fixed_om_label = ttk.Label(self.frame)
        self.variable_om_label = ttk.Label(self.frame)
        self.lifetime_label = ttk.Label(self.frame)
        self.charge_label = ttk.Label(self.frame)
        self.discharge_label = ttk.Label(self.frame)
        self.min_soc_entry = ttk.Label(self.frame)
        self.max_soc_entry = ttk.Label(self.frame)
        self.ratio_capacity_p_entry = ttk.Label(self.frame)
        self.ratio_capacity_p_label = ttk.Label(self.frame)
        self.has_fixed_capacity_checkbutton = ttk.Checkbutton(self.frame)
        self.fixed_capacity_label = ttk.Label(self.frame)
        self.installation_co2_emissions_label = ttk.Label(self.frame)
        self.fixed_co2_emissions_label = ttk.Label(self.frame)
        self.variable_co2_emissions_label = ttk.Label(self.frame)
        self.disposal_co2_emissions_label = ttk.Label(self.frame)

        self.button_frame = ttk.Frame(self.frame)
        self.adjust_value_button = ttk.Button(self.button_frame)
        self.reset_button = ttk.Button(self.button_frame)

        if self.storable_var.get():
            self.state = NORMAL
        else:
            self.state = DISABLED

        self.initialize_storage_frame()
