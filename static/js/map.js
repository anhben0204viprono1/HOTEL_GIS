// static/js/map.js
// Map functionality using Leaflet

let map = null;
let markers = [];

const mapUtils = {
  // Initialize map
  initMap: (elementId, center = [10.8231, 106.6297], zoom = 13) => {
    if (map) {
      map.remove();
    }

    map = L.map(elementId).setView(center, zoom);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    return map;
  },

  // Add marker to map
  addMarker: (lat, lng, popupContent, clickHandler) => {
    const marker = L.marker([lat, lng]).addTo(map);

    if (popupContent) {
      marker.bindPopup(popupContent);
    }

    if (clickHandler) {
      marker.on("click", clickHandler);
    }

    markers.push(marker);
    return marker;
  },

  // Add hotel marker with custom popup
  addHotelMarker: (hotel) => {
    const popupContent = `
            <div class="map-popup">
                <img src="${hotel.ImageURL || "https://via.placeholder.com/200x150"}" alt="${hotel.HotelName}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;">
                <h4 style="margin: 0 0 8px 0; font-size: 1rem;">${hotel.HotelName}</h4>
                <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 8px;">
                    <i class="fas fa-star" style="color: #F39C12;"></i>
                    <span style="font-weight: 600;">${hotel.Rating || "N/A"}</span>
                    <span style="color: #6C757D; font-size: 0.9rem;">(${hotel.TotalReviews || 0} đánh giá)</span>
                </div>
                <div style="color: #6C757D; font-size: 0.9rem; margin-bottom: 8px;">
                    <i class="fas fa-map-marker-alt"></i> ${hotel.Address}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                    <div>
                        <div style="font-size: 0.85rem; color: #6C757D;">Từ</div>
                        <div style="font-size: 1.2rem; color: #FF6B6B; font-weight: 700;">${utils.formatCurrency(hotel.MinPrice || 0)}</div>
                    </div>
                    <button onclick="window.location.href='/hotel/${hotel.HotelID}'" style="background: #FF6B6B; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500;">
                        Xem chi tiết
                    </button>
                </div>
            </div>
        `;

    return mapUtils.addMarker(
      hotel.Latitude,
      hotel.Longitude,
      popupContent,
      () => {
        // Optional: Add custom click handler
      },
    );
  },

  // Clear all markers
  clearMarkers: () => {
    markers.forEach((marker) => marker.remove());
    markers = [];
  },

  // Fit map to markers
  fitToMarkers: () => {
    if (markers.length > 0) {
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds().pad(0.1));
    }
  },

  // Add circle (for distance search)
  addCircle: (lat, lng, radius, color = "#FF6B6B") => {
    const circle = L.circle([lat, lng], {
      color: color,
      fillColor: color,
      fillOpacity: 0.2,
      radius: radius * 1000, // Convert km to meters
    }).addTo(map);

    return circle;
  },

  // Get user location
  getUserLocation: (callback) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          callback({ lat, lng });
        },
        (error) => {
          console.error("Error getting location:", error);
          utils.showToast("Không thể lấy vị trí của bạn", "warning");
        },
      );
    } else {
      utils.showToast("Trình duyệt không hỗ trợ định vị", "warning");
    }
  },

  // Calculate distance between two points
  calculateDistance: (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Radius of the Earth in km
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLng = ((lng2 - lng1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLng / 2) *
        Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    return distance;
  },
};

// Export map utilities
window.mapUtils = mapUtils;
