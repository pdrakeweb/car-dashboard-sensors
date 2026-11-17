# Car Dashboard

Home Assistant custom integration for the car dashboard. Three event-driven sensors, local only. No YAML, no polling, no network calls.

| Sensor | State | Attributes |
|---|---|---|
| `sensor.car_people_home` | Count of household members home | `home`, `away` (names) |
| `sensor.car_vehicles_home` | Count of fleet vehicles home | `home`, `away` (names) |
| `sensor.car_package_status` | `N delivered` / `none` | `count`, `location`, `last_delivery` |

## Install (HACS)

1. HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/pdrakeweb/car-dashboard-sensors`, category Integration.
2. Install **Car Dashboard**, restart Home Assistant.
3. Settings → Devices & Services → Add Integration → **Car Dashboard**. No settings.

## Sources

- People: `person.peter`, `person.kelly`, `person.abby`, `person.julia`, `person.sarah`, `person.peter_jr`
- Vehicles: `sensor.sky`, `sensor.sportage`, `sensor.sorento`, `sensor.qx80`, `sensor.commander`
- Package: `sensor.package` (+ `input_text.package_delivery_timestamp` for the delivery time)

## Requirements

Home Assistant 2024.1.0 or newer.
