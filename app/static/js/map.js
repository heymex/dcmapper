const map = L.map("map").setView([39.5, -98.35], 4);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
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
