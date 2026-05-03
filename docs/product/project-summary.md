# Project Summary

## Project Name

Automatic License Plate Recognition Based Smart Traffic Management System for Hawassa City

## Short Summary

This project is a phased government-oriented traffic enforcement platform designed to move Hawassa City from manual and radio-based traffic control toward structured digital enforcement and later smart surveillance support.

## Problem

The current operating model relies heavily on:
- manual observation
- walkie-talkie communication
- fragmented paper or ad hoc records
- weak cross-subcity coordination
- limited traceability

These limitations reduce enforcement speed, accountability, and evidence quality.

## Solution Direction

The system is designed as a four-phase platform:

1. Phase 1: manual digital enforcement and alert broadcasting
2. Phase 2: CCTV-assisted human-validated detection
3. Phase 3: predictive route intelligence
4. Phase 4: advanced automated smart enforcement

## Phase 1 Baseline

This repository is currently centered on **Phase 1** only.

Current Phase 1 progress:

| Track | Status | Notes |
| --- | --- | --- |
| Backend foundation | Complete | Released as `v0.1.0-phase1`; all readiness gates complete |
| Webs sub-phase | In progress | Browser walkthrough, responsive checks, and operator UI polish are the active path |
| Apps/PWA sub-phase | Pending | Starts after Webs evidence is recorded in the master tracker |
| Pilot readiness | Pending | Starts after Webs and PWA checks are complete |

Phase 1 includes:
- officer login and RBAC
- manual violation reporting
- GPS and timestamp capture
- alert broadcasting
- complaint handling
- payment request initiation
- audit logging

Phase 1 excludes:
- live CCTV ingestion
- ALPR/OCR processing
- prediction engines
- automated violation generation

## Primary Actors

- Traffic Officer
- Subcity Officer
- Complaint Officer
- System Administrator

External participants:
- Driver as payment participant only
- Payment Gateway

Future-phase actors:
- CCTV Operator
- CCTV System

## Recommended Technical Position

- Backend: FastAPI
- Frontend: server-rendered web with Jinja2, HTMX, Alpine.js, and Bootstrap 5
- Database: self-hosted Supabase subset using PostgreSQL and PostgREST
- Officer client: mobile-first PWA served by FastAPI
- Office/admin client: web application served by FastAPI
- Evidence storage: self-hosted Supabase Storage API with file backend in Phase 1
- Background processing: Python worker using a database outbox pattern
- Maps: OpenStreetMap-based integration via Leaflet
