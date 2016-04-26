# nest_influx
Push Nest to influxdb

Iterates through all structures and devices to create the following metrics:

* mode
* fan
* humidity
* hvac_ac_state
* hvac_cool_x2_state
* hvac_heater_state
* hvac_aux_heater_state
* hvac_heat_x2_state
* hvac_heat_x3_state
* hvac_alt_heat_state
* hvac_alt_heat_x2_state
* hvac_emer_heat_state
* temperature
* target

Each one is tagged with the name of the `Structure` and `Device`.

Until I get motivated to make it configurable, all temperature metrics are converted to from Celsius to Freedom units.

## About
Anyone who lives in a hot region where climate control becomes an important fixture of life should know how their HVAC system is running. Historical trend data can provide context to inefficient cooling (wastes money!) or identification of when a problem began to creep in.

This data has helped us identify the progression of coolant leaks in our system, as well providing empircal data on how long and when the compressor was running. Also shows how friggin hot my second story gets during the summer. Sucks for my kids.

## Visualization
### Grafana
Sample dashboard definition can be found in misc.
![alt text](https://kremlinkev.github.io/nest_influx/images/grafana.png "Grafana Dashboard")

Blue background bars (y-index 2, to visualize bool 0/1) indicate that compressor was kicked on.
