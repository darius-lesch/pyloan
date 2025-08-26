# -*- coding: utf-8 -*-
"""
This module contains functions for calculating the number of days between two dates
based on different day count conventions.
"""

import calendar as cal
from datetime import datetime
from typing import Dict, Callable, Tuple

def _get_julian_day_number(y: int, m: int, d: int) -> float:
    """
    Calculates the Julian day number for a given date.
    """
    return (1461 * (y + 4800 + (m - 14) / 12)) / 4 + (367 * (m - 2 - 12 * ((m - 14) / 12))) / 12 - (
                3 * ((y + 4900 + (m - 14) / 12) / 100)) / 4 + d - 32075


def _thirty_a_360(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[int, int]:
    """
    Calculates the number of days between two dates using the 30A/360 convention.
    """
    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day

    d1 = min(d1, 30)
    d2 = min(d2, 30) if d1 == 30 else d2

    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)), 360


def _thirty_u_360(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[int, int]:
    """
    Calculates the number of days between two dates using the 30U/360 convention.
    """
    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day
    dt1_eom_day = cal.monthrange(y1, m1)[1]
    dt2_eom_day = cal.monthrange(y2, m2)[1]

    if eom and m1 == 2 and d1 == dt1_eom_day and m2 == 2 and d2 == dt2_eom_day:
        d2 = 30
    if eom and m1 == 2 and d1 == dt1_eom_day:
        d1 = 30
    if d2 == 31 and d1 >= 30:
        d2 = 30
    if d1 == 31:
        d1 = 30

    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)), 360


def _thirty_e_360(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[int, int]:
    """
    Calculates the number of days between two dates using the 30E/360 convention.
    """
    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day

    if d1 == 31:
        d1 = 30
    if d2 == 31:
        d2 = 30

    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)), 360


def _thirty_e_360_isda(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[int, int]:
    """
    Calculates the number of days between two dates using the 30E/360 ISDA convention.
    """
    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day
    dt1_eom_day = cal.monthrange(y1, m1)[1]
    dt2_eom_day = cal.monthrange(y2, m2)[1]

    if d1 == dt1_eom_day:
        d1 = 30
    if d2 == dt2_eom_day and m2 != 2:
        d2 = 30

    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)), 360


def _a_365f(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[int, int]:
    """
    Calculates the number of days between two dates using the A/365F convention.
    """
    return (dt2 - dt1).days, 365


def _a_360(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[int, int]:
    """
    Calculates the number of days between two dates using the A/360 convention.
    """
    return (dt2 - dt1).days, 360


def _a_a_isda(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[float, float]:
    """
    Calculates the number of days between two dates using the A/A ISDA convention.
    """
    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day

    djn_dt1 = _get_julian_day_number(y1, m1, d1)
    djn_dt2 = _get_julian_day_number(y2, m2, d2)

    if y1 == y2:
        day_count = djn_dt2 - djn_dt1
        year_days = 366 if cal.isleap(y2) else 365
    else:
        djn_dt1_eoy = _get_julian_day_number(y1, 12, 31)
        day_count_dt1 = djn_dt1_eoy - djn_dt1
        year_days_dt1 = 366 if cal.isleap(y1) else 365

        djn_dt2_boy = _get_julian_day_number(y2, 1, 1)
        day_count_dt2 = djn_dt2 - djn_dt2_boy
        year_days_dt2 = 366 if cal.isleap(y2) else 365

        diff = y2 - y1 - 1

        day_count = (day_count_dt1 * year_days_dt2) + (day_count_dt2 * year_days_dt1) + (
                    diff * year_days_dt1 * year_days_dt2)
        year_days = year_days_dt1 * year_days_dt2

    return day_count, year_days


def _a_a_afb(dt1: datetime, dt2: datetime, eom: bool = False) -> Tuple[float, float]:
    """
    Calculates the number of days between two dates using the A/A AFB convention.
    """
    y1, m1, d1 = dt1.year, dt1.month, dt1.day
    y2, m2, d2 = dt2.year, dt2.month, dt2.day

    djn_dt1 = _get_julian_day_number(y1, m1, d1)
    djn_dt2 = _get_julian_day_number(y2, m2, d2)

    if y1 == y2:
        day_count = djn_dt2 - djn_dt1
        year_days = 366 if cal.isleap(y1) and (m1 < 3) else 365
    else:
        djn_dt1_eoy = _get_julian_day_number(y1, 12, 31)
        day_count_dt1 = djn_dt1_eoy - djn_dt1
        year_days_dt1 = 366 if cal.isleap(y1) and (m1 < 3) else 365

        djn_dt2_boy = _get_julian_day_number(y2, 1, 1)
        day_count_dt2 = djn_dt2 - djn_dt2_boy
        year_days_dt2 = 366 if cal.isleap(y2) and (m2 >= 3) else 365

        diff = y2 - y1 - 1

        day_count = (day_count_dt1 * year_days_dt2) + (day_count_dt2 * year_days_dt1) + (
                    diff * year_days_dt1 * year_days_dt2)
        year_days = year_days_dt1 * year_days_dt2

    return day_count, year_days


DAY_COUNT_METHODS: Dict[str, Callable[[datetime, datetime, bool], Tuple[float, float]]] = {
    '30A/360': _thirty_a_360,
    '30U/360': _thirty_u_360,
    '30E/360': _thirty_e_360,
    '30E/360 ISDA': _thirty_e_360_isda,
    'A/365F': _a_365f,
    'A/360': _a_360,
    'A/A ISDA': _a_a_isda,
    'A/A AFB': _a_a_afb
}
