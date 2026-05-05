const form = document.querySelector("[data-violation-form]");

if (form instanceof HTMLFormElement) {
  const storageKey = "alpr-stms.violation-draft";
  const submissionRefInput = document.getElementById("submission_ref");
  const latitudeInput = document.getElementById("latitude");
  const longitudeInput = document.getElementById("longitude");
  const pathInput = document.getElementById("escape_path_geojson");
  const mapElement = document.getElementById("escape-path-map");
  const locationStatus = document.getElementById("location-status");
  const clearPathButton = document.querySelector("[data-clear-path]");
  const nearbyMapElement = document.getElementById("nearby-officers-map");
  const nearbyDataElement = document.getElementById("nearby-officers-data");
  let map = null;
  let locationMarker = null;
  let hasCenteredOnLocation = false;
  let lastLocation = null;

  if (submissionRefInput instanceof HTMLInputElement && !submissionRefInput.value) {
    submissionRefInput.value = self.crypto?.randomUUID?.() || `draft-${Date.now()}`;
  }

  const restoreDraft = () => {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) {
      return;
    }
    try {
      const draft = JSON.parse(raw);
      for (const [key, value] of Object.entries(draft)) {
        const field = form.elements.namedItem(key);
        if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement || field instanceof HTMLSelectElement) {
          field.value = value;
        }
      }
    } catch (_) {
      window.localStorage.removeItem(storageKey);
    }
  };

  const persistDraft = () => {
    const payload = {};
    for (const element of form.elements) {
      if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement)) {
        continue;
      }
      if (element.type === "file" || !element.name) {
        continue;
      }
      payload[element.name] = element.value;
    }
    window.localStorage.setItem(storageKey, JSON.stringify(payload));
  };

  restoreDraft();
  form.addEventListener("input", persistDraft);
  form.addEventListener("submit", () => window.localStorage.removeItem(storageKey));

  const setLocationStatus = (message) => {
    if (locationStatus instanceof HTMLElement) {
      locationStatus.textContent = message;
    }
  };

  const updateMapLocation = (lat, lng) => {
    if (!map || !window.L) {
      return;
    }
    const point = [lat, lng];
    if (!locationMarker) {
      locationMarker = window.L.circleMarker(point, {
        radius: 6,
        color: "#1d4ed8",
        fillColor: "#1d4ed8",
        fillOpacity: 0.25,
      }).addTo(map);
    } else {
      locationMarker.setLatLng(point);
    }
    if (!hasCenteredOnLocation) {
      map.setView(point, 15);
      hasCenteredOnLocation = true;
    }
  };

  const applyLocation = (position) => {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    if (latitudeInput instanceof HTMLInputElement) {
      latitudeInput.value = String(lat);
    }
    if (longitudeInput instanceof HTMLInputElement) {
      longitudeInput.value = String(lng);
    }
    lastLocation = { lat, lng };
    const payload = new URLSearchParams({ latitude: String(lat), longitude: String(lng) });
    fetch("/api/officers/location", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload.toString(),
      credentials: "same-origin",
    }).catch(() => null);
    updateMapLocation(lat, lng);
    setLocationStatus("Device location captured.");
    persistDraft();
  };

  const handleLocationError = (error) => {
    if (error && error.code === 1) {
      setLocationStatus("Location permission denied. Add it manually if needed.");
    } else {
      setLocationStatus("Location unavailable. Add it manually if needed.");
    }
  };

  if (navigator.geolocation && latitudeInput instanceof HTMLInputElement && longitudeInput instanceof HTMLInputElement) {
    setLocationStatus("Requesting device location...");
    const geoOptions = { enableHighAccuracy: true, maximumAge: 10000, timeout: 10000 };
    navigator.geolocation.getCurrentPosition(applyLocation, handleLocationError, geoOptions);
    navigator.geolocation.watchPosition(applyLocation, handleLocationError, geoOptions);
  } else {
    setLocationStatus("Device location not supported. Add it manually if needed.");
  }

  if (mapElement && window.L) {
    const initialLat = parseFloat(latitudeInput?.value || "7.0621");
    const initialLng = parseFloat(longitudeInput?.value || "38.4767");
    map = window.L.map(mapElement).setView([initialLat, initialLng], 15);
    const markers = [];
    const polyline = window.L.polyline([], { color: "#1d4ed8", weight: 4 }).addTo(map);

    window.L.tileLayer(window.document.body.dataset.tiles || "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    const syncPath = () => {
      const latlngs = polyline.getLatLngs();
      if (pathInput instanceof HTMLInputElement) {
        pathInput.value = JSON.stringify({
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates: latlngs.map((point) => [point.lng, point.lat]),
          },
          properties: {},
        });
      }
      persistDraft();
    };

    map.on("click", (event) => {
      if (polyline.getLatLngs().length === 0 && lastLocation) {
        polyline.addLatLng([lastLocation.lat, lastLocation.lng]);
      }
      const point = [event.latlng.lat, event.latlng.lng];
      markers.push(window.L.circleMarker(point, { radius: 4, color: "#0f766e" }).addTo(map));
      polyline.addLatLng(point);
      syncPath();
    });

    if (clearPathButton instanceof HTMLButtonElement) {
      clearPathButton.addEventListener("click", () => {
        markers.forEach((marker) => marker.remove());
        markers.length = 0;
        polyline.setLatLngs([]);
        if (pathInput instanceof HTMLInputElement) {
          pathInput.value = "";
        }
        persistDraft();
      });
    }

    if (pathInput instanceof HTMLInputElement && pathInput.value) {
      try {
        const existing = JSON.parse(pathInput.value);
        const coordinates = existing.geometry?.coordinates || [];
        coordinates.forEach(([lng, lat]) => {
          markers.push(window.L.circleMarker([lat, lng], { radius: 4, color: "#0f766e" }).addTo(map));
          polyline.addLatLng([lat, lng]);
        });
      } catch (_) {
        pathInput.value = "";
      }
    }

    if (lastLocation) {
      updateMapLocation(lastLocation.lat, lastLocation.lng);
    }
  }

  if (nearbyMapElement && window.L) {
    const nearbyMap = window.L.map(nearbyMapElement).setView([7.0621, 38.4767], 13);
    window.L.tileLayer(window.document.body.dataset.tiles || "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(nearbyMap);
    if (nearbyDataElement) {
      try {
        const officers = JSON.parse(nearbyDataElement.textContent || "[]");
        officers.forEach((officer) => {
          const lat = parseFloat(officer.latitude);
          const lng = parseFloat(officer.longitude);
          if (Number.isNaN(lat) || Number.isNaN(lng)) {
            return;
          }
          window.L.marker([lat, lng]).addTo(nearbyMap).bindPopup(`${officer.username} - ${officer.full_name}`);
        });
      } catch (_) {
        // ignore parse issues for optional map payload
      }
    }
  }
}

