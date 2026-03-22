#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// ============================================================
// WIFI CREDENTIALS — change these to your WiFi name/password
// ============================================================
const char* ssid     = "WIFI_SSID";
const char* password = "YOUR_PASSWORD";

// ============================================================
// PIN DEFINITIONS
// ============================================================
#define SENSOR_1  34   // Zone 1 - Hotgi Road
#define SENSOR_2  35   // Zone 2 - Akkalkot Road
#define SENSOR_3  32   // Zone 3 - Vijapur Road

#define LED_RED    25
#define LED_YELLOW 26
#define LED_GREEN  27
#define BUZZER     14

// ============================================================
// ZONE NAMES
// ============================================================
const char* zoneNames[] = {
  "Hotgi Road",
  "Akkalkot Road",
  "Vijapur Road"
};

WebServer server(80);

float prevPressures[3] = {0, 0, 0};
bool leakDetected[3]   = {false, false, false};

// ============================================================
// CONVERT RAW SENSOR VALUE TO BAR
// ============================================================
float readPressure(int pin) {
  int raw = analogRead(pin);
  float voltage  = raw * (3.3 / 4095.0);  // ESP32 12-bit ADC
  float pressure = voltage * 1.5;          // calibrate for your sensor
  return max(0.0f, min(5.0f, pressure));   // clamp 0-5 bar
}

// ============================================================
// GET STATUS STRING
// ============================================================
const char* getStatus(float pressure) {
  if (pressure < 1.0) return "critical";
  if (pressure < 2.0) return "warning";
  return "normal";
}

// ============================================================
// LEAK DETECTION
// ============================================================
bool detectLeak(float current, float previous) {
  return (previous - current) > 0.8;  // sudden drop = leak
}

// ============================================================
// UPDATE LEDS AND BUZZER
// ============================================================
void updateIndicators(float p1, float p2, float p3, bool anyLeak) {
  bool anyCritical = (p1 < 1.0 || p2 < 1.0 || p3 < 1.0);
  bool anyWarning  = (p1 < 2.0 || p2 < 2.0 || p3 < 2.0);

  digitalWrite(LED_RED,    LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN,  LOW);
  digitalWrite(BUZZER,     LOW);

  if (anyCritical || anyLeak) {
    digitalWrite(LED_RED, HIGH);
    if (anyLeak) digitalWrite(BUZZER, HIGH);
  } else if (anyWarning) {
    digitalWrite(LED_YELLOW, HIGH);
  } else {
    digitalWrite(LED_GREEN, HIGH);
  }
}

// ============================================================
// HANDLE /data ENDPOINT
// ============================================================
void handleData() {
  // CORS header so dashboard can fetch
  server.sendHeader("Access-Control-Allow-Origin", "*");

  float pressures[3];
  pressures[0] = readPressure(SENSOR_1);
  pressures[1] = readPressure(SENSOR_2);
  pressures[2] = readPressure(SENSOR_3);

  bool anyLeak = false;

  // Check for leaks
  for (int i = 0; i < 3; i++) {
    leakDetected[i] = detectLeak(pressures[i], prevPressures[i]);
    if (leakDetected[i]) anyLeak = true;
    prevPressures[i] = pressures[i];
  }

  // Update LEDs and buzzer
  updateIndicators(
    pressures[0], pressures[1], pressures[2], anyLeak
  );

  // Build JSON response
  StaticJsonDocument<512> doc;
  JsonArray zones = doc.createNestedArray("zones");

  String zoneIds[] = {"z1", "z2", "z3"};

  for (int i = 0; i < 3; i++) {
    JsonObject zone = zones.createNestedObject();
    zone["id"]       = zoneIds[i];
    zone["name"]     = zoneNames[i];
    zone["pressure"] = round(pressures[i] * 100) / 100.0;
    zone["status"]   = getStatus(pressures[i]);
    zone["leak"]     = leakDetected[i];
    zone["flow"]     = round(pressures[i] * 16);
  }

  doc["leak_detected"] = anyLeak;
  doc["timestamp"]     = millis();

  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

// ============================================================
// HANDLE /health ENDPOINT
// ============================================================
void handleHealth() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", "{\"status\":\"ok\",\"device\":\"AquaSync ESP32\"}");
}

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== AquaSync ESP32 Starting ===");

  // Pin modes
  pinMode(LED_RED,    OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN,  OUTPUT);
  pinMode(BUZZER,     OUTPUT);

  // All off initially
  digitalWrite(LED_RED,    LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN,  LOW);
  digitalWrite(BUZZER,     LOW);

  // Connect to WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("📡 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.println("Open dashboard and set ESP32_IP to above address");
    digitalWrite(LED_GREEN, HIGH); // Green = connected
  } else {
    Serial.println("\n❌ WiFi Failed! Check credentials.");
    digitalWrite(LED_RED, HIGH); // Red = failed
  }

  // Register endpoints
  server.on("/data",   handleData);
  server.on("/health", handleHealth);
  server.begin();

  Serial.println("🌐 Web server started!");
  Serial.println("=== Ready ===");
}

// ============================================================
// LOOP
// ============================================================
void loop() {
  server.handleClient();
  delay(100);
}