#include <TimeLib.h>
#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

// --- Pin Definitions ---
const int LED_PIN = 13;               // Onboard LED (flashes during SD writes)
const int SD_CS_PIN = BUILTIN_SDCARD; // Built-in micro-SD slot on Teensy 3.5

// --- BME680 Object ---
Adafruit_BME680 bme;

// --- Data Log Structure & RAM Buffer ---
struct LogEntry {
  time_t timestamp;
  float temperature;
  float humidity;
  float pressure;
  float gasResistance; // Logged locally on SD card as kOhms
  bool isEvent;
};

const int BUFFER_SIZE = 20;           // Holds records in RAM before flushing
LogEntry logBuffer[BUFFER_SIZE];
int bufferCount = 0;

unsigned long lastFlushTime = 0;
const unsigned long FLUSH_INTERVAL = 600000; // 10 minutes in milliseconds

// --- Sampling Intervals & Burst Mode Configuration ---
const unsigned long BASELINE_INTERVAL = 15000; // 15 seconds normal rate
const unsigned long BURST_INTERVAL = 2000;     // 2 seconds high-frequency rate during events
const unsigned long BURST_DURATION = 30000;    // Stay in burst mode for 30 seconds after an event

unsigned long currentSampleInterval = BASELINE_INTERVAL;
unsigned long burstStartTime = 0;
bool inBurstMode = false;

// Event tracking baselines
float baselinePressure = 0;
float lastHumidity = 0;
bool pressureInitialized = false;

// --- Function Prototypes ---
void printDateTime(Print &out, time_t t);
void flushBufferToSD();
time_t getTeensy3Time();

void setup() {
  // Open serial channel at the high speed required by your Python parser
  Serial.begin(115200);
  
  // Flash status lights to signal setup starting
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);

  // Initialize SD Card
  if (SD.begin(SD_CS_PIN)) {
    // Create CSV header if file doesn't already exist
    if (!SD.exists("datalog.csv")) {
      File dataFile = SD.open("datalog.csv", FILE_WRITE);
      if (dataFile) {
        dataFile.println("DateTime,Temp_C,Humidity_%,Pressure_hPa,Gas_KOhms,Event");
        dataFile.close();
      }
    }
  }

  // Initialize BME680 Sensor (Attempts standard I2C addresses)
  if (bme.begin(0x76) || bme.begin(0x77)) {
    // Oversampling optimized to give low-latency reads for continuous audio curves
    bme.setTemperatureOversampling(BME680_OS_2X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
    bme.setGasHeater(320, 100); // Efficient heating parameters for 20Hz stability
  }

  // Sync internal hardware RTC time
  setSyncProvider(getTeensy3Time);
  
  lastFlushTime = millis();
}

void loop() {
  // 1. Handle Burst Mode Expiration Timer
  if (inBurstMode && (millis() - burstStartTime >= BURST_DURATION)) {
    inBurstMode = false;
    currentSampleInterval = BASELINE_INTERVAL;
    
    // Flush any remaining data to SD when returning to baseline
    flushBufferToSD();
  }

  // 2. High-Speed Serial Pipeline for Python Sound Engine (20Hz / Every 50ms)
  static unsigned long lastSerialStreamTime = 0;
  if (millis() - lastSerialStreamTime >= 50) { 
    lastSerialStreamTime = millis();
    
    if (bme.performReading()) {
      // Outputs pure raw string format: Temp,Hum,Pres,Gas
      Serial.print(bme.temperature);     
      Serial.print(",");
      Serial.print(bme.humidity);        
      Serial.print(",");
      Serial.print(bme.pressure / 100.0); // Convert Pa to hPa matching Python logic
      Serial.print(",");
      Serial.println(bme.gas_resistance); // Raw Ohms (Ω) required for dynamic FM crunch mapping
    }
  }

  // 3. Local Micro-SD Card Logging & Buffered Event Logic (Background Layer)
  static unsigned long lastSampleTime = 0;
  if (millis() - lastSampleTime >= currentSampleInterval) {
    lastSampleTime = millis();

    float temp = bme.temperature;
    float hum = bme.humidity;
    float pres = bme.pressure / 100.0;
    float gas_kohm = bme.gas_resistance / 1000.0; // Scaled to kOhms purely for clean SD file sizes
    time_t currentTime = now();

    // Event Detection Logic
    bool eventDetected = false;
    if (!pressureInitialized) {
      baselinePressure = pres;
      lastHumidity = hum;
      pressureInitialized = true;
    } else {
      // Internal triggers check sharp jumps
      if ((baselinePressure - pres > 1.5) || (gas_kohm < 12.0) || (hum - lastHumidity > 10.0)) {
        eventDetected = true;
      }
      baselinePressure = (baselinePressure * 0.98) + (pres * 0.02); // Rolling baseline tracking
    }
    lastHumidity = hum; 

    // Handle initial transition to high-speed burst saving upon sensor shock
    bool freshEvent = false;
    if (eventDetected && !inBurstMode) {
      inBurstMode = true;
      burstStartTime = millis();
      currentSampleInterval = BURST_INTERVAL;
      freshEvent = true; 
    }

    // Push new matrix record into local RAM buffer array
    logBuffer[bufferCount] = {currentTime, temp, hum, pres, gas_kohm, eventDetected};
    bufferCount++;

    // Flush to SD card if buffer limits, timeouts, or fresh shock events occur
    if (bufferCount >= BUFFER_SIZE || freshEvent || (millis() - lastFlushTime >= FLUSH_INTERVAL)) {
      flushBufferToSD();
    }
  }
}

// --- Helper Functions ---

// Universal DateTime Formatter for SD Card Row Entries
void printDateTime(Print &out, time_t t) {
  out.print(year(t)); out.print(F("-"));
  if (month(t) < 10) out.print('0');
  out.print(month(t)); out.print(F("-"));
  if (day(t) < 10) out.print('0');
  out.print(day(t)); out.print(F(" "));
  if (hour(t) < 10) out.print('0');
  out.print(hour(t)); out.print(F(":"));
  if (minute(t) < 10) out.print('0');
  out.print(minute(t)); out.print(F(":"));
  if (second(t) < 10) out.print('0');
  out.print(second(t));
}

// Writes current RAM buffer block to physical micro-SD slot
void flushBufferToSD() {
  if (bufferCount == 0) return;

  // Visual Confirmation: Blink internal LED 3 times quickly during physical write
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(30);
    digitalWrite(LED_PIN, LOW);
    delay(30);
  }

  File dataFile = SD.open("datalog.csv", FILE_WRITE);
  if (dataFile) {
    for (int i = 0; i < bufferCount; i++) {
      printDateTime(dataFile, logBuffer[i].timestamp);
      dataFile.print(F(","));
      dataFile.print(logBuffer[i].temperature); dataFile.print(",");
      dataFile.print(logBuffer[i].humidity); dataFile.print(",");
      dataFile.print(logBuffer[i].pressure); dataFile.print(",");
      dataFile.print(logBuffer[i].gasResistance); dataFile.print(",");
      dataFile.println(logBuffer[i].isEvent ? "1" : "0");
    }
    dataFile.close();
  }

  // Clear indexing limits and restart interval clock
  bufferCount = 0;
  lastFlushTime = millis();
}

// Pulls internal timestamp value from the Teensy 3.5 hardware clock registers
time_t getTeensy3Time() {
  return Teensy3Clock.get();
}


