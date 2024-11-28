"""The NOAA Weather integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from async_timeout import timeout

from homeassistant.components.sensor import DOMAIN as SENSOR_PLATFORM
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_ELEVATION,
    CONF_HOST,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import noaaweather
from .const import ATTR_FORECAST, CONF_FORECAST, DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.WEATHER]

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations
# type NoaaWeatherConfigEntry = ConfigEntry[noaaweather.NoaaWeatherApi]  # noqa: F821
# just use plain entry: ConfigEntry, nobody uses custom config entry


# TODO Update entry annotation - done, leave default
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NOAA Weather from a config entry."""
    _LOGGER.info("setup, START")
    # Set up fallbabck location
    if not hass.config.latitude or not hass.config.longitude:
        hass.config.latitude = DEFAULT_HOME_LATITUDE
        hass.config.longitude = DEFAULT_HOME_LONGITUDE
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)
    name = entry.data.get(CONF_NAME)
    api_key = entry.data.get(CONF_API_KEY)
    latitude = entry.data.get(CONF_LATITUDE, hass.config.latitude)
    longitude = entry.data.get(CONF_LONGITUDE, hass.config.longitude)

    _LOGGER.info("Name: %s, api_key: %s", name, api_key)
    _LOGGER.info("latitude: %s, longitude: %s", latitude, longitude)

    websession = async_get_clientsession(hass)
    _LOGGER.info("WebSession=%s", websession)
    _LOGGER.info("Creating UpdateCoordinator:")
    coordinator = NOAAWeatherDataUpdateCoordinator(
        hass, websession, api_key, latitude, longitude, name
    )
    _LOGGER.info("call coordinator.async_config_entry_first_refresh():")
    await coordinator.async_config_entry_first_refresh()

    _LOGGER.info("entry.async_on_unload():")
    entry.async_on_unload(entry.add_update_listener(update_listener))
    _LOGGER.info("hass.data.setdefault():")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _LOGGER.info("hass.config_entries.async_forward_entry_setups(%s):", entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("NOAA Weather setup, END")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("NOAA Weather async_unload_entry(), START")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    _LOGGER.info("NOAA Weather async_unload_entry(), END")
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    _LOGGER.info("NOAA Weather update_listener(), START")
    await hass.config_entries.async_reload(entry.entry_id)
    _LOGGER.info("NOAA Weather update_listener(), END")


class NOAAWeatherDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching NOAA weather data API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        api_key: Optional[str],
        lat: float,
        lon: float,
        name: str,
    ) -> None:
        """Initialize."""
        _LOGGER.info("NOAA Weather NOAAWeatherDataUpdateCoordinator(), START")
        self.api_key = api_key
        self.location_key = "NOAA"
        self.forecast = True
        self.lat = lat  # hass.config.latitude
        self.lon = lon  # hass.config.longitude
        self.name = name
        self.noaaweather = noaaweather.NOAAWeather(self.lat, self.lon, None, None)
        self.device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, "NOAA")},
            manufacturer=MANUFACTURER,
            name=name,
            # You don't need to provide specific details for the URL,
            # so passing in _ characters is fine if the location key
            # is correct
            configuration_url=(f"https://api.weather.gov/points/{lat},{lon}"),
        )

        # Enabling the forecast download increases the number of requests per data
        # update, we use 40 minutes for current condition only and 80 minutes for
        # current condition and forecast as update interval to not exceed allowed number
        # of requests. We have 50 requests allowed per day, so we use 36 and leave 14 as
        # a reserve for restarting HA.
        update_interval = timedelta(minutes=10)
        _LOGGER.info("Data will be updated every %s", update_interval)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        _LOGGER.info("NOAA Weather NOAAWeatherDataUpdateCoordinator(), END")

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        _LOGGER.info("NOAA Weather _async_update_data(), START")
        forecast: list[dict[str, Any]] = []
        try:
            async with timeout(10):
                current = await self.noaaweather.async_get_current_conditions()
                forecast = await self.noaaweather.async_get_daily_forecast()
        except (
            noaaweather.ApiError,
            noaaweather.ClientConnectorError,
            noaaweather.InvalidApiKeyError,
            noaaweather.RequestsExceededError,
        ) as error:
            raise UpdateFailed(error) from error
        # _LOGGER.info("Requests remaining: %d", self.noaaweather.requests_remaining)
        _LOGGER.info("Requests remaining: %d", -1)
        _LOGGER.info("NOAA Weather _async_update_data(), START")
        return {**current, ATTR_FORECAST: forecast}
