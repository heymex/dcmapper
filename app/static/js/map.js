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

async function loadLocations() {
  const res = await fetch("/api/locations", { method: "GET" });
  if (!res.ok) {
    return;
  }

  const locations = await res.json();
  if (!locations.length) {
    return;
  }

  const markers = [];
  locations.forEach((loc) => {
    const marker = L.marker([loc.latitude, loc.longitude]).addTo(map);
    marker.bindPopup(`
      <strong>${loc.name}</strong><br/>
      Type: ${loc.entity_type}<br/>
      City: ${loc.city || "n/a"}<br/>
      Operator: ${loc.operator || "n/a"}<br/>
      Confidence: ${loc.confidence}/5
    `);
    markers.push(marker);
  });

  const group = L.featureGroup(markers);
  map.fitBounds(group.getBounds().pad(0.15));
}

loadLocations();
