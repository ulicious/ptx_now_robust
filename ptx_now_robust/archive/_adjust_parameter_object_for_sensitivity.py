from _load_projects import load_project
from object_framework import ParameterObject
from _load_projects import load_project

import os
from os import walk
import yaml

path_config_file = 'C:/Users/mt5285/Desktop/setting_to_adjust/FT_Setting.yaml'
path_saving = 'C:/Users/mt5285/Desktop/setting_to_adjust/adjusted_settings/'

yaml_file = open(path_config_file)
case_data = yaml.load(yaml_file, Loader=yaml.FullLoader)

parameters_to_change = {'component': {'Synthesis Island': {'min_p': (0.1, 0.1, 1)}}}

old_name = path_config_file.split('/')[-1].split('.')[0]
n = 0
for k1 in list(parameters_to_change.keys()):
    for k2 in list(parameters_to_change[k1].keys()):
        for k3 in list(parameters_to_change[k1][k2].keys()):

            min_value = parameters_to_change[k1][k2][k3][0]
            steps = parameters_to_change[k1][k2][k3][1]
            max_value = parameters_to_change[k1][k2][k3][2]

            scaling = 1
            if min_value < 1:
                scaling = 100

            min_value = int(min_value * scaling)
            steps = int(steps * scaling)
            max_value = int(max_value * scaling)

            for i in range(min_value-steps, max_value, steps):
                case_data[k1][k2][k3] = (min_value + i) / scaling
                path_file = path_saving + old_name + ' ' + str(n) + '.yaml'

                file = open(path_file, "w")
                yaml.dump(case_data, file)
                file.close()

                n += 1
