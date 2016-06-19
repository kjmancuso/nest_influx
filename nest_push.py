#!/usr/local/bin/python3
import sys
import nest
from configobj import ConfigObj
from influxdb import InfluxDBClient
from nest import utils as nu
from validate import Validator

# Gather details from config.ini and process
config = ConfigObj(sys.path[0] + '/config.ini', configspec=['convert_to_Fahrenheit = boolean(default=True)'])
config.validate(Validator(), copy=True)
convert_to_Fahrenheit = config['convert_to_Fahrenheit']
USER = config['nest']['user']
PASS = config['nest']['pass']
IFLX_HOST = config['influx']['host']
IFLX_USER = config['influx']['user']
IFLX_PASS = config['influx']['pass']
IFLX_DB = config['influx']['database']

# Metrics to loop, uncomment any your system is capable of
metrics = ['fan',                      # Fan state
           'hvac_ac_state',            # Air Conditioning state
           #'hvac_cool_x2_state',      # Unsure of function
           'hvac_heater_state',        # Heater state
           #'hvac_aux_heater_state',   # Unsure of function
           #'hvac_heat_x2_state',      # Unsure of function
           #'hvac_heat_x3_state',      # Unsure of function
           #'hvac_alt_heat_state',     # Unsure of function 
           #'hvac_alt_heat_x2_state',  # Unsure of function 
           #'hvac_emer_heat_state',    # Unsure of function
           'humidity']                 # Measures current indoor humidity

# Function to gather data from Nest
def gather_nest(u=USER, p=PASS):
    napi = nest.Nest(u, p)
    data = []
    # Jason loves mad precision, yo. Lets turn that shiz down a notch.
    nu.decimal.getcontext().prec = 4
    for structure in napi.structures:
        struct_name = structure.name

        # loop through each of the Nest devices present in the account
        for device in structure.devices:

            # these values are reset to null in case they aren't used in this loop
            device_mode = None
            target_heat = None
            target_cool = None
        
            # loop through and record each of the metrics defined above
            for m in metrics:
                data.append({'measurement': m,
                             'tags': {'structure': struct_name,
                                      'device': device.name},
                             'fields': {'value': getattr(device, m)}})

            # process current indoor temperature
            data.append({'measurement': 'temperature',
                         'tags': {'structure': struct_name,
                                  'device': device.name},
                         'fields': {'value': convert(getattr(device,'temperature'))}})

            # get current mode of device to properly process target temps
            device_mode = getattr(device, 'mode')
            data.append({'measurement': 'mode',
                         'tags': {'structure': struct_name,
                                  'device': device.name},
                         'fields': {'value': device_mode}})

            # process target temps based on mode 
            if device_mode == "cool": # AC only
                target_heat=None
                target_cool=convert(getattr(device,'target'))
            elif device_mode == "heat": # heater only
                target_heat=convert(getattr(device,'target'))
                target_cool=None
            elif device_mode == "range": #high and low set points
                target_heat=convert(getattr(device,'target').low)
                target_cool=convert(getattr(device,'target').high)
            else: #off or other unhandled mode
                target_heat=None
                target_cool=None

            # record target_heat if it is set
            if target_heat is not None:
                data.append({'measurement': 'target_heat',
                             'tags': {'structure': struct_name,
                                      'device': device.name},
                             'fields': {'value':target_heat}})

            # record target_cool if it is set
            if target_cool is not None:
                data.append({'measurement': 'target',
                             'tags': {'structure': struct_name,
                                      'device': device.name},
                             'fields': {'value':target_cool}})

        # record current outside temperature (wherever Nest gets this from)
        data.append({'measurement': 'temperature',
                     'tags': {'structure': struct_name,
                              'device': 'Outside'},
                     'fields': {'value':  convert(structure.weather.current.temperature)}})

        # record current outside humidity (wherever Nest gets this from)
        data.append({'measurement': 'humidity',
                     'tags': {'structure': struct_name,
                              'device': 'Outside'},
                     'fields': {'value': structure.weather.current.humidity}})
    return data

# Function to send data gathered to influxDB
def send_to_influx(metrics, host=IFLX_HOST, port=8086, user=IFLX_USER,
                   pwd=IFLX_PASS, db=IFLX_DB):
    client = InfluxDBClient(host, port, user, pwd, db)
    client.write_points(metrics)

# Function to convert Celsius temps to Fahrenheit if option is set in config.ini
def convert(value):
    if convert_to_Fahrenheit:
       converted = nu.c_to_f(value)
    else:
       converted = value
    return converted

# Main body of program
if __name__ == '__main__':
    send_to_influx(gather_nest())
