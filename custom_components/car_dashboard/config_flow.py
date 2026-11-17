"""Config flow for the Car Dashboard integration."""

from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class CarDashboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Car Dashboard."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step — single instance, no settings."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Car Dashboard", data={})

        return self.async_show_form(step_id="user")
