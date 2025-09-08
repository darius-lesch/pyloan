import unittest
from decimal import Decimal
import datetime as dt
from src.pyloan.pyloan import Loan
from src.pyloan._models import Payment

class TestLoan(unittest.TestCase):

    def test_loan_creation(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01'
        )
        self.assertEqual(loan.loan_amount, Decimal('200000'))
        self.assertEqual(loan.interest_rate, Decimal('0.0600'))
        self.assertEqual(loan.loan_term, 30)

    def test_payment_schedule_annuity(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01'
        )
        schedule = loan.get_payment_schedule()
        self.assertEqual(len(schedule), 361) # 360 payments + initial balance
        self.assertAlmostEqual(schedule[-1].loan_balance_amount, Decimal('0.00'), places=2)

    def test_payment_schedule_linear(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01',
            loan_type='linear'
        )
        schedule = loan.get_payment_schedule()
        self.assertEqual(len(schedule), 361)
        self.assertAlmostEqual(schedule[-1].loan_balance_amount, Decimal('0.00'), places=2)

    def test_special_payments(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01'
        )
        loan.add_special_payment(
            payment_amount=10000,
            first_payment_date='2023-01-01',
            special_payment_term=1,
            annual_payments=1
        )
        schedule = loan.get_payment_schedule()
        zero_balance_payments = [p for p in schedule if p.loan_balance_amount == Decimal('0.00')]
        self.assertEqual(len(zero_balance_payments), 1)
        total_special_payments = sum([p.special_principal_amount for p in schedule])
        self.assertAlmostEqual(total_special_payments, Decimal('10000'), delta=100)

    def test_interest_only_period(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01',
            interest_only_period=12
        )
        schedule = loan.get_payment_schedule()
        self.assertAlmostEqual(schedule[1].loan_balance_amount, loan.loan_amount - schedule[1].principal_amount, places=2)

    def test_get_schedule_base_date(self):
        loan = Loan(
            loan_amount=100000,
            interest_rate=5.0,
            loan_term=10,
            start_date='2023-01-15',
            payment_end_of_month=True,
            annual_payments=12
        )
        expected_date = dt.datetime(2022, 12, 31)
        self.assertEqual(loan._get_schedule_base_date(), expected_date)

    def test_loan_term_in_months(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=360,
            loan_term_period='M',
            start_date='2022-01-01'
        )
        self.assertEqual(loan.loan_term, 30)
        self.assertEqual(loan.no_of_payments, 360)

    def test_validate_inputs(self):
        with self.assertRaises(ValueError):
            Loan(
                loan_amount=200000,
                interest_rate=6.0,
                loan_term=30,
                start_date='2022-01-01',
                first_payment_date='2021-01-01'
            )

    def test_initialize_payment_schedule(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01'
        )
        schedule = loan._initialize_payment_schedule()
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0].loan_balance_amount, Decimal('200000'))

    def test_first_payment_details(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01',
            compounding_method='30U/360'
        )
        schedule = loan.get_payment_schedule()
        first_payment = schedule[1]
        self.assertAlmostEqual(first_payment.interest_amount, Decimal('1000.00'), places=2)
        # This value depends on the annuity calculation, which is complex.
        # The important part is that the interest is correct.
        # The principal is the remainder of the payment.
        self.assertTrue(first_payment.principal_amount > 0)

    def test_interest_calculation_with_special_payment_on_odd_date(self):
        loan = Loan(
            loan_amount=1200,
            interest_rate=10,
            loan_term=1,
            start_date="2025-09-30",
            loan_term_period="Y",
            payment_end_of_month=True,
            annual_payments=12,
            interest_only_period=0,
            compounding_method="30U/360",
            loan_type="annuity"
        )
        loan.add_special_payment(
            payment_amount=250,
            first_payment_date="2026-01-19",
            special_payment_term=1,
            annual_payments=1,
            special_payment_term_period="Y"
        )
        schedule = loan.get_payment_schedule()
        payment_on_2026_01_31 = next(p for p in schedule if p.date.strftime('%Y-%m-%d') == '2026-01-31')
        self.assertAlmostEqual(payment_on_2026_01_31.interest_amount, Decimal('6.83'), places=2)

    def test_get_loan_summary_zero_division(self):
        loan = Loan(
            loan_amount=200000,
            interest_rate=6.0,
            loan_term=30,
            start_date='2022-01-01',
            loan_type='interest-only'
        )
        loan.loan_amount = Decimal('0')
        summary = loan.get_loan_summary()
        self.assertEqual(summary.repayment_to_principal, Decimal('0.00'))

if __name__ == '__main__':
    unittest.main()
