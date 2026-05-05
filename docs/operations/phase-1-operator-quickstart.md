# Phase 1 Operator Quickstart (Webs)

## Purpose

This quickstart guides Phase 1 operators through the core browser flows:
violation reporting, alert acknowledgement, complaint decisions, and payment
settlement. It also captures the location and escape-path behaviors that are
important for field reporting.

## Access

- App URL (local): http://localhost:8080
- Default accounts (seeded by `app.bootstrap`):
  - Traffic officer: TP1
  - Subcity officer: SC1
  - Complaint officer: CO1
  - Admin: ADMIN1
- Passwords come from `.env` values:
  - OFFICER_DEFAULT_PASSWORD
  - SUBCITY_DEFAULT_PASSWORD
  - COMPLAINT_DEFAULT_PASSWORD
  - ADMIN_DEFAULT_PASSWORD

The default values are defined in `.env.example` for local development.
Rotate them before any production use.

## Start the stack (local)

1. `make first-boot`
2. Open http://localhost:8080
3. Sign in with one of the seeded accounts above.

## Traffic officer workflow (reporting)

1. Sign in as `TP1`.
2. Open the Violations page.
3. Fill in the violation rule, plate, and location description.
4. Allow device location when prompted.
   - The form auto-fills latitude/longitude from device geolocation.
   - A status message confirms when location is captured.
5. Capture evidence photo if available.
6. Tap the map to draw the escape path.
   - Each tap adds a point to the path line.
   - Use Clear path to reset the line if needed.
7. Submit the report (Save and broadcast).
8. Confirm the detail page shows the violation, evidence, and status.

## Subcity officer workflow (alerts)

1. Sign in as `SC1`.
2. Open Alerts.
3. Review the broadcasted alert and acknowledge it.

## Complaint officer workflow (review + payments)

1. Sign in as `CO1`.
2. Open Complaints.
3. For an OPEN complaint:
   - Choose Confirm or Revoke.
   - Add optional decision notes.
4. If confirmed, a payment request is created.
5. Open Payments and simulate the outcome.
   - Success marks the violation paid.
   - Failed keeps the payment request pending for retry.

## Admin workflow (overview)

1. Sign in as `ADMIN1`.
2. Open Admin to review:
   - user counts
   - violations and payments totals
   - audit activity

## Location and escape-path behavior

- Location capture uses device geolocation to auto-fill latitude/longitude.
- The map uses OSM tiles (`MAP_TILE_URL`) and centers on the first location fix.
- Escape paths are manually drawn with map taps and stored as GeoJSON lines.
- Road snapping, route prediction, and live officer location targeting are
   planned enhancements (see [../planning/location-routing-notes.md](../planning/location-routing-notes.md)).

## Webs sub-phase evidence checklist

Capture screenshots during the walkthrough for:

- Login screen
- Violations list + report form
- Alert inbox
- Complaint queue
- Payment queue
- Admin dashboard + audit log

Add the evidence notes to the Phase 1 tracker when complete.
