"""Offline tests for the car_dashboard sensor logic.

Stubs the homeassistant package so sensor.py can be imported and exercised
without a Home Assistant instance.

Run: python3 tests/test_logic.py
"""

import asyncio
import importlib
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

# --- Stub the homeassistant package ---------------------------------------

ha = types.ModuleType("homeassistant")
ha_core = types.ModuleType("homeassistant.core")
ha_components = types.ModuleType("homeassistant.components")
ha_sensor = types.ModuleType("homeassistant.components.sensor")
ha_helpers = types.ModuleType("homeassistant.helpers")
ha_platform = types.ModuleType("homeassistant.helpers.entity_platform")
ha_event = types.ModuleType("homeassistant.helpers.event")


class SensorEntity:
    """Minimal stub of homeassistant.components.sensor.SensorEntity."""

    def async_write_ha_state(self):
        self._written = getattr(self, "_written", 0) + 1

    def async_on_remove(self, func):
        self._on_remove = func


class SensorStateClass:
    MEASUREMENT = "measurement"


class HomeAssistant:
    pass


class Event:
    pass


def callback(func):
    return func


def async_track_state_change_event(hass, entity_ids, action):
    hass.tracked = (list(entity_ids), action)
    return lambda: None


ha_core.HomeAssistant = HomeAssistant
ha_core.Event = Event
ha_core.callback = callback
ha_sensor.SensorEntity = SensorEntity
ha_sensor.SensorStateClass = SensorStateClass
ha_platform.AddEntitiesCallback = object  # annotations only
ha_event.async_track_state_change_event = async_track_state_change_event

for name, mod in {
    "homeassistant": ha,
    "homeassistant.core": ha_core,
    "homeassistant.components": ha_components,
    "homeassistant.components.sensor": ha_sensor,
    "homeassistant.helpers": ha_helpers,
    "homeassistant.helpers.entity_platform": ha_platform,
    "homeassistant.helpers.event": ha_event,
}.items():
    sys.modules[name] = mod

# --- Load the real integration package ------------------------------------

PKG_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "car_dashboard"
pkg = types.ModuleType("car_dashboard")
pkg.__path__ = [str(PKG_DIR)]
sys.modules["car_dashboard"] = pkg
sensor_mod = importlib.import_module("car_dashboard.sensor")

# --- Fake hass --------------------------------------------------------------


class FakeState:
    def __init__(self, state, attributes=None):
        self.state = state
        self.attributes = attributes or {}


class FakeStates:
    def __init__(self, mapping):
        self._m = dict(mapping)

    def get(self, entity_id):
        return self._m.get(entity_id)

    def set(self, entity_id, state, attributes=None):
        self._m[entity_id] = FakeState(state, attributes)


class FakeHass:
    def __init__(self, mapping):
        self.states = FakeStates(mapping)
        self.tracked = None


# --- Tests ------------------------------------------------------------------

PASSED = 0


def check(label, actual, expected):
    global PASSED
    assert actual == expected, f"{label}: got {actual!r}, expected {expected!r}"
    PASSED += 1
    print(f"  ok: {label}")


def test_compute_people():
    print("compute_people")
    states = {
        "person.peter": "home",
        "person.kelly": "home",
        "person.abby": "not_home",
        "person.julia": "not_home",
        "person.sarah": "not_home",
        "person.peter_jr": "home",
    }
    count, home, away = sensor_mod.compute_people(states)
    check("count", count, 3)
    check("home", home, ["Pete", "Kelly", "Peter Jr"])
    check("away", away, ["Abby", "Julia", "Sarah"])
    # A person in a named zone is in neither list.
    states["person.sarah"] = "Work"
    count, home, away = sensor_mod.compute_people(states)
    check("zone count", count, 3)
    check("zone away", away, ["Abby", "Julia"])


def test_compute_vehicles():
    print("compute_vehicles")
    states = {
        "sensor.sky": "home",
        "sensor.sportage": "away",
        "sensor.sorento": "home",
        "sensor.qx80": "home",
        "sensor.commander": "away",
    }
    count, home, away = sensor_mod.compute_vehicles(states)
    check("count", count, 3)
    check("home", home, ["Sky", "Sorento", "QX80"])
    check("away", away, ["Sportage", "Commander"])


def test_compute_package():
    print("compute_package")
    state, attrs = sensor_mod.compute_package(
        "delivered",
        {"count": 2, "location": "front porch",
         "last_delivery": "2026-11-16T21:48:48+00:00"},
        None,
    )
    check("delivered state", state, "2 delivered")
    check("delivered attrs", attrs, {
        "count": 2,
        "location": "front porch",
        "last_delivery": "2026-11-16T21:48:48+00:00",
    })
    # Delivered with no attributes: count defaults to 1.
    state, attrs = sensor_mod.compute_package("delivered", {}, None)
    check("bare delivered", state, "1 delivered")
    check("bare count", attrs["count"], 1)
    check("bare location", attrs["location"], None)
    # Not delivered.
    state, attrs = sensor_mod.compute_package("none", {}, None)
    check("none state", state, "none")
    check("none count", attrs["count"], 0)
    # Epoch timestamp helper -> ISO 8601.
    expected = datetime.fromtimestamp(1794685649, tz=timezone.utc).isoformat()
    state, attrs = sensor_mod.compute_package(
        "delivered", {"count": 1, "location": "front porch"}, "1794685649"
    )
    check("epoch last_delivery", attrs["last_delivery"], expected)


def test_entity_flow():
    print("entity flow (fake hass)")
    hass = FakeHass({
        "person.peter": FakeState("home"),
        "person.kelly": FakeState("home"),
        "person.abby": FakeState("not_home"),
        "person.julia": FakeState("not_home"),
        "person.sarah": FakeState("not_home"),
        "person.peter_jr": FakeState("home"),
    })
    entity = sensor_mod.CarDashboardSensor(hass, "people")
    check("object id", entity._attr_suggested_object_id, "car_people_home")
    check("unique id", entity._attr_unique_id, "car_dashboard_people_home")
    asyncio.run(entity.async_added_to_hass())
    check("initial value", entity._attr_native_value, 3)
    check("initial home attr", entity._attr_extra_state_attributes["home"],
          ["Pete", "Kelly", "Peter Jr"])
    check("subscribed to people", hass.tracked[0], [
        "person.peter", "person.kelly", "person.abby",
        "person.julia", "person.sarah", "person.peter_jr",
    ])
    # Sarah comes home -> event handler recomputes.
    hass.states.set("person.sarah", "home")
    hass.tracked[1](object())
    check("updated value", entity._attr_native_value, 4)
    check("state written", getattr(entity, "_written", 0) >= 1, True)

    # Package entity end to end.
    hass2 = FakeHass({
        "sensor.package": FakeState("none"),
        "input_text.package_delivery_timestamp": FakeState("0"),
    })
    pkg = sensor_mod.CarDashboardSensor(hass2, "package")
    check("package object id", pkg._attr_suggested_object_id, "car_package_status")
    asyncio.run(pkg.async_added_to_hass())
    check("package initial", pkg._attr_native_value, "none")
    hass2.states.set("sensor.package", "delivered",
                     {"count": 1, "location": "front porch"})
    hass2.tracked[1](object())
    check("package delivered", pkg._attr_native_value, "1 delivered")
    check("package location", pkg._attr_extra_state_attributes["location"],
          "front porch")

    # Vehicles entity object id.
    veh = sensor_mod.CarDashboardSensor(hass, "vehicles")
    check("vehicles object id", veh._attr_suggested_object_id, "car_vehicles_home")


if __name__ == "__main__":
    test_compute_people()
    test_compute_vehicles()
    test_compute_package()
    test_entity_flow()
    print(f"\n{PASSED} checks passed")
