import unittest
import json
from dataclasses import asdict
from src.pyloan.pyloan import Loan
from tests.snapshot_helper import SnapshotHelper

class TestLoanScenarios(unittest.TestCase):

    def setUp(self):
        self.snapshot_helper = SnapshotHelper()

    def test_loan_scenarios_from_file(self):
        with open('tests/scenarios.json', 'r') as f:
            scenarios = json.load(f)

        for scenario in scenarios:
            scenario_name = scenario['scenario_name']
            with self.subTest(scenario_name=scenario_name):
                # Instantiate Loan with parameters
                loan = Loan(**scenario['loan_params'])

                # Add any special payments
                if 'special_payments' in scenario:
                    for sp in scenario['special_payments']:
                        loan.add_special_payment(**sp)

                # Generate the payment schedule
                payment_schedule = loan.get_payment_schedule()

                # Convert schedule to a serializable format (list of dicts)
                schedule_as_dicts = [asdict(p) for p in payment_schedule]

                # Compare with snapshot
                self.snapshot_helper.compare(scenario_name, schedule_as_dicts)

if __name__ == '__main__':
    unittest.main()
