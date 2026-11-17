"""Sensor platform for the Car Dashboard integration.

Three event-driven sensors for the car dashboard buttons. Local only, no
polling, no network calls — each sensor recomputes when one of its source
entities changes state.

- sensor.car_people_home: count of household members home
- sensor.car_vehicles_home: count of fleet vehicles home
- sensor.car_package_status: "N delivered" or "none"
"""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    PACKAGE_SENSOR,
    PACKAGE_TIMESTAMP,
    PEOPLE,
    VEHICLES,
)


def _names_in_state(
    states: dict[str, str | None], mapping: dict[str, str], wanted: str
) -> list[str]:
    """Display names whose entity is in the wanted state."""
    return [name for entity_id, name in mapping.items() if states.get(entity_id) == wanted]


def compute_people(states: dict[str, str | None]) -> tuple[int, list[str], list[str]]:
    """Count household members home.

    home = state exactly "home"; away = state exactly "not_home". A person
    in a named zone is in neither list (matches the dashboard template this
    replaces).
    """
    home = _names_in_state(states, PEOPLE, "home")
    away = _names_in_state(states, PEOPLE, "not_home")
    return len(home), home, away


def compute_vehicles(states: dict[str, str | None]) -> tuple[int, list[str], list[str]]:
    """Count fleet vehicles home (state "home"; away is state "away")."""
    home = _names_in_state(states, VEHICLES, "home")
    away = _names_in_state(states, VEHICLES, "away")
    return len(home), home, away


def _package_count(package_state: str | None, package_attrs: dict) -> int:
    """Delivered parcel count: attribute when present, else 1 if delivered."""
    if package_state != "delivered":
        return 0
    try:
        count = int(package_attrs.get("count"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 1
    return max(count, 1)


def _last_delivery(package_attrs: dict, timestamp_state: str | None) -> str | None:
    """Delivery time as ISO 8601, from the package sensor or the timestamp helper."""
    value = package_attrs.get("last_delivery")
    if value:
        return str(value)
    if timestamp_state:
        try:
            return datetime.fromtimestamp(
                int(timestamp_state), tz=timezone.utc
            ).isoformat()
        except (TypeError, ValueError):
            return timestamp_state
    return None


def compute_package(
    package_state: str | None,
    package_attrs: dict,
    timestamp_state: str | None,
) -> tuple[str, dict]:
    """Package status: "N delivered" when delivered, else "none"."""
    count = _package_count(package_state, package_attrs)
    if package_state == "delivered":
        state = f"{count} delivered"
    else:
        state = "none"
    attrs = {
        "count": count,
        "location": package_attrs.get("location"),
        "last_delivery": _last_delivery(package_attrs, timestamp_state),
    }
    return state, attrs


class CarDashboardSensor(SensorEntity):
    """One of the three car dashboard sensors."""

    _KIND_CONFIG = {
        "people": {
            "name": "Car People Home",
            "object_id": "car_people_home",
            "unique_id": f"{DOMAIN}_people_home",
            "icon": "mdi:account-group",
            "state_class": SensorStateClass.MEASUREMENT,
            "track": list(PEOPLE),
        },
        "vehicles": {
            "name": "Car Vehicles Home",
            "object_id": "car_vehicles_home",
            "unique_id": f"{DOMAIN}_vehicles_home",
            "icon": "mdi:car-multiple",
            "state_class": SensorStateClass.MEASUREMENT,
            "track": list(VEHICLES),
        },
        "package": {
            "name": "Car Package Status",
            "object_id": "car_package_status",
            "unique_id": f"{DOMAIN}_package_status",
            "icon": "mdi:package-variant",
            "state_class": None,
            "track": [PACKAGE_SENSOR, PACKAGE_TIMESTAMP],
        },
    }

    def __init__(self, hass: HomeAssistant, kind: str) -> None:
        """Set up the sensor for one of the three kinds."""
        self.hass = hass
        self._kind = kind
        config = self._KIND_CONFIG[kind]
        self._attr_name = config["name"]
        self._attr_suggested_object_id = config["object_id"]
        self._attr_unique_id = config["unique_id"]
        self._attr_icon = config["icon"]
        self._attr_state_class = config["state_class"]
        self._track = config["track"]
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    def _state_of(self, entity_id: str) -> str | None:
        """Current state string of a source entity, or None if missing."""
        state = self.hass.states.get(entity_id)
        return state.state if state is not None else None

    def _attrs_of(self, entity_id: str) -> dict:
        """Current attributes of a source entity, or {} if missing."""
        state = self.hass.states.get(entity_id)
        return dict(state.attributes) if state is not None else {}

    @callback
    def _recompute(self) -> None:
        """Recompute state + attributes from the current source states."""
        if self._kind == "people":
            count, home, away = compute_people(
                {entity_id: self._state_of(entity_id) for entity_id in PEOPLE}
            )
            self._attr_native_value = count
            self._attr_extra_state_attributes = {"home": home, "away": away}
        elif self._kind == "vehicles":
            count, home, away = compute_vehicles(
                {entity_id: self._state_of(entity_id) for entity_id in VEHICLES}
            )
            self._attr_native_value = count
            self._attr_extra_state_attributes = {"home": home, "away": away}
        else:
            state, attrs = compute_package(
                self._state_of(PACKAGE_SENSOR),
                self._attrs_of(PACKAGE_SENSOR),
                self._state_of(PACKAGE_TIMESTAMP),
            )
            self._attr_native_value = state
            self._attr_extra_state_attributes = attrs

    @callback
    def _handle_event(self, event: Event) -> None:
        """A tracked source entity changed — recompute and publish."""
        self._recompute()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Compute the initial state and subscribe to source changes."""
        self._recompute()
        unsub = async_track_state_change_event(
            self.hass, self._track, self._handle_event
        )
        self.async_on_remove(unsub)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,  # ConfigEntry
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the three car dashboard sensors from a config entry."""
    async_add_entities(
        [CarDashboardSensor(hass, kind) for kind in ("people", "vehicles", "package")]
    )
