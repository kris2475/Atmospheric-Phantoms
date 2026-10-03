import threading
import time
import serial
import serial.tools.list_ports
import numpy as np
import sounddevice as sd
import plotly.graph_objs as go
import dash
from dash import Dash, dcc, html, Input, Output, State, callback_context, no_update

# Shared Global State
ser = None
global_lock = threading.Lock()
latest_data = {
    "temperature": 25.0,
    "humidity": 40.0,
    "pressure": 1013.25,
    "gas_resistance": 50000.0,
    "device_msg": "System Ready."
}

# Audio Control Parameters
audio_settings = {
    "enabled": False,
    "genre": "ambient",  # ambient, scifi, drone, cyberpunk
    "volume": 0.25,
    "min_freq": 65.41,   # C2 base
    "max_freq": 523.25   # C5 top
}

def get_available_ports():
    ports = serial.tools.list_ports.comports()
    return [{'label': f"{p.device} - {p.description}", 'value': p.device} for p in ports]

def serial_reader_thread():
    global latest_data, ser
    while True:
        current_ser = None
        with global_lock:
            current_ser = ser
        
        if current_ser and current_ser.is_open:
            try:
                if current_ser.in_waiting > 512:
                    current_ser.reset_input_buffer()

                line = current_ser.readline().decode('utf-8', errors='ignore').strip()
                if not line or line.startswith("["):
                    continue
                
                parts = line.split(',')
                if len(parts) == 4:
                    with global_lock:
                        latest_data["temperature"] = float(parts[0])
                        latest_data["humidity"] = float(parts[1])
                        latest_data["pressure"] = float(parts[2])
                        latest_data["gas_resistance"] = float(parts[3])
            except Exception:
                time.sleep(0.05)
        else:
            time.sleep(0.2)

threading.Thread(target=serial_reader_thread, daemon=True).start()

# --- Multi-Voice Synthesizer Engine ---
SAMPLE_RATE = 44100
BLOCK_SIZE = 512

phase_1 = 0.0
phase_2 = 0.0
mod_phase = 0.0
current_amp = 0.0

DELAY_TIME_SAMPLES = int(SAMPLE_RATE * 0.5)
delay_buffer = np.zeros(DELAY_TIME_SAMPLES, dtype=np.float32)
delay_index = 0

def audio_callback(outdata, frames, time_info, status):
    global phase_1, phase_2, mod_phase, current_amp, delay_buffer, delay_index
    
    with global_lock:
        is_active = audio_settings["enabled"]
        genre = audio_settings["genre"]
        vol = audio_settings["volume"]
        min_f = audio_settings["min_freq"]
        max_f = audio_settings["max_freq"]
        
        # Independent TPHG values
        t_val = latest_data["temperature"]
        h_val = latest_data["humidity"]
        p_val = latest_data["pressure"]
        g_val = latest_data["gas_resistance"]

    if not is_active:
        outdata[:] = np.zeros((frames, 1), dtype=np.float32)
        return

    # --- Independent TPHG Mapping Math ---
    # T (Temperature) -> Tone / Pitch
    target_freq = np.interp(t_val, [10.0, 40.0], [min_f, max_f])
    
    # P (Pressure) -> Echo / Space Feedback (980 hPa to 1030 hPa)
    feedback_coeff = np.interp(p_val, [980.0, 1030.0], [0.1, 0.75])
    
    # H (Humidity) -> Fade / Envelope / Release & Shimmer (0% to 100%)
    hum_normalized = np.clip(h_val / 100.0, 0.0, 1.0)
    fade_rate = 0.01 + (hum_normalized * 0.08)  
    
    # G (Gas) -> Texture / Modulation Depth (Impedance in ohms)
    gas_normalized = np.clip((g_val - 5000.0) / 150000.0, 0.0, 1.0)

    current_amp += (vol - current_amp) * 0.05
    t = np.arange(frames, dtype=np.float32) / SAMPLE_RATE

    # --- Genre Sound Sculpting ---
    if genre == "ambient":
        harmonic_spread = 1.0 + (hum_normalized * 0.02)
        s1 = np.sin(2.0 * np.pi * target_freq * t + phase_1)
        s2 = np.sin(2.0 * np.pi * (target_freq * harmonic_spread) * t + phase_2)
        
        noise = np.random.normal(0, 0.05, frames).astype(np.float32)
        signal = ((s1 * 0.5 + s2 * 0.4) + (noise * gas_normalized)) * current_amp

    elif genre == "scifi":
        mod_rate = 1.0 + (gas_normalized * 5.0)
        mod = np.sin(mod_phase + 2.0 * np.pi * mod_rate * t)
        mod_phase = (mod_phase + 2.0 * np.pi * mod_rate * (frames / SAMPLE_RATE)) % (2.0 * np.pi)
        
        ping_freq = target_freq * (1.0 + mod * 0.1)
        signal = np.sin(2.0 * np.pi * ping_freq * t + phase_1) * np.exp(-fade_rate * 10.0 * (t % 0.5)) * current_amp

    elif genre == "drone":
        sub_freq = target_freq * 0.5
        s1 = np.sin(2.0 * np.pi * sub_freq * t + phase_1)
        s2 = np.sin(2.0 * np.pi * (sub_freq * 1.5) * t + phase_2)
        signal = (s1 * 0.7 + s2 * 0.3) * current_amp

    else:  # cyberpunk
        s1 = np.sign(np.sin(2.0 * np.pi * target_freq * t + phase_1))
        s2 = np.sin(2.0 * np.pi * (target_freq * 2.0) * t + phase_2)
        signal = (s1 * 0.4 + s2 * 0.4) * current_amp * (0.8 + gas_normalized * 0.2)

    if frames > 0:
        phase_1 = (phase_1 + 2.0 * np.pi * target_freq * (frames / SAMPLE_RATE)) % (2.0 * np.pi)
        phase_2 = (phase_2 + 2.0 * np.pi * (target_freq * 1.005) * (frames / SAMPLE_RATE)) % (2.0 * np.pi)

    # --- Pressure-Controlled Echo / Delay Line ---
    output_block = np.zeros(frames, dtype=np.float32)
    for n in range(frames):
        delayed_sample = delay_buffer[delay_index]
        current_sample = signal[n] + (delayed_sample * feedback_coeff)
        
        delay_buffer[delay_index] = current_sample * 0.95  
        delay_index = (delay_index + 1) % DELAY_TIME_SAMPLES
        
        output_block[n] = current_sample

    output_block = np.tanh(output_block)
    outdata[:] = output_block.reshape(-1, 1)

stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback, blocksize=BLOCK_SIZE)
stream.start()

# --- Dash UI Layout ---
app = Dash(__name__)
app.layout = html.Div(style={'backgroundColor': '#0b0f19', 'color': '#f3f4f6', 'padding': '25px', 'fontFamily': 'Inter, sans-serif'}, children=[
    html.H1("🎛️ BME680 Multi-Parameter Generative Synth", style={'textAlign': 'center', 'color': '#10b981', 'fontWeight': '600'}),
    
    # Connection Row
    html.Div(style={'backgroundColor': '#1e293b', 'padding': '15px', 'borderRadius': '10px', 'marginBottom': '20px', 'display': 'flex', 'gap': '15px', 'alignItems': 'center'}, children=[
        dcc.Dropdown(id='port-dropdown', options=get_available_ports(), placeholder="Select Teensy COM Port...", style={'width': '300px', 'color': '#000'}),
        html.Button('Connect & Stream Node', id='btn-connect', n_clicks=0, style={'backgroundColor': '#10b981', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': '600'}),
        html.Div(id='connection-status', children="Status: Offline", style={'color': '#f87171', 'fontWeight': 'bold'})
    ]),

    # Genre Selector Deck
    html.Div(style={'backgroundColor': '#1e293b', 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
        html.H3("🎶 Soundscape Genre Selection", style={'color': '#10b981', 'marginTop': '0', 'fontSize': '1.1rem'}),
        html.Div(style={'display': 'flex', 'gap': '15px', 'flexWrap': 'wrap'}, children=[
            html.Button('🌌 Ethereal Ambient', id='btn-genre-ambient', n_clicks=0, style={'backgroundColor': '#10b981', 'color': 'white', 'padding': '12px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}),
            html.Button('📡 Sci-Fi Radar', id='btn-genre-scifi', n_clicks=0, style={'backgroundColor': '#334155', 'color': 'white', 'padding': '12px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer'}),
            html.Button('🪐 Deep Space Drone', id='btn-genre-drone', n_clicks=0, style={'backgroundColor': '#334155', 'color': 'white', 'padding': '12px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer'}),
            html.Button('⚡ Cyberpunk Terminal', id='btn-genre-cyberpunk', n_clicks=0, style={'backgroundColor': '#334155', 'color': 'white', 'padding': '12px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer'}),
        ])
    ]),

    # Master Controls
    html.Div(style={'backgroundColor': '#1e293b', 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}, children=[
        html.H3("🎛️ Audio Engine Controls", style={'color': '#10b981', 'marginTop': '0', 'fontSize': '1.1rem'}),
        html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap', 'alignItems': 'center'}, children=[
            html.Button('🔇 Toggle Audio OFF', id='btn-toggle-audio', n_clicks=0, style={'backgroundColor': '#ef4444', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}),
            html.Div(style={'display': 'inline-block', 'width': '120px'}, children=[
                html.B("Master Volume:", style={'fontSize': '0.9rem', 'color': '#94a3b8', 'display': 'block'}),
                dcc.Slider(id='slider-volume', min=0.01, max=0.5, step=0.01, value=0.25)
            ])
        ])
    ]),

    # Telemetry and Visualizer
    html.Div(id='telemetry-readouts', style={'display': 'flex', 'gap': '15px', 'justifyContent': 'space-between', 'marginBottom': '20px'}),
    dcc.Graph(id='live-atmospheric-history', style={'height': '350px'}),
    dcc.Interval(id='graph-update-interval', interval=250, n_intervals=0)
])

@app.callback(
    Output('connection-status', 'children'),
    Input('btn-connect', 'n_clicks'),
    State('port-dropdown', 'value'),
    prevent_initial_call=True
)
def connect_port(n_clicks, selected_port):
    global ser
    if not selected_port:
        return "Select valid COM port Node!"
    try:
        with global_lock:
            if ser and ser.is_open:
                ser.close()
            ser = serial.Serial(selected_port, 115200, timeout=0.5)
        return f"Connected to {selected_port}"
    except Exception as e:
        return f"Error: {e}"

@app.callback(
    [
        Output('btn-toggle-audio', 'children'),
        Output('btn-toggle-audio', 'style')
    ],
    Input('btn-toggle-audio', 'n_clicks'),
    State('btn-toggle-audio', 'children'),
    prevent_initial_call=True
)
def toggle_audio(n_clicks, current_label):
    with global_lock:
        current_state = audio_settings["enabled"]
        audio_settings["enabled"] = not current_state
    if not current_state:
        return "🔊 Toggle Audio ON", {'backgroundColor': '#10b981', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}
    else:
        return "🔇 Toggle Audio OFF", {'backgroundColor': '#ef4444', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}

@app.callback(
    [
        Output('btn-genre-ambient', 'style'),
        Output('btn-genre-scifi', 'style'),
        Output('btn-genre-drone', 'style'),
        Output('btn-genre-cyberpunk', 'style')
    ],
    [
        Input('btn-genre-ambient', 'n_clicks'),
        Input('btn-genre-scifi', 'n_clicks'),
        Input('btn-genre-drone', 'n_clicks'),
        Input('btn-genre-cyberpunk', 'n_clicks')
    ],
    prevent_initial_call=True
)
def select_genre(amb, scif, drone, cyb):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    active_style = {'backgroundColor': '#10b981', 'color': 'white', 'padding': '12px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}
    inactive_style = {'backgroundColor': '#334155', 'color': 'white', 'padding': '12px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer'}
    
    with global_lock:
        if button_id == 'btn-genre-ambient':
            audio_settings["genre"] = "ambient"
            return active_style, inactive_style, inactive_style, inactive_style
        elif button_id == 'btn-genre-scifi':
            audio_settings["genre"] = "scifi"
            return inactive_style, active_style, inactive_style, inactive_style
        elif button_id == 'btn-genre-drone':
            audio_settings["genre"] = "drone"
            return inactive_style, inactive_style, active_style, inactive_style
        elif button_id == 'btn-genre-cyberpunk':
            audio_settings["genre"] = "cyberpunk"
            return inactive_style, inactive_style, inactive_style, active_style
            
    return no_update, no_update, no_update, no_update

@app.callback(
    [
        Output('live-atmospheric-history', 'figure'),
        Output('telemetry-readouts', 'children')
    ],
    Input('graph-update-interval', 'n_intervals'),
    State('slider-volume', 'value')
)
def update_dashboard(n, vol):
    with global_lock:
        if vol is not None: 
            audio_settings["volume"] = float(vol)
            
        t = latest_data["temperature"]
        h = latest_data["humidity"]
        p = latest_data["pressure"]
        g = latest_data["gas_resistance"]

    cards = [
        html.Div(style={'backgroundColor': '#1e293b', 'padding': '15px', 'borderRadius': '8px', 'flex': '1', 'textAlign': 'center'}, children=[html.Div("🌡️ TEMP (Tone)", style={'color':'#94a3b8'}), html.H2(f"{t:.1f}°C")]),
        html.Div(style={'backgroundColor': '#1e293b', 'padding': '15px', 'borderRadius': '8px', 'flex': '1', 'textAlign': 'center'}, children=[html.Div("💧 HUMIDITY (Fade)", style={'color':'#38bdf8'}), html.H2(f"{h:.1f}%")]),
        html.Div(style={'backgroundColor': '#1e293b', 'padding': '15px', 'borderRadius': '8px', 'flex': '1', 'textAlign': 'center'}, children=[html.Div("🌪 PRESSURE (Echo)", style={'color':'#fbbf24'}), html.H2(f"{p:.1f} hPa")]),
        html.Div(style={'backgroundColor': '#1e293b', 'padding': '15px', 'borderRadius': '8px', 'flex': '1', 'textAlign': 'center'}, children=[html.Div("☣ GAS (Texture)", style={'color':'#a78bfa'}), html.H2(f"{g/1000.0:.1f} kΩ")]),
    ]
    
    fig = go.Figure(data=[go.Bar(
        x=['Temp (Tone Pitch)', 'Humidity (Fade Decay)', 'Pressure (Echo Feedback)', 'Gas (Texture Breath)'],
        y=[t, h, p/10.0, g/5000.0],
        marker_color=['#10b981', '#38bdf8', '#fbbf24', '#a78bfa']
    )])
    fig.update_layout(
        title="Live TPHG Generative Parameter Mapping",
        paper_bgcolor='#1e293b', plot_bgcolor='#0b0f19', font=dict(color='#f3f4f6'),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig, cards

if __name__ == '__main__':
    app.run(debug=False, port=8050)


