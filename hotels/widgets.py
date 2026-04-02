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

  <!-- ── Tìm địa chỉ để lấy tọa độ ── -->
  <div style="display:flex;gap:8px;margin-bottom:10px;">
    <div style="position:relative;flex:1;">
      <input type="text" id="addr-search-input"
        placeholder="🔍 Nhập địa chỉ để lấy tọa độ... VD: 22 Nguyen Hue, Q1, HCM"
        style="width:100%;padding:9px 14px;border:1.5px solid #e8e9ec;border-radius:8px;
               font-size:13px;outline:none;"
        onkeydown="if(event.key==='Enter'){{event.preventDefault();adminGeocode();}}"
      >
      <div id="addr-suggestions" style="
        position:absolute;top:100%;left:0;right:0;background:#fff;
        border:1.5px solid #C9A84C;border-top:none;border-radius:0 0 8px 8px;
        z-index:9999;max-height:200px;overflow-y:auto;display:none;
        box-shadow:0 8px 24px rgba(0,0,0,.1);">
      </div>
    </div>
    <button type="button" onclick="adminGeocode()"
      style="background:#C9A84C;color:#0f1117;border:none;border-radius:8px;
             padding:9px 18px;font-size:12px;font-weight:700;cursor:pointer;white-space:nowrap;">
      📍 Lấy tọa độ
    </button>
  </div>
  <div id="addr-msg" style="display:none;font-size:12px;padding:7px 12px;border-radius:6px;margin-bottom:8px;"></div>

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


  // ── Geocode: tìm địa chỉ → tọa độ (chỉ VN) ──────────────────────
  window.adminGeocode = async function() {{
    const q = document.getElementById('addr-search-input').value.trim();
    if (!q) return;
    showAddrMsg('⏳ Đang tìm...', '#eff6ff', '#1d4ed8');
    try {{
      const query = q.toLowerCase().includes('vi') ? q : q + ', Vietnam';
      const url = 'https://nominatim.openstreetmap.org/search?format=json&q=' + encodeURIComponent(query) + '&limit=5&countrycodes=vn&accept-language=vi';
      const data = await (await fetch(url, {{headers:{{'Accept-Language':'vi'}}}})).json();
      if (!data.length) {{
        showAddrMsg('❌ Không tìm thấy địa chỉ tại Việt Nam', '#fff5f5', '#dc2626');
        return;
      }}
      if (data.length === 1) {{
        applyGeoResult(data[0]);
      }} else {{
        window._geoResults = data;
        const box = document.getElementById('addr-suggestions');
        box.innerHTML = data.map((item, i) => {{
          const short = item.display_name.split(',').slice(0,3).join(', ');
          return '<div onclick="applyGeoResultGlobal(' + i + ')" style="padding:9px 14px;cursor:pointer;font-size:12px;border-bottom:1px solid #f3f0eb;" onmouseover="this.style.background=\'#fffdf5\'" onmouseout="this.style.background=\'\'"><div style="font-weight:600;">📍 ' + short + '</div><div style="font-size:10px;color:#aaa;">' + item.type + '</div></div>';
        }}).join('');
        box.style.display = 'block';
        window.applyGeoResultGlobal = function(i) {{ applyGeoResult(window._geoResults[i]); }};
        showAddrMsg('📍 Tìm thấy ' + data.length + ' kết quả — chọn bên dưới', '#f0fdf4', '#15803d');
      }}
    }} catch(e) {{
      showAddrMsg('❌ Lỗi kết nối. Thử lại sau.', '#fff5f5', '#dc2626');
    }}
  }};

  function applyGeoResult(item) {{
    const lat = parseFloat(item.lat), lng = parseFloat(item.lon);
    const VN_LAT_MIN=8.18, VN_LAT_MAX=23.39, VN_LNG_MIN=102.14, VN_LNG_MAX=109.46;
    if (lat < VN_LAT_MIN || lat > VN_LAT_MAX || lng < VN_LNG_MIN || lng > VN_LNG_MAX) {{
      showAddrMsg('❌ Tọa độ (' + lat.toFixed(4) + ', ' + lng.toFixed(4) + ') nằm ngoài Việt Nam!', '#fff5f5', '#dc2626');
      return;
    }}
    const la = Math.round(lat*1e6)/1e6, lo = Math.round(lng*1e6)/1e6;
    document.getElementById('id_latitude').value = la;
    document.getElementById('id_longitude').value = lo;
    document.getElementById('disp_lat').textContent = la;
    document.getElementById('disp_lng').textContent = lo;
    if (hotelMarker) hotelMap.removeLayer(hotelMarker);
    hotelMarker = L.marker([la, lo], {{
      icon: L.divIcon({{
        html: '<div style="background:#C9A84C;color:#0D0D0D;width:38px;height:38px;border-radius:50% 50% 50% 0;display:flex;align-items:center;justify-content:center;font-size:20px;transform:rotate(-45deg);box-shadow:0 4px 14px rgba(0,0,0,.35);border:2px solid #333;"><span style="transform:rotate(45deg)">&#127968;</span></div>',
        className:'', iconSize:[38,38], iconAnchor:[19,38], popupAnchor:[0,-38]
      }}),
      draggable:true
    }}).addTo(hotelMap);
    hotelMarker.on('dragend', function(e) {{ const p=e.target.getLatLng(); setCoord(p.lat, p.lng); }});
    hotelMap.setView([la, lo], 17);
    document.getElementById('addr-suggestions').style.display = 'none';
    const name = item.display_name.split(',').slice(0,2).join(', ');
    document.getElementById('addr-search-input').value = name;
    showAddrMsg('✅ Đã đặt tọa độ: ' + la + '°N, ' + lo + '°E', '#f0fdf4', '#15803d');
    document.getElementById('hotel-map-error').style.display = 'none';
  }}

  function showAddrMsg(msg, bg, color) {{
    const el = document.getElementById('addr-msg');
    el.textContent = msg; el.style.display = 'block';
    el.style.background = bg; el.style.color = color;
    el.style.border = '1px solid ' + color + '40';
  }}

  document.addEventListener('click', function(e) {{
    if (!e.target.closest('#addr-suggestions') && !e.target.closest('#addr-search-input'))
      document.getElementById('addr-suggestions').style.display = 'none';
  }});

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