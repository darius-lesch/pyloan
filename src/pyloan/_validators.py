# -*- coding: utf-8 -*-
"""
This module contains validator functions for the Loan class.
"""
import datetime as dt

def validate_positive_numeric(value, name):
    """Validate that a value is a non-negative number."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"Variable {name} can only be of type integer or float, both non-negative.")
    if value < 0:
        raise ValueError(f"Variable {name} can only be non-negative.")

def validate_positive_integer(value, name):
    """Validate that a value is a positive integer."""
    if not isinstance(value, int):
        raise TypeError(f"Variable {name} can only be of type integer.")
    if value < 1:
        raise ValueError(f"Variable {name} can only be integers greater or equal to 1.")

def validate_date_string(value, name):
    """Validate that a value is a date string in YYYY-MM-DD format."""
    if value is None:
        raise TypeError(f"Variable {name} must be of type date with format YYYY-MM-DD")
    try:
        dt.datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Variable {name} must be a valid date in YYYY-MM-DD format.")

def validate_optional_date_string(value, name):
    """Validate that a value is an optional date string in YYYY-MM-DD format."""
    if value is not None:
        validate_date_string(value, name)

def validate_boolean(value, name):
    """Validate that a value is a boolean."""
    if not isinstance(value, bool):
        raise TypeError(f"Variable {name} can only be of type boolean (either True or False)")

def validate_annual_payments(value, name):
    """Validate that a value is a valid number of annual payments."""
    if not isinstance(value, int):
        raise TypeError(f"Attribute {name} must be of type integer.")
    if value not in [12, 4, 2, 1]:
        raise ValueError(f"Attribute {name} must be either set to 12, 4, 2 or 1.")

def validate_interest_only_period(value, name, no_of_payments):
    """Validate that a value is a valid interest only period."""
    if not isinstance(value, int):
        raise TypeError(f"Attribute {name} must be of type integer.")
    if value < 0:
        raise ValueError(f"Attribute {name} must be greater or equal to 0.")
    if no_of_payments - value < 0:
        raise ValueError(f"Attribute {name} is greater than product of LOAN_TERM and ANNUAL_PAYMENTS.")

from ._enums import CompoundingMethod, LoanType

def validate_compounding_method(value, name):
    """Validate that a value is a valid compounding method."""
    if not isinstance(value, str):
        raise TypeError(f"Attribute {name} must be of type string")
    try:
        CompoundingMethod(value)
    except ValueError:
        valid_methods = [item.value for item in CompoundingMethod]
        raise ValueError(f"Attribute {name} must be set to one of the following: {', '.join(valid_methods)}.")

def validate_loan_type(value, name):
    """Validate that a value is a valid loan type."""
    if not isinstance(value, str):
        raise TypeError(f"Attribute {name} must be of type string")
    try:
        LoanType(value)
    except ValueError:
        valid_types = [item.value for item in LoanType]
        raise ValueError(f"Attribute {name} must be either set to {', '.join(valid_types)}.")
