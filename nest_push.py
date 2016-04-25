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
            data.append({'measurement': 'mode',
                         'tags': {'structure': struct_name,
                                  'device': device.name},
                         'fields': {'value': device.mode}})

            data.append({'measurement': 'temperature',
                         'tags': {'structure': struct_name,
                                  'device': device.name},
                         'fields': {'value': nu.c_to_f(device.temperature)}})

            data.append({'measurement': 'target',
                         'tags': {'structure': struct_name,
                                  'device': device.name},
                         'fields': {'value': nu.c_to_f(device.target)}})

            data.append({'measurement': 'humidity',
                         'tags': {'structure': struct_name,
                                  'device': device.name},
                         'fields': {'value': device.humidity}})

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
