# -*- coding: utf-8 -*-
import datetime as dt
import calendar as cal
import collections
from decimal import Decimal
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
    :param loan_term: The loan term in years.
    :param start_date: The start date of the loan.
    :param loan_term_period: Annual loan term (Y) or monthly loan term (M)
    :param payment_amount: The payment amount. If not provided, it will be calculated automatically.
    :param first_payment_date: The first payment date.
    :param payment_end_of_month: Whether the payment is at the end of the month.
    :param annual_payments: The number of annual payments.
    :param interest_only_period: The interest only period in months.
    :param compounding_method: The compounding method.
    :param loan_type: The loan type.
    """

    def __init__(self,loan_amount,interest_rate,loan_term,start_date,loan_term_period='Y',payment_amount=None,first_payment_date=None,payment_end_of_month=True,annual_payments=12,interest_only_period=0,compounding_method=CompoundingMethod.THIRTY_E_360.value,loan_type=LoanType.ANNUITY.value):
        
        validate_positive_numeric(loan_amount, "LOAN_AMOUNT")
        self.loan_amount = Decimal(str(loan_amount))

        validate_positive_numeric(interest_rate, "INTEREST_RATE")
        self.interest_rate = Decimal(str(interest_rate / 100)).quantize(Decimal('0.0001'))

        validate_positive_integer(loan_term, "LOAN_TERM")
        validate_loan_term_period(loan_term_period, "LOAN_TERM_PERIOD")

        if loan_term_period.upper() == 'M':
            self.loan_term = loan_term / 12
        else:
            self.loan_term = loan_term

        if payment_amount is not None:
            validate_positive_numeric(payment_amount, "PAYMENT_AMOUNT")
        self.payment_amount = payment_amount

        validate_date_string(start_date, "START_DATE")
        self.start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')

        validate_optional_date_string(first_payment_date, "FIRST_PAYMENT_DATE")
        if first_payment_date:
            self.first_payment_date = dt.datetime.strptime(first_payment_date, '%Y-%m-%d')
            if self.start_date > self.first_payment_date:
                raise ValueError('FIRST_PAYMENT_DATE cannot be before START_DATE')
        else:
            self.first_payment_date = None

        validate_boolean(payment_end_of_month, "PAYMENT_END_OF_MONTH")
        self.payment_end_of_month = payment_end_of_month

        validate_annual_payments(annual_payments, "ANNUAL_PAYMENTS")
        self.annual_payments = annual_payments

        self.no_of_payments = int(self.loan_term * self.annual_payments)
        self.delta_dt = Decimal(str(12 / self.annual_payments))

        validate_interest_only_period(interest_only_period, "INTEREST_ONLY_PERIOD", self.no_of_payments)
        self.interest_only_period = interest_only_period

        validate_compounding_method(compounding_method, "COMPOUNDING_METHOD")
        self.compounding_method = CompoundingMethod(compounding_method)

        validate_loan_type(loan_type, "LOAN_TYPE")
        self.loan_type = LoanType(loan_type)

        # define non-input variables
        self.special_payments=[]
        self.special_payments_schedule=[]

    @staticmethod
    def _quantize(amount):
        return Decimal(str(amount)).quantize(Decimal(str(0.01)))

    @staticmethod
    def _get_day_count(dt1, dt2, method, eom=False):
        day_count, year_days = DAY_COUNT_METHODS[method](dt1, dt2, eom)
        return day_count / year_days

    def _get_special_payment_schedule(self, special_payment):
        """Generates a schedule of dates and amounts for a recurring special payment."""
        term_in_years = special_payment.special_payment_term
        if special_payment.special_payment_term_period.upper() == 'M':
            term_in_years = special_payment.special_payment_term / 12

        num_payments = int(term_in_years * special_payment.annual_payments)
        payment_amount = self._quantize(special_payment.payment_amount)
        first_payment_date = dt.datetime.strptime(special_payment.first_payment_date, '%Y-%m-%d')
        
        months_between_payments = 12 / special_payment.annual_payments

        schedule = []
        for i in range(num_payments):
            payment_date = first_payment_date + relativedelta(months=int(i * months_between_payments))
            # The Payment object is used here just as a data container.
            # Most fields are zero because they are not relevant until the main schedule is built.
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

    def _calculate_regular_principal_payment(self):
        """Calculates the regular principal payment amount based on the loan type."""
        if self.payment_amount is not None:
            return self.payment_amount

        if self.loan_type == LoanType.INTEREST_ONLY:
            # For interest-only loans, there is no principal payment.
            return 0

        num_principal_payments = self.no_of_payments - self.interest_only_period
        if num_principal_payments <= 0:
            return 0

        if self.loan_type == LoanType.LINEAR:
            # For linear loans, the principal payment is constant.
            return self.loan_amount / num_principal_payments

        if self.loan_type == LoanType.ANNUITY:
            # Standard formula for annuity payment
            periodic_interest_rate = self.interest_rate / self.annual_payments
            if periodic_interest_rate == 0:
                 return self.loan_amount / num_principal_payments

            factor = (1 + periodic_interest_rate) ** num_principal_payments
            return self.loan_amount * (periodic_interest_rate * factor) / (factor - 1)

    def _get_schedule_base_date(self):
        """
        Determines the base date for the payment schedule calculation.

        This date is a reference point from which all payment dates are calculated.
        It's effectively the "zeroth" payment date, with the first actual payment
        occurring one payment period after this date.
        """
        payment_period_months = 12 / self.annual_payments
        payment_period = relativedelta(months=payment_period_months)

        if self.first_payment_date:
            # If a specific first payment date is given, the base date is one period before it.
            # We use the later of the loan start date and the first payment date.
            effective_first_payment = max(self.first_payment_date, self.start_date)
            return effective_first_payment - payment_period

        if not self.payment_end_of_month:
            # If payments are not tied to month-end, the schedule is based on the loan start date.
            return self.start_date

        # --- Logic for month-end payments ---
        is_start_date_eom = self.start_date.day == cal.monthrange(self.start_date.year, self.start_date.month)[1]

        if is_start_date_eom:
            # If the loan starts at the end of a month, base the schedule on that date.
            return self.start_date
        else:
            # If the loan starts mid-month, the first payment is at the end of that same month.
            # So, the base date is one period before that month-end date.
            first_payment_month_end = dt.datetime(self.start_date.year, self.start_date.month, cal.monthrange(self.start_date.year, self.start_date.month)[1])
            return first_payment_month_end - payment_period

    def _consolidate_special_payments(self):
        """
        Consolidates all special payment schedules into a single dictionary
        mapping payment dates to total payment amounts.
        """
        payments_by_date = collections.defaultdict(Decimal)
        for schedule in self.special_payments_schedule:
            for payment in schedule:
                payments_by_date[payment.date] += payment.special_principal_amount

        # Quantize the consolidated amounts
        for date in payments_by_date:
            payments_by_date[date] = self._quantize(payments_by_date[date])

        return dict(payments_by_date)

    def _get_payment_timeline(self, special_payments):
        """
        Generates a sorted list of all unique payment dates (events).
        """
        base_date = self._get_schedule_base_date()
        payment_dates = set(special_payments.keys())

        months_between_payments = 12 / self.annual_payments

        for i in range(1, self.no_of_payments + 1):
            date = base_date + relativedelta(months=i * months_between_payments)
            if self.payment_end_of_month and self.first_payment_date is None:
                eom_day = cal.monthrange(date.year, date.month)[1]
                date = date.replace(day=eom_day)
            payment_dates.add(date)

        return sorted(list(payment_dates))

    def get_payment_schedule(self):
        """
        Calculates the payment schedule for the loan.

        :return: A list of Payment objects.
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
        payment_schedule = [initial_payment]

        interest_only_payments_left = self.interest_only_period
        if self.loan_type == LoanType.INTEREST_ONLY:
            interest_only_payments_left = self.no_of_payments

        regular_payment_amount = self._calculate_regular_principal_payment()
        special_payments = self._consolidate_special_payments()
        payment_timeline = self._get_payment_timeline(special_payments)

        for date in payment_timeline:
            last_payment = payment_schedule[-1]
            bop_date = last_payment.date
            balance_bop = self._quantize(last_payment.loan_balance_amount)

            if balance_bop <= 0:
                continue

            # Determine if it's a regular payment day
            # This logic is a bit naive and might not perfectly match the old logic for all cases,
            # but it is much clearer. It assumes that a date from the timeline that is not a
            # special payment date must be a regular one.
            is_regular_payment_day = date not in special_payments or (date in special_payments and (len(payment_timeline) > len(special_payments)))


            compounding_factor = Decimal(str(self._get_day_count(bop_date, date, self.compounding_method.value, eom=self.payment_end_of_month)))
            interest_amount = self._quantize(balance_bop * self.interest_rate * compounding_factor)

            principal_amount = self._quantize(0)
            if is_regular_payment_day and interest_only_payments_left <= 0:
                if self.loan_type == LoanType.ANNUITY:
                    principal_amount = min(self._quantize(regular_payment_amount) - interest_amount, balance_bop)
                else: # LINEAR
                    principal_amount = min(self._quantize(regular_payment_amount), balance_bop)

            special_principal_amount = self._quantize(0)
            if date in special_payments:
                special_principal_amount = min(balance_bop - principal_amount, special_payments[date])

            total_principal_amount = min(principal_amount + special_principal_amount, balance_bop)
            total_payment_amount = total_principal_amount + interest_amount
            balance_eop = max(balance_bop - total_principal_amount, self._quantize(0))

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

            if is_regular_payment_day:
                interest_only_payments_left -= 1

        return payment_schedule

    def add_special_payment(self,payment_amount,first_payment_date,special_payment_term,annual_payments, special_payment_term_period='Y'):
        """
        Adds a special payment to the loan.

        :param payment_amount: The amount of the special payment.
        :param first_payment_date: The date of the first special payment.
        :param special_payment_term: The term of the special payment in years.
        :param annual_payments: The number of special payments per year.
        :param special_payment_term_period: The period of the special payment term, 'Y' for years, 'M' for months.
        """
        special_payment=SpecialPayment(payment_amount=payment_amount,first_payment_date=first_payment_date,special_payment_term=special_payment_term,annual_payments=annual_payments, special_payment_term_period=special_payment_term_period)
        self.special_payments.append(special_payment)
        self.special_payments_schedule.append(self._get_special_payment_schedule(special_payment))

    def get_loan_summary(self):
        """
        Calculates the loan summary.

        :return: A LoanSummary object.
        """
        payment_schedule=self.get_payment_schedule()
        total_payment_amount=0
        total_interest_amount=0
        total_principal_amount=0
        repayment_to_principal=0

        for payment in payment_schedule:
            total_payment_amount +=payment.payment_amount
            total_interest_amount +=payment.interest_amount
            total_principal_amount +=payment.total_principal_amount

        repayment_to_principal=self._quantize(total_payment_amount/total_principal_amount)
        loan_summary=LoanSummary(loan_amount=self._quantize(self.loan_amount),total_payment_amount=total_payment_amount,total_principal_amount=total_principal_amount,total_interest_amount=total_interest_amount,residual_loan_balance=self._quantize(self.loan_amount-total_principal_amount),repayment_to_principal=repayment_to_principal)

        return loan_summary
