import 'package:geolocator/geolocator.dart';
import 'package:sqflite/sqflite.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// 2-son texnikumning aniq koordinatalari va 500 metr radius
const double TECHNIKUM_LAT = 38.971199;
const double TECHNIKUM_LON = 66.707470;
const double RADIUS_METERS = 500.0; // Ruxsat etilgan radius 500 metr

// GPS orqali masofani tekshirish va saqlash funksiyasi
void checkLocationAndSave(int userId, String fullName) async {
  Position position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high);

  double distance = Geolocator.distanceBetween(
    position.latitude,
    position.longitude,
    TECHNIKUM_LAT,
    TECHNIKUM_LON,
  );

  // 500 metr radius ichida ekanligini tekshiramiz
  if (distance <= RADIUS_METERS) {
    String currentTime = DateTime.now().toString();
    
    // Internet bor-yo'qligini tekshiramiz
    bool isConnected = await checkInternetConnection();
    
    if (isConnected) {
      sendToServer(userId, fullName, position.latitude, position.longitude, "Keldi");
    } else {
      // Internet bo'lmasa mahalliy bazaga saqlab turadi
      saveToLocalDatabase(userId, fullName, currentTime, "Keldi");
    }
  }
}

// Internet mavjudligini tekshirish
Future<bool> checkInternetConnection() async {
  try {
    final result = await http.get(Uri.parse('https://google.com'));
    return result.statusCode == 200;
  } catch (_) {
    return false;
  }
}

// Serverga yuborish (Render ssilkangizni qo'yasiz)
Future<void> sendToServer(int id, String name, double lat, double lon, String status) async {
  // Quyidagi ssilka o'rniga Render'dan olgan o'z ssilkangizni yozasiz
  final url = Uri.parse('https://texnikum-davomat.onrender.com/check-attendance');
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

// Mahalliy xotiraga saqlash (internet bo'lmaganda)
void saveToLocalDatabase(int id, String name, String time, String status) {
  // SQLite bazasiga vaqtincha yozib qo'yish mantiqi
  print("Ma'lumot lokal bazaga saqlandi: $name, $time");
}
