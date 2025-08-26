# -*- coding: utf-8 -*-
"""
This module contains dataclasses for the Loan class.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Payment:
    """
    Represents a single payment in the loan schedule.

    :param date: The date of the payment.
    :param payment_amount: The total amount of the payment.
    :param interest_amount: The interest portion of the payment.
    :param principal_amount: The principal portion of the payment.
    :param special_principal_amount: The special principal portion of the payment.
    :param total_principal_amount: The total principal paid.
    :param loan_balance_amount: The remaining loan balance after the payment.
    """
    date: datetime
    payment_amount: Decimal
    interest_amount: Decimal
    principal_amount: Decimal
    special_principal_amount: Decimal
    total_principal_amount: Decimal
    loan_balance_amount: Decimal

@dataclass
class SpecialPayment:
    """
    Represents a special payment to be made on the loan.

    :param payment_amount: The amount of the special payment.
    :param first_payment_date: The date of the first special payment.
    :param special_payment_term: The term of the special payment in years or months.
    :param annual_payments: The number of special payments per year.
    :param special_payment_term_period: The period of the special payment term ('Y' for years, 'M' for months).
    """
    payment_amount: Decimal
    first_payment_date: datetime
    special_payment_term: int
    annual_payments: int
    special_payment_term_period: str = 'Y'

@dataclass
class LoanSummary:
    """
    Represents a summary of the loan.

    :param loan_amount: The initial loan amount.
    :param total_payment_amount: The total amount paid over the life of the loan.
    :param total_principal_amount: The total principal paid over the life of the loan.
    :param total_interest_amount: The total interest paid over the life of the loan.
    :param residual_loan_balance: The remaining loan balance after all payments.
    :param repayment_to_principal: The ratio of total payments to total principal.
    """
    loan_amount: Decimal
    total_payment_amount: Decimal
    total_principal_amount: Decimal
    total_interest_amount: Decimal
    residual_loan_balance: Decimal
    repayment_to_principal: Decimal
