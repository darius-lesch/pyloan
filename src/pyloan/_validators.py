# -*- coding: utf-8 -*-
"""
This module contains validator functions for the Loan class.
"""
import datetime as dt
from typing import Any, Optional

def validate_positive_numeric(value: Any, name: str) -> None:
    """
    Validate that a value is a non-negative number.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Variable {name} can only be of type integer or float, both non-negative.")
    if value < 0:
        raise ValueError(f"Variable {name} can only be non-negative.")

def validate_positive_integer(value: Any, name: str) -> None:
    """
    Validate that a value is a positive integer.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if not isinstance(value, int):
        raise TypeError(f"Variable {name} can only be of type integer.")
    if value < 1:
        raise ValueError(f"Variable {name} can only be integers greater or equal to 1.")

def validate_date_string(value: str, name: str) -> None:
    """
    Validate that a value is a date string in YYYY-MM-DD format.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if value is None:
        raise TypeError(f"Variable {name} must be of type date with format YYYY-MM-DD")
    try:
        dt.datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Variable {name} must be a valid date in YYYY-MM-DD format.")

def validate_optional_date_string(value: Optional[str], name: str) -> None:
    """
    Validate that a value is an optional date string in YYYY-MM-DD format.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if value is not None:
        validate_date_string(value, name)

def validate_boolean(value: Any, name: str) -> None:
    """
    Validate that a value is a boolean.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if not isinstance(value, bool):
        raise TypeError(f"Variable {name} can only be of type boolean (either True or False)")

def validate_annual_payments(value: int, name: str) -> None:
    """
    Validate that a value is a valid number of annual payments.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if not isinstance(value, int):
        raise TypeError(f"Attribute {name} must be of type integer.")
    if value not in [12, 4, 2, 1]:
        raise ValueError(f"Attribute {name} must be either set to 12, 4, 2 or .")

def validate_interest_only_period(value: int, name: str, no_of_payments: int) -> None:
    """
    Validate that a value is a valid interest only period.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    :param no_of_payments: The total number of payments for the loan.
    """
    if not isinstance(value, int):
        raise TypeError(f"Attribute {name} must be of type integer.")
    if value < 0:
        raise ValueError(f"Attribute {name} must be greater or equal to 0.")
    if no_of_payments - value < 0:
        raise ValueError(f"Attribute {name} is greater than product of LOAN_TERM and ANNUAL_PAYMENTS.")

from ._enums import CompoundingMethod, LoanType

def validate_compounding_method(value: str, name: str) -> None:
    """
    Validate that a value is a valid compounding method.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if not isinstance(value, str):
        raise TypeError(f"Attribute {name} must be of type string")
    try:
        CompoundingMethod(value)
    except ValueError:
        valid_methods = [item.value for item in CompoundingMethod]
        raise ValueError(f"Attribute {name} must be set to one of the following: {', '.join(valid_methods)}.")

def validate_loan_type(value: str, name: str) -> None:
    """
    Validate that a value is a valid loan type.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if not isinstance(value, str):
        raise TypeError(f"Attribute {name} must be of type string")
    try:
        LoanType(value)
    except ValueError:
        valid_types = [item.value for item in LoanType]
        raise ValueError(f"Attribute {name} must be either set to {', '.join(valid_types)}.")

def validate_loan_term_period(value: str, name: str) -> None:
    """
    Validate that a value is a valid loan term period.

    :param value: The value to validate.
    :param name: The name of the variable being validated.
    """
    if not isinstance(value, str):
        raise TypeError(f"Attribute {name} must be of type string")
    if value.upper() not in ['Y', 'M']:
        raise ValueError(f"Attribute {name} must be either set to 'Y' or 'M'.")
