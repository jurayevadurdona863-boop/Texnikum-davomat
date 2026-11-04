from flask import Flask, request, jsonify
import math
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# 2-son texnikumning aniq koordinatalari va 500 metr radius
TECHNIKUM_LAT = 38.971199
TECHNIKUM_LON = 66.707470
RADIUS_METERS = 500  # Ruxsat etilgan radius 500 metr qilib belgilandi

def calculate_distance(lat1, lon1, lat2, lon2):
    """Ikki nuqta orasidagi masofani metrda hisoblaydi"""
    R = 6371000  # Yer radiusi (metrda)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

@app.route('/check-attendance', methods=['POST'])
def check_attendance():
    data = request.json
    user_id = data.get('user_id')
    full_name = data.get('full_name')
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')
    action_type = data.get('action_type', 'Keldi')  # 'Keldi' yoki 'Ketdi'

    if not all([user_id, user_lat, user_lon, full_name]):
        return jsonify({'success': False, 'message': 'Ma’lumotlar yetishmayapti!'}), 400

    # Xodimning turgan joyi bilan texnikum orasidagi masofa
    distance = calculate_distance(user_lat, user_lon, TECHNIKUM_LAT, TECHNIKUM_LON)

    if distance <= RADIUS_METERS:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        file_path = 'attendance.csv'
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            df = pd.DataFrame(columns=['user_id', 'full_name', 'date', 'time', 'status'])

        new_row = {
            'user_id': user_id, 
            'full_name': full_name, 
            'date': today_date, 
            'time': now, 
            'status': action_type
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(file_path, index=False)

        return jsonify({
            'success': True,
            'message': f"Muvaffaqiyatli qayd etildi: {action_type}!",
            'time': now,
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