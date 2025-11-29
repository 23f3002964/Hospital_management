# 🏥 Hospital Management System

A comprehensive web-based hospital management system built with Flask that facilitates efficient management of doctors, patients, appointments, and medical records with role-based access control. This system provides separate dashboards for administrators, doctors, and patients with tailored functionality for each user type.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 🌟 Key Features

- **🔐 Role-Based Access Control**: Separate dashboards and permissions for Admin, Doctor, and Patient roles
- **📅 Appointment Management**: Book, reschedule, and cancel appointments with real-time availability
- **👨‍⚕️ Doctor Availability**: Flexible scheduling system with basic and advanced availability settings
- **📋 Medical Records**: Comprehensive patient history tracking and treatment documentation
- **🔍 Search Functionality**: Quick search for doctors and patients
- **📱 Responsive Design**: Mobile-friendly interface using Bootstrap 5
- **🛡️ Security**: Password hashing, input sanitization, and session management

## 🛠 Tech Stack / Technologies Used

### Backend
- **Flask 2.3.3** - Web framework
- **Flask-SQLAlchemy 3.0.5** - Database ORM
- **Hashlib** - Password hashing (SHA-256)
- **Jinja2** - Template engine
- **Werkzeug** - WSGI utility library

### Frontend
- **Bootstrap 5** - CSS framework
- **Bootstrap Icons** - Icon library
- **HTML5/CSS3** - Markup and styling
- **JavaScript** - Client-side validation and interactivity

### Database
- **SQLite** - Lightweight relational database with SQLAlchemy ORM

## 🏗 Project Architecture Overview

The system follows a Model-View-Controller (MVC) architecture pattern:

```
Hospital Management System
├── Models (Database Tables)
│   ├── Users (Admin, Doctors, Patients)
│   ├── Departments
│   ├── Doctors
│   ├── Patients
│   ├── Appointments
│   └── Treatments
├── Views (HTML Templates)
│   ├── Admin Dashboard
│   ├── Doctor Dashboard
│   └── Patient Dashboard
└── Controllers (Flask Routes)
    ├── Authentication
    ├── Admin Functions
    ├── Doctor Functions
    └── Patient Functions
```

## 📁 Folder Structure

```
Hospital_management/
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── PROJECT_REPORT.md       # Project documentation
├── README.md               # This file
├── static/
│   ├── style.css           # Custom CSS styling
│   └── validation.js       # Frontend validation scripts
└── templates/
    ├── base.html           # Base template
    ├── login.html          # Login page
    ├── register.html       # Patient registration
    ├── admin_dashboard.html # Admin dashboard
    ├── doctor_dashboard.html # Doctor dashboard
    ├── patient_dashboard.html # Patient dashboard
    └── ... (20+ other templates)
```

## 📄 Explanation of Important Files

| File | Description |
|------|-------------|
| `app.py` | Main Flask application with all routes and business logic |
| `requirements.txt` | Lists all Python dependencies |
| `templates/base.html` | Base template extended by all other templates |
| `templates/login.html` | User authentication interface |
| `templates/admin_dashboard.html` | Admin control panel |
| `templates/doctor_dashboard.html` | Doctor's appointment management |
| `templates/patient_dashboard.html` | Patient appointment booking system |
| `static/style.css` | Custom styling for the application |
| `static/validation.js` | Frontend form validation scripts |

## 🚀 Installation Guide

### Cloning

```bash
git clone <https://github.com/23f3002964/Hospital_management.git
>
cd Hospital_management
```

### Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```
### Run/Start Commands

To start the development server:

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🎯 Usage Instructions

### Initial Access

1. Start the application using `python app.py`
2. Open your browser and navigate to `http://localhost:5000`
3. Use the following demo credentials:

**Admin:**
- Username: `admin`
- Password: `admin`

**Doctors:**
- Username: `dr_rajesh_sharma` or `dr_priya_patel`
- Password: `password123`

**Patient:**
- Username: `patient1`
- Password: `password123`

### Role-Based Workflows

#### Admin
- Manage doctors (add, edit, delete)
- Manage patients
- View system statistics
- Search doctors/patients

#### Doctor
- Set availability schedules
- View upcoming appointments
- Complete appointments with diagnosis/treatment
- View patient medical history

#### Patient
- Book new appointments
- View medical history
- Reschedule/cancel appointments
- Browse doctors by department

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/login` | User authentication |
| GET/POST | `/register` | Patient registration |
| GET | `/logout` | User logout |

### Admin Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/dashboard` | Admin dashboard |
| GET | `/admin/doctors` | Manage doctors |
| GET/POST | `/admin/doctors/add` | Add new doctor |
| GET/POST | `/admin/doctors/edit/<id>` | Edit doctor details |
| POST | `/admin/doctors/delete/<id>` | Delete doctor |
| GET | `/admin/patients` | Manage patients |
| GET | `/admin/search` | Search functionality |

### Doctor Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/doctor/dashboard` | Doctor dashboard |
| GET | `/doctor/appointments` | View all appointments |
| GET/POST | `/doctor/availability` | Set weekly availability |
| GET/POST | `/doctor/advanced-availability` | Set advanced availability |
| GET | `/doctor/patient/<id>/history` | View patient medical history |
| GET/POST | `/doctor/appointment/<id>/update-history` | Update patient history |
| POST | `/doctor/appointment/<id>/complete` | Mark appointment as completed |
| POST | `/doctor/appointment/<id>/cancel` | Cancel appointment |

### Patient Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/patient/dashboard` | Patient dashboard |
| GET/POST | `/patient/profile` | View/update profile |
| GET | `/patient/history` | View medical history |
| GET | `/patient/departments` | Browse departments |
| GET | `/patient/department/<id>` | View doctors in department |
| GET | `/patient/doctor/<id>/availability` | View doctor availability |
| GET | `/patient/doctor/<id>/profile` | View doctor profile |
| POST | `/patient/book_appointment` | Book new appointment |
| POST | `/patient/appointment/<id>/cancel` | Cancel appointment |
| GET/POST | `/patient/appointment/<id>/reschedule` | Reschedule appointment |

## 🗄 Database Structure

The system uses 6 main tables with the following relationships:

```
erDiagram
    USERS ||--|| DOCTORS : "1:1"
    USERS ||--|| PATIENTS : "1:1"
    DOCTORS ||--o{ APPOINTMENTS : "1:N"
    PATIENTS ||--o{ APPOINTMENTS : "1:N"
    APPOINTMENTS ||--|| TREATMENTS : "1:1"
    DEPARTMENTS ||--o{ DOCTORS : "1:N"
```

### Tables

1. **USERS**: id, username, email, password_hash, role, created_at
2. **DEPARTMENTS**: id, name, description
3. **DOCTORS**: id, user_id, name, specialization, phone, availability_days, availability_hours, availability_slots, created_at
4. **PATIENTS**: id, user_id, name, phone, address, created_at
5. **APPOINTMENTS**: id, patient_id, doctor_id, appointment_date, appointment_time, status, created_at
6. **TREATMENTS**: id, appointment_id, diagnosis, prescription, treatment_notes, created_at

## ⚙ Configuration Details

The application uses Flask-SQLAlchemy for database operations with SQLite as the underlying database engine. The database (`hospital_new.db`) is automatically created on first run. Key configuration values in `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_new.db'
app.secret_key = 'hospital-management-secret-key'
```

## 👥 Contributing Instructions

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## ✨ Author Info

- **Team**: Hospital Management System Development Team
- **Version**: 1.0.0
- **License**: MIT

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📝 Extra Notes

- The application includes comprehensive input validation on both frontend and backend
- Passwords are securely hashed using SHA-256
- All database queries are parameterized to prevent SQL injection
- The UI is fully responsive and works on mobile devices
- Demo credentials are provided for easy testing of all roles
- The system automatically creates an admin user on first run

For any issues or feature requests, please open an issue on the repository.
