# `ARCHITECTURE.md`

````markdown
# MediSetu — Complete System Architecture

> This document is the authoritative technical architecture for the MediSetu project.
>
> Any developer or AI coding agent working on the project MUST read this file before making architectural or implementation decisions.
>
> The objective is to build a complete, working prototype covering the full patient → doctor → prescription → pharmacy workflow, including multilingual AI-assisted intake, document digitization, doctor-to-doctor referrals, patient history, authentication, auditing, and external-system integration boundaries.
>
> This is a hackathon prototype, not a production-certified clinical system. However, the architecture must be designed cleanly enough that the prototype behaves like a coherent real-world system rather than a collection of disconnected demos.

---

# 1. PROJECT OVERVIEW

## 1.1 Product

MediSetu is an AI-powered pre-consultation and clinical workflow platform for hospitals.

The system allows a patient to independently provide their medical history through voice and touchscreen interaction before meeting the doctor.

The system can:

1. Collect patient information.
2. Conduct a multilingual conversational history-taking process.
3. Convert speech into text.
4. Extract structured clinical information.
5. Ask adaptive follow-up questions.
6. Detect potential red-flag symptoms for triage.
7. Digitize previous medical documents.
8. Extract useful information from those documents.
9. Generate a structured physician-ready history summary.
10. Allow the doctor to review, edit, accept, or reject AI-generated information.
11. Allow the doctor to make the actual diagnosis.
12. Allow the doctor to prescribe medicines.
13. Check medicine availability in the pharmacy.
14. Reserve available medicines.
15. Send the prescription/order to the pharmacy.
16. Allow pharmacy staff to prepare the order.
17. Allow the patient to collect the medicine without waiting in the normal queue.
18. Allow one doctor to refer a case to another doctor.
19. Maintain a chronological patient medical timeline.
20. Maintain appropriate audit records.
21. Provide integration boundaries for HIS/EMR and ABHA/ABDM systems.

---

# 2. FUNDAMENTAL CLINICAL PRINCIPLE

The system is NOT an autonomous medical decision-maker.

The AI is used for:

- information collection
- transcription
- translation
- clinical information extraction
- summarization
- document extraction
- missing-information identification
- decision support
- workflow assistance

The AI must NOT independently:

- diagnose a patient
- finalize a diagnosis
- prescribe medication
- finalize treatment
- modify doctor-confirmed clinical information
- modify pharmacy inventory
- dispense medication

The authoritative clinical workflow is:

```text
Patient
   |
   v
AI-assisted information collection
   |
   v
Structured clinical information
   |
   v
Doctor review
   |
   v
Doctor modifies/confirms information
   |
   v
Doctor diagnosis
   |
   v
Doctor prescription
   |
   v
Pharmacy workflow
````

The doctor remains the final clinical authority.

---

# 3. SYSTEM OBJECTIVES

The architecture must satisfy the following objectives.

## 3.1 Patient-side objectives

* Minimal training required.
* Voice-first interaction.
* Touch/text alternative.
* Multilingual operation.
* Accessibility for elderly and low-literacy users.
* Audio guidance.
* Large text/high contrast mode.
* Simple navigation.
* Ability to scan/upload previous documents.
* Ability to review personal medical history.

## 3.2 Doctor-side objectives

* See the patient's collected history before or at consultation.
* Quickly review AI-generated information.
* Correct incorrect information.
* Add missing information.
* Approve the history.
* Enter diagnosis.
* Select medicines.
* Check actual pharmacy availability.
* Create prescriptions.
* Refer cases to other doctors.
* View previous consultations and relevant medical history.

## 3.3 Pharmacy objectives

* Maintain medicine inventory.
* View current stock.
* Receive doctor-confirmed prescriptions.
* Reserve stock.
* Prepare medicine orders.
* Mark orders ready for pickup.
* Dispense medicines.
* Automatically update stock.
* Maintain inventory transaction history.

## 3.4 System objectives

* Secure authentication.
* Role-based authorization.
* Persistent database.
* Audit logging.
* Clear API contracts.
* Modular AI integration.
* Modular external-system integration.
* Automated testing.
* Reliable error handling.

---

# 4. HIGH-LEVEL ARCHITECTURE

```text
                         ┌───────────────────────┐
                         │       PATIENT         │
                         │  Kiosk / Web / Mobile │
                         └───────────┬───────────┘
                                     │
                                     v
                         ┌───────────────────────┐
                         │       FRONTEND        │
                         │ React + TypeScript    │
                         └───────────┬───────────┘
                                     │
                              REST / HTTPS
                                     │
                                     v
┌─────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                         │
│                                                                 │
│  Authentication / Authorization                                 │
│  Patient Management                                             │
│  Consultation Management                                        │
│  Clinical History                                               │
│  AI Integration                                                 │
│  Document Processing                                            │
│  Doctor Workflow                                                │
│  Referral Workflow                                              │
│  Prescription Workflow                                          │
│  Pharmacy Workflow                                              │
│  Patient Timeline                                               │
│  Audit Logging                                                  │
│  External Integration Adapters                                  │
└───────────────┬─────────────────────┬───────────────────────────┘
                │                     │
                v                     v
      ┌──────────────────┐   ┌──────────────────────┐
      │   PostgreSQL     │   │     AI SERVICES      │
      │                  │   │                      │
      │ Patients         │   │ STT                  │
      │ Consultations    │   │ LLM                  │
      │ Clinical data    │   │ OCR                  │
      │ Prescriptions    │   │ TTS                  │
      │ Inventory        │   │ Extraction           │
      │ Referrals        │   └──────────────────────┘
      │ Audit logs       │
      └──────────────────┘

                │
                v
      ┌──────────────────────┐
      │ EXTERNAL INTEGRATION  │
      │                       │
      │ HIS / EMR             │
      │ ABHA / ABDM           │
      └──────────────────────┘
```

---

# 5. ARCHITECTURAL STYLE

Use a modular monolithic backend.

Do NOT create microservices unless a concrete requirement emerges.

The prototype should use:

```text
React frontend
       |
       v
FastAPI modular backend
       |
       v
PostgreSQL
```

AI and external services are accessed through service/adaptor interfaces.

This provides the simplicity of a monolith while keeping modules sufficiently separated for future extraction if required.

---

# 6. TECHNOLOGY STACK

## 6.1 Frontend

Preferred:

* React
* TypeScript
* Vite or Next.js
* Tailwind CSS

The frontend must communicate with the backend through documented REST APIs.

Frontend must NOT directly access PostgreSQL.

Frontend must NOT contain security-sensitive business logic.

---

# 7. BACKEND

Use:

* Python 3.x
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* PostgreSQL
* Pytest

Recommended supporting libraries may be selected by the implementation agent where appropriate.

The backend must be asynchronous where useful, but simplicity is preferred over unnecessary complexity.

---

# 8. DATABASE

Use PostgreSQL as the primary persistent database.

The database is the authoritative source of truth for:

* users
* patients
* doctors
* consultations
* clinical records
* prescriptions
* medicines
* inventory
* pharmacy orders
* referrals
* audit records

AI output is NOT authoritative.

Frontend state is NOT authoritative.

---

# 9. REPOSITORY STRUCTURE

The project should follow a structure similar to:

```text
/
├── frontend/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── patients.py
│   │   │   ├── consultations.py
│   │   │   ├── clinical_history.py
│   │   │   ├── documents.py
│   │   │   ├── referrals.py
│   │   │   ├── prescriptions.py
│   │   │   ├── medicines.py
│   │   │   ├── pharmacy.py
│   │   │   └── timeline.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   │
│   │   ├── database/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── patient_service.py
│   │   │   ├── consultation_service.py
│   │   │   ├── clinical_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── stt_service.py
│   │   │   ├── tts_service.py
│   │   │   ├── ocr_service.py
│   │   │   ├── referral_service.py
│   │   │   ├── prescription_service.py
│   │   │   ├── inventory_service.py
│   │   │   ├── pharmacy_service.py
│   │   │   ├── abha_service.py
│   │   │   └── his_service.py
│   │   │
│   │   ├── middleware/
│   │   └── utils/
│   │
│   ├── tests/
│   │
│   ├── requirements.txt
│   └── alembic.ini
│
├── ai/
│   ├── prompts/
│   ├── schemas/
│   └── README.md
│
├── docs/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
└── CURRENT_STATE.md
```

The exact organization may be improved during implementation, but responsibilities must remain modular.

---

# 10. USER ROLES

The system supports:

```text
PATIENT
DOCTOR
PHARMACY
NURSE
ADMIN
```

Roles must be enforced by the backend.

Frontend-only access restrictions are insufficient.

---

# 11. AUTHENTICATION

Use JWT-based authentication for the prototype.

Required:

* registration where appropriate
* login
* token generation
* token validation
* password hashing
* protected routes
* role-based authorization

Passwords must never be stored in plaintext.

Secrets must come from environment variables.

---

# 12. ROLE-BASED ACCESS CONTROL

## Patient

Can:

* access their own profile
* provide medical history
* complete pre-consultation
* upload documents
* view permitted personal records
* view prescriptions
* view pharmacy pickup status

Cannot:

* access another patient
* modify doctor-confirmed diagnosis
* modify prescriptions
* modify pharmacy inventory
* access another doctor's private workflow

## Doctor

Can:

* access authorized patient cases
* review clinical history
* edit AI-generated information
* approve clinical history
* record diagnosis
* create prescriptions
* view medicine availability
* create referrals
* receive referrals
* review previous records

## Pharmacy

Can:

* access pharmacy inventory
* view authorized prescriptions
* reserve medicines
* prepare orders
* mark ready for pickup
* dispense medicines
* update inventory

Cannot:

* diagnose patients
* create prescriptions
* modify clinical diagnosis

## Nurse

Can access workflows explicitly assigned to nurses, such as triage and patient intake support.

## Admin

Can:

* manage users
* manage system configuration
* view system-level audit information
* manage master data where appropriate

---

# 13. PATIENT MODEL

Patient information should include appropriate fields such as:

```text
patient_id
user_id
name
date_of_birth
age
sex
contact_information
preferred_language
abha_id
created_at
updated_at
```

Sensitive fields must be protected.

Avoid unnecessary duplication of patient data.

---

# 14. DOCTOR MODEL

Doctor information:

```text
doctor_id
user_id
name
department
specialization
registration_number
availability/status
created_at
updated_at
```

---

# 15. CONSULTATION MODEL

A consultation represents a clinical encounter.

Example states:

```text
CREATED
IN_PROGRESS
AI_PROCESSING
UNDER_REVIEW
APPROVED
COMPLETED
CANCELLED
```

Fields should include:

```text
consultation_id
patient_id
doctor_id
status
started_at
completed_at
created_at
updated_at
```

Doctor assignment may initially be optional for pre-consultation.

---

# 16. PATIENT INTAKE WORKFLOW

Primary patient workflow:

```text
Identify patient
      |
      v
Select language
      |
      v
Consent
      |
      v
Begin intake
      |
      v
Chief complaint
      |
      v
Adaptive questions
      |
      v
Voice/touch responses
      |
      v
Speech-to-text
      |
      v
Clinical extraction
      |
      v
Missing information detection
      |
      v
Additional questions
      |
      v
Structured clinical history
      |
      v
Document upload
      |
      v
Document processing
      |
      v
Clinical summary
      |
      v
Doctor review
```

---

# 17. CONVERSATIONAL AI ENGINE

The conversational engine must support adaptive questioning.

It should not use a completely fixed questionnaire for every patient.

Example:

```text
Patient:
"I have chest pain."

AI:
"When did the pain begin?"

Patient:
"Yesterday."

AI:
"Where exactly do you feel the pain?"

Patient:
"Center of my chest."

AI:
"Does the pain spread to your arm, shoulder, jaw, or back?"
```

The next question should be influenced by previous responses.

---

# 18. CLINICAL HISTORY STRUCTURE

The structured clinical record should support:

```text
Chief Complaint
History of Present Illness
Onset
Duration
Location
Character
Severity
Timing
Aggravating Factors
Relieving Factors
Associated Symptoms
Past Medical History
Past Surgical History
Medication History
Allergies
Family History
Personal History
Social History
Review of Systems
Previous Investigations
Relevant Negatives
Patient Concerns
Missing Information
AI Flags
```

---

# 19. AI DATA INTEGRITY

The AI must never fabricate information.

If the patient has not provided a value:

```text
unknown
```

or:

```text
missing_information
```

must be used.

Never infer a medical fact simply because it is clinically plausible.

Example:

Patient says:

> "I take a tablet for blood pressure."

The AI must NOT automatically convert that into:

```text
Amlodipine 5mg
```

unless the information was actually provided or extracted from a reliable document.

---

# 20. AI STRUCTURED OUTPUT

The AI should return structured JSON.

Example:

```json
{
  "chief_complaint": "Chest pain",
  "history_present_illness": {
    "onset": "Yesterday",
    "location": "Central chest",
    "severity": null,
    "character": null,
    "duration": null,
    "aggravating_factors": [],
    "relieving_factors": [],
    "associated_symptoms": []
  },
  "past_medical_history": [],
  "past_surgical_history": [],
  "medications": [],
  "allergies": [],
  "family_history": [],
  "personal_history": [],
  "review_of_systems": {},
  "relevant_negatives": [],
  "patient_concerns": [],
  "missing_information": [
    "pain severity",
    "pain character",
    "associated symptoms"
  ],
  "ai_flags": []
}
```

Pydantic schemas must validate AI output before it is stored.

---

# 21. RED-FLAG DETECTION

The intake engine should identify configured emergency/red-flag patterns.

Examples may include:

* severe chest pain
* breathing difficulty
* stroke-like symptoms
* loss of consciousness
* severe bleeding
* other configured emergency indicators

Red-flag detection must result in:

```text
TRIAGE ALERT
```

to the appropriate hospital workflow.

It must NOT claim:

```text
"This patient has condition X."
```

Instead:

```text
"Potential emergency symptom detected — immediate clinical assessment recommended."
```

The system must never replace emergency medical assessment.

---

# 22. MULTILINGUAL SUPPORT

Target languages include:

```text
English
Malayalam
Hindi
Tamil
Telugu
Kannada
Bengali
Marathi
Gujarati
```

The implementation should support expansion to additional languages.

The system should tolerate code-switching.

Example:

```text
"Doctor, ഇന്നലെ മുതൽ stomach pain ആണ്."
```

The original transcript should be preserved.

A canonical structured representation can be stored in English.

---

# 23. SPEECH-TO-TEXT ARCHITECTURE

```text
Audio
  |
  v
Audio validation
  |
  v
Speech-to-text provider
  |
  v
Transcript
  |
  v
Language metadata
  |
  v
Clinical extraction
```

STT must be abstracted behind:

```text
STTService
```

so the implementation can switch providers without changing clinical business logic.

---

# 24. TEXT-TO-SPEECH

TTS should support patient-facing responses.

Architecture:

```text
Clinical/Conversation response
          |
          v
Language selection
          |
          v
TTS Service
          |
          v
Audio
```

TTS provider must be abstracted.

---

# 25. DOCUMENT DIGITIZATION

Supported document types include:

* prescriptions
* laboratory reports
* discharge summaries
* imaging reports
* other medical records

Pipeline:

```text
Uploaded document
       |
       v
File validation
       |
       v
OCR
       |
       v
Extracted text
       |
       v
Medical information extraction
       |
       v
Structured document record
       |
       v
Timeline
```

The original document must be preserved.

---

# 26. OCR EXTRACTION

Where possible, extract:

```text
document date
hospital/clinic
diagnoses explicitly stated
medicines
dosages
investigation names
investigation values
reference ranges
procedures
surgical history
```

Do not invent missing information.

---

# 27. DOCUMENT ABNORMALITY FLAGS

The system may flag:

* laboratory values outside supplied reference ranges
* possible medication conflicts
* missing information

These are attention flags only.

The system must NOT claim that an abnormal value proves a diagnosis.

---

# 28. CLINICAL SUMMARY GENERATOR

The summary should be organized as:

```text
Chief Complaint
HPI
Past Medical History
Past Surgical History
Medications
Allergies
Family History
Personal/Social History
Review of Systems
Prior Investigations
Relevant Documents
Missing Information
AI Flags
```

The summary must be editable.

---

# 29. DOCTOR REVIEW

The doctor sees:

```text
Original patient information
+
AI-generated structured history
+
Digitized previous records
```

The doctor can:

* edit
* delete
* add
* confirm
* reject

The system should preserve:

```text
AI-generated version
Doctor-modified version
Doctor-confirmed version
```

where practical.

---

# 30. DIAGNOSIS

Only an authorized doctor may finalize a diagnosis.

Example:

```text
Doctor reviews history
        |
        v
Doctor examination
        |
        v
Doctor diagnosis
        |
        v
Diagnosis stored
```

The AI may provide information or decision-support suggestions, but diagnosis remains a doctor action.

---

# 31. PRESCRIPTION WORKFLOW

```text
Doctor
  |
  v
Diagnosis
  |
  v
Select medicine
  |
  v
Check pharmacy stock
  |
  v
Select available medicine
  |
  v
Enter dosage/frequency/duration
  |
  v
Doctor confirms prescription
  |
  v
Stock reservation
  |
  v
Pharmacy order
```

Only a doctor can finalize a prescription.

---

# 32. MEDICINE MODEL

Medicine master data should include:

```text
medicine_id
generic_name
brand_name
strength
dosage_form
manufacturer
unit
active/inactive
created_at
updated_at
```

---

# 33. INVENTORY MODEL

Inventory should support:

```text
inventory_id
medicine_id
batch_number
quantity
reserved_quantity
expiry_date
location
created_at
updated_at
```

Available stock:

```text
available_quantity =
quantity - reserved_quantity
```

Expired stock must never be considered available.

---

# 34. INVENTORY TRANSACTIONS

Every important inventory change should create a transaction.

Examples:

```text
STOCK_ADDED
STOCK_RESERVED
STOCK_RELEASED
STOCK_DISPENSED
STOCK_ADJUSTED
STOCK_EXPIRED
```

This allows the system to explain how inventory changed.

---

# 35. STOCK RESERVATION

When a doctor confirms a prescription:

```text
Check stock
    |
    v
Validate expiry
    |
    v
Validate available quantity
    |
    v
Reserve quantity
    |
    v
Create pharmacy order
```

Reservation and inventory updates must be handled transactionally.

The system must prevent double reservation where possible.

---

# 36. PHARMACY WORKFLOW

```text
Prescription confirmed
        |
        v
Stock reserved
        |
        v
Pharmacy order created
        |
        v
Pharmacy dashboard
        |
        v
Pharmacy prepares medicines
        |
        v
READY_FOR_PICKUP
        |
        v
Patient arrives
        |
        v
Pharmacy verifies order
        |
        v
Medicine dispensed
        |
        v
DISPENSED
```

---

# 37. PHARMACY ORDER STATES

Use:

```text
PENDING
RESERVED
PREPARING
READY_FOR_PICKUP
DISPENSED
CANCELLED
EXPIRED
```

State transitions must be validated by the backend.

---

# 38. DOCTOR-TO-DOCTOR REFERRAL

Doctors must be able to send cases to other doctors.

Workflow:

```text
Doctor A
   |
   v
Select patient/case
   |
   v
Select Doctor B
   |
   v
Referral reason
   |
   v
Attach relevant case information
   |
   v
Referral created
   |
   v
Doctor B notified
   |
   v
Doctor B accepts/declines
   |
   v
Doctor B reviews case
   |
   v
Consultation
```

---

# 39. REFERRAL MODEL

Fields:

```text
referral_id
patient_id
consultation_id
from_doctor_id
to_doctor_id
reason
priority
clinical_summary
status
created_at
updated_at
```

Statuses:

```text
PENDING
ACCEPTED
DECLINED
IN_REVIEW
COMPLETED
CANCELLED
```

Only authorized doctors may access referrals assigned to them.

---

# 40. PATIENT TIMELINE

The patient timeline should combine events such as:

```text
Registration
Consultation
AI Intake
Doctor Review
Diagnosis
Prescription
Referral
Document
Pharmacy Order
Medicine Dispensed
```

Example:

```text
01 Sep
Consultation
     |
     v
01 Sep
Clinical history completed
     |
     v
01 Sep
Doctor review
     |
     v
01 Sep
Diagnosis
     |
     v
01 Sep
Prescription
     |
     v
01 Sep
Medicine reserved
     |
     v
01 Sep
Ready for pickup
     |
     v
02 Sep
Dispensed
```

Timeline entries should reference their source records.

Do not duplicate entire records merely to create the timeline.

---

# 41. MEDICAL DOCUMENT STORAGE

Original documents must be stored separately from extracted structured information.

Example:

```text
MedicalDocument
    |
    +-- original_file
    |
    +-- extracted_text
    |
    +-- structured_information
    |
    +-- processing_status
```

Processing states:

```text
UPLOADED
PROCESSING
PROCESSED
FAILED
REVIEW_REQUIRED
```

---

# 42. AI SERVICE ARCHITECTURE

AI providers must be abstracted.

Example interfaces:

```text
STTService
TTSService
LLMService
OCRService
ClinicalExtractionService
SummaryService
```

Business logic must not directly depend on one provider.

Example:

```text
ClinicalService
      |
      v
ClinicalExtractionService
      |
      v
LLM Provider
```

not:

```text
ClinicalService
      |
      v
Direct OpenAI/Gemini/etc. call
```

Provider selection must be configurable.

---

# 43. AI FAILURE HANDLING

AI calls can fail.

The system must handle:

* timeout
* provider unavailable
* invalid response
* malformed JSON
* low-quality transcription
* OCR failure
* rate limits

The patient/doctor must receive a useful fallback.

Example:

```text
AI unavailable
     |
     v
Manual entry available
```

AI failure must never corrupt the patient's medical record.

---

# 44. AI CONFIDENCE

Where confidence scores are technically available, they may be stored as metadata.

However:

```text
confidence != clinical certainty
```

Never present an AI confidence value as a diagnosis probability.

---

# 45. EXTERNAL HIS INTEGRATION

The system should expose an adapter:

```text
HISService
```

The internal system should not be tightly coupled to a particular HIS.

Example:

```text
MediSetu
    |
    v
HISService interface
    |
    +---- Mock HIS adapter
    |
    +---- Real HIS adapter
```

The hackathon prototype may use a mock adapter if real credentials/API access are unavailable.

---

# 46. ABHA / ABDM INTEGRATION

Create:

```text
ABHAService
```

behind an adapter.

The system should support the conceptual flow:

```text
Patient identity
      |
      v
ABHA identity
      |
      v
Consent
      |
      v
Health record sharing
```

Do not hard-code assumptions about live ABDM infrastructure.

If real integration is unavailable during development, implement a realistic mock/sandbox interface.

---

# 47. FHIR

Where appropriate, internal clinical resources should be mappable to FHIR-compatible structures.

Potential mappings include:

```text
Patient
Encounter
Condition
MedicationRequest
Medication
DocumentReference
Observation
Practitioner
```

FHIR mapping should be isolated from core business logic.

---

# 48. CONSENT

Patient data sharing must be consent-aware.

Consent should record:

```text
consent_id
patient_id
purpose
scope
status
granted_at
revoked_at
```

Possible states:

```text
GRANTED
REVOKED
EXPIRED
```

Consent requirements should be enforced where relevant.

---

# 49. PRIVACY

Development must use synthetic patient data.

Do not commit real patient information to Git.

Sensitive data must not appear in:

* source code
* logs
* test fixtures
* Git history
* public repositories

unless intentionally anonymized/synthetic.

---

# 50. AUDIT LOGGING

Record important actions.

Examples:

```text
LOGIN
LOGOUT
PATIENT_CREATED
PATIENT_ACCESSED
CONSULTATION_CREATED
AI_PROCESSING_STARTED
AI_SUMMARY_GENERATED
AI_SUMMARY_EDITED
CLINICAL_SUMMARY_APPROVED
DIAGNOSIS_CREATED
PRESCRIPTION_CREATED
PRESCRIPTION_CONFIRMED
REFERRAL_CREATED
REFERRAL_ACCEPTED
REFERRAL_DECLINED
STOCK_ADDED
STOCK_RESERVED
STOCK_RELEASED
MEDICINE_DISPENSED
DOCUMENT_UPLOADED
DOCUMENT_ACCESSED
```

Audit record:

```text
audit_id
user_id
action
resource_type
resource_id
timestamp
metadata
```

Audit logs should not be casually editable.

---

# 51. API DESIGN

REST APIs should use:

```text
/api/auth
/api/users
/api/patients
/api/consultations
/api/clinical-history
/api/documents
/api/referrals
/api/prescriptions
/api/medicines
/api/pharmacy
/api/timeline
```

Use appropriate HTTP methods.

Examples:

```text
GET
POST
PUT
PATCH
DELETE
```

Do not expose DELETE operations for clinically important records unless there is a justified archival/deactivation design.

Prefer status changes and soft deletion where appropriate.

---

# 52. API RESPONSE FORMAT

Responses should be consistent.

Example:

```json
{
  "success": true,
  "data": {},
  "message": null
}
```

Errors should contain useful information without leaking internal implementation details.

Example:

```json
{
  "success": false,
  "error": {
    "code": "MEDICINE_OUT_OF_STOCK",
    "message": "The requested medicine is currently unavailable."
  }
}
```

---

# 53. VALIDATION

Validate at multiple levels:

```text
Frontend validation
        |
        v
Pydantic request validation
        |
        v
Business validation
        |
        v
Database constraints
```

Never rely on frontend validation alone.

---

# 54. DATABASE INTEGRITY

Use:

* foreign keys
* unique constraints
* check constraints where useful
* transactions
* indexes
* appropriate cascading rules

Do not allow orphaned clinical records.

---

# 55. TRANSACTIONAL WORKFLOWS

The following should be atomic where appropriate:

## Prescription + stock reservation

```text
Validate prescription
      |
      v
Check available inventory
      |
      v
Reserve inventory
      |
      v
Create pharmacy order
```

If any critical step fails, the transaction should roll back.

## Dispensing

```text
Validate order
      |
      v
Validate reserved stock
      |
      v
Reduce stock
      |
      v
Mark order DISPENSED
      |
      v
Create audit event
```

---

# 56. CONCURRENCY

Inventory operations must consider concurrent requests.

Example:

Two prescriptions request the final 5 units of a medicine.

The system must not allow both prescriptions to reserve the same stock.

Use appropriate database transaction/isolation/locking mechanisms.

---

# 57. ERROR HANDLING

The backend must provide centralized error handling.

Handle:

* authentication failures
* authorization failures
* validation errors
* missing records
* database errors
* AI failures
* OCR failures
* external API failures
* inventory conflicts
* invalid state transitions

Do not expose stack traces to end users.

---

# 58. LOGGING

Application logs should include:

* timestamp
* severity
* module
* event
* request correlation identifier where practical

Do not log:

* passwords
* JWT secrets
* API keys
* unnecessary patient-sensitive information

---

# 59. FILE UPLOAD SECURITY

Uploaded documents/audio must be validated.

Validate:

* file type
* file size
* filename
* extension
* content where possible

Do not trust client-provided MIME types blindly.

---

# 60. CONFIGURATION

Use environment variables.

Example:

```env
DATABASE_URL=
JWT_SECRET=
JWT_ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=

LLM_PROVIDER=
LLM_API_KEY=

STT_PROVIDER=
STT_API_KEY=

TTS_PROVIDER=
TTS_API_KEY=

OCR_PROVIDER=
OCR_API_KEY=

ABHA_BASE_URL=
ABHA_CLIENT_ID=
ABHA_CLIENT_SECRET=

HIS_BASE_URL=
HIS_API_KEY=

ENVIRONMENT=development
```

Never commit `.env`.

Provide:

```text
.env.example
```

---

# 61. FRONTEND INTEGRATION

The frontend should use an API client layer.

Do not scatter raw HTTP requests throughout components.

Preferred:

```text
frontend
  |
  v
api/
  |
  v
backend
```

The frontend should handle:

* loading states
* errors
* authentication
* session expiration
* form validation
* accessibility
* responsive layouts

---

# 62. PATIENT FRONTEND

Required screens/features:

```text
Login / Identification
Language Selection
Consent
Patient Profile
AI Intake
Voice Interaction
Text/Touch Interaction
Document Upload
Intake Summary
History
Prescription Status
Pharmacy Pickup Status
```

---

# 63. DOCTOR FRONTEND

Required screens:

```text
Login
Doctor Dashboard
Patient Queue
Patient Profile
Clinical History
AI Summary
Document Viewer
Doctor Review
Diagnosis
Prescription
Medicine Stock
Referral
Incoming Referrals
Patient Timeline
```

---

# 64. PHARMACY FRONTEND

Required screens:

```text
Pharmacy Dashboard
Inventory
Incoming Orders
Order Details
Prepare Order
Ready for Pickup
Dispensing
Inventory Transactions
```

---

# 65. KIOSK MODE

The patient workflow should support kiosk deployment.

Kiosk mode should prioritize:

* large controls
* minimal navigation
* voice guidance
* high contrast
* multilingual prompts
* simple error recovery
* session timeout
* automatic session cleanup

A patient should not be able to accidentally access another patient's session after leaving the kiosk.

---

# 66. SESSION SECURITY

After a kiosk session ends:

```text
temporary session state
        |
        v
clear
```

The next patient must start with a clean session.

Do not retain sensitive patient information in browser local storage unnecessarily.

---

# 67. DOCTOR DASHBOARD

The dashboard should surface:

* pending consultations
* patients awaiting review
* red-flag/triage alerts
* incoming referrals
* prescription status

Prioritize actionable information.

---

# 68. PHARMACY DASHBOARD

The pharmacy dashboard should surface:

* new prescriptions
* reserved orders
* preparation queue
* ready-for-pickup orders
* completed orders
* low-stock medicines

---

# 69. NOTIFICATIONS

The architecture should support notifications internally.

Examples:

```text
New referral
New pharmacy order
Order ready for pickup
Triage alert
```

For the prototype, in-app notifications are sufficient.

External SMS/push/email can be added behind an abstraction later.

---

# 70. FUTURE SMS SUPPORT

SMS can eventually support:

* appointment reminders
* pickup notifications
* next-visit reminders

SMS must not be used to autonomously prescribe medication.

---

# 71. AYUSH MODE

The system should support an AYUSH-specific history mode.

Where enabled, the intake flow can collect relevant Dashavidha Pariksha information, including:

```text
Prakriti
Vikriti
Sara
Samhanana
Pramana
Satmya
Sattva
Ahara Shakti
Vyayama Shakti
Vaya
Ahara
Vihara
```

AYUSH-specific fields should be modular rather than forcing them into every consultation.

---

# 72. CLINICAL DATA VERSIONING

Where AI and doctor edits differ, preserve the distinction.

Conceptually:

```text
AI version
    |
    v
Doctor-edited version
    |
    v
Doctor-approved version
```

The final approved clinical information is authoritative.

---

# 73. AUDITABLE CLINICAL CHANGES

When a doctor changes AI-generated information, record:

```text
field changed
old value
new value
doctor
timestamp
```

Where practical.

---

# 74. SEARCH

The system should support appropriate searching for:

* patients
* doctors
* medicines
* referrals
* prescriptions

Search must respect authorization.

---

# 75. PAGINATION

Large collections must not return unlimited records.

Use pagination for:

* patients
* consultations
* referrals
* prescriptions
* pharmacy orders
* inventory
* audit logs

---

# 76. TESTING STRATEGY

Testing must be implemented alongside features.

## Unit tests

Test:

* services
* business rules
* validation
* inventory calculations
* state transitions

## API tests

Test:

* authentication
* authorization
* patient APIs
* consultation APIs
* referrals
* prescriptions
* pharmacy
* documents

## Integration tests

Test complete workflows.

---

# 77. CRITICAL END-TO-END TEST

The complete demonstration workflow must work:

```text
Patient registers
       ↓
Patient selects language
       ↓
Patient gives consent
       ↓
Patient completes AI intake
       ↓
Transcript generated
       ↓
Structured clinical history generated
       ↓
Previous document uploaded
       ↓
Document information extracted
       ↓
Doctor sees case
       ↓
Doctor edits/approves history
       ↓
Doctor records diagnosis
       ↓
Doctor selects medicine
       ↓
System checks pharmacy stock
       ↓
Doctor confirms prescription
       ↓
Stock reserved
       ↓
Pharmacy receives order
       ↓
Pharmacy prepares medicine
       ↓
Order marked ready
       ↓
Patient arrives
       ↓
Pharmacy dispenses medicine
       ↓
Inventory updated
       ↓
Timeline updated
```

This is the primary integrated demonstration.

---

# 78. REFERRAL END-TO-END TEST

```text
Doctor A opens patient
       ↓
Doctor A creates referral
       ↓
Doctor B receives referral
       ↓
Doctor B accepts
       ↓
Doctor B reviews patient history
       ↓
Doctor B conducts consultation
       ↓
Doctor B adds clinical information
       ↓
Referral marked completed
```

---

# 79. MULTILINGUAL TEST

At minimum test:

```text
English
Malayalam
Hindi
Mixed-language input
```

Test:

* speech recognition
* transcript preservation
* clinical extraction
* structured output
* patient response language

---

# 80. AI TEST DATA

Use synthetic cases.

Include:

* simple symptoms
* multiple symptoms
* missing information
* contradictory answers
* medication history
* allergy history
* multilingual speech
* code-switching
* noisy/unclear speech
* emergency/red-flag scenarios

---

# 81. AI QUALITY REQUIREMENTS

The system should measure:

```text
Speech transcription quality
Structured extraction accuracy
Field completeness
Hallucination rate
Question relevance
Document extraction accuracy
Summary consistency
```

For the hackathon, evaluation can use a manually prepared synthetic ground-truth dataset.

---

# 82. ACCURACY REPORTING

Do not claim medical accuracy that has not been measured.

The prototype should report measured performance on the available synthetic/test dataset.

Example:

```text
Clinical field extraction accuracy: XX%
STT word/character accuracy: XX%
Document field extraction accuracy: XX%
```

The exact metrics must be calculated from actual tests.

---

# 83. DEMO DATA

Create realistic but completely synthetic data.

Example:

```text
Patients
Doctors
Medicines
Inventory
Consultations
Referrals
Prescriptions
Documents
```

Demo data should make the full workflow easy to demonstrate.

---

# 84. DEMO MODE

A controlled demo mode may be provided to simplify the hackathon presentation.

It must still use the same backend workflows rather than bypassing business logic.

Do NOT create fake UI-only state that contradicts the database.

---

# 85. API DOCUMENTATION

FastAPI's OpenAPI documentation should remain enabled for development.

Document:

* endpoints
* request schemas
* response schemas
* authentication requirements
* role requirements
* error responses

The API documentation should be useful to the frontend, AI, and pharmacy teammates.

---

# 86. TEAM INTEGRATION CONTRACTS

## Frontend → Backend

Frontend consumes documented REST APIs.

## AI → Backend

AI module returns structured data through defined interfaces.

AI does not directly modify PostgreSQL.

## Pharmacy → Backend

Pharmacy module consumes inventory/order APIs.

Pharmacy does not directly modify clinical records.

## Backend → External Systems

External integrations go through adapter interfaces.

---

# 87. MOCK SERVICES

The project must support mock implementations for external dependencies.

Examples:

```text
MockSTTService
MockLLMService
MockOCRService
MockTTSService
MockABHAService
MockHISService
```

This is essential for hackathon reliability.

If an external API fails during the demonstration, the core workflow should still be demonstrable.

---

# 88. SERVICE INTERFACES

Conceptual interfaces:

```python
class STTService:
    async def transcribe(audio) -> Transcript:
        ...


class LLMService:
    async def generate_structured_history(transcript) -> dict:
        ...


class OCRService:
    async def extract(document) -> dict:
        ...


class TTSService:
    async def synthesize(text, language) -> bytes:
        ...


class ABHAService:
    async def get_patient_record(...) -> dict:
        ...


class HISService:
    async def push_record(...) -> dict:
        ...
```

The implementation may use abstract base classes, protocols, or another appropriate pattern.

---

# 89. BACKEND BUSINESS LOGIC

Business logic must reside in services, not inside route handlers.

Preferred:

```text
API route
   |
   v
Schema validation
   |
   v
Service
   |
   v
Repository/database
```

Avoid giant route handlers containing all business logic.

---

# 90. DATABASE ACCESS

Use a consistent database access pattern.

Avoid raw SQL scattered throughout the application.

SQLAlchemy should be the primary ORM/data-access layer.

Raw SQL may be used where justified for performance or database-specific operations.

---

# 91. MIGRATIONS

All schema changes must use Alembic.

Never manually modify the production schema without a migration.

Development workflow:

```text
Model change
    |
    v
Alembic migration
    |
    v
Migration test
```

---

# 92. SEEDING

Provide a seed mechanism for demo data.

Example:

```text
python -m app.seed
```

or an equivalent command.

Seed data must be deterministic where possible.

---

# 93. DEVELOPMENT ENVIRONMENT

The project should be runnable locally.

Minimum:

```text
Python
Node.js
PostgreSQL
Git
```

Docker may be provided for convenience but should not be mandatory if the local development setup already works.

---

# 94. DOCKER

If Docker is used, provide:

```text
docker-compose.yml
```

for services such as:

```text
PostgreSQL
Backend
Frontend
```

Do not introduce unnecessary infrastructure.

---

# 95. DEPLOYMENT

The architecture should allow deployment of:

```text
Frontend
Backend
PostgreSQL
```

with environment-based configuration.

Deployment provider is not part of the core architecture.

---

# 96. PERFORMANCE

The prototype should be responsive enough for demonstration.

Optimize obvious bottlenecks, but do not prematurely optimize.

AI processing may be asynchronous where appropriate.

Long-running AI/OCR tasks should not unnecessarily block unrelated API requests.

---

# 97. BACKGROUND PROCESSING

For the prototype, simple background tasks may be used for:

* document processing
* TTS generation
* non-critical notifications

A full distributed job queue is not required unless implementation proves necessary.

---

# 98. STATE MACHINES

Important workflows should have explicit valid state transitions.

Example pharmacy:

```text
PENDING
  ↓
RESERVED
  ↓
PREPARING
  ↓
READY_FOR_PICKUP
  ↓
DISPENSED
```

Invalid transitions must be rejected.

---

# 99. SECURITY PRINCIPLES

Follow:

```text
Least privilege
Defense in depth
Backend authorization
Input validation
Secure secrets
Minimal data exposure
Auditability
```

Never trust:

* frontend role claims
* client-side stock values
* client-side prescription status
* AI-generated values without validation

---

# 100. SECRETS

Never commit:

```text
API keys
JWT secrets
database passwords
ABHA credentials
HIS credentials
```

Use:

```text
.env
```

and:

```text
.env.example
```

---

# 101. GIT WORKFLOW

Use feature-oriented commits.

Examples:

```text
feat: initialize backend
feat: configure postgres
feat: add authentication
feat: add patient workflow
feat: add consultation workflow
feat: add clinical extraction
feat: add document processing
feat: add doctor review
feat: add referrals
feat: add prescriptions
feat: add pharmacy inventory
feat: add pharmacy workflow
feat: add audit logging
test: add end-to-end consultation workflow
```

Commit stable milestones.

Do not commit known broken intermediate states unless unavoidable.

---

# 102. IMPLEMENTATION PHASES

## Phase 1 — Foundation

Implement:

* repository structure
* FastAPI
* configuration
* PostgreSQL
* SQLAlchemy
* Alembic
* health endpoint
* logging
* testing framework

Definition of done:

```text
Backend starts
PostgreSQL connects
Migration runs
Health check passes
Tests run
```

---

## Phase 2 — Authentication

Implement:

* User model
* password hashing
* JWT
* login
* authorization
* role system

---

## Phase 3 — Patient

Implement:

* Patient model
* patient APIs
* patient profile
* patient history

---

## Phase 4 — Consultation

Implement:

* Consultation model
* consultation APIs
* transcript model
* consultation state management

---

## Phase 5 — AI Intake

Implement:

* STT abstraction
* LLM abstraction
* structured clinical schema
* clinical extraction
* adaptive questions
* multilingual processing
* summary generation
* red-flag detection

---

## Phase 6 — Doctor Workflow

Implement:

* doctor dashboard APIs
* case review
* editing
* approval
* diagnosis
* prescription creation

---

## Phase 7 — Medical Documents

Implement:

* upload
* storage
* OCR abstraction
* extraction
* timeline integration

---

## Phase 8 — Referrals

Implement:

* referral model
* referral APIs
* doctor-to-doctor transfer
* status workflow
* notifications

---

## Phase 9 — Pharmacy

Implement:

* medicine model
* inventory
* inventory transactions
* stock checking
* reservation
* prescription integration
* pharmacy orders
* preparation
* pickup
* dispensing

---

## Phase 10 — Timeline

Implement:

* event aggregation
* patient timeline
* consultation history
* prescription history
* referral history
* pharmacy history

---

## Phase 11 — External Integration

Implement:

* ABHA service interface
* HIS service interface
* FHIR mapping
* mock implementations

---

## Phase 12 — Integration

Connect:

```text
Frontend
   +
AI
   +
Backend
   +
Pharmacy
   +
Database
```

Run the complete end-to-end workflow.

---

## Phase 13 — Testing and Hardening

Test:

* authorization
* data integrity
* AI failures
* inventory concurrency
* referrals
* prescriptions
* documents
* complete workflow

Fix critical issues.

---

# 103. DEFINITION OF DONE

The system is considered functionally complete when the following can be demonstrated without manually editing the database:

```text
1. Patient logs in/registers.
2. Patient selects language.
3. Patient provides consent.
4. Patient completes voice/text intake.
5. System generates transcript.
6. System extracts structured clinical history.
7. System identifies missing information.
8. System can ask follow-up questions.
9. Patient uploads previous medical documents.
10. System processes documents.
11. Doctor receives the case.
12. Doctor reviews AI-generated history.
13. Doctor edits/approves the history.
14. Doctor records diagnosis.
15. Doctor selects medicine.
16. System checks pharmacy stock.
17. Doctor confirms prescription.
18. Medicine stock is reserved.
19. Pharmacy receives the order.
20. Pharmacy prepares it.
21. Patient receives pickup-ready status.
22. Pharmacy dispenses medicine.
23. Inventory is updated.
24. Timeline reflects the workflow.
25. Doctor can refer the case to another doctor.
26. Receiving doctor can access the referral.
27. Important actions appear in audit logs.
```

---

# 104. NON-GOALS

The following are NOT required for the hackathon MVP unless time/resources allow:

* autonomous diagnosis
* autonomous prescription
* production hospital deployment
* forensic/clinical certification
* nationwide ABDM deployment
* nationwide hospital integration
* enterprise microservice infrastructure
* Kubernetes
* advanced distributed systems
* fully autonomous clinical decision-making

These exclusions do NOT remove the core user-facing functionality described elsewhere in this document.

---

# 105. ARCHITECTURAL PRIORITY

When making implementation decisions, prioritize:

```text
1. Correctness
2. Data integrity
3. Security
4. End-to-end functionality
5. Clear integration contracts
6. Maintainability
7. Demonstrability
8. Performance
9. Scalability
```

Do not sacrifice database integrity merely to make a feature appear to work.

Do not sacrifice the end-to-end workflow by overengineering individual components.

---

# 106. AI CODING AGENT RULES

Any AI coding agent working on this repository MUST:

1. Read this file before implementing.
2. Read REQUIREMENTS.md.
3. Read CURRENT_STATE.md.
4. Inspect existing code.
5. Never assume an unimplemented feature exists.
6. Never silently remove a required feature.
7. Never replace working functionality without justification.
8. Preserve existing APIs unless there is a documented reason to change them.
9. Run tests after meaningful changes.
10. Update CURRENT_STATE.md after milestones.
11. Keep database migrations synchronized with models.
12. Keep API schemas synchronized with implementation.
13. Document major architectural changes.
14. Never hard-code secrets.
15. Never introduce unnecessary infrastructure.
16. Never make AI-generated clinical information authoritative.
17. Never allow the frontend to bypass backend authorization.
18. Never allow AI to directly modify critical database state.
19. Never claim a feature is complete without verifying it.
20. Prefer a working complete workflow over isolated technically impressive components.

---

# 107. CHECKPOINT REQUIREMENT FOR AI CODING AGENTS

`CURRENT_STATE.md` is the persistent handoff mechanism between AI coding sessions.

At every meaningful milestone, update:

```text
Current phase
Completed work
In-progress work
Files changed
Database changes
API changes
Tests
Known issues
Next actions
Integration requirements
```

Before a session ends, ensure the repository is left in a recoverable state.

A fresh AI session must be able to:

```text
Read ARCHITECTURE.md
       ↓
Read REQUIREMENTS.md
       ↓
Read CURRENT_STATE.md
       ↓
Inspect repository
       ↓
Understand exactly what remains
       ↓
Continue implementation
```

without relying on previous chat history.

---

# 108. FINAL SYSTEM ARCHITECTURE

The final MediSetu system is:

```text
                         PATIENT
                            |
             ┌──────────────┴──────────────┐
             |                             |
           VOICE                          TOUCH
             |                             |
             └──────────────┬──────────────┘
                            |
                            v
                    AI INTAKE ENGINE
                            |
                ┌───────────┼───────────┐
                |           |           |
               STT        LLM          TTS
                |           |
                └─────┬─────┘
                      |
                      v
              STRUCTURED HISTORY
                      |
                      +───────────────┐
                      |               |
                      v               v
                  DOCUMENTS       RED FLAGS
                      |               |
                      v               v
                    OCR             TRIAGE
                      |
                      v
              CLINICAL SUMMARY
                      |
                      v
               DOCTOR REVIEW
                      |
             ┌────────┴────────┐
             |                 |
             v                 v
         DIAGNOSIS          REFERRAL
             |
             v
        PRESCRIPTION
             |
             v
       STOCK CHECK
             |
             v
       STOCK RESERVATION
             |
             v
      PHARMACY ORDER
             |
             v
       READY FOR PICKUP
             |
             v
          DISPENSE
             |
             v
       INVENTORY UPDATE
             |
             v
       PATIENT TIMELINE

Supporting all workflows:

        AUTHENTICATION
              +
        ROLE AUTHORIZATION
              +
         AUDIT LOGGING
              +
        POSTGRESQL
              +
       HIS / ABHA ADAPTERS
```

This architecture is the authoritative technical blueprint for MediSetu.

```
```
