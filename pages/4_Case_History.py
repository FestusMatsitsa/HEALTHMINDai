import streamlit as st
import json
from datetime import datetime, timedelta
from auth import require_auth
from database import get_user_cases, get_case_by_id, update_case, delete_case
from medical_ai import generate_medical_report
from utils import (
    display_medical_disclaimer, display_findings_summary, format_medical_timestamp,
    generate_case_summary, display_confidence_score, export_case_data
)

# Require authentication
user = require_auth()
if not user:
    st.stop()

st.set_page_config(
    page_title="Case History - AI Medical Assistant",
    page_icon="📚",
    layout="wide"
)

st.markdown('<h1 style="color: #2E86AB; text-align: center;">📚 Case History & Management</h1>', 
           unsafe_allow_html=True)

display_medical_disclaimer()

# Initialize session state
if 'selected_case_id' not in st.session_state:
    st.session_state.selected_case_id = None
if 'show_report' not in st.session_state:
    st.session_state.show_report = False

# Sidebar for case filters and actions
with st.sidebar:
    st.subheader("🔍 Case Filters")
    
    # Date range filter
    date_range = st.selectbox(
        "Time Period",
        ["All Time", "Last 7 days", "Last 30 days", "Last 90 days", "Custom Range"]
    )
    
    if date_range == "Custom Range":
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
    
    # Status filter
    status_filter = st.selectbox(
        "Case Status",
        ["All", "Active", "Completed", "Under Review"]
    )
    
    # Search
    search_term = st.text_input("Search Cases", placeholder="Patient ID, diagnosis, etc.")
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    if st.button("🔄 Refresh Cases", use_container_width=True):
        st.rerun()
    
    if st.button("📊 Export All Cases", use_container_width=True):
        cases = get_user_cases(user['id'])
        if cases:
            export_data = export_case_data(cases, 'json')
            st.download_button(
                label="📥 Download JSON",
                data=export_data,
                file_name=f"medical_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Get user cases
cases = get_user_cases(user['id'], limit=100)

# Apply filters
filtered_cases = cases
if search_term:
    filtered_cases = [
        case for case in filtered_cases
        if (search_term.lower() in case.get('patient_id', '').lower() or
            search_term.lower() in case.get('case_title', '').lower() or
            search_term.lower() in str(case.get('ai_diagnosis', {})).lower())
    ]

if status_filter != "All":
    status_map = {"Active": "active", "Completed": "completed", "Under Review": "under_review"}
    filtered_cases = [
        case for case in filtered_cases
        if case.get('case_status') == status_map.get(status_filter, 'active')
    ]

# Main content
if not cases:
    st.info("No cases found. Start by analyzing medical images or clinical data.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔬 Start Image Analysis", use_container_width=True):
            st.switch_page("pages/2_Image_Analysis.py")
    
    with col2:
        if st.button("📋 Enter Clinical Data", use_container_width=True):
            st.switch_page("pages/3_Clinical_Data.py")

else:
    # Case overview metrics
    st.subheader("📊 Case Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cases", len(cases))
    
    with col2:
        active_count = len([c for c in cases if c.get('case_status') == 'active'])
        st.metric("Active Cases", active_count)
    
    with col3:
        recent_count = len([
            c for c in cases 
            if datetime.fromisoformat(str(c['created_at']).replace('Z', '+00:00')) > 
               datetime.now() - timedelta(days=7)
        ])
        st.metric("Recent (7 days)", recent_count)
    
    with col4:
        high_confidence = len([
            c for c in cases 
            if c.get('ai_diagnosis', {}).get('integrated_diagnosis', {}).get('confidence', 0) > 0.8
        ])
        st.metric("High Confidence", high_confidence)
    
    st.markdown("---")
    
    # Cases list and details
    if st.session_state.selected_case_id:
        # Show detailed case view
        case = get_case_by_id(st.session_state.selected_case_id, user['id'])
        
        if case:
            col_back, col_actions = st.columns([1, 4])
            
            with col_back:
                if st.button("⬅️ Back to List"):
                    st.session_state.selected_case_id = None
                    st.session_state.show_report = False
                    st.rerun()
            
            with col_actions:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("📄 Generate Report"):
                        st.session_state.show_report = True
                        st.rerun()
                
                with col2:
                    export_data = export_case_data(case, 'json')
                    st.download_button(
                        label="📥 Export Case",
                        data=export_data,
                        file_name=f"case_{case['id']}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                
                with col3:
                    new_status = st.selectbox(
                        "Status",
                        ["active", "completed", "under_review"],
                        index=["active", "completed", "under_review"].index(case.get('case_status', 'active'))
                    )
                    if new_status != case.get('case_status'):
                        if update_case(case['id'], user['id'], {'case_status': new_status}):
                            st.success("Status updated!")
                            st.rerun()
                
                with col4:
                    if st.button("🗑️ Delete Case", type="secondary"):
                        if st.warning("Are you sure? This action cannot be undone."):
                            if delete_case(case['id'], user['id']):
                                st.success("Case deleted!")
                                st.session_state.selected_case_id = None
                                st.rerun()
            
            # Case details
            st.markdown("---")
            st.subheader(f"📋 Case Details: {case.get('case_title', 'Untitled Case')}")
            
            # Basic information
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Basic Information")
                st.write(f"**Case ID:** {case['id']}")
                if case.get('patient_id'):
                    st.write(f"**Patient ID:** {case['patient_id']}")
                st.write(f"**Status:** {case.get('case_status', 'Unknown').title()}")
                st.write(f"**Created:** {format_medical_timestamp(case['created_at'])}")
                st.write(f"**Updated:** {format_medical_timestamp(case['updated_at'])}")
            
            with col2:
                st.markdown("#### 🎯 Summary")
                summary = generate_case_summary(case)
                st.write(summary)
            
            # Tabbed content for case details
            tab1, tab2, tab3, tab4 = st.tabs(["🩺 Clinical Data", "🔬 Image Analysis", "🤖 AI Diagnosis", "📝 Notes"])
            
            with tab1:
                st.subheader("🩺 Clinical Data")
                
                # Symptoms
                if case.get('symptoms'):
                    st.markdown("#### Symptoms")
                    symptoms = case['symptoms']
                    if isinstance(symptoms, list) and symptoms:
                        for symptom in symptoms:
                            st.write(f"• {symptom}")
                    elif isinstance(symptoms, dict):
                        st.json(symptoms)
                    else:
                        st.write("No specific symptoms recorded")
                
                # Vitals
                if case.get('vitals'):
                    st.markdown("#### Vital Signs")
                    vitals = case['vitals']
                    for key, value in vitals.items():
                        if value:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                # Lab results
                if case.get('lab_results'):
                    st.markdown("#### Laboratory Results")
                    labs = case['lab_results']
                    for key, value in labs.items():
                        if value:
                            st.write(f"**{key.upper()}:** {value}")
            
            with tab2:
                st.subheader("🔬 Image Analysis")
                
                if case.get('image_analysis'):
                    image_analysis = case['image_analysis']
                    
                    # Overall assessment
                    if image_analysis.get('overall_assessment'):
                        assessment = image_analysis['overall_assessment']
                        st.markdown("#### 🎯 Overall Assessment")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Primary Diagnosis:** {assessment.get('primary_diagnosis', 'Not determined')}")
                            if assessment.get('confidence'):
                                display_confidence_score(assessment['confidence'], "Confidence")
                        
                        with col2:
                            st.write(f"**Severity:** {assessment.get('severity', 'Unknown').title()}")
                            st.write(f"**Urgency:** {assessment.get('urgency', 'Unknown').title()}")
                    
                    # Findings
                    if image_analysis.get('findings'):
                        st.markdown("---")
                        display_findings_summary(image_analysis['findings'])
                    
                    # Technical quality
                    if image_analysis.get('technical_quality'):
                        st.markdown("---")
                        st.markdown("#### 📊 Technical Quality")
                        quality = image_analysis['technical_quality']
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Image Quality:** {quality.get('image_quality', 'Unknown')}")
                            st.write(f"**Positioning:** {quality.get('positioning', 'Unknown')}")
                        
                        with col2:
                            st.write(f"**Inspiration:** {quality.get('inspiration', 'Unknown')}")
                            st.write(f"**Penetration:** {quality.get('penetration', 'Unknown')}")
                
                else:
                    st.info("No image analysis data available for this case.")
            
            with tab3:
                st.subheader("🤖 AI Diagnosis")
                
                if case.get('ai_diagnosis'):
                    diagnosis = case['ai_diagnosis']
                    
                    # Integrated diagnosis
                    if diagnosis.get('integrated_diagnosis'):
                        integrated = diagnosis['integrated_diagnosis']
                        st.markdown("#### 🎯 Primary Diagnosis")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Diagnosis:** {integrated.get('primary_diagnosis', 'Not determined')}")
                            if integrated.get('confidence'):
                                display_confidence_score(integrated['confidence'], "Confidence")
                        
                        with col2:
                            if integrated.get('supporting_evidence'):
                                st.write("**Supporting Evidence:**")
                                for evidence in integrated['supporting_evidence']:
                                    st.write(f"• {evidence}")
                    
                    # Clinical analysis
                    if diagnosis.get('clinical_analysis'):
                        clinical = diagnosis['clinical_analysis']
                        
                        if clinical.get('risk_assessment'):
                            st.markdown("---")
                            st.markdown("#### ⚠️ Risk Assessment")
                            risk = clinical['risk_assessment']
                            
                            risk_level = risk.get('overall_risk', 'unknown')
                            risk_colors = {
                                'low': '#28a745',
                                'moderate': '#ffc107',
                                'high': '#fd7e14',
                                'critical': '#dc3545'
                            }
                            
                            st.markdown(f"""
                            <div style="background-color: {risk_colors.get(risk_level, '#6c757d')}; 
                                        color: white; padding: 10px; border-radius: 10px; 
                                        text-align: center; margin: 10px 0;">
                                Risk Level: {risk_level.upper()}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Recommendations
                    if case.get('recommendations'):
                        st.markdown("---")
                        st.markdown("#### 💡 Recommendations")
                        recommendations = case['recommendations'].split('\n') if isinstance(case['recommendations'], str) else case['recommendations']
                        if isinstance(recommendations, list):
                            for rec in recommendations:
                                if rec.strip():
                                    st.write(f"• {rec.strip()}")
                        else:
                            st.write(case['recommendations'])
                
                else:
                    st.info("No AI diagnosis data available for this case.")
            
            with tab4:
                st.subheader("📝 Case Notes")
                st.info("Case notes functionality would be implemented here for adding clinical observations and follow-up notes.")
            
            # Medical report generation
            if st.session_state.show_report:
                st.markdown("---")
                st.subheader("📄 Medical Report")
                
                with st.spinner("Generating comprehensive medical report..."):
                    report = generate_medical_report(
                        case,
                        case.get('image_analysis'),
                        case.get('ai_diagnosis', {}).get('clinical_analysis'),
                        case.get('ai_diagnosis')
                    )
                    
                    if report:
                        st.markdown("#### Generated Medical Report")
                        st.text_area(
                            "Medical Report",
                            value=report,
                            height=400,
                            help="Professional medical report based on case data"
                        )
                        
                        st.download_button(
                            label="📥 Download Report",
                            data=report,
                            file_name=f"medical_report_case_{case['id']}_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("Failed to generate report. Please try again.")
        
        else:
            st.error("Case not found or access denied.")
            st.session_state.selected_case_id = None
    
    else:
        # Show cases list
        st.subheader(f"📋 Cases ({len(filtered_cases)} found)")
        
        if filtered_cases:
            # Cases table
            for case in filtered_cases:
                with st.expander(f"Case {case['id']}: {case.get('case_title', 'Untitled Case')}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Summary:** {generate_case_summary(case)}")
                        
                        if case.get('ai_diagnosis', {}).get('integrated_diagnosis'):
                            diagnosis = case['ai_diagnosis']['integrated_diagnosis']
                            primary = diagnosis.get('primary_diagnosis', 'N/A')
                            confidence = diagnosis.get('confidence', 0)
                            st.write(f"**Primary Diagnosis:** {primary}")
                            if confidence > 0:
                                display_confidence_score(confidence, "Confidence")
                    
                    with col2:
                        st.write(f"**Status:** {case.get('case_status', 'Unknown').title()}")
                        st.write(f"**Created:** {format_medical_timestamp(case['created_at'])}")
                        
                        if case.get('patient_id'):
                            st.write(f"**Patient ID:** {case['patient_id']}")
                    
                    with col3:
                        if st.button(f"View Details", key=f"view_case_{case['id']}"):
                            st.session_state.selected_case_id = case['id']
                            st.rerun()
                        
                        if st.button(f"Quick Export", key=f"export_case_{case['id']}"):
                            export_data = export_case_data(case, 'json')
                            st.download_button(
                                label="📥 Download",
                                data=export_data,
                                file_name=f"case_{case['id']}.json",
                                mime="application/json",
                                key=f"download_case_{case['id']}"
                            )
        
        else:
            st.info("No cases match the current filters.")

# Help section
with st.expander("❓ Help & Case Management"):
    st.markdown("""
    ### 📚 Case History Features:
    
    #### Case Management:
    - **View Details**: Complete case information with all analysis results
    - **Status Tracking**: Active, Completed, Under Review status management
    - **Search & Filter**: Find cases by date, status, or content
    - **Export Options**: JSON export for individual cases or bulk export
    
    #### Medical Reports:
    - **AI-Generated Reports**: Comprehensive diagnostic summaries
    - **Professional Format**: Medical-grade documentation
    - **Download Options**: Text and JSON formats available
    
    #### Data Organization:
    - **Clinical Data**: Symptoms, vitals, lab results
    - **Image Analysis**: AI findings with confidence scores
    - **AI Diagnosis**: Integrated multimodal analysis
    - **Recommendations**: Evidence-based next steps
    
    ### 🔧 Tips:
    - Use filters to quickly find specific cases
    - Regular status updates help track patient progress
    - Export important cases for external documentation
    - Generated reports are suitable for clinical documentation
    """)
