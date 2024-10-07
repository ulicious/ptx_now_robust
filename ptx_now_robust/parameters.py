import os

# this file contains all parameter assumptions

basic_path = os.getcwd()
data_path = basic_path + '/applied_data/'

working_directory = 'C:/Users/mt5285/Desktop/robust/'  # todo: adjust

costs_missing = 3.75

electricity_available = True
electricity_price = 10

demand_type = 'total'
energy_carrier = 'FT'  # decide between Hydrogen, FT and MeOH
framework_name = energy_carrier + '.yaml'

countries = ['Australia', 'Saudi Arabia', 'Chile', 'Germany', 'Kazakhstan']  # available countries: Australia, Saudi Arabia, Chile, Germany and Kazakhstan

cluster_lengths = [24, 48, 72, 96, 120, 144, 168, 192, 216, 240, 264, 288, 312, 336, 8760]
