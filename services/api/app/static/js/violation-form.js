const form = document.querySelector("[data-violation-form]");

if (form instanceof HTMLFormElement) {
  const storageKey = "alpr-stms.violation-draft";
  const submissionRefInput = document.getElementById("submission_ref");
  const latitudeInput = document.getElementById("latitude");
  const longitudeInput = document.getElementById("longitude");
  const pathInput = document.getElementById("escape_path_geojson");
  const mapElement = document.getElementById("escape-path-map");

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

  if (navigator.geolocation && latitudeInput instanceof HTMLInputElement && longitudeInput instanceof HTMLInputElement) {
    navigator.geolocation.getCurrentPosition((position) => {
      latitudeInput.value = String(position.coords.latitude);
      longitudeInput.value = String(position.coords.longitude);
      persistDraft();
    });
  }

  if (mapElement && window.L) {
    const initialLat = parseFloat(latitudeInput?.value || "7.0621");
    const initialLng = parseFloat(longitudeInput?.value || "38.4767");
    const map = window.L.map(mapElement).setView([initialLat, initialLng], 14);
    const markers = [];
    const polyline = window.L.polyline([], { color: "#1d4ed8", weight: 4 }).addTo(map);

    window.L.tileLayer(window.document.body.dataset.tiles || "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    const syncPath = () => {
      const latlngs = polyline.getLatLngs();
      pathInput.value = JSON.stringify({
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: latlngs.map((point) => [point.lng, point.lat]),
        },
        properties: {},
      });
      persistDraft();
    };

    map.on("click", (event) => {
      const point = [event.latlng.lat, event.latlng.lng];
      markers.push(window.L.circleMarker(point, { radius: 4, color: "#0f766e" }).addTo(map));
      polyline.addLatLng(point);
      syncPath();
    });

    if (pathInput.value) {
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
  }
}

