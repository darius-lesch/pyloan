# -*- coding: utf-8 -*-
"""
This module contains the Loan class, which is the main class of the pyloan package.
"""
import datetime as dt
import calendar as cal
import collections
from decimal import Decimal, InvalidOperation
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

class Loan(object):
    """
    The Loan class is the main class of the pyloan package. It is used to create a loan object and to perform loan calculations.

    :param loan_amount: The loan amount.
    :param interest_rate: The annual interest rate.
    :param loan_term: The loan term in years or months.
    :param start_date: The start date of the loan in YYYY-MM-DD format.
    :param loan_term_period: The period of the loan term, 'Y' for years or 'M' for months.
    :param payment_amount: The payment amount. If not provided, it will be calculated automatically.
    :param first_payment_date: The first payment date in YYYY-MM-DD format.
    :param payment_end_of_month: Whether the payment is at the end of the month.
    :param annual_payments: The number of annual payments.
    :param interest_only_period: The interest only period in months.
    :param compounding_method: The compounding method.
    :param loan_type: The loan type.
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
                 compounding_method: str = CompoundingMethod.THIRTY_E_360.value,
                 loan_type: str = LoanType.ANNUITY.value) -> None:
        
        self._validate_inputs(loan_amount, interest_rate, loan_term, start_date, loan_term_period, payment_amount, first_payment_date, payment_end_of_month, annual_payments, interest_only_period, compounding_method, loan_type)

        self.loan_amount: Decimal = Decimal(str(loan_amount))
        self.interest_rate: Decimal = Decimal(str(interest_rate / 100)).quantize(Decimal('0.0001'))

        if loan_term_period.upper() == 'M':
            self.loan_term: Union[int, float] = loan_term / 12
        else:
            self.loan_term = loan_term

        self.payment_amount: Optional[Decimal] = Decimal(str(payment_amount)) if payment_amount else None
        self.start_date: dt.datetime = dt.datetime.strptime(start_date, '%Y-%m-%d')

        if first_payment_date:
            self.first_payment_date: Optional[dt.datetime] = dt.datetime.strptime(first_payment_date, '%Y-%m-%d')
        else:
            self.first_payment_date = None

        self.payment_end_of_month: bool = payment_end_of_month
        self.annual_payments: int = annual_payments
        self.no_of_payments: int = int(self.loan_term * self.annual_payments)
        self.delta_dt: Decimal = Decimal(str(12 / self.annual_payments))
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

    @staticmethod
    def _quantize(amount: Union[int, float, Decimal]) -> Decimal:
        """
        Quantizes a numeric value to two decimal places.

        :param amount: The amount to quantize.
        :return: The quantized amount as a Decimal.
        """
        return Decimal(str(amount)).quantize(Decimal(str(0.01)))

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
        payment_amount = self._quantize(special_payment.payment_amount)
        
        months_between_payments = 12 / special_payment.annual_payments

        schedule: List[Payment] = []
        for i in range(num_payments):
            payment_date = special_payment.first_payment_date + relativedelta(months=int(i * months_between_payments))
            payment = Payment(
                date=payment_date,
                payment_amount=self._quantize(0),
                interest_amount=self._quantize(0),
                principal_amount=self._quantize(0),
                special_principal_amount=payment_amount,
                total_principal_amount=self._quantize(0),
                loan_balance_amount=self._quantize(0)
            )
            schedule.append(payment)

        return schedule

    def _calculate_regular_principal_payment(self) -> Union[Decimal, int]:
        """
        Calculates the regular principal payment amount based on the loan type.

        :return: The regular principal payment amount.
        """
        if self.payment_amount is not None:
            return self.payment_amount

        if self.loan_type == LoanType.INTEREST_ONLY:
            return 0

        num_principal_payments = self.no_of_payments - self.interest_only_period
        if num_principal_payments <= 0:
            return 0

        if self.loan_type == LoanType.LINEAR:
            return self.loan_amount / num_principal_payments

        if self.loan_type == LoanType.ANNUITY:
            periodic_interest_rate = self.interest_rate / self.annual_payments
            if periodic_interest_rate == 0:
                 return self.loan_amount / num_principal_payments

            factor = (1 + periodic_interest_rate) ** num_principal_payments
            return self.loan_amount * (periodic_interest_rate * factor) / (factor - 1)
        return 0

    def _get_schedule_base_date(self) -> dt.datetime:
        """
        Determines the base date for the payment schedule calculation.

        This date is a reference point from which all payment dates are calculated.
        It's effectively the "zeroth" payment date, with the first actual payment
        occurring one payment period after this date.

        :return: The base date for the payment schedule.
        """
        payment_period_months = 12 / self.annual_payments
        payment_period = relativedelta(months=int(payment_period_months))

        if self.first_payment_date:
            effective_first_payment = max(self.first_payment_date, self.start_date)
            return effective_first_payment - payment_period

        if not self.payment_end_of_month:
            return self.start_date

        is_start_date_eom = self.start_date.day == cal.monthrange(self.start_date.year, self.start_date.month)[1]

        if is_start_date_eom:
            return self.start_date
        else:
            first_payment_month_end = dt.datetime(self.start_date.year, self.start_date.month, cal.monthrange(self.start_date.year, self.start_date.month)[1])
            return first_payment_month_end - payment_period

    def _consolidate_special_payments(self) -> Dict[dt.datetime, Decimal]:
        """
        Consolidates all special payment schedules into a single dictionary
        mapping payment dates to total payment amounts.

        :return: A dictionary mapping payment dates to total special payment amounts.
        """
        payments_by_date: Dict[dt.datetime, Decimal] = collections.defaultdict(Decimal)
        for schedule in self.special_payments_schedule:
            for payment in schedule:
                payments_by_date[payment.date] += payment.special_principal_amount

        for date in payments_by_date:
            payments_by_date[date] = self._quantize(payments_by_date[date])

        return dict(payments_by_date)

    def _get_regular_payment_dates(self) -> List[dt.datetime]:
        """
        Generates a sorted list of all unique regular payment dates.
        :return: A sorted list of all payment dates.
        """
        base_date = self._get_schedule_base_date()
        payment_dates = set()

        months_between_payments = 12 / self.annual_payments

        for i in range(1, self.no_of_payments + 1):
            date = base_date + relativedelta(months=int(i * months_between_payments))
            if self.payment_end_of_month and self.first_payment_date is None:
                eom_day = cal.monthrange(date.year, date.month)[1]
                date = date.replace(day=eom_day)
            payment_dates.add(date)

        return sorted(list(payment_dates))

    def _get_payment_timeline(self, special_payments: Dict[dt.datetime, Decimal]) -> List[dt.datetime]:
        """
        Generates a sorted list of all unique payment dates (events).

        :param special_payments: A dictionary of special payment dates and amounts.
        :return: A sorted list of all payment dates.
        """
        regular_dates = self._get_regular_payment_dates()
        payment_dates = set(special_payments.keys()).union(set(regular_dates))

        return sorted(list(payment_dates))

    def _initialize_payment_schedule(self) -> List[Payment]:
        """
        Initializes the payment schedule with the first payment.
        """
        initial_payment = Payment(
            date=self.start_date,
            payment_amount=self._quantize(0),
            interest_amount=self._quantize(0),
            principal_amount=self._quantize(0),
            special_principal_amount=self._quantize(0),
            total_principal_amount=self._quantize(0),
            loan_balance_amount=self._quantize(self.loan_amount)
        )
        return [initial_payment]

    def get_payment_schedule(self) -> List[Payment]:
        """
        Calculates the payment schedule for the loan.

        :return: A list of Payment objects.
        """
        payment_schedule = self._initialize_payment_schedule()

        interest_only_payments_left = self.interest_only_period
        if self.loan_type == LoanType.INTEREST_ONLY:
            interest_only_payments_left = self.no_of_payments

        regular_payment_amount = self._calculate_regular_principal_payment()
        special_payments = self._consolidate_special_payments()
        payment_timeline = self._get_payment_timeline(special_payments)
        regular_payment_dates = self._get_regular_payment_dates()

        accrued_interest = Decimal('0')

        for date in payment_timeline:
            last_payment = payment_schedule[-1]
            balance_bop = self._quantize(last_payment.loan_balance_amount)

            if balance_bop <= 0:
                continue

            bop_date = last_payment.date
            compounding_factor = Decimal(str(DAY_COUNT_METHODS[self.compounding_method.value](bop_date, date, self.payment_end_of_month)[0] / DAY_COUNT_METHODS[self.compounding_method.value](bop_date, date, self.payment_end_of_month)[1]))
            period_interest = self._quantize(balance_bop * self.interest_rate * compounding_factor)
            accrued_interest += period_interest

            is_regular_day = date in regular_payment_dates
            is_special_day = date in special_payments

            interest_amount = Decimal('0')
            principal_amount = Decimal('0')
            special_principal_amount = Decimal('0')

            if is_regular_day:
                interest_amount = self._quantize(accrued_interest)
                accrued_interest = Decimal('0')

                if interest_only_payments_left <= 0:
                    if self.loan_type == LoanType.ANNUITY:
                        principal_amount = min(self._quantize(regular_payment_amount) - interest_amount, balance_bop)
                    else: # LINEAR
                        principal_amount = min(self._quantize(regular_payment_amount), balance_bop)

                interest_only_payments_left -= 1

            if is_special_day:
                special_principal_amount = min(balance_bop - principal_amount, special_payments[date])

            total_principal_amount = min(principal_amount + special_principal_amount, balance_bop)
            total_payment_amount = total_principal_amount + interest_amount
            balance_eop = max(balance_bop - total_principal_amount, self._quantize(0))

            # The last payment amount should be the remaining balance + interest
            if balance_eop == 0 and total_principal_amount < balance_bop:
                total_principal_amount = balance_bop
                total_payment_amount = total_principal_amount + interest_amount


            payment = Payment(
                date=date,
                payment_amount=total_payment_amount,
                interest_amount=interest_amount,
                principal_amount=principal_amount,
                special_principal_amount=special_principal_amount,
                total_principal_amount=total_principal_amount,
                loan_balance_amount=balance_eop
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
            payment_amount=Decimal(str(payment_amount)),
            first_payment_date=dt.datetime.strptime(first_payment_date, '%Y-%m-%d'),
            special_payment_term=special_payment_term,
            annual_payments=annual_payments,
            special_payment_term_period=special_payment_term_period
        )
        self.special_payments.append(special_payment)
        self.special_payments_schedule.append(self._get_special_payment_schedule(special_payment))

    def get_loan_summary(self) -> LoanSummary:
        """
        Calculates the loan summary.

        :return: A LoanSummary object.
        """
        payment_schedule = self.get_payment_schedule()
        total_payment_amount = Decimal('0')
        total_interest_amount = Decimal('0')
        total_principal_amount = Decimal('0')
        repayment_to_principal = Decimal('0')

        for payment in payment_schedule:
            total_payment_amount += payment.payment_amount
            total_interest_amount += payment.interest_amount
            total_principal_amount += payment.total_principal_amount

        try:
            repayment_to_principal = self._quantize(total_payment_amount / total_principal_amount)
        except (ZeroDivisionError, InvalidOperation):
            repayment_to_principal = self._quantize(0)

        loan_summary = LoanSummary(
            loan_amount=self._quantize(self.loan_amount),
            total_payment_amount=total_payment_amount,
            total_principal_amount=total_principal_amount,
            total_interest_amount=total_interest_amount,
            residual_loan_balance=self._quantize(self.loan_amount - total_principal_amount),
            repayment_to_principal=repayment_to_principal
        )

        return loan_summary
