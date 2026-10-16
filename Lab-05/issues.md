# Static Analysis Issues — Car Rental System

This table records issues found in the original `car_rental.py`.
Line numbers refer to that original version.

All 11 original Bandit findings have been addressed. Pylint scores
**10.00/10 with no warnings**, and Flake8 reports **no issues**.

The shared feature-list bug, negative daily rates, double booking, and
invalid rental dates have also been addressed.

Original reports are preserved in `reports/before/`, and final reports
are saved in `reports/after/`. Table line numbers refer to the original code.

## Baseline reports

- [Pylint report](reports/before/pylint_report.txt): **4.94/10**.
- [Bandit report](reports/before/bandit_report.txt): **11 findings** —
  2 high, 4 medium, and 5 low severity.
- [Flake8 report](reports/before/flake8_report.txt): formatting and code issues.

High and medium Bandit findings appear first. Severity labels below are taken
from Bandit; Pylint and Flake8 findings are identified by their warning codes.
Related warnings are grouped into one row where they describe the same issue.

## Issues reported by the tools

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Weak SHA-1 hashing | Security — High; Bandit B324 | 48 | `licenceHash()` uses SHA-1, which is unsuitable for security-sensitive hashing because of known collision weaknesses. | Use SHA-256 if the function only needs a digest. If the purpose is to conceal predictable licence numbers, use a keyed HMAC with SHA-256 and a separately configured secret; an ordinary hash alone does not provide that protection. |
| Receipt permissions are too broad | Security — High; Bandit B103 | 67 | `os.chmod(path, 0o777)` gives every local user read, write, and execute permissions on the receipt, subject to directory access. | Remove the permissive permission change and retain the secure temporary file's owner-only permissions, or explicitly use `0o600`. Receipts do not need execute permission. |
| SQL injection in customer registration | Security — Medium; Bandit B608 | 23 | Customer values are inserted into SQL through `%` string formatting. Quotes in input can break the query or alter its meaning. | Use SQLite `?` placeholders and pass `(name, licence, phone)` separately to `conn.execute()`. Do not replace SQL interpolation with an f-string. |
| SQL injection in customer lookup | Security — Medium; Bandit B608 | 26–27 | Concatenating the name into the query lets input change the SQL condition. The demo's injection string can return all customers. | Execute `SELECT * FROM customers WHERE name = ?` with `(name,)` as the parameter tuple. |
| Arbitrary code execution through promo rules | Security — Medium; Bandit B102; Pylint W0122 | 50–54 | `exec()` executes the supplied promo rule as Python code. An empty globals dictionary does not make this safe. | Replace executable rule text with supported promo identifiers or a validated numeric discount, and calculate the price using explicit arithmetic. Update the demo call to use the new interface. |
| Unsafe temporary receipt creation | Security — Medium; Bandit B306 | 63–64 | `tempfile.mktemp()` produces a filename without creating the file. Another process may create that path before `open()` uses it. | Create and open the file atomically with `tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False)` in a context manager, then return its name. |
| Customer validation relies on an assertion | Security — Low; Bandit B101 | 30 | Python can remove `assert` statements in optimized mode, allowing the registration check to disappear. | Use an explicit condition and raise a clear exception, such as `ValueError`, when the customer is not registered. |
| Exceptions are caught and silently ignored | Security — Low; Bandit B110; Pylint W0702; Flake8 E722 | 36–42 | A bare `except` catches all exceptions, including interrupts, and `pass` hides failures. Returning an unknown car therefore fails silently. | Validate the plate before accessing the fleet. Catch only exceptions that can be handled meaningfully, and report or propagate errors instead of ignoring them. |
| Booking codes use a non-cryptographic generator | Security — Low; Bandit B311 | 45 | `random.randint()` is unsuitable if booking codes must be unpredictable. The five-digit space can also produce duplicate codes, a separate concern identified by code review. | Use `secrets` for unpredictable codes, choose an adequate code space, and check for existing codes before accepting a new one. Cryptographic randomness alone does not guarantee uniqueness. |
| Hardcoded admin password and password default | Security — Low; Bandit B107 and B105 | 70–71; demo call at 97 | The password is embedded in the source and is also the default argument. Calling `adminLogin("admin")` succeeds without the caller supplying a password. | Require an explicit password, load the expected credential from configuration outside the source, and reject login when that configuration is missing. Update the demo to supply a password explicitly. |
| Mutable default argument | Bug risk — Pylint W0102 | 16; stored at 19 | The default `features=[]` list is created once and shared between calls that omit it. A later mutation can affect multiple cars. | Use `features=None` and create a fresh list inside the function. Copy a supplied list if each car should own an independent feature list. |
| Inconsistent return values | Code quality — Pylint R1710 | 16–20, 36–42 | `addCar()` returns a dictionary or no value. `returnCar()` returns a charge only when kilometres exceed 300 and otherwise returns `None`. | Define consistent behavior: return the created car or raise a validation error; return a numeric charge, including `0` when no extra charge applies, and raise an error for invalid returns. |
| Receipt file is not managed by a context manager | Resource handling — Pylint R1732 | 64–66 | If writing raises an exception, execution can skip `f.close()`. | Use a `with` block around the securely created temporary file so it closes even when writing fails. |
| Receipt encoding is implicit | Portability — Pylint W1514 | 64 | Omitting an encoding makes receipt text depend on the platform's default encoding. | Specify `encoding="utf-8"` when opening the receipt for writing. |
| Missing module and function documentation | Documentation — Pylint C0114 and C0116 | 1; 16, 22, 25, 29, 36, 44, 47, 50, 56, 62, 70, 75, 82 | The module and every function lack docstrings explaining their purpose and behavior. | Add a module docstring and concise function docstrings, including relevant return values and validation errors. |
| Function names do not follow snake_case | Naming — Pylint C0103 | 16, 22, 25, 29, 36, 44, 47, 50, 56, 62, 70, 75 | Functions use names such as `addCar` and `registerCustomer` instead of Python's snake_case convention. | Rename them consistently, such as `add_car` and `register_customer`, and update all call sites. |
| Unused JSON import | Code quality — Pylint W0611; Flake8 F401 | 2 | `json` is imported but never used. | Remove the unused import. |
| Lines exceed configured length limits | Style — Pylint C0301; Flake8 E501 | 19, 23, 31, 33, 65, 88–90 | Flake8 reports lines over 79 characters; Pylint also reports lines 33 and 65 for exceeding its 100-character limit. | Wrap expressions, dictionaries, and calls across multiple lines using parentheses. Keep lines within 79 characters to satisfy both reports' limits. |
| Missing blank lines around top-level functions | Style — Flake8 E302 and E305 | 16, 22, 25, 29, 36, 44, 47, 50, 56, 62, 70, 75, 82, 101 | Top-level definitions and the code after `main()` do not have the required two blank lines. | Add two blank lines around top-level function definitions and before the final top-level call. |
| Older string formatting | Style — Pylint C0209 | 23, 65 | Pylint suggests f-strings for `%` formatting. SQL construction at line 23 requires a security fix, not just a formatting change. | Use parameterized SQL at line 23 and an f-string for the receipt text at line 65. |
| Redundant comparison with True | Style — Pylint C0121; Flake8 E712 | 78 | The availability flag is explicitly compared with `True`. | Test the boolean flag directly, such as `if car["available"]:`. |
| Dictionary iteration performs repeated lookups | Code quality — Pylint C0206 | 77–79 | The loop iterates over keys and then looks up each corresponding car. | Iterate over `fleet.items()` to access each plate and car directly. |
| Plate validation has a redundant conditional | Code quality — Pylint R1703 and R1705 | 57–60 | The conditional returns `True` or `False` directly and includes an unnecessary `else` after `return`. | Return the boolean result directly. Using `re.fullmatch(pattern, plate) is not None` also expresses whole-string validation clearly. |

## Additional observations from reading the code

These are manual observations, not findings attributed to the saved reports.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| A car can be booked repeatedly while rented | Logic bug | 29–34; demonstrated at 88–89 | `rentCar()` neither checks the availability flag nor sets it to `False`. The demo accepts two overlapping rentals for the same car. | For this simple availability-based model, reject unavailable cars and mark a car unavailable after a successful booking. Mark it available again on return. |
| Reversed dates create a negative rental cost | Input validation | 31–32; demonstrated at 90 | The date difference is used without checking that the end date comes after the start date. | Validate both dates and require a positive rental duration before calculating the cost or adding a booking. Handle the expected rejection in the demo. |
| Negative daily rates are accepted | Input validation | 16–19; demonstrated at 85 | The fleet accepts a daily rate of `-500`, which could produce a negative charge when rented. | Reject negative rates before adding a car. Decide explicitly whether a zero rate is allowed, and update the demo to handle invalid input. |

## Verification after fixes

- [Final Pylint report](reports/after/pylint_report.txt): **10.00/10**, with no warnings.
- [Final Bandit report](reports/after/bandit_report.txt): **No issues identified**, with no skipped tests or files reported.
- [Final Flake8 report](reports/after/flake8_report.txt): **No issues**; the empty report is the expected result of a clean scan.
- The demo confirmed a valid Swift rental costs `4500`, the injection lookup returns `[]`, and driving 420 kilometres produces an extra charge of `600`.
- The demo also confirmed that negative daily rates, a second rental of an unavailable car, reversed rental dates, and returning an unknown car are rejected with clear messages.
