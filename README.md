# Spectral Ghosts 👻🌫️

> *A decentralized swarm of privacy-preserving architectural nodes that translate invisible atmospheric decay and human breath into living, ambient soundscapes.*

---

## Manifesto

Modern smart buildings are designed for hyper-surveillance. They rely on cameras, cloud tracking, and binary triggers to log human presence, treating occupants as data points to be optimized. 

**Spectral Ghosts** rejects this paradigm. 

Instead of tracking *who* you are, this device listens to *how a space changes* when you inhabit it. Using a BME688 environmental sensor to monitor volatile organic compounds (VOCs), humidity, and metabolic gas shifts, running local **TinyML** inference on-metal, and refusing to connect to the cloud, these autonomous nodes give architecture a subconscious. They capture the ghost of human habitation—and let it decay gracefully over time.

---

## Core Features

* **Absolute Privacy by Design:** Built on the Bosch BME688 sensor. It reads atmospheric chemistry and chemical footprints without ever capturing a video frame, an audio recording, or a personal identifier.
* **Edge TinyML Inference:** No cloud servers, no Wi-Fi telemetry. Local machine learning models running directly on the ESP32 classify environmental states (Empty, Occupied, Fading).
* **Digital Patina & Logarithmic Decay:** Absence is not a binary switch. When a human leaves, the audio engine mirrors human psychology—using an organic, logarithmic decay curve to let the room's memory slowly dissolve back into silence.
* **Granular Ambient Sonification:** Translates atmospheric shifts into living, breathing drone soundscapes via an I2S digital amplifier.
* **Distributed Swarm Architecture:** Deployable as isolated nodes or connected via local peer-to-peer mesh to let adjacent rooms "feel" each other's atmospheric changes.

---

## Hardware Bill of Materials (BOM)

| Component | Role |
| :--- | :--- |
| **ESP32 Dev Module** | The central computing core and TinyML runner. |
| **Bosch BME688** | 4-in-1 environmental sensor (Temperature, Pressure, Humidity, VOC Gas Resistance). |
| **MAX98357A** | I2S Digital Amplifier for clean, real-time audio synthesis. |
| **64x128 OLED Display** | Minimalist, abstract visualization of atmospheric energy and state. |
| **Micro SD Card Module** | Local data-archaeology storage (logging spatial history). |
| **4Ω–8Ω Speaker (3W)** | The physical voice of the room. |

---

## Wiring Reference

| Component | Signal / Pin | ESP32 GPIO Pin |
| :--- | :--- | :--- |
| **BME688 (Environmental)** | SDA | Default I2C (`GPIO 21`) |
| | SCL | Default I2C (`GPIO 22`) |
| **MAX98357A (Audio)** | DIN (Data) | `GPIO 2` |
| | BCLK (Clock) | `GPIO 4` |
| | LRC (Word Select) | `GPIO 15` |
| **OLED Display** | SCL / SDA | Shared I2C (`GPIO 22` / `21`) |
| **Micro SD Card** | SPI Bus | MOSI (`23`), MISO (`19`), SCK (`18`), CS (`5`) |

---

## The Sound Architecture: The Haunting Loop

The device operates across three distinct emotional acoustic states driven by local atmospheric variance:

1. **The Equilibrium (Empty Room):** A deep, slow, sub-bass drone representing a space at rest.
2. **The Intrusion (Presence):** Metabolic VOC shifts and gas resistance drops trigger brighter harmonics and granular textures as the room "notices" human disturbance.
3. **The Residue (Departure):** A long, asymptotic logarithmic decay curve that slowly downshifts pitch and fades into an echoing reverb tail—simulating architectural grief.

---

## Getting Started

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/spectral-ghosts.git](https://github.com/your-username/spectral-ghosts.git)
