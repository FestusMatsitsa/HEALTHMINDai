import os
import sqlite3
from datetime import datetime
import json
import streamlit as st

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "medical_assistant.db")

def get_param_placeholder():
    """Get the correct parameter placeholder for the database type"""
    if DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'):
        return '%s'
    else:
        return '?'

def is_postgres():
    """Check if using PostgreSQL"""
    return DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://')

def get_db_connection():
    """Get database connection - supports both SQLite and PostgreSQL"""
    if DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn

def init_database():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        is_postgres = DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://')
        
        if is_postgres:
            # PostgreSQL syntax
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    specialty VARCHAR(100),
                    license_number VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Medical cases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medical_cases (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    patient_id VARCHAR(100),
                    case_title VARCHAR(255),
                    symptoms TEXT,
                    vitals TEXT,
                    lab_results TEXT,
                    image_filename VARCHAR(255),
                    image_analysis TEXT,
                    ai_diagnosis TEXT,
                    confidence_scores TEXT,
                    recommendations TEXT,
                    case_status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Case notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS case_notes (
                    id SERIAL PRIMARY KEY,
                    case_id INTEGER NOT NULL,
                    note_text TEXT NOT NULL,
                    note_type VARCHAR(50) DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES medical_cases (id)
                )
            """)
            
            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    action VARCHAR(100) NOT NULL,
                    details TEXT,
                    ip_address VARCHAR(45),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
        else:
            # SQLite syntax
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    specialty VARCHAR(100),
                    license_number VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Medical cases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medical_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    patient_id VARCHAR(100),
                    case_title VARCHAR(255),
                    symptoms TEXT,
                    vitals TEXT,
                    lab_results TEXT,
                    image_filename VARCHAR(255),
                    image_analysis TEXT,
                    ai_diagnosis TEXT,
                    confidence_scores TEXT,
                    recommendations TEXT,
                    case_status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Case notes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS case_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL,
                    note_text TEXT NOT NULL,
                    note_type VARCHAR(50) DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES medical_cases (id)
                )
            """)
            
            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action VARCHAR(100) NOT NULL,
                    details TEXT,
                    ip_address VARCHAR(45),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return False

def log_user_action(user_id, action, details=None):
    """Log user actions for audit trail"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            INSERT INTO system_logs (user_id, action, details, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        """, (user_id, action, details, datetime.now()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Logging error: {str(e)}")

def create_medical_case(user_id, case_data):
    """Create a new medical case"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = get_param_placeholder()
        if is_postgres():
            query = f"""
                INSERT INTO medical_cases 
                (user_id, patient_id, case_title, symptoms, vitals, lab_results, 
                 image_filename, image_analysis, ai_diagnosis, confidence_scores, 
                 recommendations, created_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING id
            """
        else:
            query = f"""
                INSERT INTO medical_cases 
                (user_id, patient_id, case_title, symptoms, vitals, lab_results, 
                 image_filename, image_analysis, ai_diagnosis, confidence_scores, 
                 recommendations, created_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """
        cursor.execute(query, (
            user_id,
            case_data.get('patient_id'),
            case_data.get('case_title'),
            json.dumps(case_data.get('symptoms', {})),
            json.dumps(case_data.get('vitals', {})),
            json.dumps(case_data.get('lab_results', {})),
            case_data.get('image_filename'),
            case_data.get('image_analysis'),
            json.dumps(case_data.get('ai_diagnosis', {})),
            json.dumps(case_data.get('confidence_scores', {})),
            case_data.get('recommendations'),
            datetime.now()
        ))
        
        if is_postgres():
            result = cursor.fetchone()
            case_id = result['id'] if result else None
        else:
            case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        log_user_action(user_id, "CREATE_CASE", f"Created case ID: {case_id}")
        return case_id
        
    except Exception as e:
        st.error(f"Error creating medical case: {str(e)}")
        return None

def get_user_cases(user_id, limit=50):
    """Get user's medical cases"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            SELECT * FROM medical_cases 
            WHERE user_id = {placeholder} 
            ORDER BY created_at DESC 
            LIMIT {placeholder}
        """, (user_id, limit))
        
        cases = cursor.fetchall()
        conn.close()
        
        # Parse JSON fields
        parsed_cases = []
        for case in cases:
            case_dict = dict(case)
            case_dict['symptoms'] = json.loads(case_dict.get('symptoms', '{}'))
            case_dict['vitals'] = json.loads(case_dict.get('vitals', '{}'))
            case_dict['lab_results'] = json.loads(case_dict.get('lab_results', '{}'))
            case_dict['ai_diagnosis'] = json.loads(case_dict.get('ai_diagnosis', '{}'))
            case_dict['confidence_scores'] = json.loads(case_dict.get('confidence_scores', '{}'))
            parsed_cases.append(case_dict)
            
        return parsed_cases
        
    except Exception as e:
        st.error(f"Error fetching cases: {str(e)}")
        return []

def get_case_by_id(case_id, user_id):
    """Get specific case by ID (with user verification)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            SELECT * FROM medical_cases 
            WHERE id = {placeholder} AND user_id = {placeholder}
        """, (case_id, user_id))
        
        case = cursor.fetchone()
        conn.close()
        
        if case:
            case_dict = dict(case)
            case_dict['symptoms'] = json.loads(case_dict.get('symptoms', '{}'))
            case_dict['vitals'] = json.loads(case_dict.get('vitals', '{}'))
            case_dict['lab_results'] = json.loads(case_dict.get('lab_results', '{}'))
            case_dict['ai_diagnosis'] = json.loads(case_dict.get('ai_diagnosis', '{}'))
            case_dict['confidence_scores'] = json.loads(case_dict.get('confidence_scores', '{}'))
            return case_dict
            
        return None
        
    except Exception as e:
        st.error(f"Error fetching case: {str(e)}")
        return None

def update_case(case_id, user_id, updates):
    """Update an existing case"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Whitelist allowed columns for security
        allowed_columns = [
            'patient_id', 'case_title', 'symptoms', 'vitals', 'lab_results',
            'image_filename', 'image_analysis', 'ai_diagnosis', 'confidence_scores',
            'recommendations', 'case_status'
        ]
        
        # Build update query dynamically
        set_clauses = []
        values = []
        placeholder = get_param_placeholder()
        
        for key, value in updates.items():
            if key not in allowed_columns:
                continue  # Skip non-whitelisted columns
                
            if key in ['symptoms', 'vitals', 'lab_results', 'ai_diagnosis', 'confidence_scores']:
                set_clauses.append(f"{key} = {placeholder}")
                values.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = {placeholder}")
                values.append(value)
        
        set_clauses.append(f"updated_at = {placeholder}")
        values.append(datetime.now())
        values.extend([case_id, user_id])
        
        query = f"""
            UPDATE medical_cases 
            SET {', '.join(set_clauses)}
            WHERE id = {placeholder} AND user_id = {placeholder}
        """
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        log_user_action(user_id, "UPDATE_CASE", f"Updated case ID: {case_id}")
        return True
        
    except Exception as e:
        st.error(f"Error updating case: {str(e)}")
        return False

def delete_case(case_id, user_id):
    """Delete a case"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            DELETE FROM medical_cases 
            WHERE id = {placeholder} AND user_id = {placeholder}
        """, (case_id, user_id))
        
        conn.commit()
        conn.close()
        
        log_user_action(user_id, "DELETE_CASE", f"Deleted case ID: {case_id}")
        return True
        
    except Exception as e:
        st.error(f"Error deleting case: {str(e)}")
        return False

def get_user_statistics(user_id):
    """Get user statistics for dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total cases
        placeholder = get_param_placeholder()
        cursor.execute(f"SELECT COUNT(*) AS count FROM medical_cases WHERE user_id = {placeholder}", (user_id,))
        result = cursor.fetchone()
        total_cases = dict(result)['count'] if result else 0
        
        # Active cases
        cursor.execute(f"SELECT COUNT(*) AS count FROM medical_cases WHERE user_id = {placeholder} AND case_status = 'active'", (user_id,))
        result = cursor.fetchone()
        active_cases = dict(result)['count'] if result else 0
        
        # Cases this month
        if is_postgres():
            cursor.execute(f"""
                SELECT COUNT(*) AS count FROM medical_cases 
                WHERE user_id = {placeholder} AND created_at >= date_trunc('month', now())
            """, (user_id,))
        else:
            cursor.execute(f"""
                SELECT COUNT(*) AS count FROM medical_cases 
                WHERE user_id = {placeholder} AND created_at >= date('now', 'start of month')
            """, (user_id,))
        result = cursor.fetchone()
        monthly_cases = dict(result)['count'] if result else 0
        
        # Recent activity
        cursor.execute(f"""
            SELECT action, created_at FROM system_logs 
            WHERE user_id = {placeholder} 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (user_id,))
        recent_activity = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_cases': total_cases,
            'active_cases': active_cases,
            'monthly_cases': monthly_cases,
            'recent_activity': [dict(row) for row in recent_activity]
        }
        
    except Exception as e:
        st.error(f"Error fetching statistics: {str(e)}")
        return {
            'total_cases': 0,
            'active_cases': 0,
            'monthly_cases': 0,
            'recent_activity': []
        }
