# Phase 1 Webs Validation Sweep

## Purpose

This document records the manual validation sweep for the Phase 1 Webs sub-phase
and the initial PWA install checks. It is the evidence log for P1-WEB-003,
P1-WEB-005, P1-WEB-006, and P1-PWA-001.

## Environment

- Date: 2026-05-04
- App URL: http://localhost:8080
- Stack startup: `make first-boot`
- Data seed: `python -m app.bootstrap`

## P1-WEB-003: Validation, empty states, and error pages

### Form validation

- Verified `submission_ref` auto-populates with a UUID when empty.
- Empty form returns `form.checkValidity()` false and blocks submission.
- `plate_number` uses `autocapitalize="characters"`.
- Evidence input restricts to `image/*`.
- Invalid login shows the error banner.

### Empty states

- `/violations?q=NO_MATCH` shows the empty-state row.
- `/complaints?status=REVOKED` shows the empty-state row.
- `/payments?status=FAILED` shows the empty-state row.
- `/alerts` filter did not honor invalid status values, so empty state could not be forced.

### Error pages

- Logged-in 404 (`/this-does-not-exist`) renders the error card with navigation.
- Logged-out 404 renders the minimal header with brand only.

## P1-WEB-005: Reporting location auto-capture UX

- Initial load shows "Requesting device location..." status.
- Mocked success reports "Device location captured.", updates lat/lng inputs, and recenters the map at zoom 15.
- Mocked permission denied reports "Location permission denied. Add it manually if needed."
- Mocked unavailable reports "Location unavailable. Add it manually if needed."

## P1-WEB-006: Escape path UX refinements

- Map default view initializes at latitude 7.0621, longitude 38.4767, zoom 15.
- Map clicks add markers, extend the LineString, and update the hidden GeoJSON field.
- Clear path control removes markers, clears the LineString, and empties the hidden field.
- Database verification confirmed `escape_path_geojson` stored as a LineString.

Command used:

```
docker compose exec -T supabase-db psql -U postgres -d postgres -c "select id, reference_code, escape_path_geojson from public.violations order by created_at desc limit 1;"
```

## P1-PWA-001: Manifest and service worker checks

- `GET /manifest.webmanifest` returns 200 with name, start URL, scope, theme color, and icons.
- Icons respond at `/static/images/icon.svg`, `/static/images/icon-180.png`, `/static/images/icon-192.png`, and `/static/images/icon-512.png`.
- Service worker registers and activates with scope `/`.
- Cache `alpr-stms-shell-v2` includes the manifest and icon assets after reload.
- Install prompt could not be forced in the headless run; only registration and asset checks were validated.
