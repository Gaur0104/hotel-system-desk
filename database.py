import sqlite3
import os
import bcrypt
import random
import string
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel.db")

def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def _scalar(conn, sql, params=()):
    """Execute a single-value query and return the first column value."""
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return 0
    return list(row.values())[0]

def generate_booking_ref():
    return "BK" + ''.join(random.choices(string.digits, k=8))

# ─────────────────────────── INIT ────────────────────────────

def initialize_database():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'staff',
        full_name TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE NOT NULL,
        room_type TEXT NOT NULL,
        price_per_night REAL NOT NULL,
        status TEXT DEFAULT 'Available',
        floor INTEGER DEFAULT 1,
        capacity INTEGER DEFAULT 2,
        amenities TEXT DEFAULT '',
        description TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        id_type TEXT DEFAULT 'Passport',
        id_number TEXT,
        address TEXT,
        nationality TEXT DEFAULT 'Indian',
        date_of_birth TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_ref TEXT UNIQUE NOT NULL,
        customer_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        check_in_date TEXT NOT NULL,
        check_out_date TEXT NOT NULL,
        status TEXT DEFAULT 'Confirmed',
        total_nights INTEGER DEFAULT 1,
        room_charges REAL DEFAULT 0,
        extra_charges REAL DEFAULT 0,
        discount_amount REAL DEFAULT 0,
        tax_rate REAL DEFAULT 0.12,
        tax_amount REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Pending',
        payment_method TEXT DEFAULT 'Cash',
        special_requests TEXT DEFAULT '',
        coupon_code TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id),
        FOREIGN KEY (room_id) REFERENCES rooms(id)
    );

    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        service_type TEXT NOT NULL,
        description TEXT DEFAULT '',
        quantity INTEGER DEFAULT 1,
        unit_price REAL NOT NULL,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'Delivered',
        date TEXT DEFAULT CURRENT_DATE,
        FOREIGN KEY (booking_id) REFERENCES bookings(id)
    );

    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_type TEXT DEFAULT 'percentage',
        discount_value REAL NOT NULL,
        min_amount REAL DEFAULT 0,
        max_uses INTEGER DEFAULT 100,
        used_count INTEGER DEFAULT 0,
        valid_from TEXT,
        valid_until TEXT,
        is_active INTEGER DEFAULT 1,
        description TEXT DEFAULT ''
    );

    """)
    conn.commit()

    # Default admin
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    if not c.fetchone():
        ph = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users (username,password_hash,role,full_name,email) VALUES (?,?,'admin','System Administrator','admin@hotel.com')", ('admin', ph))
        ph2 = bcrypt.hashpw(b'staff123', bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users (username,password_hash,role,full_name,email) VALUES (?,?,'staff','Front Desk Staff','staff@hotel.com')", ('staff', ph2))
        conn.commit()

    # Sample rooms
    c.execute("SELECT COUNT(*) AS cnt FROM rooms")
    if c.fetchone()['cnt'] == 0:
        rooms = [
            ('101','Single',2500,'Available',1,1,'WiFi, TV, AC','Cozy single room'),
            ('102','Single',2500,'Available',1,1,'WiFi, TV, AC','Cozy single room'),
            ('103','Double',3500,'Available',1,2,'WiFi, TV, AC, Mini Bar','Comfortable double room'),
            ('104','Double',3500,'Maintenance',1,2,'WiFi, TV, AC, Mini Bar','Under maintenance'),
            ('201','Deluxe',5000,'Available',2,2,'WiFi, Smart TV, AC, Mini Bar, Balcony','Deluxe with city view'),
            ('202','Deluxe',5000,'Available',2,2,'WiFi, Smart TV, AC, Mini Bar, Balcony','Deluxe with pool view'),
            ('203','Deluxe',5500,'Available',2,3,'WiFi, Smart TV, AC, Jacuzzi','Premium deluxe room'),
            ('301','Suite',9000,'Available',3,4,'WiFi, Smart TV, AC, Mini Bar, Jacuzzi, Butler','Luxury suite'),
            ('302','Suite',9000,'Booked',3,4,'WiFi, Smart TV, AC, Mini Bar, Jacuzzi','Luxury suite'),
            ('303','Presidential Suite',15000,'Available',3,6,'All Premium Amenities, Private Pool','Presidential suite'),
        ]
        c.executemany("INSERT INTO rooms (room_number,room_type,price_per_night,status,floor,capacity,amenities,description) VALUES (?,?,?,?,?,?,?,?)", rooms)

        coupons = [
            ('WELCOME10','percentage',10,1000,50,None,None,1,'10% off for new guests'),
            ('SUMMER20','percentage',20,2000,30,'2026-04-01','2026-09-30',1,'Summer special'),
            ('FLAT500','fixed',500,3000,20,None,None,1,'Flat ₹500 off'),
        ]
        c.executemany("INSERT INTO coupons (code,discount_type,discount_value,min_amount,max_uses,valid_from,valid_until,is_active,description) VALUES (?,?,?,?,?,?,?,?,?)", coupons)
        conn.commit()

    conn.close()

# ─────────────────────────── AUTH ────────────────────────────

def authenticate_user(username, password):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if row and bcrypt.checkpw(password.encode(), row['password_hash'].encode()):
        conn.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (row['id'],))
        conn.commit()
        conn.close()
        return row
    conn.close()
    return None

def get_all_users(conn=None):
    close = conn is None
    if close: conn = get_connection()
    rows = conn.execute("SELECT id,username,role,full_name,email,created_at,last_login FROM users").fetchall()
    if close: conn.close()
    return rows

def create_user(username, password, role, full_name, email):
    conn = get_connection()
    # Only allow creating staff accounts — admin is a single protected account
    role = 'staff'
    ph = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        conn.execute("INSERT INTO users (username,password_hash,role,full_name,email) VALUES (?,?,?,?,?)", (username,ph,role,full_name,email))
        conn.commit()
        return True, "User created"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def delete_user(user_id):
    conn = get_connection()
    user = conn.execute("SELECT role, username FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return False, "User not found"
    if user['role'] == 'admin':
        conn.close()
        return False, "Cannot delete the admin account"
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True, f"User '{user['username']}' deleted successfully"

# ─────────────────────────── ROOMS ───────────────────────────

def get_all_rooms(status_filter=None, type_filter=None):
    conn = get_connection()
    q = "SELECT * FROM rooms WHERE 1=1"
    params = []
    if status_filter and status_filter != "All":
        q += " AND status=?"; params.append(status_filter)
    if type_filter and type_filter != "All":
        q += " AND room_type=?"; params.append(type_filter)
    q += " ORDER BY room_number"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows

def get_room(room_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
    conn.close()
    return row

def add_room(data):
    conn = get_connection()
    try:
        conn.execute("""INSERT INTO rooms (room_number,room_type,price_per_night,status,floor,capacity,amenities,description)
                        VALUES (:room_number,:room_type,:price_per_night,:status,:floor,:capacity,:amenities,:description)""", data)
        conn.commit()
        return True, "Room added"
    except sqlite3.IntegrityError:
        return False, "Room number already exists"
    finally:
        conn.close()

def update_room(room_id, data):
    conn = get_connection()
    conn.execute("""UPDATE rooms SET room_number=:room_number, room_type=:room_type,
        price_per_night=:price_per_night, status=:status, floor=:floor,
        capacity=:capacity, amenities=:amenities, description=:description WHERE id=:id""",
        {**data, 'id': room_id})
    conn.commit()
    conn.close()

def delete_room(room_id):
    conn = get_connection()
    # Check if room has any active bookings (Confirmed or Checked In)
    active = conn.execute(
        "SELECT COUNT(*) AS cnt FROM bookings WHERE room_id=? AND status IN ('Confirmed','Checked In')",
        (room_id,)
    ).fetchone()['cnt']
    if active > 0:
        conn.close()
        raise Exception(f"Room has {active} active booking(s). Check out or cancel them first.")
    # Delete services linked to this room's old bookings
    conn.execute(
        "DELETE FROM services WHERE booking_id IN (SELECT id FROM bookings WHERE room_id=?)",
        (room_id,)
    )
    # Delete old bookings (Cancelled / Checked Out) for this room
    conn.execute("DELETE FROM bookings WHERE room_id=?", (room_id,))
    # Now safely delete the room
    conn.execute("DELETE FROM rooms WHERE id=?", (room_id,))
    conn.commit()
    conn.close()

def get_available_rooms(check_in, check_out, room_type=None):
    conn = get_connection()
    q = """SELECT * FROM rooms WHERE status='Available' AND id NOT IN (
        SELECT room_id FROM bookings
        WHERE status NOT IN ('Cancelled','Checked Out')
        AND check_in_date < ? AND check_out_date > ?
    )"""
    params = [check_out, check_in]
    if room_type and room_type != "All":
        q += " AND room_type=?"; params.append(room_type)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows

# ─────────────────────────── CUSTOMERS ───────────────────────

def get_all_customers(search=None):
    conn = get_connection()
    if search:
        rows = conn.execute("SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? ORDER BY name",
                            (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        rows = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    conn.close()
    return rows

def get_customer(customer_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
    conn.close()
    return row

def add_customer(data):
    conn = get_connection()
    conn.execute("""INSERT INTO customers (name,email,phone,id_type,id_number,address,nationality,date_of_birth)
                    VALUES (:name,:email,:phone,:id_type,:id_number,:address,:nationality,:date_of_birth)""", data)
    conn.commit()
    lid = _scalar(conn, "SELECT last_insert_rowid()")
    conn.close()
    return lid

def update_customer(customer_id, data):
    conn = get_connection()
    conn.execute("""UPDATE customers SET name=:name,email=:email,phone=:phone,id_type=:id_type,
        id_number=:id_number,address=:address,nationality=:nationality,date_of_birth=:date_of_birth
        WHERE id=:id""", {**data, 'id': customer_id})
    conn.commit()
    conn.close()

def get_customer_bookings(customer_id):
    conn = get_connection()
    rows = conn.execute("""SELECT b.*, r.room_number, r.room_type FROM bookings b
        JOIN rooms r ON b.room_id=r.id WHERE b.customer_id=? ORDER BY b.created_at DESC""",
        (customer_id,)).fetchall()
    conn.close()
    return rows

# ─────────────────────────── BOOKINGS ────────────────────────

def create_booking(data):
    conn = get_connection()
    ref = generate_booking_ref()
    ci = datetime.strptime(data['check_in_date'], "%Y-%m-%d").date()
    co = datetime.strptime(data['check_out_date'], "%Y-%m-%d").date()
    nights = max((co - ci).days, 1)
    room = conn.execute("SELECT price_per_night FROM rooms WHERE id=?", (data['room_id'],)).fetchone()
    room_charges = room['price_per_night'] * nights
    tax = round(room_charges * 0.12, 2)
    total = round(room_charges + tax, 2)

    conn.execute("""INSERT INTO bookings
        (booking_ref,customer_id,room_id,check_in_date,check_out_date,status,
         total_nights,room_charges,tax_amount,total_amount,payment_method,special_requests)
        VALUES (?,?,?,?,?,'Confirmed',?,?,?,?,?,?)""",
        (ref, data['customer_id'], data['room_id'], data['check_in_date'], data['check_out_date'],
         nights, room_charges, tax, total, data.get('payment_method','Cash'), data.get('special_requests','')))
    conn.execute("UPDATE rooms SET status='Booked' WHERE id=?", (data['room_id'],))
    conn.commit()
    lid = _scalar(conn, "SELECT last_insert_rowid()")
    conn.close()
    return lid, ref

def get_all_bookings(status_filter=None, date_from=None, date_to=None):
    conn = get_connection()
    q = """SELECT b.*, c.name as customer_name, c.phone, r.room_number, r.room_type
           FROM bookings b JOIN customers c ON b.customer_id=c.id JOIN rooms r ON b.room_id=r.id
           WHERE 1=1"""
    params = []
    if status_filter and status_filter != "All":
        q += " AND b.status=?"; params.append(status_filter)
    if date_from:
        q += " AND b.check_in_date >= ?"; params.append(date_from)
    if date_to:
        q += " AND b.check_in_date <= ?"; params.append(date_to)
    q += " ORDER BY b.created_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows

def get_booking(booking_id):
    conn = get_connection()
    row = conn.execute("""SELECT b.*, c.name as customer_name, c.phone, c.email,
        c.id_number, r.room_number, r.room_type, r.price_per_night, r.amenities
        FROM bookings b JOIN customers c ON b.customer_id=c.id JOIN rooms r ON b.room_id=r.id
        WHERE b.id=?""", (booking_id,)).fetchone()
    conn.close()
    return row

def update_booking(booking_id, data):
    conn = get_connection()
    ci = datetime.strptime(data['check_in_date'], "%Y-%m-%d").date()
    co = datetime.strptime(data['check_out_date'], "%Y-%m-%d").date()
    nights = max((co - ci).days, 1)
    room = conn.execute("SELECT price_per_night FROM rooms WHERE id=?", (data['room_id'],)).fetchone()
    room_charges = room['price_per_night'] * nights
    svc = _scalar(conn, "SELECT COALESCE(SUM(amount),0) FROM services WHERE booking_id=?", (booking_id,))
    disc = float(data.get('discount_amount', 0))
    subtotal = room_charges + svc - disc
    tax = round(max(subtotal, 0) * 0.12, 2)
    total = round(max(subtotal, 0) + tax, 2)
    conn.execute("""UPDATE bookings SET check_in_date=?,check_out_date=?,room_id=?,
        total_nights=?,room_charges=?,extra_charges=?,discount_amount=?,
        tax_amount=?,total_amount=?,payment_method=?,special_requests=?,
        coupon_code=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (data['check_in_date'],data['check_out_date'],data['room_id'],nights,
         room_charges,svc,disc,tax,total,data.get('payment_method','Cash'),
         data.get('special_requests',''),data.get('coupon_code',''),booking_id))
    conn.commit()
    conn.close()

def checkin_booking(booking_id):
    conn = get_connection()
    conn.execute("UPDATE bookings SET status='Checked In',updated_at=CURRENT_TIMESTAMP WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

def checkout_booking(booking_id):
    conn = get_connection()
    b = conn.execute("SELECT room_id FROM bookings WHERE id=?", (booking_id,)).fetchone()
    conn.execute("UPDATE bookings SET status='Checked Out',updated_at=CURRENT_TIMESTAMP WHERE id=?", (booking_id,))
    if b:
        conn.execute("UPDATE rooms SET status='Available' WHERE id=?", (b['room_id'],))
    conn.commit()
    conn.close()

def cancel_booking(booking_id):
    conn = get_connection()
    b = conn.execute("SELECT room_id FROM bookings WHERE id=?", (booking_id,)).fetchone()
    conn.execute("UPDATE bookings SET status='Cancelled',updated_at=CURRENT_TIMESTAMP WHERE id=?", (booking_id,))
    if b:
        conn.execute("UPDATE rooms SET status='Available' WHERE id=?", (b['room_id'],))
    conn.commit()
    conn.close()

def process_payment(booking_id, amount, method):
    conn = get_connection()
    b = conn.execute("SELECT paid_amount,total_amount FROM bookings WHERE id=?", (booking_id,)).fetchone()
    new_paid = b['paid_amount'] + amount
    status = 'Paid' if new_paid >= b['total_amount'] else 'Partial'
    conn.execute("""UPDATE bookings SET paid_amount=?,payment_status=?,payment_method=?,updated_at=CURRENT_TIMESTAMP
        WHERE id=?""", (new_paid, status, method, booking_id))
    conn.commit()
    conn.close()
    return status

def apply_coupon(booking_id, code):
    conn = get_connection()
    coupon = conn.execute("SELECT * FROM coupons WHERE code=? AND is_active=1", (code,)).fetchone()
    if not coupon:
        conn.close()
        return False, "Invalid coupon code"
    b = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if not b:
        conn.close()
        return False, "Booking not found"

    today = date.today().isoformat()
    if coupon['valid_from'] and today < coupon['valid_from']:
        conn.close()
        return False, "Coupon not yet valid"
    if coupon['valid_until'] and today > coupon['valid_until']:
        conn.close()
        return False, "Coupon expired"
    if coupon['used_count'] >= coupon['max_uses']:
        conn.close()
        return False, "Coupon usage limit reached"
    if b['room_charges'] < coupon['min_amount']:
        conn.close()
        return False, f"Minimum amount ₹{coupon['min_amount']:,.0f} required"

    if coupon['discount_type'] == 'percentage':
        disc = round(b['room_charges'] * coupon['discount_value'] / 100, 2)
    else:
        disc = coupon['discount_value']

    svc = _scalar(conn, "SELECT COALESCE(SUM(amount),0) FROM services WHERE booking_id=?", (booking_id,))
    subtotal = b['room_charges'] + svc - disc
    tax = round(max(subtotal, 0) * 0.12, 2)
    total = round(max(subtotal, 0) + tax, 2)

    conn.execute("""UPDATE bookings SET discount_amount=?,coupon_code=?,extra_charges=?,
        tax_amount=?,total_amount=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (disc, code, svc, tax, total, booking_id))
    conn.execute("UPDATE coupons SET used_count=used_count+1 WHERE id=?", (coupon['id'],))
    conn.commit()
    conn.close()
    return True, f"Coupon applied! Discount: ₹{disc:,.2f}"

def recalculate_booking(booking_id):
    conn = get_connection()
    b = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if not b:
        conn.close()
        return
    svc = _scalar(conn, "SELECT COALESCE(SUM(amount),0) FROM services WHERE booking_id=?", (booking_id,))
    subtotal = b['room_charges'] + svc - b['discount_amount']
    tax = round(max(subtotal, 0) * 0.12, 2)
    total = round(max(subtotal, 0) + tax, 2)
    conn.execute("UPDATE bookings SET extra_charges=?,tax_amount=?,total_amount=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                 (svc, tax, total, booking_id))
    conn.commit()
    conn.close()

# ─────────────────────────── SERVICES ────────────────────────

def add_service(booking_id, service_type, description, quantity, unit_price):
    conn = get_connection()
    amount = round(quantity * unit_price, 2)
    conn.execute("""INSERT INTO services (booking_id,service_type,description,quantity,unit_price,amount)
                    VALUES (?,?,?,?,?,?)""", (booking_id, service_type, description, quantity, unit_price, amount))
    conn.commit()
    conn.close()
    recalculate_booking(booking_id)

def get_booking_services(booking_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM services WHERE booking_id=? ORDER BY date DESC,id DESC", (booking_id,)).fetchall()
    conn.close()
    return rows

def delete_service(service_id, booking_id):
    conn = get_connection()
    conn.execute("DELETE FROM services WHERE id=?", (service_id,))
    conn.commit()
    conn.close()
    recalculate_booking(booking_id)

# ─────────────────────────── ANALYTICS ───────────────────────

def get_dashboard_stats():
    conn = get_connection()
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    stats = {}
    stats['total_rooms']          = _scalar(conn, "SELECT COUNT(*) FROM rooms")
    stats['available_rooms']      = _scalar(conn, "SELECT COUNT(*) FROM rooms WHERE status='Available'")
    stats['booked_rooms']         = _scalar(conn, "SELECT COUNT(*) FROM rooms WHERE status='Booked'")
    stats['maintenance_rooms']    = _scalar(conn, "SELECT COUNT(*) FROM rooms WHERE status='Maintenance'")
    stats['total_customers']      = _scalar(conn, "SELECT COUNT(*) FROM customers")
    stats['active_bookings']      = _scalar(conn, "SELECT COUNT(*) FROM bookings WHERE status IN ('Confirmed','Checked In')")
    stats['today_checkins']       = _scalar(conn, "SELECT COUNT(*) FROM bookings WHERE check_in_date=? AND status!='Cancelled'", (today,))
    stats['today_checkouts']      = _scalar(conn, "SELECT COUNT(*) FROM bookings WHERE check_out_date=? AND status!='Cancelled'", (today,))
    stats['today_revenue']        = _scalar(conn, "SELECT COALESCE(SUM(paid_amount),0) FROM bookings WHERE DATE(updated_at)=? AND payment_status IN ('Paid','Partial')", (today,)) or 0
    stats['monthly_revenue']      = _scalar(conn, "SELECT COALESCE(SUM(paid_amount),0) FROM bookings WHERE check_in_date>=? AND payment_status IN ('Paid','Partial')", (month_start,)) or 0

    recent = conn.execute("""SELECT b.booking_ref, c.name AS customer_name, r.room_number, b.check_in_date,
        b.check_out_date, b.status, b.total_amount, b.payment_status
        FROM bookings b JOIN customers c ON b.customer_id=c.id JOIN rooms r ON b.room_id=r.id
        ORDER BY b.created_at DESC LIMIT 8""").fetchall()
    stats['recent_bookings'] = recent
    conn.close()
    return stats

def get_revenue_chart_data(period='monthly', months=6):
    conn = get_connection()
    labels, values = [], []
    today = date.today()
    if period == 'monthly':
        for i in range(months-1, -1, -1):
            d = today.replace(day=1) - timedelta(days=i*30)
            d = d.replace(day=1)
            next_m = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
            rev = _scalar(conn, """SELECT COALESCE(SUM(paid_amount),0) FROM bookings
                WHERE check_in_date>=? AND check_in_date<? AND payment_status IN ('Paid','Partial')""",
                (d.isoformat(), next_m.isoformat())) or 0
            labels.append(d.strftime("%b %Y"))
            values.append(rev)
    else:
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            rev = _scalar(conn, """SELECT COALESCE(SUM(paid_amount),0) FROM bookings
                WHERE DATE(updated_at)=? AND payment_status IN ('Paid','Partial')""",
                (d.isoformat(),)) or 0
            labels.append(d.strftime("%d %b"))
            values.append(rev)
    conn.close()
    return labels, values

def get_room_type_stats():
    conn = get_connection()
    rows = conn.execute("""SELECT room_type, COUNT(*) as count FROM rooms GROUP BY room_type""").fetchall()
    conn.close()
    return [(r['room_type'], r['count']) for r in rows]

def get_booking_status_stats():
    conn = get_connection()
    rows = conn.execute("SELECT status, COUNT(*) as count FROM bookings GROUP BY status").fetchall()
    conn.close()
    return [(r['status'], r['count']) for r in rows]

def get_occupancy_data():
    conn = get_connection()
    total = _scalar(conn, "SELECT COUNT(*) FROM rooms")
    booked = _scalar(conn, "SELECT COUNT(*) FROM rooms WHERE status='Booked'")
    rate = round(booked / total * 100, 1) if total else 0
    conn.close()
    return rate, booked, total
