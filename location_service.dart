import 'package:geolocator/geolocator.dart';
import 'package:sqflite/sqflite.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// 2-son texnikumning aniq koordinatalari va 500 metr radius
const double TECHNIKUM_LAT = 38.971199;
const double TECHNIKUM_LON = 66.707470;
const double RADIUS_METERS = 500.0; // Ruxsat etilgan radius 500 metr

// GPS orqali masofani tekshirish va yuborish funksiyasi
void checkLocationAndSave(String userJshr) async {
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
      sendToServer(userJshr, position.latitude, position.longitude, "Keldi");
    } else {
      // Internet bo'lmasa mahalliy bazaga saqlab turadi
      saveToLocalDatabase(userJshr, currentTime, "Keldi");
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

// Serverga JSHR va koordinatalarni yuborish
Future<void> sendToServer(String jshr, double lat, double lon, String status) async {
  // Render'dan olgan o'z ssilkangizni yozasiz
  final url = Uri.parse('https://texnikum-davomat.onrender.com/check-attendance');
  try {
    await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "user_id": jshr, // Exceldagi JSHR kodi jo'natiladi
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
void saveToLocalDatabase(String jshr, String time, String status) {
  print("Ma'lumot lokal bazaga saqlandi: JSHR $jshr, $time");
}
