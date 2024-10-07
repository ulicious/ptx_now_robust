import tkinter as tk
from tkinter import ttk
from tkinter import *


class GeneratorFrame:

    def activate_entry(self):

        if self.checkbox_generator_available_var.get():

            self.pm_object.get_component(self.generator).set_final(True)
            self.state = NORMAL

            if self.uses_ppa_var.get() == 'investment':
                self.state_investment = NORMAL
                self.state_ppa = DISABLED
            else:
                self.state_investment = DISABLED
                self.state_ppa = NORMAL

        else:

            self.pm_object.get_component(self.generator).set_final(False)
            self.state = DISABLED

            self.state_investment = DISABLED
            self.state_ppa = DISABLED

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def adjust_values(self):

        def change_investment_ppa():

            if self.uses_ppa_var.get() == 'investment':
                capex_entry.config(state=NORMAL)
                lifetime_entry.config(state=NORMAL)
                fixed_om_entry.config(state=NORMAL)
                variable_om_entry.config(state=NORMAL)

                ppa_entry.config(state=DISABLED)

            else:
                capex_entry.config(state=DISABLED)
                lifetime_entry.config(state=DISABLED)
                fixed_om_entry.config(state=DISABLED)
                variable_om_entry.config(state=DISABLED)

                ppa_entry.config(state=NORMAL)

        def check_fixed_capacity():

            if self.checkbox_fixed_capacity_var.get():
                fixed_capacity_label.config(state=NORMAL)
                fixed_capacity_entry.config(state=NORMAL)

            else:
                fixed_capacity_label.config(state=DISABLED)
                fixed_capacity_entry.config(state=DISABLED)

        def get_values_and_kill_window():
            generator = self.pm_object.get_component(self.generator)

            if self.uses_ppa_var.get() == 'investment':

                generator.set_uses_ppa(False)

                if capex_entry.get() != '':
                    generator.set_capex(float(capex_entry.get()))
                if lifetime_entry.get() != '':
                    generator.set_lifetime(float(lifetime_entry.get()))
                if fixed_om_entry.get() != '':
                    generator.set_fixed_OM(float(fixed_om_entry.get()) / 100)
                if variable_om_entry.get() != '':
                    generator.set_variable_OM(float(variable_om_entry.get()))
            else:

                generator.set_uses_ppa(True)

                if ppa_entry.get() != '':
                    generator.set_ppa_price(float(ppa_entry.get()))

            generator.set_generated_commodity(generated_commodity_cb.get())

            generator.set_curtailment_possible(self.checkbox_curtailment_var.get())

            generator.set_has_fixed_capacity(self.checkbox_fixed_capacity_var.get())
            generator.set_fixed_capacity(float(fixed_capacity_entry.get()))

            generator.set_installation_co2_emissions(float(installation_co2_emissions_entry.get()))
            generator.set_fixed_co2_emissions(float(fixed_co2_emissions_entry.get()))
            generator.set_variable_co2_emissions(float(variable_co2_emissions_entry.get()))
            generator.set_disposal_co2_emissions(float(disposal_co2_emissions_entry.get()))

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            window.destroy()

        def kill_window():
            window.destroy()

        window = Toplevel(self.frame)
        window.title('Adjust Parameters')
        window.grab_set()

        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(2, weight=1)

        if self.commodity_unit in ['kWh', 'MWh', 'GWh', 'TWh']:
            component_unit = self.commodity_unit[0:2]
        else:
            component_unit = self.commodity_unit + ' / h'

        if self.uses_ppa_var.get() == 'investment':
            state_investment = NORMAL
            state_ppa = DISABLED
        else:
            state_investment = DISABLED
            state_ppa = NORMAL

        radiobutton_uses_investment = ttk.Radiobutton(window, text='Investment', value='investment',
                                                      variable=self.uses_ppa_var, command=change_investment_ppa)
        radiobutton_uses_investment.grid(row=0, column=0, sticky='w')

        tk.Label(window, text='CAPEX [' + self.monetary_unit + '/' + component_unit + ']', state=state_investment).grid(row=1,
                                                                                                column=0,
                                                                                                sticky='w')
        capex_entry = tk.Entry(window, textvariable=self.capex_var, state=state_investment)
        capex_entry.grid(row=1, column=1, sticky='ew')

        tk.Label(window, text='Lifetime [years]', state=state_investment).grid(row=2, column=0, sticky='w')
        lifetime_entry = tk.Entry(window, textvariable=self.lifetime_var, state=state_investment)
        lifetime_entry.grid(row=2, column=1, sticky='ew')

        tk.Label(window, text='Fixed O&M [%]', state=state_investment).grid(row=3, column=0, sticky='w')
        fixed_om_entry = tk.Entry(window, textvariable=self.fixed_om_var, state=state_investment)
        fixed_om_entry.grid(row=3, column=1, sticky='ew')

        tk.Label(window, text='Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + self.commodity_unit + ']', state=state_investment).grid(row=4, column=0, sticky='w')
        variable_om_entry = tk.Entry(window, textvariable=self.variable_om_var, state=state_investment)
        variable_om_entry.grid(row=4, column=1, sticky='ew')

        radiobutton_uses_ppa = ttk.Radiobutton(window, text='PPA', value='ppa',
                                               variable=self.uses_ppa_var, command=change_investment_ppa)
        radiobutton_uses_ppa.grid(row=5, column=0, sticky='w')

        ttk.Label(window, text='PPA price [' + self.monetary_unit + ' / ' + self.commodity_unit + ']').grid(row=6, column=0, sticky='w')
        ppa_entry = ttk.Entry(window, textvariable=self.ppa_price_var, state=state_ppa)
        ppa_entry.grid(row=6, column=1, sticky='w')

        tk.Label(window, text='Generated commodity').grid(row=7, column=0, sticky='w')

        commodities = []
        for commodity in self.pm_object.get_final_commodities_objects():
            commodities.append(commodity.get_name())

        generated_commodity_cb = ttk.Combobox(window, values=commodities, state='readonly')
        generated_commodity_cb.grid(row=7, column=1, sticky='ew')
        generated_commodity_cb.set(self.generated_commodity_var.get())

        curtailment_checkbutton = ttk.Checkbutton(window,
                                                  text='Curtailment possible?',
                                                  variable=self.checkbox_curtailment_var)
        curtailment_checkbutton.grid(row=8, column=0, sticky='ew')

        ttk.Checkbutton(window, text='Fixed Capacity used?', variable=self.checkbox_fixed_capacity_var,
                        command=check_fixed_capacity).grid(row=9, column=0, sticky='ew')

        fixed_capacity_label = ttk.Label(window, text='Fixed Capacity [' + component_unit + ']:')
        fixed_capacity_label.grid(row=10, column=0, sticky='w')
        fixed_capacity_entry = ttk.Entry(window, textvariable=self.fixed_capacity_var)
        fixed_capacity_entry.grid(row=10, column=1, sticky='ew')

        installation_co2_emissions_label = ttk.Label(window,
                                                 text='Installation CO2 emissions [t CO2 / ' + component_unit + ']')
        installation_co2_emissions_label.grid(row=11, column=0, sticky='ew')
        installation_co2_emissions_entry = ttk.Entry(window, textvariable=self.installation_co2_emissions_var)
        installation_co2_emissions_entry.grid(row=11, column=1, sticky='ew')

        fixed_co2_emissions_label = ttk.Label(window, text='Fixed CO2 emissions [t CO2 / ' + component_unit + ' / a]')
        fixed_co2_emissions_label.grid(row=12, column=0, sticky='ew')
        fixed_co2_emissions_entry = ttk.Entry(window, textvariable=self.fixed_co2_emissions_var)
        fixed_co2_emissions_entry.grid(row=12, column=1, sticky='ew')

        variable_co2_emissions_label = ttk.Label(window,
                                                 text='Variable CO2 emissions [t CO2 / ' + self.commodity_unit + ']')
        variable_co2_emissions_label.grid(row=13, column=0, sticky='ew')
        variable_co2_emissions_entry = ttk.Entry(window, textvariable=self.variable_co2_emissions_var)
        variable_co2_emissions_entry.grid(row=13, column=1, sticky='ew')

        disposal_co2_emissions_label = ttk.Label(window,
                                                 text='Disposal CO2 emissions [t CO2 / ' + component_unit + ']')
        disposal_co2_emissions_label.grid(row=14, column=0, sticky='ew')
        disposal_co2_emissions_entry = ttk.Entry(window, textvariable=self.disposal_co2_emissions_var)
        disposal_co2_emissions_entry.grid(row=14, column=1, sticky='ew')

        ttk.Button(window, text='Adjust values', command=get_values_and_kill_window).grid(row=15, column=0,  sticky='ew')

        ttk.Button(window, text='Cancel', command=kill_window).grid(row=15, column=1, sticky='ew')

        window.grid_columnconfigure(0, weight=1, uniform='a')
        window.grid_columnconfigure(1, weight=1, uniform='a')

        check_fixed_capacity()

    def set_generator_settings_to_default(self):

        # Delete all current generators
        for generator in self.pm_object.get_generator_components_names():
            self.pm_object.remove_component_entirely(generator)

        # Get all generators from original pm object
        for self.generator in self.pm_object_original.get_generator_components_names():
            generator_original = self.pm_object_original.get_component(self.generator)
            self.pm_object.add_component(self.generator, generator_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def initialize_generator_frame(self):

        if self.commodity_unit in ['kWh', 'MWh', 'GWh', 'TWh']:
            component_unit = self.commodity_unit[0:2]
        else:
            component_unit = self.commodity_unit + ' / h'

        self.checkbox_generator_available.config(text='Generator available', onvalue=True, offvalue=False, variable=self.checkbox_generator_available_var,
                                                 command=self.activate_entry)
        self.checkbox_generator_available.grid(row=0, columnspan=2, sticky='w')

        ttk.Label(self.frame, text='CAPEX [' + self.monetary_unit + '/' + component_unit + ']', state=self.state_investment)\
            .grid(row=1, column=0, sticky='w')
        self.capex_label.config(text=self.capex_var.get(), state=self.state_investment)
        self.capex_label.grid(row=1, column=1, sticky='w')

        ttk.Label(self.frame, text='Lifetime [Years]', state=self.state_investment).grid(row=2, column=0, sticky='w')
        self.lifetime_label.config(text=self.lifetime_var.get(), state=self.state_investment)
        self.lifetime_label.grid(row=2, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed O&M [%]', state=self.state_investment).grid(row=3, column=0, sticky='w')
        self.fixed_om_label.config(text=self.fixed_om_var.get(), state=self.state_investment)
        self.fixed_om_label.grid(row=3, column=1, sticky='w')

        ttk.Label(self.frame,
                  text='Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + self.commodity_unit + ']',
                  state=self.state_investment).grid(row=4, column=0, sticky='w')
        self.variable_om_label.config(text=self.variable_om_var.get(), state=self.state_investment)
        self.variable_om_label.grid(row=4, column=1, sticky='w')

        ttk.Label(self.frame,
                  text='PPA price [' + self.pm_object.get_monetary_unit() + ' / ' + self.commodity_unit + ']',
                  state=self.state_ppa).grid(row=5, column=0, sticky='w')
        self.ppa_price_label.config(text=self.ppa_price_var.get(), state=self.state_ppa)
        self.ppa_price_label.grid(row=5, column=1, sticky='w')

        ttk.Label(self.frame, text='Generated commodity', state=self.state).grid(row=6, column=0, sticky='w')
        self.generated_commodity_label.config(text=self.generated_commodity_var.get(), state=self.state)
        self.generated_commodity_label.grid(row=6, column=1, sticky='w')

        ttk.Label(self.frame, text='Curtailment possible: ', state=self.state).grid(row=7, column=0, sticky='w')
        if self.checkbox_curtailment_var.get():
            text_curtailment = 'Yes'
        else:
            text_curtailment = 'No'

        self.curtailment_label.config(text=text_curtailment, state=self.state)
        self.curtailment_label.grid(row=7, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed Capacity [' + self.commodity_unit + ']: ', state=self.state)\
            .grid(row=8, column=0, sticky='w')
        if self.checkbox_fixed_capacity_var.get():
            text_fixed_capacity = self.fixed_capacity_var.get()

        else:
            text_fixed_capacity = 'Not used'

        self.fixed_capacity_label.config(text=text_fixed_capacity, state=self.state)
        self.fixed_capacity_label.grid(row=8, column=1, sticky='w')

        ttk.Label(self.frame, text='Installation CO2 emissions [t CO2 / ' + component_unit + ']', state=self.state) \
            .grid(row=9, column=0, sticky='w')
        self.installation_co2_emissions_label.config(text=self.installation_co2_emissions_var.get(),
                                                     state=self.state)
        self.installation_co2_emissions_label.grid(row=9, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed CO2 emissions [t CO2 / ' + component_unit + ' / a]', state=self.state) \
            .grid(row=10, column=0, sticky='w')
        self.fixed_co2_emissions_label.config(text=self.fixed_co2_emissions_var.get(),
                                              state=self.state)
        self.fixed_co2_emissions_label.grid(row=10, column=1, sticky='w')

        ttk.Label(self.frame, text='Variable CO2 emissions [t CO2 / ' + self.commodity_unit + ']', state=self.state) \
            .grid(row=11, column=0, sticky='w')
        self.variable_co2_emissions_label.config(text=self.variable_co2_emissions_var.get(),
                                                 state=self.state)
        self.variable_co2_emissions_label.grid(row=11, column=1, sticky='w')

        ttk.Label(self.frame, text='Disposal CO2 emissions [t CO2 / ' + component_unit + ']', state=self.state) \
            .grid(row=12, column=0, sticky='w')
        self.disposal_co2_emissions_label.config(text=self.disposal_co2_emissions_var.get(),
                                                 state=self.state)
        self.disposal_co2_emissions_label.grid(row=12, column=1, sticky='w')

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1)

        adjust_values_button = ttk.Button(button_frame, text='Adjust values', command=self.adjust_values,
                                          state=self.state)
        adjust_values_button.grid(row=0, column=0, sticky='ew')

        button_frame.grid(row=13, columnspan=2, sticky='ew')

    def __init__(self, parent, frame, generator, pm_object, pm_object_original):

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.generator = generator

        self.frame = ttk.Frame(frame)
        self.frame.grid_columnconfigure(0, weight=1, uniform='a')
        self.frame.grid_columnconfigure(1, weight=1, uniform='a')

        self.generator_object = self.pm_object.get_component(self.generator)
        self.generated_commodity = self.generator_object.get_generated_commodity()
        self.commodity_unit = self.pm_object.get_commodity(self.generator_object.get_generated_commodity()).get_unit()
        self.curtailment_possible = self.generator_object.get_curtailment_possible()
        self.has_fixed_capacity = self.generator_object.get_has_fixed_capacity()
        self.fixed_capacity = self.generator_object.get_fixed_capacity()
        self.installation_co2_emissions = self.generator_object.get_installation_co2_emissions()
        self.fixed_co2_emissions = self.generator_object.get_fixed_co2_emissions()
        self.variable_co2_emissions = self.generator_object.get_variable_co2_emissions()
        self.disposal_co2_emissions = self.generator_object.get_disposal_co2_emissions()

        self.textvar_profile = StringVar()
        self.checkbox_generator_available_var = BooleanVar()

        self.capex_var = DoubleVar()
        self.lifetime_var = DoubleVar()
        self.uses_ppa_var = StringVar()
        self.ppa_price_var = DoubleVar()
        self.subsidies_var = DoubleVar()
        self.fixed_om_var = DoubleVar()
        self.variable_om_var = DoubleVar()
        self.generated_commodity_var = StringVar()
        self.checkbox_curtailment_var = BooleanVar()
        self.checkbox_fixed_capacity_var = BooleanVar()
        self.fixed_capacity_var = DoubleVar()
        self.installation_co2_emissions_var = DoubleVar()
        self.fixed_co2_emissions_var = DoubleVar()
        self.variable_co2_emissions_var = DoubleVar()
        self.disposal_co2_emissions_var = DoubleVar()

        self.capex_var.set(self.generator_object.get_capex())
        self.lifetime_var.set(self.generator_object.get_lifetime())
        self.fixed_om_var.set(round(float(self.generator_object.get_fixed_OM()) * 100, 2))
        self.variable_om_var.set(round(float(self.generator_object.get_variable_OM()), 2))
        self.generated_commodity_var.set(self.generator_object.get_generated_commodity())
        self.checkbox_curtailment_var.set(self.generator_object.get_curtailment_possible())
        self.checkbox_fixed_capacity_var.set(self.generator_object.get_has_fixed_capacity())
        self.fixed_capacity_var.set(self.generator_object.get_fixed_capacity())
        self.installation_co2_emissions_var.set(self.installation_co2_emissions)
        self.fixed_co2_emissions_var.set(self.fixed_co2_emissions)
        self.variable_co2_emissions_var.set(self.variable_co2_emissions)
        self.disposal_co2_emissions_var.set(self.disposal_co2_emissions)

        if not self.generator_object.get_uses_ppa():
            self.uses_ppa_var.set('investment')
        else:
            self.uses_ppa_var.set('ppa')

        self.ppa_price_var.set(self.generator_object.get_ppa_price())
        self.subsidies_var.set(self.generator_object.get_subsidies())

        self.monetary_unit = self.pm_object.get_monetary_unit()

        self.checkbox_generator_available = ttk.Checkbutton(self.frame)
        self.capex_label = ttk.Label(self.frame)
        self.lifetime_label = ttk.Label(self.frame)
        self.fixed_om_label = ttk.Label(self.frame)
        self.variable_om_label = ttk.Label(self.frame)
        self.generated_commodity_label = ttk.Label(self.frame)
        self.curtailment_label = ttk.Label(self.frame)
        self.fixed_capacity_label = ttk.Label(self.frame)
        self.ppa_price_label = ttk.Label(self.frame)
        self.installation_co2_emissions_label = ttk.Label(self.frame)
        self.fixed_co2_emissions_label = ttk.Label(self.frame)
        self.variable_co2_emissions_label = ttk.Label(self.frame)
        self.disposal_co2_emissions_label = ttk.Label(self.frame)

        if self.generator_object in self.pm_object.get_final_generator_components_objects():
            self.state = NORMAL
            self.checkbox_generator_available_var.set(True)

            if self.uses_ppa_var.get() == 'investment':
                self.state_investment = NORMAL
                self.state_ppa = DISABLED
            else:
                self.state_investment = DISABLED
                self.state_ppa = NORMAL

        else:
            self.state = DISABLED
            self.checkbox_generator_available_var.set(False)

            self.state_investment = DISABLED
            self.state_ppa = DISABLED

        self.initialize_generator_frame()
