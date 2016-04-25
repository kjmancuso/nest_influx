import sys

import nest

from configobj import ConfigObj
from influxdb import InfluxDBClient
from nest import utils as nu

config = ConfigObj(sys.path[0] + '/config.ini')
USER = config['nest']['user']
PASS = config['nest']['pass']
IFLX_HOST = config['influx']['host']
IFLX_USER = config['influx']['user']
IFLX_PASS = config['influx']['pass']
IFLX_DB = config['influx']['database']

# Metrics to loop
metrics = ['mode',
           'fan',
           'humidity',
           'hvac_ac_state',
           'hvac_cool_x2_state',
           'hvac_heater_state',
           'hvac_aux_heater_state',
           'hvac_heat_x2_state',
           'hvac_heat_x3_state',
           'hvac_alt_heat_state',
           'hvac_alt_heat_x2_state',
           'hvac_emer_heat_state']

metrics_convert = ['temperature',
                   'target']


def send_to_influx(metrics, host=IFLX_HOST, port=8086, user=IFLX_USER,
                   pwd=IFLX_PASS, db=IFLX_DB):
    client = InfluxDBClient(host, port, user, pwd, db)
    client.write_points(metrics)


def gather_nest(u=USER, p=PASS):
    napi = nest.Nest(u, p)
    data = []
    # Jason loves mad precision, yo. Lets turn that shiz down a notch.
    nu.decimal.getcontext().prec = 4
    for structure in napi.structures:
        struct_name = structure.name

        for device in structure.devices:
            for m in metrics:
                data.append({'measurement': m,
                             'tags': {'structure': struct_name,
                                      'device': device.name},
                             'fields': {'value': getattr(device, m)}})

            for m in metrics_convert:
                data.append({'measurement': m,
                             'tags': {'structure': struct_name,
                                      'device': device.name},
                             'fields': {'value':
                                        nu.c_to_f(getattr(device, m))}})

        t = nu.c_to_f(structure.weather.current.temperature)
        data.append({'measurement': 'temperature',
                     'tags': {'structure': struct_name,
                              'device': 'Outside'},
                     'fields': {'value':  t}})

        data.append({'measurement': 'humidity',
                     'tags': {'structure': struct_name,
                              'device': 'Outside'},
                     'fields': {'value': structure.weather.current.humidity}})

    return data

if __name__ == '__main__':
    data = gather_nest()
    send_to_influx(data)
