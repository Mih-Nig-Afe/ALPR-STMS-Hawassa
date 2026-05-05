# Phase 1 Webs Walkthrough Evidence

## Purpose

This document records the manual walkthrough for the Phase 1 Webs sub-phase.
It is the evidence log for P1-WEB-001 and the foundation for screenshot
capture. Store screenshots under `docs/operations/screenshots/` using the
filenames listed below.

## Environment

- Date: 2026-05-04
- App URL: http://localhost:8080
- Stack startup: `make first-boot`
- Data seed: `python -m app.bootstrap`

## Accounts used

- TP1 (Traffic Officer)
- SC1 (Subcity Officer)
- CO1 (Complaint Officer)
- ADMIN1 (System Administrator)

Passwords are defined in `.env`:
`OFFICER_DEFAULT_PASSWORD`, `SUBCITY_DEFAULT_PASSWORD`,
`COMPLAINT_DEFAULT_PASSWORD`, `ADMIN_DEFAULT_PASSWORD`.

## Walkthrough steps

### 1) Login screen

- Open `/auth/login`
- Confirm login form, seeded account hints, and password toggle

Screenshot: `login.png`

### 2) Traffic officer - Violations

- Sign in as `TP1`
- Confirm the violation report form renders
- Confirm location auto-capture status message appears
- Use the map to draw an escape path and clear it once
- Submit the form and land on the detail page

Screenshots:
- `violations-form.png`
- `violations-detail.png`

### 3) Subcity officer - Alerts

- Sign in as `SC1`
- Open `/alerts`
- Acknowledge the new alert

Screenshot: `alerts-inbox.png`

### 4) Complaint officer - Complaints

- Sign in as `CO1`
- Open `/complaints`
- Confirm a complaint and add notes

Screenshot: `complaints-queue.png`

### 5) Complaint officer - Payments

- Open `/payments`
- Simulate a successful callback

Screenshot: `payments-queue.png`

### 6) Admin - Overview

- Sign in as `ADMIN1`
- Open `/admin`
- Confirm stats and audit table render

Screenshot: `admin-dashboard.png`

## Notes

- Location auto-capture uses device geolocation with status feedback.
- Escape path is captured as a GeoJSON LineString from map clicks.
- Route-aware alerting and officer location targeting are waitlisted.

## Run log

- 2026-05-04: Walkthrough completed; all screenshots captured in `docs/operations/screenshots/`.
- 2026-05-04: Location capture validated using a mocked browser geolocation during the walkthrough session.

## Screenshot checklist

Store files in `docs/operations/screenshots/`:

- login.png
- violations-form.png
- violations-detail.png
- alerts-inbox.png
- complaints-queue.png
- payments-queue.png
- admin-dashboard.png
