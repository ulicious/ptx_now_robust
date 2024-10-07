class Commodity:

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_unit(self, unit):
        self.commodity_unit = unit

    def get_unit(self):
        return self.commodity_unit

    def set_energy_content(self, energy_content):
        self.energy_content = energy_content

    def get_energy_content(self):
        return self.energy_content

    def set_purchasable(self, status):
        self.purchasable = status

    def is_purchasable(self):
        return self.purchasable

    def set_purchase_price_type(self, purchase_price_type):
        self.purchase_price_type = purchase_price_type

    def get_purchase_price_type(self):
        return self.purchase_price_type

    def set_purchase_price(self, purchase_price):
        self.purchase_price = float(purchase_price)

    def get_purchase_price(self):
        return self.purchase_price

    def set_saleable(self, status):
        self.saleable = status

    def is_saleable(self):
        return self.saleable

    def set_sale_price_type(self, sale_price_type):
        self.sale_price_type = sale_price_type

    def get_sale_price_type(self):
        return self.sale_price_type

    def set_sale_price(self, sale_price):
        self.sale_price = float(sale_price)

    def get_sale_price(self):
        return self.sale_price

    def set_available(self, status):
        self.available = status

    def is_available(self):
        return self.available

    def set_emittable(self, status):
        self.emittable = status

    def is_emittable(self):
        return self.emittable

    def set_demanded(self, status):
        self.demanded = status

    def is_demanded(self):
        return self.demanded

    def set_demand(self, demand):
        self.demand = float(demand)

    def get_demand(self):
        return self.demand

    def set_demand_type(self, status):
        self.demand_type = status

    def get_demand_type(self):
        return self.demand_type

    def set_total_demand(self, status):
        self.total_demand = status

    def is_total_demand(self):
        return self.total_demand

    def set_specific_co2_emissions_available(self, specific_co2_emissions_available):
        self.specific_co2_emissions_available = specific_co2_emissions_available

    def get_specific_co2_emissions_available(self):
        return self.specific_co2_emissions_available

    def set_total_co2_emissions_available(self, total_co2_emissions_available):
        self.total_co2_emissions_available = total_co2_emissions_available

    def get_total_co2_emissions_available(self):
        return self.total_co2_emissions_available

    def set_specific_co2_emissions_emitted(self, specific_co2_emissions_emitting):
        self.specific_co2_emissions_emitting = specific_co2_emissions_emitting

    def get_specific_co2_emissions_emitted(self):
        return self.specific_co2_emissions_emitting

    def set_total_co2_emissions_emitted(self, total_co2_emissions_emitted):
        self.total_co2_emissions_emitted = total_co2_emissions_emitted

    def get_total_co2_emissions_emitted(self):
        return self.total_co2_emissions_emitted

    def set_specific_co2_emissions_purchase(self, specific_co2_emissions_purchase):
        self.specific_co2_emissions_purchase = specific_co2_emissions_purchase

    def get_specific_co2_emissions_purchase(self):
        return self.specific_co2_emissions_purchase

    def set_total_co2_emissions_purchase(self, total_co2_emissions_purchase):
        self.total_co2_emissions_purchase = total_co2_emissions_purchase

    def get_total_co2_emissions_purchase(self):
        return self.specific_co2_emissions_purchase

    def set_specific_co2_emissions_sale(self, specific_co2_emissions_sale):
        self.specific_co2_emissions_sale = specific_co2_emissions_sale

    def get_specific_co2_emissions_sale(self):
        return self.specific_co2_emissions_sale

    def set_total_co2_emissions_sale(self, total_co2_emissions_sale):
        self.total_co2_emissions_sale = total_co2_emissions_sale

    def get_total_co2_emissions_sale(self):
        return self.total_co2_emissions_sale

    def set_total_co2_emissions_generation(self, total_co2_emissions_generation):
        self.total_co2_emissions_generation = total_co2_emissions_generation

    def get_total_co2_emissions_generation(self):
        return self.total_co2_emissions_generation

    def set_total_co2_emissions_storage(self, total_co2_emissions_storage):
        self.total_co2_emissions_storage = total_co2_emissions_storage

    def get_total_co2_emissions_storage(self):
        return self.total_co2_emissions_storage

    def set_total_co2_emissions_production(self, total_co2_emissions_production):
        self.total_co2_emissions_production = total_co2_emissions_production

    def get_total_co2_emissions_production(self):
        return self.total_co2_emissions_production

    def set_default(self, status):  # todo: remove
        self.default_commodity = status

    def set_final(self, status):
        self.final_commodity = status

    def set_custom(self, status):
        self.custom_commodity = status

    def is_default(self):
        return self.default_commodity

    def is_final(self):
        return self.final_commodity

    def is_custom(self):
        return self.custom_commodity

    def set_purchased_quantity(self, purchased_quantity):
        self.purchased_quantity = purchased_quantity

    def get_purchased_quantity(self):
        return self.purchased_quantity

    def set_purchase_costs(self, purchase_costs):
        self.purchase_costs = purchase_costs

    def get_purchase_costs(self):
        return self.purchase_costs

    def set_sold_quantity(self, sold_quantity):
        self.sold_quantity = sold_quantity

    def get_sold_quantity(self):
        return self.sold_quantity

    def set_selling_revenue(self, selling_revenue):
        self.selling_revenue = selling_revenue

    def get_selling_revenue(self):
        return self.selling_revenue

    def set_available_quantity(self, available_quantity):
        self.available_quantity = available_quantity

    def get_available_quantity(self):
        return self.purchased_quantity

    def set_emitted_quantity(self, emitted_quantity):
        self.emitted_quantity = emitted_quantity

    def get_emitted_quantity(self):
        return self.emitted_quantity

    def set_demanded_quantity(self, demanded_quantity):
        self.demanded_quantity = demanded_quantity

    def get_demanded_quantity(self):
        return self.demanded_quantity

    def set_charged_quantity(self, charged_quantity):
        self.charged_quantity = charged_quantity

    def get_charged_quantity(self):
        return self.charged_quantity

    def set_discharged_quantity(self, discharged_quantity):
        self.discharged_quantity = discharged_quantity

    def get_discharged_quantity(self):
        return self.discharged_quantity

    def set_total_storage_costs(self, total_storage_costs):
        self.total_storage_costs = total_storage_costs

    def get_total_storage_costs(self):
        return self.total_storage_costs

    def set_standby_quantity(self, standby_quantity):
        self.standby_quantity = standby_quantity

    def get_standby_quantity(self):
        return self.standby_quantity

    def set_consumed_quantity(self, consumed_quantity):
        self.consumed_quantity = consumed_quantity

    def get_consumed_quantity(self):
        return self.consumed_quantity

    def set_produced_quantity(self, produced_quantity):
        self.produced_quantity = produced_quantity

    def get_produced_quantity(self):
        return self.produced_quantity

    def set_total_production_costs(self, total_production_costs):
        # Important: Total production costs only derive from conversion components where commodity is main output
        self.total_production_costs = total_production_costs

    def get_total_production_costs(self):
        return self.total_production_costs

    def set_generated_quantity(self, generated_quantity):
        self.generated_quantity = generated_quantity

    def get_generated_quantity(self):
        return self.generated_quantity

    def set_total_generation_costs(self, total_generation_costs):
        self.total_generation_costs = total_generation_costs

    def get_total_generation_costs(self):
        return self.total_generation_costs

    def __copy__(self):
        return Commodity(
            name=self.name, commodity_unit=self.commodity_unit,
            energy_content=self.energy_content, final_commodity=self.final_commodity,
            custom_commodity=self.custom_commodity, emittable=self.emittable, available=self.available,
            purchasable=self.purchasable, purchase_price=self.purchase_price,
            purchase_price_type=self.purchase_price_type, saleable=self.saleable,
            sale_price=self.sale_price, sale_price_type=self.sale_price_type, demanded=self.demanded,
            demand=self.demand, total_demand=self.total_demand, demand_type=self.demand_type,
            purchased_quantity=self.purchased_quantity, purchase_costs=self.purchase_costs,
            sold_quantity=self.sold_quantity, selling_revenue=self.selling_revenue,
            emitted_quantity=self.emitted_quantity, available_quantity=self.available_quantity,
            demanded_quantity=self.demanded_quantity, charged_quantity=self.charged_quantity,
            discharged_quantity=self.discharged_quantity, total_storage_costs=self.total_storage_costs,
            standby_quantity=self.standby_quantity, consumed_quantity=self.consumed_quantity,
            produced_quantity=self.produced_quantity, total_production_costs=self.total_production_costs,
            generated_quantity=self.generated_quantity, total_generation_costs=self.total_generation_costs,
            specific_co2_emissions_available=self.specific_co2_emissions_available,
            total_co2_emissions_available=self.total_co2_emissions_available,
            specific_co2_emissions_emitted=self.specific_co2_emissions_emitting,
            total_co2_emissions_emitted=self.total_co2_emissions_emitted,
            specific_co2_emissions_purchase=self.specific_co2_emissions_purchase,
            total_co2_emissions_purchase=self.total_co2_emissions_purchase,
            specific_co2_emissions_sale=self.specific_co2_emissions_sale,
            total_co2_emissions_sale=self.total_co2_emissions_sale,
            total_co2_emissions_generation=self.total_co2_emissions_generation,
            total_co2_emissions_storage=self.total_co2_emissions_storage,
            total_co2_emissions_production=self.total_co2_emissions_production)

    def __init__(self, name, commodity_unit, energy_content=None, final_commodity=False,
                 custom_commodity=False, emittable=False, available=False,
                 purchasable=False, purchase_price=0, purchase_price_type='fixed',
                 saleable=False, sale_price=0, sale_price_type='fixed',
                 demanded=False, demand=0, total_demand=False, demand_type='fixed',
                 purchased_quantity=0., purchase_costs=0., sold_quantity=0., selling_revenue=0.,
                 emitted_quantity=0., available_quantity=0., demanded_quantity=0.,
                 charged_quantity=0., discharged_quantity=0., total_storage_costs=0.,
                 standby_quantity=0., consumed_quantity=0.,
                 produced_quantity=0., total_production_costs=0.,
                 generated_quantity=0., total_generation_costs=0.,
                 specific_co2_emissions_available=0., total_co2_emissions_available=0.,
                 specific_co2_emissions_emitted=0., total_co2_emissions_emitted=0.,
                 specific_co2_emissions_purchase=0., total_co2_emissions_purchase=0.,
                 specific_co2_emissions_sale=0., total_co2_emissions_sale=0.,
                 total_co2_emissions_generation=0., total_co2_emissions_storage=0., total_co2_emissions_production=0.):

        """

        :param name: [string] - Abbreviation of commodity
        :param commodity_unit: [string] - Unit of commodity
        :param energy_content: [float] - Energy content per unit
        :param final_commodity: [boolean] - Is used in the final optimization?
        :param custom_commodity: [boolean] - Is a custom commodity?
        :param emittable: [boolean] - can be emitted?
        :param available: [boolean] - is freely available without limitation or price?
        :param purchasable: [boolean] - can be purchased?
        :param purchase_price: [float or list] - fixed price or time varying price
        :param purchase_price_type: [string] - fixed price or time varying price
        :param saleable: [boolean] - can be sold?
        :param sale_price: [float or list] - fixed price or time varying price
        :param sale_price_type: [string] - fixed price or time varying price
        :param demanded: [boolean] - is demanded?
        :param demand: [float] - Demand
        :param total_demand: [boolean] - Demand over all time steps or for each time step
        """

        self.name = name
        self.commodity_unit = commodity_unit
        if energy_content is not None:
            self.energy_content = float(energy_content)
        elif self.commodity_unit == 'kWh':
            self.energy_content = 0.001
        elif self.commodity_unit == 'MWh':
            self.energy_content = 1
        elif self.commodity_unit == 'GWh':
            self.energy_content = 1000
        elif self.commodity_unit == 'kJ':
            self.energy_content = 2.7777e-7
        elif self.commodity_unit == 'MJ':
            self.energy_content = 2.7777e-4
        elif self.commodity_unit == 'GJ':
            self.energy_content = 2.7777e-1
        else:
            self.energy_content = 0

        self.final_commodity = bool(final_commodity)
        self.custom_commodity = bool(custom_commodity)

        self.emittable = bool(emittable)
        self.available = bool(available)

        self.purchasable = bool(purchasable)
        if purchase_price_type == 'fixed':
            self.purchase_price = float(purchase_price)
        else:
            self.purchase_price = purchase_price
        self.purchase_price_type = purchase_price_type

        self.saleable = bool(saleable)
        if sale_price_type == 'fixed':
            self.sale_price = float(sale_price)
        else:
            self.sale_price = sale_price
        self.sale_price_type = sale_price_type

        self.demanded = bool(demanded)
        self.total_demand = bool(total_demand)
        if demand_type == 'fixed':
            self.demand = float(demand)
        else:
            self.demand = demand
        self.demand_type = demand_type

        self.purchased_quantity = purchased_quantity
        self.purchase_costs = purchase_costs

        self.sold_quantity = sold_quantity
        self.selling_revenue = selling_revenue

        self.emitted_quantity = emitted_quantity
        self.available_quantity = available_quantity
        self.demanded_quantity = demanded_quantity

        self.charged_quantity = charged_quantity
        self.discharged_quantity = discharged_quantity
        self.total_storage_costs = total_storage_costs

        self.standby_quantity = standby_quantity

        self.produced_quantity = produced_quantity
        self.consumed_quantity = consumed_quantity
        self.total_production_costs = total_production_costs

        self.generated_quantity = generated_quantity
        self.total_generation_costs = total_generation_costs

        self.specific_co2_emissions_available = specific_co2_emissions_available
        self.specific_co2_emissions_emitting = specific_co2_emissions_emitted
        self.specific_co2_emissions_purchase = specific_co2_emissions_purchase
        self.specific_co2_emissions_sale = specific_co2_emissions_sale

        self.total_co2_emissions_available = total_co2_emissions_available
        self.total_co2_emissions_emitted = total_co2_emissions_emitted
        self.total_co2_emissions_purchase = total_co2_emissions_purchase
        self.total_co2_emissions_sale = total_co2_emissions_sale
        self.total_co2_emissions_generation = total_co2_emissions_generation
        self.total_co2_emissions_storage = total_co2_emissions_storage
        self.total_co2_emissions_production = total_co2_emissions_production
