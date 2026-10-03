# Atmospheric & Spectral Audio Synthesiser Lab

> *A hardware-to-software telemetry network that streams invisible environmental chemistry and spectral data into a real-time Python synthesis engine and interactive desktop dashboard.*

---

## Repository Overview

This repository contains two separate microcontroller sensor deployment workflows. Both hardware nodes act as dedicated edge transmitters, polling data at high frequencies and streaming raw packets over USB serial to a unified Python dashboard and FM synthesis engine.

```text
├── ESP32_C12880MA_JukeBox/       # ESP32-driven spectrometer data streamer & pulse engine
└── Teensy_BME680_Phantoms/       # Teensy 3.5 atmospheric data logging & streaming node
```

---

## 🛰️ Node 1: Teensy BME680 Atmospheric Streamer & Logger
`Directory: Teensy_BME680_Phantoms`

This node pairs a **Teensy 3.5** with a **Bosch BME680** sensor to create an offline data-exfiltration and logging pipeline. It features a dual-rate execution model that splits data tasks:

1. **High-Speed Telemetry Pipeline (20Hz):** Every 50ms, the Teensy polls the BME680 and flashes raw, unlabelled comma-separated numbers (`Temp,Hum,Pres,Gas`) out of its USB serial port to feed the Python synth engine with zero lag.
2. **Local SD Storage (Background Layer):** Simultaneously, the Teensy tracks long-term data trends in a local RAM buffer. If it captures an atmospheric shock—such as a sudden pressure drop (>1.5 hPa), gas drop, or humidity spike (>10%)—it automatically forces an immediate flush into high-frequency **Burst Saving Mode** to dump records securely onto its physical micro-SD slot.

### Hardware Connection Reference

| BME680 Pin | Teensy 3.5 Pin | Note |
| :--- | :--- | :--- |
| **VIN** | **3.3V** | System power rail |
| **GND** | **GND** | Shared common ground |
| **SCL** | **Pin 19** | I2C Clock Line |
| **SDA** | **Pin 18** | I2C Data Line |

---

## 🛸 Node 2: ESP32 C12880MA Spectral Streamer
`Directory: ESP32_C12880MA_JukeBox`

This node configures an **ESP32 Dev Module** to handle a **Hamamatsu C12880MA micro-spectrometer**. The microcontroller drives the raw clock and video timing lines of the spectrometer, capturing optical intensity across 288 distinct pixels, and flushes those arrays across USB serial to be sonically interpreted by your computer.

---

## 🎛️ The Central Engine: Python Dash & Synthesis Dashboard
`File: bme680_synth.py`

The core of the sound generation and data visualisation happens entirely on your PC via a custom **Python Dash application**. When you connect a hardware node, the script maps the metrics to an algorithmic soundscape engine:

* **Temperature / Spectral Centroid:** Drives the **Base Carrier Pitch**.
* **Gas Resistance (VOCs):** Maps to **Modulation Depth**. Clean air produces pure sine tones; exhalations or chemical vapours drop the sensor resistance and morph the sound into an aggressive, crunchy FM sci-fi growl.
* **Humidity:** Modifies the **Harmonic Ratio Multiplier**, adding complex, ring-modulated sidebands.
* **Pressure:** Dictates the **Echo Delay Feedback & Timing** through a software delay buffer.

### Python Architecture
* **Multi-Threaded Reading:** A dedicated background thread handles high-speed serial reading, resetting the input buffers continuously to eliminate lag.
* **Bare-Metal Audio Synthesis:** Sound generation runs directly inside a `sounddevice` output block callback using `numpy` math, bypassing heavy external audio production software.
* **Analogue Clipping Emulation:** Uses a `np.tanh` soft-saturation mapping layer to provide a warm analogue-style crunch to the final soundwave output.

---

## Getting Started

### 1. Hardware Initialisation
Flash your Teensy 3.5 or ESP32 with its respective sketch via the Arduino IDE. Once powered, the hardware will immediately begin streaming raw CSV telemetry strings out of its USB port.

### 2. Python Setup & Execution
Instal the required mathematical, audio, and web dashboard libraries on your computer:
```bash
pip install numpy sounddevice plotly dash pyserial
```

Execute the central synthesis application from your terminal:
```bash
python bme680_synth.py
```

### 3. Connection
Open your web browser and go to **`http://127.0.0.1:8050`**. Select your microcontroller's COM port from the dropdown list, hit **Connect & Stream Node**, and switch the toggle to **Audio ON** to start the sonification.

---

## License
Distributed under the Apache-2.0 License.


