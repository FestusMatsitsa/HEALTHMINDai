import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def display_confidence_score(score, label):
    """Display confidence score with color coding"""
    if score >= 0.8:
        color = "#28a745"  # Green
        level = "High"
    elif score >= 0.6:
        color = "#ffc107"  # Yellow
        level = "Moderate"
    elif score >= 0.4:
        color = "#fd7e14"  # Orange
        level = "Low"
    else:
        color = "#dc3545"  # Red
        level = "Very Low"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin: 5px 0;">
        <span style="font-weight: bold; margin-right: 10px;">{label}:</span>
        <div style="background-color: {color}; color: white; padding: 2px 8px; 
                    border-radius: 12px; font-size: 0.8em; margin-right: 5px;">
            {level}
        </div>
        <span style="color: {color}; font-weight: bold;">{score:.1%}</span>
    </div>
    """, unsafe_allow_html=True)

def create_vitals_chart(vitals_data):
    """Create interactive vitals chart"""
    if not vitals_data:
        return None
    
    fig = go.Figure()
    
    # Temperature
    if vitals_data.get('temperature'):
        temp = float(vitals_data['temperature'])
        color = 'red' if temp > 37.5 or temp < 36.0 else 'green'
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=temp,
            domain={'x': [0, 0.5], 'y': [0.5, 1]},
            title={'text': "Temperature (°C)"},
            delta={'reference': 37.0},
            gauge={
                'axis': {'range': [None, 42]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 36], 'color': "lightblue"},
                    {'range': [36, 37.5], 'color': "lightgreen"},
                    {'range': [37.5, 42], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 37.5
                }
            }
        ))
    
    # Heart Rate
    if vitals_data.get('heart_rate'):
        hr = float(vitals_data['heart_rate'])
        color = 'red' if hr > 100 or hr < 60 else 'green'
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=hr,
            domain={'x': [0.5, 1], 'y': [0.5, 1]},
            title={'text': "Heart Rate (bpm)"},
            delta={'reference': 75},
            gauge={
                'axis': {'range': [None, 200]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 60], 'color': "lightblue"},
                    {'range': [60, 100], 'color': "lightgreen"},
                    {'range': [100, 200], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
    
    # Blood Pressure (if available)
    if vitals_data.get('systolic_bp') and vitals_data.get('diastolic_bp'):
        systolic = float(vitals_data['systolic_bp'])
        diastolic = float(vitals_data['diastolic_bp'])
        
        fig.add_trace(go.Bar(
            x=['Systolic', 'Diastolic'],
            y=[systolic, diastolic],
            name='Blood Pressure',
            marker_color=['red' if systolic > 140 else 'green', 
                         'red' if diastolic > 90 else 'green']
        ))
    
    fig.update_layout(
        title="Patient Vital Signs",
        height=400,
        showlegend=False
    )
    
    return fig

def create_lab_results_chart(lab_data):
    """Create lab results visualization"""
    if not lab_data:
        return None
    
    # Define normal ranges
    normal_ranges = {
        'wbc': (4.0, 11.0),
        'rbc': (4.2, 5.4),
        'hemoglobin': (12.0, 16.0),
        'hematocrit': (36, 46),
        'platelets': (150, 450),
        'glucose': (70, 100),
        'creatinine': (0.6, 1.2),
        'bun': (7, 20),
        'sodium': (135, 145),
        'potassium': (3.5, 5.0),
        'chloride': (98, 107),
        'co2': (22, 28),
        'crp': (0, 3.0),
        'esr': (0, 30)
    }
    
    lab_names = []
    lab_values = []
    colors = []
    reference_ranges = []
    
    for key, value in lab_data.items():
        if value and key in normal_ranges:
            try:
                val = float(value)
                lab_names.append(key.upper())
                lab_values.append(val)
                reference_ranges.append(f"{normal_ranges[key][0]}-{normal_ranges[key][1]}")
                
                # Color code based on normal ranges
                min_val, max_val = normal_ranges[key]
                if val < min_val or val > max_val:
                    colors.append('red')
                else:
                    colors.append('green')
            except ValueError:
                continue
    
    if not lab_names:
        return None
    
    fig = go.Figure(data=[
        go.Bar(
            x=lab_names,
            y=lab_values,
            marker_color=colors,
            text=[f"{val}<br>({ref})" for val, ref in zip(lab_values, reference_ranges)],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Laboratory Results",
        xaxis_title="Tests",
        yaxis_title="Values",
        height=500,
        showlegend=False
    )
    
    return fig

def display_findings_summary(findings):
    """Display AI findings in an organized manner"""
    if not findings:
        st.warning("No findings available.")
        return
    
    st.subheader("🔍 AI Analysis Results")
    
    # High probability findings
    high_prob_findings = []
    moderate_prob_findings = []
    low_prob_findings = []
    
    for finding, details in findings.items():
        if isinstance(details, dict) and 'probability' in details:
            prob = details['probability']
            if prob >= 0.7:
                high_prob_findings.append((finding, details))
            elif prob >= 0.3:
                moderate_prob_findings.append((finding, details))
            else:
                low_prob_findings.append((finding, details))
    
    # Display high probability findings
    if high_prob_findings:
        st.markdown("#### 🚨 High Probability Findings")
        for finding, details in high_prob_findings:
            with st.expander(f"🔴 {finding.replace('_', ' ').title()}", expanded=True):
                display_confidence_score(details['probability'], "Probability")
                if details.get('location'):
                    st.write(f"**Location:** {details['location']}")
                if details.get('description'):
                    st.write(f"**Description:** {details['description']}")
    
    # Display moderate probability findings
    if moderate_prob_findings:
        st.markdown("#### ⚠️ Moderate Probability Findings")
        for finding, details in moderate_prob_findings:
            with st.expander(f"🟡 {finding.replace('_', ' ').title()}"):
                display_confidence_score(details['probability'], "Probability")
                if details.get('location'):
                    st.write(f"**Location:** {details['location']}")
                if details.get('description'):
                    st.write(f"**Description:** {details['description']}")
    
    # Display low probability findings
    if low_prob_findings:
        st.markdown("#### ✅ Low Probability Findings")
        with st.expander("View Low Probability Findings"):
            for finding, details in low_prob_findings:
                col1, col2 = st.columns([1, 3])
                with col1:
                    display_confidence_score(details['probability'], finding.replace('_', ' ').title())
                with col2:
                    if details.get('description'):
                        st.write(details['description'])

def format_medical_timestamp(timestamp):
    """Format timestamp for medical records"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

def generate_case_summary(case_data):
    """Generate a concise case summary"""
    summary = []
    
    if case_data.get('patient_id'):
        summary.append(f"Patient ID: {case_data['patient_id']}")
    
    if case_data.get('symptoms'):
        symptoms = case_data['symptoms']
        if isinstance(symptoms, list):
            summary.append(f"Symptoms: {', '.join(symptoms[:3])}{'...' if len(symptoms) > 3 else ''}")
        elif isinstance(symptoms, dict):
            summary.append(f"Symptoms: {len(symptoms)} reported")
    
    if case_data.get('ai_diagnosis') and case_data['ai_diagnosis'].get('integrated_diagnosis'):
        primary = case_data['ai_diagnosis']['integrated_diagnosis'].get('primary_diagnosis')
        if primary:
            summary.append(f"AI Diagnosis: {primary}")
    
    if case_data.get('created_at'):
        date = format_medical_timestamp(case_data['created_at'])
        summary.append(f"Created: {date}")
    
    return " | ".join(summary) if summary else "Case summary unavailable"

def validate_vital_signs(vitals):
    """Validate vital signs and return warnings"""
    warnings = []
    
    if vitals.get('temperature'):
        try:
            temp = float(vitals['temperature'])
            if temp > 38.0:
                warnings.append(f"High temperature: {temp}°C (normal: 36-37.5°C)")
            elif temp < 36.0:
                warnings.append(f"Low temperature: {temp}°C (normal: 36-37.5°C)")
        except ValueError:
            warnings.append("Invalid temperature value")
    
    if vitals.get('heart_rate'):
        try:
            hr = float(vitals['heart_rate'])
            if hr > 100:
                warnings.append(f"Tachycardia: {hr} bpm (normal: 60-100 bpm)")
            elif hr < 60:
                warnings.append(f"Bradycardia: {hr} bpm (normal: 60-100 bpm)")
        except ValueError:
            warnings.append("Invalid heart rate value")
    
    if vitals.get('systolic_bp'):
        try:
            sbp = float(vitals['systolic_bp'])
            if sbp > 140:
                warnings.append(f"High systolic BP: {sbp} mmHg (normal: <120 mmHg)")
            elif sbp < 90:
                warnings.append(f"Low systolic BP: {sbp} mmHg (normal: >90 mmHg)")
        except ValueError:
            warnings.append("Invalid systolic blood pressure value")
    
    if vitals.get('oxygen_saturation'):
        try:
            spo2 = float(vitals['oxygen_saturation'])
            if spo2 < 95:
                warnings.append(f"Low oxygen saturation: {spo2}% (normal: >95%)")
        except ValueError:
            warnings.append("Invalid oxygen saturation value")
    
    return warnings

def export_case_data(case_data, format='json'):
    """Export case data in various formats"""
    if format == 'json':
        return json.dumps(case_data, indent=2, default=str)
    elif format == 'csv':
        # Flatten the data for CSV export
        flattened = {}
        for key, value in case_data.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    flattened[f"{key}_{subkey}"] = subvalue
            elif isinstance(value, list):
                flattened[key] = ', '.join(map(str, value))
            else:
                flattened[key] = value
        
        df = pd.DataFrame([flattened])
        return df.to_csv(index=False)
    else:
        return str(case_data)

def display_medical_disclaimer():
    """Display standard medical disclaimer"""
    st.markdown("""
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; 
                padding: 1rem; margin: 1rem 0; color: #856404;">
        <strong>⚠️ MEDICAL DISCLAIMER:</strong> This AI system is intended for healthcare professional 
        use only as a decision support tool. It is NOT a substitute for professional medical judgment, 
        diagnosis, or treatment. All AI-generated analyses should be verified by qualified healthcare 
        professionals. Do not use for emergency situations - contact emergency services immediately 
        for urgent medical needs.
    </div>
    """, unsafe_allow_html=True)

def calculate_risk_score(findings, clinical_data):
    """Calculate overall risk score based on findings and clinical data"""
    risk_score = 0.0
    risk_factors = []
    
    # Image findings contribution
    if findings:
        for finding, details in findings.items():
            if isinstance(details, dict) and details.get('probability'):
                prob = details['probability']
                if finding in ['pneumonia', 'pneumothorax', 'pulmonary_edema'] and prob > 0.5:
                    risk_score += prob * 0.3
                    risk_factors.append(f"{finding.replace('_', ' ').title()} ({prob:.1%})")
    
    # Clinical data contribution
    if clinical_data:
        vitals = clinical_data.get('vitals', {})
        
        # Temperature
        if vitals.get('temperature'):
            try:
                temp = float(vitals['temperature'])
                if temp > 38.0:
                    risk_score += 0.1
                    risk_factors.append(f"Fever ({temp}°C)")
            except ValueError:
                pass
        
        # Oxygen saturation
        if vitals.get('oxygen_saturation'):
            try:
                spo2 = float(vitals['oxygen_saturation'])
                if spo2 < 95:
                    risk_score += 0.2
                    risk_factors.append(f"Low SpO2 ({spo2}%)")
            except ValueError:
                pass
        
        # Heart rate
        if vitals.get('heart_rate'):
            try:
                hr = float(vitals['heart_rate'])
                if hr > 120:
                    risk_score += 0.1
                    risk_factors.append(f"Tachycardia ({hr} bpm)")
            except ValueError:
                pass
    
    # Cap risk score at 1.0
    risk_score = min(risk_score, 1.0)
    
    return risk_score, risk_factors
