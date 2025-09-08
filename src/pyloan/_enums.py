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
    THIRTY_360_US = '30U/360'
    THIRTY_E_360_ISDA = '30E/360'
    ACTUAL_365_FIXED = 'A/365'
    ACTUAL_360 = 'A/360'
    ACTUAL_ACTUAL_ISDA = 'A/A'
