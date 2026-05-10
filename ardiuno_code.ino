#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 21
#define RST_PIN 22

MFRC522 mfrc522(SS_PIN, RST_PIN);

// 📶 WiFi credentials
const char* ssid = "Santhosh";
const char* password = "12345678";

// 🌐 YOUR HTTPS NGROK URL
String serverURL = "https://dingbat-blinks-luminance.ngrok-free.dev/update";

// 📍 Location
String LOCATION = "Chengalpattu Toll Gate";
float LAT = 12.6916;
float LON = 79.9832;

// 🔥 UID → Vehicle map
String getVehicleNumber(String uid) {
  uid.toLowerCase();

  if (uid == "4390c0e3") {
    return "HR99GX0777";
  }
  else if (uid == "d3b9d6e2") {
    return "HR98AA0000";
  }

  return "UNKNOWN";
}

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();

  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi Connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {

  // 📡 Wait for RFID
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  String uid = "";

  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }

  uid.toLowerCase();

  Serial.print("📌 UID: ");
  Serial.println(uid);

  String vehicleNumber = getVehicleNumber(uid);

  if (vehicleNumber == "UNKNOWN") {
    Serial.println("❌ Unknown card");
    return;
  }

  Serial.print("✅ Vehicle: ");
  Serial.println(vehicleNumber);

  if (WiFi.status() == WL_CONNECTED) {

    // 🔥 HTTPS FIX
    WiFiClientSecure client;
    client.setInsecure();  // skip SSL cert validation

    HTTPClient http;
    http.begin(client, serverURL);
    http.addHeader("Content-Type", "application/json");

    // ✅ MATCH PYTHON FORMAT
    String payload = "{";
    payload += "\"bus_no\":\"" + vehicleNumber + "\",";
    payload += "\"location\":\"" + LOCATION + "\",";
    payload += "\"lat\":" + String(LAT, 6) + ",";
    payload += "\"lon\":" + String(LON, 6) + ",";
    payload += "\"route\":\"RFID Route\"";
    payload += "}";

    Serial.println("📤 Sending JSON:");
    Serial.println(payload);

    int code = http.POST(payload);

    Serial.print("📡 Response Code: ");
    Serial.println(code);

    if (code == -1) {
      Serial.println("❌ ERROR: Connection failed");
      Serial.println("👉 Check ngrok is running");
      Serial.println("👉 Check URL is active");
    }

    http.end();
  }

  delay(3000); // cooldown
}
