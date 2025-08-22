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
    validate_loan_type
)
from ._enums import LoanType, CompoundingMethod

from ._models import Payment, SpecialPayment, LoanSummary

class Loan(object):
    """
    The Loan class is the main class of the pyloan package. It is used to create a loan object and to perform loan calculations.

    :param loan_amount: The loan amount.
    :param interest_rate: The annual interest rate.
    :param loan_term: The loan term in years.
    :param start_date: The start date of the loan.
    :param payment_amount: The payment amount. If not provided, it will be calculated automatically.
    :param first_payment_date: The first payment date.
    :param payment_end_of_month: Whether the payment is at the end of the month.
    :param annual_payments: The number of annual payments.
    :param interest_only_period: The interest only period in months.
    :param compounding_method: The compounding method.
    :param loan_type: The loan type.
    """

    def __init__(self,loan_amount,interest_rate,loan_term,start_date,payment_amount=None,first_payment_date=None,payment_end_of_month=True,annual_payments=12,interest_only_period=0,compounding_method=CompoundingMethod.THIRTY_E_360.value,loan_type=LoanType.ANNUITY.value):
        
        validate_positive_numeric(loan_amount, "LOAN_AMOUNT")
        self.loan_amount = Decimal(str(loan_amount))

        validate_positive_numeric(interest_rate, "INTEREST_RATE")
        self.interest_rate = Decimal(str(interest_rate / 100)).quantize(Decimal('0.0001'))

        validate_positive_integer(loan_term, "LOAN_TERM")
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

        self.no_of_payments = self.loan_term * self.annual_payments
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
    def _get_day_count(dt1,dt2,method,eom=False):

        def get_julian_day_number(y,m,d):
            julian_day_count = (1461 * (y + 4800 + (m - 14)/12))/4 +(367 * (m - 2 - 12 * ((m - 14)/12)))/12 - (3 * ((y + 4900 + (m - 14)/12)/100))/4 + d - 32075
            return julian_day_count

        y1, m1, d1 = dt1.year, dt1.month, dt1.day
        y2, m2, d2 = dt2.year, dt2.month, dt2.day
        dt1_eom_day=cal.monthrange(y1,m1)[1]
        dt2_eom_day=cal.monthrange(y2,m2)[1]

        if method in {'30A/360','30U/360','30E/360','30E/360 ISDA'}:
            if method=='30A/360':
                d1 = min(d1,30)
                d2 = min(d2,30) if d1 == 30 else d2
            if method=='30U/360':
                if eom and m1 == 2 and d1==dt1_eom_day and m2==2 and d2==dt2_eom_day:
                    d2=30
                if eom and m1 == 2 and d1==dt1_eom_day:
                    d1=30
                if d2 == 31 and d1 >= 30:
                    d2=30
                if d1==31:
                    d1=30
            if method=='30E/360':
                if d1 == 31:
                    d1=30
                if d2 == 31:
                    d2=30
            if method=='30E/360 ISDA':
                if d1==dt1_eom_day:
                    d1=30
                if d2==dt2_eom_day and m2 != 2:
                    d2=30

            day_count = (360*(y2-y1)+30*(m2-m1)+(d2-d1))
            year_days = 360

        if method=='A/365F':
            day_count=(dt2-dt1).days
            year_days=365

        if method=='A/360':
            day_count=(dt2-dt1).days
            year_days=360

        if method in {'A/A ISDA','A/A AFB'}:
            djn_dt1= get_julian_day_number(y1,m1,d1)
            djn_dt2= get_julian_day_number(y2,m2,d2)
            if y1==y2:
                day_count=djn_dt2-djn_dt1
                if method=='A/A ISDA':
                    year_days=366 if cal.isleap(y2) else 365
                if method=='A/A AFB':
                    year_days=366 if cal.isleap(y1) and (m1<3) else 365
            if y1 < y2:
                djn_dt1_eoy= get_julian_day_number(y1,12,31)
                day_count_dt1=djn_dt1_eoy-djn_dt1
                if method=='A/A ISDA':
                    year_days_dt1=366 if cal.isleap(y1) else 365
                if method=='A/A AFB':
                    year_days_dt1=366 if cal.isleap(y1) and (m1<3) else 365

                djn_dt2_boy= get_julian_day_number(y2,1,1)
                day_count_dt2=djn_dt2-djn_dt2_boy
                if method=='A/A ISDA':
                    year_days_dt2=366 if cal.isleap(y2) else 365
                if method=='A/A AFB':
                    year_days_dt2=366 if cal.isleap(y2) and (m2>=3) else 365

                diff=y2-y1-1

                day_count=(day_count_dt1*year_days_dt2)+(day_count_dt2*year_days_dt1)+(diff*year_days_dt1*year_days_dt2)
                year_days=year_days_dt1*year_days_dt2

        factor = day_count / year_days
        return factor

    @staticmethod
    def _get_special_payment_schedule(self,special_payment):
        no_of_payments=special_payment.special_payment_term * special_payment.annual_payments
        annual_payments = special_payment.annual_payments
        dt0=dt.datetime.strptime(special_payment.first_payment_date,'%Y-%m-%d')
        
        special_payment_amount=self._quantize(special_payment.payment_amount)
        initial_special_payment=Payment(date=dt0,payment_amount=self._quantize(0),interest_amount=self._quantize(0),principal_amount=self._quantize(0),special_principal_amount=special_payment_amount,total_principal_amount=self._quantize(0),loan_balance_amount=self._quantize(0))
        special_payment_schedule=[initial_special_payment]

        for i in range(1,no_of_payments):
            date=dt0+relativedelta(months=i*12/annual_payments)
            special_payment=Payment(date=date,payment_amount=self._quantize(0),interest_amount=self._quantize(0),principal_amount=self._quantize(0),special_principal_amount=special_payment_amount,total_principal_amount=self._quantize(0),loan_balance_amount=self._quantize(0))
            special_payment_schedule.append(special_payment)

        return special_payment_schedule

    def _calculate_regular_payment_amount(self):
        """Calculates the regular payment amount based on the loan type."""
        if self.loan_type == LoanType.ANNUITY:
            if self.payment_amount is None:
                # Standard formula for annuity payment
                return self.loan_amount * ((self.interest_rate / self.annual_payments) * (1 + (self.interest_rate / self.annual_payments)) ** ((self.no_of_payments - self.interest_only_period))) / ((1 + (self.interest_rate / self.annual_payments)) ** ((self.no_of_payments - self.interest_only_period)) - 1)
            return self.payment_amount
        if self.loan_type == LoanType.LINEAR:
            if self.payment_amount is None:
                # For linear loans, the principal payment is constant
                return self.loan_amount / (self.no_of_payments - self.interest_only_period)
            return self.payment_amount
        if self.loan_type == LoanType.INTEREST_ONLY:
            # For interest-only loans, there is no principal payment
            return 0

    def _get_payment_start_date(self):
        """Determines the start date for the payment schedule calculation."""
        if self.first_payment_date is None:
            if self.payment_end_of_month:
                # If payment is at the end of the month, adjust the start date accordingly
                if self.start_date.day == cal.monthrange(self.start_date.year, self.start_date.month)[1]:
                    return self.start_date
                return dt.datetime(self.start_date.year, self.start_date.month, cal.monthrange(self.start_date.year, self.start_date.month)[1], 0, 0) + relativedelta(months=-12 / self.annual_payments)
            return self.start_date
        return max(self.first_payment_date, self.start_date) + relativedelta(months=-12 / self.annual_payments)

    def _consolidate_special_payments(self):
        """Consolidates all special payments into a single schedule."""
        special_payments_schedule_raw = []
        if len(self.special_payments_schedule) > 0:
            for schedule in self.special_payments_schedule:
                for payment in schedule:
                    special_payments_schedule_raw.append([payment.date, payment.special_principal_amount])

        # Get unique dates and sort them
        special_payments_dates = sorted(list(set([item[0] for item in special_payments_schedule_raw])))

        consolidated_schedule = []
        for date in special_payments_dates:
            # Sum all payments for the same date
            amount = self._quantize(sum(item[1] for item in special_payments_schedule_raw if item[0] == date))
            consolidated_schedule.append([date, amount])

        return consolidated_schedule

    def _handle_interim_special_payments(self, bop_date, date, balance_bop, special_payments, payment_schedule, m):
        """Handles special payments that occur between regular payment dates."""
        for sp_date, sp_amount in special_payments:
            if bop_date < sp_date < date:
                # Calculate interest for the period until the special payment
                compounding_factor = Decimal(str(self._get_day_count(bop_date, sp_date, self.compounding_method.value, eom=self.payment_end_of_month)))
                interest_amount = self._quantize(balance_bop * self.interest_rate * compounding_factor)

                principal_amount = self._quantize(0)
                special_principal_amount = self._quantize(0) if balance_bop == Decimal('0') else min(sp_amount - interest_amount, balance_bop)
                total_principal_amount = min(principal_amount + special_principal_amount, balance_bop)
                total_payment_amount = total_principal_amount + interest_amount
                balance_eop = max(balance_bop - total_principal_amount, self._quantize(0))

                payment = Payment(date=sp_date, payment_amount=total_payment_amount, interest_amount=interest_amount, principal_amount=principal_amount, special_principal_amount=special_principal_amount, total_principal_amount=total_principal_amount, loan_balance_amount=balance_eop)
                payment_schedule.append(payment)

                # Update loop variables
                m += 1
                bop_date = sp_date
                balance_bop = balance_eop
        return bop_date, balance_bop, m

    def get_payment_schedule(self):
        """
        Calculates the payment schedule for the loan.

        :return: A list of Payment objects.
        """
        initial_payment = Payment(date=self.start_date, payment_amount=self._quantize(0), interest_amount=self._quantize(0), principal_amount=self._quantize(0), special_principal_amount=self._quantize(0), total_principal_amount=self._quantize(0), loan_balance_amount=self._quantize(self.loan_amount))
        payment_schedule = [initial_payment]

        interest_only_period = self.interest_only_period
        if self.loan_type == LoanType.INTEREST_ONLY:
            interest_only_period = self.no_of_payments

        regular_principal_payment_amount = self._calculate_regular_payment_amount()
        dt0 = self._get_payment_start_date()
        consolidated_special_payments = self._consolidate_special_payments()

        m = 0
        for i in range(1, self.no_of_payments + 1):
            date = dt0 + relativedelta(months=i * 12 / self.annual_payments)
            if self.payment_end_of_month and self.first_payment_date is None:
                eom_day = cal.monthrange(date.year, date.month)[1]
                date = date.replace(day=eom_day)

            bop_date = payment_schedule[(i + m) - 1].date
            balance_bop = self._quantize(payment_schedule[(i + m) - 1].loan_balance_amount)

            bop_date, balance_bop, m = self._handle_interim_special_payments(bop_date, date, balance_bop, consolidated_special_payments, payment_schedule, m)

            special_principal_amount_for_date = self._quantize(sum(item[1] for item in consolidated_special_payments if item[0] == date))

            compounding_factor = Decimal(str(self._get_day_count(bop_date, date, self.compounding_method.value, eom=self.payment_end_of_month)))
            interest_amount = self._quantize(0) if balance_bop == Decimal('0') else self._quantize(balance_bop * self.interest_rate * compounding_factor)

            principal_amount = self._quantize(0) if balance_bop == Decimal('0') or interest_only_period >= i else min(self._quantize(regular_principal_payment_amount) - (interest_amount if self.loan_type == LoanType.ANNUITY else 0), balance_bop)
            special_principal_amount = min(balance_bop - principal_amount, special_principal_amount_for_date) if interest_only_period < i else self._quantize(0)
            total_principal_amount = min(principal_amount + special_principal_amount, balance_bop)
            total_payment_amount = total_principal_amount + interest_amount
            balance_eop = max(balance_bop - total_principal_amount, self._quantize(0))

            payment = Payment(date=date, payment_amount=total_payment_amount, interest_amount=interest_amount, principal_amount=principal_amount, special_principal_amount=special_principal_amount, total_principal_amount=total_principal_amount, loan_balance_amount=balance_eop)
            payment_schedule.append(payment)

        return payment_schedule

    def add_special_payment(self,payment_amount,first_payment_date,special_payment_term,annual_payments):
        """
        Adds a special payment to the loan.

        :param payment_amount: The amount of the special payment.
        :param first_payment_date: The date of the first special payment.
        :param special_payment_term: The term of the special payment in years.
        :param annual_payments: The number of special payments per year.
        """
        special_payment=SpecialPayment(payment_amount=payment_amount,first_payment_date=first_payment_date,special_payment_term=special_payment_term,annual_payments=annual_payments)
        self.special_payments.append(special_payment)
        self.special_payments_schedule.append(self._get_special_payment_schedule(self,special_payment))

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
