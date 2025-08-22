# AGENTS

## Project Overview
This is a Python package intended for defining and analyzing mortgage and/or loand payment schedules, including periodic and ad-hoc repayments. The objective is to have a lean and robust mortage and/or loan payment schedule comparison tool that would allow users to make informed decisions about mortgages and/or loans.

## Technology Stack
* **Code:** all code is writeen in Python.
* **Testing:** The project uses the `unittest` framework for testing.

## Code Structure
The core logic is located in `src/pyloan`. The main class is `Loan` in `src/pyloan/pyloan.py`. The code is structured as follows:
- `pyloan.py`: Contains the main `Loan` class and its methods.
- `_validators.py`: Contains validation functions for the `Loan` class inputs.
- `_enums.py`: Contains `Enum` classes for loan types and compounding methods.
- `_models.py`: Contains `dataclasses` for data structures like `Payment`, `SpecialPayment`, and `LoanSummary`.

## Common Tasks:
* **Feature Development:** Create python-based methods enhance `pyloan` package features. All new features should be accompanied by unit tests.
* **Bug Fixes:** Address issues in the code. Make sure that the best practices for building Python package are used consistently. All bug fixes should be accompanied by unit tests that reproduce the bug and verify the fix.
* **Refactoring**: Improve existing code for readability and performance. But avoid introducing breaking changes without a clear plan.

## Important Notes:
* When working on new features, create a separate branch from the `develop` branch ad submit a pull request for review. Follow the `gitflow` model.
* Use the helper modules (`_validators.py`, `_enums.py`, `_models.py`) when adding new features or modifying existing ones.
* Write unit tests for all new code and ensure that all tests pass before submitting a pull request.
