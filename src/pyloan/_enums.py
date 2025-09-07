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
    THIRTY_360_US = '30/360 (US)'
    THIRTY_E_360_ISDA = '30E/360 ISDA'
    ACTUAL_365_FIXED = 'Actual/365 (Fixed)'
    ACTUAL_360 = 'Actual/360'
    ACTUAL_ACTUAL_ISDA = 'Actual/Actual (ISDA)'
