# AI-Powered Health Assistant — Full Project Documentation

> **Project name:** AI-Powered Health Assistant (Medical Diagnosis Support)

---

## 1. Executive summary

**Goal:** Build a clinically-useful, explainable system that assists clinicians by analyzing patient inputs (symptoms, structured labs, and chest X-ray / medical images) to suggest likely diagnoses, prioritized differentials, confidence scores, and recommended next steps. The system is *decision-support* (not a substitute for clinical judgement).

**Key capabilities:**
- Image analysis (e.g., chest X-rays) for findings such as pneumonia, pneumothorax, consolidation, cardiomegaly.
- Structured-data analysis (labs, vitals) to detect abnormal patterns.
- Symptom/NLP analysis from clinical notes or patient-entered text.
- Multimodal fusion to combine image + clinical data for improved accuracy.
- Explainability (Grad-CAM for images, SHAP for tabular/NLP) and uncertainty estimates.
- Web UI for clinicians with report view, heatmaps, and suggested next steps.

**Primary users:** clinicians (doctors, radiologists), triage nurses, and healthcare researchers.

**Scope & constraints:**
- Must comply with patient privacy (de-identify PHI) and local regulations (HIPAA, GDPR where applicable).
- Intended as an assistive tool — include strong disclaimers and provenance of model outputs.

---

## 2. Project objectives & success metrics

**Objectives:**
1. Achieve clinically-meaningful performance on prioritized conditions (target ROC-AUC > 0.92 for specific binary findings where dataset allows).
2. Produce interpretable visual explanations for image predictions and actionable clinical recommendations.
3. Deploy a secure prototype web app for demonstration and limited pilot testing.

**Success metrics:**
- Model-level: ROC-AUC, sensitivity, specificity, PPV, NPV, F1, calibration (Brier score), per-class recall.
- Clinical-level: reduction in missed critical findings in retrospective test, clinician satisfaction score (survey), time saved in triage.
- System-level: inference latency < 1s per image on GPU (or <5s on CPU for demo), 99.9% uptime for API.

---

## 3. Data sources & licensing (recommended)

**Image datasets:**
- NIH ChestX-ray14 — large public chest X-ray dataset with labels (useful for pretraining). Check license and citation.
- CheXpert (Stanford) — high-quality labeled chest X-rays with uncertainty labels (academic use). Requires request.
- MIMIC-CXR — paired radiology reports & images (requires credentialed access through PhysioNet and CITI training).
- Kaggle datasets (e.g., RSNA Pneumonia Detection, SIIM-ACR Pneumothorax) — for specific findings and bounding-box tasks.

**Clinical text & structured data:**
- MIMIC-IV (for tabular vitals and labs) — requires credentialed access.
- Synthetic or de-identified EHR extracts from partner clinics (recommended for pilot).

**Labeling plan:**
- Use existing dataset labels where possible (radiology report-extracted labels using CheXpert labeler).
- Expert re-reads: sample 5-10% of training/validation images to be labeled by radiologists for high-quality ground truth and to measure label noise.
- For novel local findings, set up annotation platform (e.g., MD.ai, Labelbox, or open-source DICOM annotator) and hire clinical annotators.

**Ethics & licensing:**
- Confirm dataset licenses (some academic datasets are for research only). Document citation and allowed use.
- Obtain IRB approval for any patient data used beyond public datasets. Maintain data use agreements.

---

## 4. Data pipeline & preprocessing

**4.1 Image pipeline**
- Input formats: DICOM (preferred) and PNG/JPEG.
- Steps:
  - Validate DICOM headers, extract image pixel array and orientation.
  - De-identify DICOM (strip PHI tags) or convert to PNG/JPEG for model training after de-identification.
  - Window/level normalization where needed.
  - Resize images to target resolution (e.g., 224×224 or 512×512 depending on model) while preserving aspect ratio with padding.
  - Intensity normalization (z-score per image or per-dataset normalization).
  - Data augmentation: random rotation (±10°), translation, horizontal flip (only if medically valid for the view), brightness/contrast jitter, random crop, cutout.
  - Save preprocessed tensors in TFRecords / PyTorch dataset format for fast I/O.

**4.2 Structured & clinical text**
- Map observational vocabularies (units harmonization for labs) and normalize ranges.
- Impute missing values carefully — use clinical-aware imputation (e.g., last-observation-carried-forward for time series, or missingness indicator variables).
- Encode categorical variables (one-hot, target encoding as appropriate).
- For clinical notes: de-identify PHI, run standard NLP preprocessing (lowercase, tokenization). Consider using clinical BERT/TinyBERT for encoding.

**4.3 Label handling**
- Deal with label uncertainty (CheXpert uses uncertain labels): options are ignore, map uncertain→positive, or use uncertain as separate class.
- Label smoothing for multi-label outputs if appropriate.

---

## 5. Model architecture & design

**5.1 Image-only baseline**
- Transfer learning with pre-trained CNN backbones: DenseNet-121, ResNet-50/101, EfficientNet-B3/B4.
- Replace classification head with sigmoid outputs for multi-label tasks (one output per finding).
- Add dropout, batchnorm, and/or small fully-connected (FC) layers.

**5.2 Tabular-only baseline**
- Gradient boosting (XGBoost / LightGBM / CatBoost) for labs/vitals + engineered features.
- Neural net for structured/time-series inputs (1D-CNN, LSTM, Transformer encoder for time series).

**5.3 Multimodal fusion (recommended)**
- Late fusion: produce embeddings from image encoder and tabular encoder, then concatenate and run FC layers to predict labels.
- Cross-attention fusion: use cross-attention layers to let tabular features attend to image embeddings.
- When using text (radiology report or symptoms), create a text encoder (ClinicalBERT) and include it in the fusion pipeline.

**5.4 Uncertainty & calibration**
- Use temperature scaling for post-hoc calibration.
- Consider Bayesian approximations (MC Dropout) or deep ensembles for predictive uncertainty.

**5.5 Explainability**
- Visual: Grad-CAM, Score-CAM, Integrated Gradients for image regions.
- Tabular/Text: SHAP (Kernel or Tree SHAP for boosting models), LIME for local explanations.

---

## 6. Training plan & hyperparameters

**6.1 Training procedure**
- Use transfer learning: freeze backbone for initial epochs, then unfreeze progressively.
- Optimizer: AdamW or SGD+momentum depending on backbone.
- Learning rate schedule: cosine annealing or ReduceLROnPlateau; use warmup for transformer parts.
- Batch size: choose based on GPU memory (e.g., 16–64). Use gradient accumulation if batch too small.
- Loss functions:
  - Multi-label binary cross-entropy with class weights for imbalance.
  - Focal loss as alternative when positive classes are rare.

**6.2 Regularization**
- Weight decay, dropout in heads, data augmentation (mixup, cutmix if applicable), label smoothing.

**6.3 Handling imbalance**
- Oversample minority classes or use class-weighted losses.
- Use stratified splits per patient (ensure patient-level split to avoid leakage).

**6.4 Hyperparameter tuning**
- Use Optuna or Weights & Biases sweeps for LR, weight decay, dropout, and augmentation magnitudes.
- Track results with experiment tracking (W&B, MLflow).

---

## 7. Evaluation & validation

**7.1 Data splits**
- Train / Validation / Test with patient-level separation.
- External validation: test on a different hospital dataset if possible (assess generalization).

**7.2 Metrics**
- For binary findings: ROC-AUC, PR-AUC, sensitivity (recall), specificity, PPV, NPV, F1.
- For multi-label: macro and micro averaged metrics.
- Calibration: reliability diagram, Brier score.
- Clinical utility: decision-curve analysis (net benefit at different thresholds).

**7.3 Robustness checks**
- Evaluate on subgroups: age, sex, device/vendor, view (AP vs PA), and comorbidities.
- Test susceptibility to common real-world artifacts (motion blur, low-dose images).
- Check for shortcut learning (e.g., hospital-specific tags) using attribution methods.

**7.4 Statistical significance**
- Use bootstrapping to compute confidence intervals for metrics.

---

## 8. Explainability & clinician-facing outputs

**8.1 Explainability artifacts**
- Heatmap overlay (Grad-CAM) on X-ray with adjustable opacity.
- SHAP values for tabular features showing contribution to the prediction.
- Short natural-language explanation: "Model predicts pneumonia (prob=0.87). Key evidence: consolidation in left lower lobe on image (heatmap), elevated WBC (13,200), fever 38.5°C." Use templated text to avoid overclaiming.

**8.2 UI elements for clinicians**
- Patient header (age, sex, MRN if allowed), image viewer with window/level controls, toggles for heatmaps.
- Confidence and recommended next steps (e.g., "Recommend urgent radiologist review" if high risk).
- Audit trail: show model version, training data summary, date/time of inference.

---

## 9. System architecture & deployment

**9.1 High-level architecture**
- Frontend: Streamlit / React (for polished UI). Streamlit is faster for prototyping; React + Tailwind for production-grade.
- Backend API: FastAPI serving model predictions, expose endpoints for image upload, patient data, request inference, and retrieve explanations.
- Model serving: TorchServe, TensorFlow Serving, or custom FastAPI + Uvicorn workers. Containerize with Docker.
- Data store: PostgreSQL for user and patient metadata, object storage (S3) for images and artifacts.
- Logging/monitoring: Prometheus + Grafana, ELK stack for logs. W&B for experiment tracking.

**9.2 Deployment options**
- Cloud: AWS (ECS/EKS + S3 + RDS), GCP (GKE + GCS), or Azure. For HIPAA, choose compliant offerings (AWS HIPAA-eligible services).
- On-prem: Kubernetes cluster with GPU nodes for inference in hospitals needing data to remain onsite.

**9.3 CI/CD & reproducibility**
- Container builds via GitHub Actions or GitLab CI; run unit tests and model integration tests.
- Store model artifacts and metadata in a model registry (MLflow or Hugging Face Hub private repo).

---

## 10. Security, privacy & compliance

**10.1 Data security**
- Encrypt data at rest and in transit (TLS). Use KMS for keys.
- RBAC for system users; audit logs for access to patient data.

**10.2 Privacy & de-identification**
- Remove or hash PHI fields in DICOM (name, MRN, DOB). Use deterministic hashing only where necessary.
- Consider synthetic data augmentation where real data is limited.

**10.3 Regulatory considerations**
- In many jurisdictions this is a medical device if used clinically — consult regulatory experts (FDA, CE) before clinical deployment.
- Keep extensive documentation of training data, versioning, intended use, and validation results for regulatory submissions.

---

## 11. Monitoring & maintenance post-deployment

**11.1 Model monitoring**
- Track data drift for inputs (covariate shift) and concept drift for labels.
- Monitor model performance over time and alert when metrics degrade beyond thresholds.

**11.2 Feedback loop**
- Enable clinicians to flag incorrect predictions; capture flagged cases for re-labeling and retraining.
- Schedule periodic retraining with new labeled data; use controlled rollouts and A/B testing.

**11.3 Versioning & rollback**
- Tag model versions with semantic versioning. Keep the ability to rollback swiftly to previous stable model.

---

## 12. Implementation roadmap & timeline (example)

**Phase 0 — Planning (2 weeks)**
- Stakeholder interviews, data access agreements, IRB if needed, success criteria.

**Phase 1 — Data & baseline models (6–8 weeks)**
- Acquire datasets, implement preprocessing, train image-only and tabular-only baselines.

**Phase 2 — Multimodal model & explainability (6–8 weeks)**
- Implement multimodal fusion, integrate explainability methods, internal validation.

**Phase 3 — UI & prototype deployment (4 weeks)**
- Build Streamlit/React UI, backend API, containerize, test inference performance.

**Phase 4 — Pilot testing & iterating (8–12 weeks)**
- Deploy to pilot site (with oversight), collect clinician feedback, refine model and UX.

**Phase 5 — Regulatory readiness & scale-up (variable)**
- Document, run prospective validation, submit for regulatory review if intended for clinical use.

---

## 13. Folder structure & sample files

```
health-assistant/
├── data/                  # raw and preprocessed datasets (DO NOT store PHI here publicly)
│   ├── raw/
│   └── processed/
├── notebooks/             # EDA and prototyping notebooks
├── src/
│   ├── data/              # preprocessing scripts
│   ├── models/            # model definitions and training loops
│   ├── api/               # FastAPI app
│   ├── webapp/            # Streamlit or React frontend
│   └── utils/             # helpers (logging, config)
├── experiments/           # tracked experiments (W&B links)
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── environment.yml
└── README.md
```

**Sample `config.yml`**

```yaml
model:
  backbone: densenet121
  input_size: 224
training:
  lr: 1e-4
  batch_size: 32
  epochs: 30
data:
  img_dir: data/processed/images
  labels: data/processed/labels.csv
```

---

## 14. API spec (simplified)

**POST /infer**
- Description: Run inference on a new patient case.
- Request body (multipart/form-data): `image_file` (DICOM/PNG), `patient_id` (optional), `metadata` (JSON with age, sex, vitals, labs).
- Response (JSON):
```json
{
  "predictions": [{"finding": "pneumonia", "prob": 0.87}, ...],
  "explanations": {"heatmap_url": "s3://.../heatmap.png", "shap_summary": {"WBC": 0.12}},
  "model_version": "v1.3.0"
}
```

**GET /model/metadata**
- Return model version, training data summary, date.

**POST /feedback**
- Collect clinician feedback (case id, true label, comments).

---

## 15. Example code snippets (training & inference)

> Code below is illustrative. Move to `src/` and adapt to your code style.

**PyTorch model skeleton (image)**

```python
import torch
import torch.nn as nn
from torchvision import models

class ImageModel(nn.Module):
    def __init__(self, backbone='densenet121', num_classes=14):
        super().__init__()
        self.backbone = models.densenet121(pretrained=True)
        in_features = self.backbone.classifier.in_features
        self.backbone.classifier = nn.Identity()
        self.head = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(512, num_classes)
        )
    def forward(self, x):
        feat = self.backbone(x)
        out = self.head(feat)
        return out
```

**FastAPI inference endpoint (simplified)**

```python
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

app = FastAPI()

@app.post('/infer')
async def infer(file: UploadFile = File(...), metadata: dict = None):
    # load image, preprocess, run model, return json
    return {"predictions": [{"finding": "pneumonia", "prob": 0.87}], "model_version": "v1"}
```

---

## 16. Ethical considerations & bias mitigation

- **Bias sources:** training data skew (e.g., one hospital, one ethnicity, device vendor) can lead to reduced performance for underrepresented groups.
- **Mitigations:** audit performance per subgroup; include diverse datasets; use fairness-aware reweighting if required.
- **Transparency:** publish model card with intended use, limitations, performance across subgroups, and caveats.
- **Human oversight:** ensure workflows route ambiguous or critical cases to human experts.

---

## 17. Documentation & reproducibility artifacts

- Model card (text explaining model scope and limitations).
- Datasheet for datasets used.
- README with step-by-step setup and run instructions.
- Reproducible environment files (`environment.yml` / `requirements.txt`), seeds in code, and saved checkpoints.

---

## 18. Risks & mitigations

- **Clinical risk:** false negatives for critical conditions — mitigate by conservative thresholds for triage and human-in-the-loop design.
- **Data breaches:** enforce strict access control and encryption.
- **Regulatory risk:** consult legal/regulatory experts early.

---

## 19. Appendices

**A. Useful links & references**
- NIH ChestX-ray14: https://nihcc.app.box.com/v/ChestXray-NIHCC
- CheXpert: https://stanfordmlgroup.github.io/competitions/chexpert/
- MIMIC-CXR: https://physionet.org/content/mimic-cxr/
- Grad-CAM paper, SHAP docs, and relevant model zoo links.

**B. Checklist before clinical pilot**
- IRB approvals & DUAs
- Data de-identification pipeline validated
- Clinician training on system use
- Logging and rollback plans

---

# End of document


*If you'd like, I can now:*
- Provide a ready-to-run starter repo (code + small notebook) for the image-only baseline.
- Generate a Streamlit prototype UI that calls a mock inference API.
- Create a slide deck summarizing this documentation for stakeholders.

Tell me which one you'd like next and I’ll produce it.

