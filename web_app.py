from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from functools import wraps
import database as db
import os, tempfile, json
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "grand_azure_hotel_secret_2026"

# ─── Auth helpers ────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session['user']['role'] != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# ─── Form parsers ────────────────────────────────────────────

def _room_form():
    return {
        'room_number': request.form['room_number'],
        'room_type': request.form['room_type'],
        'price_per_night': float(request.form['price_per_night']),
        'status': request.form['status'],
        'floor': int(request.form.get('floor', 1)),
        'capacity': int(request.form.get('capacity', 2)),
        'amenities': request.form.get('amenities', ''),
        'description': request.form.get('description', ''),
    }

def _customer_form():
    return {
        'name': request.form['name'],
        'email': request.form.get('email', ''),
        'phone': request.form.get('phone', ''),
        'id_type': request.form.get('id_type', 'Passport'),
        'id_number': request.form.get('id_number', ''),
        'nationality': request.form.get('nationality', 'Indian'),
        'date_of_birth': request.form.get('date_of_birth', ''),
        'address': request.form.get('address', ''),
    }

def _booking_form():
    return {
        'customer_id': int(request.form['customer_id']),
        'room_id': int(request.form['room_id']),
        'check_in_date': request.form['check_in_date'],
        'check_out_date': request.form['check_out_date'],
        'payment_method': request.form.get('payment_method', 'Cash'),
        'special_requests': request.form.get('special_requests', ''),
    }

# ─── Auth ────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        user = db.authenticate_user(request.form['username'], request.form['password'])
        if user:
            session['user'] = user
            return redirect(url_for('dashboard'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Dashboard ───────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    stats = db.get_dashboard_stats()
    occ_rate, _, _ = db.get_occupancy_data()
    stats['occ_rate'] = occ_rate
    return render_template('dashboard.html', stats=stats)

# ─── Rooms ───────────────────────────────────────────────────

@app.route('/rooms')
@login_required
def rooms():
    status = request.args.get('status', 'All')
    rtype  = request.args.get('type', 'All')
    rooms_list = db.get_all_rooms(
        status_filter=status if status != 'All' else None,
        type_filter=rtype if rtype != 'All' else None
    )
    return render_template('rooms.html', rooms=rooms_list, status=status, rtype=rtype)

@app.route('/rooms/add', methods=['GET', 'POST'])
@admin_required
def room_add():
    if request.method == 'POST':
        ok, msg = db.add_room(_room_form())
        if ok:
            flash('Room added successfully!', 'success')
            return redirect(url_for('rooms'))
        flash(msg, 'danger')
    return render_template('room_form.html', room=None, title='Add Room')

@app.route('/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
@admin_required
def room_edit(room_id):
    room = db.get_room(room_id)
    if not room:
        flash('Room not found.', 'danger')
        return redirect(url_for('rooms'))
    if request.method == 'POST':
        db.update_room(room_id, _room_form())
        flash('Room updated!', 'success')
        return redirect(url_for('rooms'))
    return render_template('room_form.html', room=room, title='Edit Room')

@app.route('/rooms/<int:room_id>/delete', methods=['POST'])
@admin_required
def room_delete(room_id):
    try:
        db.delete_room(room_id)
        flash('Room deleted.', 'success')
    except Exception as e:
        flash(f'Cannot delete room: {e}', 'danger')
    return redirect(url_for('rooms'))

# ─── Customers ───────────────────────────────────────────────

@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '')
    custs = db.get_all_customers(search if search else None)
    return render_template('customers.html', customers=custs, search=search)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def customer_add():
    if request.method == 'POST':
        db.add_customer(_customer_form())
        flash('Customer added!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=None, title='Add Customer')

@app.route('/customers/<int:cid>/edit', methods=['GET', 'POST'])
@login_required
def customer_edit(cid):
    cust = db.get_customer(cid)
    if not cust:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customers'))
    if request.method == 'POST':
        db.update_customer(cid, _customer_form())
        flash('Customer updated!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=cust, title='Edit Customer')

@app.route('/customers/<int:cid>/history')
@login_required
def customer_history(cid):
    cust = db.get_customer(cid)
    bookings = db.get_customer_bookings(cid)
    total_spent = sum(b.get('paid_amount', 0) for b in bookings)
    return render_template('customer_history.html', customer=cust, bookings=bookings, total_spent=total_spent)

# ─── Bookings ────────────────────────────────────────────────

@app.route('/bookings')
@login_required
def bookings():
    status = request.args.get('status', 'All')
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    blist = db.get_all_bookings(
        status_filter=status if status != 'All' else None,
        date_from=date_from or None,
        date_to=date_to or None
    )
    return render_template('bookings.html', bookings=blist, status=status,
                           date_from=date_from, date_to=date_to)

@app.route('/bookings/new', methods=['GET', 'POST'])
@login_required
def booking_new():
    customers_list = db.get_all_customers()
    if request.method == 'POST':
        booking_id, ref = db.create_booking(_booking_form())
        flash(f'Booking confirmed! Reference: {ref}', 'success')
        return redirect(url_for('booking_detail', bid=booking_id))
    return render_template('booking_form.html', customers=customers_list, booking=None, title='New Booking')

@app.route('/bookings/<int:bid>')
@login_required
def booking_detail(bid):
    b = db.get_booking(bid)
    if not b:
        flash('Booking not found.', 'danger')
        return redirect(url_for('bookings'))
    services = db.get_booking_services(bid)
    return render_template('booking_detail.html', booking=b, services=services)

@app.route('/bookings/<int:bid>/edit', methods=['GET', 'POST'])
@login_required
def booking_edit(bid):
    b = db.get_booking(bid)
    customers_list = db.get_all_customers()
    if request.method == 'POST':
        data = {**_booking_form(),
                'discount_amount': b.get('discount_amount', 0),
                'coupon_code': b.get('coupon_code', '')}
        db.update_booking(bid, data)
        flash('Booking updated!', 'success')
        return redirect(url_for('booking_detail', bid=bid))
    return render_template('booking_form.html', customers=customers_list, booking=b, title='Edit Booking')

@app.route('/bookings/<int:bid>/checkin', methods=['POST'])
@login_required
def booking_checkin(bid):
    b = db.get_booking(bid)
    db.checkin_booking(bid)
    flash(f'Guest {b["customer_name"]} checked in to Room {b["room_number"]}!', 'success')
    return redirect(url_for('booking_detail', bid=bid))

@app.route('/bookings/<int:bid>/checkout', methods=['POST'])
@login_required
def booking_checkout(bid):
    b = db.get_booking(bid)
    db.checkout_booking(bid)
    flash(f'Guest {b["customer_name"]} checked out from Room {b["room_number"]}.', 'success')
    return redirect(url_for('booking_detail', bid=bid))

@app.route('/bookings/<int:bid>/cancel', methods=['POST'])
@login_required
def booking_cancel(bid):
    db.cancel_booking(bid)
    flash('Booking cancelled.', 'warning')
    return redirect(url_for('bookings'))

# ─── Billing ─────────────────────────────────────────────────

@app.route('/billing')
@login_required
def billing():
    blist = db.get_all_bookings()
    blist = [b for b in blist if b['status'] in ('Confirmed', 'Checked In', 'Checked Out')]
    return render_template('billing.html', bookings=blist)

@app.route('/billing/<int:bid>')
@login_required
def billing_detail(bid):
    b = db.get_booking(bid)
    services = db.get_booking_services(bid)
    return render_template('billing_detail.html', booking=b, services=services)

@app.route('/billing/<int:bid>/payment', methods=['POST'])
@login_required
def billing_payment(bid):
    amount = float(request.form['amount'])
    method = request.form.get('method', 'Cash')
    status = db.process_payment(bid, amount, method)
    flash(f'Payment of ₹{amount:,.2f} received. Status: {status}', 'success')
    return redirect(url_for('billing_detail', bid=bid))

@app.route('/billing/<int:bid>/coupon', methods=['POST'])
@login_required
def billing_coupon(bid):
    code = request.form.get('code', '').strip().upper()
    ok, msg = db.apply_coupon(bid, code)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('billing_detail', bid=bid))

@app.route('/billing/<int:bid>/pdf')
@login_required
def billing_pdf(bid):
    b = db.get_booking(bid)
    services = db.get_booking_services(bid)
    from utils.pdf_invoice import generate_invoice
    path = os.path.join(tempfile.gettempdir(), f"Invoice_{b['booking_ref']}.pdf")
    generate_invoice(b, services, path)
    return send_file(path, as_attachment=True, download_name=f"Invoice_{b['booking_ref']}.pdf")

# ─── Services ────────────────────────────────────────────────

@app.route('/services')
@login_required
def services():
    active = db.get_all_bookings()
    active = [b for b in active if b['status'] in ('Confirmed', 'Checked In')]
    bid = request.args.get('booking_id', type=int)
    svc_list = db.get_booking_services(bid) if bid else []
    selected = db.get_booking(bid) if bid else None
    return render_template('services.html', bookings=active, services=svc_list,
                           selected=selected, bid=bid)

@app.route('/services/add', methods=['POST'])
@login_required
def service_add():
    bid = int(request.form['booking_id'])
    db.add_service(
        bid,
        request.form['service_type'],
        request.form['description'],
        int(request.form.get('quantity', 1)),
        float(request.form['unit_price'])
    )
    flash('Service added to bill!', 'success')
    return redirect(url_for('services', booking_id=bid))

@app.route('/services/<int:sid>/delete', methods=['POST'])
@login_required
def service_delete(sid):
    bid = int(request.form['booking_id'])
    db.delete_service(sid, bid)
    flash('Service removed.', 'warning')
    return redirect(url_for('services', booking_id=bid))

# ─── Analytics ───────────────────────────────────────────────

@app.route('/analytics')
@admin_required
def analytics():
    stats = db.get_dashboard_stats()
    occ_rate, _, _ = db.get_occupancy_data()
    labels, rev_values = db.get_revenue_chart_data('monthly')
    room_types = db.get_room_type_stats()
    booking_statuses = db.get_booking_status_stats()
    return render_template('analytics.html', stats=stats, occ_rate=occ_rate,
        rev_labels=json.dumps(labels), rev_values=json.dumps(rev_values),
        room_types=json.dumps(room_types),
        booking_statuses=json.dumps(booking_statuses))

# ─── Users & Staff ───────────────────────────────────────────

@app.route('/users')
@admin_required
def users():
    users_list = db.get_all_users()
    return render_template('users.html', users=users_list)

@app.route('/users/add', methods=['GET', 'POST'])
@admin_required
def user_add():
    if request.method == 'POST':
        ok, msg = db.create_user(
            username=request.form['username'],
            password=request.form['password'],
            role='staff',
            full_name=request.form['full_name'],
            email=request.form.get('email', '')
        )
        if ok:
            flash(f'User {request.form["username"]} created successfully!', 'success')
            return redirect(url_for('users'))
        flash(msg, 'danger')
    return render_template('user_form.html')

@app.route('/users/<int:uid>/delete', methods=['POST'])
@admin_required
def user_delete(uid):
    ok, msg = db.delete_user(uid)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('users'))

# ─── AJAX APIs ───────────────────────────────────────────────

@app.route('/api/available-rooms')
@login_required
def api_available_rooms():
    ci = request.args.get('check_in')
    co = request.args.get('check_out')
    rtype = request.args.get('type')
    if not ci or not co:
        return jsonify([])
    rooms = db.get_available_rooms(ci, co, rtype if rtype and rtype != 'All' else None)
    return jsonify(rooms)

@app.route('/api/customers')
@login_required
def api_customers():
    search = request.args.get('q', '')
    custs = db.get_all_customers(search if search else None)
    return jsonify([{'id': c['id'], 'text': f"{c['name']} ({c.get('phone','')})"}
                    for c in custs])

# ─── Template filters ─────────────────────────────────────────

@app.template_filter('inr')
def inr_filter(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"

@app.template_filter('status_badge')
def status_badge(status):
    colors = {
        'Available': 'success', 'Booked': 'danger', 'Maintenance': 'warning',
        'Confirmed': 'primary', 'Checked In': 'success', 'Checked Out': 'secondary',
        'Cancelled': 'danger', 'Paid': 'success', 'Partial': 'warning',
        'Pending': 'warning', 'Clean': 'success', 'Dirty': 'danger',
        'Completed': 'success', 'In Progress': 'info',
    }
    color = colors.get(status, 'secondary')
    return f'<span class="badge bg-{color}">{status}</span>'

@app.context_processor
def inject_globals():
    return dict(current_user=session.get('user'), now=datetime.now())

# ─── Run ─────────────────────────────────────────────────────

if __name__ == '__main__':
    db.initialize_database()
    print("\n[*] Grand Azure Hotel - Web App")
    print("    Running at: http://127.0.0.1:5001")
    print("    Login: admin / admin123\n")
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    app.run(debug=debug_mode, port=port)
