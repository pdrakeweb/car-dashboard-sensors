# Design note

## Domain: `car_dashboard`

Chosen to match the dashboard it serves (`car_dashboard` dashboard id,
`/car-dashboard` URL). Short, unambiguous, and the sensor entity ids read
naturally: `sensor.car_people_home`, `sensor.car_vehicles_home`,
`sensor.car_package_status`.

Rejected: `car_dashboard_sensors` — longer, adds nothing; the entity ids
come from the sensor names, not the domain.

## Fixed sources, no options

The three sensors read a fixed set of source entities (see README). No
config or options flow: the dashboard buttons bind to these exact entity
ids, so configurability would only create a way to break the binding.
If the household or fleet changes, the source lists in `const.py` change.

## Event-driven, not polling

Each sensor subscribes to state changes on its source entities
(`async_track_state_change_event`) and recomputes on change. No scan
interval, no network calls, no external dependencies.

## Package `last_delivery`

`sensor.package` carries no delivery-time attribute, so the sensor falls
back to `input_text.package_delivery_timestamp` (epoch seconds, as the
camera-intelligence package guard writes it) and converts it to ISO 8601.
If that helper is missing or unparseable, the attribute is `None`.
