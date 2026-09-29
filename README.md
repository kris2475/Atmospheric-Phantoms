# Atmospheric Phantoms

> *A decentralised swarm of privacy-preserving architectural nodes that translate invisible atmospheric decay and human breath into living, ambient soundscapes.*

---

## Manifesto

Modern smart buildings are designed for hyper-surveillance. They rely on intrusive cameras, cloud tracking, and binary triggers to log human presence, treating human occupants merely as data points to be optimised and monetised. 


Every smart device in your home is watching you, listening to you, and streaming your life to the cloud. We built the opposite. Atmospheric Phantoms is an edge-AI node that listens to the chemical footprint of your breath and translates it into a living, breathing soundscape—completely offline. It trades the false comfort of corporate surveillance for ambient, privacy-first poetry. Why do we willingly hand over our lives to tech monopolies, yet find it unnerving when a room simply acknowledges that we were there?

**Atmospheric Phantoms** fundamentally rejects this paradigm. 

Instead of tracking *who* you are, this device listens to *how a space changes* when you inhabit it. Using a Bosch BME688 environmental sensor to monitor volatile organic compounds (VOCs), relative humidity, and metabolic gas shifts, running local **TinyML** inference directly on the metal, and strictly refusing to connect to the cloud, these autonomous nodes give architecture a subconscious. They capture the ghost of human habitation - and let it decay gracefully over time.

---

## The Aesthetics of Honesty: Embracing the Creep
Most commercial IoT devices are aggressively, artificially non-threatening. They wear a mask of cheerful corporate utility—glowing polite blue, chirping happy startup jingles, and pretending to be harmless while quietly harvesting your data to remote cloud servers. They lie about what they are.

**Atmospheric Phantoms** refuses this polite deception. It is intentionally, unapologetically uncanny. 

By using raw environmental decay and shifting drone audio to reflect human absence, it taps into the psychological weight of *hauntology* - the feeling that a space remembers us. It uses speculative unease as a critical probe to ask a vital question: *Why do we find a room reflecting our own invisible biological trace to be unnerving, yet we willingly hand over 24/7 video and audio feeds to corporate tech monopolies without a second thought?* It trades the false comfort of surveillance capitalism for eerie, transparent honesty.

---

## Core Features

* **Absolute Privacy by Design:** Built on the Bosch BME688 sensor. It reads atmospheric chemistry and chemical footprints without ever capturing a video frame, an audio recording, or any personal identifier.
* **Edge TinyML Inference:** No cloud servers, no Wi-Fi telemetry, and no external data dependencies. Local machine learning models running directly on the ESP32 classify environmental states (Empty, Occupied, Fading) in real-time.
* **Digital Patina & Logarithmic Decay:** Absence is never a binary switch. When a human leaves a room, the audio engine mirrors human psychology - using an organic, logarithmic decay curve to let the room's memory slowly and naturally dissolve back into silence.
* **Granular Ambient Sonification:** Translates subtle atmospheric shifts into living, breathing drone soundscapes via an I2S digital amplifier.
* **Distributed Swarm Architecture:** Fully deployable as isolated nodes or connected via a local peer-to-peer wireless mesh, allowing adjacent rooms to harmonise and "feel" each other's atmospheric fluctuations.

---

## Physical Materiality: Porous Enclosures
A device that tracks decay cannot be housed in pristine injection-molded white plastic. **Atmospheric Phantoms** are designed for porous, raw, and weathering materials - such as unglassed terracotta, charred *Shou Sugi Ban* wood, or raw cast concrete. As the system ages and logs spatial history, the enclosure itself absorbs environmental moisture, patinates, and weathers, ensuring the hardware physically reflects the passage of time just as the audio engine does.

---

## Inter-Node Empathy (The Swarm's Whisper)
Nodes do not exist in isolation. Utilising local **ESP-NOW** peer-to-peer mesh networking, adjacent rooms can sense each other's atmospheric shifts completely offline. When a bedroom node detects a human waking up and shifting the air, it silently transmits a lightweight packet to the hallway node, causing the hallway node to pre-emptively shift its drone chord. The building begins to breathe in sync before you even walk through the door.

---

## The Architecture of Forgetting (Digital Bit-Rot)
Unlike security loops that cleanly overwrite old files or cloud services that store everything indefinitely, the Micro SD card architecture features a built-in **death cycle**. Memories and archival audio loops older than a defined window do not simply delete—they undergo algorithmic bit-rot, permanently fragmenting, distorting, and dissolving into digital white noise. The machine actively chooses to forget, honoring the true ephemerality of human life.

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

## Deployment Scenarios

Because each node runs its own local TinyML model and memory architecture, **Atmospheric Phantoms** adapts entirely to the local rhythm of its surroundings:

* **The Solitary Flat (Home & Loneliness):** Sits in deep equilibrium during the day. When you return home, your metabolic footprint warms the soundscape. When you leave for extended periods, the node dips into its SD card memory ring-buffer, softly whispering stretched-out audio echoes of your daily routine.
* **The Corporate Office or Care Home (Nightshift Transition):** Transforms a frantic, high-tension workspace during the day into a dramatic logarithmic decay at midnight. Nightshift workers walking past quiet meeting rooms at 4:00 AM can hear the building literally exhaling the day's stress.

---

Apache-2.0 licence
