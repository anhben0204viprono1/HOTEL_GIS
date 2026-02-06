document.addEventListener("DOMContentLoaded", function () {
  initHotelDetailPage();
});

function initHotelDetailPage() {
  loadHotelFromTemplate();
}



function renderHotels(hotels) {
  const list = document.getElementById("hotel-list");
  list.innerHTML = "";

  hotels.forEach(h => {
    list.innerHTML += `
      <div class="hotel-card">
        <h3>${h.name}</h3>
        <p>${h.address}</p>
        <p>⭐ ${h.star_rating ?? "N/A"}</p>
        <hr>
      </div>
    `;
  });
}


function renderMap(hotels) {
  if (hotels.length === 0) return;

  const map = L.map("map").setView(
    [hotels[0].lat, hotels[0].lng],
    13
  );

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

  hotels.forEach(h => {
    L.marker([h.lat, h.lng])
      .addTo(map)
      .bindPopup(`<b>${h.name}</b><br>${h.address}`);
  });
}
