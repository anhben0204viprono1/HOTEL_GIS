// static/js/search.js
// Search page functionality

document.addEventListener("DOMContentLoaded", () => {
  initSearchPage();
});

let currentHotels = [];
let currentFilters = {
  minPrice: null,
  maxPrice: null,
  minRating: null,
  distance: null,
  amenities: [],
  city: null,
  district: null,
  lat: null,
  lng: null,
};

function initSearchPage() {
  // Check if we're on search page
  if (!document.getElementById("searchResults")) return;

  // Load filters from URL
  loadFiltersFromURL();

  // Setup event listeners
  setupFilterListeners();
  setupSortListener();
  setupViewToggle();

  // Perform initial search
  performSearch();
}

function loadFiltersFromURL() {
  const params = new URLSearchParams(window.location.search);

  currentFilters.city = params.get("city");
  currentFilters.district = params.get("district");
  currentFilters.minPrice = params.get("min_price");
  currentFilters.maxPrice = params.get("max_price");
  currentFilters.minRating = params.get("min_rating");
  currentFilters.distance = params.get("distance");
  currentFilters.lat = params.get("lat");
  currentFilters.lng = params.get("lng");

  // Set form values
  if (currentFilters.city) {
    const locationInput = document.getElementById("searchLocation");
    if (locationInput) locationInput.value = currentFilters.city;
  }

  if (currentFilters.minPrice) {
    const minPriceInput = document.getElementById("minPrice");
    if (minPriceInput) minPriceInput.value = currentFilters.minPrice;
  }

  if (currentFilters.maxPrice) {
    const maxPriceInput = document.getElementById("maxPrice");
    if (maxPriceInput) maxPriceInput.value = currentFilters.maxPrice;
  }
}

function setupFilterListeners() {
  // Price filter
  const priceRange = document.getElementById("priceRange");
  const minPriceInput = document.getElementById("minPrice");
  const maxPriceInput = document.getElementById("maxPrice");

  if (priceRange) {
    priceRange.addEventListener("input", (e) => {
      maxPriceInput.value = e.target.value;
      currentFilters.maxPrice = e.target.value;
      performSearch();
    });
  }

  if (minPriceInput) {
    minPriceInput.addEventListener("change", (e) => {
      currentFilters.minPrice = e.target.value;
      performSearch();
    });
  }

  if (maxPriceInput) {
    maxPriceInput.addEventListener("change", (e) => {
      currentFilters.maxPrice = e.target.value;
      if (priceRange) priceRange.value = e.target.value;
      performSearch();
    });
  }

  // Rating filter
  const ratingFilters = document.querySelectorAll(".rating-filter");
  ratingFilters.forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const ratings = Array.from(
        document.querySelectorAll(".rating-filter:checked"),
      ).map((cb) => parseFloat(cb.value));
      currentFilters.minRating =
        ratings.length > 0 ? Math.min(...ratings) : null;
      performSearch();
    });
  });

  // Distance filter
  const distanceRange = document.getElementById("distanceRange");
  const distanceValue = document.getElementById("distanceValue");

  if (distanceRange) {
    distanceRange.addEventListener("input", (e) => {
      const distance = e.target.value;
      distanceValue.textContent = `Trong vòng ${distance} km`;
      currentFilters.distance = distance;
      performSearch();
    });
  }

  // Use location button
  const btnUseLocation = document.querySelector(".btn-use-location");
  if (btnUseLocation) {
    btnUseLocation.addEventListener("click", () => {
      mapUtils.getUserLocation((coords) => {
        currentFilters.lat = coords.lat;
        currentFilters.lng = coords.lng;
        performSearch();
        utils.showToast("Đã cập nhật vị trí của bạn", "success");
      });
    });
  }

  // Amenities filter
  const amenityFilters = document.querySelectorAll(".amenity-filter");
  amenityFilters.forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      currentFilters.amenities = Array.from(
        document.querySelectorAll(".amenity-filter:checked"),
      ).map((cb) => cb.value);
      performSearch();
    });
  });

  // Clear filters
  const btnClearFilters = document.querySelector(".btn-clear-filters");
  if (btnClearFilters) {
    btnClearFilters.addEventListener("click", () => {
      clearFilters();
    });
  }

  // Search button
  const searchBar = document.querySelector(".search-bar-sticky .btn-primary");
  if (searchBar) {
    searchBar.addEventListener("click", () => {
      const location = document.getElementById("searchLocation").value;
      if (location) {
        currentFilters.city = location;
        performSearch();
      }
    });
  }
}

function setupSortListener() {
  const sortSelect = document.getElementById("sortBy");
  if (sortSelect) {
    sortSelect.addEventListener("change", (e) => {
      sortHotels(e.target.value);
    });
  }
}

function setupViewToggle() {
  const viewButtons = document.querySelectorAll(".view-btn");
  const searchResults = document.getElementById("searchResults");
  const mapContainer = document.getElementById("mapContainer");

  viewButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      viewButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const view = btn.dataset.view;
      if (view === "map") {
        searchResults.style.display = "none";
        mapContainer.style.display = "block";
        initializeMap();
      } else {
        searchResults.style.display = "flex";
        mapContainer.style.display = "none";
      }
    });
  });
}

async function performSearch() {
  const searchResults = document.getElementById("searchResults");
  searchResults.innerHTML =
    '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Đang tìm kiếm khách sạn...</p></div>';

  try {
    const params = {};
    if (currentFilters.city) params.city = currentFilters.city;
    if (currentFilters.district) params.district = currentFilters.district;
    if (currentFilters.minPrice) params.min_price = currentFilters.minPrice;
    if (currentFilters.maxPrice) params.max_price = currentFilters.maxPrice;
    if (currentFilters.minRating) params.min_rating = currentFilters.minRating;
    if (currentFilters.distance) params.distance = currentFilters.distance;
    if (currentFilters.lat) params.lat = currentFilters.lat;
    if (currentFilters.lng) params.lng = currentFilters.lng;

    const response = await api.searchHotels(params);

    if (response.success) {
      currentHotels = response.data;
      displayHotels(currentHotels);
      updateResultCount(currentHotels.length);
    } else {
      searchResults.innerHTML =
        '<div class="empty-state"><i class="fas fa-search"></i><h3>Không tìm thấy khách sạn</h3><p>Vui lòng thử lại với bộ lọc khác</p></div>';
    }
  } catch (error) {
    searchResults.innerHTML =
      '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h3>Có lỗi xảy ra</h3><p>Vui lòng thử lại sau</p></div>';
  }
}

function displayHotels(hotels) {
  const searchResults = document.getElementById("searchResults");

  if (hotels.length === 0) {
    searchResults.innerHTML =
      '<div class="empty-state"><i class="fas fa-search"></i><h3>Không tìm thấy khách sạn</h3><p>Vui lòng thử lại với bộ lọc khác</p></div>';
    return;
  }

  searchResults.innerHTML = hotels
    .map((hotel) => createHotelCard(hotel))
    .join("");
}

function createHotelCard(hotel) {
  const distanceBadge = hotel.Distance
    ? `<div class="distance-badge"><i class="fas fa-map-marker-alt"></i> ${hotel.Distance} km</div>`
    : "";

  return `
        <div class="hotel-card" onclick="window.location.href='/hotel/${hotel.HotelID}'">
            <div class="hotel-card-image">
                <img src="${hotel.ImageURL || "https://via.placeholder.com/300x250"}" alt="${hotel.HotelName}">
                <button class="hotel-card-favorite" onclick="event.stopPropagation(); toggleFavorite(${hotel.HotelID})">
                    <i class="far fa-heart"></i>
                </button>
            </div>
            <div class="hotel-card-body">
                <div class="hotel-card-header">
                    <div>
                        <h3>${hotel.HotelName}</h3>
                        <div class="rating">
                            <i class="fas fa-star"></i>
                            <span>${hotel.Rating || "N/A"}</span>
                            <span class="reviews">(${hotel.TotalReviews || 0} đánh giá)</span>
                        </div>
                    </div>
                </div>
                <div class="hotel-meta">
                    <p><i class="fas fa-map-marker-alt"></i> ${hotel.Address}, ${hotel.City}</p>
                    <p><i class="fas fa-phone"></i> ${hotel.PhoneNumber || "N/A"}</p>
                </div>
                <div class="hotel-amenities">
                    <span class="amenity-badge"><i class="fas fa-wifi"></i> WiFi</span>
                    <span class="amenity-badge"><i class="fas fa-parking"></i> Parking</span>
                    <span class="amenity-badge"><i class="fas fa-swimming-pool"></i> Pool</span>
                </div>
            </div>
            <div class="hotel-card-price">
                ${distanceBadge}
                <div class="price-display">
                    <span class="price-label">Giá từ</span>
                    <span class="price">${utils.formatCurrency(hotel.MinPrice || 0)}</span>
                    <span class="price-per-night">/ đêm</span>
                </div>
                <button class="btn btn-primary btn-view-details" onclick="event.stopPropagation(); window.location.href='/hotel/${hotel.HotelID}'">
                    Xem chi tiết
                </button>
            </div>
        </div>
    `;
}

function sortHotels(sortBy) {
  let sortedHotels = [...currentHotels];

  switch (sortBy) {
    case "price_asc":
      sortedHotels.sort((a, b) => (a.MinPrice || 0) - (b.MinPrice || 0));
      break;
    case "price_desc":
      sortedHotels.sort((a, b) => (b.MinPrice || 0) - (a.MinPrice || 0));
      break;
    case "rating":
      sortedHotels.sort((a, b) => (b.Rating || 0) - (a.Rating || 0));
      break;
    case "distance":
      sortedHotels.sort((a, b) => (a.Distance || 999) - (b.Distance || 999));
      break;
    default:
      // Recommended - keep current order
      break;
  }

  displayHotels(sortedHotels);
}

function updateResultCount(count) {
  const resultCount = document.getElementById("resultCount");
  if (resultCount) {
    resultCount.textContent = `Tìm thấy ${count} khách sạn`;
  }
}

function clearFilters() {
  currentFilters = {
    minPrice: null,
    maxPrice: null,
    minRating: null,
    distance: null,
    amenities: [],
    city: null,
    district: null,
    lat: null,
    lng: null,
  };

  // Clear form inputs
  document.getElementById("minPrice").value = "";
  document.getElementById("maxPrice").value = "";
  document.getElementById("priceRange").value = 5000000;

  document
    .querySelectorAll(".rating-filter:checked")
    .forEach((cb) => (cb.checked = false));
  document
    .querySelectorAll(".amenity-filter:checked")
    .forEach((cb) => (cb.checked = false));

  performSearch();
}

function initializeMap() {
  if (!mapUtils || !window.L) return;

  const center =
    currentFilters.lat && currentFilters.lng
      ? [currentFilters.lat, currentFilters.lng]
      : [10.8231, 106.6297]; // Default to Ho Chi Minh City

  mapUtils.initMap("map", center, 13);

  // Add hotel markers
  currentHotels.forEach((hotel) => {
    if (hotel.Latitude && hotel.Longitude) {
      mapUtils.addHotelMarker(hotel);
    }
  });

  // Fit map to show all markers
  mapUtils.fitToMarkers();

  // Add circle if distance filter is active
  if (currentFilters.distance && currentFilters.lat && currentFilters.lng) {
    mapUtils.addCircle(
      currentFilters.lat,
      currentFilters.lng,
      parseFloat(currentFilters.distance),
    );
  }
}

function toggleFavorite(hotelId) {
  // Implement favorite functionality
  utils.showToast("Đã thêm vào danh sách yêu thích", "success");
}
