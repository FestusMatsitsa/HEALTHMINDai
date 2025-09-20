import bcrypt
import streamlit as st
from database import get_db_connection, log_user_action
from datetime import datetime

def hash_password(password):
    """Hash a password for storing"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(name, email, password, specialty, license_number=""):
    """Register a new user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, specialty, license_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, password_hash, specialty, license_number, datetime.now()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        log_user_action(user_id, "REGISTER", f"New user registered: {email}")
        return True
        
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False

def authenticate_user(email, password):
    """Authenticate user login"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, password_hash, specialty, license_number 
            FROM users WHERE email = ?
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user['password_hash']):
            user_dict = dict(user)
            log_user_action(user_dict['id'], "LOGIN", f"User logged in: {email}")
            return user_dict
        
        return None
        
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def get_current_user(user_id):
    """Get current user information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, specialty, license_number, created_at
            FROM users WHERE id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
        
    except Exception as e:
        st.error(f"Error fetching user: {str(e)}")
        return None

def update_user_profile(user_id, updates):
    """Update user profile"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['name', 'specialty', 'license_number']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return False
            
        set_clauses.append("updated_at = ?")
        values.append(datetime.now())
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        log_user_action(user_id, "UPDATE_PROFILE", "Profile updated")
        return True
        
    except Exception as e:
        st.error(f"Error updating profile: {str(e)}")
        return False

def change_password(user_id, current_password, new_password):
    """Change user password"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current password hash
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or not verify_password(current_password, user['password_hash']):
            conn.close()
            return False
        
        # Update password
        new_hash = hash_password(new_password)
        cursor.execute("""
            UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?
        """, (new_hash, datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        
        log_user_action(user_id, "CHANGE_PASSWORD", "Password changed")
        return True
        
    except Exception as e:
        st.error(f"Error changing password: {str(e)}")
        return False

def logout_user():
    """Logout current user"""
    if 'user_id' in st.session_state:
        log_user_action(st.session_state.user_id, "LOGOUT", "User logged out")
        
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def require_auth():
    """Decorator-like function to require authentication"""
    if 'user_id' not in st.session_state:
        st.error("Please login to access this page.")
        st.stop()
        return None
    
    user = get_current_user(st.session_state.user_id)
    if not user:
        st.error("Session expired. Please login again.")
        logout_user()
        st.stop()
        return None
        
    return user
