import unittest
import timeit
from src.pyloan.pyloan import Loan

class TestPerformance(unittest.TestCase):

    def test_get_payment_schedule_performance(self):
        """
        Benchmarks the performance of the get_payment_schedule method.

        Note: A direct comparison with the pre-refactoring implementation is not
        performed here. This benchmark serves to quantify the performance of the
        current implementation and can be used to track future optimizations.
        The refactoring had to prioritize correctness of the complex date logic
        over full vectorization of the main calculation loop, so performance gains
        are expected to be modest.
        """
        loan = Loan(
            loan_amount=500000,
            interest_rate=4.5,
            loan_term=30,
            start_date='2023-01-01'
        )

        # Add a special payment to make the scenario more complex
        loan.add_special_payment(
            payment_amount=10000,
            first_payment_date='2025-01-01',
            special_payment_term=1,
            annual_payments=1
        )

        # Time the execution of get_payment_schedule
        execution_time = timeit.timeit(lambda: loan.get_payment_schedule(), number=10)

        print(f"\nExecution time for get_payment_schedule (10 runs): {execution_time:.4f} seconds")

        # We are not asserting any specific performance target, just measuring.
        self.assertTrue(execution_time > 0)

if __name__ == '__main__':
    unittest.main()
