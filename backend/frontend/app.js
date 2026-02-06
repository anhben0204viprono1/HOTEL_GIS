const API_URL = "http://127.0.0.1:8000/api/hotels/search/";

function searchHotels() {
    const keyword = document.getElementById("searchInput").value;
    const resultList = document.getElementById("resultList");

    resultList.innerHTML = "Đang tìm...";

    fetch(`${API_URL}?q=${encodeURIComponent(keyword)}`)
        .then(response => response.json())
        .then(data => {
            resultList.innerHTML = "";

            if (data.length === 0) {
                resultList.innerHTML = "<li>Không tìm thấy kết quả</li>";
                return;
            }

            data.forEach(hotel => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <b>${hotel.name}</b><br>
                    ⭐ ${hotel.star} | ${hotel.address}
                `;
                resultList.appendChild(li);
            });
        })
        .catch(error => {
            console.error(error);
            resultList.innerHTML = "<li>Lỗi kết nối backend</li>";
        });
}
