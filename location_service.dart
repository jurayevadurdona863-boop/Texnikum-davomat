import 'package:geolocator/geolocator.dart';
import 'package:sqflite/sqflite.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// Texnikum koordinatalari
const double TECHNIKUM_LAT = 38.971199;
const double TECHNIKUM_LON = 66.707470;
const double RADIUS_METERS = 500.0;

// 1. GPS orqali masofani tekshirish funksiyasi
void checkLocationAndSave(int userId, String fullName) async {
  Position position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high);

  double distance = Geolocator.distanceBetween(
    position.latitude,
    position.longitude,
    TECHNIKUM_LAT,
    TECHNIKUM_LON,
  );

  if (distance <= RADIUS_METERS) {
    // Hududda! Vaqtni olamiz
    String currentTime = DateTime.now().toString();
    
    // Internet bor-yo'qligini tekshirib, serverga yuboramiz yoki lokal bazaga saqlaymiz
    bool isConnected = await checkInternetConnection();
    
    if (isConnected) {
      sendToServer(userId, fullName, position.latitude, position.longitude, "Keldi");
    } else {
      saveToLocalDatabase(userId, fullName, currentTime, "Keldi");
    }
  }
}

// 2. Serverga yuborish
Future<void> sendToServer(int id, String name, double lat, double lon, String status) async {
  final url = Uri.parse('https://SIZNING-RENDER-SSILKANGIZ.onrender.com/check-attendance');
  try {
    await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "user_id": id,
        "full_name": name,
        "latitude": lat,
        "longitude": lon,
        "action_type": status
      }),
    );
  } catch (e) {
    print("Serverga ulanish xatosi, ma'lumot saqlab qolindi.");
  }
}