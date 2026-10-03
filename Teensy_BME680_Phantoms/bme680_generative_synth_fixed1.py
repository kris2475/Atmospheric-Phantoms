import threading
import time

import numpy as np
import serial
import serial.tools.list_ports
import sounddevice as sd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, ctx, no_update


# ============================================================
# Shared state
# ============================================================

ser = None
lock = threading.RLock()

latest_data = {
    "temperature": 25.0,
    "humidity": 40.0,
    "pressure": 1013.25,
    "gas_resistance": 50000.0,
    "device_msg": "System ready",
}

audio_settings = {
    "enabled": False,
    "genre": "ambient",
    "volume": 0.25,
    "min_freq": 65.41,
    "max_freq": 523.25,
}

SAMPLE_RATE = 44100
BLOCK_SIZE = 512

phase_1 = 0.0
phase_2 = 0.0
phase_sub = 0.0
lfo_phase = 0.0
vibrato_phase = 0.0
pulse_phase = 0.0
current_amp = 0.0
current_freq = 220.0


# ============================================================
# Serial port
# ============================================================

def get_ports():
    try:
        return [
            {
                "label": f"{p.device} - {p.description}",
                "value": p.device,
            }
            for p in serial.tools.list_ports.comports()
        ]
    except Exception:
        return []


def serial_reader():
    global ser

    while True:
        with lock:
            port = ser

        if port is None:
            time.sleep(0.2)
            continue

        try:
            if not port.is_open:
                time.sleep(0.2)
                continue

            raw = port.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="ignore").strip()

            if not line or line.startswith("["):
                continue

            parts = line.split(",")

            if len(parts) != 4:
                continue

            values = [float(x.strip()) for x in parts]

            if not all(np.isfinite(x) for x in values):
                continue

            with lock:
                if ser is port:
                    latest_data["temperature"] = values[0]
                    latest_data["humidity"] = values[1]
                    latest_data["pressure"] = values[2]
                    latest_data["gas_resistance"] = values[3]
                    latest_data["device_msg"] = "Receiving telemetry"

        except (ValueError, serial.SerialException, OSError) as exc:
            with lock:
                latest_data["device_msg"] = f"Serial error: {exc}"
            time.sleep(0.2)

        except Exception as exc:
            with lock:
                latest_data["device_msg"] = f"Reader error: {exc}"
            time.sleep(0.2)


threading.Thread(target=serial_reader, daemon=True).start()


# ============================================================
# 100% Crackle-Free Lifelike Audio Callback
# ============================================================

def audio_callback(outdata, frames, time_info, status):
    global phase_1, phase_2, phase_sub, lfo_phase, vibrato_phase, pulse_phase, current_amp, current_freq

    with lock:
        enabled = audio_settings["enabled"]
        genre = audio_settings["genre"]
        volume = audio_settings["volume"]
        min_freq = audio_settings["min_freq"]
        max_freq = audio_settings["max_freq"]

        temp = latest_data["temperature"]
        humidity = latest_data["humidity"]
        pressure = latest_data["pressure"]
        gas = latest_data["gas_resistance"]

    if not enabled:
        outdata.fill(0)
        return

    # --- TPHG MAPPINGS ---
    target_base_freq = float(np.interp(temp, [10, 40], [min_freq, max_freq]))
    
    vib_depth = float(np.interp(pressure, [980, 1030], [0.0, 12.0]))
    vib_rate = 3.0 + float(np.interp(pressure, [980, 1030], [0.0, 3.0]))

    h_mix = float(np.clip(humidity / 100.0, 0.0, 1.0))
    g_mix = float(np.clip((gas - 5000) / 150000.0, 0.0, 1.0))

    current_amp += (volume - current_amp) * 0.05

    # Smooth frequency gliding across the block
    target_freq_array = np.linspace(current_freq, target_base_freq, frames, endpoint=True)
    current_freq = target_base_freq

    t = np.arange(frames, dtype=np.float32) / SAMPLE_RATE

    # Continuous vibrato phase
    vibrato = vib_depth * np.sin(vibrato_phase + 2 * np.pi * vib_rate * t)
    vibrato_phase = (vibrato_phase + 2 * np.pi * vib_rate * frames / SAMPLE_RATE) % (2 * np.pi)
    base_freqs = np.maximum(20.0, target_freq_array + vibrato)

    # Continuous LFO for organic modulation
    mod_rate = 0.5 + (g_mix * 3.0)
    lfo_inc = 2 * np.pi * mod_rate / SAMPLE_RATE
    lfo_arr = lfo_phase + np.cumsum(np.full(frames, lfo_inc, dtype=np.float32))
    lfo_phase = lfo_arr[-1] % (2 * np.pi)
    mod = np.sin(lfo_arr)

    # --- GENRE FREQUENCY ROUTING ---
    if genre == "ambient":
        f1 = base_freqs
        f2 = base_freqs * 1.5
        f_sub = base_freqs * 0.5
    elif genre == "forest":
        # Sweeping wind harmonics driven smoothly by humidity and temperature
        f1 = base_freqs * (1.0 + mod * 0.2)
        f2 = base_freqs * (1.5 + h_mix * 0.5)
        f_sub = base_freqs * 0.5
    elif genre == "ocean":
        # Tidal swelling motion
        f1 = base_freqs * 0.75
        f2 = base_freqs * 1.25
        f_sub = base_freqs * 0.375
    elif genre == "biopulse":
        # Organic biological rhythmic breathing
        f1 = base_freqs
        f2 = base_freqs * 2.0
        f_sub = base_freqs * 0.5
    elif genre == "scifi":
        f1 = base_freqs * (1.0 + mod * 0.15)
        f2 = base_freqs * 2.0
        f_sub = base_freqs * 0.5
    elif genre == "drone":
        f1 = base_freqs
        f2 = base_freqs * 0.5
        f_sub = base_freqs * 0.25
    else:  # cyberpunk
        f1 = base_freqs
        f2 = base_freqs * 2.0
        f_sub = base_freqs * 1.5

    # True continuous sample-accurate phase integration
    inc1 = 2 * np.pi * f1 / SAMPLE_RATE
    inc2 = 2 * np.pi * f2 / SAMPLE_RATE
    inc_sub = 2 * np.pi * f_sub / SAMPLE_RATE

    p1_arr = phase_1 + np.cumsum(inc1)
    p2_arr = phase_2 + np.cumsum(inc2)
    ps_arr = phase_sub + np.cumsum(inc_sub)

    phase_1 = p1_arr[-1] % (2 * np.pi)
    phase_2 = p2_arr[-1] % (2 * np.pi)
    phase_sub = ps_arr[-1] % (2 * np.pi)

    # --- GENRE SYNTHESIS MIXING (Lifelike & Organic) ---
    s1 = np.sin(p1_arr)
    s2 = np.sin(p2_arr)
    s3 = np.sin(ps_arr)

    if genre == "ambient":
        signal = (s1 * 0.5 + s2 * (0.3 * h_mix) + s3 * (0.4 * g_mix)) * current_amp

    elif genre == "forest":
        # Whispering wind simulated purely with smooth harmonic sine layers (zero harsh white-noise hiss)
        wind_swell = 0.5 + 0.5 * np.sin(lfo_arr * 0.5)
        signal = (s1 * (0.4 * wind_swell) + s2 * (0.3 * h_mix) + s3 * (0.3 * g_mix)) * current_amp

    elif genre == "ocean":
        # Gentle rolling wave swell driven by barometric pressure & humidity
        tide_rate = 0.2 + (h_mix * 0.3)
        pulse_inc = 2 * np.pi * tide_rate / SAMPLE_RATE
        pulse_arr = pulse_phase + np.cumsum(np.full(frames, pulse_inc, dtype=np.float32))
        pulse_phase = pulse_arr[-1] % (2 * np.pi)
        tide = 0.2 + 0.8 * np.abs(np.sin(pulse_arr))
        signal = (s1 * 0.5 * tide + s2 * 0.3 * tide + s3 * (0.4 * g_mix)) * current_amp

    elif genre == "biopulse":
        # Rhythmic living organism pulse
        heart_rate = 1.0 + (g_mix * 3.0)
        pulse_inc = 2 * np.pi * heart_rate / SAMPLE_RATE
        pulse_arr = pulse_phase + np.cumsum(np.full(frames, pulse_inc, dtype=np.float32))
        pulse_phase = pulse_arr[-1] % (2 * np.pi)
        envelope = np.power(np.abs(np.sin(pulse_arr)), 3.0)
        signal = (s1 * 0.5 + s2 * (0.4 * h_mix)) * envelope * current_amp

    elif genre == "scifi":
        signal = (s1 * 0.6 + s2 * (0.3 * h_mix)) * current_amp

    elif genre == "drone":
        signal = (s1 * 0.3 + s2 * (0.4 + 0.3 * g_mix) + s3 * (0.3 * h_mix)) * current_amp

    else:  # cyberpunk
        signal = (s1 * 0.4 + s2 * (0.3 * h_mix) + s3 * (0.2 * g_mix)) * current_amp

    # Master soft limiter
    outdata[:, 0] = np.tanh(signal)


# ============================================================
# Start audio safely
# ============================================================

audio_stream = None

try:
    audio_stream = sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback,
        blocksize=BLOCK_SIZE,
        dtype="float32",
    )
    audio_stream.start()
    audio_error = ""

except Exception as exc:
    audio_error = str(exc)
    print("Audio device error:", audio_error)


# ============================================================
# Dash application
# ============================================================

app = Dash(__name__)
app.title = "BME680 Generative Synth"

PANEL = {
    "backgroundColor": "#1e293b",
    "padding": "20px",
    "borderRadius": "10px",
    "marginBottom": "20px",
}

BUTTON = {
    "color": "white",
    "padding": "10px 20px",
    "border": "none",
    "borderRadius": "6px",
    "cursor": "pointer",
    "fontWeight": "bold",
}

GENRE_BUTTON = {
    "color": "white",
    "padding": "12px 20px",
    "border": "none",
    "borderRadius": "6px",
    "cursor": "pointer",
}


app.layout = html.Div(
    style={
        "backgroundColor": "#0b0f19",
        "color": "#f3f4f6",
        "padding": "25px",
        "fontFamily": "Arial, sans-serif",
        "minHeight": "100vh",
    },
    children=[

        html.H1(
            "BME680 Multi-Parameter Generative Synth",
            style={
                "textAlign": "center",
                "color": "#10b981",
            },
        ),

        html.Div(
            style={
                **PANEL,
                "display": "flex",
                "gap": "12px",
                "alignItems": "center",
                "flexWrap": "wrap",
            },
            children=[
                dcc.Dropdown(
                    id="port-dropdown",
                    options=get_ports(),
                    placeholder="Select serial port",
                    style={"width": "320px", "color": "#000"},
                ),

                html.Button(
                    "Refresh Ports",
                    id="btn-refresh-ports",
                    n_clicks=0,
                    style={
                        **BUTTON,
                        "backgroundColor": "#475569",
                    },
                ),

                html.Button(
                    "Connect & Stream",
                    id="btn-connect",
                    n_clicks=0,
                    style={
                        **BUTTON,
                        "backgroundColor": "#10b981",
                    },
                ),

                html.Div(
                    id="connection-status",
                    children="Status: Offline",
                ),
            ],
        ),

        html.Div(
            style=PANEL,
            children=[
                html.H3(
                    "Soundscape Genre Selection",
                    style={"color": "#10b981"},
                ),

                html.Div(
                    style={
                        "display": "flex",
                        "gap": "12px",
                        "flexWrap": "wrap",
                    },
                    children=[
                        html.Button(
                            "Ethereal Ambient",
                            id="btn-genre-ambient",
                            n_clicks=0,
                            style={
                                **GENRE_BUTTON,
                                "backgroundColor": "#10b981",
                            },
                        ),

                        html.Button(
                            "Whispering Forest",
                            id="btn-genre-forest",
                            n_clicks=0,
                            style={
                                **GENRE_BUTTON,
                                "backgroundColor": "#334155",
                            },
                        ),

                        html.Button(
                            "Ocean Tides",
                            id="btn-genre-ocean",
                            n_clicks=0,
                            style={
                                **GENRE_BUTTON,
                                "backgroundColor": "#334155",
                            },
                        ),

                        html.Button(
                            "Bio-Pulse Organism",
                            id="btn-genre-biopulse",
                            n_clicks=0,
                            style={
                                **GENRE_BUTTON,
                                "backgroundColor": "#334155",
                            },
                        ),

                        html.Button(
                            "Sci-Fi Radar",
                            id="btn-genre-scifi",
                            n_clicks=0,
                            style={
                                **GENRE_BUTTON,
                                "backgroundColor": "#334155",
                            },
                        ),

                        html.Button(
                            "Deep Space Drone",
                            id="btn-genre-drone",
                            n_clicks=0,
                            style={
                                **GENRE_BUTTON,
                                "backgroundColor": "#334155",
                            },
                        ),

                        html.Button(
                            "Cyberpunk Terminal",
                            id="btn-genre-cyberpunk",
                            n_clicks=0,
                            style={
                                **GENRE_BUTTON,
                                "backgroundColor": "#334155",
                            },
                        ),
                    ],
                ),
            ],
        ),

        html.Div(
            style=PANEL,
            children=[
                html.H3(
                    "Audio Engine Controls",
                    style={"color": "#10b981"},
                ),

                html.Button(
                    "Audio OFF",
                    id="btn-toggle-audio",
                    n_clicks=0,
                    style={
                        **BUTTON,
                        "backgroundColor": "#ef4444",
                    },
                ),

                html.Div(
                    "Master Volume",
                    style={"marginTop": "20px"},
                ),

                dcc.Slider(
                    id="slider-volume",
                    min=0.01,
                    max=0.5,
                    step=0.01,
                    value=0.25,
                    marks={
                        0.01: "0.01",
                        0.25: "0.25",
                        0.5: "0.50",
                    },
                ),

                html.Div(
                    id="audio-device-status",
                    children=(
                        f"Audio error: {audio_error}"
                        if audio_error
                        else "Audio output ready"
                    ),
                    style={
                        "color": "#94a3b8",
                        "marginTop": "12px",
                    },
                ),
            ],
        ),

        html.Div(
            id="telemetry-readouts",
            style={
                "display": "flex",
                "gap": "15px",
                "flexWrap": "wrap",
                "marginBottom": "20px",
            },
        ),

        dcc.Graph(
            id="live-atmospheric-history",
            style={"height": "380px"},
            config={"displayModeBar": False},
        ),

        html.Div(
            id="device-message",
            children="System ready",
            style={"color": "#94a3b8"},
        ),

        dcc.Interval(
            id="graph-update-interval",
            interval=500,
            n_intervals=0,
        ),
    ],
)


# ============================================================
# Callbacks
# ============================================================

@app.callback(
    Output("port-dropdown", "options"),
    Input("btn-refresh-ports", "n_clicks"),
    prevent_initial_call=True,
)
def refresh_ports(_clicks):
    return get_ports()


@app.callback(
    Output("connection-status", "children"),
    Input("btn-connect", "n_clicks"),
    State("port-dropdown", "value"),
    prevent_initial_call=True,
)
def connect_port(_clicks, selected_port):
    global ser

    if not selected_port:
        return "Select a valid COM port."

    try:
        new_port = serial.Serial(
            selected_port,
            115200,
            timeout=0.5,
        )

        with lock:
            old_port = ser
            ser = new_port
            latest_data["device_msg"] = (
                f"Connected to {selected_port}"
            )

        if old_port is not None:
            try:
                old_port.close()
            except Exception:
                pass

        return f"Connected: {selected_port}"

    except Exception as exc:
        return f"Connection error: {exc}"


@app.callback(
    Output("btn-toggle-audio", "children"),
    Output("btn-toggle-audio", "style"),
    Input("btn-toggle-audio", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_audio(_clicks):
    with lock:
        audio_settings["enabled"] = not audio_settings["enabled"]
        enabled = audio_settings["enabled"]

    if enabled:
        return (
            "Audio ON",
            {**BUTTON, "backgroundColor": "#10b981"},
        )

    return (
        "Audio OFF",
        {**BUTTON, "backgroundColor": "#ef4444"},
    )


@app.callback(
    Output("btn-genre-ambient", "style"),
    Output("btn-genre-forest", "style"),
    Output("btn-genre-ocean", "style"),
    Output("btn-genre-biopulse", "style"),
    Output("btn-genre-scifi", "style"),
    Output("btn-genre-drone", "style"),
    Output("btn-genre-cyberpunk", "style"),
    Input("btn-genre-ambient", "n_clicks"),
    Input("btn-genre-forest", "n_clicks"),
    Input("btn-genre-ocean", "n_clicks"),
    Input("btn-genre-biopulse", "n_clicks"),
    Input("btn-genre-scifi", "n_clicks"),
    Input("btn-genre-drone", "n_clicks"),
    Input("btn-genre-cyberpunk", "n_clicks"),
    prevent_initial_call=True,
)
def select_genre(_ambient, _forest, _ocean, _biopulse, _scifi, _drone, _cyberpunk):
    button_to_genre = {
        "btn-genre-ambient": "ambient",
        "btn-genre-forest": "forest",
        "btn-genre-ocean": "ocean",
        "btn-genre-biopulse": "biopulse",
        "btn-genre-scifi": "scifi",
        "btn-genre-drone": "drone",
        "btn-genre-cyberpunk": "cyberpunk",
    }

    selected = ctx.triggered_id

    if selected not in button_to_genre:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    with lock:
        audio_settings["genre"] = button_to_genre[selected]

    styles = []

    for button_id in button_to_genre:
        styles.append({
            **GENRE_BUTTON,
            "backgroundColor": (
                "#10b981" if button_id == selected else "#334155"
            ),
        })

    return tuple(styles)


def make_card(title, value, accent):
    return html.Div(
        style={
            "backgroundColor": "#1e293b",
            "padding": "15px",
            "borderRadius": "8px",
            "flex": "1 1 180px",
            "textAlign": "center",
        },
        children=[
            html.Div(
                title,
                style={"color": "#94a3b8"},
            ),
            html.H2(
                value,
                style={"color": accent},
            ),
        ],
    )


@app.callback(
    Output("live-atmospheric-history", "figure"),
    Output("telemetry-readouts", "children"),
    Output("device-message", "children"),
    Input("graph-update-interval", "n_intervals"),
    State("slider-volume", "value"),
)
def update_dashboard(_interval, volume):

    with lock:
        if volume is not None:
            audio_settings["volume"] = float(volume)

        temperature = latest_data["temperature"]
        humidity = latest_data["humidity"]
        pressure = latest_data["pressure"]
        gas = latest_data["gas_resistance"]
        message = latest_data["device_msg"]

    cards = [
        make_card(
            "TEMPERATURE (Pitch)",
            f"{temperature:.1f} °C",
            "#10b981",
        ),
        make_card(
            "HUMIDITY (Shimmer)",
            f"{humidity:.1f} %",
            "#38bdf8",
        ),
        make_card(
            "PRESSURE (Vibrato)",
            f"{pressure:.1f} hPa",
            "#fbbf24",
        ),
        make_card(
            "GAS (Sub-Bass)",
            f"{gas / 1000:.1f} kΩ",
            "#a78bfa",
        ),
    ]

    figure = go.Figure(
        data=[
            go.Bar(
                x=[
                    "Temp (Pitch)",
                    "Humidity (Shimmer)",
                    "Pressure / 10 (Vibrato)",
                    "Gas / 5000 (Sub-Bass)",
                ],
                y=[
                    temperature,
                    humidity,
                    pressure / 10,
                    gas / 5000,
                ],
                marker_color=[
                    "#10b981",
                    "#38bdf8",
                    "#fbbf24",
                    "#a78bfa",
                ],
            )
        ]
    )

    figure.update_layout(
        title="Live T/H/P/G Parameter Mapping",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#0b0f19",
        font={"color": "#f3f4f6"},
        margin={"l": 40, "r": 25, "t": 55, "b": 55},
        yaxis={"gridcolor": "#334155"},
    )

    return figure, cards, message


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    print("Starting dashboard.")
    print("Open http://127.0.0.1:8050")
    print("Running file:", __file__)

    try:
        app.run(
            host="127.0.0.1",
            port=8050,
            debug=False,
        )

    finally:
        with lock:
            active_port = ser
            ser = None

        if active_port is not None:
            try:
                active_port.close()
            except Exception:
                pass

        if audio_stream is not None:
            try:
                audio_stream.stop()
                audio_stream.close()
            except Exception:
                pass
