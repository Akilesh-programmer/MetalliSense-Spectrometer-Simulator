import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
import json
from mqtt_server import SpectrometerMQTTServer
import time
import os

# Constants for style names and font
ACCENT_TBUTTON = 'Accent.TButton'
READ_TBUTTON = 'Read.TButton'
OFF_TBUTTON = 'Off.TButton'
SEGOE_UI_FONT = "Segoe UI"
NOT_DISABLED = '!disabled'

class SpectrometerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("MetalliSense Spectrometer Simulator")
        self.master.geometry("600x470")
        self.master.configure(bg="#ffffff")
        self.master.resizable(False, False)

        icon_path = os.path.join(os.path.dirname(__file__), "spectrometer_icon.ico")
        if os.path.exists(icon_path):
            self.master.iconbitmap(icon_path)

        self.server = SpectrometerMQTTServer()
        self.server_thread = None
        self.server_running = False

        # Style for ttk buttons
        style = ttk.Style()
        style.theme_use('default')
        style.configure(ACCENT_TBUTTON,
                        font=(SEGOE_UI_FONT, 14, "bold"),
                        foreground="#ffffff",
                        background="#1976d2",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none',
                        padding=10)
        style.map(ACCENT_TBUTTON,
                  background=[('active', '#1565c0'), ('disabled', '#b0bec5')])
        style.configure(READ_TBUTTON,
                        font=(SEGOE_UI_FONT, 14, "bold"),
                        foreground="#ffffff",
                        background="#26a69a",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none',
                        padding=10)
        style.map(READ_TBUTTON,
                  background=[('active', '#00897b'), ('disabled', '#b0bec5')])
        style.configure(OFF_TBUTTON,
                        font=(SEGOE_UI_FONT, 14, "bold"),
                        foreground="#ffffff",
                        background="#b71c1c",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none',
                        padding=10)
        style.map(OFF_TBUTTON,
                  background=[('active', '#d32f2f'), ('disabled', '#b0bec5')])

        # Header
        self.header = tk.Label(master, text="MetalliSense Spectrometer Simulator", bg="#ffffff", fg="#1a237e", font=(SEGOE_UI_FONT, 22, "bold"))
        self.header.pack(pady=(22, 4))

        # OPC UA Highlight Label (side by side) - Updated for MQTT
        self.mqtt_frame = tk.Frame(master, bg="#ffffff")
        self.mqtt_frame.pack(pady=(0, 10))
        self.mqtt_label1 = tk.Label(self.mqtt_frame, text="Powered by ", bg="#ffffff", fg="#1976d2", font=(SEGOE_UI_FONT, 13, "bold"))
        self.mqtt_label1.pack(side="left")
        self.mqtt_label2 = tk.Label(self.mqtt_frame, text="MQTT", bg="#ffffff", fg="#ff9800", font=(SEGOE_UI_FONT, 13, "bold"))
        self.mqtt_label2.pack(side="left")

        # Sub-header / instructions
        self.instructions = tk.Label(master, text="1. Turn on the spectrometer MQTT server before connecting the client.\n2. Client sets parameters, then operator clicks 'Read Data'.", bg="#ffffff", fg="#37474f", font=(SEGOE_UI_FONT, 12), justify="center")
        self.instructions.pack(pady=(0, 16))

        # Status
        self.status_label = tk.Label(master, text="Status: OFFLINE", bg="#ffffff", fg="#b71c1c", font=(SEGOE_UI_FONT, 14, "bold"))
        self.status_label.pack(pady=10)

        # Button frame for better layout
        self.button_frame = tk.Frame(master, bg="#ffffff")
        self.button_frame.pack(pady=10)

        # Turn on spectrometer button
        self.turn_on_button = ttk.Button(self.button_frame, text="Turn on Spectrometer MQTT Server", style=ACCENT_TBUTTON, command=self.start_server)
        self.turn_on_button.pack(fill="x", padx=16, pady=(0, 14))

        # Turn off spectrometer button
        self.turn_off_button = ttk.Button(self.button_frame, text="Turn off Spectrometer", style=OFF_TBUTTON, command=self.stop_server, state="disabled")
        self.turn_off_button.pack(fill="x", padx=16, pady=(0, 14))

        # Read data button
        self.read_button = ttk.Button(self.button_frame, text="Read Data", style=READ_TBUTTON, command=self.read_data, state="disabled")
        self.read_button.pack(fill="x", padx=16, pady=(0, 8))

        # Footer (copyright) in a dedicated frame
        self.footer_frame = tk.Frame(master, bg="#ffffff")
        self.footer_frame.pack(side="bottom", fill="x")
        self.footer = tk.Label(self.footer_frame, text="© 2024 MetalliSense Hackathon", bg="#ffffff", fg="#78909c", font=(SEGOE_UI_FONT, 12, "italic"))
        self.footer.pack(pady=32)

    def start_server(self):
        """Start the MQTT server"""
        # Show connecting status
        self.status_label.config(text="Status: CONNECTING...", fg="#ff9800")
        self.master.update()
        
        if self.server.start():
            self.server_running = True
            # Check if using embedded broker
            broker_type = "EMBEDDED" if self.server.use_embedded else "EXTERNAL"
            self.status_label.config(text=f"Status: ONLINE ({broker_type})", fg="#388e3c")
            self.read_button.config(state="normal")
            self.turn_on_button.config(state="disabled")
            self.turn_off_button.config(state="normal")
            
            if self.server.use_embedded:
                messagebox.showinfo("MQTT Broker", 
                    "Using embedded MQTT broker.\n\n" +
                    "For production use, consider installing Mosquitto:\n" +
                    "https://mosquitto.org/download/")
        else:
            self.status_label.config(text="Status: OFFLINE", fg="#b71c1c")
            messagebox.showerror("Connection Error", 
                "Failed to start MQTT server.\n\n" +
                "Solutions:\n" +
                "1. Install and start Mosquitto broker\n" +
                "2. Run 'start_mqtt_broker.bat' as Administrator\n" +
                "3. Or install Docker and run:\n" +
                "   docker run -p 1883:1883 eclipse-mosquitto")

    def stop_server(self):
        """Stop the MQTT server"""
        if self.server_running:
            self.server.stop()
            self.server_running = False
            self.status_label.config(text="Status: OFFLINE", fg="#b71c1c")
            self.read_button.config(state="disabled")
            self.turn_on_button.config(state="normal")
            self.turn_off_button.config(state="disabled")

    def read_data(self):
        """Generate and display reading data"""
        try:
            result = self.server.generate_reading()
            if result:
                reading_str = json.dumps(result, indent=2)
                messagebox.showinfo("Spectrometer Reading", f"Simulated Reading:\n{reading_str}")
            else:
                messagebox.showerror("Error", "Failed to generate reading")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate reading: {e}")

def run_app():
    root = tk.Tk()
    SpectrometerApp(root)
    root.mainloop()
