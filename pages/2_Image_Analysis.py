import streamlit as st
import os
from PIL import Image
from auth import require_auth
from medical_ai import preprocess_medical_image, analyze_chest_xray, generate_multimodal_diagnosis
from database import create_medical_case, get_case_by_id, update_case
from utils import (
    display_medical_disclaimer, display_findings_summary, 
    display_confidence_score, calculate_risk_score
)
from datetime import datetime

# Require authentication
user = require_auth()
if not user:
    st.stop()

st.set_page_config(
    page_title="Image Analysis - AI Medical Assistant",
    page_icon="🔬",
    layout="wide"
)

st.markdown('<h1 style="color: #2E86AB; text-align: center;">🔬 Medical Image Analysis</h1>', 
           unsafe_allow_html=True)

display_medical_disclaimer()

# Initialize session state
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'image_analysis' not in st.session_state:
    st.session_state.image_analysis = None
if 'image_metadata' not in st.session_state:
    st.session_state.image_metadata = None

# Sidebar for image upload and controls
with st.sidebar:
    st.subheader("📤 Image Upload")
    
    uploaded_file = st.file_uploader(
        "Choose medical image",
        type=['png', 'jpg', 'jpeg', 'dcm', 'dicom'],
        help="Upload chest X-ray in PNG, JPEG, or DICOM format"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Process the image
        with st.spinner("Processing medical image..."):
            processed_image, metadata = preprocess_medical_image(uploaded_file)
            
            if processed_image:
                st.session_state.current_image = processed_image
                st.session_state.image_metadata = metadata
                st.success("✅ Image processed successfully")
            else:
                st.error("❌ Failed to process image")
    
    st.markdown("---")
    
    # Image metadata display
    if st.session_state.image_metadata:
        st.subheader("📋 Image Metadata")
        metadata = st.session_state.image_metadata
        
        for key, value in metadata.items():
            if value != 'Unknown' and value != 'Not Available':
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    st.markdown("---")
    
    # Analysis controls
    st.subheader("🤖 AI Analysis")
    
    if st.session_state.current_image:
        # Clinical context input
        include_clinical_context = st.checkbox("Include clinical context", value=False)
        
        clinical_context = {}
        if include_clinical_context:
            st.write("**Patient Symptoms:**")
            symptoms = st.multiselect(
                "Select symptoms",
                ["Cough", "Shortness of breath", "Chest pain", "Fever", 
                 "Fatigue", "Weight loss", "Night sweats", "Hemoptysis"]
            )
            if symptoms:
                clinical_context['symptoms'] = symptoms
            
            st.write("**Vital Signs:**")
            temperature = st.number_input("Temperature (°C)", min_value=35.0, max_value=42.0, step=0.1)
            if temperature > 35.0:
                clinical_context['vitals'] = {'temperature': temperature}
        
        # Analyze button
        if st.button("🔍 Analyze Image", type="primary", use_container_width=True):
            with st.spinner("Analyzing chest X-ray with AI..."):
                analysis = analyze_chest_xray(
                    st.session_state.current_image,
                    clinical_context if include_clinical_context else None
                )
                
                if analysis:
                    st.session_state.image_analysis = analysis
                    st.success("✅ Analysis complete!")
                    st.rerun()
                else:
                    st.error("❌ Analysis failed")
    else:
        st.info("Please upload an image to begin analysis")

# Main content area
if st.session_state.current_image:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🖼️ Medical Image")
        st.image(
            st.session_state.current_image,
            caption="Processed Chest X-ray",
            use_container_width=True
        )
        
        # Image controls
        st.markdown("#### Image Controls")
        col_controls1, col_controls2 = st.columns(2)
        
        with col_controls1:
            if st.button("🔍 Zoom", help="Zoom functionality"):
                st.info("Zoom feature would be implemented here")
        
        with col_controls2:
            if st.button("🎨 Adjust", help="Brightness/Contrast adjustment"):
                st.info("Adjustment controls would be implemented here")
    
    with col2:
        st.subheader("🤖 AI Analysis Results")
        
        if st.session_state.image_analysis:
            analysis = st.session_state.image_analysis
            
            # Overall assessment
            if analysis.get('overall_assessment'):
                assessment = analysis['overall_assessment']
                st.markdown("#### 🎯 Overall Assessment")
                
                col_assess1, col_assess2 = st.columns(2)
                with col_assess1:
                    st.metric("Primary Diagnosis", assessment.get('primary_diagnosis', 'Not determined'))
                    display_confidence_score(assessment.get('confidence', 0), "Overall Confidence")
                
                with col_assess2:
                    severity = assessment.get('severity', 'unknown')
                    urgency = assessment.get('urgency', 'unknown')
                    
                    # Color code severity
                    severity_colors = {
                        'low': '#28a745',
                        'moderate': '#ffc107',
                        'high': '#dc3545'
                    }
                    
                    urgency_colors = {
                        'routine': '#28a745',
                        'urgent': '#fd7e14',
                        'emergent': '#dc3545'
                    }
                    
                    st.markdown(f"""
                    <div style="text-align: center; margin: 10px 0;">
                        <div style="background-color: {severity_colors.get(severity, '#6c757d')}; 
                                    color: white; padding: 5px 10px; border-radius: 15px; 
                                    display: inline-block; margin: 5px;">
                            Severity: {severity.title()}
                        </div>
                        <div style="background-color: {urgency_colors.get(urgency, '#6c757d')}; 
                                    color: white; padding: 5px 10px; border-radius: 15px; 
                                    display: inline-block; margin: 5px;">
                            Urgency: {urgency.title()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Detailed findings
            if analysis.get('findings'):
                st.markdown("---")
                display_findings_summary(analysis['findings'])
            
            # Recommendations
            if analysis.get('recommendations'):
                st.markdown("#### 💡 Recommendations")
                for i, rec in enumerate(analysis['recommendations'], 1):
                    st.write(f"{i}. {rec}")
            
            # Technical quality
            if analysis.get('technical_quality'):
                st.markdown("---")
                st.markdown("#### 📊 Technical Quality Assessment")
                quality = analysis['technical_quality']
                
                col_tech1, col_tech2 = st.columns(2)
                with col_tech1:
                    st.write(f"**Image Quality:** {quality.get('image_quality', 'Unknown')}")
                    st.write(f"**Positioning:** {quality.get('positioning', 'Unknown')}")
                
                with col_tech2:
                    st.write(f"**Inspiration:** {quality.get('inspiration', 'Unknown')}")
                    st.write(f"**Penetration:** {quality.get('penetration', 'Unknown')}")
        else:
            st.info("No analysis results yet. Upload an image and click 'Analyze Image' to begin.")

else:
    # Welcome screen
    st.markdown("""
    ### 🔬 Welcome to AI-Powered Image Analysis
    
    This module provides advanced AI analysis of chest X-rays with:
    
    - **Multi-finding Detection**: Pneumonia, pneumothorax, pleural effusion, cardiomegaly, and more
    - **DICOM Support**: Full compatibility with medical DICOM files
    - **Confidence Scoring**: Quantified uncertainty estimates for each finding
    - **Clinical Context**: Integration with patient symptoms and vital signs
    - **Visual Explanations**: Attention maps highlighting areas of interest (coming soon)
    - **Professional Reports**: Comprehensive diagnostic summaries
    
    #### 📤 Supported Formats:
    - **DICOM** (.dcm, .dicom) - Medical imaging standard
    - **JPEG** (.jpg, .jpeg) - Common image format
    - **PNG** (.png) - Lossless image format
    
    #### 🚀 Getting Started:
    1. Upload a chest X-ray image using the sidebar
    2. Optionally add clinical context (symptoms, vitals)
    3. Click "Analyze Image" to get AI-powered insights
    4. Review findings and save to case history
    """)
    
    # Sample analysis capabilities
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 🫁 Pulmonary Findings
        - Pneumonia detection
        - Pneumothorax identification
        - Pleural effusion
        - Pulmonary edema
        - Consolidation patterns
        """)
    
    with col2:
        st.markdown("""
        #### ❤️ Cardiac Assessment
        - Cardiomegaly evaluation
        - Heart size measurements
        - Cardiac silhouette analysis
        - Vascular patterns
        """)
    
    with col3:
        st.markdown("""
        #### 🦴 Additional Findings
        - Bone fractures
        - Masses and nodules
        - Foreign objects
        - Device positioning
        - Anatomical variants
        """)

# Bottom action area
if st.session_state.image_analysis:
    st.markdown("---")
    st.subheader("💾 Save Analysis")
    
    col_save1, col_save2, col_save3 = st.columns(3)
    
    with col_save1:
        case_title = st.text_input(
            "Case Title", 
            value=f"Chest X-ray Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
    
    with col_save2:
        patient_id = st.text_input("Patient ID (optional)", placeholder="PAT001")
    
    with col_save3:
        if st.button("💾 Save Case", type="primary", use_container_width=True):
            case_data = {
                'case_title': case_title,
                'patient_id': patient_id,
                'image_filename': f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                'image_analysis': st.session_state.image_analysis,
                'ai_diagnosis': {
                    'integrated_diagnosis': st.session_state.image_analysis.get('overall_assessment', {}),
                    'findings': st.session_state.image_analysis.get('findings', {})
                },
                'confidence_scores': {
                    finding: details.get('probability', 0) 
                    for finding, details in st.session_state.image_analysis.get('findings', {}).items()
                    if isinstance(details, dict)
                },
                'recommendations': '\n'.join(st.session_state.image_analysis.get('recommendations', []))
            }
            
            case_id = create_medical_case(user['id'], case_data)
            
            if case_id:
                st.success(f"✅ Case saved successfully! Case ID: {case_id}")
                
                # Clear session state
                st.session_state.current_image = None
                st.session_state.image_analysis = None
                st.session_state.image_metadata = None
                
                if st.button("View Case History"):
                    st.switch_page("pages/4_Case_History.py")
            else:
                st.error("❌ Failed to save case. Please try again.")

# Help section
with st.expander("❓ Help & Tips"):
    st.markdown("""
    ### 📋 Usage Tips:
    
    1. **Image Quality**: Ensure good quality X-rays for best results
    2. **DICOM Files**: Preferred format for medical analysis
    3. **Clinical Context**: Adding symptoms improves accuracy
    4. **Multiple Views**: Compare PA and lateral views when available
    5. **Professional Review**: Always verify AI findings with radiologist
    
    ### 🔧 Troubleshooting:
    
    - **Upload Issues**: Check file format and size (<10MB)
    - **Processing Errors**: Try different image format
    - **Analysis Fails**: Ensure image shows chest area clearly
    - **Slow Performance**: Large images may take longer to process
    """)
