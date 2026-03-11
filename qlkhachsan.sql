-- ============================================================
--   HỆ THỐNG QUẢN LÝ KHÁCH SẠN - PostgreSQL Schema
--   Bao gồm: Hotel, Customer, RoomType, Room, Amenity,
--            Booking, Payment, Review
-- ============================================================

-- Xóa nếu đã tồn tại (đúng thứ tự phụ thuộc)
DROP TABLE IF EXISTS Review        CASCADE;
DROP TABLE IF EXISTS Payment       CASCADE;
DROP TABLE IF EXISTS Booking       CASCADE;
DROP TABLE IF EXISTS Room          CASCADE;
DROP TABLE IF EXISTS RoomAmenity   CASCADE;
DROP TABLE IF EXISTS Amenity       CASCADE;
DROP TABLE IF EXISTS RoomType      CASCADE;
DROP TABLE IF EXISTS Hotel         CASCADE;
DROP TABLE IF EXISTS Customer      CASCADE;

-- Tạo ENUM types
DO $$ BEGIN
    CREATE TYPE gender_type      AS ENUM ('male', 'female', 'other');
    CREATE TYPE room_status      AS ENUM ('available', 'occupied', 'maintenance');
    CREATE TYPE booking_status   AS ENUM ('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled');
    CREATE TYPE payment_method   AS ENUM ('cash', 'credit_card', 'debit_card', 'bank_transfer', 'e_wallet', 'momo', 'vnpay', 'zalopay');
    CREATE TYPE payment_status   AS ENUM ('pending', 'paid', 'failed', 'refunded');
    CREATE TYPE amenity_category AS ENUM ('bedroom', 'bathroom', 'entertainment', 'kitchen', 'climate', 'accessibility', 'other');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


-- ============================================================
-- 1. BẢNG Customer (Khách hàng)
-- ============================================================
CREATE TABLE Customer (
    id            SERIAL          PRIMARY KEY,
    full_name     VARCHAR(255)    NOT NULL,
    email         VARCHAR(255)    UNIQUE NOT NULL,
    phone         VARCHAR(20),
    password_hash VARCHAR(255)    NOT NULL,
    avatar_url    VARCHAR(500),
    date_of_birth DATE,
    gender        gender_type,
    id_card       VARCHAR(20),                    -- CCCD / Passport
    current_lat   DECIMAL(10, 8),                 -- Vĩ độ hiện tại của khách
    current_lng   DECIMAL(11, 8),                 -- Kinh độ hiện tại của khách
    is_active     BOOLEAN         DEFAULT TRUE,
    created_at    TIMESTAMPTZ     DEFAULT NOW(),
    updated_at    TIMESTAMPTZ     DEFAULT NOW()
);

COMMENT ON TABLE  Customer             IS 'Thông tin khách hàng';
COMMENT ON COLUMN Customer.current_lat IS 'Vĩ độ GPS hiện tại - dùng để tìm khách sạn gần nhất';
COMMENT ON COLUMN Customer.current_lng IS 'Kinh độ GPS hiện tại - dùng để tìm khách sạn gần nhất';
COMMENT ON COLUMN Customer.id_card     IS 'Số CCCD hoặc Passport';


-- ============================================================
-- 2. BẢNG Hotel (Khách sạn)
-- ============================================================
CREATE TABLE Hotel (
    id            SERIAL          PRIMARY KEY,
    name          VARCHAR(255)    NOT NULL,
    address       VARCHAR(500),
    latitude      DECIMAL(10, 8)  NOT NULL,        -- Vĩ độ khách sạn
    longitude     DECIMAL(11, 8)  NOT NULL,        -- Kinh độ khách sạn
    phone         VARCHAR(20),
    email         VARCHAR(255),
    star_rating   SMALLINT        CHECK (star_rating BETWEEN 1 AND 5),
    description   TEXT,
    thumbnail_url VARCHAR(500),
    website       VARCHAR(255),
    check_in_time TIME            DEFAULT '14:00', -- Giờ nhận phòng
    check_out_time TIME           DEFAULT '12:00', -- Giờ trả phòng
    is_active     BOOLEAN         DEFAULT TRUE,
    created_at    TIMESTAMPTZ     DEFAULT NOW(),
    updated_at    TIMESTAMPTZ     DEFAULT NOW()
);

COMMENT ON TABLE  Hotel           IS 'Thông tin khách sạn';
COMMENT ON COLUMN Hotel.latitude  IS 'Vĩ độ GPS - dùng Haversine để tính khoảng cách';
COMMENT ON COLUMN Hotel.longitude IS 'Kinh độ GPS - dùng Haversine để tính khoảng cách';

-- Index tăng tốc tìm kiếm theo tọa độ
CREATE INDEX idx_hotel_location ON Hotel (latitude, longitude);
CREATE INDEX idx_hotel_active   ON Hotel (is_active);


-- ============================================================
-- 3. BẢNG Amenity (Danh mục tiện ích)
-- ============================================================
CREATE TABLE Amenity (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,           -- VD: WiFi, TV, Bồn tắm, Điều hòa
    category    amenity_category DEFAULT 'other',   -- Nhóm tiện ích
    icon_url    VARCHAR(500),                        -- Icon hiển thị UI
    description TEXT
);

COMMENT ON TABLE Amenity IS 'Danh mục tiện ích (dùng chung cho mọi loại phòng)';

-- Dữ liệu mẫu tiện ích
INSERT INTO Amenity (name, category, description) VALUES
    ('WiFi miễn phí',       'other',         'Kết nối WiFi tốc độ cao'),
    ('TV màn hình phẳng',   'entertainment', 'TV LED 40 inch trở lên'),
    ('Điều hòa',            'climate',       'Điều hòa 2 chiều'),
    ('Máy sưởi',            'climate',       'Máy sưởi điện'),
    ('Minibar',             'kitchen',       'Tủ lạnh minibar có đồ uống'),
    ('Máy pha cà phê',      'kitchen',       'Máy pha cà phê Nespresso'),
    ('Bồn tắm',             'bathroom',      'Bồn tắm nằm'),
    ('Vòi hoa sen',         'bathroom',      'Vòi sen tăng áp'),
    ('Két sắt',             'bedroom',       'Két sắt điện tử trong phòng'),
    ('Ban công',            'other',         'Ban công riêng với view đẹp'),
    ('Lối đi xe lăn',       'accessibility', 'Hỗ trợ người khuyết tật'),
    ('Netflix',             'entertainment', 'Tài khoản Netflix sẵn có');


-- ============================================================
-- 4. BẢNG RoomType (Loại phòng)
-- ============================================================
CREATE TABLE RoomType (
    id              SERIAL          PRIMARY KEY,
    hotel_id        INT             NOT NULL REFERENCES Hotel(id) ON DELETE CASCADE,
    name            VARCHAR(100)    NOT NULL,   -- VD: Standard, Deluxe, Suite, Family
    description     TEXT,
    max_occupancy   SMALLINT        DEFAULT 2,
    bed_type        VARCHAR(50),               -- VD: Single, Double, Twin, King
    area_sqm        DECIMAL(6, 2),             -- Diện tích phòng (m²)
    price_per_night DECIMAL(12, 2)  NOT NULL,  -- Giá mỗi đêm
    thumbnail_url   VARCHAR(500),
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

COMMENT ON TABLE RoomType IS 'Loại phòng (Standard / Deluxe / Suite ...) theo từng khách sạn';


-- ============================================================
-- 5. BẢNG RoomAmenity (Tiện ích của loại phòng - N:N)
-- ============================================================
CREATE TABLE RoomAmenity (
    room_type_id INT NOT NULL REFERENCES RoomType(id) ON DELETE CASCADE,
    amenity_id   INT NOT NULL REFERENCES Amenity(id)  ON DELETE CASCADE,
    PRIMARY KEY (room_type_id, amenity_id)
);

COMMENT ON TABLE RoomAmenity IS 'Bảng trung gian: loại phòng ↔ tiện ích (many-to-many)';


-- ============================================================
-- 6. BẢNG Room (Phòng thực tế)
-- ============================================================
CREATE TABLE Room (
    id           SERIAL       PRIMARY KEY,
    hotel_id     INT          NOT NULL REFERENCES Hotel(id)    ON DELETE CASCADE,
    room_type_id INT          NOT NULL REFERENCES RoomType(id) ON DELETE RESTRICT,
    room_number  VARCHAR(10)  NOT NULL,      -- VD: 101, 202A
    floor        SMALLINT,
    status       room_status  DEFAULT 'available',
    note         TEXT,                       -- Ghi chú nội bộ (sửa chữa, ...)
    created_at   TIMESTAMPTZ  DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (hotel_id, room_number)           -- Số phòng không trùng trong cùng hotel
);

COMMENT ON TABLE Room IS 'Phòng thực tế, mỗi phòng thuộc 1 loại phòng cụ thể';

CREATE INDEX idx_room_status   ON Room (status);
CREATE INDEX idx_room_hotel    ON Room (hotel_id);


-- ============================================================
-- 7. BẢNG Booking (Đặt phòng)
-- ============================================================
CREATE TABLE Booking (
    id            SERIAL          PRIMARY KEY,
    customer_id   INT             NOT NULL REFERENCES Customer(id) ON DELETE RESTRICT,
    room_id       INT             NOT NULL REFERENCES Room(id)     ON DELETE RESTRICT,
    check_in      DATE            NOT NULL,
    check_out     DATE            NOT NULL,
    num_guests    SMALLINT        DEFAULT 1,
    total_price   DECIMAL(12, 2)  NOT NULL,    -- Tổng tiền = số đêm × giá phòng
    status        booking_status  DEFAULT 'pending',
    note          TEXT,                         -- Yêu cầu đặc biệt của khách
    cancelled_at  TIMESTAMPTZ,                  -- Thời điểm huỷ (nếu có)
    cancel_reason TEXT,                         -- Lý do huỷ
    created_at    TIMESTAMPTZ     DEFAULT NOW(),
    updated_at    TIMESTAMPTZ     DEFAULT NOW(),
    CONSTRAINT chk_dates CHECK (check_out > check_in)
);

COMMENT ON TABLE Booking IS 'Lịch sử đặt phòng của khách hàng';

CREATE INDEX idx_booking_customer ON Booking (customer_id);
CREATE INDEX idx_booking_room     ON Booking (room_id);
CREATE INDEX idx_booking_dates    ON Booking (check_in, check_out);
CREATE INDEX idx_booking_status   ON Booking (status);


-- ============================================================
-- 8. BẢNG Payment (Thanh toán)
-- ============================================================
CREATE TABLE Payment (
    id                SERIAL          PRIMARY KEY,
    booking_id        INT             NOT NULL REFERENCES Booking(id) ON DELETE RESTRICT,
    amount            DECIMAL(12, 2)  NOT NULL,          -- Số tiền thanh toán
    method            payment_method  NOT NULL,           -- Hình thức thanh toán
    status            payment_status  DEFAULT 'pending',
    transaction_code  VARCHAR(100),                       -- Mã giao dịch từ cổng thanh toán
    gateway_response  TEXT,                               -- JSON phản hồi từ cổng (VNPay, MoMo...)
    paid_at           TIMESTAMPTZ,                        -- Thời điểm thanh toán thành công
    refunded_at       TIMESTAMPTZ,                        -- Thời điểm hoàn tiền (nếu có)
    refund_amount     DECIMAL(12, 2),                     -- Số tiền hoàn (nếu hoàn 1 phần)
    note              TEXT,                               -- Ghi chú kế toán
    created_at        TIMESTAMPTZ     DEFAULT NOW(),
    updated_at        TIMESTAMPTZ     DEFAULT NOW()
);

COMMENT ON TABLE  Payment                  IS 'Thông tin thanh toán cho từng booking';
COMMENT ON COLUMN Payment.transaction_code IS 'Mã giao dịch từ VNPay / MoMo / ZaloPay';
COMMENT ON COLUMN Payment.gateway_response IS 'Lưu toàn bộ JSON response từ cổng thanh toán để debug';

CREATE INDEX idx_payment_booking     ON Payment (booking_id);
CREATE INDEX idx_payment_status      ON Payment (status);
CREATE INDEX idx_payment_transaction ON Payment (transaction_code);


-- ============================================================
-- 9. BẢNG Review (Đánh giá)
-- ============================================================
CREATE TABLE Review (
    id          SERIAL       PRIMARY KEY,
    booking_id  INT          NOT NULL UNIQUE REFERENCES Booking(id) ON DELETE CASCADE, -- 1 booking = 1 review
    customer_id INT          NOT NULL REFERENCES Customer(id) ON DELETE CASCADE,
    hotel_id    INT          NOT NULL REFERENCES Hotel(id)    ON DELETE CASCADE,
    rating      SMALLINT     NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    is_visible  BOOLEAN      DEFAULT TRUE,   -- Ẩn review vi phạm
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

COMMENT ON TABLE Review IS 'Đánh giá của khách sau khi trả phòng (1 booking chỉ được review 1 lần)';

CREATE INDEX idx_review_hotel  ON Review (hotel_id);
CREATE INDEX idx_review_rating ON Review (rating);


-- ============================================================
-- TRIGGER: Tự động cập nhật updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customer_updated BEFORE UPDATE ON Customer FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_hotel_updated    BEFORE UPDATE ON Hotel    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_room_updated     BEFORE UPDATE ON Room     FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_booking_updated  BEFORE UPDATE ON Booking  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_payment_updated  BEFORE UPDATE ON Payment  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

INSERT INTO Hotel (name, address, latitude, longitude, phone, email, star_rating, description, website, check_in_time, check_out_time) VALUES
('The Reverie Saigon', '22-36 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM', 10.773786006404364, 106.70454925698805, '02838236688', 'info@thereveriesaigon.com', 5, 'Khách sạn sang trọng tại trung tâm TP.HCM', 'https://www.thereveriesaigon.com', '14:00', '12:00'),
('Rex Hotel','141 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM', 10.775869343535927, 106.701264286985 , '02838222222', 'info@rexhotel.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.rexhotel.com', '14:00', '12:00'),
('Park Hyatt Saigon','2 Công Trường Lam Sơn, Phường Bến Nghé, Quận 1, TP.HCM',10.777761696610716, 106.70338422880332 , '02838233333', 'info@parkhyattsaigon.com', 5, 'Khách sạn cao cấp tại trung tâm TP.HCM', 'https://www.parkhyattsaigon.com', '14:00', '12:00'),
('Caravelle Saigon','123 Nguyễn Văn Cừ, Phường 1, Quận 5, TP.HCM', 10.776268960087013, 106.70360481958376, '02838244444', 'info@caravellesaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.caravellesaigon.com', '14:00', '12:00'),
('Hotel Majestic Saigon','1 Đồng Khởi, Phường Bến Nghé, Quận 1, TP.HCM', 10.772776438821918, 106.7061873501408, '02838255555', 'info@hotelmajesticsaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.majesticsaigon.com/vi/', '14:00', '12:00'),
('Liberty Central Saigon Citypoint','59 Pasteur, Phường Bến Nghé, Quận 1, TP.HCM',10.774693732575594, 106.70063289155311 , '02838266666', 'info@libertycentralsaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.libertycentralsaigon.com', '14:00', '12:00'),
('Hotel Nikko Saigon','235 Nguyễn Văn Cừ, Phường 1, Quận 5, TP.HCM', 10.776268960087013, 106.70360481958376, '02838277777', 'info@hotelnikkosaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.hotelnikkosaigon.com', '14:00', '12:00'),
('Saigon Prince Hotel','63 Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM', 10.772820429082751, 106.70404733750729, '02838288888', 'info@saigonprincehotel.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.saigonprincehotel.com', '14:00', '12:00'),
('PullMan Saigon Centre','148 Trần Hưng Đạo, Phường Nguyễn Cư Trinh, Quận 1, TP.HCM', 10.774693732575594, 106.70063289155311, '02838299999', 'info@pullmansaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.pullmansaigon.com', '14:00', '12:00'),
('Hotel des Arts Saigon MGallery','76-78 Nguyễn Thị Minh Khai, Phường 6, Quận 3, TP.HCM', 10.776268960087013, 106.70360481958376, '02838300000', 'info@hoteldesartssaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.hoteldesartssaigon.com', '14:00', '12:00'),
('The Myst Dong Khoi','2-4-6 Đồng Khởi, Phường Bến Nghé, Quận 1, TP.HCM', 10.772776438821918, 106.7061873501408, '02838311111', 'info@themystdongkhoi.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.themystdongkhoi.com', '14:00', '12:00'),
('Hotel Continental Saigon','132-134 Đồng Khởi, Phường Bến Nghé, Quận 1, TP.HCM', 10.772776438821918, 106.7061873501408, '02838322222', 'info@hotelcontinentialsaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.hotelcontinentialsaigon.com', '14:00', '12:00'),
('Fusion Original Saigon','65 Lê Lợi, Bến Nghé, Quận 1, Thành phố Hồ Chí Minh ',10.773633067398759, 106.70125249517822, '02838333333', 'info@fusionoriginalsaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.fusionoriginalsaigon.com', '14:00', '12:00'),
('La Vela Saigon','280 Nam Kỳ Khởi Nghĩa, Phường Xuân Hòa, Quận 3, Thành phố Hồ Chí Minh ', 10.788670423084099, 106.68547900298559, '02838344444', 'info@lavelsaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://lavelasaigon.com/vi/trang-chu/', '14:00', '12:00'),
('Mai House Saigon','1-3-5, Ngô Thời Nhiệm, Phường 6, Quận 3, Thành phố Hồ Chí Minh ',10.782099580585877, 106.69159148479056, '02838355555', 'info@maihousesaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.maihousesaigon.com', '14:00', '12:00'),
('Orchids Saigon Hotel','192 Pasteur, phường, Xuân Hòa, Thành phố Hồ Chí Minh ',10.781038080127509, 106.69557191972062, '02838366666', 'info@orchidssaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.orchidssaigon.com', '14:00', '12:00'),
('Aristo Saigon Hotel','3A Võ Văn Tần, Phường 6, Quận 3, Thành phố Hồ Chí Minh',10.781110838198982, 106.69459260094462, '02838377777', 'info@aristosaigon.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.aristosaigon.com', '14:00', '12:00'),
('Garden View Court','101 Nguyễn Du, Phường Bến Thành, Ward, Thành phố Hồ Chí Minh ',)10.775080651543322, 106.69667407791049, '02838388888', 'info@gardenviewcourt.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.gardenviewcourt.com', '14:00', '12:00'),
('Windsor Plaza Hotel','1 Sư Vạn Hạnh, Phường 9, Quận 5, Thành phố Hồ Chí Minh',10.757890288963845, 106.67338508606713,' 02838399999', 'info@windsorplazahotel.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.windsorplazahotel.com', '14:00', '12:00'),
('Chloe Gallery','02 - 06 Phan Văn Chương Hồ Bán Nguyệt - Phú Mỹ Hưng, Thành phố Hồ Chí Minh ',10.723963440639952, 106.72006483750658, '02838400000', 'info@chloegallery.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.chloegallery.com', '14:00', '12:00'),
('Ibis Saigon South','Hoàng Văn Thái/73 Street, Khu đô thị Phú Mỹ Hưng, Thành phố Hồ Chí Minh ',10.730701461053238, 106.72321754279996, '02838411111', 'info@ibissaigonsouth.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.ibissaigonsouth.com', '14:00', '12:00'),
('Hotel Equatorial Ho Chi Minh City','242 Trần Bình Trọng, Phường 4, Quận 5, Thành phố Hồ Chí Minh ',10.771038080127509, 106.69557191972062, '02838422222', 'info@hotelequatorialhochiminhcity.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.hotelequatorialhochiminhcity.com', '14:00', '12:00'),
('Vinpearl Landmark 81','720A Điện Biên Phủ, Phường 22, Bình Thạnh, Thành phố Hồ Chí Minh',10.795236028320632, 106.72188839530826, '02838433333', 'info@vinpearllandmark81.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.vinpearllandmark81.com', '14:00', '12:00'),
('Cozrum Homes','182 Diên Hồng, Phường 1, Bình Thạnh, Thành phố Hồ Chí Minh',10.798564043655695, 106.69830076395488, '02838444444', 'info@cozrumhomes.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.cozrumhomes.com', '14:00', '12:00'),
('Mường Thanh Luxury', '261C Đ. Nguyễn Văn Trỗi, Phường 10, Phú Nhuận, Thành phố Hồ Chí Minh 700000',10.797412342824353, 106.67211331953814, '02838455555', 'info@muongthanh luxury.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.muongthanh luxury.com', '14:00', '12:00'),
('Holiday Inn & Suites','18E Cộng Hòa, Street, Ward, Thành phố Hồ Chí Minh',10.801652366786383, 106.6550617529333, '02838466666', 'info@holidayinnandsuites.com', 4, 'Khách sạn hiện đại tại trung tâm TP.HCM', 'https://www.holidayinnandsuites.com', '14:00', '12:00');