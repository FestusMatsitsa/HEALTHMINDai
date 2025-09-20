import base64
import json
import os
import numpy as np
from PIL import Image, ImageEnhance
import pydicom
from io import BytesIO
import streamlit as st

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def preprocess_medical_image(image_file, target_size=(512, 512)):
    """Preprocess medical images for AI analysis"""
    try:
        if image_file.type == "application/dicom":
            # Handle DICOM files
            ds = pydicom.dcmread(image_file)
            
            # Extract pixel array
            image_array = ds.pixel_array
            
            # Handle different photometric interpretations
            if ds.PhotometricInterpretation == "MONOCHROME1":
                image_array = np.max(image_array) - image_array
                
            # Normalize to 0-255 range
            image_array = ((image_array - np.min(image_array)) / 
                          (np.max(image_array) - np.min(image_array)) * 255).astype(np.uint8)
            
            # Convert to PIL Image
            image = Image.fromarray(image_array)
            
            # Extract DICOM metadata
            metadata = {
                'patient_id': getattr(ds, 'PatientID', 'Unknown'),
                'study_date': getattr(ds, 'StudyDate', 'Unknown'),
                'modality': getattr(ds, 'Modality', 'Unknown'),
                'body_part': getattr(ds, 'BodyPartExamined', 'Unknown'),
                'view_position': getattr(ds, 'ViewPosition', 'Unknown'),
                'image_size': f"{image_array.shape[1]}x{image_array.shape[0]}"
            }
            
        else:
            # Handle regular image files
            image = Image.open(image_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            metadata = {
                'patient_id': 'Not Available',
                'study_date': 'Not Available',
                'modality': 'Unknown',
                'body_part': 'Unknown',
                'view_position': 'Unknown',
                'image_size': f"{image.size[0]}x{image.size[1]}"
            }
        
        # Resize while maintaining aspect ratio
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create new image with target size and paste original
        processed_image = Image.new('RGB', target_size, (0, 0, 0))
        offset = ((target_size[0] - image.size[0]) // 2,
                 (target_size[1] - image.size[1]) // 2)
        processed_image.paste(image, offset)
        
        # Enhance contrast for better AI analysis
        enhancer = ImageEnhance.Contrast(processed_image)
        processed_image = enhancer.enhance(1.2)
        
        return processed_image, metadata
        
    except Exception as e:
        st.error(f"Error processing medical image: {str(e)}")
        return None, None

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    try:
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    except Exception as e:
        st.error(f"Error converting image to base64: {str(e)}")
        return None

def analyze_chest_xray(image, clinical_data=None):
    """Analyze chest X-ray using OpenAI GPT-5 Vision"""
    try:
        base64_image = image_to_base64(image)
        if not base64_image:
            return None
            
        # Prepare clinical context
        clinical_context = ""
        if clinical_data:
            if clinical_data.get('symptoms'):
                clinical_context += f"Patient symptoms: {', '.join(clinical_data['symptoms'])}. "
            if clinical_data.get('vitals'):
                vitals = clinical_data['vitals']
                clinical_context += f"Vitals - Temperature: {vitals.get('temperature', 'N/A')}°C, "
                clinical_context += f"Heart Rate: {vitals.get('heart_rate', 'N/A')} bpm, "
                clinical_context += f"Blood Pressure: {vitals.get('blood_pressure', 'N/A')} mmHg, "
                clinical_context += f"SpO2: {vitals.get('oxygen_saturation', 'N/A')}%. "
            if clinical_data.get('lab_results'):
                labs = clinical_data['lab_results']
                clinical_context += f"Lab Results - WBC: {labs.get('wbc', 'N/A')}, "
                clinical_context += f"CRP: {labs.get('crp', 'N/A')}. "
        
        prompt = f"""You are an expert radiologist analyzing a chest X-ray. Provide a comprehensive analysis in JSON format with the following structure:

{{
    "findings": {{
        "pneumonia": {{"probability": float, "location": "string", "description": "string"}},
        "pneumothorax": {{"probability": float, "location": "string", "description": "string"}},
        "pleural_effusion": {{"probability": float, "location": "string", "description": "string"}},
        "cardiomegaly": {{"probability": float, "description": "string"}},
        "consolidation": {{"probability": float, "location": "string", "description": "string"}},
        "pulmonary_edema": {{"probability": float, "description": "string"}},
        "masses_nodules": {{"probability": float, "location": "string", "description": "string"}},
        "fractures": {{"probability": float, "location": "string", "description": "string"}}
    }},
    "overall_assessment": {{
        "primary_diagnosis": "string",
        "confidence": float,
        "severity": "low|moderate|high",
        "urgency": "routine|urgent|emergent"
    }},
    "differential_diagnoses": [
        {{"diagnosis": "string", "probability": float, "rationale": "string"}}
    ],
    "recommendations": [
        "string"
    ],
    "technical_quality": {{
        "image_quality": "poor|adequate|good|excellent",
        "positioning": "string",
        "inspiration": "poor|adequate|good",
        "penetration": "underpenetrated|adequate|overpenetrated"
    }},
    "key_observations": [
        "string"
    ],
    "attention_areas": [
        {{"region": "string", "description": "string", "significance": "low|moderate|high"}}
    ]
}}

{f"Clinical Context: {clinical_context}" if clinical_context else ""}

Please analyze this chest X-ray systematically, considering all anatomical structures. Provide probability scores between 0.0 and 1.0 for each finding. Focus on clinically significant abnormalities."""

        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert radiologist with extensive experience in chest X-ray interpretation. Provide thorough, accurate, and clinically relevant analyses. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=2048
        )
        
        content = response.choices[0].message.content
        if content:
            analysis = json.loads(content)
            return analysis
        return None
        
    except Exception as e:
        st.error(f"Error analyzing chest X-ray: {str(e)}")
        return None

def analyze_clinical_data(symptoms, vitals, lab_results):
    """Analyze clinical data using AI"""
    try:
        # Prepare clinical data summary
        clinical_summary = "Clinical Data Analysis:\n\n"
        
        if symptoms:
            clinical_summary += f"Symptoms: {', '.join(symptoms)}\n"
        
        if vitals:
            clinical_summary += f"Vital Signs:\n"
            for key, value in vitals.items():
                if value:
                    clinical_summary += f"  - {key.replace('_', ' ').title()}: {value}\n"
        
        if lab_results:
            clinical_summary += f"Laboratory Results:\n"
            for key, value in lab_results.items():
                if value:
                    clinical_summary += f"  - {key.upper()}: {value}\n"
        
        prompt = f"""Analyze the following clinical data and provide assessment in JSON format:

{clinical_summary}

Provide analysis in this JSON structure:
{{
    "risk_assessment": {{
        "overall_risk": "low|moderate|high|critical",
        "risk_score": float,
        "risk_factors": ["string"]
    }},
    "clinical_impressions": [
        {{"condition": "string", "probability": float, "rationale": "string"}}
    ],
    "abnormal_findings": [
        {{"parameter": "string", "value": "string", "reference_range": "string", "significance": "string"}}
    ],
    "recommendations": [
        {{"category": "immediate|short_term|long_term", "action": "string", "priority": "low|medium|high"}}
    ],
    "red_flags": [
        "string"
    ],
    "follow_up": {{
        "timeframe": "string",
        "recommended_tests": ["string"],
        "specialist_referral": "string"
    }}
}}

Focus on clinically significant patterns and provide evidence-based recommendations."""

        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert clinician analyzing patient data. Provide thorough clinical assessments with evidence-based recommendations."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=1500
        )
        
        content = response.choices[0].message.content
        if content:
            analysis = json.loads(content)
            return analysis
        return None
        
    except Exception as e:
        st.error(f"Error analyzing clinical data: {str(e)}")
        return None

def generate_multimodal_diagnosis(image_analysis, clinical_analysis, patient_data):
    """Generate comprehensive multimodal diagnosis"""
    try:
        prompt = f"""Based on the following image analysis and clinical data, provide a comprehensive multimodal diagnostic assessment:

IMAGE ANALYSIS:
{json.dumps(image_analysis, indent=2)}

CLINICAL ANALYSIS:
{json.dumps(clinical_analysis, indent=2)}

PATIENT DATA:
{json.dumps(patient_data, indent=2)}

Provide a comprehensive assessment in JSON format:
{{
    "integrated_diagnosis": {{
        "primary_diagnosis": "string",
        "confidence": float,
        "supporting_evidence": ["string"],
        "contradicting_evidence": ["string"]
    }},
    "multimodal_findings": [
        {{"finding": "string", "image_support": float, "clinical_support": float, "overall_confidence": float}}
    ],
    "clinical_correlation": {{
        "image_clinical_agreement": "strong|moderate|weak|conflicting",
        "key_correlations": ["string"],
        "discrepancies": ["string"]
    }},
    "treatment_recommendations": [
        {{"intervention": "string", "priority": "immediate|urgent|routine", "rationale": "string"}}
    ],
    "prognosis": {{
        "outlook": "excellent|good|fair|poor|critical",
        "factors": ["string"]
    }},
    "monitoring_plan": [
        {{"parameter": "string", "frequency": "string", "target": "string"}}
    ],
    "disposition": {{
        "recommended_setting": "outpatient|emergency|admission|ICU",
        "rationale": "string",
        "urgency": "immediate|within_hours|within_days|routine"
    }}
}}

Integrate findings from both imaging and clinical data to provide the most accurate assessment."""

        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior physician integrating multimodal medical data. Provide comprehensive, evidence-based diagnostic assessments that consider all available information."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=2048
        )
        
        content = response.choices[0].message.content
        if content:
            diagnosis = json.loads(content)
            return diagnosis
        return None
        
    except Exception as e:
        st.error(f"Error generating multimodal diagnosis: {str(e)}")
        return None

def generate_medical_report(case_data, image_analysis, clinical_analysis, diagnosis):
    """Generate comprehensive medical report"""
    try:
        report_data = {
            'case_info': case_data,
            'image_analysis': image_analysis,
            'clinical_analysis': clinical_analysis,
            'diagnosis': diagnosis
        }
        
        prompt = f"""Generate a comprehensive medical report based on the following data:

{json.dumps(report_data, indent=2)}

Create a professional medical report in the following format:

MEDICAL DIAGNOSTIC REPORT
=========================

PATIENT INFORMATION:
- Case ID: [case_id]
- Date of Analysis: [date]
- Clinician: [clinician_name]

CLINICAL PRESENTATION:
[Summary of symptoms, vitals, and lab results]

IMAGING FINDINGS:
[Detailed description of imaging findings with key observations]

CLINICAL CORRELATION:
[Integration of imaging and clinical data]

DIAGNOSTIC IMPRESSION:
[Primary diagnosis with differential diagnoses and confidence levels]

RECOMMENDATIONS:
[Treatment recommendations, follow-up plans, and monitoring]

URGENCY AND DISPOSITION:
[Recommended care setting and urgency level]

DISCLAIMER:
This AI-generated analysis is intended for clinical decision support only and should not replace professional medical judgment. All findings should be verified by qualified healthcare professionals.

Please provide a detailed, professional report suitable for medical documentation."""

        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical report generator creating professional, comprehensive reports for healthcare documentation."
                },
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2048
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"Error generating medical report: {str(e)}")
        return None
