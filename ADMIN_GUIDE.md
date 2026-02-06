# 🏨 Admin Booking Review & Approval System - Hướng Dẫn

## ✨ Tính Năng

Hệ thống admin cho phép quản lý và duyệt các booking từ khách hàng:

- **📊 Dashboard Quản Lý**: Xem tất cả booking với thống kê theo trạng thái
- **🔍 Bộ Lọc Trạng Thái**: Lọc booking theo PENDING, APPROVED, REJECTED, CONFIRMED, CANCELLED
- **✅ Duyệt Booking**: Chuyển trạng thái từ PENDING → APPROVED
- **❌ Từ Chối Booking**: Chuyển trạng thái từ PENDING → REJECTED với lý do cụ thể
- **📋 Chi Tiết Booking**: Xem toàn bộ thông tin chi tiết của một booking

## 🔐 Đăng Nhập Admin

```
URL: http://localhost:8000/admin/
Username: admin
Password: Admin@123456
```

## 📍 Trình Tự Booking

```
1. Khách đặt phòng (POST /booking/)
   ↓
2. Booking được tạo với status = "PENDING"
   ↓
3. Admin duyệt / từ chối
   ├─→ Duyệt: status = "APPROVED"
   └─→ Từ chối: status = "REJECTED"
   ↓
4. Booking được xác nhận: status = "CONFIRMED"
```

## 🛠️ Trạng Thái Booking

| Trạng Thái | Mô Tả | Hành Động |
|-----------|-------|----------|
| **PENDING** | Chờ duyệt | Duyệt / Từ chối |
| **APPROVED** | Đã duyệt bởi admin | Chuyển sang xác nhận |
| **REJECTED** | Bị từ chối | Không thể thay đổi |
| **CONFIRMED** | Đã xác nhận | Hoàn tất |
| **CANCELLED** | Đã huỷ | Không thể thay đổi |

## 🚀 Sử Dụng

### 1. Xem Danh Sách Booking

**URL**: `/admin/bookings/`

- Xem tất cả booking với thông tin:
  - ID Booking
  - Tên khách sạn
  - Số phòng
  - Tên khách hàng
  - Ngày nhận / trả
  - Giá
  - Trạng thái
  - Ngày tạo booking

### 2. Lọc Booking

Sử dụng nút bộ lọc ở tab **Bộ Lọc**:
- **Tất Cả**: Xem tất cả booking
- **Chờ Duyệt**: Chỉ xem booking chưa duyệt
- **Đã Duyệt**: Xem booking đã duyệt
- **Bị Từ Chối**: Xem booking bị từ chối
- **Xác Nhận**: Xem booking đã xác nhận
- **Huỷ**: Xem booking đã huỷ

Hoặc xem số lượng từ **Thống Kê** tab.

### 3. Duyệt Booking

**Bước 1**: Tìm booking cần duyệt (trạng thái PENDING)

**Bước 2**: Click nút **"Duyệt"** trong cột Thao Tác

**Bước 3**: Xác nhận duyệt khi hỏi confirmdialog

**Bước 4**: Booking sẽ chuyển sang trạng thái "APPROVED"

### 4. Từ Chối Booking

**Bước 1**: Tìm booking cần từ chối (trạng thái PENDING)

**Bước 2**: Click nút **"Từ Chối"** trong cột Thao Tác

**Bước 3**: Popup modal sẽ hiện, nhập **Lý do từ chối**

**Bước 4**: Click nút **"Từ Chối"** để xác nhận

**Bước 5**: Booking sẽ chuyển sang trạng thái "REJECTED"

### 5. Xem Chi Tiết Booking

**URL**: `/admin/bookings/<booking_id>/`

Hoặc click nút **"Chi Tiết"** từ danh sách booking

Trang chi tiết hiển thị:
- **Trạng Thái**: Hiển thị icon và màu trạng thái
- **Thông Tin Khách Sạn**: Tên, địa chỉ, xếp hạng
- **Thông Tin Phòng**: Số phòng, loại, sức chứa, tầng
- **Ngày Booking**: Nhận, trả, số khách
- **Giá**: Giá/đêm, tổng giá
- **Thông Tin Khách**: Tên, email, tên đăng nhập (nếu đăng nhập)
- **Thông Tin Khác**: Ngày tạo, ngày duyệt, người duyệt, ghi chú

## 📄 Cơ Sở Dữ Liệu

### Bảng: bookings

| Cột | Kiểu | Ghi Chú |
|-----|------|--------|
| booking_id | INT PK | ID booking |
| user_id | INT FK | ID khách hàng (NULL = anonymous) |
| hotel_id | INT FK | ID khách sạn |
| room_id | INT FK | ID phòng |
| checkin_date | DATE | Ngày nhận phòng |
| checkout_date | DATE | Ngày trả phòng |
| guests | INT | Số khách |
| total_price | DECIMAL | Tổng giá |
| created_date | DATETIME | Ngày tạo booking |
| status | VARCHAR(20) | PENDING / APPROVED / REJECTED / CONFIRMED / CANCELLED |
| reviewed_by_id | INT FK | ID admin duyệt (NULL nếu chưa duyệt) |
| reviewed_date | DATETIME | Ngày duyệt |
| review_notes | TEXT | Ghi chú duyệt |

## 🔧 API Endpoints

### GET /admin/bookings/

**Mô tả**: Xem danh sách booking của admin

**Parameters**:
- `status` (optional): Lọc theo trạng thái (PENDING, APPROVED, REJECTED, CONFIRMED, CANCELLED)

**Response**: HTML trang admin dashboard

**Yêu Cầu**: Đăng nhập, is_staff=True

### POST /admin/approve-booking/

**Mô Tả**: Duyệt booking

**Headers**:
```javascript
{
  "Content-Type": "application/json",
  "X-CSRFToken": "<csrf-token>"
}
```

**Body**:
```json
{
  "booking_id": 5,
  "notes": "Approved by admin"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Booking được duyệt thành công",
  "booking_id": 5
}
```

**Lỗi**:
- 405: Chỉ POST được chấp nhận
- 403: Không có quyền admin
- 400: Thiếu booking_id hoặc booking không ở trạng thái PENDING
- 404: Booking không tồn tại
- 500: Lỗi server

### POST /admin/reject-booking/

**Mô Tả**: Từ chối booking

**Headers**:
```javascript
{
  "Content-Type": "application/json",
  "X-CSRFToken": "<csrf-token>"
}
```

**Body**:
```json
{
  "booking_id": 5,
  "notes": "Phòng không còn trống"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Booking đã bị từ chối",
  "booking_id": 5
}
```

**Lỗi**:
- 405: Chỉ POST được chấp nhận
- 403: Không có quyền admin
- 400: Thiếu booking_id, notes hoặc booking không ở trạng thái PENDING
- 404: Booking không tồn tại
- 500: Lỗi server

### GET /admin/bookings/<int:booking_id>/

**Mô Tả**: Xem chi tiết booking

**Response**: HTML trang chi tiết booking

**Yêu Cầu**: Đăng nhập, is_staff=True

## 🎨 Giao Diện

### Màu Trạng Thái

- **PENDING** (Chờ Duyệt): 🟡 Vàng (#f39c12)
- **APPROVED** (Đã Duyệt): 🟢 Xanh lá (#27ae60)
- **REJECTED** (Bị Từ Chối): 🔴 Đỏ (#e74c3c)
- **CONFIRMED** (Xác Nhận): 🔵 Xanh dương (#3498db)
- **CANCELLED** (Huỷ): ⚪ Xám (#95a5a6)

## 📊 Thống Kê

Admin dashboard hiển thị số lượng booking theo trạng thái:
- Tất cả trạng thái có thể click để lọc

## 🔒 Bảo Mật

- Chỉ admin (is_staff=True) có thể truy cập `/admin/bookings/`
- CSRF token bắt buộc cho tất cả POST requests
- Logging tất cả hành động admin
  - `[ADMIN] Booking {id} approved by {username}`
  - `[ADMIN] Booking {id} rejected by {username}`

## 📝 Ghi Chú

1. Booking khách hàng đều bắt đầu ở trạng thái **PENDING**
2. Admin phải duyệt booking trước khi nó có thể được xác nhận
3. Sau khi từ chối/duyệt, không thể thay đổi lại trạng thái từ giao diện admin
4. Tất cả hành động admin được lưu lại: người duyệt, ngày duyệt, ghi chú
5. Booking ẩm danh (anonymous) được hỗ trợ - khách không cần đăng nhập để đặt phòng

## 🚨 Troubleshooting

### Lỗi: "Bạn không có quyền truy cập trang này"

- Đảm bảo bạn đã đăng nhập
- Admin user phải có `is_staff=True`
- Xử lý qua Django admin: http://localhost:8000/admin/

### Lỗi: "Booking không tồn tại"

- Kiểm tra booking_id có chính xác
- Booking đó có thể bị xóa

### Lỗi CSRF

- Đảm bảo `{% csrf_token %}` có trong form
- Đảm bảo header `X-CSRFToken` có trong fetch request
- Kiểm tra cookies có csrftoken

## 📞 Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra server logs (terminal Django runserver)
2. Kiểm tra browser console (F12)
3. Đảm bảo database đã khởi tạo đúng (`python manage.py migrate`)
