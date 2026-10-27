# MediSetu — Project Requirements

## 1. Project Overview

MediSetu is an AI-powered pre-consultation clinical intake and healthcare workflow platform.

The system allows patients to provide their medical history before meeting a physician using voice and touchscreen interaction. It can also digitize existing medical documents and organize the patient's previous medical information.

The collected information is converted into a structured, physician-ready clinical history summary. The physician reviews and verifies this information before or during the consultation.

After the consultation, the platform supports physician-controlled workflows such as doctor-to-doctor case referral, prescription generation, pharmacy stock checking, and pharmacy medicine preparation.

The AI assists with information collection, transcription, extraction, organization, and summarization. It does NOT independently diagnose patients or prescribe medicines.

The physician remains the final clinical authority.

---

# 2. Problem Being Addressed

Patient history-taking is often performed manually during consultations.

This can result in:

- Significant consultation time being spent collecting basic history
- Incomplete or inconsistently documented patient histories
- Difficulty communicating with patients with low literacy or language barriers
- Previous physical medical documents being difficult to use efficiently
- Doctors spending less consultation time on examination, reasoning, and counselling
- Fragmented medical information across visits and facilities
- Delays in downstream workflows such as pharmacy preparation

MediSetu aims to move structured history collection before the consultation while connecting the resulting information to the physician and hospital workflow.

---

# 3. Primary Goals

The system should:

1. Allow patients to independently provide their medical history before consultation.
2. Support voice and touchscreen interaction.
3. Support multilingual patient interaction.
4. Accommodate low-literacy and elderly users.
5. Digitize existing physical medical documents.
6. Extract useful structured information from those documents.
7. Generate a structured clinical history summary.
8. Allow physicians to review, edit, accept, or reject AI-generated information.
9. Identify predefined clinical red flags for triage attention.
10. Allow physicians to refer cases to other doctors.
11. Allow physicians to prescribe medicines after consultation.
12. Allow the prescription workflow to check pharmacy stock.
13. Notify the pharmacy of the required medicines.
14. Allow the pharmacy to prepare medicines before the patient reaches the pharmacy counter.
15. Support integration with digital healthcare records where feasible.
16. Maintain appropriate consent, privacy, and security controls.

---

# 4. Core User Roles

## 4.1 Patient

The patient can:

- Identify/login to their profile
- Select a preferred language
- Provide consent
- Answer clinical history questions through voice
- Answer questions through touchscreen interaction
- Upload or scan previous medical documents
- Review information captured about them
- Receive confirmation that their information has been submitted
- View relevant medical history through their patient dashboard

---

## 4.2 Physician

The physician can:

- View the patient's structured history before/during consultation
- Review the AI-generated history
- Edit incorrect information
- Accept or reject individual information
- View digitized previous medical documents
- Review extracted medical information
- Review flagged red-flag symptoms
- Conduct the actual clinical consultation
- Make the final diagnosis
- Prescribe medicines
- Refer a case to another doctor
- Review information received from another physician
- Approve or modify information before it becomes part of the official record

The AI must not replace the physician's clinical decision-making.

---

## 4.3 Pharmacy Staff

Pharmacy staff can:

- Receive prescriptions sent by physicians
- View prescribed medicines
- Check current stock
- Mark medicines as available/unavailable
- Prepare available medicines before the patient reaches the counter
- Update dispensing status

---

## 4.4 Administrator / Hospital Staff

Administrators may:

- Manage doctors
- Manage departments
- Manage pharmacy information
- Manage system configuration
- Monitor system activity
- Manage users and access permissions

Administrative functionality should remain limited to what is required for the prototype.

---

# 5. Patient Intake System

The patient should be able to complete the pre-consultation process using either:

- A self-service kiosk in an OPD
- A mobile/web application before arriving at the hospital

The interface should support:

- Large and readable text
- Clear visual controls
- Audio guidance
- Multiple languages
- Voice input
- Touch input
- Simple navigation
- Minimal technical knowledge

The system should be usable by patients with limited literacy.

---

# 6. Conversational Voice History

The system should provide an AI-assisted conversational history-taking interface.

The patient can answer questions by speaking.

The system should:

1. Ask a question.
2. Capture the patient's response.
3. Convert speech to text.
4. Interpret the response.
5. Store the structured information.
6. Ask the next relevant question.
7. Dynamically adapt questions based on the patient's responses.

The system should collect relevant clinical history such as:

- Chief complaint
- History of present illness
- Past medical history
- Past surgical history
- Medication history
- Allergy history
- Family history
- Personal history
- Relevant review of systems
- Previous investigations

The exact questions should depend on the patient's complaint.

For example, if the patient reports chest pain, the system can collect information such as:

- Onset
- Duration
- Character
- Location
- Radiation
- Aggravating factors
- Relieving factors
- Associated symptoms

The AI should structure the information but must not independently diagnose the patient.

---

# 7. Multilingual Support

The system should support multilingual interaction.

The architecture should allow additional Indian languages to be added without redesigning the entire system.

The voice pipeline should be designed to handle:

- Regional languages
- Different accents
- Noisy OPD environments
- Natural conversational speech

Potential technologies may include Indian-language speech models such as Bhashini or AI4Bharat, subject to availability and licensing.

The technology choice should be determined during architecture design rather than hard-coded into the requirements.

---

# 8. AYUSH Support

The system should support an AYUSH-specific history-taking mode where required.

For Ayurvedic OPDs, the history workflow may capture:

- Prakriti
- Vikriti
- Sara
- Samhanana
- Pramana
- Satmya
- Sattva
- Ahara Shakti
- Vyayama Shakti
- Vaya
- Ahara
- Vihara

The architecture should allow different history templates/workflows for different departments.

---

# 9. Red-Flag Detection

The system should identify predefined emergency or high-priority symptoms during intake.

Examples may include combinations of symptoms such as:

- Severe chest pain with breathing difficulty
- Stroke-like symptoms
- Severe bleeding
- Loss of consciousness
- Other predefined emergency indicators

The system should NOT diagnose the patient.

Instead, it should:

1. Detect a predefined red-flag pattern.
2. Mark the intake as requiring attention.
3. Alert appropriate triage/hospital staff.
4. Allow staff/physicians to make the actual clinical decision.

Red-flag detection is therefore an alerting/triage-support function, not an autonomous diagnostic system.

---

# 10. Medical Document Digitization

Patients should be able to upload or photograph existing medical documents.

Supported documents may include:

- Prescriptions
- Laboratory reports
- Discharge summaries
- Imaging reports
- Other relevant medical records

The document processing pipeline should:

1. Receive the document/image.
2. Perform OCR.
3. Extract relevant information.
4. Structure the extracted information.
5. Associate it with the patient's medical history.
6. Organize records chronologically where dates are available.

The system should attempt to extract information such as:

- Diagnoses mentioned in documents
- Medicines
- Dosages
- Investigation results
- Reference ranges
- Procedures
- Surgical history
- Dates
- Relevant clinical information

OCR should support printed documents and, where technically feasible, handwritten documents.

---

# 11. Clinical Summary Generation

The system should combine:

- Patient conversational history
- Extracted document information
- Relevant previous medical information

into a concise structured clinical history.

The preferred structure is:

1. Chief Complaint
2. History of Present Illness
3. Past Medical History
4. Past Surgical History
5. Drug History
6. Allergy History
7. Family History
8. Personal History
9. Review of Systems
10. Previous Investigations

The generated summary is a DRAFT.

The physician must be able to:

- Review it
- Edit it
- Accept it
- Reject information
- Correct errors

The system must clearly communicate that the AI-generated information requires physician verification.

---

# 12. Physician Consultation Workflow

The intended workflow is:

Patient
→ Pre-consultation intake
→ AI-assisted history collection
→ Document digitization
→ Structured history generation
→ Physician review
→ Clinical consultation
→ Physician diagnosis and treatment decision

The physician should receive the patient's structured history without having to manually reconstruct the entire history from raw responses.

The system should optimize the physician's time for:

- Examination
- Clinical reasoning
- Diagnosis
- Treatment decisions
- Patient counselling

---

# 13. Doctor-to-Doctor Referral

Physicians should be able to transfer/refer a patient's case to another physician when appropriate.

A referral should contain relevant information such as:

- Patient identity
- Current clinical history
- Relevant documents
- Investigation results
- Current physician's notes
- Reason for referral
- Referring department
- Target department/doctor
- Referral timestamp
- Referral status

The receiving physician should be able to review the case without requiring the patient to repeat the entire history.

The receiving physician retains full clinical authority.

---

# 14. Prescription Workflow

After the consultation, the physician can create a prescription.

The physician should control:

- Medicine
- Dosage
- Frequency
- Duration
- Instructions

The system should not autonomously prescribe medicines.

The prescription should only enter the pharmacy workflow after physician authorization.

---

# 15. Pharmacy Integration

The pharmacy module should receive physician-authorized prescriptions.

The pharmacy system should:

1. Receive the prescription.
2. Check current medicine inventory.
3. Determine which medicines are available.
4. Notify pharmacy staff.
5. Allow pharmacy staff to prepare available medicines.
6. Associate the prepared medicine order with the patient.
7. Update the dispensing status.

The objective is to reduce waiting time at the pharmacy.

Example workflow:

Doctor prescribes
→ System sends prescription to pharmacy
→ Pharmacy checks stock
→ Pharmacy prepares medicines
→ Patient reaches pharmacy
→ Staff retrieves prepared order
→ Medicines are dispensed

The system should not assume that all medicines will always be available.

Stock status must be represented explicitly.

---

# 16. Patient Dashboard

The patient dashboard may provide:

- Patient profile
- Medical history
- Previous consultations
- Uploaded documents
- Relevant prescriptions
- Referral information
- Visit history

The exact dashboard scope should be kept manageable for the hackathon MVP.

---

# 17. Kiosk Deployment

A self-service kiosk is a primary deployment mode for the hospital OPD.

The kiosk should provide:

- Touchscreen interface
- Microphone/audio input
- Document/image capture
- Patient identification
- Consent interface
- Multilingual interaction
- Intake completion
- Submission to the backend

The kiosk should be designed for operation with minimal staff assistance.

---

# 18. Mobile/Web Deployment

A patient-facing mobile/web interface may allow patients to complete intake before arriving at the hospital.

The same backend should support both:

- Kiosk
- Mobile/web

The system should avoid duplicating business logic between these interfaces.

---

# 19. Authentication and Identity

The system should support patient and staff authentication.

Where appropriate, integration with:

- ABHA
- ABDM
- Aadhaar-linked identity workflows

may be considered.

However, identity integration must comply with the actual APIs, authentication mechanisms, consent requirements, and availability of the relevant services.

The prototype should not falsely claim production-level ABHA/ABDM integration if actual integration has not been implemented.

---

# 20. Consent and Privacy

Patient consent is required before collecting and processing medical information.

The consent workflow should be:

- Explicit
- Understandable
- Revocable where applicable
- Accessible to low-literacy users
- Available in the patient's selected language

The system should minimize unnecessary storage of sensitive information.

Security should be considered from the beginning rather than added at the end.

The system should consider:

- Encryption at rest
- Encryption in transit
- Authentication
- Authorization
- Role-based access control
- Audit logging
- Data minimization
- Session management
- Secure handling of uploaded documents
- Secure handling of voice data

The platform should be designed with the Digital Personal Data Protection Act 2023 and relevant ABDM consent principles in mind.

Actual legal/regulatory compliance must not be claimed unless properly validated.

---

# 21. AI Safety Principles

AI is an assistant, not the final decision-maker.

AI MAY:

- Transcribe speech
- Structure patient responses
- Extract information from documents
- Summarize medical history
- Identify predefined red-flag patterns
- Organize information
- Assist workflow

AI MUST NOT:

- Independently diagnose a patient
- Independently prescribe medication
- Override a physician
- Make final clinical decisions
- Automatically modify a physician's decision
- Present an AI-generated diagnosis as confirmed fact

All AI-generated clinical information should be treated as requiring human verification.

---

# 22. Core System Data

The backend will likely need to represent entities such as:

- Patient
- Doctor
- Department
- Hospital
- Intake Session
- Patient Response
- Clinical History
- Medical Document
- Extracted Medical Information
- Investigation
- Consultation
- Referral
- Prescription
- Prescription Item
- Medicine
- Pharmacy
- Inventory/Stock
- Pharmacy Order
- Consent
- Audit Event

The final database schema should be determined during architecture design.

Do not create unnecessary entities simply because they are listed here.

---

# 23. Team Responsibilities

## Team Member 1 — Frontend/UI

Responsible for:

- Patient interface
- Kiosk interface
- Physician interface
- Pharmacy interface
- Patient dashboard
- API integration with backend
- Multilingual UI presentation
- Voice interaction UI integration

The frontend should consume defined backend APIs rather than directly accessing the database.

---

## Team Member 2 — Voice AI

Responsible for:

- Speech-to-text
- Voice interaction
- Conversational question flow
- Multilingual speech processing
- Integration with the clinical history workflow
- Returning structured patient responses to the backend

The voice module should expose a clearly defined interface/API to the backend.

The voice AI should not directly modify unrelated backend data without going through agreed interfaces.

---

## Team Member 3 — Pharmacy

Responsible for:

- Pharmacy interface
- Medicine inventory
- Stock management
- Prescription reception
- Pharmacy order preparation
- Dispensing status
- Integration with the backend prescription workflow

The pharmacy module should consume the physician-authorized prescription generated by the backend.

---

## Team Member 4 — Backend, AI Processing & Integration

Responsible for:

- Backend architecture
- Database
- API layer
- Authentication/authorization
- Patient records
- Clinical history data model
- Document upload
- OCR pipeline
- Medical information extraction
- Clinical summary generation
- Red-flag detection
- Doctor-to-doctor referrals
- Prescription backend
- Pharmacy integration
- Integration between all team modules
- External healthcare integrations where feasible
- System-wide testing
- Deployment/integration

This role is responsible for ensuring that the modules developed by the other team members work together as one system.

---

# 24. Integration Principle

The project should be designed around clear interfaces.

The major data flow should resemble:

Patient
    ↓
Frontend
    ↓
Backend
    ↓
Voice AI / Document AI
    ↓
Structured Patient History
    ↓
Physician
    ↓
Diagnosis + Physician Decision
    ↓
Prescription
    ↓
Pharmacy
    ↓
Medicine Preparation
    ↓
Patient

Referral flow:

Physician A
    ↓
Referral
    ↓
Backend
    ↓
Physician B
    ↓
Review Case

The frontend, voice AI, pharmacy, and backend must agree on data formats and API contracts before final integration.

---

# 25. MVP Scope

The MVP should prioritize a complete end-to-end demonstration rather than attempting to implement every possible feature.

The minimum successful demonstration should show:

1. Patient starts intake.
2. Patient selects language.
3. Patient provides history using voice/touch.
4. Voice response is transcribed.
5. Patient information is structured.
6. Patient uploads/scans a medical document.
7. OCR extracts information.
8. A structured history summary is generated.
9. Physician reviews and edits the summary.
10. Physician completes consultation.
11. Physician creates a prescription.
12. Pharmacy receives the prescription.
13. Pharmacy checks stock.
14. Pharmacy prepares the available medicines.
15. Patient can proceed to medicine collection.
16. A physician can optionally refer the case to another doctor.

The demo should show the system functioning as one connected workflow.

---

# 26. Features That Are Secondary to the MVP

The following should not compromise the core workflow:

- Advanced patient analytics
- Complex hospital administration
- Extensive insurance integration
- Fully automated department routing
- Advanced predictive analytics
- Large-scale production infrastructure
- Extensive external integrations
- Complex mobile application features

These can be implemented only if the core system is stable.

---

# 27. Future Scope

Potential future features include:

- Ambient consultation scribing
- Advanced doctor-assistance tools
- Automated appointment reminders
- SMS-based workflows
- Department re-routing assistance
- Additional healthcare integrations
- More Indian languages
- Advanced medical document understanding
- Larger-scale hospital deployment
- Analytics for hospital operations

These are not required for the core MVP unless specifically added later.

---

# 28. Technical Philosophy

This is a hackathon prototype.

The architecture should therefore prioritize:

- Reliability
- Demonstrability
- Simplicity
- Clear module boundaries
- Easy integration
- Maintainability
- Security
- Fast development

Avoid unnecessary:

- Microservices
- Distributed infrastructure
- Complex cloud architecture
- Redundant databases
- Over-engineered abstractions

A modular monolithic backend is preferred unless there is a strong technical reason to use another architecture.

Technology choices should be made based on:

1. Ability to build quickly
2. Availability of libraries/models
3. Integration simplicity
4. Reliability during demonstration
5. Ease of debugging
6. Ability for the team to understand and maintain the system

---

# 29. Prototype vs Production

The project is a proof-of-concept/hackathon prototype.

Prototype implementations may use simplified components where appropriate.

However, the architecture should avoid decisions that make future expansion impossible.

The system must clearly distinguish between:

- Features actually implemented
- Features simulated for demonstration
- Features planned for future implementation

The team must not claim that simulated integrations are real production integrations.

---

# 30. Definition of Success

MediSetu is successful as a prototype if it can demonstrate a coherent end-to-end healthcare workflow in which:

A patient provides their history before consultation
→ AI assists in collecting and structuring the information
→ previous medical documents are digitized
→ a physician receives a concise editable history
→ the physician makes the clinical decision
→ the physician can refer the case or prescribe medication
→ the pharmacy receives the authorized prescription
→ medicine availability is checked
→ pharmacy staff can prepare the medicine
→ the patient experiences a faster overall workflow.

The central principle is:

AI reduces information and administrative burden while keeping clinical authority with the physician.
