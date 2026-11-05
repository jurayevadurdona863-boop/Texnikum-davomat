from flask import Flask, request, jsonify
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

app = Flask(__name__)

# 2-son texnikumning aniq koordinatalari va 500 metr radius
TECHNIKUM_LAT = 38.971199
TECHNIKUM_LON = 66.707470
RADIUS_METERS = 500  # Ruxsat etilgan radius 500 metr

EXCEL_FILE = 'teachers.xlsx'  # Xodimlar Excel fayli

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

@app.route('/')
def home():
    return "2-son Texnikum Davomat Serveri mukammal ishlamoqda!"

@app.route('/check-attendance', methods=['POST'])
def check_attendance():
    data = request.json
    user_id = data.get('user_id')  # JSHR raqami
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')
    action_type = data.get('action_type', 'Keldi')

    if not all([user_id, user_lat, user_lon]):
        return jsonify({'success': False, 'message': 'Ma’lumotlar yetishmayapti!'}), 400

    # Excel bazadan xodimni JSHR (F ustuni / 5-indeks) bo'yicha qidiramiz
    full_name = "Noma'lum xodim"
    if os.path.exists(EXCEL_FILE):
        try:
            df_excel = pd.read_excel(EXCEL_FILE, header=None)
            
            # F ustuni (5-indeks) PNFL bo'yicha qidirishga to'g'irlandi
            matched = df_excel[df_excel.iloc[:, 5].astype(str).str.contains(str(user_id), na=False)]
            if not matched.empty:
                # B ustunidan (1-indeks) Ism sharifini olamiz
                full_name = str(matched.iloc[0, 1])
        except Exception as e:
            print("Excel o'qish xatosi:", e)

    # Masofani hisoblaymiz
    distance = calculate_distance(user_lat, user_lon, TECHNIKUM_LAT, TECHNIKUM_LON)

    if distance <= RADIUS_METERS:
        # O'zbekiston vaqti (UTC +5) bo'yicha aniq vaqtni olish
        UZT = timezone(timedelta(hours=5))
        now_uzt = datetime.now(UZT)
        today_date = now_uzt.strftime("%Y-%m-%d")
        now_time = now_uzt.strftime("%H:%M:%S")  # Soat va minutigacha
        
        file_path = 'attendance.csv'
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            df = pd.DataFrame(columns=['user_id', 'full_name', 'date', 'time', 'status'])

        new_row = {
            'user_id': user_id, 
            'full_name': full_name, 
            'date': today_date, 
            'time': now_time, 
            'status': action_type
        }
        
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
