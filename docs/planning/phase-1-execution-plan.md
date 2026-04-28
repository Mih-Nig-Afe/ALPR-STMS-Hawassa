# ALPR STMS Hawassa Phase 1 Execution Plan

## 1. Current folder review

This folder is a documentation package, not an implementation repository.

What exists:
- Main proposal: `ALPR STMS, Hawassa.docx`
- Proposal PDF export: `ALPR STMS, Hawassa-20260121152523.pdf`
- Academic guideline: `Project-Guideline For Software Engineering.pdf`
- Schedule image: `Project Tasks AND Schedule.jpg`
- Reference plate image: `New plate design model.webp`
- UML set under `UML/`
  - use case
  - class diagram
  - activity diagram
  - sequence diagrams
  - collaboration diagrams
  - component diagram
  - deployment diagram
  - persistence diagram
  - violation state chart

What does **not** exist:
- no backend code
- no frontend code
- no mobile code
- no database schema or migrations
- no API spec
- no tests
- no deployment scripts
- no sample data
- no integration adapters

Conclusion:
- the analysis and design package is fairly complete
- Phase 1 is **not built yet**
- the project is currently at "requirements/design baseline", not "implementation baseline"

## 2. What Phase 1 actually is

The proposal defines Phase 1 as:
- manual digital violation reporting
- automatic timestamp and GPS capture
- digital alert broadcasting to nearby officers and relevant subcity offices
- map-based officer escape-path drawing
- centralized violation, penalty, payment, complaint, and audit records
- OTP-based payment initiation after confirmation
- zero automated CCTV detection
- zero ML route prediction
- zero autonomous enforcement

Authoritative Phase 1 interpretation for implementation:
- build the manual enforcement platform only
- keep CCTV, ALPR, and predictive intelligence out of the implementation scope
- keep the data model extensible so later phases can plug in without redesign

## 3. Critical findings from the folder

### 3.1 Strengths

- The problem statement, actors, workflows, and architecture are well documented.
- The system boundary is mostly clear.
- The layered/service-oriented architecture is appropriate.
- The role model is strong for a government workflow.
- The state chart, activity diagram, component diagram, deployment diagram, and persistence notes are useful implementation inputs.
- The schedule, phase breakdown, and cost estimates already exist.

### 3.2 Blocking inconsistencies

These must be resolved before coding starts.

1. Phase leakage in requirements
- Phase 1 is defined as manual reporting only.
- But the FR list includes CCTV extraction, ALPR validation, and route prediction items that belong to later phases.

2. Workflow leakage in diagrams
- The activity diagram and some use case details merge Phase 1, Phase 2, and Phase 3 behavior into one end-to-end flow.

3. Actor inconsistency around the driver
- The prose says the driver is not a system actor.
- The use case and class diagrams still show the driver as an external participant in payment.
- Implementation should treat the driver as an external payment participant, not an authenticated user.

4. Violation state inconsistency
- Text states: `Pending`, `Confirmed`, `UnderComplaint`, `Dismissed`, `Paid`
- State chart states: `Reported`, `UnderReview`, `Broadcasted`, `VehicleStopped`, `Penalized`, `ComplaintInitiated`, `ComplaintUnderReview`, `Confirmed`, `PaymentRequested`, `Paid`, `Revoked`
- One canonical state model is required before database design.

5. Penalty timing inconsistency
- Some sections imply penalty calculation at report time.
- Others require finalization only after officer/subcity confirmation.
- Correct implementation model:
  - calculate a draft penalty immediately
  - confirm the penalty only after legal confirmation

6. Technology ambiguity
- Backend is listed as `FastAPI or Flask`
- database is `PostgreSQL or MySQL`
- maps are `OpenStreetMap or Google Maps`
- prototype data is `Firebase`, production is relational
- payment gateway is unspecified
- these must be frozen into one execution stack

7. Delivery schedule mismatch
- The proposal schedule says:
  - implementation: March 2, 2026 to April 20, 2026
  - testing: March 16, 2026 to May 4, 2026
  - finalization: May 4, 2026 to May 31, 2026
- As of **April 28, 2026**, implementation is already past due and the folder still contains no code.

## 4. Phase 1 scope lock

### In scope

- authentication and RBAC
- traffic officer dashboard
- manual violation creation
- GPS/time auto-capture
- structured plate entry for Ethiopian plate format
- evidence photo upload from officer device
- draft penalty calculation from configured rules
- alert generation and broadcast
- alert inbox and acknowledgement
- subcity coordination dashboard
- complaint workflow
- payment request initiation
- payment status tracking
- admin user/role/rule management
- audit logging
- reporting dashboard
- offline-safe capture queue for weak connectivity

### Out of scope

- live CCTV ingestion
- ALPR/OCR
- detection confidence scoring
- CCTV operator workflow as an active production feature
- predictive route intelligence
- automatic violation creation
- national registry integration unless a ready source already exists
- smart-city analytics

## 5. Decisions that should be frozen now

These are the right choices if the goal is to finish Phase 1 fast and cleanly.

1. Backend
- `FastAPI`

2. Database
- `PostgreSQL`

3. Frontend strategy
- one responsive web application for office roles
- one mobile-first officer client
- if time is tight, make the officer client a PWA first instead of building Flutter and web in parallel

4. Maps
- `OpenStreetMap` with a web map library

5. File storage
- local/S3-compatible object storage abstraction for evidence

6. Auth
- username/password with RBAC
- second factor optional, not required for first release

7. Alert delivery
- in-app alerts first
- SMS only for payment OTP via gateway

8. Integration stance
- payment gateway through an adapter interface
- start with a simulator/mock if live gateway access is not already approved

## 6. Canonical Phase 1 business flow

1. Officer logs in.
2. Officer opens `Create Violation`.
3. System captures:
- officer ID
- timestamp
- GPS location
4. Officer enters:
- plate number
- violation type
- optional description
- optional image evidence
- optional manually drawn path
5. System creates violation in `REPORTED`.
6. System calculates draft penalty from rule table.
7. System creates alert set:
- nearby officers
- owning subcity
- optionally adjacent subcities
8. Vehicle is stopped.
9. If driver admits:
- officer confirms violation
- payment request is created
10. If driver disputes:
- violation gets complaint state
- complaint officer reviews record and evidence
- subcity/complaint authority confirms or revokes
11. If confirmed:
- payment request is created
12. When payment gateway confirms:
- violation becomes `PAID`
13. Audit trail is appended at every state transition.

## 7. Canonical Phase 1 data model

Minimum entities:
- `users`
- `roles`
- `subcities`
- `officer_assignments`
- `vehicles`
- `violation_rules`
- `violations`
- `violation_evidence`
- `violation_alerts`
- `alert_recipients`
- `complaints`
- `complaint_decisions`
- `payment_requests`
- `payment_transactions`
- `audit_logs`
- `device_sessions`

Recommended violation statuses for Phase 1:
- `REPORTED`
- `BROADCASTED`
- `STOPPED`
- `UNDER_COMPLAINT`
- `CONFIRMED`
- `REVOKED`
- `PAYMENT_REQUESTED`
- `PAID`
- `CLOSED`

Do **not** use Phase 2/3 statuses in the Phase 1 UI unless they are dormant backend values.

## 8. Required external inputs before development

These are dependencies, not nice-to-haves.

1. User master data
- officers
- subcity officers
- complaint officers
- admins

2. Jurisdiction data
- subcity boundaries
- checkpoint list
- officer assignment rules

3. Violation rulebook
- legal code
- fee amount
- point amount
- escalation rules

4. Payment integration information
- gateway API
- OTP flow
- callback format

5. Plate format standard
- Ethiopian plate structure
- valid character set
- normalization rules

6. Operational policy
- when a complaint is allowed
- who can confirm/revoke
- who can trigger payment
- retention requirements

## 9. Execution workstreams

### Workstream A: Scope and governance
- freeze Phase 1 scope
- approve canonical state model
- approve role/action matrix
- approve violation rule source
- approve payment integration mode

### Workstream B: UX and process design
- finalize officer flow
- finalize subcity dashboard
- finalize complaint workflow
- finalize admin workflow
- convert diagrams into screen inventory and action matrix

### Workstream C: Platform foundation
- initialize repo structure
- environment setup
- config management
- logging
- error handling
- file storage abstraction
- auth foundation

### Workstream D: Backend core
- RBAC
- user management
- violation service
- rule engine
- alert service
- complaint service
- payment request service
- audit log service

### Workstream E: Frontend/mobile
- login
- officer dashboard
- create violation form
- map and route drawing
- alert inbox
- subcity dashboard
- complaint review
- admin panels

### Workstream F: Data and integrations
- PostgreSQL schema
- migrations
- seed data
- payment adapter
- OTP callback handling
- map/geolocation services

### Workstream G: QA
- unit tests
- workflow integration tests
- role access tests
- payment state tests
- offline/poor network tests

### Workstream H: Deployment and adoption
- staging environment
- production checklist
- user training
- pilot rollout
- defect triage

## 10. Realistic rebaseline from April 28, 2026

The original written schedule is no longer realistic because there is still no implementation in the folder.

### Recommended rebaseline

#### Week 1: April 29 to May 5, 2026
- freeze scope
- resolve contradictions
- finalize stack
- finalize schema and API contract
- set up repo and environments

#### Week 2: May 6 to May 12, 2026
- auth and RBAC
- user, role, and subcity master data
- admin rule configuration basics
- audit logging base

#### Week 3: May 13 to May 19, 2026
- officer dashboard
- manual violation creation
- GPS/time capture
- photo evidence upload
- violation state handling

#### Week 4: May 20 to May 26, 2026
- alert engine
- recipient targeting by subcity/proximity
- alert inbox and acknowledgement
- map-based route drawing

#### Week 5: May 27 to June 2, 2026
- complaint workflow
- subcity dashboard
- confirm/revoke decisions
- decision audit trail

#### Week 6: June 3 to June 9, 2026
- payment request flow
- gateway adapter
- callback processing
- paid/failed/pending state handling

#### Week 7: June 10 to June 16, 2026
- reports
- exports
- role hardening
- validation polish
- offline-safe queue behavior

#### Week 8: June 17 to June 23, 2026
- full integration testing
- UAT with scenario scripts
- defect fixing
- pilot readiness review

### If academic submission must stay inside May 31, 2026

Then the only credible target is:
- a working Phase 1 MVP
- one officer client
- one office web console
- mocked payment gateway or limited live integration
- no Flutter/native duplication
- no CCTV code

Anything larger than that will slip.

## 11. Delivery sequence by priority

Build in this order:

1. auth + RBAC
2. violation rules
3. manual violation creation
4. violation state machine
5. audit logs
6. officer alerts
7. subcity coordination
8. complaint handling
9. payment request flow
10. reports and polish

This order is critical. If alerts are built before the violation state machine and audit model are stable, the system will become inconsistent fast.

## 12. Acceptance criteria for Phase 1 completion

Phase 1 is complete only when all of these are true:

1. A traffic officer can log in and file a violation from a mobile-friendly interface.
2. The system auto-captures timestamp and GPS.
3. The violation receives a unique ID and draft penalty.
4. Alerts are sent to the correct officers/subcity recipients.
5. Evidence can be attached and retrieved.
6. The complaint officer can review, confirm, or revoke a disputed violation.
7. Payment can be requested only after legal confirmation.
8. Payment status updates the violation correctly.
9. All state transitions are audit-logged.
10. Admin can manage users, roles, and violation rules.
11. The reporting view can show daily/weekly violation summaries.
12. The system works acceptably under low bandwidth and temporary connectivity loss.

## 13. Test matrix

Minimum test scenarios:
- login success/failure
- role access denial
- create violation with full data
- create violation with weak network
- duplicate submission protection
- invalid plate format handling
- evidence upload failure
- alert routing by subcity
- alert acknowledgement
- admit violation and request payment
- dispute violation and open complaint
- confirm complaint outcome
- revoke complaint outcome
- gateway success callback
- gateway failed callback
- audit log completeness
- report accuracy

## 14. Main risks and mitigation

### Risk: scope explosion
- Mitigation: hard exclude CCTV, ALPR, and prediction from implementation

### Risk: no real payment integration access
- Mitigation: build adapter + sandbox/mock first

### Risk: incomplete legal penalty rules
- Mitigation: load configurable rules from admin panel, not hard-coded values

### Risk: low connectivity in field
- Mitigation: local draft queue with delayed sync

### Risk: inconsistent documentation
- Mitigation: create one signed-off Phase 1 functional baseline before code

### Risk: dual-client overbuild
- Mitigation: PWA first for officers, full native client later only if still required

## 15. Recommended deliverables

By the end of Phase 1, the project should have:
- source repository
- architecture decision record
- database schema and migrations
- backend API
- officer client
- office/admin web client
- seeded rule and user data
- payment adapter
- test suite
- deployment guide
- pilot rollout guide
- training checklist

## 16. Final judgment

This folder is a strong design baseline but not an implementation baseline.

The fastest credible path to complete Phase 1 is:
- lock scope to manual digital enforcement
- collapse all ambiguous future-phase features out of the build
- choose one backend stack and one relational database
- avoid parallel native-mobile and full web duplication unless resourcing is proven
- deliver one end-to-end enforcement workflow with auditability, complaint handling, and payment state control

If this discipline is kept, Phase 1 is achievable.
If Phase 2 and Phase 3 features are allowed back into the build, Phase 1 will not finish cleanly.
