# 🏨 Grand Azure — Hotel Management System

A full-featured **Hotel Management System** web application built with Python Flask and SQLite. Designed for hotel front desk operations — manage rooms, guests, bookings, billing, room services, and analytics all from a modern browser-based dashboard.

---

## ✨ Features

### Core Operations
- **Room Management** — Add, edit, delete rooms with type, pricing, floor, capacity, and amenities
- **Customer Registry** — Maintain guest records with ID proof, contact details, nationality, and booking history
- **Booking System** — Full reservation lifecycle: Create → Confirm → Check-In → Check-Out / Cancel
- **Smart Room Availability** — Real-time AJAX room search with date overlap detection to prevent double bookings

### Billing & Payments
- **Itemized Billing** — Room charges + extra services + 12% GST tax, calculated automatically
- **Partial & Full Payments** — Track payment status (Pending / Partial / Paid)
- **Coupon System** — Apply percentage or fixed-amount discount coupons (e.g., `WELCOME10`, `SUMMER20`, `FLAT500`)
- **PDF Invoice Generation** — Download professional invoices as PDF files via ReportLab

### Room Services
- **Service Tracking** — Add food, laundry, spa, mini bar, airport transfer, and other charges to active bookings
- **Auto Bill Recalculation** — Adding or removing services instantly recalculates the total bill

### Administration
- **Role-Based Access Control** — Admin and Staff roles with different permissions
- **Staff Management** — Admin can create new staff user accounts with encrypted passwords
- **Analytics Dashboard** — Occupancy rate, revenue trends, room type distribution, booking status charts (Admin only)

### User Experience
- **Dark / Light Mode** — Toggle theme with persistence via `localStorage`
- **Responsive Design** — Works on desktop, tablet, and mobile browsers
- **DataTables Integration** — Searchable, sortable, paginated tables across all listing pages
- **Flash Notifications** — Success, warning, and error messages with auto-dismiss

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Database** | SQLite 3 (file-based, zero configuration) |
| **Frontend** | HTML5, CSS3, JavaScript |
| **UI Framework** | Bootstrap 5.3, Bootstrap Icons |
| **Tables** | jQuery DataTables |
| **Authentication** | bcrypt (password hashing) |
| **PDF Generation** | ReportLab |
| **Templating** | Jinja2 |

---

## 📁 Project Structure

```
Grand-Azure-Hotel/
│
├── web_app.py              # Main Flask application (routes, auth, controllers)
├── database.py             # SQLite database layer (models, queries, business logic)
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           #   └── Master layout (sidebar, topbar, theme toggle)
│   ├── login.html          #   └── Login page
│   ├── dashboard.html      #   └── Dashboard with live stats
│   ├── rooms.html          #   └── Room listing with filters
│   ├── room_form.html      #   └── Add / Edit room form
│   ├── bookings.html       #   └── Booking listing with date & status filters
│   ├── booking_form.html   #   └── New / Edit booking (AJAX room availability)
│   ├── booking_detail.html #   └── Booking details, check-in/out actions
│   ├── customers.html      #   └── Guest listing with search
│   ├── customer_form.html  #   └── Add / Edit guest
│   ├── customer_history.html#  └── Guest booking history & total spend
│   ├── billing.html        #   └── Billing overview (all invoices)
│   ├── billing_detail.html #   └── Invoice detail, payments, coupons, PDF download
│   ├── services.html       #   └── Room service management (POS-style)
│   ├── analytics.html      #   └── Charts & analytics (Admin only)
│   ├── users.html          #   └── Staff listing (Admin only)
│   └── user_form.html      #   └── Create staff account (Admin only)
│
├── static/
│   ├── css/style.css       # Custom CSS (dark/light themes, layout, components)
│   └── js/main.js          # Client-side JS (sidebar, theme toggle, tooltips)
│
└── utils/
    └── pdf_invoice.py      # ReportLab PDF invoice generator
```

---

## 🗄️ Database Schema

The application uses **SQLite** with 6 relational tables:

```
┌──────────┐     ┌───────────┐     ┌──────────┐
│  users   │     │ customers │     │  rooms   │
├──────────┤     ├───────────┤     ├──────────┤
│ id (PK)  │     │ id (PK)   │     │ id (PK)  │
│ username │     │ name      │     │ room_no  │
│ password │     │ email     │     │ type     │
│ role     │     │ phone     │     │ price    │
│ full_name│     │ id_type   │     │ status   │
│ email    │     │ id_number │     │ floor    │
└──────────┘     │ nationality│    │ capacity │
                 └─────┬─────┘     │ amenities│
                       │           └────┬─────┘
                       │                │
                 ┌─────▼────────────────▼─────┐
                 │        bookings            │
                 ├────────────────────────────┤
                 │ id (PK)                    │
                 │ booking_ref                │
                 │ customer_id (FK)           │
                 │ room_id (FK)               │
                 │ check_in / check_out       │
                 │ status, total, paid, tax   │
                 │ payment_status, method     │
                 │ coupon_code, discount      │
                 └─────────────┬──────────────┘
                               │
                 ┌─────────────▼──────────────┐
                 │         services            │
                 ├─────────────────────────────┤
                 │ id (PK)                     │
                 │ booking_id (FK)             │
                 │ service_type, description   │
                 │ quantity, unit_price, amount │
                 └─────────────────────────────┘

                 ┌─────────────────────────────┐
                 │          coupons             │
                 ├─────────────────────────────┤
                 │ id (PK)                     │
                 │ code (UNIQUE)               │
                 │ discount_type (% or fixed)  │
                 │ discount_value              │
                 │ valid_from / valid_until     │
                 │ max_uses, used_count         │
                 └─────────────────────────────┘
```

---

## 🚀 How to Run This Project Locally

### Prerequisites
- **Python 3.10+** installed on your system ([Download Python](https://www.python.org/downloads/))
- **pip** (comes pre-installed with Python)
- **Git** (optional, for cloning)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/hotel-management-system.git
cd hotel-management-system
```

Or download the ZIP from GitHub and extract it.

### Step 2: Create a Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install flask bcrypt reportlab Pillow matplotlib
```

### Step 4: Run the Application

```bash
python web_app.py
```

You should see:
```
[*] Grand Azure Hotel - Web App
    Running at: http://127.0.0.1:5001
    Login: admin / admin123
    Login: staff / staff123
```

### Step 5: Open in Browser

Navigate to **http://127.0.0.1:5001** in your web browser.

---

## 🔑 Default Login Credentials

| Role | Username | Password | Access Level |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full access (Rooms, Bookings, Billing, Services, Analytics, Staff Management) |
| **Staff** | `staff` | `staff123` | Operational access (Rooms, Bookings, Billing, Services — no Analytics or Staff Management) |

> **Note:** Passwords are securely hashed using **bcrypt**. The database (`hotel.db`) is automatically created on first run with sample rooms, coupons, and user accounts.

---

## 📋 Sample Data (Auto-Generated on First Run)

### Rooms (10 rooms across 3 floors)
| Room | Type | Price/Night | Floor |
|---|---|---|---|
| 101, 102 | Single | ₹2,500 | 1 |
| 103, 104 | Double | ₹3,500 | 1 |
| 201, 202, 203 | Deluxe | ₹5,000 – ₹5,500 | 2 |
| 301, 302 | Suite | ₹9,000 | 3 |
| 303 | Presidential Suite | ₹15,000 | 3 |

### Discount Coupons
| Code | Discount | Condition |
|---|---|---|
| `WELCOME10` | 10% off | Min ₹1,000 booking |
| `SUMMER20` | 20% off | Valid Apr–Sep 2026 |
| `FLAT500` | ₹500 flat off | Min ₹3,000 booking |

---

## 🔄 Application Workflow

```
Guest Arrives → Register Customer → Create Booking → Room Status: Booked
                                         │
                                    Check-In Guest → Room Status: Occupied
                                         │
                                    Add Room Services (Food, Laundry, Spa, etc.)
                                         │
                                    Process Payments (Cash / Card / UPI)
                                    Apply Discount Coupons
                                         │
                                    Check-Out Guest → Room Status: Available
                                         │
                                    Download PDF Invoice
```

---

## 🛡️ Security Features

- **bcrypt Password Hashing** — Passwords are never stored in plain text
- **Role-Based Access Control** — Admin-only routes are protected with `@admin_required` decorator
- **Session-Based Authentication** — Flask secure session management
- **SQL Parameterized Queries** — All database queries use parameterized statements to prevent SQL injection
- **WAL Mode** — SQLite Write-Ahead Logging for safe concurrent database access

---

## 💻 Development Mode

To run with **debug mode enabled** (auto-reload on code changes + interactive error pages):

**Windows PowerShell:**
```powershell
$env:FLASK_DEBUG="True"; python web_app.py
```

**macOS / Linux:**
```bash
FLASK_DEBUG=True python web_app.py
```
