# -*- coding: utf-8 -*-
"""
This module contains dataclasses for the Loan class.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Payment:
    date: datetime
    payment_amount: Decimal
    interest_amount: Decimal
    principal_amount: Decimal
    special_principal_amount: Decimal
    total_principal_amount: Decimal
    loan_balance_amount: Decimal

@dataclass
class SpecialPayment:
    payment_amount: float
    first_payment_date: str
    special_payment_term: int
    annual_payments: int

@dataclass
class LoanSummary:
    loan_amount: Decimal
    total_payment_amount: Decimal
    total_principal_amount: Decimal
    total_interest_amount: Decimal
    residual_loan_balance: Decimal
    repayment_to_principal: Decimal
