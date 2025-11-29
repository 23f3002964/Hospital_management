
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from datetime import datetime, date, timedelta
from functools import wraps
from markupsafe import escape
import re

app = Flask(__name__)
app.secret_key = 'hospital-management-secret-key'

DATABASE = 'hospital_new.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'doctor', 'patient')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create departments table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')
    
    # Create doctors table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            specialization TEXT,
            phone TEXT,
            availability_days TEXT,
            availability_hours TEXT,
            availability_slots TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create patients table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create appointments table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'booked' CHECK(status IN ('booked', 'completed', 'cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
        )
    ''')
    
    # Create treatments table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            diagnosis TEXT,
            prescription TEXT,
            treatment_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE CASCADE
        )
    ''')
    
    # Only create the admin user if no users exist
    admin_exists = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    
    if admin_exists == 0:
        # Create default admin user only
        admin_password = hashlib.sha256('admin'.encode()).hexdigest()
        conn.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                     ('admin', 'admin@hospital.com', admin_password, 'admin'))
        conn.commit()
    
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_input(input_string):
    """Sanitize user input to prevent XSS attacks"""
    if input_string is None:
        return ''
    # Escape HTML characters
    sanitized = escape(str(input_string))
    # Remove any potentially dangerous characters
    sanitized = re.sub(r'[<>"]', '', str(sanitized))
    return sanitized

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    # Allow common phone formats
    pattern = r'^[+]?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """Validate password strength - lenient for demo purposes"""
    if not password:
        return False
    # At least 8 characters for stronger security, but allow simpler passwords for demo
    if len(password) < 4:  # Minimum 4 characters for demo purposes
        return False
    return True

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        if session['user_role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['user_role'] == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        elif session['user_role'] == 'patient':
            return redirect(url_for('patient_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form['username'])
        password = request.form['password']  # Don't sanitize passwords
        
        # Validate inputs
        if not username or len(username) < 3:
            flash('Invalid username. Username must be at least 3 characters long.', 'error')
            return render_template('login.html')
        
        if not password or len(password) < 4:
            flash('Invalid password. Password must be at least 4 characters long.', 'error')
            return render_template('login.html')
        
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password_hash = ?', 
                          (username, password_hash)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = sanitize_input(user['username'])
            session['user_role'] = sanitize_input(user['role'])
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user['role'] == 'patient':
                return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Sanitize inputs
        username = sanitize_input(request.form['username'])
        email = sanitize_input(request.form['email'])
        password = request.form['password']  # Don't sanitize passwords
        name = sanitize_input(request.form['name'])
        phone = sanitize_input(request.form.get('phone', ''))
        address = sanitize_input(request.form.get('address', ''))
        
        # Validate inputs
        errors = []
        
        if not username or len(username) < 3 or len(username) > 50:
            errors.append('Username must be between 3 and 50 characters long.')
        
        if not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        if not validate_password(password):
            errors.append('Password must be at least 4 characters long.')
        
        if not name or len(name) < 2 or len(name) > 100:
            errors.append('Name must be between 2 and 100 characters long.')
        
        if phone and not validate_phone(phone):
            errors.append('Please enter a valid phone number (10-15 digits).')
        
        if len(address) > 500:
            errors.append('Address must be less than 500 characters.')
        
        # If there are validation errors, display them
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        try:
            cursor = conn.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                                (username, email, password_hash, 'patient'))
            user_id = cursor.lastrowid
            
            conn.execute('INSERT INTO patients (user_id, name, phone, address) VALUES (?, ?, ?, ?)',
                        (user_id, name, phone, address))
            
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    conn = get_db_connection()
    
    total_doctors = conn.execute('SELECT COUNT(*) as count FROM doctors').fetchone()['count']
    total_patients = conn.execute('SELECT COUNT(*) as count FROM patients').fetchone()['count']
    total_appointments = conn.execute('SELECT COUNT(*) as count FROM appointments').fetchone()['count']
    
    recent_appointments = conn.execute('''
        SELECT a.*, p.id as patient_id, p.name as patient_name, d.name as doctor_name 
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.created_at DESC LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         recent_appointments=recent_appointments)

@app.route('/admin/doctors')
@login_required
@role_required(['admin'])
def manage_doctors():
    search_query = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    if search_query:
        doctors = conn.execute('''
            SELECT d.*, u.username, u.email 
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            WHERE d.name LIKE ? OR d.specialization LIKE ? OR u.username LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        doctors = conn.execute('''
            SELECT d.*, u.username, u.email 
            FROM doctors d
            JOIN users u ON d.user_id = u.id
        ''').fetchall()
    conn.close()
    
    return render_template('manage_doctors.html', doctors=doctors, search_query=search_query)

@app.route('/admin/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_doctor(doctor_id):
    conn = get_db_connection()
    
    # Get doctor details
    doctor = conn.execute('''
        SELECT d.*, u.username, u.email 
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ?
    ''', (doctor_id,)).fetchone()
    
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('manage_doctors'))
    
    if request.method == 'POST':
        # Sanitize inputs
        name = sanitize_input(request.form['name'])
        specialization = sanitize_input(request.form['specialization'])
        phone = sanitize_input(request.form['phone'])
        email = sanitize_input(request.form['email'])
        
        # Validate inputs
        errors = []
        
        if not name or len(name) < 2 or len(name) > 100:
            errors.append('Name must be between 2 and 100 characters long.')
        
        if not specialization or len(specialization) < 2 or len(specialization) > 100:
            errors.append('Specialization must be between 2 and 100 characters long.')
        
        if phone and not validate_phone(phone):
            errors.append('Please enter a valid phone number (10-15 digits).')
        
        if not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        # If there are validation errors, display them
        if errors:
            for error in errors:
                flash(error, 'error')
            conn.close()
            return render_template('edit_doctor.html', doctor=doctor)
        
        try:
            # Update doctor and user details
            conn.execute('UPDATE doctors SET name = ?, specialization = ?, phone = ? WHERE id = ?',
                        (name, specialization, phone, doctor_id))
            conn.execute('UPDATE users SET email = ? WHERE id = ?',
                        (email, doctor['user_id']))
            conn.commit()
            flash('Doctor updated successfully!', 'success')
            return redirect(url_for('manage_doctors'))
        except sqlite3.Error as e:
            flash('An error occurred while updating the doctor', 'error')
            conn.rollback()
        finally:
            conn.close()
    else:
        conn.close()
    
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/admin/doctors/delete/<int:doctor_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_doctor(doctor_id):
    conn = get_db_connection()
    
    try:
        # Get the user_id for this doctor
        doctor_user = conn.execute('SELECT user_id FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
        
        if not doctor_user:
            flash('Doctor not found', 'error')
            return redirect(url_for('manage_doctors'))
        
        # Delete the doctor record
        conn.execute('DELETE FROM doctors WHERE id = ?', (doctor_id,))
        
        # Delete the user record (this will also delete any related records due to CASCADE)
        conn.execute('DELETE FROM users WHERE id = ?', (doctor_user['user_id'],))
        
        conn.commit()
        flash('Doctor deleted successfully!', 'success')
    except sqlite3.Error as e:
        flash('An error occurred while deleting the doctor', 'error')
        conn.rollback()
    finally:
        conn.close()
    
    return redirect(url_for('manage_doctors'))

@app.route('/admin/patients')
@login_required
@role_required(['admin'])
def manage_patients():
    search_query = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    if search_query:
        patients = conn.execute('''
            SELECT p.*, u.username, u.email, u.created_at
            FROM patients p
            JOIN users u ON p.user_id = u.id
            WHERE p.name LIKE ? OR u.username LIKE ? OR u.email LIKE ? OR p.phone LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        patients = conn.execute('''
            SELECT p.*, u.username, u.email, u.created_at
            FROM patients p
            JOIN users u ON p.user_id = u.id
        ''').fetchall()
    conn.close()
    
    return render_template('manage_patients.html', patients=patients, search_query=search_query)

@app.route('/admin/doctors/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_doctor():
    if request.method == 'POST':
        # Sanitize inputs
        username = sanitize_input(request.form['username'])
        email = sanitize_input(request.form['email'])
        password = request.form['password']  # Don't sanitize passwords
        name = sanitize_input(request.form['name'])
        specialization = sanitize_input(request.form['specialization'])
        phone = sanitize_input(request.form['phone'])
        
        # Validate inputs
        errors = []
        
        if not username or len(username) < 3 or len(username) > 50:
            errors.append('Username must be between 3 and 50 characters long.')
        
        if not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        if not validate_password(password):
            errors.append('Password must be at least 4 characters long.')
        
        if not name or len(name) < 2 or len(name) > 100:
            errors.append('Name must be between 2 and 100 characters long.')
        
        if not specialization or len(specialization) < 2 or len(specialization) > 100:
            errors.append('Specialization must be between 2 and 100 characters long.')
        
        if phone and not validate_phone(phone):
            errors.append('Please enter a valid phone number (10-15 digits).')
        
        # If there are validation errors, display them
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('add_doctor.html')
        
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        try:
            cursor = conn.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                                (username, email, password_hash, 'doctor'))
            user_id = cursor.lastrowid
            
            conn.execute('INSERT INTO doctors (user_id, name, specialization, phone) VALUES (?, ?, ?, ?)',
                        (user_id, name, specialization, phone))
            
            conn.commit()
            conn.close()
            
            flash('Doctor added successfully!', 'success')
            return redirect(url_for('manage_doctors'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
            conn.close()
    
    return render_template('add_doctor.html')

@app.route('/admin/search')
@login_required
@role_required(['admin'])
def admin_search():
    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'doctors')  # default to doctors
    
    if not search_query:
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    results = []
    
    if search_type == 'doctors':
        results = conn.execute('''
            SELECT d.*, u.username, u.email 
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            WHERE d.name LIKE ? OR d.specialization LIKE ? OR u.username LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')).fetchall()
    elif search_type == 'patients':
        results = conn.execute('''
            SELECT p.*, u.username, u.email, u.created_at
            FROM patients p
            JOIN users u ON p.user_id = u.id
            WHERE p.name LIKE ? OR u.username LIKE ? OR u.email LIKE ? OR p.phone LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')).fetchall()
    
    conn.close()
    
    return render_template('admin_search.html', 
                         results=results, 
                         search_query=search_query, 
                         search_type=search_type)

# Doctor routes
@app.route('/doctor/dashboard')
@login_required
@role_required(['doctor'])
def doctor_dashboard():
    conn = get_db_connection()
    
    doctor = conn.execute('''
        SELECT d.* FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get appointments for the next 7 days
    today = date.today()
    week_end = today + timedelta(days=7)
    
    appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, p.phone as patient_phone
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = ? AND a.appointment_date BETWEEN ? AND ? AND a.status = 'booked'
        ORDER BY a.appointment_date, a.appointment_time
    ''', (doctor['id'], today, week_end)).fetchall()
    
    conn.close()
    
    return render_template('doctor_dashboard.html', 
                         doctor=doctor,
                         appointments=appointments)

@app.route('/doctor/appointment/<int:appointment_id>/complete', methods=['POST'])
@login_required
@role_required(['doctor'])
def complete_appointment(appointment_id):
    # Sanitize inputs
    diagnosis = sanitize_input(request.form['diagnosis'])
    prescription = sanitize_input(request.form['prescription'])
    treatment_notes = sanitize_input(request.form['treatment_notes'])
    
    # Validate inputs
    errors = []
    
    if not diagnosis or len(diagnosis) < 5 or len(diagnosis) > 500:
        errors.append('Diagnosis must be between 5 and 500 characters long.')
    
    if not prescription or len(prescription) < 5 or len(prescription) > 500:
        errors.append('Prescription must be between 5 and 500 characters long.')
    
    if len(treatment_notes) > 1000:
        errors.append('Treatment notes must be less than 1000 characters.')
    
    # If there are validation errors, display them
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('doctor_dashboard'))
    
    conn = get_db_connection()
    
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', ('completed', appointment_id))
    
    conn.execute('''INSERT INTO treatments (appointment_id, diagnosis, prescription, treatment_notes) 
                    VALUES (?, ?, ?, ?)''', (appointment_id, diagnosis, prescription, treatment_notes))
    
    conn.commit()
    conn.close()
    
    flash('Appointment completed successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@role_required(['doctor'])
def doctor_cancel_appointment(appointment_id):
    conn = get_db_connection()
    
    # Verify that this appointment belongs to this doctor
    doctor = conn.execute('''
        SELECT d.id FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        conn.close()
        return redirect(url_for('doctor_dashboard'))
    
    # Check if appointment belongs to this doctor
    appointment = conn.execute('''
        SELECT * FROM appointments 
        WHERE id = ? AND doctor_id = ? AND status = 'booked'
    ''', (appointment_id, doctor['id'])).fetchone()
    
    if not appointment:
        flash('Appointment not found or you do not have permission to cancel it', 'error')
        conn.close()
        return redirect(url_for('doctor_dashboard'))
    
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', ('cancelled', appointment_id))
    conn.commit()
    conn.close()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/availability', methods=['GET', 'POST'])
@login_required
@role_required(['doctor'])
def doctor_availability():
    conn = get_db_connection()
    
    # Get doctor details
    doctor = conn.execute('''
        SELECT d.* FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    if request.method == 'POST':
        availability_days = request.form.getlist('availability_days')
        availability_hours = sanitize_input(request.form['availability_hours'])
        
        # Sanitize each day in the list
        sanitized_days = [sanitize_input(day) for day in availability_days]
        
        # Validate inputs
        errors = []
        
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in sanitized_days:
            if day not in valid_days:
                errors.append('Invalid day selected.')
                break
        
        if len(availability_hours) > 200:
            errors.append('Availability hours description must be less than 200 characters.')
        
        # If there are validation errors, display them
        if errors:
            for error in errors:
                flash(error, 'error')
            conn.close()
            # Convert stored days string to list for the template
            available_days = doctor['availability_days'].split(',') if doctor['availability_days'] else []
            # Default days if none are set
            if not available_days or available_days == ['']:
                available_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            return render_template('doctor_availability.html', 
                                 doctor=doctor, 
                                 available_days=available_days,
                                 availability_hours=doctor['availability_hours'])
        
        # Convert list of days to comma-separated string
        days_str = ','.join(sanitized_days) if sanitized_days else ''
        
        try:
            # Update doctor availability
            conn.execute('UPDATE doctors SET availability_days = ?, availability_hours = ? WHERE id = ?',
                        (days_str, availability_hours, doctor['id']))
            conn.commit()
            flash('Availability updated successfully!', 'success')
            return redirect(url_for('doctor_availability'))
        except sqlite3.Error as e:
            flash('An error occurred while updating availability', 'error')
            conn.rollback()
        finally:
            conn.close()
    else:
        conn.close()
    
    # Convert stored days string to list for the template
    available_days = doctor['availability_days'].split(',') if doctor['availability_days'] else []
    
    # Default days if none are set
    if not available_days or available_days == ['']:
        available_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    return render_template('doctor_availability.html', 
                         doctor=doctor, 
                         available_days=available_days,
                         availability_hours=doctor['availability_hours'])


@app.route('/doctor/advanced-availability', methods=['GET', 'POST'])
@login_required
@role_required(['doctor'])
def advanced_doctor_availability():
    from datetime import datetime, timedelta, date
    
    conn = get_db_connection()
    
    # Get doctor details
    doctor = conn.execute('''
        SELECT d.* FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get today's date
    today = date.today()
    
    # Get existing availability slots for this doctor
    availability_slots = {}
    if doctor['availability_slots']:
        import json
        try:
            availability_slots = json.loads(doctor['availability_slots'])
        except:
            availability_slots = {}
    
    def is_slot_available(date_str, time_slot):
        """Check if a specific time slot is available"""
        if date_str in availability_slots and time_slot in availability_slots[date_str]:
            return availability_slots[date_str][time_slot] == 'available'
        return False
    
    # Generate date information for the next 7 days
    dates_info = []
    for i in range(7):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d')
        day_name = date_obj.strftime('%A')
        dates_info.append({
            'date': date_str,
            'day': day_name,
            'morning_status': 'available' if is_slot_available(date_str, 'morning') else 
                             ('booked' if date_str in availability_slots and 'morning' in availability_slots[date_str] and availability_slots[date_str]['morning'] == 'booked' else 'unavailable'),
            'afternoon_status': 'available' if is_slot_available(date_str, 'afternoon') else 
                               ('booked' if date_str in availability_slots and 'afternoon' in availability_slots[date_str] and availability_slots[date_str]['afternoon'] == 'booked' else 'unavailable'),
            'evening_status': 'available' if is_slot_available(date_str, 'evening') else 
                             ('booked' if date_str in availability_slots and 'evening' in availability_slots[date_str] and availability_slots[date_str]['evening'] == 'booked' else 'unavailable')
        })
    
    if request.method == 'POST':
        # Process form data to update availability slots
        new_availability_slots = {}
        
        for i in range(7):
            date_obj = today + timedelta(days=i)
            date_str = date_obj.strftime('%Y-%m-%d')
            new_availability_slots[date_str] = {}
            
            # Check which slots are selected
            morning_key = f'availability_{date_str}_morning'
            afternoon_key = f'availability_{date_str}_afternoon'
            evening_key = f'availability_{date_str}_evening'
            
            # Get existing appointments for this date to mark slots as booked
            appointments = conn.execute('''
                SELECT appointment_time FROM appointments 
                WHERE doctor_id = ? AND appointment_date = ? AND status = 'booked'
            ''', (doctor['id'], date_str)).fetchall()
            
            booked_slots = set()
            for appt in appointments:
                time_str = appt['appointment_time']
                if '09:00' <= time_str <= '12:00':
                    booked_slots.add('morning')
                elif '12:00' <= time_str <= '15:00':
                    booked_slots.add('afternoon')
                elif '15:00' <= time_str <= '18:00':
                    booked_slots.add('evening')
            
            # Set slot status
            if morning_key in request.form:
                new_availability_slots[date_str]['morning'] = 'available'
            elif 'morning' in booked_slots:
                new_availability_slots[date_str]['morning'] = 'booked'
            else:
                new_availability_slots[date_str]['morning'] = 'unavailable'
                
            if afternoon_key in request.form:
                new_availability_slots[date_str]['afternoon'] = 'available'
            elif 'afternoon' in booked_slots:
                new_availability_slots[date_str]['afternoon'] = 'booked'
            else:
                new_availability_slots[date_str]['afternoon'] = 'unavailable'
                
            if evening_key in request.form:
                new_availability_slots[date_str]['evening'] = 'available'
            elif 'evening' in booked_slots:
                new_availability_slots[date_str]['evening'] = 'booked'
            else:
                new_availability_slots[date_str]['evening'] = 'unavailable'
        
        # Convert to JSON and save
        import json
        slots_json = json.dumps(new_availability_slots)
        
        try:
            # Update doctor availability slots
            conn.execute('UPDATE doctors SET availability_slots = ? WHERE id = ?',
                        (slots_json, doctor['id']))
            conn.commit()
            flash('Advanced availability updated successfully!', 'success')
            return redirect(url_for('advanced_doctor_availability'))
        except sqlite3.Error as e:
            flash('An error occurred while updating availability', 'error')
            conn.rollback()
        finally:
            conn.close()
    else:
        conn.close()
    
    # Convert stored days string to list for the template
    available_days = doctor['availability_days'].split(',') if doctor['availability_days'] else []
    
    # Default days if none are set
    if not available_days or available_days == ['']:
        available_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    return render_template('advanced_doctor_availability.html', 
                         doctor=doctor, 
                         dates_info=dates_info,
                         available_days=available_days,
                         availability_hours=doctor['availability_hours'])

@app.route('/doctor/appointments')
@login_required
@role_required(['doctor'])
def doctor_appointments():
    conn = get_db_connection()
    
    # Get doctor details
    doctor = conn.execute('''
        SELECT d.* FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get all appointments for this doctor
    appointments = conn.execute('''
        SELECT a.*, p.name as patient_name, p.phone as patient_phone
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (doctor['id'],)).fetchall()
    
    conn.close()
    
    return render_template('doctor_appointments.html', 
                         doctor=doctor,
                         appointments=appointments)

@app.route('/doctor/patient/<int:patient_id>/history')
@login_required
@role_required(['doctor'])
def doctor_patient_history(patient_id):
    conn = get_db_connection()
    
    # Get doctor details
    doctor = conn.execute('''
        SELECT d.* FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get patient details
    patient = conn.execute('''
        SELECT p.*, u.email FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    ''', (patient_id,)).fetchone()
    
    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Check if this patient has appointments with this doctor
    appointment_check = conn.execute('''
        SELECT COUNT(*) as count FROM appointments
        WHERE patient_id = ? AND doctor_id = ?
    ''', (patient_id, doctor['id'])).fetchone()
    
    if appointment_check['count'] == 0:
        flash('This patient has no appointments with you', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Get patient's treatment history with this doctor
    treatments = conn.execute('''
        SELECT t.*, a.appointment_date, a.appointment_time
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        WHERE a.patient_id = ? AND a.doctor_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (patient_id, doctor['id'])).fetchall()
    
    conn.close()
    
    return render_template('doctor_patient_history.html', 
                         doctor=doctor,
                         patient=patient,
                         treatments=treatments)


@app.route('/doctor/appointment/<int:appointment_id>/update-history', methods=['GET', 'POST'])
@login_required
@role_required(['doctor'])
def update_patient_history(appointment_id):
    conn = get_db_connection()
    
    # Get doctor details
    doctor = conn.execute('''
        SELECT d.* FROM doctors d
        JOIN users u ON d.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get appointment details
    appointment = conn.execute('''
        SELECT a.*, p.name as patient_name, p.phone as patient_phone
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.id = ? AND a.doctor_id = ?
    ''', (appointment_id, doctor['id'])).fetchone()
    
    # Get treatment details if they exist
    treatment = conn.execute('''
        SELECT * FROM treatments WHERE appointment_id = ?
    ''', (appointment_id,)).fetchone()
    
    # Merge treatment data with appointment if it exists
    if treatment:
        appointment_dict = dict(appointment)
        appointment_dict.update(dict(treatment))
        appointment = appointment_dict
    
    if not appointment:
        flash('Appointment not found or you do not have permission to access it', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Get patient details
    patient = conn.execute('''
        SELECT * FROM patients WHERE id = ?
    ''', (appointment['patient_id'],)).fetchone()
    
    if request.method == 'POST':
        appointment_date = request.form['appointment_date']
        diagnosis = request.form['diagnosis']
        prescription = request.form['prescription']
        treatment_notes = request.form['treatment_notes']
        
        try:
            # Update appointment
            conn.execute('UPDATE appointments SET appointment_date = ? WHERE id = ?', 
                        (appointment_date, appointment_id))
            
            # Insert or update treatment
            conn.execute('''INSERT OR REPLACE INTO treatments 
                            (appointment_id, diagnosis, prescription, treatment_notes) 
                            VALUES (?, ?, ?, ?)''', 
                        (appointment_id, diagnosis, prescription, treatment_notes))
            
            conn.commit()
            flash('Patient history updated successfully!', 'success')
            return redirect(url_for('doctor_dashboard'))
        except sqlite3.Error as e:
            flash('An error occurred while updating patient history', 'error')
            conn.rollback()
        finally:
            conn.close()
    else:
        conn.close()
    
    return render_template('update_patient_history.html', 
                         doctor=doctor,
                         patient=patient,
                         appointment=appointment)

# Patient routes
@app.route('/patient/dashboard')
@login_required
@role_required(['patient'])
def patient_dashboard():
    conn = get_db_connection()
    
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    departments = conn.execute('SELECT * FROM departments').fetchall()
    doctors = conn.execute('SELECT * FROM doctors').fetchall()
    
    appointments = conn.execute('''
        SELECT a.*, d.name as doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (patient['id'],)).fetchall()
    
    # Get today's date for consistent date handling
    from datetime import date
    today_date = date.today().strftime('%Y-%m-%d')
    
    conn.close()
    
    return render_template('patient_dashboard.html', 
                         patient=patient,
                         departments=departments,
                         doctors=doctors,
                         appointments=appointments,
                         today_date=today_date)

@app.route('/patient/book_appointment', methods=['POST'])
@login_required
@role_required(['patient'])
def book_appointment():
    doctor_id = request.form['doctor_id']
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']
    
    conn = get_db_connection()
    
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    existing = conn.execute('''
        SELECT * FROM appointments 
        WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ? AND status = 'booked'
    ''', (doctor_id, appointment_date, appointment_time)).fetchone()
    
    if existing:
        flash('This time slot is already booked. Please choose another time.', 'error')
    else:
        conn.execute('''INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time) 
                        VALUES (?, ?, ?, ?)''', (patient['id'], doctor_id, appointment_date, appointment_time))
        conn.commit()
        flash('Appointment booked successfully!', 'success')
    
    conn.close()
    return redirect(url_for('patient_dashboard'))

@app.route('/patient/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@role_required(['patient'])
def cancel_appointment(appointment_id):
    conn = get_db_connection()
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', ('cancelled', appointment_id))
    conn.commit()
    conn.close()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('patient_dashboard'))

# Add the reschedule appointment route here
@app.route('/patient/appointment/<int:appointment_id>/reschedule', methods=['GET', 'POST'])
@login_required
@role_required(['patient'])
def reschedule_appointment(appointment_id):
    conn = get_db_connection()
    
    # Get patient details
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not patient:
        flash('Patient profile not found', 'error')
        conn.close()
        return redirect(url_for('logout'))
    
    # Get the appointment details
    appointment = conn.execute('''
        SELECT a.*, d.name as doctor_name, d.specialization, d.id as doctor_id
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.id = ? AND a.patient_id = ? AND a.status = 'booked'
    ''', (appointment_id, patient['id'])).fetchone()
    
    if not appointment:
        flash('Appointment not found or cannot be rescheduled', 'error')
        conn.close()
        return redirect(url_for('patient_dashboard'))
    
    doctors = conn.execute('SELECT * FROM doctors').fetchall()
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        
        # Verify doctor exists
        doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
        if not doctor:
            flash('Selected doctor not found', 'error')
            conn.close()
            return redirect(url_for('reschedule_appointment', appointment_id=appointment_id))
        
        # Check if the time slot is available
        existing = conn.execute('''
            SELECT * FROM appointments 
            WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ? AND status = 'booked' AND id != ?
        ''', (doctor_id, appointment_date, appointment_time, appointment_id)).fetchone()
        
        if existing:
            flash('This time slot is already booked. Please choose another time.', 'error')
        else:
            # Update the appointment
            conn.execute('''UPDATE appointments 
                            SET doctor_id = ?, appointment_date = ?, appointment_time = ? 
                            WHERE id = ?''', 
                        (doctor_id, appointment_date, appointment_time, appointment_id))
            conn.commit()
            flash('Appointment rescheduled successfully!', 'success')
            conn.close()
            return redirect(url_for('patient_dashboard'))
    
    # Get today's date for consistent date handling
    from datetime import date
    today_date = date.today().strftime('%Y-%m-%d')
    
    conn.close()
    
    return render_template('reschedule_appointment.html', 
                         patient=patient,
                         appointment=appointment,
                         doctors=doctors,
                         today_date=today_date)

@app.route('/patient/profile', methods=['GET', 'POST'])
@login_required
@role_required(['patient'])
def patient_profile():
    conn = get_db_connection()
    
    # Get patient details
    patient = conn.execute('''
        SELECT p.*, u.username, u.email 
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    if request.method == 'POST':
        # Sanitize inputs
        name = sanitize_input(request.form['name'])
        phone = sanitize_input(request.form['phone'])
        address = sanitize_input(request.form['address'])
        email = sanitize_input(request.form['email'])
        
        # Validate inputs
        errors = []
        
        if not name or len(name) < 2 or len(name) > 100:
            errors.append('Name must be between 2 and 100 characters long.')
        
        if phone and not validate_phone(phone):
            errors.append('Please enter a valid phone number (10-15 digits).')
        
        if not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        if len(address) > 500:
            errors.append('Address must be less than 500 characters.')
        
        # If there are validation errors, display them
        if errors:
            for error in errors:
                flash(error, 'error')
            conn.close()
            # Pass the form data back to the template
            patient_data = {
                'id': patient['id'],
                'user_id': patient['user_id'],
                'username': patient['username'],
                'email': email,
                'name': name,
                'phone': phone,
                'address': address
            }
            return render_template('patient_profile.html', patient=patient_data)
        
        try:
            # Update patient and user details
            conn.execute('UPDATE patients SET name = ?, phone = ?, address = ? WHERE id = ?',
                        (name, phone, address, patient['id']))
            conn.execute('UPDATE users SET email = ? WHERE id = ?',
                        (email, session['user_id']))
            conn.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('patient_profile'))
        except sqlite3.Error as e:
            flash('An error occurred while updating the profile', 'error')
            conn.rollback()
        finally:
            conn.close()
    else:
        conn.close()
    
    return render_template('patient_profile.html', patient=patient)

@app.route('/patient/history')
@login_required
@role_required(['patient'])
def patient_history():
    conn = get_db_connection()
    
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    treatments = conn.execute('''
        SELECT t.*, a.appointment_date, a.appointment_time, d.name as doctor_name, d.specialization
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (patient['id'],)).fetchall()
    
    # Add serial numbers to treatments
    treatments_with_serial = []
    for i, treatment in enumerate(treatments, 1):
        treatment_dict = dict(treatment)
        treatment_dict['serial_no'] = i
        treatments_with_serial.append(treatment_dict)
    
    conn.close()
    
    return render_template('patient_history.html', treatments=treatments_with_serial)


@app.route('/patient/departments')
@login_required
@role_required(['patient'])
def patient_departments():
    conn = get_db_connection()
    
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    departments = conn.execute('SELECT * FROM departments').fetchall()
    conn.close()
    
    return render_template('departments.html', 
                         patient=patient,
                         departments=departments)


@app.route('/patient/department/<int:department_id>')
@login_required
@role_required(['patient'])
def department_details(department_id):
    conn = get_db_connection()
    
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get department details
    department = conn.execute('SELECT * FROM departments WHERE id = ?', (department_id,)).fetchone()
    
    if not department:
        flash('Department not found', 'error')
        return redirect(url_for('patient_departments'))
    
    # Get doctors in this department
    doctors = conn.execute('SELECT * FROM doctors WHERE specialization = ?', (department['name'],)).fetchall()
    
    conn.close()
    
    return render_template('department_details.html', 
                         patient=patient,
                         department=department,
                         doctors=doctors)


@app.route('/patient/doctor/<int:doctor_id>/availability')
@login_required
@role_required(['patient'])
def doctor_availability_patient_view(doctor_id):
    conn = get_db_connection()
    
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get doctor details
    doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
    
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('patient_departments'))
    
    # Get doctor's availability slots
    availability_slots = {}
    if doctor['availability_slots']:
        import json
        try:
            availability_slots = json.loads(doctor['availability_slots'])
        except:
            availability_slots = {}
    
    def is_slot_available(date_str, time_slot):
        """Check if a specific time slot is available"""
        if date_str in availability_slots and time_slot in availability_slots[date_str]:
            return availability_slots[date_str][time_slot] == 'available'
        return False
    
    # Generate date information for the next 7 days
    from datetime import date, timedelta
    today = date.today()
    dates_info = []
    for i in range(7):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d')
        day_name = date_obj.strftime('%A')
        dates_info.append({
            'date': date_str,
            'day': day_name,
            'morning_status': 'available' if is_slot_available(date_str, 'morning') else 
                             ('booked' if date_str in availability_slots and 'morning' in availability_slots[date_str] and availability_slots[date_str]['morning'] == 'booked' else 'unavailable'),
            'afternoon_status': 'available' if is_slot_available(date_str, 'afternoon') else 
                               ('booked' if date_str in availability_slots and 'afternoon' in availability_slots[date_str] and availability_slots[date_str]['afternoon'] == 'booked' else 'unavailable'),
            'evening_status': 'available' if is_slot_available(date_str, 'evening') else 
                             ('booked' if date_str in availability_slots and 'evening' in availability_slots[date_str] and availability_slots[date_str]['evening'] == 'booked' else 'unavailable')
        })
    
    conn.close()
    
    return render_template('doctor_availability_patient.html', 
                         patient=patient,
                         doctor=doctor,
                         dates_info=dates_info)


@app.route('/patient/doctor/<int:doctor_id>/profile')
@login_required
@role_required(['patient'])
def doctor_profile_patient_view(doctor_id):
    conn = get_db_connection()
    
    patient = conn.execute('''
        SELECT p.* FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
    ''', (session['user_id'],)).fetchone()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get doctor details
    doctor = conn.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
    
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('patient_departments'))
    
    conn.close()
    
    return render_template('doctor_profile_patient.html', 
                         patient=patient,
                         doctor=doctor)


@app.route('/admin/patient/<int:patient_id>/history')
@login_required
@role_required(['admin'])
def admin_patient_history(patient_id):
    conn = get_db_connection()
    
    # Get patient details
    patient = conn.execute('''
        SELECT p.*, u.username, u.email, u.created_at
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    ''', (patient_id,)).fetchone()
    
    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Get patient's complete treatment history
    treatments = conn.execute('''
        SELECT t.*, a.appointment_date, a.appointment_time, d.name as doctor_name, d.specialization
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (patient_id,)).fetchall()
    
    # Add serial numbers to treatments
    treatments_with_serial = []
    for i, treatment in enumerate(treatments, 1):
        treatment_dict = dict(treatment)
        treatment_dict['serial_no'] = i
        treatments_with_serial.append(treatment_dict)
    
    conn.close()
    
    return render_template('admin_patient_history.html', 
                         patient=patient,
                         treatments=treatments_with_serial)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
