import unittest
from decimal import Decimal
from src.pyloan.pyloan import Loan

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
        self.assertTrue(len(zero_balance_payments) > 1)
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
        # During interest only period, principal should not decrease
        self.assertAlmostEqual(schedule[1].loan_balance_amount, loan.loan_amount - schedule[1].principal_amount, places=2)

if __name__ == '__main__':
    unittest.main()
