# Route-Aware Alerts and Device Location (Waitlist)

This note captures the planned location and routing enhancements that extend
Phase 1 once the Webs and PWA sub-phases are complete.

## Current Phase 1 behavior

- Reporting uses device geolocation to auto-fill latitude/longitude.
- The escape path is a manually drawn GeoJSON LineString.
- Alerts are broadcast to subcity and system admins only.
- Officer device location is not ingested or tracked.

## Planned requirements

- Map display should open with a familiar mobile scale and consistent zoom.
- Escape paths should snap to the nearest road geometry.
- Derive multiple likely routes from the escape path for predictive routing.
- Send high-priority alerts to officers whose device location is near the
  predicted route alternatives.
- Capture officer device location continuously (with user consent) to keep
  alert targeting accurate.

## Data and integration considerations

- Add a location update stream for officers (table + retention policy).
- Add route candidates linked to a violation (geometry + confidence score).
- Extend alert payloads with route candidates and priority flags.
- Use a map-matching or routing engine (OSRM, Valhalla, or GraphHopper).

## Notes

Keep Phase 1 scope focused on manual enforcement. These enhancements should
be tracked and delivered in a later phase once operational evidence is
captured for the Webs and PWA tracks.
