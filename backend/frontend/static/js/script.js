// Khởi tạo bản đồ
const map = L.map('map').setView([10.8231, 106.6297], 12); // TP.HCM

// Load OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

// Marker test (fake data)
const hotels = [
    { name: "Khách sạn A", lat: 10.823, lng: 106.63 },
    { name: "Nhà nghỉ B", lat: 10.83, lng: 106.62 }
];

// Hiển thị marker
hotels.forEach(hotel => {
    L.marker([hotel.lat, hotel.lng])
        .addTo(map)
        .bindPopup(`<b>${hotel.name}</b>`);
});

// Search location (FAKE – để test UI)
function searchLocation() {
    const query = document.getElementById("locationInput").value;

    fetch(`/search/?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            console.log("Backend trả về:", data);

            alert("Tìm thấy " + data.results.length + " địa điểm");

            data.results.forEach(item => {
                L.marker([item.lat, item.lng])
                    .addTo(map)
                    .bindPopup(item.name);
            });
        })
        .catch(err => {
            console.error("Lỗi backend:", err);
        });
}
