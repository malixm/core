"""Support for the NOAA Weather service."""

from __future__ import annotations

import logging
from typing import cast

from homeassistant.components.weather import (
    ATTR_FORECAST_CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_APPARENT_TEMP,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utc_from_timestamp

from . import NOAAWeatherDataUpdateCoordinator
from .const import (
    ATTR_DIRECTION,
    ATTR_FORECAST,
    ATTR_SPEED,
    ATTR_VALUE,
    ATTRIBUTION,
    CONDITION_CLASSES,
    DOMAIN,
)

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add a NOAA Weather weather entity from a config_entry."""

    coordinator: NOAAWeatherDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.info("Add async_add_entities to coordinator %s", coordinator)

    async_add_entities([NOAAWeatherEntity(coordinator)])


class NOAAWeatherEntity(
    CoordinatorEntity[NOAAWeatherDataUpdateCoordinator], WeatherEntity
):
    """Define an NOAA Weather entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: NOAAWeatherDataUpdateCoordinator) -> None:
        """Initialize."""
        _LOGGER.info("Initializing weather entity.")
        super().__init__(coordinator)
        # Coordinator data is used also for sensors which don't have units automatically
        # converted, hence the weather entity's native units follow the configured unit
        # system
        self._attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
        self._attr_native_pressure_unit = UnitOfPressure.HPA
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_native_visibility_unit = UnitOfLength.KILOMETERS
        self._attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
        self._attr_unique_id = coordinator.location_key
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = coordinator.device_info
        self._attr_supported_features = (
            WeatherEntityFeature.FORECAST_DAILY
        )  # add also: FORECAST_TWICE_DAILY, FORECAST_HOURLY
        # https://developers.home-assistant.io/docs/core/entity/weather/#supported-features
        # and implement methods async_forecast_xxx

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        try:
            return [
                k
                for k, v in CONDITION_CLASSES.items()
                if self.coordinator.data["WeatherIcon"] in v
            ][0]
        except IndexError:
            return None

    @property
    def cloud_coverage(self) -> float:
        """Return the Cloud coverage in %."""
        return cast(float, self.coordinator.data["CloudCover"])

    @property
    def native_apparent_temperature(self) -> float:
        """Return the apparent temperature."""
        return cast(float, self.coordinator.data["ApparentTemperature"][ATTR_VALUE])

    @property
    def native_temperature(self) -> float:
        """Return the temperature."""
        return cast(float, self.coordinator.data["Temperature"][ATTR_VALUE])

    @property
    def native_pressure(self) -> float:
        """Return the pressure."""
        return cast(float, self.coordinator.data.get("Pressure").get(ATTR_VALUE))

    @property
    def native_dew_point(self) -> float:
        """Return the dew point."""
        return cast(float, self.coordinator.data["DewPoint"][ATTR_VALUE])

    @property
    def humidity(self) -> int:
        """Return the humidity."""
        return cast(int, self.coordinator.data["RelativeHumidity"])

    @property
    def native_wind_gust_speed(self) -> float:
        """Return the wind gust speed."""
        return cast(float, self.coordinator.data["WindGust"][ATTR_SPEED][ATTR_VALUE])

    @property
    def native_wind_speed(self) -> float:
        """Return the wind speed."""
        return cast(float, self.coordinator.data["Wind"][ATTR_SPEED][ATTR_VALUE])

    @property
    def wind_bearing(self) -> int:
        """Return the wind bearing."""
        return cast(int, self.coordinator.data["Wind"][ATTR_DIRECTION]["Degrees"])

    @property
    def native_visibility(self) -> float:
        """Return the visibility."""
        return cast(float, self.coordinator.data["Visibility"][ATTR_VALUE])

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return the forecast array."""
        if not self.coordinator.forecast:
            return None
        # remap keys from library to keys understood by the weather component
        return [
            {
                ATTR_FORECAST_TIME: utc_from_timestamp(item["EpochDate"]).isoformat(),
                ATTR_FORECAST_CLOUD_COVERAGE: item["CloudCoverDay"],
                ATTR_FORECAST_NATIVE_TEMP: item["TemperatureMax"][ATTR_VALUE],
                ATTR_FORECAST_NATIVE_TEMP_LOW: item["TemperatureMin"][ATTR_VALUE],
                ATTR_FORECAST_NATIVE_APPARENT_TEMP: item["RealFeelTemperatureMax"][
                    ATTR_VALUE
                ],
                ATTR_FORECAST_NATIVE_PRECIPITATION: item["TotalLiquidDay"][ATTR_VALUE],
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: item[
                    "PrecipitationProbabilityDay"
                ],
                ATTR_FORECAST_NATIVE_WIND_SPEED: item["WindDay"][ATTR_SPEED][
                    ATTR_VALUE
                ],
                ATTR_FORECAST_NATIVE_WIND_GUST_SPEED: item["WindGustDay"][ATTR_SPEED][
                    ATTR_VALUE
                ],
                ATTR_FORECAST_WIND_BEARING: item["WindDay"][ATTR_DIRECTION]["Degrees"],
                ATTR_FORECAST_CONDITION: [
                    k for k, v in CONDITION_CLASSES.items() if item["IconDay"] in v
                ][0],
            }
            for item in self.coordinator.data[ATTR_FORECAST]
        ]

    # async def async_forecast_daily(self) -> list[Forecast] | None:
    #     """Return the daily forecast in native units.

    #     Only implement this method if `WeatherEntityFeature.FORECAST_DAILY` is set
    #     """
    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return [
            {
                ATTR_FORECAST_TIME: utc_from_timestamp(item["EpochDate"]).isoformat(),
                ATTR_FORECAST_CLOUD_COVERAGE: item["CloudCoverDay"],
                ATTR_FORECAST_HUMIDITY: item["RelativeHumidityDay"]["Average"],
                ATTR_FORECAST_NATIVE_TEMP: item["TemperatureMax"][ATTR_VALUE],
                ATTR_FORECAST_NATIVE_TEMP_LOW: item["TemperatureMin"][ATTR_VALUE],
                ATTR_FORECAST_NATIVE_APPARENT_TEMP: item["RealFeelTemperatureMax"][
                    ATTR_VALUE
                ],
                ATTR_FORECAST_NATIVE_PRECIPITATION: item["TotalLiquidDay"][ATTR_VALUE],
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: item[
                    "PrecipitationProbabilityDay"
                ],
                ATTR_FORECAST_NATIVE_WIND_SPEED: item["WindDay"][ATTR_SPEED][
                    ATTR_VALUE
                ],
                ATTR_FORECAST_NATIVE_WIND_GUST_SPEED: item["WindGustDay"][ATTR_SPEED][
                    ATTR_VALUE
                ],
                ATTR_FORECAST_UV_INDEX: item["UVIndex"][ATTR_VALUE],
                ATTR_FORECAST_WIND_BEARING: item["WindDay"][ATTR_DIRECTION]["Degrees"],
                ATTR_FORECAST_CONDITION: CONDITION_MAP.get(item["IconDay"]),
            }
            for item in self.daily_coordinator.data
        ]

    # async def async_forecast_twice_daily(self) -> list[Forecast] | None:
    #     """Return the twice daily forecast in native units.

    #     Only implement this method if `WeatherEntityFeature.FORECAST_TWICE_DAILY` is set
    #     """

    # async def async_forecast_hourly(self) -> list[Forecast] | None:
    #     """Return the hourly forecast in native units.

    #     Only implement this method if `WeatherEntityFeature.FORECAST_HOURLY` is set
    #     """
