document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("confirmBookingBtn").addEventListener("click", () => {

    const payload = {
      hotel_id: document.getElementById("hotelId").value,
      room_id: document.getElementById("roomId").value,
      checkin: document.getElementById("checkin").value,
      checkout: document.getElementById("checkout").value,
      guests: document.getElementById("guests").value,
      payment_method: document.getElementById("paymentMethod").value
    };
    console.log("hotelId:", document.getElementById("hotelId")?.value);
    console.log("roomId:", document.getElementById("roomId")?.value);
    console.log("checkin:", document.getElementById("checkin")?.value);
    console.log("checkout:", document.getElementById("checkout")?.value);
    console.log("guests:", document.getElementById("guests")?.value);
    console.log("payment:", document.getElementById("paymentMethod")?.value);

    // VALIDATE
    for (let key in payload) {
      if (!payload[key]) {
        alert("Thiếu dữ liệu: " + key);
        return;
      }
    }

    console.log("BOOKING PAYLOAD:", payload);

    const csrftoken = getCookie("csrftoken");
    console.log("CSRF Token retrieved:", csrftoken);

    fetch("/booking/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken || ""
      },
      body: JSON.stringify(payload)
    })
    .then(async res => {
      console.log("Response status:", res.status);
      const contentType = res.headers.get("content-type");
      console.log("Content-Type:", contentType);
      
      if (!res.ok) {
        const text = await res.text();
        console.error("Error response:", text.substring(0, 200));
        throw new Error(`HTTP ${res.status}: ${text.substring(0, 100)}`);
      }

      if (contentType && contentType.includes("application/json")) {
        return res.json();
      } else {
        throw new Error("Response không phải JSON");
      }
    })
    .then(data => {
      console.log("Booking response data:", data);
      if (data.success) {
        alert("Đặt phòng thành công! Mã đặt phòng: " + data.booking_id);
        window.location.href = "/my-bookings/";
      } else {
        alert(data.error || "Đặt phòng thất bại");
      }
    })
    .catch(err => {
      console.error("Lỗi khi đặt phòng:", err);
      alert("Lỗi kết nối tới server");
    });
  });
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    document.cookie.split(";").forEach(c => {
      const cookie = c.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
      }
    });
  }
  return cookieValue;
}
