import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import random

def init_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        company TEXT,
        industry TEXT,
        status TEXT DEFAULT 'lead',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_contact TIMESTAMP,
        lead_score INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        interaction_type TEXT,
        content TEXT,
        sentiment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL,
        category TEXT,
        features TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        scheduled_date TIMESTAMP,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    ''')
    
    sample_customers = [
        ('TechCorp Solutions', 'contact@techcorp.com', '+1234567890', 'TechCorp', 'Technology', 'lead', 75),
        ('HealthSystems Inc', 'info@healthsys.com', '+1234567891', 'HealthSystems', 'Healthcare', 'qualified', 85),
        ('EduTech Global', 'hello@edutech.com', '+1234567892', 'EduTech', 'Education', 'customer', 95),
        ('FinancePro Ltd', 'support@financepro.com', '+1234567893', 'FinancePro', 'Finance', 'lead', 60),
        ('RetailSmart', 'sales@retailsmart.com', '+1234567894', 'RetailSmart', 'Retail', 'qualified', 80)
    ]
    
    for customer in sample_customers:
        cursor.execute('''
        INSERT OR IGNORE INTO customers (name, email, phone, company, industry, status, lead_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', customer)
    
    sample_products = [
        ('SalesBot Pro', 'AI-powered sales automation platform', 499.99, 'Software', 'Lead scoring, Auto-dialer, Email automation'),
        ('CRM Suite', 'Complete CRM solution', 299.99, 'Software', 'Contact management, Pipeline tracking, Analytics'),
        ('Analytics Dashboard', 'Real-time sales analytics', 199.99, 'Analytics', 'Custom reports, Forecasting, KPI tracking')
    ]
    
    for product in sample_products:
        cursor.execute('''
        INSERT OR IGNORE INTO products (name, description, price, category, features)
        VALUES (?, ?, ?, ?, ?)
        ''', product)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

if __name__ == "__main__":
    os.makedirs("./database", exist_ok=True)
    init_database("./database/salesbot.db")