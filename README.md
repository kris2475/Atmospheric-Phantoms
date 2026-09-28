# Atmospheric Phantoms

> *A decentralised swarm of privacy-preserving architectural nodes that translate invisible atmospheric decay and human breath into living, ambient soundscapes.*

---

## Manifesto

Modern smart buildings are designed for hyper-surveillance. They rely on intrusive cameras, cloud tracking, and binary triggers to log human presence, treating human occupants merely as data points to be optimised and monetised. 

**Spectral Ghosts** fundamentally rejects this paradigm. 

Instead of tracking *who* you are, this device listens to *how a space changes* when you inhabit it. Using a Bosch BME688 environmental sensor to monitor volatile organic compounds (VOCs), relative humidity, and metabolic gas shifts, running local **TinyML** inference directly on the metal, and strictly refusing to connect to the cloud, these autonomous nodes give architecture a subconscious. They capture the ghost of human habitation—and let it decay gracefully over time.

---

## Core Features

* **Absolute Privacy by Design:** Built on the Bosch BME688 sensor. It reads atmospheric chemistry and chemical footprints without ever capturing a video frame, an audio recording, or any personal identifier.
* **Edge TinyML Inference:** No cloud servers, no Wi-Fi telemetry, and no external data dependencies. Local machine learning models running directly on the ESP32 classify environmental states (Empty, Occupied, Fading) in real-time.
* **Digital Patina & Logarithmic Decay:** Absence is never a binary switch. When a human leaves a room, the audio engine mirrors human psychology - using an organic, logarithmic decay curve to let the room's memory slowly and naturally dissolve back into silence.
* **Granular Ambient Sonification:** Translates subtle atmospheric shifts into living, breathing drone soundscapes via an I2S digital amplifier.
* **Distributed Swarm Architecture:** Fully deployable as isolated nodes or connected via a local peer-to-peer wireless mesh, allowing adjacent rooms to harmonise and "feel" each other's atmospheric fluctuations.

---

## Hardware Bill of Materials (BOM)

| Component | Role & Function |
| :--- | :--- |
| **ESP32 Dev Module** | The central computing core, handling sensor polling, TinyML inference, and audio synthesis. |
| **Bosch BME688** | 4-in-1 environmental sensor measuring ambient temperature, barometric pressure, relative humidity, and VOC gas resistance. |
| **MAX98357A** | I2S Digital Amplifier providing clean, distortion-free real-time audio output directly to the speaker. |
| **64x128 OLED Display** | Minimalist, abstract visualisation of atmospheric energy levels, system state, and historical trends. |
| **Micro SD Card Module** | Local data-archaeology storage for logging long-term spatial history and temporal patterns. |
| **4Ω–8Ω Speaker (3W)** | The physical voice and acoustic transducer of the room. |

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

1. **The Equilibrium (Empty Room):** A deep, slow, resonant sub-bass drone representing a space at rest, tuned to match the natural ambient hum of the building infrastructure.
2. **The Intrusion (Presence):** Metabolic VOC shifts and sharp gas resistance drops trigger brighter harmonics, shimmering overtones, and granular textures as the room "notices" human disturbance.
3. **The Residue (Departure):** A long, asymptotic logarithmic decay curve that slowly downshifts pitch and fades into an echoing reverb tail—simulating architectural grief and the slow fading of human presence.

---

Apache-2.0 license
