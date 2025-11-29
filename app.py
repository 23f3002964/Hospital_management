from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import hashlib
from datetime import datetime, date, timedelta
from functools import wraps
from markupsafe import escape
import re

app = Flask(__name__)
app.secret_key = 'hospital-management-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)  # admin, doctor, patient
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    doctor = db.relationship('Doctor', back_populates='user', uselist=False)
    patient = db.relationship('Patient', back_populates='user', uselist=False)

class Department(db.Model):
    __tablename__ = 'departments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str] = mapped_column()

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    specialization: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    availability_days: Mapped[str] = mapped_column(nullable=True)
    availability_hours: Mapped[str] = mapped_column(nullable=True)
    availability_slots: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='doctor')
    appointments = db.relationship('Appointment', back_populates='doctor')

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str] = mapped_column()
    address: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='patient')
    appointments = db.relationship('Appointment', back_populates='patient')

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.ForeignKey('patients.id'), nullable=False)
    doctor_id: Mapped[int] = mapped_column(db.ForeignKey('doctors.id'), nullable=False)
    appointment_date: Mapped[date] = mapped_column(nullable=False)
    appointment_time: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(default='booked')  # booked, completed, cancelled
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    treatment = db.relationship('Treatment', back_populates='appointment', uselist=False)

class Treatment(db.Model):
    __tablename__ = 'treatments'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(db.ForeignKey('appointments.id'), nullable=False)
    diagnosis: Mapped[str] = mapped_column()
    prescription: Mapped[str] = mapped_column()
    treatment_notes: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    appointment = db.relationship('Appointment', back_populates='treatment')

def init_db():
    with app.app_context():
        # Check if tables already exist and have data
        if User.query.first() is None:
            # Only initialize if no data exists
            db.create_all()
            
            # Only create the admin user if no users exist
            admin_user = User.query.first()
            if not admin_user:
                # Create default admin user only
                admin_password = hashlib.sha256('admin'.encode()).hexdigest()
                admin = User(username='admin', email='admin@hospital.com', password_hash=admin_password, role='admin')
                db.session.add(admin)
                db.session.commit()
        else:
            # Tables exist, no need for initialization
            print("Database already initialized.")

# Import all routes from routes.py
from routes import *

if __name__ == '__main__':
    init_db()
    app.run(debug=True)