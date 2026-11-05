from flask import Flask, request, jsonify
import math
from datetime import datetime, timezone, timedelta
import os

app = Flask(__name__)

TECHNIKUM_LAT = 38.971199
TECHNIKUM_LON = 66.707470
RADIUS_METERS = 500

# O'qituvchilar bazasi (JSHR va Ism-shariflar)
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
    return "2-son Texnikum Davomat Serveri mukammal ishlamoqda!"

@app.route('/check-attendance', methods=['POST'])
def check_attendance():
    data = request.json
    user_id = str(data.get('user_id')).strip()
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')
    action_type = data.get('action_type', 'Keldi')

    if not all([user_id, user_lat, user_lon]):
        return jsonify({'success': False, 'message': 'Ma’lumotlar yetishmayapti!'}), 400

    # Baza orqali ismni topamiz
    full_name = TEACHERS_DB.get(user_id, "Noma'lum xodim")

    distance = calculate_distance(user_lat, user_lon, TECHNIKUM_LAT, TECHNIKUM_LON)

    if distance <= RADIUS_METERS:
        UZT = timezone(timedelta(hours=5))
        now_uzt = datetime.now(UZT)
        today_date = now_uzt.strftime("%Y-%m-%d")
        now_time = now_uzt.strftime("%H:%M:%S")
        
        file_path = 'attendance.csv'
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
        except Exception:
            import pandas as pd
            df = pd.DataFrame(columns=['user_id', 'full_name', 'date', 'time', 'status'])

        new_row = {
            'user_id': user_id, 
            'full_name': full_name, 
            'date': today_date, 
            'time': now_time, 
            'status': action_type
        }
        
        import pandas as pd
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(file_path, index=False)

        return jsonify({
            'success': True,
            'message': f"Muvaffaqiyatli qayd etildi: {full_name} ({action_type})!",
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
