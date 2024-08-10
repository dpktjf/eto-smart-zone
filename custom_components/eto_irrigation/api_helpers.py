"""The Smart Irrigation Integration."""

import logging
import math

from numpy import floating, mean

from custom_components.eto_irrigation.const import (
    K_TO_C_FACTOR,
    SOLAR_CONSTANT,
    STEFAN_BOLTZMANN_CONSTANT,
)

_LOGGER = logging.getLogger(__name__)


def c_to_k(celcius: float) -> float:
    """
    Convert degrees celcius to Kelvin.

    :param celcius: the temperature in C
    :return Kelvin
    :rtype float
    """
    return celcius + K_TO_C_FACTOR


def deg2rad(degrees: float) -> float:
    """
    Convert angular degrees to radians.

    :param degrees: Value in degrees to be converted.
    :return: Value in radians
    :rtype: float
    """
    return degrees * (math.pi / 180.0)


# Internal constants
# Latitude
_MINLAT_RADIANS = deg2rad(-90.0)
_MAXLAT_RADIANS = deg2rad(90.0)

# Solar declination
_MINSOLDEC_RADIANS = deg2rad(-23.5)
_MAXSOLDEC_RADIANS = deg2rad(23.5)

# Sunset hour angle
_MINSHA_RADIANS = 0.0
_MAXSHA_RADIANS = deg2rad(180)


def _check_doy(doy: int) -> None:
    """Check day of the year is valid."""
    if not 1 <= doy <= 366:  # noqa: PLR2004
        msg = f"Day of the year (doy) must be in range 1-366: {doy!r}"
        raise ValueError(msg)


def _check_latitude_rad(latitude: float) -> None:
    if not _MINLAT_RADIANS <= latitude <= _MAXLAT_RADIANS:
        msg = f"latitude outside valid range {_MINLAT_RADIANS!r} to \
            {_MAXLAT_RADIANS!r} rad: {latitude!r}"
        raise ValueError(msg)


def _check_sol_dec_rad(sd: float) -> None:
    """
    Solar declination can vary between -23.5 and +23.5 degrees.

    See http://mypages.iit.edu/~maslanka/SolarGeo.pdf
    """
    if not _MINSOLDEC_RADIANS <= sd <= _MAXSOLDEC_RADIANS:
        msg = f"solar declination outside valid range {_MINSOLDEC_RADIANS!r} to \
            {_MAXSOLDEC_RADIANS!r} rad: {sd!r}"
        raise ValueError(msg)


def _check_sunset_hour_angle_rad(sha: float) -> None:
    """
    Sunset hour angle has the range 0 to 180 degrees.

    See http://mypages.iit.edu/~maslanka/SolarGeo.pdf
    """
    if not _MINSHA_RADIANS <= sha <= _MAXSHA_RADIANS:
        msg = f"sunset hour angle outside valid range {_MINSHA_RADIANS!r} to \
            {_MAXSHA_RADIANS!r} rad: {sha!r}"
        raise ValueError(msg)


def wind_speed(wind: float, height: float) -> float:
    """
    Calculate wind speed.

    The average daily wind speed in meters per second (ms-1) measured at 2m
    above the ground level is required.

    Based on step 3 equation 7 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param wind: wind speed at the given height in ms-1
    :param height: the height of the observed wind speed in m
    :return Wind speed at 2m [ms-1]
    :rtype float
    """
    numer: float = math.log(67.8 * height - 5.42)
    return wind * 4.87 / numer


def delta_svp(t: float) -> float:
    """
    Estimate the slope of the saturation vapour pressure curve at a given temperature.

    Based on step 4 equation 9 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param t: Air temperature [deg C]. Use mean air temperature for use in
        Penman-Monteith.
    :return: Saturation vapour pressure [kPa degC-1]
    :rtype: float
    """
    tmp = 4098 * (0.6108 * math.exp((17.27 * t) / (c_to_k(t))))
    return tmp / math.pow(c_to_k(t), 2)


def atm_pressure(altitude: float) -> float:
    """
    Estimate atmospheric pressure from altitude.

    Based on step 5 equation 10 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param altitude: Elevation/altitude above sea level [m]
    :return: atmospheric pressure [kPa]
    :rtype: float
    """
    tmp = (293.0 - (0.0065 * altitude)) / 293.0
    return math.pow(tmp, 5.26) * 101.3


def psy_const(atmos_pres: float) -> float:
    """
    Calculate the psychrometric constant.

    This method assumes that the air is saturated with water vapour at the
    minimum daily temperature. This assumption may not hold in arid areas.

    Based on step 6 equation 11 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param atmos_pres: Atmospheric pressure [kPa]. Can be estimated using
        ``atm_pressure()``.
    :return: Psychrometric constant [kPa degC-1].
    :rtype: float
    """
    return 0.000665 * atmos_pres


def delta_term(slope: float, psycho: float, wind_speed: float) -> float:
    """
    Calculate the Delta Term.

    The delta term is used to calculate the Radiation Term of the overall ETo equation

    Based on step 7 equation 12 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param slope: slope of saturation vapor curve
    :param psycho: psychrometric constant
    :param wind_speed: wind speed 2 m above the ground surface, m s-1

    :return: Delta Term [kPa degC-1].
    :rtype: float
    """
    numer: float = psycho * (1 + (0.34 * wind_speed)) + slope
    return slope / numer


def psi_term(slope: float, psycho: float, wind_speed: float) -> float:
    """
    Calculate the Psi Term.

    The psi term is used to calculate the Wind Term of the overall ETo equation

    Based on step 8 equation 13 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param slope: slope of saturation vapor curve
    :param psycho: psychrometric constant
    :param wind_speed: wind speed 2 m above the ground surface, m s-1

    :return: Psi Term.
    :rtype: float
    """
    numer: float = slope + psycho * (1 + 0.34 * wind_speed)
    return psycho / numer


def temperature_term(mean_temp: float, wind_speed: float) -> float:
    """
    Calculate the Temperature Term.

    The temperature term is used to calculate the Wind Term of the overall ETo
    equation.

    Based on step 9 equation 14 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param mean_temp: mean daily air temperature, ºC
    :param wind_speed: wind speed 2 m above the ground surface, m s-1

    :return: Temperature Term.
    :rtype: float
    """
    return (900 / (mean_temp + 273)) * wind_speed


def svp_from_t(t: float) -> float:
    """
    Estimate saturation vapour pressure (*es*) from air temperature.

    Based on step 10 equation 15, 16, 17 - Step by Step Calculation of the
    Penman-Monteith Evapotranspiration (FAO-56 Method)

    :param t: Temperature [deg C]
    :return: Saturation vapour pressure [kPa]
    :rtype: float
    """
    return 0.6108 * math.exp((17.27 * t) / c_to_k(t))


def ea_from_rh(t: float, h: float) -> float:
    """
    Calculate vapour pressure from humidity.

    Based on step 11 equation 19 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param t: Temperature [deg C]
    :param h: Humidity [%]
    :return: Saturation vapour pressure [kPa]
    :rtype: float
    """
    return t * h


def inv_rel_dist_earth_sun(day_of_year: int) -> float:
    """
    Calculate the inverse relative distance between earth and sun from day of the year.

    Based on step 12 equation 23 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param day_of_year: Day of the year [1 to 366]
    :return: Inverse relative distance between earth and the sun
    :rtype: float
    """
    _check_doy(day_of_year)
    return 1 + (0.033 * math.cos((2.0 * math.pi / 365.0) * day_of_year))


def sol_dec(day_of_year: int) -> float:
    """
    Calculate solar declination from day of the year.

    Based on step 12 equation 24 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param day_of_year: Day of year integer between 1 and 365 or 366).
    :return: solar declination [radians]
    :rtype: float
    """
    _check_doy(day_of_year)
    return 0.409 * math.sin((2.0 * math.pi / 365.0) * day_of_year - 1.39)


def sunset_hour_angle(latitude: float, sol_dec: float) -> float:
    """
    Calculate sunset hour angle (*Ws*) from latitude and solar declination.

    Based on step 14 equation 26 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param latitude: Latitude [radians]. Note: *latitude* should be negative
        if it in the southern hemisphere, positive if in the northern
        hemisphere.
    :param sol_dec: Solar declination [radians]. Can be calculated using
        ``sol_dec()``.
    :return: Sunset hour angle [radians].
    :rtype: float
    """
    _check_latitude_rad(latitude)
    _check_sol_dec_rad(sol_dec)

    cos_sha = -math.tan(latitude) * math.tan(sol_dec)
    # If tmp is >= 1 there is no sunset, i.e. 24 hours of daylight
    # If tmp is <= 1 there is no sunrise, i.e. 24 hours of darkness
    # See http://www.itacanet.org/the-sun-as-a-source-of-energy/
    # part-3-calculating-solar-angles/
    # Domain of acos is -1 <= x <= 1 radians (this is not mentioned in FAO-56!)
    return math.acos(min(max(cos_sha, -1.0), 1.0))


def et_rad(latitude: float, sol_dec: float, sha: float, ird: float) -> float:
    """
    Estimate daily extraterrestrial radiation (*Ra*, 'top of the atmosphere radiation').

    Based on step 15 equation 27 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)


    :param latitude: Latitude [radians]
    :param sol_dec: Solar declination [radians]. Can be calculated using
        ``sol_dec()``.
    :param sha: Sunset hour angle [radians]. Can be calculated using
        ``sunset_hour_angle()``.
    :param ird: Inverse relative distance earth-sun [dimensionless]. Can be
        calculated using ``inv_rel_dist_earth_sun()``.
    :return: Daily extraterrestrial radiation [MJ m-2 day-1]
    :rtype: float
    """
    _check_latitude_rad(latitude)
    _check_sol_dec_rad(sol_dec)
    _check_sunset_hour_angle_rad(sha)

    tmp1 = (24.0 * 60.0) / math.pi
    tmp2 = sha * math.sin(latitude) * math.sin(sol_dec)
    tmp3 = math.cos(latitude) * math.cos(sol_dec) * math.sin(sha)
    return tmp1 * SOLAR_CONSTANT * ird * (tmp2 + tmp3)


def cs_rad(altitude: float, et_rad: float) -> float:
    """
    Estimate clear sky radiation from altitude and extraterrestrial radiation.

    Based on step 16 equation 28 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param altitude: Elevation above sea level [m]
    :param et_rad: Extraterrestrial radiation [MJ m-2 day-1]. Can be
        estimated using ``et_rad()``.
    :return: Clear sky radiation [MJ m-2 day-1]
    :rtype: float
    """
    return (0.00002 * altitude + 0.75) * et_rad


def net_in_sol_rad(sol_rad: float, albedo: float) -> float:
    """
    Calculate net incoming solar (or shortwave) radiation.

    Net incoming solar radiation is the net shortwave radiation resulting
    from the balance between incoming and reflected solar radiation given some
    reference crop (albedo). The output can be converted to equivalent
    evaporation [mm day-1] using ``energy2evap()``.

    Based on step 17 equation 29 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param sol_rad: Gross incoming solar radiation [MJ m-2 day-1]. If
        necessary this can be estimated using functions whose name
        begins with 'sol_rad_from'.
    :param albedo: Albedo of the crop as the proportion of gross incoming solar
        radiation that is reflected by the surface. Default value is 0.23,
        which is the value used by the FAO for a short grass reference crop.
        Albedo can be as high as 0.95 for freshly fallen snow and as low as
        0.05 for wet bare soil. A green vegetation over has an albedo of
        about 0.20-0.25 (Allen et al, 1998).
    :return: Net incoming solar (or shortwave) radiation [MJ m-2 day-1].
    :rtype: float
    """
    return (1 - albedo) * sol_rad


def net_out_lw_rad(
    tmin: float, tmax: float, sol_rad: float, cs_rad: float, avp: float
) -> float:
    """
    Estimate net outgoing longwave radiation.

    This is the net longwave energy (net energy flux) leaving the
    earth's surface. It is proportional to the absolute temperature of
    the surface raised to the fourth power according to the Stefan-Boltzmann
    law. However, water vapour, clouds, carbon dioxide and dust are absorbers
    and emitters of longwave radiation. This function corrects the Stefan-
    Boltzmann law for humidity (using actual vapor pressure) and cloudiness
    (using solar radiation and clear sky radiation). The concentrations of all
    other absorbers are assumed to be constant.

    The output can be converted to equivalent evaporation [mm day-1] using
    ``energy2evap()``.

    Based on step 18 equation 30 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param tmin: Absolute daily minimum temperature [degrees Kelvin]
    :param tmax: Absolute daily maximum temperature [degrees Kelvin]
    :param sol_rad: Solar radiation [MJ m-2 day-1]. If necessary this can be
        estimated using ``sol+rad()``.
    :param cs_rad: Clear sky radiation [MJ m-2 day-1]. Can be estimated using
        ``cs_rad()``.
    :param avp: Actual vapour pressure [kPa]. Can be estimated using functions
        with names beginning with 'avp_from'.
    :return: Net outgoing longwave radiation [MJ m-2 day-1]
    :rtype: float
    """
    tmp1: floating = STEFAN_BOLTZMANN_CONSTANT * mean(
        [math.pow(tmax, 4), math.pow(tmin, 4)]
    )
    tmp2: float = 0.34 - (0.14 * math.sqrt(avp))
    tmp3: float = 1.35 * (sol_rad / cs_rad) - 0.35
    return tmp1 * tmp2 * tmp3  # type: ignore  # noqa: PGH003


def net_rad(net_solar: float, lw_rad: float) -> float:
    """
    Calculate net radiation.

    The net radiation (Rn) is the difference between the incoming net shortwave
    radiation (Rns) and the outgoing net longwave radiation (Rnl):

    Based on step 19 equation 31 - Step by Step Calculation of the
    Penman-Monteith Evapotranspiration (FAO-56 Method)

    :param net_solar: net solar or shortwave radiation, MJ m-2 day-1, [Step 17,
        Eq. 29]
    :param lw_rad: net outgoing longwave radiation, MJ m-2 day-1,[Step 18, Eq.
        30].
    :return: Net radiation [MJ m-2 day-1].
    :rtype: float
    """
    return net_solar - lw_rad


def net_rad_eto(net_rad: float) -> float:
    """
    Express the net radiation (Rn) in equivalent of evaporation (mm) (Rng).

    Based on step 19 equation 32 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param net_rad: The net radiation MJ m-2 day-1, [Step 19, Eq. 31]
    :return: Net radiation in equivalent of evaporation (mm).
    :rtype: float
    """
    return net_rad * 0.408


def radiation_term(delta_term: float, net_rad: float) -> float:
    """
    Calculate radiation term for overall ETO equation.

    Based on final step equation 33 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param delta_term: Step 7, Eq. 12
    :param net_rad: net radiation, mm, [Eq. 32]
    :return: Radiation term [mm day-1].
    :rtype: float
    """
    return delta_term * net_rad


def wind_term(
    psi_term: float, temp_term: float, actual_vp: float, mean_sat_vp: float
) -> float:
    """
    Calculate wind term for overall ETO equation.

    Based on final step equation 34 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param psi_term: Psi term, [Step 8, Eq. 13]
    :param temp_term: Temperature term, [Step 9, Eq. 14]
    :param actual_vp: actual vapor pressure, kPa, [Step 11, Eq. 19]
    :param mean_sat_vp: mean saturation vapor pressure derived from air
        temperature, kPa, [Step 10, Eq. 15]
    :return: Wind term [mm day-1].
    :rtype: float
    """
    return psi_term * temp_term * (mean_sat_vp - actual_vp)


def eto(wind_term: float, rad_term: float) -> float:
    """
    Calculate Final Reference Evapotranspiration Value.

    Based on final step equation 35 - Step by Step Calculation of the Penman-Monteith
    Evapotranspiration (FAO-56 Method)

    :param wind_term: wind term, mm d-1 [Eq. 34]
    :param rad_term: radiation term, mm d-1, [Eq. 33]
    :return: Final Reference Evapotranspiration Value [mm day-1].
    :rtype: float
    """
    # raise ValueError("test error")  # noqa: ERA001
    return round(wind_term + rad_term, 1)


def calc_duration(eto: float, rain: float, throughput: float) -> int:
    """
    Calculate runtime duration in seconds.

    Calculate difference between the days rain fall and the required ETO and if
    negative, then watering is required. Calculate based on the delta and
    sprinkler throughput provided.

    :param eto: Final Reference Evapotranspiration Value [mm day-1]
    :param rain: Daily rainfall [mm]
    :param throughput: Sprinkler throughput [mm hour-1]
    :rtype: int
    """
    delta: float = rain - eto
    if delta < 0:
        # not enough rainfall for the day given ETO; work out runtime duration
        reqd: float = abs(delta) / throughput * 60 * 60
        return round(reqd)
    return 0
