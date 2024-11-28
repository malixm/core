from typing import Any


class ApiError(Exception):
    """Base class for exceptions raised by an API."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ClientConnectorError(ApiError):
    """Base class for exceptions raised by an API."""

    def __init__(self, message, status_code=None, response=None):
        message = "Client Connector Error." + message
        super().__init__(message, status_code, response)


class InvalidApiKeyError(ApiError):
    """Base class for exceptions raised by an API."""

    def __init__(self, message, status_code=None, response=None):
        message = "Invalid API Key." + message
        super().__init__(message, status_code, response)


class RequestsExceededError(ApiError):
    """Base class for exceptions raised by an API."""

    def __init__(self, message, status_code=None, response=None):
        message = "Requests Exceeded." + message
        super().__init__(message, status_code, response)


class NOAAWeather:
    def __init__(
        self,
        lat: float,
        lon: float,
        url: str | None = None,
        api_key: str | None = None,
    ):
        pass

    async def async_get_current_conditions(self) -> dict[str, Any]:
        current = {
            "Temperature": {"Unit": "C", "UnitType": 17, "Value": 25.5},
            "DewPoint": {"Unit": "C", "UnitType": 17, "Value": 18.3},
            "RelativeHumidity": 62,
            "WindChillTemperature": {"Unit": "C", "UnitType": 17, "Value": None},
            "ApparentTemperature": {"Unit": "C", "UnitType": 17, "Value": 27.8},
            "Wind": {
                "Direction": {"Degrees": 140, "English": "SE", "Localized": "SE"},
                "Speed": {"Unit": "km/h", "UnitType": 7, "Value": 15.4},
            },
            "Visibility": {"Unit": "km", "UnitType": 6, "Value": 16.1},
            "CloudCover": 30,
            "Precipitation": {"Unit": "mm/h", "UnitType": 3, "Value": 0},
            "WeatherIcon": 34,
            "WeatherText": "Mostly sunny",
        }
        return current

    async def async_get_daily_forecast(self) -> list[dict[str, Any]]:
        forecast = [
            {
                "EpochDate": 1697817600,
                "TemperatureMax": {"Unit": "C", "UnitType": 17, "Value": 28.9},
                "TemperatureMin": {"Unit": "C", "UnitType": 17, "Value": 19.4},
                "RealFeelTemperatureMax": {"Unit": "C", "UnitType": 17, "Value": 32.2},
                "RealFeelTemperatureMin": {"Unit": "C", "UnitType": 17, "Value": 18.9},
                "TotalLiquidDay": {"Unit": "mm", "UnitType": 3, "Value": 0.5},
                "PrecipitationProbabilityDay": 30,
                "WindDay": {
                    "Direction": {"Degrees": 165, "English": "SSE", "Localized": "SSE"},
                    "Speed": {"Unit": "km/h", "UnitType": 7, "Value": 12.9},
                },
                "WindGustDay": {
                    "Direction": {"Degrees": 170, "English": "S", "Localized": "S"},
                    "Speed": {"Unit": "km/h", "UnitType": 7, "Value": 20.4},
                },
                "CloudCoverDay": 40,
                "IconDay": 36,
            },
            {
                "EpochDate": 1729472302,
                "TemperatureMax": {"Unit": "C", "UnitType": 17, "Value": 18.1},
                "TemperatureMin": {"Unit": "C", "UnitType": 17, "Value": 1.5},
                "RealFeelTemperatureMax": {"Unit": "C", "UnitType": 17, "Value": 22.8},
                "RealFeelTemperatureMin": {"Unit": "C", "UnitType": 17, "Value": 0.9},
                "TotalLiquidDay": {"Unit": "mm", "UnitType": 3, "Value": 3.5},
                "PrecipitationProbabilityDay": 30,
                "WindDay": {
                    "Direction": {"Degrees": 42, "English": "SSE", "Localized": "SSE"},
                    "Speed": {"Unit": "km/h", "UnitType": 7, "Value": 33.9},
                },
                "WindGustDay": {
                    "Direction": {"Degrees": 30, "English": "S", "Localized": "S"},
                    "Speed": {"Unit": "km/h", "UnitType": 7, "Value": 49.4},
                },
                "CloudCoverDay": 90,
                "IconDay": 36,
            },
        ]
        return forecast
