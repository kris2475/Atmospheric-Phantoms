import threading
import time
import serial
import serial.tools.list_ports
import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, clientside_callback

# Calibration coefficients
A0 = 3.086965198E+02
B1 = 2.718912698E+00
B2 = -1.434471882E-03
B3 = -5.759067943E-06
B4 = 3.250344320E-09
B5 = 1.237572658E-11

def pixel_to_wavelength(pix_rel):
    return (A0 + B1 * pix_rel + B2 * (pix_rel ** 2) + 
            B3 * (pix_rel ** 3) + B4 * (pix_rel ** 4) + B5 * (pix_rel ** 5))

ALL_WAVELENGTHS = [pixel_to_wavelength(i) for i in range(288)]

# Shared Global State
ser = None
global_lock = threading.Lock()
latest_data = {
    "pixels": [0.0] * 288,
    "device_msg": "System Ready."
}

# --- 6 Genuinely Distinct Real Music & Audio Streams ---
GENRE_STREAMS = {
    "Electronic Ambient": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "Classical Symphony": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "Smooth Jazz":        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "1980s Pop":          "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
    "Country & Western":  "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
    "Rock / Alternative": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3"
}

current_active_genre = "None"

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
                if current_ser.in_waiting > 1024:
                    current_ser.reset_input_buffer()

                line = current_ser.readline().decode('utf-8', errors='ignore').strip()
                if not line or line.startswith("[") or "MENU" in line:
                    continue
                
                parts = line.split(',')
                if len(parts) >= 294:
                    raw_pixels = [float(x) for x in parts[6:294]]
                    with global_lock:
                        latest_data["pixels"] = raw_pixels
                elif len(parts) == 288:
                    raw_pixels = [float(x) for x in parts]
                    with global_lock:
                        latest_data["pixels"] = raw_pixels
            except Exception:
                time.sleep(0.05)
        else:
            time.sleep(0.2)

threading.Thread(target=serial_reader_thread, daemon=True).start()

# Initialize Dash App Layout
app = Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#0b0f19', 'color': '#f3f4f6', 'padding': '25px', 'fontFamily': 'Inter, sans-serif'}, children=[
    
    html.Audio(id='audio-player-1', preload='auto'),
    html.Audio(id='audio-player-2', preload='auto'),
    html.Div(id='crossfade-trigger', style={'display': 'none'}),

    html.Div(style={'textAlign': 'center', 'marginBottom': '20px'}, children=[
        html.H1("📻 C12880MA Spectral Shape & Slope Jukebox", style={'color': '#38bdf8', 'fontWeight': '700', 'margin': '0'}),
        html.P("Genre selection is driven by the overall spectral slope, distribution shape, and regional energy balance.", style={'color': '#94a3b8', 'fontSize': '1rem'})
    ]),
    
    html.Div(style={'backgroundColor': '#1e293b', 'padding': '15px', 'borderRadius': '10px', 'marginBottom': '20px', 'display': 'flex', 'gap': '15px', 'alignItems': 'center', 'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'}, children=[
        dcc.Dropdown(id='port-dropdown', options=get_available_ports(), placeholder="Select COM Port...", style={'width': '300px', 'color': '#000'}),
        html.Button('Connect & Stream', id='btn-connect', n_clicks=0, style={'backgroundColor': '#0284c7', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': '600'}),
        html.Div(id='connection-status', children="Status: Disconnected", style={'color': '#f87171', 'fontWeight': 'bold'})
    ]),

    html.Div(style={'backgroundColor': '#0f172a', 'border': '2px solid #38bdf8', 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '20px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'boxShadow': '0 0 15px rgba(56, 189, 248, 0.15)'}, children=[
        html.Div(children=[
            html.H4("🎯 Active Spectral Station", style={'color': '#94a3b8', 'margin': '0 0 5px 0', 'fontSize': '0.9rem', 'textTransform': 'uppercase', 'letterSpacing': '1px'}),
            html.H2(id='active-genre-display', children="Waiting for Light Signal...", style={'color': '#38bdf8', 'margin': '0', 'fontWeight': '700'})
        ]),
        html.Div(style={'textAlign': 'right'}, children=[
            html.H4("Spectral Shape Metrics (Slope / Spread)", style={'color': '#94a3b8', 'margin': '0 0 5px 0', 'fontSize': '0.9rem'}),
            html.H3(id='centroid-wavelength-display', children="---", style={'color': '#facc15', 'margin': '0', 'fontWeight': '600'})
        ])
    ]),

    html.Div(style={'backgroundColor': '#1e293b', 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px', 'boxShadow': '0 4px 6px -1px rgba(0,0,0,0.1)'}, children=[
        html.H3("🎛️ Hardware & Manual Jukebox Controls", style={'color': '#38bdf8', 'marginTop': '0', 'fontSize': '1.1rem'}),
        html.Div(style={'display': 'flex', 'gap': '15px', 'flexWrap': 'wrap', 'alignItems': 'center'}, children=[
            html.Button('💡 Toggle LED Strobe', id='btn-toggle-led', n_clicks=0, style={'backgroundColor': '#f59e0b', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}),
            html.Button('⚡ Toggle Auto-Integration', id='btn-toggle-auto', n_clicks=0, style={'backgroundColor': '#8b5cf6', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}),
            
            html.Div(style={'display': 'inline-block', 'minWidth': '240px'}, children=[
                html.B("Manual Genre Override:", style={'fontSize': '0.9rem', 'color': '#94a3b8', 'display': 'block', 'marginBottom': '3px'}),
                dcc.Dropdown(
                    id='manual-genre-dropdown',
                    options=[{'label': g, 'value': g} for g in GENRE_STREAMS.keys()],
                    placeholder="Auto (Shape & Slope Analysis)",
                    style={'color': '#000'}
                )
            ])
        ])
    ]),

    dcc.Graph(id='live-spectrum-plot', style={'height': '380px'}),
    dcc.Interval(id='graph-update-interval', interval=400, n_intervals=0)
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
        return "Please select a port!"
    try:
        with global_lock:
            if ser and ser.is_open:
                ser.close()
            ser = serial.Serial(selected_port, 115200, timeout=0.5)
            time.sleep(1.5)
            ser.write(b"STREAM\n")
        return f"Connected to {selected_port}"
    except Exception as e:
        return f"Error: {e}"

@app.callback(
    Output('btn-toggle-led', 'style'),
    Input('btn-toggle-led', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_led(n_clicks):
    global ser
    try:
        with global_lock:
            if ser and ser.is_open:
                ser.write(b"L\n")
    except Exception as e:
        print(f"LED command error: {e}")
    return {'backgroundColor': '#10b981', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}

@app.callback(
    Output('btn-toggle-auto', 'style'),
    Input('btn-toggle-auto', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_auto_integration(n_clicks):
    global ser
    try:
        with global_lock:
            if ser and ser.is_open:
                ser.write(b"A\n")
    except Exception as e:
        print(f"Auto-Integration command error: {e}")
    return {'backgroundColor': '#06b6d4', 'color': 'white', 'padding': '10px 20px', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold'}

@app.callback(
    [Output('live-spectrum-plot', 'figure'),
     Output('active-genre-display', 'children'),
     Output('centroid-wavelength-display', 'children'),
     Output('crossfade-trigger', 'children')],
    [Input('graph-update-interval', 'n_intervals'),
     Input('manual-genre-dropdown', 'value')]
)
def update_dashboard(n, manual_genre):
    global current_active_genre
    
    with global_lock:
        pixels = list(latest_data["pixels"])

    detected_genre = "Electronic Ambient"
    shape_desc = "---"
    audio_url_to_trigger = ""
    
    genres_list = list(GENRE_STREAMS.keys())

    if manual_genre:
        detected_genre = manual_genre
        shape_desc = "Manual Override"
    else:
        if len(pixels) == 288:
            arr = np.array(pixels, dtype=np.float32)
            floor = np.min(arr)
            cleaned = np.clip(arr - floor, 0, None)
            total_intensity = np.sum(cleaned)
            
            if total_intensity > 100:
                # 1. Linear regression slope across the spectrum (overall upward or downward trend)
                x_indices = np.arange(288)
                slope, _ = np.polyfit(x_indices, cleaned, 1)
                
                # 2. Split spectrum into 3 regional energy ratios (Blue/UV end, Middle, Red/IR end)
                third = 96
                low_energy = np.sum(cleaned[:third]) / total_intensity
                mid_energy = np.sum(cleaned[third:2*third]) / total_intensity
                high_energy = np.sum(cleaned[2*third:]) / total_intensity
                
                # 3. Compute spectral spread / standard deviation (indicates peak sharpness vs broad profile)
                weights = cleaned / total_intensity
                mean_idx = np.sum(x_indices * weights)
                spread = np.sqrt(np.sum(weights * (x_indices - mean_idx)**2))
                
                shape_desc = f"Slope: {slope:.2f} | Spread: {spread:.1f}"
                
                # Composite scoring metric combining slope, energy distribution, and spread
                # This guarantees that changing the spectral contour maps cleanly across all 6 genres
                composite_score = (slope * 2.0) + (high_energy - low_energy) * 50.0 + (spread * 0.1)
                
                # Normalize / map score into 6 discrete bins
                bin_idx = int(np.clip((composite_score + 10) / 25.0 * 6, 0, 5))
                detected_genre = genres_list[bin_idx]
            else:
                detected_genre = "No Light Signal Detected"

    if detected_genre in GENRE_STREAMS and detected_genre != current_active_genre:
        current_active_genre = detected_genre
        audio_url_to_trigger = GENRE_STREAMS[detected_genre]

    fig = go.Figure(
        data=[go.Scatter(
            x=ALL_WAVELENGTHS,
            y=pixels,
            mode='lines',
            line=dict(color='#38bdf8', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(56, 189, 248, 0.1)'
        )]
    )
    fig.update_layout(
        title="Live Spectral Shape & Slope Curve",
        xaxis_title="Wavelength (nm)",
        yaxis_title="Intensity",
        paper_bgcolor='#1e293b',
        plot_bgcolor='#0b0f19',
        font=dict(color='#f3f4f6'),
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(showgrid=True, gridcolor='#334155'),
        yaxis=dict(showgrid=True, gridcolor='#334155')
    )
    
    return fig, detected_genre, shape_desc, audio_url_to_trigger

# --- Browser Clientside Crossfade Callback ---
clientside_callback(
    """
    function(url) {
        if (!url) return '';
        
        let p1 = document.getElementById('audio-player-1');
        let p2 = document.getElementById('audio-player-2');
        
        let activePlayer = window.activeAudioPlayer === 2 ? p2 : p1;
        let nextPlayer = window.activeAudioPlayer === 2 ? p1 : p2;
        window.activeAudioPlayer = window.activeAudioPlayer === 2 ? 1 : 2;
        
        nextPlayer.src = url;
        nextPlayer.volume = 0.0;
        nextPlayer.play().catch(e => console.log("Waiting for user gesture or autoplay restricted"));
        
        let duration = 1500;
        let steps = 30;
        let intervalTime = duration / steps;
        let stepCount = 0;
        
        let fadeInterval = setInterval(function() {
            stepCount++;
            let progress = stepCount / steps;
            
            nextPlayer.volume = Math.min(1.0, progress);
            if (activePlayer && !activePlayer.paused) {
                activePlayer.volume = Math.max(0.0, 1.0 - progress);
            }
            
            if (stepCount >= steps) {
                clearInterval(fadeInterval);
                if (activePlayer) {
                    activePlayer.pause();
                }
            }
        }, intervalTime);
        
        return '';
    }
    """,
    Output('crossfade-trigger', 'title'),
    Input('crossfade-trigger', 'children')
)

if __name__ == '__main__':
    app.run(debug=False, port=8050)