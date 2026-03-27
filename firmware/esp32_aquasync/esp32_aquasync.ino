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
// Flow sensors (YF-S201) output pulse signals — use interrupt-
// capable digital GPIO pins on ESP WROOM-32.
// ============================================================
#define FLOW_SENSOR_1  18   // Zone 1 - Hotgi Road
#define FLOW_SENSOR_2  19   // Zone 2 - Akkalkot Road

#define LED_RED    25
#define LED_YELLOW 26
#define LED_GREEN  27
#define BUZZER     14

// ============================================================
// FLOW SENSOR CALIBRATION
// YF-S201: 7.5 pulses per second per L/min
// If you have a different sensor, adjust FLOW_CALIBRATION_FACTOR.
// ============================================================
#define FLOW_CALIBRATION_FACTOR  7.5f   // pulses/sec per L/min (YF-S201)

// Flow measurement window in milliseconds
#define FLOW_SAMPLE_MS  1000UL

// ============================================================
// ZONE NAMES
// ============================================================
const char* zoneNames[] = {
  "Hotgi Road",
  "Akkalkot Road"
};

WebServer server(80);

// Pulse counters — updated by interrupts
volatile unsigned long pulseCount1 = 0;
volatile unsigned long pulseCount2 = 0;

// Calculated flow rates updated in loop() — read by handleData()
float currentFlowRates[2] = {0.0f, 0.0f};
unsigned long lastSampleMs = 0;

float prevFlowRates[2] = {0.0f, 0.0f};
bool  leakDetected[2]  = {false, false};

void IRAM_ATTR onPulse1() { pulseCount1++; }
void IRAM_ATTR onPulse2() { pulseCount2++; }

// ============================================================
// UPDATE FLOW RATES — called from loop() every FLOW_SAMPLE_MS.
// Snapshot and reset pulse counters atomically to avoid races.
// ============================================================
void updateFlowRates() {
  noInterrupts();
  unsigned long c1 = pulseCount1;
  unsigned long c2 = pulseCount2;
  pulseCount1 = 0;
  pulseCount2 = 0;
  interrupts();

  float elapsed = (float)FLOW_SAMPLE_MS / 1000.0f;  // seconds
  currentFlowRates[0] = max(0.0f, min(60.0f, (c1 / elapsed) / FLOW_CALIBRATION_FACTOR));
  currentFlowRates[1] = max(0.0f, min(60.0f, (c2 / elapsed) / FLOW_CALIBRATION_FACTOR));
}

// ============================================================
// GET STATUS STRING
// ============================================================
const char* getStatus(float flowRate) {
  if (flowRate < 5.0)  return "critical";
  if (flowRate < 10.0) return "warning";
  return "normal";
}

// ============================================================
// LEAK DETECTION — sudden drop of >5 L/min between readings
// ============================================================
bool detectLeak(float current, float previous) {
  return (previous > 5.0f) && (previous - current) > 5.0f;
}

// ============================================================
// UPDATE LEDS AND BUZZER
// ============================================================
void updateIndicators(float f1, float f2, bool anyLeak) {
  bool anyCritical = (f1 < 5.0 || f2 < 5.0);
  bool anyWarning  = (f1 < 10.0 || f2 < 10.0);

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

  float flowRates[2];
  flowRates[0] = currentFlowRates[0];
  flowRates[1] = currentFlowRates[1];

  bool anyLeak = false;

  // Check for leaks
  for (int i = 0; i < 2; i++) {
    leakDetected[i] = detectLeak(flowRates[i], prevFlowRates[i]);
    if (leakDetected[i]) anyLeak = true;
    prevFlowRates[i] = flowRates[i];
  }

  // Update LEDs and buzzer
  updateIndicators(flowRates[0], flowRates[1], anyLeak);

  // Build JSON response
  StaticJsonDocument<512> doc;
  JsonArray zones = doc.createNestedArray("zones");

  String zoneIds[] = {"z1", "z2"};

  for (int i = 0; i < 2; i++) {
    JsonObject zone = zones.createNestedObject();
    zone["id"]        = zoneIds[i];
    zone["name"]      = zoneNames[i];
    zone["flow_rate"] = round(flowRates[i] * 10) / 10.0;
    zone["status"]    = getStatus(flowRates[i]);
    zone["leak"]      = leakDetected[i];
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

  // Output pins
  pinMode(LED_RED,    OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN,  OUTPUT);
  pinMode(BUZZER,     OUTPUT);

  // Flow sensor interrupt pins (INPUT_PULLUP works with YF-S201)
  pinMode(FLOW_SENSOR_1, INPUT_PULLUP);
  pinMode(FLOW_SENSOR_2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_1), onPulse1, RISING);
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_2), onPulse2, RISING);

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

  // Update flow rates once per FLOW_SAMPLE_MS without blocking
  unsigned long now = millis();
  if (now - lastSampleMs >= FLOW_SAMPLE_MS) {
    lastSampleMs = now;
    updateFlowRates();
  }
}