from app import app, db, User, Doctor, Patient, Department, Appointment, Treatment
from flask import render_template, request, redirect, url_for, session, flash
from datetime import datetime, date, timedelta
from functools import wraps
import hashlib
from markupsafe import escape
import re

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
    """Redirect users to their respective dashboards based on their role"""
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
    """Handle user login with validation and authentication"""
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
        
        user = User.query.filter_by(username=username, password_hash=password_hash).first()
        
        if user:
            session['user_id'] = user.id
            session['username'] = sanitize_input(user.username)
            session['user_role'] = sanitize_input(user.role)
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user.role == 'patient':
                return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle patient registration with validation"""
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
        
        user = User(username=username, email=email, password_hash=password_hash, role='patient')
        db.session.add(user)
        db.session.commit()
        
        patient = Patient(user_id=user.id, name=name, phone=phone, address=address)
        db.session.add(patient)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Clear user session and redirect to login page"""
    session.clear()
    return redirect(url_for('login'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    """Display admin dashboard with system statistics"""
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    
    # Join Appointment with Patient and Doctor to get names
    # Show booked, completed, and cancelled appointments in recent list
    recent_appointments = db.session.query(
        Appointment,
        Patient.name.label('patient_name'),
        Doctor.name.label('doctor_name')
    ).join(Patient, Appointment.patient_id == Patient.id)\
     .join(Doctor, Appointment.doctor_id == Doctor.id)\
     .filter(Appointment.status.in_(['booked', 'completed', 'cancelled']))\
     .order_by(Appointment.created_at.desc())\
     .limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         recent_appointments=recent_appointments)

@app.route('/admin/dashboard/recent-appointments')
@login_required
@role_required(['admin'])
def admin_dashboard_recent_appointments():
    """Return recent appointments data in JSON format for AJAX updates"""
    # Join Appointment with Patient and Doctor to get names
    # Show booked, completed, and cancelled appointments
    recent_appointments = db.session.query(
        Appointment,
        Patient.name.label('patient_name'),
        Doctor.name.label('doctor_name')
    ).join(Patient, Appointment.patient_id == Patient.id)\
     .join(Doctor, Appointment.doctor_id == Doctor.id)\
     .filter(Appointment.status.in_(['booked', 'completed', 'cancelled']))\
     .order_by(Appointment.created_at.desc())\
     .limit(10).all()
    
    # Convert to JSON-serializable format
    appointments_data = []
    for appointment_tuple in recent_appointments:
        appointment = appointment_tuple[0]
        patient_name = appointment_tuple[1]
        doctor_name = appointment_tuple[2]
        
        appointments_data.append({
            'id': appointment.id,
            'patient_id': appointment.patient_id,
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'appointment_date': appointment.appointment_date.isoformat() if hasattr(appointment.appointment_date, 'isoformat') else str(appointment.appointment_date),
            'status': appointment.status
        })
    
    return {'appointments': appointments_data}

@app.route('/admin/doctors')
@login_required
@role_required(['admin'])
def manage_doctors():
    """Display list of doctors with search functionality"""
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        doctors = Doctor.query.join(User).filter(
            (Doctor.name.like(f'%{search_query}%')) |
            (Doctor.specialization.like(f'%{search_query}%')) |
            (User.username.like(f'%{search_query}%'))
        ).all()
    else:
        doctors = Doctor.query.join(User).all()
    
    return render_template('manage_doctors.html', doctors=doctors, search_query=search_query)

@app.route('/admin/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_doctor(doctor_id):
    """Edit doctor details with validation"""
    doctor = Doctor.query.join(User).filter(Doctor.id == doctor_id).first()
    
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('manage_doctors'))
    
    # Get distinct specializations from existing doctors
    specializations = db.session.query(Doctor.specialization).distinct().filter(Doctor.specialization.isnot(None)).all()
    specializations = [spec[0] for spec in specializations]
    
    if request.method == 'POST':
        # Sanitize inputs
        name = sanitize_input(request.form['name'])
        specialization = sanitize_input(request.form['specialization'])
        # If 'Other' is selected, use the other_specialization field
        if specialization == 'Other':
            specialization = sanitize_input(request.form.get('other_specialization', ''))
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
            return render_template('edit_doctor.html', doctor=doctor, specializations=specializations)
        
        doctor.name = name
        doctor.specialization = specialization
        doctor.phone = phone
        doctor.user.email = email
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('manage_doctors'))
    
    # Handle GET request - display the form
    return render_template('edit_doctor.html', doctor=doctor, specializations=specializations)

@app.route('/admin/doctors/delete/<int:doctor_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_doctor(doctor_id):
    """Delete a doctor from the system"""
    doctor = Doctor.query.filter(Doctor.id == doctor_id).first()
    
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('manage_doctors'))
    
    db.session.delete(doctor)
    db.session.commit()
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('manage_doctors'))

@app.route('/admin/patients')
@login_required
@role_required(['admin'])
def manage_patients():
    """Display list of patients with search functionality"""
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        patients = Patient.query.join(User).filter(
            (Patient.name.like(f'%{search_query}%')) |
            (User.username.like(f'%{search_query}%')) |
            (User.email.like(f'%{search_query}%')) |
            (Patient.phone.like(f'%{search_query}%'))
        ).all()
    else:
        patients = Patient.query.join(User).all()
    
    return render_template('manage_patients.html', patients=patients, search_query=search_query)

@app.route('/admin/doctors/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_doctor():
    """Add a new doctor to the system"""
    # Get distinct specializations from existing doctors
    specializations = db.session.query(Doctor.specialization).distinct().filter(Doctor.specialization.isnot(None)).all()
    specializations = [spec[0] for spec in specializations]
    
    if request.method == 'POST':
        # Sanitize inputs
        username = sanitize_input(request.form['username'])
        email = sanitize_input(request.form['email'])
        password = request.form['password']  # Don't sanitize passwords
        name = sanitize_input(request.form['name'])
        specialization = sanitize_input(request.form['specialization'])
        # If 'Other' is selected, use the other_specialization field
        if specialization == 'Other':
            specialization = sanitize_input(request.form.get('other_specialization', ''))
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
            return render_template('add_doctor.html', specializations=specializations)
        
        password_hash = hash_password(password)
        
        user = User(username=username, email=email, password_hash=password_hash, role='doctor')
        db.session.add(user)
        db.session.commit()
        
        doctor = Doctor(user_id=user.id, name=name, specialization=specialization, phone=phone)
        db.session.add(doctor)
        db.session.commit()
        
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('manage_doctors'))
    
    return render_template('add_doctor.html', specializations=specializations)

@app.route('/admin/appointments')
@login_required
@role_required(['admin'])
def admin_appointments():
    """Display all appointments for admin with patient and doctor information"""
    # Get all appointments with patient and doctor information
    appointments = db.session.query(
        Appointment,
        Patient.name.label('patient_name'),
        Patient.phone.label('patient_phone'),
        Doctor.name.label('doctor_name'),
        Doctor.specialization.label('doctor_specialization')
    ).join(Patient, Appointment.patient_id == Patient.id)\
     .join(Doctor, Appointment.doctor_id == Doctor.id)\
     .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    return render_template('admin_appointments.html', 
                         appointments=appointments)

@app.route('/admin/search')
@login_required
@role_required(['admin'])
def admin_search():
    """Search for doctors or patients based on query parameters"""
    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'doctors')  # default to doctors
    
    if not search_query:
        return redirect(url_for('admin_dashboard'))
    
    results = []
    
    if search_type == 'doctors':
        results = Doctor.query.join(User).filter(
            (Doctor.name.like(f'%{search_query}%')) |
            (Doctor.specialization.like(f'%{search_query}%')) |
            (User.username.like(f'%{search_query}%'))
        ).all()
    elif search_type == 'patients':
        results = Patient.query.join(User).filter(
            (Patient.name.like(f'%{search_query}%')) |
            (User.username.like(f'%{search_query}%')) |
            (User.email.like(f'%{search_query}%')) |
            (Patient.phone.like(f'%{search_query}%'))
        ).all()
    
    return render_template('admin_search.html', 
                         results=results, 
                         search_query=search_query, 
                         search_type=search_type)

# Doctor routes
@app.route('/doctor/dashboard')
@login_required
@role_required(['doctor'])
def doctor_dashboard():
    """Display doctor dashboard with upcoming appointments"""
    doctor = Doctor.query.join(User).filter(User.id == session['user_id']).first()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get appointments for the next 7 days with patient information
    today = date.today()
    week_end = today + timedelta(days=7)
    
    appointments = db.session.query(
        Appointment,
        Patient.name.label('patient_name'),
        Patient.phone.label('patient_phone')
    ).join(Patient, Appointment.patient_id == Patient.id)\
     .filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date.between(today, week_end),
        Appointment.status == 'booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    return render_template('doctor_dashboard.html', 
                         doctor=doctor,
                         appointments=appointments)

@app.route('/doctor/appointment/<int:appointment_id>/complete', methods=['POST'])
@login_required
@role_required(['doctor'])
def complete_appointment(appointment_id):
    """Mark an appointment as completed and add treatment details"""
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
    
    appointment = Appointment.query.filter(Appointment.id == appointment_id).first()
    appointment.status = 'completed'
    db.session.flush()  # Flush changes to database
    
    treatment = Treatment(appointment_id=appointment_id, diagnosis=diagnosis, prescription=prescription, treatment_notes=treatment_notes)
    db.session.add(treatment)
    db.session.commit()  # Commit both changes together
    
    flash('Appointment completed successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@role_required(['doctor'])
def doctor_cancel_appointment(appointment_id):
    """Cancel a doctor's appointment"""
    doctor = Doctor.query.join(User).filter(User.id == session['user_id']).first()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    appointment = Appointment.query.filter(
        Appointment.id == appointment_id,
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'booked'
    ).first()
    
    if not appointment:
        flash('Appointment not found or you do not have permission to cancel it', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/availability', methods=['GET', 'POST'])
@login_required
@role_required(['doctor'])
def doctor_availability():
    """Manage doctor's weekly availability settings"""
    doctor = Doctor.query.join(User).filter(User.id == session['user_id']).first()
    
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
            # Convert stored days string to list for the template
            available_days = doctor.availability_days.split(',') if doctor.availability_days else []
            # Default days if none are set
            if not available_days or available_days == ['']:
                available_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            return render_template('doctor_availability.html', 
                                 doctor=doctor, 
                                 available_days=available_days,
                                 availability_hours=doctor.availability_hours)
        
        # Convert list of days to comma-separated string
        days_str = ','.join(sanitized_days) if sanitized_days else ''
        
        doctor.availability_days = days_str
        doctor.availability_hours = availability_hours
        db.session.commit()
        flash('Availability updated successfully!', 'success')
        return redirect(url_for('doctor_availability'))
    else:
        # Convert stored days string to list for the template
        available_days = doctor.availability_days.split(',') if doctor.availability_days else []
        
        # Default days if none are set
        if not available_days or available_days == ['']:
            available_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        return render_template('doctor_availability.html', 
                             doctor=doctor, 
                             available_days=available_days,
                             availability_hours=doctor.availability_hours)

@app.route('/doctor/advanced-availability', methods=['GET', 'POST'])
@login_required
@role_required(['doctor'])
def advanced_doctor_availability():
    """Manage doctor's advanced availability settings with time slots"""
    doctor = Doctor.query.join(User).filter(User.id == session['user_id']).first()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get today's date
    today = date.today()
    
    # Get existing availability slots for this doctor
    availability_slots = {}
    if doctor.availability_slots:
        import json
        try:
            availability_slots = json.loads(doctor.availability_slots)
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
            appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == date_str,
                Appointment.status == 'booked'
            ).all()
            
            booked_slots = set()
            for appt in appointments:
                time_str = appt.appointment_time
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
        
        doctor.availability_slots = slots_json
        db.session.commit()
        flash('Advanced availability updated successfully!', 'success')
        return redirect(url_for('advanced_doctor_availability'))
    else:
        # Convert stored days string to list for the template
        available_days = doctor.availability_days.split(',') if doctor.availability_days else []
        
        # Default days if none are set
        if not available_days or available_days == ['']:
            available_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        return render_template('advanced_doctor_availability.html', 
                             doctor=doctor, 
                             dates_info=dates_info,
                             available_days=available_days,
                             availability_hours=doctor.availability_hours)

@app.route('/doctor/appointments')
@login_required
@role_required(['doctor'])
def doctor_appointments():
    """Display all appointments for the logged-in doctor"""
    doctor = Doctor.query.join(User).filter(User.id == session['user_id']).first()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get all appointments for this doctor with patient information
    appointments = db.session.query(
        Appointment,
        Patient.name.label('patient_name'),
        Patient.phone.label('patient_phone')
    ).join(Patient, Appointment.patient_id == Patient.id)\
     .filter(Appointment.doctor_id == doctor.id)\
     .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    return render_template('doctor_appointments.html', 
                         doctor=doctor,
                         appointments=appointments)

@app.route('/doctor/patient/<int:patient_id>/history')
@login_required
@role_required(['doctor'])
def doctor_patient_history(patient_id):
    """Display a patient's medical history for a doctor"""
    doctor = Doctor.query.join(User).filter(User.id == session['user_id']).first()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get patient details
    patient = Patient.query.join(User).filter(Patient.id == patient_id).first()
    
    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Check if this patient has appointments with this doctor
    appointment_check = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == doctor.id
    ).count()
    
    if appointment_check == 0:
        flash('This patient has no appointments with you', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Get patient's treatment history with this doctor
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == doctor.id
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    return render_template('doctor_patient_history.html', 
                         doctor=doctor,
                         patient=patient,
                         treatments=treatments)

@app.route('/doctor/appointment/<int:appointment_id>/update-history', methods=['GET', 'POST'])
@login_required
@role_required(['doctor'])
def update_patient_history(appointment_id):
    """Update a patient's medical history for a specific appointment"""
    doctor = Doctor.query.join(User).filter(User.id == session['user_id']).first()
    
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get appointment details
    appointment = Appointment.query.join(Patient).filter(
        Appointment.id == appointment_id,
        Appointment.doctor_id == doctor.id
    ).first()
    
    # Get treatment details if they exist
    treatment = Treatment.query.filter(Treatment.appointment_id == appointment_id).first()
    
    if not appointment:
        flash('Appointment not found or you do not have permission to access it', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Get patient details
    patient = Patient.query.filter(Patient.id == appointment.patient_id).first()
    
    if request.method == 'POST':
        appointment_date = request.form['appointment_date']
        diagnosis = request.form['diagnosis']
        prescription = request.form['prescription']
        treatment_notes = request.form['treatment_notes']
        
        # Convert string date to Python date object
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        
        # Update appointment
        appointment.appointment_date = appointment_date_obj
        db.session.commit()
        
        if treatment:
            treatment.diagnosis = diagnosis
            treatment.prescription = prescription
            treatment.treatment_notes = treatment_notes
            db.session.commit()
        else:
            treatment = Treatment(appointment_id=appointment_id, diagnosis=diagnosis, prescription=prescription, treatment_notes=treatment_notes)
            db.session.add(treatment)
            db.session.commit()
        
        flash('Patient history updated successfully!', 'success')
        return redirect(url_for('doctor_dashboard'))
    
    # Prepare data for the template
    # Combine appointment and treatment data for display
    appointment_data = {
        'id': appointment.id,
        'patient_id': appointment.patient_id,
        'doctor_id': appointment.doctor_id,
        'appointment_date': appointment.appointment_date,
        'appointment_time': appointment.appointment_time,
        'status': appointment.status,
        'created_at': appointment.created_at,
        'diagnosis': treatment.diagnosis if treatment else '',
        'prescription': treatment.prescription if treatment else '',
        'treatment_notes': treatment.treatment_notes if treatment else ''
    }
    
    return render_template('update_patient_history.html', 
                         doctor=doctor,
                         patient=patient,
                         appointment=appointment_data)

# Patient routes
@app.route('/patient/dashboard')
@login_required
@role_required(['patient'])
def patient_dashboard():
    """Display patient dashboard with appointment booking options"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    departments = Department.query.all()
    doctors = Doctor.query.all()
    
    # Get appointments with doctor information
    appointments = db.session.query(
        Appointment,
        Doctor.name.label('doctor_name'),
        Doctor.specialization.label('specialization')
    ).join(Doctor, Appointment.doctor_id == Doctor.id)\
     .filter(Appointment.patient_id == patient.id)\
     .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    # Get today's date for consistent date handling
    today_date = date.today().strftime('%Y-%m-%d')
    
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
    """Book a new appointment for the patient"""
    doctor_id = request.form['doctor_id']
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']
    
    # Convert string date to Python date object
    appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    existing = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == appointment_date_obj,
        Appointment.appointment_time == appointment_time,
        Appointment.status == 'booked'
    ).first()
    
    if existing:
        flash('This time slot is already booked. Please choose another time.', 'error')
    else:
        appointment = Appointment(patient_id=patient.id, doctor_id=doctor_id, appointment_date=appointment_date_obj, appointment_time=appointment_time)
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully!', 'success')
    
    return redirect(url_for('patient_dashboard'))

@app.route('/patient/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@role_required(['patient'])
def cancel_appointment(appointment_id):
    """Cancel a patient's appointment"""
    appointment = Appointment.query.filter(Appointment.id == appointment_id).first()
    appointment.status = 'cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully!', 'success')
    return redirect(url_for('patient_dashboard'))

@app.route('/patient/appointment/<int:appointment_id>/reschedule', methods=['GET', 'POST'])
@login_required
@role_required(['patient'])
def reschedule_appointment(appointment_id):
    """Reschedule an existing appointment"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get the appointment details
    appointment = Appointment.query.join(Doctor).filter(
        Appointment.id == appointment_id,
        Appointment.patient_id == patient.id,
        Appointment.status == 'booked'
    ).first()
    
    if not appointment:
        flash('Appointment not found or cannot be rescheduled', 'error')
        return redirect(url_for('patient_dashboard'))
    
    doctors = Doctor.query.all()
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        
        # Verify doctor exists
        doctor = Doctor.query.filter(Doctor.id == doctor_id).first()
        if not doctor:
            flash('Selected doctor not found', 'error')
            return redirect(url_for('reschedule_appointment', appointment_id=appointment_id))
        
        # Check if the time slot is available
        # Convert string date to Python date object for comparison
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        
        existing = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date_obj,
            Appointment.appointment_time == appointment_time,
            Appointment.status == 'booked',
            Appointment.id != appointment_id
        ).first()
        
        if existing:
            flash('This time slot is already booked. Please choose another time.', 'error')
        else:
            appointment.doctor_id = doctor_id
            # Convert string date to Python date object
            appointment.appointment_date = appointment_date_obj
            appointment.appointment_time = appointment_time
            db.session.commit()
            flash('Appointment rescheduled successfully!', 'success')
            return redirect(url_for('patient_dashboard'))
    
    # Get today's date for consistent date handling
    today_date = date.today().strftime('%Y-%m-%d')
    
    return render_template('reschedule_appointment.html', 
                         patient=patient,
                         appointment=appointment,
                         doctors=doctors,
                         today_date=today_date)

@app.route('/patient/profile', methods=['GET', 'POST'])
@login_required
@role_required(['patient'])
def patient_profile():
    """View and update patient profile information"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
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
            # Pass the form data back to the template
            patient_data = {
                'id': patient.id,
                'user_id': patient.user_id,
                'username': patient.user.username,
                'email': email,
                'name': name,
                'phone': phone,
                'address': address
            }
            return render_template('patient_profile.html', patient=patient_data)
        
        patient.name = name
        patient.phone = phone
        patient.address = address
        patient.user.email = email
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient_profile'))
    
    return render_template('patient_profile.html', patient=patient)

@app.route('/patient/history')
@login_required
@role_required(['patient'])
def patient_history():
    """Display patient's complete medical history"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    treatments = Treatment.query.join(Appointment).join(Doctor).filter(
        Appointment.patient_id == patient.id
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    # Add serial numbers to treatments
    treatments_with_serial = []
    for i, treatment in enumerate(treatments, 1):
        # Create a dictionary with treatment data
        treatment_dict = {
            'id': treatment.id,
            'appointment_id': treatment.appointment_id,
            'diagnosis': treatment.diagnosis,
            'prescription': treatment.prescription,
            'treatment_notes': treatment.treatment_notes,
            'created_at': treatment.created_at,
            'serial_no': i
        }
        treatments_with_serial.append(treatment_dict)
    
    return render_template('patient_history.html', treatments=treatments_with_serial)

@app.route('/patient/departments')
@login_required
@role_required(['patient'])
def patient_departments():
    """Display list of medical departments"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    departments = Department.query.all()
    
    return render_template('departments.html', 
                         patient=patient,
                         departments=departments)

@app.route('/patient/department/<int:department_id>')
@login_required
@role_required(['patient'])
def department_details(department_id):
    """Display details of a specific department and its doctors"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get department details
    department = Department.query.filter(Department.id == department_id).first()
    
    if not department:
        flash('Department not found', 'error')
        return redirect(url_for('patient_departments'))
    
    # Get doctors in this department
    doctors = Doctor.query.filter(Doctor.specialization == department.name).all()
    
    return render_template('department_details.html', 
                         patient=patient,
                         department=department,
                         doctors=doctors)

@app.route('/patient/doctor/<int:doctor_id>/availability')
@login_required
@role_required(['patient'])
def doctor_availability_patient_view(doctor_id):
    """View a doctor's availability from patient perspective"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get doctor details
    doctor = Doctor.query.filter(Doctor.id == doctor_id).first()
    
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('patient_departments'))
    
    # Get doctor's availability slots
    availability_slots = {}
    if doctor.availability_slots:
        import json
        try:
            availability_slots = json.loads(doctor.availability_slots)
        except:
            availability_slots = {}
    
    def is_slot_available(date_str, time_slot):
        """Check if a specific time slot is available"""
        if date_str in availability_slots and time_slot in availability_slots[date_str]:
            return availability_slots[date_str][time_slot] == 'available'
        return False
    
    # Generate date information for the next 7 days
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
    
    return render_template('doctor_availability_patient.html', 
                         patient=patient,
                         doctor=doctor,
                         dates_info=dates_info)

@app.route('/patient/doctor/<int:doctor_id>/profile')
@login_required
@role_required(['patient'])
def doctor_profile_patient_view(doctor_id):
    """View a doctor's profile from patient perspective"""
    patient = Patient.query.join(User).filter(User.id == session['user_id']).first()
    
    if not patient:
        flash('Patient profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get doctor details
    doctor = Doctor.query.filter(Doctor.id == doctor_id).first()
    
    if not doctor:
        flash('Doctor not found', 'error')
        return redirect(url_for('patient_departments'))
    
    return render_template('doctor_profile_patient.html', 
                         patient=patient,
                         doctor=doctor)

@app.route('/admin/patient/<int:patient_id>/history')
@login_required
@role_required(['admin'])
def admin_patient_history(patient_id):
    """Display a patient's complete medical history for admin"""
    # Get patient details with user information
    patient = Patient.query.join(User).filter(Patient.id == patient_id).first()
    
    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Get patient's complete treatment history with doctor information
    treatments = db.session.query(
        Treatment,
        Appointment.appointment_date,
        Appointment.appointment_time,
        Doctor.name.label('doctor_name'),
        Doctor.specialization.label('specialization')
    ).join(Appointment, Treatment.appointment_id == Appointment.id)\
     .join(Doctor, Appointment.doctor_id == Doctor.id)\
     .filter(Appointment.patient_id == patient_id)\
     .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    # Add serial numbers and appointment info to treatments
    treatments_with_info = []
    for i, treatment_tuple in enumerate(treatments, 1):
        treatment = treatment_tuple[0]
        appointment_date = treatment_tuple[1]
        appointment_time = treatment_tuple[2]
        doctor_name = treatment_tuple[3]
        specialization = treatment_tuple[4]
        
        # Create a dictionary with treatment data
        treatment_dict = {
            'id': treatment.id,
            'appointment_id': treatment.appointment_id,
            'diagnosis': treatment.diagnosis,
            'prescription': treatment.prescription,
            'treatment_notes': treatment.treatment_notes,
            'created_at': treatment.created_at,
            'serial_no': i,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'doctor_name': doctor_name,
            'specialization': specialization
        }
        treatments_with_info.append(treatment_dict)
    
    return render_template('admin_patient_history.html', 
                         patient=patient,
                         treatments=treatments_with_info)