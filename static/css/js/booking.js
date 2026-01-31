// static/js/booking.js
// Booking page functionality

document.addEventListener("DOMContentLoaded", () => {
  initBookingPage();
  initHotelDetailPage();
});

let currentBookingData = {
  hotelId: null,
  roomId: null,
  checkin: null,
  checkout: null,
  guests: 2,
  totalPrice: 0,
};

function initHotelDetailPage() {
  if (!window.location.pathname.includes("/hotel/")) return;

  const hotelId = window.location.pathname.split("/hotel/")[1];
  if (hotelId) {
    loadHotelDetails(hotelId);
  }

  // Setup booking form
  setupBookingForm();

  // Setup gallery
  setupGallery();
}

async function loadHotelDetails(hotelId) {
  try {
    utils.showLoading();
    const response = await api.getHotelDetails(hotelId);

    if (response.success) {
      displayHotelDetails(response.data);
      currentBookingData.hotelId = hotelId;
    }
    utils.hideLoading();
  } catch (error) {
    utils.hideLoading();
    console.error("Error loading hotel details:", error);
  }
}

function displayHotelDetails(hotel) {
  // Set hotel information
  document.getElementById("hotelName").textContent = hotel.HotelName;
  document.getElementById("hotelRating").textContent = hotel.Rating || "N/A";
  document.getElementById("hotelReviews").textContent =
    `(${hotel.TotalReviews || 0} đánh giá)`;
  document.getElementById("hotelAddress").textContent = hotel.Address;
  document.getElementById("hotelDescription").textContent = hotel.Description;

  // Set main image
  const mainImage = document.getElementById("mainImage");
  if (mainImage) {
    mainImage.src = hotel.ImageURL || "https://via.placeholder.com/800x500";
  }

  // Display amenities
  const amenitiesContainer = document.getElementById("hotelAmenities");
  if (amenitiesContainer && hotel.Amenities) {
    amenitiesContainer.innerHTML = hotel.Amenities.map(
      (amenity) => `
            <div class="amenity-item">
                <i class="fas fa-${amenity.Icon || "check"}"></i>
                <span>${amenity.AmenityName}</span>
            </div>
        `,
    ).join("");
  }

  // Display rooms
  const roomsList = document.getElementById("roomsList");
  if (roomsList && hotel.RoomTypes) {
    roomsList.innerHTML = hotel.RoomTypes.map((room) =>
      createRoomCard(room),
    ).join("");

    // Populate room type select
    const roomSelect = document.getElementById("bookingRoomType");
    if (roomSelect) {
      roomSelect.innerHTML = hotel.RoomTypes.map(
        (room) => `
                <option value="${room.RoomTypeID}" data-price="${room.MinPrice}">
                    ${room.RoomTypeName} - ${utils.formatCurrency(room.MinPrice)}/đêm
                </option>
            `,
      ).join("");
    }
  }

  // Display reviews
  const reviewsList = document.getElementById("reviewsList");
  if (reviewsList && hotel.Reviews) {
    reviewsList.innerHTML = hotel.Reviews.map((review) =>
      createReviewCard(review),
    ).join("");
  }

  // Initialize map
  if (hotel.Latitude && hotel.Longitude) {
    setTimeout(() => {
      mapUtils.initMap("hotelMap", [hotel.Latitude, hotel.Longitude], 15);
      mapUtils.addMarker(hotel.Latitude, hotel.Longitude, hotel.HotelName);
    }, 100);

    document.getElementById("mapAddress").textContent = hotel.Address;
  }

  // Update review summary
  document.getElementById("avgRating").textContent = hotel.Rating || "0.0";
  document.getElementById("totalReviews").textContent =
    `${hotel.TotalReviews || 0} đánh giá`;
}

function createRoomCard(room) {
  return `
        <div class="room-card">
            <div class="room-card-image">
                <img src="${room.ImageURL || "https://via.placeholder.com/250x200"}" alt="${room.RoomTypeName}">
            </div>
            <div class="room-card-info">
                <h4>${room.RoomTypeName}</h4>
                <p>${room.Description || ""}</p>
                <div class="room-features">
                    <span><i class="fas fa-users"></i> ${room.MaxGuests} khách</span>
                    <span><i class="fas fa-bed"></i> ${room.BedType}</span>
                    <span><i class="fas fa-expand"></i> ${room.RoomSize} m²</span>
                </div>
            </div>
            <div class="room-card-price">
                <div class="price-display">
                    <span class="price">${utils.formatCurrency(room.MinPrice)}</span>
                    <span class="price-per-night">/ đêm</span>
                </div>
                <button class="btn btn-primary" onclick="selectRoom(${room.RoomTypeID}, ${room.MinPrice})">
                    Chọn phòng
                </button>
            </div>
        </div>
    `;
}

function createReviewCard(review) {
  const initial = review.CustomerName
    ? review.CustomerName.charAt(0).toUpperCase()
    : "U";

  return `
        <div class="review-card">
            <div class="review-header">
                <div class="reviewer-info">
                    <div class="reviewer-avatar">${initial}</div>
                    <div class="reviewer-details">
                        <h5>${review.CustomerName}</h5>
                        <div class="review-date">${utils.formatDate(review.ReviewDate)}</div>
                    </div>
                </div>
                <div class="review-rating">
                    ${createStarRating(review.Rating)}
                </div>
            </div>
            <p>${review.Comment}</p>
        </div>
    `;
}

function createStarRating(rating) {
  let stars = "";
  for (let i = 1; i <= 5; i++) {
    stars += `<i class="fas fa-star" style="color: ${i <= rating ? "#F39C12" : "#DEE2E6"}"></i>`;
  }
  return stars;
}

function selectRoom(roomTypeId, price) {
  currentBookingData.roomId = roomTypeId;

  // Scroll to booking card
  document
    .querySelector(".booking-card")
    .scrollIntoView({ behavior: "smooth" });

  // Set room type in select
  const roomSelect = document.getElementById("bookingRoomType");
  if (roomSelect) {
    roomSelect.value = roomTypeId;
    updateBookingPrice();
  }
}

function setupBookingForm() {
  const bookingForm = document.getElementById("bookingForm");
  if (!bookingForm) return;

  // Date change listeners
  const checkinInput = document.getElementById("bookingCheckin");
  const checkoutInput = document.getElementById("bookingCheckout");
  const roomSelect = document.getElementById("bookingRoomType");

  if (checkinInput) {
    checkinInput.addEventListener("change", () => {
      currentBookingData.checkin = checkinInput.value;
      updateBookingPrice();
    });
  }

  if (checkoutInput) {
    checkoutInput.addEventListener("change", () => {
      currentBookingData.checkout = checkoutInput.value;
      updateBookingPrice();
    });
  }

  if (roomSelect) {
    roomSelect.addEventListener("change", () => {
      const selectedOption = roomSelect.options[roomSelect.selectedIndex];
      currentBookingData.roomId = roomSelect.value;
      updateBookingPrice();
    });
  }

  // Form submission
  bookingForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const hotelId = currentBookingData.hotelId;
    const params = new URLSearchParams({
      hotel_id: hotelId,
      room_id: document.getElementById("bookingRoomType").value,
      checkin: document.getElementById("bookingCheckin").value,
      checkout: document.getElementById("bookingCheckout").value,
      guests: document.getElementById("bookingGuests").value,
    });
    window.location.href = `/booking?${params.toString()}`;
  });
}

function updateBookingPrice() {
  const checkin = document.getElementById("bookingCheckin")?.value;
  const checkout = document.getElementById("bookingCheckout")?.value;
  const roomSelect = document.getElementById("bookingRoomType");

  if (!checkin || !checkout || !roomSelect) return;

  const selectedOption = roomSelect.options[roomSelect.selectedIndex];
  const pricePerNight = parseFloat(selectedOption.dataset.price) || 0;
  const nights = utils.calculateNights(checkin, checkout);

  const subtotal = pricePerNight * nights;
  const serviceFee = subtotal * 0.05; // 5% service fee
  const total = subtotal + serviceFee;

  // Update display
  document.getElementById("nightsCount").textContent = `${nights} đêm`;
  document.getElementById("nightsPrice").textContent =
    utils.formatCurrency(subtotal);
  document.getElementById("serviceFee").textContent =
    utils.formatCurrency(serviceFee);
  document.getElementById("totalPrice").textContent =
    utils.formatCurrency(total);

  currentBookingData.totalPrice = total;
}

function setupGallery() {
  // Gallery navigation (if implemented)
  const prevBtn = document.querySelector(".gallery-btn.prev");
  const nextBtn = document.querySelector(".gallery-btn.next");

  // Implement gallery navigation here if needed
}

// Booking confirmation page
function initBookingPage() {
  if (!window.location.pathname.includes("/booking")) return;

  loadBookingSummary();
  setupPaymentForm();
  setupBookingConfirmation();
}

function loadBookingSummary() {
  const params = new URLSearchParams(window.location.search);
  const hotelId = params.get("hotel_id");
  const roomId = params.get("room_id");
  const checkin = params.get("checkin");
  const checkout = params.get("checkout");
  const guests = params.get("guests");

  // Store in currentBookingData
  currentBookingData = {
    hotelId,
    roomId,
    checkin,
    checkout,
    guests,
    totalPrice: 0,
  };

  // Display booking summary
  if (checkin)
    document.getElementById("summaryCheckin").textContent =
      utils.formatDate(checkin);
  if (checkout)
    document.getElementById("summaryCheckout").textContent =
      utils.formatDate(checkout);
  if (guests)
    document.getElementById("summaryGuests").textContent = `${guests} người`;

  if (checkin && checkout) {
    const nights = utils.calculateNights(checkin, checkout);
    document.getElementById("summaryNights").textContent = `${nights} đêm`;

    // Calculate price (you should get actual price from API)
    const pricePerNight = 1500000; // Example price
    const subtotal = pricePerNight * nights;
    const serviceFee = subtotal * 0.05;
    const taxFee = subtotal * 0.1;
    const total = subtotal + serviceFee + taxFee;

    document.getElementById("priceDetail").textContent =
      `${utils.formatCurrency(pricePerNight)} x ${nights} đêm`;
    document.getElementById("roomTotal").textContent =
      utils.formatCurrency(subtotal);
    document.getElementById("serviceFee").textContent =
      utils.formatCurrency(serviceFee);
    document.getElementById("taxFee").textContent =
      utils.formatCurrency(taxFee);
    document.getElementById("totalPrice").textContent =
      utils.formatCurrency(total);

    currentBookingData.totalPrice = total;
  }

  // Load hotel details for summary
  if (hotelId) {
    loadHotelForBooking(hotelId);
  }
}

async function loadHotelForBooking(hotelId) {
  try {
    const response = await api.getHotelDetails(hotelId);
    if (response.success) {
      const hotel = response.data;
      document.getElementById("summaryHotelName").textContent = hotel.HotelName;
      document.getElementById("summaryRating").textContent =
        hotel.Rating || "N/A";
      document.getElementById("summaryAddress").textContent = hotel.Address;
      document.getElementById("summaryHotelImage").src =
        hotel.ImageURL || "https://via.placeholder.com/100";
    }
  } catch (error) {
    console.error("Error loading hotel for booking:", error);
  }
}

function setupPaymentForm() {
  const paymentMethods = document.querySelectorAll('input[name="payment"]');
  const creditCardForm = document.getElementById("creditCardForm");

  paymentMethods.forEach((method) => {
    method.addEventListener("change", (e) => {
      if (e.target.value === "credit-card") {
        creditCardForm.style.display = "block";
      } else {
        creditCardForm.style.display = "none";
      }
    });
  });

  // Format card number
  const cardNumber = document.getElementById("cardNumber");
  if (cardNumber) {
    cardNumber.addEventListener("input", (e) => {
      let value = e.target.value.replace(/\s/g, "");
      let formattedValue = value.match(/.{1,4}/g)?.join(" ") || value;
      e.target.value = formattedValue;
    });
  }

  // Format expiry date
  const cardExpiry = document.getElementById("cardExpiry");
  if (cardExpiry) {
    cardExpiry.addEventListener("input", (e) => {
      let value = e.target.value.replace(/\D/g, "");
      if (value.length >= 2) {
        value = value.slice(0, 2) + "/" + value.slice(2, 4);
      }
      e.target.value = value;
    });
  }
}

function setupBookingConfirmation() {
  const confirmBtn = document.getElementById("confirmBookingBtn");
  if (!confirmBtn) return;

  confirmBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    // Validate form
    if (!validateForm("customerInfoForm")) {
      utils.showToast("Vui lòng điền đầy đủ thông tin", "warning");
      return;
    }

    const agreeTerms = document.getElementById("agreeTerms");
    if (!agreeTerms.checked) {
      utils.showToast("Vui lòng đồng ý với điều khoản", "warning");
      return;
    }

    try {
      utils.showLoading();

      // Collect booking data
      const bookingData = {
        customer_id: 1, // Should come from logged in user
        hotel_id: currentBookingData.hotelId,
        room_id: currentBookingData.roomId,
        checkin_date: currentBookingData.checkin,
        checkout_date: currentBookingData.checkout,
        num_guests: currentBookingData.guests,
        total_price: currentBookingData.totalPrice,
        special_requests: document.getElementById("specialNotes")?.value,
      };

      // Create booking
      const response = await api.createBooking(bookingData);

      if (response.success) {
        // Show success modal
        const bookingCode = "BK" + String(response.booking_id).padStart(6, "0");
        document.getElementById("bookingCode").textContent = bookingCode;
        document.getElementById("successModal").style.display = "flex";

        utils.showToast("Đặt phòng thành công!", "success");
      } else {
        utils.showToast(response.message || "Đặt phòng thất bại", "danger");
      }

      utils.hideLoading();
    } catch (error) {
      utils.hideLoading();
      console.error("Booking error:", error);
    }
  });
}

// Export functions
window.selectRoom = selectRoom;
window.updateBookingPrice = updateBookingPrice;
