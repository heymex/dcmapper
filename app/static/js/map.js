delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "/static/img/leaflet/marker-icon-2x.png",
  iconUrl: "/static/img/leaflet/marker-icon.png",
  shadowUrl: "/static/img/leaflet/marker-shadow.png",
});

const map = L.map("map").setView([44.02, -92.47], 11);

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
  subdomains: "abcd",
  maxZoom: 20,
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
}).addTo(map);

const restrictionLayer = L.layerGroup().addTo(map);
const facilityMarkers = [];

function formatRestrictionDates(restriction) {
  const start = restriction.start_date || "—";
  const end = restriction.end_date || "—";
  return `${start} → ${end}`;
}

function restrictionStyle(restriction) {
  const kind = restriction.restriction_kind;
  const status = restriction.display_status;

  if (status === "proposed") {
    return {
      color: "#fbbf24",
      fillColor: "#fbbf24",
      fillOpacity: 0.2,
      weight: 2,
      dashArray: "6 4",
    };
  }
  if (kind === "ban") {
    return {
      color: "#ef4444",
      fillColor: "#ef4444",
      fillOpacity: 0.28,
      weight: 2,
    };
  }
  if (status === "expired") {
    return {
      color: "#94a3b8",
      fillColor: "#94a3b8",
      fillOpacity: 0.12,
      weight: 1,
      dashArray: "4 4",
    };
  }
  return {
    color: "#f97316",
    fillColor: "#f97316",
    fillOpacity: 0.25,
    weight: 2,
  };
}

function restrictionPopup(restriction) {
  const kindLabel =
    restriction.restriction_kind === "ban" ? "Permanent ban" : "Moratorium";
  return `
    <strong>${restriction.name}</strong><br/>
    ${kindLabel} · ${restriction.display_status}<br/>
    Dates: ${formatRestrictionDates(restriction)}<br/>
    ${restriction.notes || ""}
  `;
}

async function loadRestrictions() {
  const res = await fetch("/api/restrictions", { method: "GET" });
  if (!res.ok) {
    return;
  }

  const restrictions = await res.json();
  restrictions.forEach((restriction) => {
    const layer = L.geoJSON(
      { type: "Feature", geometry: restriction.geometry, properties: {} },
      { style: () => restrictionStyle(restriction) },
    );
    layer.bindPopup(restrictionPopup(restriction));
    restrictionLayer.addLayer(layer);
  });
}

async function loadLocations() {
  const res = await fetch("/api/locations", { method: "GET" });
  if (!res.ok) {
    return;
  }

  const locations = await res.json();
  locations.forEach((loc) => {
    const marker = L.marker([loc.latitude, loc.longitude]).addTo(map);
    marker.bindPopup(`
      <strong>${loc.name}</strong><br/>
      Type: ${loc.entity_type}<br/>
      City: ${loc.city || "n/a"}<br/>
      Operator: ${loc.operator || "n/a"}<br/>
      Confidence: ${loc.confidence}/5
    `);
    facilityMarkers.push(marker);
  });

  const layers = [...facilityMarkers];
  restrictionLayer.eachLayer((layer) => layers.push(layer));
  if (layers.length) {
    map.fitBounds(L.featureGroup(layers).getBounds().pad(0.12));
  }
}

loadRestrictions();
loadLocations();
