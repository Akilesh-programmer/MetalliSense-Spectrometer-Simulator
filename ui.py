import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
from opc_server import SpectrometerOPCUAServer
import time
import os

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

        self.server = SpectrometerOPCUAServer()
        self.server_thread = None
        self.server_running = False

        # Style for ttk buttons
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Accent.TButton',
                        font=("Segoe UI", 14, "bold"),
                        foreground="#ffffff",
                        background="#1976d2",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none',
                        padding=10)
        style.map('Accent.TButton',
                  background=[('active', '#1565c0'), ('disabled', '#b0bec5')])
        style.configure('Read.TButton',
                        font=("Segoe UI", 14, "bold"),
                        foreground="#ffffff",
                        background="#26a69a",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none',
                        padding=10)
        style.map('Read.TButton',
                  background=[('active', '#00897b'), ('disabled', '#b0bec5')])
        style.configure('Off.TButton',
                        font=("Segoe UI", 14, "bold"),
                        foreground="#ffffff",
                        background="#b71c1c",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none',
                        padding=10)
        style.map('Off.TButton',
                  background=[('active', '#d32f2f'), ('disabled', '#b0bec5')])

        # Header
        self.header = tk.Label(master, text="MetalliSense Spectrometer Simulator", bg="#ffffff", fg="#1a237e", font=("Segoe UI", 22, "bold"))
        self.header.pack(pady=(22, 4))

        # OPC UA Highlight Label (side by side)
        self.opcua_frame = tk.Frame(master, bg="#ffffff")
        self.opcua_frame.pack(pady=(0, 10))
        self.opcua_label1 = tk.Label(self.opcua_frame, text="Powered by ", bg="#ffffff", fg="#1976d2", font=("Segoe UI", 13, "bold"))
        self.opcua_label1.pack(side="left")
        self.opcua_label2 = tk.Label(self.opcua_frame, text="OPC UA", bg="#ffffff", fg="#ff9800", font=("Segoe UI", 13, "bold"))
        self.opcua_label2.pack(side="left")

        # Sub-header / instructions
        self.instructions = tk.Label(master, text="1. Turn on the spectrometer OPC/UA server before connecting the client.\n2. Client sets parameters, then operator clicks 'Read Data'.", bg="#ffffff", fg="#37474f", font=("Segoe UI", 12), justify="center")
        self.instructions.pack(pady=(0, 16))

        # Status
        self.status_label = tk.Label(master, text="Status: OFFLINE", bg="#ffffff", fg="#b71c1c", font=("Segoe UI", 14, "bold"))
        self.status_label.pack(pady=10)

        # Button frame for better layout
        self.button_frame = tk.Frame(master, bg="#ffffff")
        self.button_frame.pack(pady=10)

        # Turn on spectrometer button
        self.turn_on_button = ttk.Button(self.button_frame, text="Turn on Spectrometer OPC/UA Server", style='Accent.TButton', command=self.start_server)
        self.turn_on_button.pack(fill="x", padx=16, pady=(0, 14))

        # Turn off spectrometer button
        self.turn_off_button = ttk.Button(self.button_frame, text="Turn off Spectrometer", style='Off.TButton', command=self.stop_server, state="disabled")
        self.turn_off_button.pack(fill="x", padx=16, pady=(0, 14))

        # Read data button
        self.read_button = ttk.Button(self.button_frame, text="Read Data", style='Read.TButton', command=self.read_data, state="disabled")
        self.read_button.pack(fill="x", padx=16, pady=(0, 8))

        # Footer (copyright)
        self.footer = tk.Label(master, text="© 2024 MetalliSense Hackathon", bg="#ffffff", fg="#78909c", font=("Segoe UI", 12, "italic"))
        self.footer.pack(side="bottom", pady=24)

    def start_server(self):
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)
        self.server_running = True
        self.status_label.config(text="Status: ONLINE", fg="#388e3c")
        self.read_button.config(state="normal")
        self.turn_on_button.config(state="disabled")
        self.turn_off_button.config(state="normal")

    def stop_server(self):
        if self.server_running:
            self.server.server.stop()
            self.server_running = False
            self.status_label.config(text="Status: OFFLINE", fg="#b71c1c")
            self.read_button.config(state="disabled")
            self.turn_on_button.config(state="normal")
            self.turn_off_button.config(state="disabled")

    def read_data(self):
        try:
            result = self.server.generate_reading()
            messagebox.showinfo("Spectrometer Reading", f"Simulated Reading:\n{result}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate reading: {e}")

def run_app():
    root = tk.Tk()
    app = SpectrometerApp(root)
    root.mainloop()
