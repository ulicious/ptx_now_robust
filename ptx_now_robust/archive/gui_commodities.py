import tkinter as tk
from tkinter import ttk
from tkinter import *
from copy import deepcopy


class CommodityFrame:

    def adjust_values(self):
        AdjustCommodityWindow(self, self.pm_object, self.commodity)

    def set_commodity_settings_to_default(self):

        self.pm_object.remove_commodity_entirely(self.commodity)

        commodity_original = self.pm_object_original.get_commodity(self.commodity)
        self.pm_object.add_commodity(self.commodity, commodity_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def create_widgets_in_frame(self):
        for child_parameters in self.frame.winfo_children():
            child_parameters.destroy()

        self.initialize_commodity()

        tk.Label(self.frame, text='').grid(row=0, column=0, sticky='w')
        tk.Label(self.frame, text='Configuration').grid(row=0, column=1, sticky='w')
        tk.Label(self.frame, text='Specific CO2 emissions [t / ' + self.commodity_object.get_unit() + ']').grid(row=0,
                                                                                                                column=2,
                                                                                                                sticky='w')

        i = 1

        tk.Label(self.frame, text='Commodity freely available?').grid(row=i, column=0, sticky='w')
        if self.available_var.get():
            text_dummy = 'Yes'
            specific_emissions = self.specific_co2_emissions_available_var.get()
        else:
            text_dummy = 'No'
            specific_emissions = ''

        tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')
        tk.Label(self.frame, text=specific_emissions).grid(row=i, column=2, sticky='w')

        i += 1

        tk.Label(self.frame, text='Commodity purchasable?').grid(row=i, column=0, sticky='w')
        if self.purchasable_var.get():
            text_dummy = 'Yes'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')

            text_purchase_price = str(self.commodity_object.get_purchase_price())
            text_purchase_price_unit = self.monetary_unit + ' / ' + self.commodity_object.get_unit()

            tk.Label(self.frame, text='Purchase price type:').grid(row=i + 1, column=0, sticky='w')
            if self.purchase_price_type_var.get() == 'fixed':
                text = 'Fixed price at: ' + text_purchase_price + ' ' + text_purchase_price_unit
                specific_emissions = self.specific_co2_emissions_purchase_var.get()
            else:
                text = 'Variable price [see profile data]'
                specific_emissions = 'Variable emissions [see profile data]'

            tk.Label(self.frame, text=text).grid(row=i + 1, column=1, sticky='w')
            tk.Label(self.frame, text=specific_emissions).grid(row=i + 1, column=2, sticky='w')

            i += 2
        else:
            text_dummy = 'No'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')

            specific_emissions = ''
            tk.Label(self.frame, text=specific_emissions).grid(row=i + 1, column=2, sticky='w')

            i += 1

        tk.Label(self.frame, text='Excess commodity emitted?').grid(row=i, column=0, sticky='w')
        if self.emitted_var.get():
            text_dummy = 'Yes'
            specific_emissions = self.specific_co2_emissions_emitted_var.get()
        else:
            text_dummy = 'No'
            specific_emissions = ''

        tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')
        tk.Label(self.frame, text=specific_emissions).grid(row=i, column=2, sticky='w')
        i += 1

        tk.Label(self.frame, text='Commodity saleable?').grid(row=i, column=0, sticky='w')
        if self.saleable_var.get():
            text_dummy = 'Yes'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')

            text_sale_price = str(self.commodity_object.get_sale_price())
            text_sale_price_unit = self.monetary_unit + ' / ' + self.commodity_object.get_unit()

            tk.Label(self.frame, text='Sale price type:').grid(row=i + 1, column=0, sticky='w')
            if self.sale_price_type_var.get() == 'fixed':
                text = 'Fixed price at: ' + text_sale_price + ' ' + text_sale_price_unit
                specific_emissions = self.specific_co2_emissions_sale_var.get()
            else:
                text = 'Variable price [see profile data]'
                specific_emissions = 'Variable emissions [see profile data]'

            tk.Label(self.frame, text=text).grid(row=i + 1, column=1, sticky='w')
            tk.Label(self.frame, text=specific_emissions).grid(row=i + 1, column=2, sticky='w')

            i += 2
        else:
            text_dummy = 'No'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')
            tk.Label(self.frame, text='').grid(row=i + 1, column=2, sticky='w')

            i += 1

        tk.Label(self.frame, text='Commodity demanded?').grid(row=i, column=0, sticky='w')
        if self.demand_var.get():
            text_dummy = 'Yes'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')
            tk.Label(self.frame, text='Demand type').grid(row=i + 1, column=0, sticky='w')

            if self.demand_type_var.get() == 'fixed':

                if not self.total_demand_var.get():

                    if self.commodity_object.get_unit() == 'MWh':
                        unit_new = 'MW'
                    elif self.commodity_object.get_unit() == 'GWh':
                        unit_new = 'GW'
                    elif self.commodity_object.get_unit() == 'kWh':
                        unit_new = 'kW'
                    else:
                        unit_new = self.commodity_object.get_unit() + ' / h'

                    text = 'Hourly fixed demand of: ' + self.demand_text_var.get() + ' ' + unit_new
                    tk.Label(self.frame, text=text).grid(row=i + 1, column=1, sticky='w')
                else:
                    text = 'Total demand of: ' + self.demand_text_var.get() + ' ' + self.commodity_object.get_unit()
                    tk.Label(self.frame, text=text).grid(row=i + 1, column=1, sticky='w')

                i += 2

            else:
                tk.Label(self.frame, text='Hourly variable demand [see profile]').grid(row=i + 1, column=1, sticky='w')

                i += 2

        else:
            text_dummy = 'No'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1, sticky='w')

            i += 1

        i += 1

        energy_units = ['kWh', 'MWh', 'GWh', 'kJ', 'MJ', 'GJ']
        if not self.commodity_object.get_unit() in energy_units:
            ttk.Label(self.frame, text='Energy content:').grid(row=i, column=0, sticky='w')
            ttk.Label(self.frame, text=self.energy_content_var.get() + ' MWh/' + self.commodity_object.get_unit()) \
                .grid(row=i, column=1, sticky='w')

            i += 1

        button_frame = ttk.Frame(self.frame)
        ttk.Button(button_frame, text='Adjust Commodity', command=self.adjust_values) \
            .grid(row=0, columnspan=3, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid(row=i, columnspan=3, sticky='ew')

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

    def initialize_commodity(self):

        if self.commodity_object.is_available():
            self.available_var.set(True)
            self.specific_co2_emissions_available_var.set(self.commodity_object.get_specific_co2_emissions_available())
        else:
            self.available_var.set(False)
            self.specific_co2_emissions_available_var.set(0)

        if self.commodity_object.is_purchasable():

            self.purchasable_var.set(True)
            self.purchase_price_type_var.set(self.commodity_object.get_purchase_price_type())

            if self.commodity_object.get_purchase_price_type() == 'fixed':
                self.purchase_price_fixed_text_var.set(self.commodity_object.get_purchase_price())
                self.specific_co2_emissions_purchase_var.set(
                    self.commodity_object.get_specific_co2_emissions_purchase())
        else:
            self.purchasable_var.set(False)
            self.purchase_price_type_var.set(self.commodity_object.get_purchase_price_type())
            self.specific_co2_emissions_purchase_var.set(0)

        if self.commodity_object.is_emittable():
            self.emitted_var.set(True)
            self.specific_co2_emissions_emitted_var.set(self.commodity_object.get_specific_co2_emissions_emitted())
        else:
            self.emitted_var.set(False)
            self.specific_co2_emissions_emitted_var.set(0)

        if self.commodity_object.is_saleable():
            self.saleable_var.set(True)
            if self.commodity_object.get_sale_price_type() == 'fixed':
                self.sale_price_type_var.set('fixed')
                self.sale_price_fixed_text_var.set(self.commodity_object.get_sale_price())
                self.specific_co2_emissions_sale_var.set(
                    self.commodity_object.get_specific_co2_emissions_sale())

        else:
            self.saleable_var.set(False)
            self.sale_price_type_var.set('fixed')
            self.specific_co2_emissions_sale_var.set(0)

        if self.commodity_object.is_demanded():
            self.demand_var.set(True)
        else:
            self.demand_var.set(False)

        if self.commodity_object.get_demand_type() == 'fixed':

            if self.commodity_object.is_total_demand():
                self.total_demand_var.set(True)
            else:
                self.total_demand_var.set(False)

        else:
            self.total_demand_var.set(False)

        self.demand_text_var.set(self.commodity_object.get_demand())
        self.demand_type_var.set(self.commodity_object.get_demand_type())

        self.energy_content_var.set(self.commodity_object.get_energy_content())

    def __init__(self, parent, frame, commodity, pm_object, pm_object_original):

        self.parent = parent
        self.frame = ttk.Frame(frame)
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.commodity = commodity
        self.commodity_object = self.pm_object.get_commodity(self.commodity)
        self.monetary_unit = self.pm_object.get_monetary_unit()

        self.available_var = tk.BooleanVar()
        self.specific_co2_emissions_available_var = tk.DoubleVar()

        self.emitted_var = tk.BooleanVar()
        self.specific_co2_emissions_emitted_var = tk.DoubleVar()

        self.purchasable_var = tk.BooleanVar()
        self.purchase_price_type_var = tk.StringVar()
        self.purchase_price_fixed_text_var = tk.StringVar()
        self.specific_co2_emissions_purchase_var = tk.DoubleVar()

        self.saleable_var = tk.BooleanVar()
        self.sale_price_type_var = tk.StringVar()
        self.sale_price_fixed_text_var = tk.StringVar()
        self.specific_co2_emissions_sale_var = tk.DoubleVar()

        self.demand_var = tk.BooleanVar()
        self.total_demand_var = tk.BooleanVar()
        self.demand_text_var = StringVar()
        self.demand_type_var = StringVar()

        self.energy_content_var = StringVar()

        self.profile_var = StringVar()
        self.textvar_profile = StringVar()
        self.profile_needed = BooleanVar()

        self.create_widgets_in_frame()


class AdjustCommodityWindow:

    def create_widgets_in_frame(self):

        self.initialize_commodity()

        basic_setting_frame = ttk.Frame(self.newWindow)

        self.specific_co2_emissions_available_label = ttk.Label(basic_setting_frame,
                                                                text='Specific CO2 emissions [t / ' + self.commodity_object.get_unit() + ']')
        self.specific_co2_emissions_available_label.grid(row=0, column=1, sticky='ew')

        ttk.Checkbutton(basic_setting_frame, text='Freely available', variable=self.available_var, onvalue=True,
                        offvalue=False, command=self.configure_available).grid(row=1, column=0, sticky='ew')
        self.specific_co2_emissions_available_entry = Entry(basic_setting_frame,
                                                            text=self.specific_co2_emissions_available)
        self.specific_co2_emissions_available_entry.grid(row=1, column=1, sticky='ew')

        ttk.Checkbutton(basic_setting_frame, text='Emitted', variable=self.emitted_var, onvalue=True,
                        offvalue=False, command=self.configure_emitted).grid(row=2, column=0, sticky='ew')

        self.specific_co2_emissions_emitted_entry = Entry(basic_setting_frame,
                                                          text=self.specific_co2_emissions_emitted)
        self.specific_co2_emissions_emitted_entry.grid(row=2, column=1, sticky='ew')

        basic_setting_frame.grid_columnconfigure(0, weight=1)
        basic_setting_frame.grid_columnconfigure(1, weight=1)
        basic_setting_frame.grid_columnconfigure(2, weight=1)

        basic_setting_frame.grid(row=0, columnspan=3, sticky='ew')

        ttk.Separator(self.newWindow).grid(row=1, columnspan=3, sticky='ew')

        ttk.Checkbutton(self.newWindow, text='Purchasable', variable=self.purchasable_var, onvalue=True, offvalue=False,
                        command=self.configure_purchase) \
            .grid(row=2, column=0, rowspan=3, sticky='w')

        self.purchase_fixed_price_radiobutton.config(
            text='Fixed price [' + self.monetary_unit + ' / ' + self.commodity_object.get_unit() + ']',
            variable=self.purchase_price_type_var, value='fixed',
            command=self.configure_purchase)
        self.purchase_fixed_price_radiobutton.grid(row=2, column=1, sticky='w')

        self.purchase_fixed_price_entry.config(text=self.purchase_price_fixed_text_var)
        self.purchase_fixed_price_entry.grid(row=3, column=1, sticky='ew')

        self.specific_co2_emissions_purchase_label.config(
            text='Specific CO2 emissions [t / ' + self.commodity_object.get_unit() + ']')
        self.specific_co2_emissions_purchase_label.grid(row=2, column=2, sticky='w')
        self.specific_co2_emissions_purchase_entry.config(text=self.specific_co2_emissions_purchase)
        self.specific_co2_emissions_purchase_entry.grid(row=3, column=2, sticky='ew')

        self.purchase_variable_radiobutton.config(text='Price curve',
                                                  variable=self.purchase_price_type_var, value='variable',
                                                  command=self.configure_purchase)
        self.purchase_variable_radiobutton.grid(row=4, column=1, sticky='w')

        ttk.Separator(self.newWindow).grid(row=5, columnspan=3, sticky='ew')

        ttk.Checkbutton(self.newWindow, text='Saleable', variable=self.saleable_var,
                        onvalue=True, offvalue=False, command=self.configure_sale) \
            .grid(row=6, column=0, rowspan=3, sticky='w')

        self.sale_fixed_price_radiobutton.config(
            text='Fixed price [' + self.monetary_unit + ' / ' + self.commodity_object.get_unit() + ']',
            variable=self.sale_price_type_var, value='fixed',
            command=self.configure_sale)
        self.sale_fixed_price_radiobutton.grid(row=6, column=1, sticky='w')

        self.sale_fixed_price_entry.config(text=self.sale_price_fixed_text_var)
        self.sale_fixed_price_entry.grid(row=7, column=1, sticky='ew')

        self.specific_co2_emissions_sale_label.config(
            text='Specific CO2 emissions [t / ' + self.commodity_object.get_unit() + ']')
        self.specific_co2_emissions_sale_label.grid(row=6, column=2, sticky='w')
        self.specific_co2_emissions_sale_entry.config(text=self.specific_co2_emissions_sale)
        self.specific_co2_emissions_sale_entry.grid(row=7, column=2, sticky='ew')

        self.sale_variable_radiobutton.config(text='Price curve',
                                              variable=self.sale_price_type_var,
                                              value='variable',
                                              command=self.configure_sale)
        self.sale_variable_radiobutton.grid(row=8, column=1, sticky='w')

        ttk.Separator(self.newWindow).grid(row=9, columnspan=3, sticky='ew')

        demand_cb = ttk.Checkbutton(self.newWindow, text='Demand', variable=self.demand_var, onvalue=True,
                                    offvalue=False, command=self.configure_demand)
        demand_cb.grid(row=10, rowspan=3, column=0, sticky='w')

        text_total = 'Fixed Total Demand [' + self.commodity_object.get_unit() + ']'
        if self.commodity_object.get_unit() == 'MWh':
            unit = 'MW'
            text_hourly = 'Fixed Hourly Demand [' + unit + ']'
        elif self.commodity_object.get_unit() == 'GWh':
            unit = 'GW'
            text_hourly = 'Fixed Hourly Demand [' + unit + ']'
        elif self.commodity_object.get_unit() == 'kWh':
            unit = 'kW'
            text_hourly = 'Fixed Hourly Demand [' + unit + ']'
        else:
            unit = self.commodity_object.get_unit()
            text_hourly = 'Fixed Hourly Demand [' + unit + ' / h]'

        self.demand_type_fixed_hourly_radiobutton.config(
            text=text_hourly,
            variable=self.demand_type_var, value='fixed_hourly',
            command=self.configure_demand)
        self.demand_type_fixed_hourly_radiobutton.grid(row=10, column=1, sticky='w')

        self.demand_type_fixed_total_radiobutton.config(
            text=text_total,
            variable=self.demand_type_var, value='fixed_total',
            command=self.configure_demand)
        self.demand_type_fixed_total_radiobutton.grid(row=11, column=1, sticky='w')

        self.fixed_demand_entry.config(text=self.demand_text_var)
        self.fixed_demand_entry.grid(row=10, rowspan=2, column=2, sticky='ew')

        self.demand_type_variable_radiobutton.config(text='Variable Demand',
                                                     variable=self.demand_type_var,
                                                     value='variable',
                                                     command=self.configure_demand)
        self.demand_type_variable_radiobutton.grid(row=12, column=1, sticky='w')

        ttk.Separator(self.newWindow).grid(row=13, columnspan=3, sticky='ew')
        ttk.Label(self.newWindow, text='Energy content').grid(row=14, column=0, sticky='w')
        ttk.Entry(self.newWindow, textvariable=self.energy_content_var).grid(row=14, column=1, sticky='w')
        ttk.Label(self.newWindow, text='MWh/' + self.commodity_object.get_unit()).grid(row=14, column=2, sticky='w')
        i = 2

        ttk.Label(self.newWindow, text='Commodity Name').grid(row=14 + i, column=0, sticky='w')
        name_entry = ttk.Entry(self.newWindow, textvariable=self.name_var)
        name_entry.grid(row=14 + i, column=1, sticky='w')

        ttk.Label(self.newWindow, text='Commodity Unit').grid(row=15 + i, column=0, sticky='w')
        unit_entry = ttk.Entry(self.newWindow, textvariable=self.unit_var)
        unit_entry.grid(row=15 + i, column=1, sticky='w')

        i += 2

        button_frame = ttk.Frame(self.newWindow)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(button_frame, text='Ok', command=self.safe_values) \
            .grid(row=0, column=0, sticky='ew')
        ttk.Button(button_frame, text='Cancel', command=self.kill_only) \
            .grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=14 + i, columnspan=3, sticky='ew')

        self.configure_available()
        self.configure_emitted()
        self.configure_purchase()
        self.configure_sale()
        self.configure_demand()

    def initialize_commodity(self):

        if self.commodity_object.is_available():
            self.available_var.set(True)
        else:
            self.available_var.set(False)

        self.specific_co2_emissions_available.set(self.commodity_object.get_specific_co2_emissions_available())

        self.purchase_price_type_var.set(self.commodity_object.get_purchase_price_type())
        if self.commodity_object.is_purchasable():
            self.purchasable_var.set(True)
            if self.commodity_object.get_purchase_price_type() == 'fixed':
                self.purchase_price_type_var.set('fixed')
                self.purchase_price_fixed_text_var.set(self.commodity_object.get_purchase_price())
                self.specific_co2_emissions_purchase.set(self.commodity_object.get_specific_co2_emissions_purchase())
            else:
                self.purchase_price_type_var.set('variable')
        else:
            self.purchasable_var.set(False)

        if self.commodity_object.is_emittable():
            self.emitted_var.set(True)
        else:
            self.emitted_var.set(False)

        self.specific_co2_emissions_emitted.set(self.commodity_object.get_specific_co2_emissions_emitted())

        self.sale_price_type_var.set(self.commodity_object.get_sale_price_type())
        if self.commodity_object.is_saleable():
            self.saleable_var.set(True)
            if self.commodity_object.get_sale_price_type() == 'fixed':
                self.sale_price_type_var.set('fixed')
                self.sale_price_fixed_text_var.set(self.commodity_object.get_sale_price())
                self.specific_co2_emissions_sale.set(self.commodity_object.get_specific_co2_emissions_sale())
            else:
                self.sale_price_type_var.set('variable')
        else:
            self.saleable_var.set(False)

        if self.commodity_object.is_demanded():
            self.demand_var.set(True)
        else:
            self.demand_var.set(False)

        if self.commodity_object.get_demand_type() == 'fixed':
            if not self.commodity_object.is_total_demand():
                self.demand_type_var.set('fixed_hourly')
            else:
                self.demand_type_var.set('fixed_total')
        else:
            self.demand_type_var.set('variable')

        self.demand_text_var.set(self.commodity_object.get_demand())

        self.energy_content_var.set(self.commodity_object.get_energy_content())

        self.name_var.set(self.commodity_object.get_name())
        self.unit_var.set(self.commodity_object.get_unit())

    def configure_available(self):
        if self.available_var.get():
            self.specific_co2_emissions_available_entry.config(state=NORMAL)
            self.specific_co2_emissions_available_label.config(state=NORMAL)
        else:
            self.specific_co2_emissions_available_entry.config(state=DISABLED)

            if self.emitted_var.get():
                self.specific_co2_emissions_available_label.config(state=NORMAL)
            else:
                self.specific_co2_emissions_available_label.config(state=DISABLED)

    def configure_emitted(self):
        if self.emitted_var.get():
            self.specific_co2_emissions_emitted_entry.config(state=NORMAL)
        else:
            self.specific_co2_emissions_emitted_entry.config(state=DISABLED)

            if self.available_var.get():
                self.specific_co2_emissions_available_label.config(state=NORMAL)
            else:
                self.specific_co2_emissions_available_label.config(state=DISABLED)

    def configure_purchase(self):
        if self.purchasable_var.get():
            self.purchase_fixed_price_radiobutton.config(state=NORMAL)
            self.purchase_variable_radiobutton.config(state=NORMAL)

            if self.purchase_price_type_var.get() == 'fixed':
                self.purchase_fixed_price_entry.config(state=NORMAL)
                self.specific_co2_emissions_purchase_entry.config(state=NORMAL)
                self.specific_co2_emissions_purchase_label.config(state=NORMAL)
            else:
                self.purchase_fixed_price_entry.config(state=DISABLED)
                self.specific_co2_emissions_purchase_entry.config(state=DISABLED)
                self.specific_co2_emissions_purchase_label.config(state=DISABLED)

        else:
            self.purchase_fixed_price_radiobutton.config(state=DISABLED)
            self.purchase_variable_radiobutton.config(state=DISABLED)
            self.purchase_fixed_price_entry.config(state=DISABLED)
            self.specific_co2_emissions_purchase_entry.config(state=DISABLED)
            self.specific_co2_emissions_purchase_label.config(state=DISABLED)

    def configure_sale(self):
        if self.saleable_var.get():
            self.sale_fixed_price_radiobutton.config(state=NORMAL)
            self.sale_variable_radiobutton.config(state=NORMAL)

            if self.sale_price_type_var.get() == 'fixed':
                self.sale_fixed_price_entry.config(state=NORMAL)
                self.specific_co2_emissions_sale_entry.config(state=NORMAL)
                self.specific_co2_emissions_sale_label.config(state=NORMAL)
            else:
                self.sale_fixed_price_entry.config(state=DISABLED)
                self.specific_co2_emissions_sale_entry.config(state=DISABLED)
                self.specific_co2_emissions_sale_label.config(state=DISABLED)
        else:
            self.sale_fixed_price_radiobutton.config(state=DISABLED)
            self.sale_fixed_price_entry.config(state=DISABLED)
            self.sale_variable_radiobutton.config(state=DISABLED)
            self.specific_co2_emissions_sale_entry.config(state=DISABLED)
            self.specific_co2_emissions_sale_label.config(state=DISABLED)

    def configure_demand(self):
        if not self.demand_var.get():
            self.demand_type_fixed_hourly_radiobutton.config(state=DISABLED)
            self.demand_type_fixed_total_radiobutton.config(state=DISABLED)
            self.demand_type_variable_radiobutton.config(state=DISABLED)
            self.fixed_demand_entry.config(state=DISABLED)
        else:
            self.demand_type_fixed_hourly_radiobutton.config(state=NORMAL)
            self.demand_type_fixed_total_radiobutton.config(state=NORMAL)
            self.demand_type_variable_radiobutton.config(state=NORMAL)

            self.fixed_demand_entry.config(state=NORMAL)

            if self.demand_type_var.get() == 'variable':
                self.fixed_demand_entry.config(state=DISABLED)

    def kill_only(self):
        self.newWindow.destroy()

    def safe_values(self):

        # Set availability settings
        if self.available_var.get():
            self.commodity_object.set_available(True)
            self.commodity_object.set_specific_co2_emissions_available(self.specific_co2_emissions_available.get())
        else:
            self.commodity_object.set_available(False)

        # Set purchase settings
        if self.purchasable_var.get():
            self.commodity_object.set_purchasable(True)

            if self.purchase_price_type_var.get() == 'fixed':
                self.commodity_object.set_purchase_price_type('fixed')
                self.commodity_object.set_specific_co2_emissions_purchase(self.specific_co2_emissions_purchase.get())
            else:
                self.commodity_object.set_purchase_price_type('variable')
        else:
            self.commodity_object.set_purchasable(False)

        # Set emittable settings
        if self.emitted_var.get():
            self.commodity_object.set_emittable(True)
            self.commodity_object.set_specific_co2_emissions_emitted(self.specific_co2_emissions_emitted.get())
        else:
            self.commodity_object.set_emittable(False)

        # Set selling settings
        if self.saleable_var.get():
            self.commodity_object.set_saleable(True)
            if self.sale_price_type_var.get() == 'fixed':
                self.commodity_object.set_sale_price_type('fixed')
                self.commodity_object.set_specific_co2_emissions_sale(self.specific_co2_emissions_sale.get())
            else:
                self.commodity_object.set_sale_price_type('variable')
        else:
            self.commodity_object.set_saleable(False)

        # Set demand settings
        if self.demand_var.get():
            self.commodity_object.set_demanded(True)
            if self.demand_type_var.get() == 'fixed_hourly':
                self.commodity_object.set_demand_type('fixed')
                self.commodity_object.set_demand(self.fixed_demand_entry.get())
                self.commodity_object.set_total_demand(False)
            elif self.demand_type_var.get() == 'fixed_total':
                self.commodity_object.set_demand_type('fixed')
                self.commodity_object.set_demand(self.fixed_demand_entry.get())
                self.commodity_object.set_total_demand(True)
            else:
                self.commodity_object.set_demand_type('variable')
        else:
            self.commodity_object.set_demanded(False)

        if self.purchasable_var.get():
            if self.purchase_price_type_var.get() == 'fixed':
                self.commodity_object.set_purchase_price(float(self.purchase_fixed_price_entry.get()))

        if self.saleable_var.get():
            if self.sale_price_type_var.get() == 'fixed':
                self.commodity_object.set_sale_price(float(self.sale_fixed_price_entry.get()))

        self.commodity_object.set_energy_content(float(self.energy_content_var.get()))

        self.commodity_object.set_unit(self.unit_var.get())

        if self.commodity != self.name_var.get():
            new_commodity = deepcopy(self.commodity_object)
            new_commodity.set_name(self.name_var.get())
            self.commodity_object.set_final(False)
            self.pm_object.adjust_commodity(self.commodity, new_commodity)

        self.pm_object.check_commodity_data_needed()

        self.parent.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.parent.update_widgets()

        self.newWindow.destroy()

    def __init__(self, parent, pm_object, commodity):

        self.parent = parent
        self.pm_object = pm_object
        self.commodity = commodity
        self.commodity_object = self.pm_object.get_commodity(self.commodity)
        self.monetary_unit = self.pm_object.get_monetary_unit()

        self.newWindow = Toplevel()
        self.newWindow.title('Adjust Commodity Parameters')
        self.newWindow.grab_set()

        # variables
        self.specific_co2_emissions_available = DoubleVar()
        self.specific_co2_emissions_emitted = DoubleVar()

        self.purchasable_var = BooleanVar()
        self.purchase_price_type_var = StringVar()
        self.purchase_price_fixed_text_var = StringVar()
        self.purchase_price_curve_text_var = StringVar()
        self.specific_co2_emissions_purchase = DoubleVar()

        self.saleable_var = BooleanVar()
        self.sale_price_type_var = StringVar()
        self.sale_price_fixed_text_var = StringVar()
        self.sale_price_curve_text_var = StringVar()
        self.specific_co2_emissions_sale = DoubleVar()

        self.available_var = BooleanVar()
        self.emitted_var = BooleanVar()
        self.demand_var = BooleanVar()
        self.demand_type_var = StringVar()

        self.demand_text_var = StringVar()

        self.energy_content_var = StringVar()

        self.name_var = StringVar()
        self.unit_var = StringVar()

        # widgets
        self.specific_co2_emissions_available_entry = None
        self.specific_co2_emissions_emitted_entry = None
        self.specific_co2_emissions_available_label = None

        self.purchase_fixed_price_radiobutton = ttk.Radiobutton(self.newWindow)
        self.purchase_variable_radiobutton = ttk.Radiobutton(self.newWindow)
        self.purchase_fixed_price_entry = ttk.Entry(self.newWindow)
        self.specific_co2_emissions_purchase_entry = ttk.Entry(self.newWindow)
        self.specific_co2_emissions_purchase_label = tk.Label(self.newWindow)

        self.sale_fixed_price_radiobutton = ttk.Radiobutton(self.newWindow)
        self.sale_variable_radiobutton = ttk.Radiobutton(self.newWindow)
        self.sale_fixed_price_entry = ttk.Entry(self.newWindow)
        self.specific_co2_emissions_sale_entry = ttk.Entry(self.newWindow)
        self.specific_co2_emissions_sale_label = tk.Label(self.newWindow)

        self.fixed_demand_entry = ttk.Entry(self.newWindow)
        self.demand_type_fixed_hourly_radiobutton = ttk.Radiobutton(self.newWindow)
        self.demand_type_fixed_total_radiobutton = ttk.Radiobutton(self.newWindow)
        self.demand_type_variable_radiobutton = ttk.Radiobutton(self.newWindow)

        self.create_widgets_in_frame()
