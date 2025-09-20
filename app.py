import streamlit as st
import os
from auth import authenticate_user, register_user, logout_user, get_current_user
from database import init_database

# Configure page
st.set_page_config(
    page_title="AI Medical Diagnosis Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_database()

# Custom CSS for medical styling
st.markdown("""
<style>
    .main-header {
        color: #2E86AB;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #2E86AB;
        margin-bottom: 2rem;
    }
    
    .disclaimer {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    .medical-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(45deg, #2E86AB, #A23B72);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        # Login/Register page
        st.markdown('<h1 class="main-header">🏥 AI Medical Diagnosis Assistant</h1>', unsafe_allow_html=True)
        
        # Medical disclaimer
        st.markdown("""
        <div class="disclaimer">
            <strong>⚠️ MEDICAL DISCLAIMER:</strong> This AI system is intended for healthcare professional use only 
            as a decision support tool. It is NOT a substitute for professional medical judgment, diagnosis, or treatment. 
            Always consult qualified healthcare professionals for medical decisions. The system provides preliminary 
            analysis and should not be used for emergency situations.
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Healthcare Professional Login")
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="doctor@hospital.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                
                if submitted:
                    if email and password:
                        user = authenticate_user(email, password)
                        if user:
                            st.session_state.user_id = user['id']
                            st.session_state.user_name = user['name']
                            st.session_state.user_email = user['email']
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")
                    else:
                        st.error("Please fill in all fields.")
        
        with tab2:
            st.subheader("Healthcare Professional Registration")
            with st.form("register_form"):
                name = st.text_input("Full Name", placeholder="Dr. John Smith")
                email = st.text_input("Email", placeholder="doctor@hospital.com")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                specialty = st.selectbox("Medical Specialty", [
                    "General Practice", "Internal Medicine", "Emergency Medicine", 
                    "Radiology", "Pulmonology", "Cardiology", "Family Medicine",
                    "Critical Care", "Other"
                ])
                license_number = st.text_input("Medical License Number", placeholder="Optional")
                
                submitted = st.form_submit_button("Register")
                
                if submitted:
                    if name and email and password and confirm_password:
                        if password == confirm_password:
                            if len(password) >= 8:
                                success = register_user(name, email, password, specialty, license_number)
                                if success:
                                    st.success("Registration successful! Please login.")
                                else:
                                    st.error("Registration failed. Email may already exist.")
                            else:
                                st.error("Password must be at least 8 characters long.")
                        else:
                            st.error("Passwords do not match.")
                    else:
                        st.error("Please fill in all required fields.")
    
    else:
        # Main app for logged-in users
        user = get_current_user(st.session_state.user_id)
        if not user:
            st.error("Session expired. Please login again.")
            logout_user()
            st.rerun()
            return
            
        # Sidebar navigation
        with st.sidebar:
            st.markdown(f"### Welcome, Dr. {user['name'].split()[0]}")
            st.markdown(f"**Email:** {user['email']}")
            st.markdown(f"**Specialty:** {user['specialty']}")
            
            st.markdown("---")
            
            # Navigation
            st.markdown("### Navigation")
            st.page_link("app.py", label="🏠 Home", icon="🏠")
            st.page_link("pages/1_Dashboard.py", label="📊 Dashboard", icon="📊")
            st.page_link("pages/2_Image_Analysis.py", label="🔬 Image Analysis", icon="🔬")
            st.page_link("pages/3_Clinical_Data.py", label="📋 Clinical Data", icon="📋")
            st.page_link("pages/4_Case_History.py", label="📚 Case History", icon="📚")
            st.page_link("pages/5_Profile.py", label="👤 Profile", icon="👤")
            
            st.markdown("---")
            
            if st.button("🚪 Logout"):
                logout_user()
                st.rerun()
        
        # Home page content
        st.markdown('<h1 class="main-header">🏥 AI Medical Diagnosis Assistant</h1>', unsafe_allow_html=True)
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>📊 Dashboard</h3>
                <p>View patient analytics and system overview</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🔬 Image Analysis</h3>
                <p>AI-powered chest X-ray analysis with explanations</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>📋 Clinical Data</h3>
                <p>Input symptoms, vitals, and lab results</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>📚 Case History</h3>
                <p>Review past cases and generate reports</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # System features
        st.subheader("🎯 System Capabilities")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🔬 AI Image Analysis
            - **Chest X-ray Analysis**: Automated detection of pneumonia, pneumothorax, consolidation
            - **DICOM Support**: Full DICOM file handling and metadata extraction
            - **Visual Explanations**: Grad-CAM heatmaps highlighting areas of interest
            - **Confidence Scores**: Quantified uncertainty estimates for each finding
            """)
            
            st.markdown("""
            ### 📊 Clinical Data Integration
            - **Structured Data Entry**: Symptoms, vitals, lab results
            - **Real-time Analysis**: Immediate pattern recognition in clinical data
            - **Historical Tracking**: Longitudinal patient data analysis
            - **Multi-modal Fusion**: Combining image and clinical data for enhanced accuracy
            """)
        
        with col2:
            st.markdown("""
            ### 🤖 AI-Powered Insights
            - **Diagnostic Suggestions**: Evidence-based preliminary findings
            - **Risk Stratification**: Priority scoring for urgent cases
            - **Differential Diagnosis**: Multiple potential diagnoses with probabilities
            - **Next Steps Recommendations**: Suggested follow-up actions
            """)
            
            st.markdown("""
            ### 📋 Professional Features
            - **Report Generation**: Comprehensive diagnostic reports
            - **Case Management**: Organized patient case tracking
            - **Audit Trail**: Complete logging of all analyses
            - **HIPAA Compliance**: Secure handling of medical data
            """)
        
        # Important notices
        st.markdown("---")
        st.markdown("""
        <div class="disclaimer">
            <strong>🔒 Privacy & Security:</strong> All patient data is encrypted and handled according to HIPAA guidelines. 
            This system maintains comprehensive audit logs and ensures data anonymization where required.
            <br><br>
            <strong>⚡ AI Technology:</strong> Powered by advanced multimodal AI models trained on extensive medical datasets. 
            The system provides explainable AI with visual attention maps and feature importance scoring.
            <br><br>
            <strong>🎯 Clinical Integration:</strong> Designed for seamless integration into clinical workflows with 
            support for DICOM imaging, HL7 data standards, and EHR compatibility.
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
