# Test Failures Report 🧪❌

This document lists the **4 intentional test failures** added to the testing suite to verify that our system correctly detects and rejects invalid states (such as double bookings, expired discounts, price mismatches, and over-stock checkouts).

---

## 1. Peak Hour Price Assertion Mismatch
* **Test Case**: `test_peak_hour_price_assertion_mismatch`
* **File**: `tests/test_failures.py`
* **Description**: Asserts that a booking slot during peak hours (17:00 - 18:00) costs the regular flat rate (Rs. 1000.0) instead of the peak rate (Rs. 1250.0).
* **Why it failed**: The pricing engine correctly applies the 25% peak-hour multiplier, returning a cost of Rs. 1250.0, causing the assert equal to fail.
* **Traceback / Error Output**:
  ```
  AssertionError: 1250.0 != 1000.0
  Traceback (most recent call last):
    File "tests/test_failures.py", line 58, in test_peak_hour_price_assertion_mismatch
      self.assertEqual(pricing['court_cost'], 1000.0)
  ```

---

## 2. Double-Booking Validation
* **Test Case**: `test_double_booking_success_expectation`
* **File**: `tests/test_failures.py`
* **Description**: Expects that booking a court slot that has already been reserved by another customer will succeed.
* **Why it failed**: The booking controller correctly blocks double booking and returns `False` for the second attempt, which conflicts with our assertion of `True`.
* **Traceback / Error Output**:
  ```
  AssertionError: False is not true
  Traceback (most recent call last):
    File "tests/test_failures.py", line 89, in test_double_booking_success_expectation
      self.assertTrue(success2)
  ```

---

## 3. Expired Promo Code Discount
* **Test Case**: `test_expired_promo_code_discount_expectation`
* **File**: `tests/test_failures.py`
* **Description**: Tries to apply an expired promo code (`EXPIRED50` valid until 5 days ago) to a booking, expecting a 50% discount (Rs. 500.0).
* **Why it failed**: The pricing calculation correctly verifies the validity date of the promo code and applies Rs. 0.0 discount instead of Rs. 500.0.
* **Traceback / Error Output**:
  ```
  AssertionError: 0.0 != 500.0
  Traceback (most recent call last):
    File "tests/test_failures.py", line 114, in test_expired_promo_code_discount_expectation
      self.assertEqual(pricing['discount'], 500.0)
  ```

---

## 4. Insufficient Equipment Stock Checkout
* **Test Case**: `test_insufficient_equipment_stock_success_expectation`
* **File**: `tests/test_failures.py`
* **Description**: Attempts to reserve 10 units of futsal shoes when the system stock level is only 5 units.
* **Why it failed**: The controller blocks the reservation due to lack of stock and returns `False`, whereas the test asserts `True`.
* **Traceback / Error Output**:
  ```
  AssertionError: False is not true
  Traceback (most recent call last):
    File "tests/test_failures.py", line 135, in test_insufficient_equipment_stock_success_expectation
      self.assertTrue(success)
  ```
