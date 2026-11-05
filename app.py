from flask import Flask, request, jsonify, render_template_string, Response
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
from functools import wraps

app = Flask(__name__)

TECHNIKUM_LAT = 38.971199
TECHNIKUM_LON = 66.707470
RADIUS_METERS = 500

# O'qituvchilar bazasi
TEACHERS_DB = {
    "30306817710045": "Xujauyozov Bekzod Sunnatovich",
    "950741212": "Sultonov Abror Tursunpo'lat o'g'li",
    "990294334": "Hasanov Zohid Pardayevich",
    "317127530022": "Qulmanatov Azamat Xolmanatovich",
    "30102985730037": "Ismatov Xudoyqul Dilshod o'g'li",
    "31304605730039": "Azimov Tohir Eshpo'latovich",
    "42308952710050": "Xo'janov Chori Karimovich",
    "32501/15/30026": "Ismatova Umida Dilshod qizi",
    "41401815730020": "Moyliyev Muxtor Xushmurodovich",
    "33117915590010": "Boysmov Chinnigul Xayrullayevna"
}

ADMIN_USER = "admin"
ADMIN_PASS = "texnikum2026"

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
        'Kirish taqiqlandi! Login va parolni kiriting.', 401,
        {'WWW-Authenticate': 'Basic realm="Admin Panel"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route('/')
def home():
    return "2-son Texnikum Davomat Serveri (Avtomatik vaqt nazorati bilan) ishlamoqda!"

# --- ADMIN PANEL ---
@app.route('/admin')
@requires_auth
def admin_panel():
    file_path = 'attendance.csv'
    attendance_data = []
    
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            attendance_data = df.to_dict(orient='records')
        except Exception as e:
            print("CSV o'qish xatosi:", e)

    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <title>2-son Texnikum - Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f6f9; }
            h2 { color: #333; text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            th, td { padding: 12px; border: 1px solid #ddd; text-align: center; }
            th { background-color: #007bff; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .badge-keldi { padding: 5px 10px; border-radius: 4px; color: white; background: #28a745; }
            .badge-kechikdi { padding: 5px 10px; border-radius: 4px; color: white; background: #ffc107; color: black; }
            .badge-erta { padding: 5px 10px; border-radius: 4px; color: white; background: #dc3545; }
        </style>
    </head>
    <body>
        <h2>2-son Texnikum Xodimlari Davomati (Admin Panel)</h2>
        <table>
            <tr>
                <th>JSHR (User ID)</th>
                <th>F.I.SH</th>
                <th>Sana</th>
                <th>Vaqt</th>
                <th>Holati</th>
            </tr>
            {% for row in data %}
            <tr>
                <td>{{ row.user_id }}</td>
                <td>{{ row.full_name }}</td>
                <td>{{ row.date }}</td>
                <td>{{ row.time }}</td>
                <td>
                    {% if "Kechikdi" in row.status %}
                        <span class="badge-kechikdi">{{ row.status }}</span>
                    {% elif "Erta" in row.status %}
                        <span class="badge-erta">{{ row.status }}</span>
                    {% else %}
                        <span class="badge-keldi">{{ row.status }}</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_content, data=attendance_data)

@app.route('/check-attendance', methods=['POST'])
def check_attendance():
    data = request.json
    user_id = str(data.get('user_id')).strip()
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')
    action_type = data.get('action_type', 'Keldi') # Keldi yoki Ketdi

    if not all([user_id, user_lat, user_lon]):
        return jsonify({'success': False, 'message': 'Ma’lumotlar yetishmayapti!'}), 400

    full_name = TEACHERS_DB.get(user_id, "Noma'lum xodim")
    distance = calculate_distance(user_lat, user_lon, TECHNIKUM_LAT, TECHNIKUM_LON)

    if distance <= RADIUS_METERS:
        UZT = timezone(timedelta(hours=5))
        now_uzt = datetime.now(UZT)
        today_date = now_uzt.strftime("%Y-%m-%d")
        now_time = now_uzt.strftime("%H:%M:%S")
        current_hour_minute = now_uzt.strftime("%H:%M")

        # Avtomatik vaqt tekshiruvi mantiqi
        final_status = action_type
        if action_type == 'Keldi':
            if current_hour_minute <= "08:30":
                final_status = "O'z vaqtida keldi"
            else:
                final_status = f"Kechikdi ({current_hour_minute})"
        elif action_type == 'Ketdi':
            if current_hour_minute < "16:00":
                final_status = f"Erta chiqib ketdi ({current_hour_minute})"
            else:
                final_status = "O'z vaqtida ketdi"

        file_path = 'attendance.csv'
        try:
            df = pd.read_csv(file_path)
        except Exception:
            df = pd.DataFrame(columns=['user_id', 'full_name', 'date', 'time', 'status'])

        new_row = {
            'user_id': user_id, 
            'full_name': full_name, 
            'date': today_date, 
            'time': now_time, 
            'status': final_status
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(file_path, index=False)

        return jsonify({
            'success': True,
            'message': f"Qayd etildi: {full_name} - {final_status}!",
            'time': now_time,
            'distance': round(distance, 1)
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Siz texnikum hududida emassiz! Masofa: {int(distance)} metr.'
        }), 403

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
