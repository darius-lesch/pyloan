# -*- coding: utf-8 -*-
"""
This module contains Enum classes for the Loan class.
"""
from enum import Enum

class LoanType(Enum):
    ANNUITY = 'annuity'
    LINEAR = 'linear'
    INTEREST_ONLY = 'interest-only'

class CompoundingMethod(Enum):
    THIRTY_A_360 = '30A/360'
    THIRTY_U_360 = '30U/360'
    THIRTY_E_360 = '30E/360'
    THIRTY_E_360_ISDA = '30E/360 ISDA'
    ACTUAL_360 = 'A/360'
    ACTUAL_365_FIXED = 'A/365F'
    ACTUAL_ACTUAL_ISDA = 'A/A ISDA'
    ACTUAL_ACTUAL_AFB = 'A/A AFB'
