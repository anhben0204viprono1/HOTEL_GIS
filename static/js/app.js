// static/js/app.js
// Main application JavaScript

// API Configuration
const API_BASE_URL = "http://localhost:5000/api";

// Utility Functions
const utils = {
  // Format currency
  formatCurrency: (amount) => {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(amount);
  },

  // Format date
  formatDate: (dateString) => {
    const date = new Date(dateString);
    const days = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
    return `${days[date.getDay()]}, ${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`;
  },

  // Calculate nights between dates
  calculateNights: (checkin, checkout) => {
    const date1 = new Date(checkin);
    const date2 = new Date(checkout);
    const diffTime = Math.abs(date2 - date1);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  },

  // Debounce function
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Show toast notification
  showToast: (message, type = "info") => {
    const toastContainer =
      document.querySelector(".toast-container") || createToastContainer();
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    const icons = {
      success: "fa-check-circle",
      warning: "fa-exclamation-triangle",
      danger: "fa-times-circle",
      info: "fa-info-circle",
    };

    toast.innerHTML = `
            <i class="fas ${icons[type]} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;

    toastContainer.appendChild(toast);

    // Close button
    toast.querySelector(".toast-close").addEventListener("click", () => {
      toast.remove();
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.remove();
    }, 5000);
  },

  // Show loading overlay
  showLoading: () => {
    const overlay = document.createElement("div");
    overlay.className = "loading-overlay";
    overlay.innerHTML = `
            <div class="spinner"></div>
            <div class="loading-text">Đang xử lý...</div>
        `;
    document.body.appendChild(overlay);
  },

  // Hide loading overlay
  hideLoading: () => {
    const overlay = document.querySelector(".loading-overlay");
    if (overlay) overlay.remove();
  },

  // Get query parameters
  getQueryParam: (param) => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
  },

  // Set query parameter
  setQueryParam: (param, value) => {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.pushState({}, "", url);
  },
};

// Create toast container if it doesn't exist
function createToastContainer() {
  const container = document.createElement("div");
  container.className = "toast-container";
  document.body.appendChild(container);
  return container;
}

// API Service
const api = {
  // Search hotels
  searchHotels: async (params) => {
    try {
      const queryString = new URLSearchParams(params).toString();
      const response = await fetch(
        `${API_BASE_URL}/hotels/search?${queryString}`,
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error searching hotels:", error);
      utils.showToast("Có lỗi xảy ra khi tìm kiếm khách sạn", "danger");
      throw error;
    }
  },

  // Get hotel details
  // getHotelDetails: async (hotelId) => {
   // try {
   //   const response = await fetch(`${API_BASE_URL}/hotels/${hotelId}`);
  //    const data = await response.json();
  //    return data;
  //  } catch (error) {
//console.error("Error getting hotel details:", error);
  //    utils.showToast("Có lỗi xảy ra khi tải thông tin khách sạn", "danger");
  //    throw error;
 //  }
  // },

  // Create booking
  createBooking: async (bookingData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/bookings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(bookingData),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error creating booking:", error);
      utils.showToast("Có lỗi xảy ra khi đặt phòng", "danger");
      throw error;
    }
  },

  // Get booking details
  getBookingDetails: async (bookingId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/bookings/${bookingId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error getting booking details:", error);
      utils.showToast("Có lỗi xảy ra khi tải thông tin đặt phòng", "danger");
      throw error;
    }
  },

  // Get customer bookings
  getCustomerBookings: async (customerId) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/customers/${customerId}/bookings`,
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error getting customer bookings:", error);
      utils.showToast("Có lỗi xảy ra khi tải danh sách đặt phòng", "danger");
      throw error;
    }
  },

  // Cancel booking
  cancelBooking: async (bookingId) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/bookings/${bookingId}/cancel`,
        {
          method: "POST",
        },
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error canceling booking:", error);
      utils.showToast("Có lỗi xảy ra khi hủy đặt phòng", "danger");
      throw error;
    }
  },

  // Create payment
  createPayment: async (paymentData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/payments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(paymentData),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error creating payment:", error);
      utils.showToast("Có lỗi xảy ra khi thanh toán", "danger");
      throw error;
    }
  },
};

// Mobile Navigation Toggle
document.addEventListener("DOMContentLoaded", () => {
  const hamburger = document.querySelector(".hamburger");
  const navMenu = document.querySelector(".nav-menu");

  if (hamburger) {
    hamburger.addEventListener("click", () => {
      navMenu.classList.toggle("active");
    });
  }

  // Close menu when clicking outside
  document.addEventListener("click", (e) => {
    if (navMenu && navMenu.classList.contains("active")) {
      if (!e.target.closest(".navbar")) {
        navMenu.classList.remove("active");
      }
    }
  });

  // Set minimum dates for date inputs
  const today = new Date().toISOString().split("T")[0];
  const checkinInputs = document.querySelectorAll(
    "#checkin, #searchCheckin, #bookingCheckin",
  );
  const checkoutInputs = document.querySelectorAll(
    "#checkout, #searchCheckout, #bookingCheckout",
  );

  checkinInputs.forEach((input) => {
    if (input) input.min = today;
  });

  checkoutInputs.forEach((input) => {
    if (input) input.min = today;
  });

  // Update checkout min date when checkin changes
  checkinInputs.forEach((checkin) => {
    if (checkin) {
      checkin.addEventListener("change", () => {
        const checkinDate = new Date(checkin.value);
        checkinDate.setDate(checkinDate.getDate() + 1);
        const minCheckout = checkinDate.toISOString().split("T")[0];

        checkoutInputs.forEach((checkout) => {
          if (checkout) {
            checkout.min = minCheckout;
            if (
              checkout.value &&
              new Date(checkout.value) <= new Date(checkin.value)
            ) {
              checkout.value = minCheckout;
            }
          }
        });
      });
    }
  });
});

// Popular destinations click handler
document.addEventListener("DOMContentLoaded", () => {
  const destinationCards = document.querySelectorAll(".destination-card");
  destinationCards.forEach((card) => {
    card.addEventListener("click", () => {
      const city = card.dataset.city;
      window.location.href = `/search?city=${encodeURIComponent(city)}`;
    });
  });
});

// Quick filters
document.addEventListener("DOMContentLoaded", () => {
  const quickFilters = document.querySelectorAll(".quick-filters .filter-btn");
  quickFilters.forEach((btn) => {
    btn.addEventListener("click", () => {
      const filter = btn.dataset.filter;
      let url = "/search?";

      switch (filter) {
        case "price":
          url += "max_price=1000000";
          break;
        case "rating":
          url += "min_rating=4";
          break;
        case "nearby":
          // Get user location and search
          getUserLocationAndSearch();
          return;
      }

      window.location.href = url;
    });
  });
});

// Get user location
function getUserLocationAndSearch() {
  if (navigator.geolocation) {
    utils.showLoading();
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        window.location.href = `/search?lat=${lat}&lng=${lng}&distance=5`;
        utils.hideLoading();
      },
      (error) => {
        utils.hideLoading();
        utils.showToast("Không thể lấy vị trí của bạn", "warning");
        console.error("Error getting location:", error);
      },
    );
  } else {
    utils.showToast("Trình duyệt không hỗ trợ định vị", "warning");
  }
}

// Form validation
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return false;

  const inputs = form.querySelectorAll(
    "input[required], select[required], textarea[required]",
  );
  let isValid = true;

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      isValid = false;
      input.classList.add("is-invalid");
    } else {
      input.classList.remove("is-invalid");
    }
  });

  // Email validation
  const emailInputs = form.querySelectorAll('input[type="email"]');
  emailInputs.forEach((input) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (input.value && !emailRegex.test(input.value)) {
      isValid = false;
      input.classList.add("is-invalid");
      utils.showToast("Email không hợp lệ", "warning");
    }
  });

  // Phone validation
  const phoneInputs = form.querySelectorAll('input[type="tel"]');
  phoneInputs.forEach((input) => {
    const phoneRegex = /^[0-9]{10}$/;
    if (input.value && !phoneRegex.test(input.value.replace(/\s/g, ""))) {
      isValid = false;
      input.classList.add("is-invalid");
      utils.showToast("Số điện thoại không hợp lệ", "warning");
    }
  });

  return isValid;
}

// Export utilities and API
window.utils = utils;
window.api = api;
window.validateForm = validateForm;
