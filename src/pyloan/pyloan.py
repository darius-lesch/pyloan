# -*- coding: utf-8 -*-
"""
This module contains the Loan class, which is the main class of the pyloan package.
"""
import logging
import datetime as dt
import calendar as cal
import collections
import numpy as np
import numpy_financial as npf
from typing import List, Optional, Union, Dict, Tuple
from dateutil.relativedelta import relativedelta
from ._validators import (
    validate_positive_numeric,
    validate_positive_integer,
    validate_date_string,
    validate_optional_date_string,
    validate_boolean,
    validate_annual_payments,
    validate_interest_only_period,
    validate_compounding_method,
    validate_loan_type,
    validate_loan_term_period
)
from ._enums import LoanType, CompoundingMethod
from ._day_count import DAY_COUNT_METHODS
from ._models import Payment, SpecialPayment, LoanSummary


logger = logging.getLogger(__name__)


class Loan(object):
    """
    The Loan class is the main class of the pyloan package. It is used to create a loan object and to perform loan calculations.
    This class can be used to model various types of loans, including annuity, linear, and interest-only loans. It supports
    different payment frequencies, compounding methods, and special ad-hoc payments.

    :param loan_amount: The principal amount of the loan.
    :param interest_rate: The nominal annual interest rate in percentage.
    :param loan_term: The duration of the loan, specified in either years or months.
    :param start_date: The date when the loan is disbursed, in 'YYYY-MM-DD' format.
    :param loan_term_period: Defines the unit for `loan_term`, either 'Y' for years or 'M' for months. Defaults to 'Y'.
    :param payment_amount: The fixed payment amount for each period. If not provided, it is calculated based on the loan type.
    :param first_payment_date: The date of the first payment, in 'YYYY-MM-DD' format. If not provided, it's calculated based on the start date and payment frequency.
    :param payment_end_of_month: If True, payments are scheduled for the end of the month. Defaults to True.
    :param annual_payments: The number of payments per year (e.g., 12 for monthly, 4 for quarterly). Defaults to 12.
    :param interest_only_period: The number of initial payments that are interest-only. Defaults to 0.
    :param compounding_method: The day count convention for interest calculation. See `pyloan._enums.CompoundingMethod` for options. Defaults to '30E/360 ISDA'.
    :param loan_type: The type of loan, which determines how the principal and interest are repaid. See `pyloan._enums.LoanType` for options. Defaults to 'annuity'.
    """

    def __init__(self,
                 loan_amount: Union[int, float],
                 interest_rate: float,
                 loan_term: int,
                 start_date: str,
                 loan_term_period: str = 'Y',
                 payment_amount: Optional[Union[int, float]] = None,
                 first_payment_date: Optional[str] = None,
                 payment_end_of_month: bool = True,
                 annual_payments: int = 12,
                 interest_only_period: int = 0,
                 compounding_method: str = CompoundingMethod.THIRTY_E_360_ISDA.value,
                 loan_type: str = LoanType.ANNUITY.value) -> None:

        self._validate_inputs(loan_amount, interest_rate, loan_term, start_date, loan_term_period, payment_amount, first_payment_date, payment_end_of_month, annual_payments, interest_only_period, compounding_method, loan_type)

        self.loan_amount: float = float(loan_amount)
        self.interest_rate: float = float(interest_rate)

        if loan_term_period.upper() == 'M':
            self.loan_term: Union[int, float] = loan_term / 12
        else:
            self.loan_term = loan_term

        self.payment_amount: Optional[float] = float(payment_amount) if payment_amount else None
        self.start_date: dt.datetime = dt.datetime.strptime(start_date, '%Y-%m-%d')

        if first_payment_date:
            self.first_payment_date: Optional[dt.datetime] = dt.datetime.strptime(first_payment_date, '%Y-%m-%d')
        else:
            self.first_payment_date = None

        self.payment_end_of_month: bool = payment_end_of_month
        self.annual_payments: int = annual_payments
        self.no_of_payments: int = int(self.loan_term * self.annual_payments)
        self.delta_dt: float = 12 / self.annual_payments
        self.interest_only_period: int = interest_only_period
        self.compounding_method: CompoundingMethod = CompoundingMethod(compounding_method)
        self.loan_type: LoanType = LoanType(loan_type)

        self.special_payments: List[SpecialPayment] = []
        self.special_payments_schedule: List[List[Payment]] = []

    def _validate_inputs(self,
                         loan_amount: Union[int, float],
                         interest_rate: float,
                         loan_term: int,
                         start_date: str,
                         loan_term_period: str,
                         payment_amount: Optional[Union[int, float]],
                         first_payment_date: Optional[str],
                         payment_end_of_month: bool,
                         annual_payments: int,
                         interest_only_period: int,
                         compounding_method: str,
                         loan_type: str) -> None:
        """
        Validates the inputs to the Loan class.
        """
        validate_positive_numeric(loan_amount, "LOAN_AMOUNT")
        validate_positive_numeric(interest_rate, "INTEREST_RATE")
        validate_positive_integer(loan_term, "LOAN_TERM")
        validate_loan_term_period(loan_term_period, "LOAN_TERM_PERIOD")
        if payment_amount is not None:
            validate_positive_numeric(payment_amount, "PAYMENT_AMOUNT")
        validate_date_string(start_date, "START_DATE")
        validate_optional_date_string(first_payment_date, "FIRST_PAYMENT_DATE")
        if first_payment_date:
            if dt.datetime.strptime(start_date, '%Y-%m-%d') > dt.datetime.strptime(first_payment_date, '%Y-%m-%d'):
                raise ValueError('FIRST_PAYMENT_DATE cannot be before START_DATE')
        validate_boolean(payment_end_of_month, "PAYMENT_END_OF_MONTH")
        validate_annual_payments(annual_payments, "ANNUAL_PAYMENTS")
        no_of_payments = int((loan_term / 12 if loan_term_period.upper() == 'M' else loan_term) * annual_payments)
        validate_interest_only_period(interest_only_period, "INTEREST_ONLY_PERIOD", no_of_payments)
        validate_compounding_method(compounding_method, "COMPOUNDING_METHOD")
        validate_loan_type(loan_type, "LOAN_TYPE")

    def _get_special_payment_schedule(self, special_payment: SpecialPayment) -> List[Payment]:
        """
        Generates a schedule of dates and amounts for a recurring special payment.

        :param special_payment: The SpecialPayment object.
        :return: A list of Payment objects representing the special payment schedule.
        """
        term_in_years = special_payment.special_payment_term
        if special_payment.special_payment_term_period.upper() == 'M':
            term_in_years = special_payment.special_payment_term / 12

        num_payments = int(term_in_years * special_payment.annual_payments)
        payment_amount = round(special_payment.payment_amount, 2)

        months_between_payments = 12 / special_payment.annual_payments

        schedule: List[Payment] = []
        for i in range(num_payments):
            payment_date = special_payment.first_payment_date + relativedelta(months=int(i * months_between_payments))
            payment = Payment(
                date=payment_date,
                payment_amount=0.0,
                interest_amount=0.0,
                principal_amount=0.0,
                special_principal_amount=payment_amount,
                total_principal_amount=0.0,
                loan_balance_amount=0.0
            )
            schedule.append(payment)

        return schedule

    def _calculate_regular_principal_payment(self, current_balance: Optional[float] = None, payments_left: Optional[int] = None) -> float:
        """
        Calculates the regular principal payment amount based on the loan type.

        :param current_balance: The current loan balance. If not provided, the initial loan amount is used.
        :param payments_left: The number of payments left. If not provided, the total number of payments is used.
        :return: The regular principal payment amount.
        """
        if self.payment_amount is not None:
            return self.payment_amount

        if self.loan_type == LoanType.INTEREST_ONLY:
            return 0.0

        balance = current_balance if current_balance is not None else self.loan_amount
        num_principal_payments = payments_left if payments_left is not None else self.no_of_payments - self.interest_only_period

        if num_principal_payments <= 0:
            return 0.0

        if self.loan_type == LoanType.LINEAR:
            return balance / num_principal_payments

        if self.loan_type == LoanType.ANNUITY:
            periodic_interest_rate = (self.interest_rate / 100) / self.annual_payments
            if periodic_interest_rate == 0:
                 return balance / num_principal_payments

            return npf.pmt(periodic_interest_rate, num_principal_payments, -balance)
        return 0.0

    def _consolidate_special_payments(self) -> Dict[dt.datetime, float]:
        """
        Consolidates all special payment schedules into a single dictionary
        mapping payment dates to total payment amounts.

        :return: A dictionary mapping payment dates to total special payment amounts.
        """
        payments_by_date: Dict[dt.datetime, float] = collections.defaultdict(float)
        for schedule in self.special_payments_schedule:
            for payment in schedule:
                payments_by_date[payment.date] += payment.special_principal_amount

        for date in payments_by_date:
            payments_by_date[date] = round(payments_by_date[date], 2)

        return dict(payments_by_date)

    def _calculate_interest_for_period(self, balance, start_date, end_date):
        day_count_func = DAY_COUNT_METHODS[self.compounding_method.value]
        days, year = day_count_func(start_date, end_date)
        return balance * (self.interest_rate / 100) * (days / year)

    def _get_payment_timeline(self, special_payments: Dict[dt.datetime, float]) -> Tuple[List[dt.datetime], List[dt.datetime]]:
        """
        Generates a sorted list of all unique payment dates (events) and regular payment dates.
        """
        months_between_payments = int(12 / self.annual_payments)

        regular_dates = []

        if self.first_payment_date:
            current_date = self.first_payment_date
            regular_dates.append(current_date)
            for _ in range(1, self.no_of_payments):
                current_date += relativedelta(months=months_between_payments)
                if self.payment_end_of_month:
                    current_date = dt.datetime(current_date.year, current_date.month, cal.monthrange(current_date.year, current_date.month)[1])
                regular_dates.append(current_date)
        else:
            # No first_payment_date specified
            current_date = self.start_date
            for i in range(self.no_of_payments):
                # For the first payment, we need to handle end of month logic carefully
                if i == 0:
                    if self.payment_end_of_month:
                        # If start date is last day of month, first payment is end of next month
                        is_last_day = self.start_date.day == cal.monthrange(self.start_date.year, self.start_date.month)[1]
                        if is_last_day:
                             payment_date = self.start_date + relativedelta(months=months_between_payments)
                        else:
                             payment_date = self.start_date

                        payment_date = dt.datetime(payment_date.year, payment_date.month, cal.monthrange(payment_date.year, payment_date.month)[1])
                    else:
                        payment_date = self.start_date + relativedelta(months=months_between_payments)
                else:
                    # Subsequent payment dates
                    payment_date = regular_dates[-1] + relativedelta(months=months_between_payments)
                    if self.payment_end_of_month:
                        payment_date = dt.datetime(payment_date.year, payment_date.month, cal.monthrange(payment_date.year, payment_date.month)[1])

                regular_dates.append(payment_date)


        payment_dates = sorted(list(set(regular_dates).union(special_payments.keys())))

        return payment_dates, regular_dates

    def get_payment_schedule(self) -> List[Payment]:
        """
        Calculates the payment schedule for the loan.
        This method uses a hybrid approach: vectorized date generation and an iterative loop for financial calculations.
        """
        special_payments_map = self._consolidate_special_payments()
        payment_timeline, regular_payment_dates = self._get_payment_timeline(special_payments_map)
        regular_payment_dates_set = set(regular_payment_dates)

        payment_schedule = [Payment(date=self.start_date, payment_amount=0, interest_amount=0, principal_amount=0, special_principal_amount=0, total_principal_amount=0, loan_balance_amount=self.loan_amount)]

        interest_only_payments_left = self.interest_only_period
        regular_payment_amount = self._calculate_regular_principal_payment()

        for i, date in enumerate(payment_timeline):
            last_payment = payment_schedule[-1]
            balance_bop = last_payment.loan_balance_amount

            if balance_bop <= 0:
                continue

            is_regular_day = date in regular_payment_dates_set
            is_special_day = date in special_payments_map

            interest_amount = 0.0
            principal_amount = 0.0
            special_principal_amount = 0.0

            if is_regular_day:
                last_regular_date = next((d for d in reversed(regular_payment_dates) if d < date), self.start_date)

                balance_at_period_start_payment = next((p for p in reversed(payment_schedule) if p.date == last_regular_date), None)
                balance_at_period_start = balance_at_period_start_payment.loan_balance_amount if balance_at_period_start_payment else self.loan_amount

                interest_amount = self._calculate_interest_for_period(balance_at_period_start, last_regular_date, date)

                if interest_only_payments_left <= 0:
                    if self.loan_type == LoanType.ANNUITY:
                        principal_amount = min(regular_payment_amount - interest_amount, balance_bop)
                    else: # LINEAR
                        principal_amount = min(regular_payment_amount, balance_bop)

                interest_only_payments_left -= 1

            if is_special_day:
                special_principal_amount = min(balance_bop - principal_amount, special_payments_map[date])

            total_principal_amount = principal_amount + special_principal_amount
            total_payment_amount = total_principal_amount + interest_amount
            balance_eop = balance_bop - total_principal_amount

            if 0 < balance_eop < 0.01:
                total_principal_amount += balance_eop
                total_payment_amount += balance_eop
                balance_eop = 0.0

            payment = Payment(
                date=date,
                payment_amount=round(total_payment_amount, 2),
                interest_amount=round(interest_amount, 2),
                principal_amount=round(principal_amount, 2),
                special_principal_amount=round(special_principal_amount, 2),
                total_principal_amount=round(total_principal_amount, 2),
                loan_balance_amount=round(balance_eop, 2)
            )
            payment_schedule.append(payment)

        return payment_schedule

    def add_special_payment(self,
                            payment_amount: Union[int, float],
                            first_payment_date: str,
                            special_payment_term: int,
                            annual_payments: int,
                            special_payment_term_period: str = 'Y') -> None:
        """
        Adds a special payment to the loan.

        :param payment_amount: The amount of the special payment.
        :param first_payment_date: The date of the first special payment in YYYY-MM-DD format.
        :param special_payment_term: The term of the special payment in years or months.
        :param annual_payments: The number of special payments per year.
        :param special_payment_term_period: The period of the special payment term, 'Y' for years or 'M' for months.
        """

        validate_positive_numeric(payment_amount, "SPECIAL_PAYMENT_AMOUNT")
        validate_date_string(first_payment_date, "SPECIAL_PAYMENT_FIRST_PAYMENT_DATE")

        special_payment = SpecialPayment(
            payment_amount=float(payment_amount),
            first_payment_date=dt.datetime.strptime(first_payment_date, '%Y-%m-%d'),
            special_payment_term=special_payment_term,
            annual_payments=annual_payments,
            special_payment_term_period=special_payment_term_period
        )
        self.special_payments.append(special_payment)
        self.special_payments_schedule.append(self._get_special_payment_schedule(special_payment))

    def _calculate_xirr(self, dates: List[dt.datetime], values: List[float], guess: float = 0.1) -> float:
        """
        Calculates the internal rate of return for a schedule of cash flows that is not necessarily periodic.
        This function implements the Newton-Raphson method to find the root of the XNPV equation.
        """
        if len(dates) != len(values):
            raise ValueError("dates and values must have the same length.")

        # The functions for XNPV and its derivative
        def xnpv(rate):
            return sum([v / ((1 + rate) ** ((d - dates[0]).days / 365.0)) for v, d in zip(values, dates)])

        def xnpv_derivative(rate):
            return sum([-((d - dates[0]).days / 365.0) * v / ((1 + rate) ** (((d - dates[0]).days / 365.0) + 1)) for v, d in zip(values, dates)])

        # Newton-Raphson method
        rate = guess
        for _ in range(100):  # Max 100 iterations
            npv = xnpv(rate)
            deriv = xnpv_derivative(rate)

            if abs(npv) < 1e-6:  # Tolerance
                return rate
            if deriv == 0:
                break # Avoid division by zero

            rate = rate - npv / deriv

        return rate # Return the best guess if not converged

    def get_internal_rate_of_return(self) -> float:
        """
        Calculates the effective annual interest rate (IRR) of the loan.

        This method considers all cash flows, including the initial loan amount,
        all regular payments, and any special payments. The IRR is the discount
        rate that makes the net present value (NPV) of all cash flows equal to zero.
        It is a common measure of the true cost of a loan.

        This implementation uses a custom XIRR calculation to handle irregular cash flows.

        :return: The annualized internal rate of return as a percentage.
        """
        schedule = self.get_payment_schedule()
        if not schedule or len(schedule) <= 1:
            return 0.0

        dates = [p.date for p in schedule]
        values = [p.payment_amount for p in schedule]
        values[0] = -self.loan_amount # The first cash flow is an outflow

        # Ensure there are positive and negative cash flows
        if not (any(v > 0 for v in values) and any(v < 0 for v in values)):
            return 0.0

        try:
            irr = self._calculate_xirr(dates, values)
            return irr * 100
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0

    def get_loan_summary(self) -> LoanSummary:
        """
        Calculates the loan summary.

        :return: A LoanSummary object.
        """
        payment_schedule = self.get_payment_schedule()
        total_payment_amount = 0.0
        total_interest_amount = 0.0
        total_principal_amount = 0.0
        repayment_to_principal = 0.0

        for payment in payment_schedule:
            total_payment_amount += payment.payment_amount
            total_interest_amount += payment.interest_amount
            total_principal_amount += payment.total_principal_amount

        if total_principal_amount == 0:
            repayment_to_principal = 0.0
        else:
            repayment_to_principal = round(total_payment_amount / total_principal_amount, 2)

        loan_summary = LoanSummary(
            loan_amount=round(self.loan_amount, 2),
            total_payment_amount=round(total_payment_amount, 2),
            total_principal_amount=round(total_principal_amount, 2),
            total_interest_amount=round(total_interest_amount, 2),
            residual_loan_balance=round(self.loan_amount - total_principal_amount, 2),
            repayment_to_principal=repayment_to_principal
        )

        return loan_summary
