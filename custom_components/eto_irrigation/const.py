"""Constants for eto_irrigation."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "eto_irrigation"
DEFAULT_NAME = "ETO Zone"
ATTRIBUTION = "Data provided by OWM and calculations"
MANUFACTURER = "DPK"
CONFIG_FLOW_VERSION = 1

DEFAULT_NAME = "ETO"
DEFAULT_RETRY = 60

# entities for data
CONF_TEMPS = "temperature"
CONF_TEMP_MIN = "temp_min"
CONF_TEMP_MAX = "temp_max"
CONF_HUMIDITY_MIN = "humidity_min"
CONF_HUMIDITY_MAX = "humidity_max"
CONF_WIND = "wind"
CONF_SOLAR_RAD = "solar_rad"
CONF_ALBEDO = "albedo"
CONF_DOY = "day_of_year"

# additional attributes
ATTR_API_RUNTIME = "eto_runtime"

# calculation factors
CALC_S1_5 = "calc_mean_daily_temp_Tmean"
CALC_S2_6 = "calc_mean_daily_solar_rad_Rs"
CALC_S3_7 = "calc_wind_speed_u2"
CALC_S4_9 = "calc_slope_Δ"
CALC_S5_10 = "calc_at_pressure_P"
CALC_S6_11 = "calc_psychrometric_constant_γ"  # noqa: RUF001
CALC_S7_12 = "calc_delta_term_DT"
CALC_S8_13 = "calc_psi_term_PT"
CALC_S9_14 = "calc_temperature_term_TT"
CALC_S10_16 = "calc_max_saturation_vapor_pressure_eTmax"
CALC_S10_17 = "calc_min_saturation_vapor_pressure_eTmin"
CALC_S10_18 = "calc_mean_saturation_vapor_pressure_eT"
CALC_S11_19 = "calc_actual_vapor_pressure_ea"
CALC_S12_23 = "calc_relative_distance_earth_sun_dr"
CALC_S12_24 = "calc_solar_declination_d"
CALC_S13_25 = "calc_latitude_radians_φrad"
CALC_S14_26 = "calc_sunset_hour_angle_ωs"
CALC_S15_27 = "calc_et_rad_Ra"
CALC_S16_28 = "calc_slear_sky_solar_rad_Rso"
CALC_S17_29 = "calc_net_solar_rad_Rns"
CALC_S18_30 = "calc_net_long_wave_solar_rad_Rnl"
CALC_S19_31 = "calc_net_radiation_Rn"
CALC_S19_32 = "calc_net_radiation_eto_Rng"
CALC_FS_33 = "calc_radiation_term_ETrad"
CALC_FS_34 = "calc_wind_term_ETwind"
CALC_FSETO_35 = "calc_evapotranspiration_ETo"

# OTHER FACTORS
W_TO_MJ_DAY_FACTOR = 0.0864  # w * factor = mj/day, same for w/m2 to mj/day/m2
K_TO_C_FACTOR = 273.15  # K-factor = C, C+factor=K
SOLAR_CONSTANT = 0.0820  # MJ m-2 min-1
STEFAN_BOLTZMANN_CONSTANT = 0.000000004903  # [MJ K-4 m-2 day-1]
