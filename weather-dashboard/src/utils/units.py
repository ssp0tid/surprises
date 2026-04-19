"""Unit conversion utilities for metric/imperial units."""

from enum import Enum


class Units(str, Enum):
    """Unit system enumeration."""

    METRIC = "metric"
    IMPERIAL = "imperial"


# Unit labels
METRIC_LABELS = {
    "temperature": "°C",
    "wind_speed": "km/h",
    "precipitation": "mm",
}

IMPERIAL_LABELS = {
    "temperature": "°F",
    "wind_speed": "mph",
    "precipitation": "in",
}


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5 / 9


def kmh_to_mph(kmh: float) -> float:
    """Convert km/h to mph."""
    return kmh * 0.621371


def mph_to_kmh(mph: float) -> float:
    """Convert mph to km/h."""
    return mph * 1.60934


def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm * 0.0393701


def inches_to_mm(inches: float) -> float:
    """Convert inches to millimeters."""
    return inches / 0.0393701


def convert_temperature(temp: float, units: Units) -> float:
    """Convert temperature to the specified unit system."""
    if units == Units.IMPERIAL:
        return celsius_to_fahrenheit(temp)
    return temp


def convert_wind_speed(speed: float, units: Units) -> float:
    """Convert wind speed to the specified unit system."""
    if units == Units.IMPERIAL:
        return kmh_to_mph(speed)
    return speed


def convert_precipitation(precip: float, units: Units) -> float:
    """Convert precipitation to the specified unit system."""
    if units == Units.IMPERIAL:
        return mm_to_inches(precip)
    return precip


def get_unit_label(unit_type: str, units: Units) -> str:
    """Get the unit label for the specified unit type and system."""
    if units == Units.IMPERIAL:
        return IMPERIAL_LABELS.get(unit_type, "")
    return METRIC_LABELS.get(unit_type, "")


def format_temperature(temp: float, units: Units, decimals: int = 1) -> str:
    """Format temperature with unit suffix."""
    converted = convert_temperature(temp, units)
    unit = get_unit_label("temperature", units)
    return f"{converted:.{decimals}f}{unit}"


def format_wind_speed(speed: float, units: Units, decimals: int = 1) -> str:
    """Format wind speed with unit suffix."""
    converted = convert_wind_speed(speed, units)
    unit = get_unit_label("wind_speed", units)
    return f"{converted:.{decimals}f} {unit}"


def format_precipitation(precip: float, units: Units, decimals: int = 1) -> str:
    """Format precipitation with unit suffix."""
    converted = convert_precipitation(precip, units)
    unit = get_unit_label("precipitation", units)
    return f"{converted:.{decimals}f} {unit}"
