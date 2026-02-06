# Hotel GIS - Admin Booking Review/Approval System

## 🎉 Tính Năng Mới Đã Thêm

### Admin Booking Review Dashboard

Hệ thống quản lý booking hoàn chỉnh cho phép admin duyệt và phê duyệt các booking từ khách hàng.

#### ✨ Chức Năng Chính

1. **Admin Dashboard** (`/admin/bookings/`)
   - Xem danh sách tất cả booking
   - Thống kê booking theo trạng thái (PENDING, APPROVED, REJECTED, CONFIRMED, CANCELLED)
   - Bộ lọc booking theo trạng thái
   - Xem chi tiết từng booking

2. **Duyệt Booking** (`/admin/approve-booking/`)
   - Chuyển trạng thái từ PENDING → APPROVED
   - Ghi lại admin duyệt và thời gian duyệt

3. **Từ Chối Booking** (`/admin/reject-booking/`)
   - Chuyển trạng thái từ PENDING → REJECTED
   - Yêu cầu nhập lý do từ chối
   - Ghi lại ghi chú duyệt

4. **Chi Tiết Booking** (`/admin/bookings/<id>/`)
   - Xem toàn bộ thông tin booking
   - Hiển thị thông tin khách sạn, phòng, khách hàng
   - Hiển thị thông tin duyệt (nếu có)

#### 🔄 Trạng Thái Booking

```
PENDING (Chờ Duyệt)
  ↓ [Admin Duyệt]
APPROVED (Đã Duyệt)
  ↓ [Xác Nhận]
CONFIRMED (Xác Nhận)

PENDING (Chờ Duyệt)
  ↓ [Admin Từ Chối]
REJECTED (Bị Từ Chối)
```

#### 🗄️ Cơ Sở Dữ Liệu

Booking model được mở rộng với các trường mới:
- `status`: PENDING, APPROVED, REJECTED, CONFIRMED, CANCELLED
- `reviewed_by`: Foreign Key đến User (admin duyệt)
- `reviewed_date`: Thời gian duyệt
- `review_notes`: Ghi chú duyệt

#### 🔐 Bảo Mật

- Chỉ admin (is_staff=True) có thể truy cập admin dashboard
- CSRF token bắt buộc cho tất cả POST requests
- Logging tất cả hành động admin
- Manual auth checks thay vì @login_required

#### 📚 Tài Liệu

Xem [ADMIN_GUIDE.md](ADMIN_GUIDE.md) để hướng dẫn chi tiết.

## 🚀 Cách Sử Dụng

### 1. Đăng Nhập Admin

```
URL: http://localhost:8000/admin/
Username: admin
Password: Admin@123456
```

### 2. Truy Cập Admin Dashboard

```
http://localhost:8000/admin/bookings/
```

### 3. Duyệt/Từ Chối Booking

- Xem danh sách PENDING booking
- Click "Duyệt" để duyệt hoặc "Từ Chối" để từ chối
- Nhập lý do nếu từ chối

## 📂 Files Được Sửa/Tạo

### Backend
- `backend/gis_api/models.py` - Thêm fields: reviewed_by, reviewed_date, review_notes
- `backend/gis_api/views.py` - Thêm 3 views mới: admin_bookings, approve_booking, reject_booking
- `backend/gis_api/urls.py` - Thêm 4 routes mới

### Frontend Templates
- `templates/admin_bookings.html` - Admin dashboard
- `templates/booking_detail.html` - Chi tiết booking
- `templates/error.html` - Trang lỗi

### Documentation
- `ADMIN_GUIDE.md` - Hướng dẫn sử dụng admin system

## 🧪 Testing

### Tạo Test Data

```bash
# Tạo admin user (tự động)
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@test.com', 'Admin@123456')"

# Test booking creation
POST /booking/ with PENDING status

# Test admin approval
POST /admin/approve-booking/ with booking_id and notes
```

### Test Scenarios

1. **Booking Creation**
   - Khách tạo booking → status = PENDING ✓
   - Booking lưu vào database ✓

2. **Admin Dashboard**
   - Admin truy cập /admin/bookings/ ✓
   - Thống kê hiển thị đúng ✓
   - Bộ lọc status hoạt động ✓

3. **Approve Booking**
   - Admin click Duyệt ✓
   - Status thay đổi thành APPROVED ✓
   - reviewed_by và reviewed_date được ghi ✓

4. **Reject Booking**
   - Admin click Từ Chối ✓
   - Modal hiện yêu cầu lý do ✓
   - Status thay đổi thành REJECTED ✓
   - review_notes được lưu ✓

## 📊 API Endpoints

```
GET  /admin/bookings/                    - Admin dashboard
POST /admin/approve-booking/             - Duyệt booking
POST /admin/reject-booking/              - Từ chối booking
GET  /admin/bookings/<int:booking_id>/   - Chi tiết booking
```

## 🎯 Next Steps (Tùy Chọn)

Các tính năng có thể thêm tiếp:
- [ ] Email notification khi booking được duyệt/từ chối
- [ ] Admin notification khi có booking mới
- [ ] Bulk approve/reject bookings
- [ ] Admin user management
- [ ] Activity log
- [ ] Export booking data to CSV
- [ ] Payment integration
