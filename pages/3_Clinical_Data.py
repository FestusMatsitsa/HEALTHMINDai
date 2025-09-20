import streamlit as st
from datetime import datetime, date
from auth import require_auth
from medical_ai import analyze_clinical_data, generate_multimodal_diagnosis
from database import create_medical_case, update_case, get_user_cases
from utils import (
    display_medical_disclaimer, create_vitals_chart, create_lab_results_chart, 
    validate_vital_signs, display_confidence_score, calculate_risk_score
)

# Require authentication
user = require_auth()
if not user:
    st.stop()

st.set_page_config(
    page_title="Clinical Data - AI Medical Assistant",
    page_icon="📋",
    layout="wide"
)

st.markdown('<h1 style="color: #2E86AB; text-align: center;">📋 Clinical Data Analysis</h1>', 
           unsafe_allow_html=True)

display_medical_disclaimer()

# Initialize session state
if 'clinical_data' not in st.session_state:
    st.session_state.clinical_data = {
        'symptoms': [],
        'vitals': {},
        'lab_results': {}
    }
if 'clinical_analysis' not in st.session_state:
    st.session_state.clinical_analysis = None

# Sidebar for data input
with st.sidebar:
    st.subheader("🎯 Quick Actions")
    
    if st.button("🔄 Reset All Data", type="secondary"):
        st.session_state.clinical_data = {
            'symptoms': [],
            'vitals': {},
            'lab_results': {}
        }
        st.session_state.clinical_analysis = None
        st.rerun()
    
    if st.button("🤖 Analyze Data", type="primary", disabled=not any([
        st.session_state.clinical_data['symptoms'],
        any(st.session_state.clinical_data['vitals'].values()),
        any(st.session_state.clinical_data['lab_results'].values())
    ])):
        with st.spinner("Analyzing clinical data..."):
            analysis = analyze_clinical_data(
                st.session_state.clinical_data['symptoms'],
                st.session_state.clinical_data['vitals'],
                st.session_state.clinical_data['lab_results']
            )
            
            if analysis:
                st.session_state.clinical_analysis = analysis
                st.success("✅ Analysis complete!")
                st.rerun()
            else:
                st.error("❌ Analysis failed")
    
    st.markdown("---")
    
    # Data summary
    st.subheader("📊 Data Summary")
    st.write(f"**Symptoms:** {len(st.session_state.clinical_data['symptoms'])}")
    st.write(f"**Vitals:** {sum(1 for v in st.session_state.clinical_data['vitals'].values() if v)}")
    st.write(f"**Labs:** {sum(1 for v in st.session_state.clinical_data['lab_results'].values() if v)}")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["🩺 Symptoms", "💓 Vital Signs", "🧪 Lab Results", "📊 Analysis"])

with tab1:
    st.subheader("🩺 Patient Symptoms")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Common symptoms checklist
        st.markdown("#### Common Symptoms")
        
        common_symptoms = [
            "Cough", "Shortness of breath", "Chest pain", "Fever", 
            "Fatigue", "Weight loss", "Night sweats", "Hemoptysis",
            "Wheezing", "Sputum production", "Palpitations", "Dizziness",
            "Nausea", "Vomiting", "Headache", "Abdominal pain"
        ]
        
        # Create checkboxes in columns
        cols = st.columns(4)
        selected_symptoms = []
        
        for i, symptom in enumerate(common_symptoms):
            with cols[i % 4]:
                if st.checkbox(symptom, key=f"symptom_{symptom}"):
                    selected_symptoms.append(symptom)
        
        # Additional symptoms
        st.markdown("#### Additional Symptoms")
        additional_symptoms = st.text_area(
            "Other symptoms (one per line)",
            placeholder="Enter any additional symptoms...",
            height=100
        )
        
        if additional_symptoms:
            additional_list = [s.strip() for s in additional_symptoms.split('\n') if s.strip()]
            selected_symptoms.extend(additional_list)
        
        # Update session state
        st.session_state.clinical_data['symptoms'] = selected_symptoms
    
    with col2:
        st.markdown("#### Symptom Details")
        
        if selected_symptoms:
            st.success(f"✅ {len(selected_symptoms)} symptoms recorded")
            
            with st.expander("View Selected Symptoms"):
                for symptom in selected_symptoms:
                    st.write(f"• {symptom}")
        else:
            st.info("No symptoms selected")
        
        # Symptom duration and severity
        if selected_symptoms:
            st.markdown("#### Symptom Characteristics")
            
            duration = st.selectbox(
                "Symptom Duration",
                ["Acute (<24 hours)", "Subacute (1-7 days)", "Chronic (>1 week)", "Unknown"]
            )
            
            severity = st.select_slider(
                "Overall Severity",
                options=["Mild", "Moderate", "Severe", "Critical"],
                value="Moderate"
            )
            
            onset = st.selectbox(
                "Onset",
                ["Sudden", "Gradual", "Progressive", "Intermittent", "Unknown"]
            )

with tab2:
    st.subheader("💓 Vital Signs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Primary Vitals")
        
        # Temperature
        temperature = st.number_input(
            "Temperature (°C)",
            min_value=35.0,
            max_value=42.0,
            step=0.1,
            format="%.1f",
            help="Normal: 36.0-37.5°C"
        )
        if temperature > 35.0:
            st.session_state.clinical_data['vitals']['temperature'] = temperature
        
        # Heart Rate
        heart_rate = st.number_input(
            "Heart Rate (bpm)",
            min_value=30,
            max_value=200,
            step=1,
            help="Normal: 60-100 bpm"
        )
        if heart_rate > 30:
            st.session_state.clinical_data['vitals']['heart_rate'] = heart_rate
        
        # Blood Pressure
        col_bp1, col_bp2 = st.columns(2)
        with col_bp1:
            systolic_bp = st.number_input(
                "Systolic BP (mmHg)",
                min_value=60,
                max_value=250,
                step=1,
                help="Normal: <120 mmHg"
            )
            if systolic_bp > 60:
                st.session_state.clinical_data['vitals']['systolic_bp'] = systolic_bp
        
        with col_bp2:
            diastolic_bp = st.number_input(
                "Diastolic BP (mmHg)",
                min_value=40,
                max_value=150,
                step=1,
                help="Normal: <80 mmHg"
            )
            if diastolic_bp > 40:
                st.session_state.clinical_data['vitals']['diastolic_bp'] = diastolic_bp
        
        # Format blood pressure
        if systolic_bp > 60 and diastolic_bp > 40:
            st.session_state.clinical_data['vitals']['blood_pressure'] = f"{systolic_bp}/{diastolic_bp}"
    
    with col2:
        st.markdown("#### Additional Vitals")
        
        # Respiratory Rate
        respiratory_rate = st.number_input(
            "Respiratory Rate (breaths/min)",
            min_value=8,
            max_value=40,
            step=1,
            help="Normal: 12-20 breaths/min"
        )
        if respiratory_rate > 8:
            st.session_state.clinical_data['vitals']['respiratory_rate'] = respiratory_rate
        
        # Oxygen Saturation
        oxygen_saturation = st.number_input(
            "Oxygen Saturation (%)",
            min_value=70,
            max_value=100,
            step=1,
            help="Normal: >95%"
        )
        if oxygen_saturation > 70:
            st.session_state.clinical_data['vitals']['oxygen_saturation'] = oxygen_saturation
        
        # Pain Scale
        pain_score = st.select_slider(
            "Pain Scale (0-10)",
            options=list(range(0, 11)),
            value=0,
            help="0 = No pain, 10 = Worst pain"
        )
        if pain_score > 0:
            st.session_state.clinical_data['vitals']['pain_score'] = pain_score
    
    # Vital signs validation
    warnings = validate_vital_signs(st.session_state.clinical_data['vitals'])
    if warnings:
        st.markdown("#### ⚠️ Vital Signs Alerts")
        for warning in warnings:
            st.warning(warning)
    
    # Vital signs visualization
    vitals_chart = create_vitals_chart(st.session_state.clinical_data['vitals'])
    if vitals_chart:
        st.plotly_chart(vitals_chart, use_container_width=True)

with tab3:
    st.subheader("🧪 Laboratory Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Complete Blood Count (CBC)")
        
        # WBC
        wbc = st.number_input(
            "White Blood Cells (×10³/μL)",
            min_value=0.0,
            max_value=50.0,
            step=0.1,
            format="%.1f",
            help="Normal: 4.0-11.0"
        )
        if wbc > 0:
            st.session_state.clinical_data['lab_results']['wbc'] = wbc
        
        # RBC
        rbc = st.number_input(
            "Red Blood Cells (×10⁶/μL)",
            min_value=0.0,
            max_value=8.0,
            step=0.1,
            format="%.1f",
            help="Normal: 4.2-5.4"
        )
        if rbc > 0:
            st.session_state.clinical_data['lab_results']['rbc'] = rbc
        
        # Hemoglobin
        hemoglobin = st.number_input(
            "Hemoglobin (g/dL)",
            min_value=0.0,
            max_value=20.0,
            step=0.1,
            format="%.1f",
            help="Normal: 12.0-16.0"
        )
        if hemoglobin > 0:
            st.session_state.clinical_data['lab_results']['hemoglobin'] = hemoglobin
        
        # Hematocrit
        hematocrit = st.number_input(
            "Hematocrit (%)",
            min_value=0.0,
            max_value=60.0,
            step=0.1,
            format="%.1f",
            help="Normal: 36-46%"
        )
        if hematocrit > 0:
            st.session_state.clinical_data['lab_results']['hematocrit'] = hematocrit
        
        # Platelets
        platelets = st.number_input(
            "Platelets (×10³/μL)",
            min_value=0,
            max_value=1000,
            step=1,
            help="Normal: 150-450"
        )
        if platelets > 0:
            st.session_state.clinical_data['lab_results']['platelets'] = platelets
    
    with col2:
        st.markdown("#### Chemistry Panel")
        
        # Glucose
        glucose = st.number_input(
            "Glucose (mg/dL)",
            min_value=0,
            max_value=500,
            step=1,
            help="Normal: 70-100"
        )
        if glucose > 0:
            st.session_state.clinical_data['lab_results']['glucose'] = glucose
        
        # Creatinine
        creatinine = st.number_input(
            "Creatinine (mg/dL)",
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            format="%.1f",
            help="Normal: 0.6-1.2"
        )
        if creatinine > 0:
            st.session_state.clinical_data['lab_results']['creatinine'] = creatinine
        
        # BUN
        bun = st.number_input(
            "BUN (mg/dL)",
            min_value=0,
            max_value=100,
            step=1,
            help="Normal: 7-20"
        )
        if bun > 0:
            st.session_state.clinical_data['lab_results']['bun'] = bun
        
        st.markdown("#### Inflammatory Markers")
        
        # CRP
        crp = st.number_input(
            "C-Reactive Protein (mg/L)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f",
            help="Normal: <3.0"
        )
        if crp > 0:
            st.session_state.clinical_data['lab_results']['crp'] = crp
        
        # ESR
        esr = st.number_input(
            "ESR (mm/hr)",
            min_value=0,
            max_value=150,
            step=1,
            help="Normal: <30"
        )
        if esr > 0:
            st.session_state.clinical_data['lab_results']['esr'] = esr
    
    # Lab results visualization
    lab_chart = create_lab_results_chart(st.session_state.clinical_data['lab_results'])
    if lab_chart:
        st.plotly_chart(lab_chart, use_container_width=True)

with tab4:
    st.subheader("📊 Clinical Data Analysis")
    
    if st.session_state.clinical_analysis:
        analysis = st.session_state.clinical_analysis
        
        # Risk Assessment
        if analysis.get('risk_assessment'):
            risk = analysis['risk_assessment']
            st.markdown("#### 🎯 Risk Assessment")
            
            col1, col2 = st.columns(2)
            
            with col1:
                risk_level = risk.get('overall_risk', 'unknown')
                risk_colors = {
                    'low': '#28a745',
                    'moderate': '#ffc107', 
                    'high': '#fd7e14',
                    'critical': '#dc3545'
                }
                
                st.markdown(f"""
                <div style="text-align: center; padding: 20px;">
                    <div style="background-color: {risk_colors.get(risk_level, '#6c757d')}; 
                                color: white; padding: 10px 20px; border-radius: 20px; 
                                display: inline-block; font-size: 1.2em; font-weight: bold;">
                        Risk Level: {risk_level.upper()}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if risk.get('risk_score'):
                    display_confidence_score(risk['risk_score'], "Risk Score")
            
            with col2:
                if risk.get('risk_factors'):
                    st.markdown("**Risk Factors:**")
                    for factor in risk['risk_factors']:
                        st.write(f"• {factor}")
        
        # Clinical Impressions
        if analysis.get('clinical_impressions'):
            st.markdown("---")
            st.markdown("#### 🔍 Clinical Impressions")
            
            for impression in analysis['clinical_impressions']:
                with st.expander(f"🎯 {impression.get('condition', 'Unknown Condition')}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if impression.get('probability'):
                            display_confidence_score(impression['probability'], "Probability")
                    
                    with col2:
                        if impression.get('rationale'):
                            st.write(f"**Rationale:** {impression['rationale']}")
        
        # Abnormal Findings
        if analysis.get('abnormal_findings'):
            st.markdown("---")
            st.markdown("#### ⚠️ Abnormal Findings")
            
            for finding in analysis['abnormal_findings']:
                st.warning(f"**{finding.get('parameter', 'Unknown')}:** {finding.get('value', 'N/A')} "
                          f"(Normal: {finding.get('reference_range', 'N/A')}) - {finding.get('significance', '')}")
        
        # Recommendations
        if analysis.get('recommendations'):
            st.markdown("---")
            st.markdown("#### 💡 Recommendations")
            
            # Group by priority
            immediate = [r for r in analysis['recommendations'] if r.get('category') == 'immediate']
            short_term = [r for r in analysis['recommendations'] if r.get('category') == 'short_term']
            long_term = [r for r in analysis['recommendations'] if r.get('category') == 'long_term']
            
            if immediate:
                st.markdown("**🚨 Immediate Actions:**")
                for rec in immediate:
                    st.error(f"• {rec.get('action', 'Unknown action')}")
            
            if short_term:
                st.markdown("**⏰ Short-term Actions:**")
                for rec in short_term:
                    st.warning(f"• {rec.get('action', 'Unknown action')}")
            
            if long_term:
                st.markdown("**📅 Long-term Actions:**")
                for rec in long_term:
                    st.info(f"• {rec.get('action', 'Unknown action')}")
        
        # Follow-up Plan
        if analysis.get('follow_up'):
            st.markdown("---")
            st.markdown("#### 📋 Follow-up Plan")
            
            follow_up = analysis['follow_up']
            
            col1, col2 = st.columns(2)
            
            with col1:
                if follow_up.get('timeframe'):
                    st.write(f"**Timeframe:** {follow_up['timeframe']}")
                
                if follow_up.get('specialist_referral'):
                    st.write(f"**Specialist Referral:** {follow_up['specialist_referral']}")
            
            with col2:
                if follow_up.get('recommended_tests'):
                    st.write("**Recommended Tests:**")
                    for test in follow_up['recommended_tests']:
                        st.write(f"• {test}")
        
        # Save analysis button
        st.markdown("---")
        col_save1, col_save2 = st.columns([3, 1])
        
        with col_save1:
            case_title = st.text_input(
                "Case Title",
                value=f"Clinical Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        
        with col_save2:
            if st.button("💾 Save Case", type="primary"):
                case_data = {
                    'case_title': case_title,
                    'symptoms': st.session_state.clinical_data['symptoms'],
                    'vitals': st.session_state.clinical_data['vitals'],
                    'lab_results': st.session_state.clinical_data['lab_results'],
                    'ai_diagnosis': {
                        'clinical_analysis': analysis,
                        'integrated_diagnosis': {
                            'primary_diagnosis': analysis.get('clinical_impressions', [{}])[0].get('condition', 'Multiple findings'),
                            'confidence': analysis.get('risk_assessment', {}).get('risk_score', 0),
                            'severity': analysis.get('risk_assessment', {}).get('overall_risk', 'unknown')
                        }
                    },
                    'recommendations': '\n'.join([
                        rec.get('action', '') for rec in analysis.get('recommendations', [])
                    ])
                }
                
                case_id = create_medical_case(user['id'], case_data)
                
                if case_id:
                    st.success(f"✅ Case saved! Case ID: {case_id}")
                    
                    # Reset data
                    st.session_state.clinical_data = {
                        'symptoms': [],
                        'vitals': {},
                        'lab_results': {}
                    }
                    st.session_state.clinical_analysis = None
                else:
                    st.error("❌ Failed to save case")
    
    else:
        st.info("Enter clinical data in the previous tabs and click 'Analyze Data' to see AI analysis results.")
        
        if any([
            st.session_state.clinical_data['symptoms'],
            any(st.session_state.clinical_data['vitals'].values()),
            any(st.session_state.clinical_data['lab_results'].values())
        ]):
            if st.button("🤖 Analyze Current Data", type="primary"):
                with st.spinner("Analyzing clinical data..."):
                    analysis = analyze_clinical_data(
                        st.session_state.clinical_data['symptoms'],
                        st.session_state.clinical_data['vitals'],
                        st.session_state.clinical_data['lab_results']
                    )
                    
                    if analysis:
                        st.session_state.clinical_analysis = analysis
                        st.rerun()
                    else:
                        st.error("❌ Analysis failed")

# Help section
with st.expander("❓ Help & Guidelines"):
    st.markdown("""
    ### 📋 Clinical Data Entry Guidelines:
    
    #### Symptoms:
    - Select all applicable symptoms from the checklist
    - Add additional symptoms in the text area
    - Be specific about symptom characteristics
    
    #### Vital Signs:
    - Enter current vital signs measurements
    - System will alert for abnormal values
    - All fields are optional but more data improves analysis
    
    #### Laboratory Results:
    - Enter recent lab values (within 24-48 hours)
    - Include units as specified
    - Focus on abnormal values for better insights
    
    ### 🎯 Analysis Features:
    - **Risk Stratification**: Automated risk level assessment
    - **Clinical Correlation**: Pattern recognition across all data
    - **Evidence-based Recommendations**: Guidelines-based suggestions
    - **Follow-up Planning**: Structured care coordination
    """)
