"""Manage a car rental fleet, customers, bookings, and receipts."""
import os
import re
import sqlite3
import hashlib
import secrets
import tempfile
from datetime import datetime
from getpass import getpass

# Global rental state
fleet = {}
bookings = []
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)")


def add_car(plate, model="Unknown", daily_rate=0, features=None):
    """Add a car with its own feature list and a nonnegative daily rate."""
    if not plate:
        raise ValueError("Plate cannot be empty")

    if plate in fleet:
        raise ValueError("Car already exists")

    if daily_rate < 0:
        raise ValueError("Daily rate cannot be negative")

    fleet[plate] = {
        "model": model,
        "rate": daily_rate,
        "available": True,
        "features": list(features) if features is not None else [],
    }
    return fleet[plate]


def register_customer(name, licence, phone):
    """Store a customer's name, licence, and phone number."""
    conn.execute(
        "INSERT INTO customers VALUES (?, ?, ?)",
        (name, licence, phone),
    )


def find_customer(name):
    """Find customer records matching the supplied name."""
    query = "SELECT * FROM customers WHERE name = ?"
    return conn.execute(query, (name,)).fetchall()


def rent_car(plate, customer, start, end):
    """Book an available car for a positive number of days."""
    if not find_customer(customer):
        raise ValueError("Customer not registered")

    if plate not in fleet:
        raise ValueError("Unknown car")

    if not fleet[plate]["available"]:
        raise ValueError("Car is already rented")

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    days = (end_date - start_date).days

    if days <= 0:
        raise ValueError("End date must be after start date")

    cost = days * fleet[plate]["rate"]
    bookings.append(
        {
            "code": booking_code(),
            "plate": plate,
            "customer": customer,
            "days": days,
            "cost": cost,
        }
    )
    fleet[plate]["available"] = False
    return cost


def return_car(plate, km_driven):
    """Mark a known car available and calculate its extra distance fee."""
    if plate not in fleet:
        raise ValueError("Unknown car")

    if km_driven < 0:
        raise ValueError("Distance cannot be negative")

    fleet[plate]["available"] = True
    return max(0, km_driven - 300) * 5


def booking_code():
    """Generate a random code not already used by a current booking."""
    while True:
        code = f"BK-{secrets.token_hex(8)}"
        if not any(booking["code"] == code for booking in bookings):
            return code


def licence_hash(licence):
    """Return the SHA-256 digest of a licence number."""
    return hashlib.sha256(licence.encode("utf-8")).hexdigest()


def apply_promo(discount_percent, amount):
    """Apply a discount percentage between zero and one hundred."""
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")

    return amount * (1 - discount_percent / 100)


def is_valid_plate(plate):
    """Return whether a plate matches the required format."""
    pattern = r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}"
    return re.fullmatch(pattern, plate) is not None


def write_receipt(booking):
    """Write a booking receipt securely and return its file path."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        delete=False,
    ) as receipt:
        receipt.write(
            f"Booking {booking['code']}: {booking['plate']} "
            f"for {booking['days']} days = Rs.{booking['cost']}\n"
        )
        path = receipt.name

    return path


def admin_login(user, password):
    """Check credentials against the configured admin password."""
    expected_password = os.getenv("CAR_RENTAL_ADMIN_PASSWORD")

    if not expected_password:
        return False

    return user == "admin" and secrets.compare_digest(
        password.encode("utf-8"),
        expected_password.encode("utf-8"),
    )


def available_cars():
    """Return the plates of cars currently available for rental."""
    return [
        plate
        for plate, car in fleet.items()
        if car["available"]
    ]


def main():
    """Demonstrate valid operations and rejected invalid requests."""
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)
    try:
        add_car("KA03EF9999", "Nexon", -500)
    except ValueError as error:
        print("Add Nexon:", error)
    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")
    print(
        "Rent Swift:",
        rent_car("KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"),
    )
    try:
        cost = rent_car(
            "KA01AB1234", "Ravi", "2026-11-02", "2026-11-03"
        )
        print("Rent Swift again:", cost)
    except ValueError as error:
        print("Rent Swift again:", error)
    try:
        cost = rent_car(
            "KA02CD5678", "Ravi", "2026-11-10", "2026-11-07"
        )
        print("Rent Innova:", cost)
    except ValueError as error:
        print("Rent Innova:", error)
    print("Lookup injection:", find_customer("x' OR '1'='1"))
    print("Extra km charge:", return_car("KA01AB1234", 420))
    try:
        print("Return unknown car:", return_car("XX00XX0000", 50))
    except ValueError as error:
        print("Return unknown car:", error)
    print("Promo price:", apply_promo(10, 4500))
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    print("Licence hash:", licence_hash("DL-0420110012345"))
    print("Admin:", admin_login("admin", getpass("Admin password: ")))
    print("Available:", available_cars())
    print("Receipt saved to:", write_receipt(bookings[0]))


main()
