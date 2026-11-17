"""Constants for the Car Dashboard integration."""

DOMAIN = "car_dashboard"

# person entity -> display name, in dashboard order.
PEOPLE: dict[str, str] = {
    "person.peter": "Pete",
    "person.kelly": "Kelly",
    "person.abby": "Abby",
    "person.julia": "Julia",
    "person.sarah": "Sarah",
    "person.peter_jr": "Peter Jr",
}

# Vehicle sensor entity -> display name, in dashboard order.
VEHICLES: dict[str, str] = {
    "sensor.sky": "Sky",
    "sensor.sportage": "Sportage",
    "sensor.sorento": "Sorento",
    "sensor.qx80": "QX80",
    "sensor.commander": "Commander",
}

PACKAGE_SENSOR = "sensor.package"
PACKAGE_TIMESTAMP = "input_text.package_delivery_timestamp"
