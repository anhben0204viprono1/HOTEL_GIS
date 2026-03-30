"""
hotels/widgets.py — Map picker widget cho Django Admin
Dùng 2 field riêng biệt: latitude + longitude, kèm bản đồ Leaflet
"""
from django import forms


class LeafletMapWidget(forms.TextInput):
    """
    Widget hiển thị bản đồ Leaflet bên dưới field latitude.
    Gắn vào field latitude, tự động đồng bộ với field longitude.
    """

    def render(self, name, value, attrs=None, renderer=None):
        # Render input gốc (ẩn đi, dùng JS cập nhật)
        attrs = attrs or {}
        attrs['style'] = 'width:120px;font-family:monospace;font-size:13px;'
        base_input = super().render(name, value, attrs, renderer)

        lat_val = value or ''
        # ID của field longitude dựa theo convention Django admin
        lng_field_id = 'id_longitude'
        lat_field_id = attrs.get('id', f'id_{name}')

        html = f"""
{base_input}
<div id="hotel-map-container" style="margin-top:12px;">

  <!-- Thanh tọa độ + nút -->
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
    <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:8px;">
      <span style="font-size:11px;font-weight:700;color:#166534;letter-spacing:1px;">VĨ ĐỘ</span>
      <span id="disp_lat" style="font-family:monospace;font-weight:700;color:#15803d;font-size:14px;min-width:70px;">{lat_val or '—'}</span>
    </div>
    <div style="background:#eff6ff;border:1px solid #93c5fd;border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:8px;">
      <span style="font-size:11px;font-weight:700;color:#1e40af;letter-spacing:1px;">KINH ĐỘ</span>
      <span id="disp_lng" style="font-family:monospace;font-weight:700;color:#1d4ed8;font-size:14px;min-width:70px;">—</span>
    </div>
    <button type="button" onclick="hotelMapLocateMe()"
      style="background:#2563eb;color:#fff;border:none;border-radius:6px;padding:9px 16px;font-size:12px;font-weight:600;cursor:pointer;">
      📍 Vị trí của tôi
    </button>
    <button type="button" onclick="hotelMapReset()"
      style="background:#ef4444;color:#fff;border:none;border-radius:6px;padding:9px 14px;font-size:12px;font-weight:600;cursor:pointer;">
      ✕ Xóa
    </button>
  </div>

  <!-- Map -->
  <div id="hotel-leaflet-map" style="
    height:450px;
    border:2px solid #d1d5db;
    border-radius:12px;
    overflow:hidden;
    box-shadow:0 4px 16px rgba(0,0,0,.1);
  "></div>

  <!-- Gợi ý -->
  <p style="font-size:11px;color:#6b7280;margin-top:8px;margin-bottom:0;">
    🖱️ <strong>Click lên bản đồ</strong> để đặt vị trí · Marker có thể <strong>kéo thả</strong> · Chỉ nhận tọa độ trong <strong>Việt Nam</strong>
  </p>

  <!-- Error -->
  <div id="hotel-map-error" style="
    display:none;
    color:#dc2626;font-size:12px;
    background:#fef2f2;border:1px solid #fca5a5;
    border-radius:6px;padding:8px 12px;margin-top:8px;
  "></div>

</div>

<script>
(function() {{

  const LAT_MIN=8.18, LAT_MAX=23.39, LNG_MIN=102.14, LNG_MAX=109.46;
  let hotelMap = null;
  let hotelMarker = null;

  function getLatInput()  {{ return document.getElementById('{lat_field_id}'); }}
  function getLngInput()  {{ return document.getElementById('{lng_field_id}'); }}
  function getDispLat()   {{ return document.getElementById('disp_lat'); }}
  function getDispLng()   {{ return document.getElementById('disp_lng'); }}
  function getErrDiv()    {{ return document.getElementById('hotel-map-error'); }}

  function showError(msg) {{
    const d = getErrDiv();
    d.textContent = msg; d.style.display = 'block';
    setTimeout(() => d.style.display='none', 5000);
  }}

  function isInVN(lat, lng) {{
    return lat >= LAT_MIN && lat <= LAT_MAX && lng >= LNG_MIN && lng <= LNG_MAX;
  }}

  function setCoord(lat, lng) {{
    if (!isInVN(lat, lng)) {{
      showError(`❌ Tọa độ (${{lat.toFixed(4)}}, ${{lng.toFixed(4)}}) nằm ngoài Việt Nam! Vui lòng chọn điểm trong lãnh thổ VN.`);
      return false;
    }}
    const la = Math.round(lat*10000)/10000;
    const lo = Math.round(lng*10000)/10000;

    getLatInput().value = la;
    getLngInput().value = lo;
    getDispLat().textContent = la;
    getDispLng().textContent = lo;
    getErrDiv().style.display = 'none';

    const hotelIcon = L.divIcon({{
      html: `<div style="background:#C9A84C;color:#0D0D0D;width:38px;height:38px;
        border-radius:50% 50% 50% 0;display:flex;align-items:center;
        justify-content:center;font-size:20px;transform:rotate(-45deg);
        box-shadow:0 4px 14px rgba(0,0,0,.35);border:2px solid #333;">
        <span style="transform:rotate(45deg)">🏨</span></div>`,
      className:'', iconSize:[38,38], iconAnchor:[19,38], popupAnchor:[0,-38]
    }});

    if (hotelMarker) {{
      hotelMarker.setLatLng([la, lo]);
    }} else {{
      hotelMarker = L.marker([la, lo], {{icon: hotelIcon, draggable: true}}).addTo(hotelMap);
      hotelMarker.on('dragend', function(e) {{
        const p = e.target.getLatLng();
        setCoord(p.lat, p.lng);
      }});
    }}
    return true;
  }}

  function initHotelMap() {{
    if (typeof L === 'undefined') {{ setTimeout(initHotelMap, 300); return; }}
    const mapEl = document.getElementById('hotel-leaflet-map');
    if (!mapEl || mapEl._leaflet_id) return;

    // Xác định center: nếu đã có tọa độ thì zoom vào đó
    const existLat = parseFloat(getLatInput().value);
    const existLng = parseFloat(getLngInput().value);
    const hasExist = !isNaN(existLat) && !isNaN(existLng);

    hotelMap = L.map('hotel-leaflet-map', {{
      center: hasExist ? [existLat, existLng] : [16.0, 106.0],
      zoom:   hasExist ? 14 : 6,
      minZoom: 5,
      maxZoom: 18,
    }});

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }}).addTo(map);widgets.py — Map picker widget cho Django Admin
Dùng 2 field riêng biệt: latitude + longitude, kèm bản đồ Leaflet
"""
from django import forms


class LeafletMapWidget(forms.TextInput):
    """
    Widget hiển thị bản đồ Leaflet bên dưới field latitude.
    Gắn vào field latitude, tự động đồng bộ với field longitude.
    """

    def render(self, name, value, attrs=None, renderer=None):
        # Render input gốc (ẩn đi, dùng JS cập nhật)
        attrs = attrs or {}
        attrs['style'] = 'width:120px;font-family:monospace;font-size:13px;'
        base_input = super().render(name, value, attrs, renderer)

        lat_val = value or ''
        # ID của field longitude dựa theo convention Django admin
        lng_field_id = 'id_longitude'
        lat_field_id = attrs.get('id', f'id_{name}')

        html = f"""
{base_input}
<div id="hotel-map-container" style="margin-top:12px;">

  <!-- Thanh tọa độ + nút -->
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
    <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:8px;">
      <span style="font-size:11px;font-weight:700;color:#166534;letter-spacing:1px;">VĨ ĐỘ</span>
      <span id="disp_lat" style="font-family:monospace;font-weight:700;color:#15803d;font-size:14px;min-width:70px;">{lat_val or '—'}</span>
    </div>
    <div style="background:#eff6ff;border:1px solid #93c5fd;border-radius:8px;padding:8px 14px;display:flex;align-items:center;gap:8px;">
      <span style="font-size:11px;font-weight:700;color:#1e40af;letter-spacing:1px;">KINH ĐỘ</span>
      <span id="disp_lng" style="font-family:monospace;font-weight:700;color:#1d4ed8;font-size:14px;min-width:70px;">—</span>
    </div>
    <button type="button" onclick="hotelMapLocateMe()"
      style="background:#2563eb;color:#fff;border:none;border-radius:6px;padding:9px 16px;font-size:12px;font-weight:600;cursor:pointer;">
      📍 Vị trí của tôi
    </button>
    <button type="button" onclick="hotelMapReset()"
      style="background:#ef4444;color:#fff;border:none;border-radius:6px;padding:9px 14px;font-size:12px;font-weight:600;cursor:pointer;">
      ✕ Xóa
    </button>
  </div>

  <!-- Map -->
  <div id="hotel-leaflet-map" style="
    height:450px;
    border:2px solid #d1d5db;
    border-radius:12px;
    overflow:hidden;
    box-shadow:0 4px 16px rgba(0,0,0,.1);
  "></div>

  <!-- Gợi ý -->
  <p style="font-size:11px;color:#6b7280;margin-top:8px;margin-bottom:0;">
    🖱️ <strong>Click lên bản đồ</strong> để đặt vị trí · Marker có thể <strong>kéo thả</strong> · Chỉ nhận tọa độ trong <strong>Việt Nam</strong>
  </p>

  <!-- Error -->
  <div id="hotel-map-error" style="
    display:none;
    color:#dc2626;font-size:12px;
    background:#fef2f2;border:1px solid #fca5a5;
    border-radius:6px;padding:8px 12px;margin-top:8px;
  "></div>

</div>

<script>
(function() {{

  const LAT_MIN=8.18, LAT_MAX=23.39, LNG_MIN=102.14, LNG_MAX=109.46;
  let hotelMap = null;
  let hotelMarker = null;

  function getLatInput()  {{ return document.getElementById('{lat_field_id}'); }}
  function getLngInput()  {{ return document.getElementById('{lng_field_id}'); }}
  function getDispLat()   {{ return document.getElementById('disp_lat'); }}
  function getDispLng()   {{ return document.getElementById('disp_lng'); }}
  function getErrDiv()    {{ return document.getElementById('hotel-map-error'); }}

  function showError(msg) {{
    const d = getErrDiv();
    d.textContent = msg; d.style.display = 'block';
    setTimeout(() => d.style.display='none', 5000);
  }}

  function isInVN(lat, lng) {{
    return lat >= LAT_MIN && lat <= LAT_MAX && lng >= LNG_MIN && lng <= LNG_MAX;
  }}

  function setCoord(lat, lng) {{
    if (!isInVN(lat, lng)) {{
      showError(`❌ Tọa độ (${{lat.toFixed(4)}}, ${{lng.toFixed(4)}}) nằm ngoài Việt Nam! Vui lòng chọn điểm trong lãnh thổ VN.`);
      return false;
    }}
    const la = Math.round(lat*10000)/10000;
    const lo = Math.round(lng*10000)/10000;

    getLatInput().value = la;
    getLngInput().value = lo;
    getDispLat().textContent = la;
    getDispLng().textContent = lo;
    getErrDiv().style.display = 'none';

    const hotelIcon = L.divIcon({{
      html: `<div style="background:#C9A84C;color:#0D0D0D;width:38px;height:38px;
        border-radius:50% 50% 50% 0;display:flex;align-items:center;
        justify-content:center;font-size:20px;transform:rotate(-45deg);
        box-shadow:0 4px 14px rgba(0,0,0,.35);border:2px solid #333;">
        <span style="transform:rotate(45deg)">🏨</span></div>`,
      className:'', iconSize:[38,38], iconAnchor:[19,38], popupAnchor:[0,-38]
    }});

    if (hotelMarker) {{
      hotelMarker.setLatLng([la, lo]);
    }} else {{
      hotelMarker = L.marker([la, lo], {{icon: hotelIcon, draggable: true}}).addTo(hotelMap);
      hotelMarker.on('dragend', function(e) {{
        const p = e.target.getLatLng();
        setCoord(p.lat, p.lng);
      }});
    }}
    return true;
  }}

  function initHotelMap() {{
    if (typeof L === 'undefined') {{ setTimeout(initHotelMap, 300); return; }}
    const mapEl = document.getElementById('hotel-leaflet-map');
    if (!mapEl || mapEl._leaflet_id) return;

    // Xác định center: nếu đã có tọa độ thì zoom vào đó
    const existLat = parseFloat(getLatInput().value);
    const existLng = parseFloat(getLngInput().value);
    const hasExist = !isNaN(existLat) && !isNaN(existLng);

    hotelMap = L.map('hotel-leaflet-map', {{
      center: hasExist ? [existLat, existLng] : [16.0, 106.0],
      zoom:   hasExist ? 14 : 6,
      minZoom: 5,
      maxZoom: 18,
    }});

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd', maxZoom: 19,

    // Vẽ khung Việt Nam
    L.rectangle([[LAT_MIN,LNG_MIN],[LAT_MAX,LNG_MAX]], {{
      color:'#16a34a', weight:1.5, fillOpacity:0.03, dashArray:'8,5'
    }}).addTo(hotelMap).bindTooltip('🇻🇳 Lãnh thổ Việt Nam', {{permanent:false}});

    // Nếu đã có tọa độ, đặt marker luôn
    if (hasExist) {{
      setCoord(existLat, existLng);
      // Cập nhật display lng vì đã load sẵn
      const lngEl = getLngInput();
      if (lngEl) getDispLng().textContent = lngEl.value || '—';
    }}

    // Click map
    hotelMap.on('click', function(e) {{
      setCoord(e.latlng.lat, e.latlng.lng);
    }});

    // Hiện tọa độ chuột
    const mouseDiv = L.control({{position:'bottomleft'}});
    mouseDiv.onAdd = function() {{
      const d = L.DomUtil.create('div');
      d.id = 'hotel-mouse-coord';
      d.style.cssText = 'background:rgba(255,255,255,.9);padding:5px 10px;border-radius:5px;font-size:11px;font-family:monospace;color:#374151;';
      d.textContent = 'Di chuyển chuột lên bản đồ...';
      return d;
    }};
    mouseDiv.addTo(hotelMap);

    hotelMap.on('mousemove', function(e) {{
      const d = document.getElementById('hotel-mouse-coord');
      if (d) d.textContent = `${{e.latlng.lat.toFixed(5)}}°N  ${{e.latlng.lng.toFixed(5)}}°E`;
    }});
  }}

  // Nút định vị
  window.hotelMapLocateMe = function() {{
    if (!navigator.geolocation) {{ showError('Trình duyệt không hỗ trợ GPS'); return; }}
    const btn = event.target;
    btn.textContent = '⏳ Đang định vị...'; btn.disabled = true;
    navigator.geolocation.getCurrentPosition(
      function(pos) {{
        btn.textContent = '📍 Vị trí của tôi'; btn.disabled = false;
        const ok = setCoord(pos.coords.latitude, pos.coords.longitude);
        if (ok && hotelMap) hotelMap.setView([pos.coords.latitude, pos.coords.longitude], 16);
      }},
      function() {{
        btn.textContent = '📍 Vị trí của tôi'; btn.disabled = false;
        showError('❌ Không lấy được GPS. Hãy click thẳng lên bản đồ.');
      }},
      {{enableHighAccuracy:true, timeout:12000}}
    );
  }};

  // Nút reset
  window.hotelMapReset = function() {{
    getLatInput().value = ''; getLngInput().value = '';
    getDispLat().textContent = '—'; getDispLng().textContent = '—';
    getErrDiv().style.display = 'none';
    if (hotelMarker && hotelMap) {{ hotelMap.removeLayer(hotelMarker); hotelMarker = null; }}
  }};

  // Khởi động
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initHotelMap);
  }} else {{
    initHotelMap();
  }}

}})();
</script>
"""
        return html