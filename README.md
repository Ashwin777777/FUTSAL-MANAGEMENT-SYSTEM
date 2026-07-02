# Futsal Hub - Futsal Management System ⚽🇳🇵

Futsal Hub is a simple web application designed to help futsal arenas in Nepal manage their court bookings, equipment rentals, and customer logs. 

---

## Key Features

* **Interactive Slot Booking**: Select a date and click on consecutive time slots to book a court.
* **Smart Surcharges**: Surcharges are automatically calculated for weekend bookings (15%) and peak evening slots (25% from 4:00 PM to 10:00 PM).
* **Gear Rentals**: Add rentable gear (balls, bibs, shoes, gloves) to bookings, with stock levels tracked dynamically.
* **Promo Code Discounts**: Enter valid codes (like `WELCOME10`) to receive instant booking discounts.
* **Management Dashboards**: View visual reports, register courts, update gear, and block schedules for maintenance.

---

## Getting Started

Follow these steps to run the application on your computer:

### 1. Install Dependencies
Make sure you have Python installed, then install the required libraries:
```powershell
pip install -r requirements.txt
```

### 2. Setup the Database
Ensure your MySQL server is running, configure your database details in `config.py`, and run the setup script to create tables and seed initial records:
```powershell
python seed.py
```

### 3. Run the Application
Start the Flask web server:
```powershell
python run.py
```
Open your web browser and go to **[http://127.0.0.1:5000](http://127.0.0.1:5000)** to view the website.

---

## running unit tests
To run the automated tests locally (runs in-memory and will not affect your MySQL database):
```powershell
python -m unittest discover -s tests
```
