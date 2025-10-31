import socket
import threading
import os
import mido
from mido import open_input
import time
from collections import deque  # For send queue
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk  # For theme styling
import subprocess  # For system theme detection

# Force rtmidi backend
os.environ['MIDO_BACKEND'] = 'mido.backends.rtmidi'

# Config
HOST = '127.0.0.1'
PORT = 8899
BUFFER_SIZE = 1024

class MidiBridgeGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MIDI Bridge")
        self.root.geometry("600x400")

        # Detect system theme (macOS-specific)
        self.theme = self.get_system_theme()
        self.root_bg = 'black' if self.theme == 'dark' else 'white'
        self.fg = 'white' if self.theme == 'dark' else 'black'
        self.select_bg = 'blue' if self.theme == 'dark' else 'lightblue'
        self.select_fg = 'white' if self.theme == 'dark' else 'black'
        self.insert_bg = self.fg
        self.root.configure(bg=self.root_bg)

        # Use native aqua theme for better system integration
        style = ttk.Style()
        style.theme_use('aqua')

        # Get button background color for frames
        button_bg = style.lookup('TButton', 'background') or '#f0f0f0'  # Fallback to light gray

        # Top frame for buttons and status
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Button frame on left
        self.btn_frame = ttk.Frame(self.top_frame)
        self.btn_frame.pack(side=tk.LEFT)

        self.start_btn = ttk.Button(self.btn_frame, text="Start Bridge", command=self.start_bridge)
        self.start_btn.pack(side=tk.LEFT, pady=2, padx=(0, 10))

        self.stop_btn = ttk.Button(self.btn_frame, text="Stop Bridge", command=self.stop_bridge, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, pady=2)

        # Status frame on right
        self.status_frame = ttk.Frame(self.top_frame)
        self.status_frame.pack(side=tk.RIGHT)

        # Picotron label (static, white)
        self.picotron_label = tk.Label(
            self.status_frame,
            text="Picotron: ",
            fg=self.fg,
            bg=button_bg,
            font=('Monaco', 9)
        )
        self.picotron_label.pack(side=tk.LEFT)

        # Connection label (colored, packed next)
        self.connection_label = tk.Label(
            self.status_frame,
            text="Disconnected",
            fg='#B71C1C',  # Dull red
            bg=button_bg,
            font=('Monaco', 9, 'bold')
        )
        self.connection_label.pack(side=tk.LEFT)

        # Separator label
        self.separator_label = tk.Label(
            self.status_frame,
            text=" | ",
            fg=self.fg,
            bg=button_bg,
            font=('Monaco', 9)
        )
        self.separator_label.pack(side=tk.LEFT)

        # Details label (Queue and Notes)
        self.details_label = tk.Label(
            self.status_frame,
            text="Queue: 0 | Notes: 0",
            fg=self.fg,
            bg=button_bg,
            font=('Monaco', 9)
        )
        self.details_label.pack(side=tk.LEFT)

        self.log_text = scrolledtext.ScrolledText(
            self.root, 
            height=20, 
            width=80, 
            bg=self.root_bg, 
            fg=self.fg,
            selectbackground=self.select_bg, 
            selectforeground=self.select_fg,
            insertbackground=self.insert_bg,
            relief='flat',
            bd=0,
            font=('Monaco', 10)  # Fixed-width font for better log readability
        )
        # Apply a custom tag for consistent coloring
        self.log_text.tag_configure('log', foreground=self.fg, background=self.root_bg)
        self.log_text.pack(pady=5, fill=tk.BOTH, expand=True)

        # Globals
        self.active_notes = {}
        self.channels_in_use = set()
        self.free_channels = list(range(8))
        self.send_queue = deque()
        self.connected_event = threading.Event()
        self.client_socket = None
        self.inport = None
        self.stop_event = threading.Event()

        # Start TCP listener thread
        threading.Thread(target=self.tcp_accept_thread, daemon=True).start()

        # Start status updates (faster polling: 200ms)
        self.update_status()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def get_system_theme(self):
        """Detect macOS system appearance (light/dark)."""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell app "System Events" to tell appearance preferences to return dark mode'],
                capture_output=True, text=True, timeout=5
            )
            return 'dark' if result.stdout.strip() == 'true' else 'light'
        except Exception:
            # Fallback to light if detection fails
            return 'light'

    def log(self, msg):
        def update():
            timestamp = time.strftime('%H:%M:%S')
            self.log_text.insert(tk.END, f"{timestamp} {msg}\n", 'log')
            self.log_text.see(tk.END)
            self.log_text.update_idletasks()  # Force redraw
        self.root.after(0, update)

    def update_status(self):
        """Update status labels with current values."""
        is_connected = self.connected_event.is_set()
        queue_len = len(self.send_queue)
        notes_count = len(self.active_notes)

        # Update connection label
        if is_connected:
            self.connection_label.config(text="Connected", fg='#4CAF50')  # Medium green
        else:
            self.connection_label.config(text="Disconnected", fg='#B71C1C')  # Dull red

        # Update details label
        self.details_label.config(text=f"Queue: {queue_len} | Notes: {notes_count}")

        # Poll every 200ms for responsiveness
        self.root.after(200, self.update_status)

    def get_free_channel(self):
        for ch in self.free_channels:
            if ch not in self.channels_in_use:
                return ch
        return None

    def release_channel(self, channel):
        if channel in self.channels_in_use:
            self.channels_in_use.discard(channel)

    def midi_to_picotron_pitch(self, note):
        pitch = note - 12
        return max(0, min(120, pitch))

    def send_message(self, msg_str):
        """Thread-safe send or queue."""
        if self.connected_event.is_set() and self.client_socket:
            try:
                self.client_socket.send((msg_str + ',').encode('utf-8'))
                self.log(f"Sent: {msg_str}")
            except Exception as e:
                print(f"Send error: {e}")  # Log to console instead
                # On send error, assume connection lost
                self.connected_event.clear()
        else:
            self.send_queue.append(msg_str)
            print(f"Queued (not connected): {msg_str}")  # Log to console instead

    def flush_queue(self):
        """Send buffered msgs on connect."""
        while self.send_queue:
            self.send_message(self.send_queue.popleft())

    def handle_midi_messages(self, inport):
        print("MIDI handler thread started—waiting for notes (connect Jazz Hands to enable sends)...")  # Console only
        for msg in inport:
            if self.stop_event.is_set():
                break
            note_val = getattr(msg, 'note', 'N/A')
            vel_val = getattr(msg, 'velocity', 'N/A')
            print(f"Received MIDI msg: type={msg.type}, note={note_val}, velocity={vel_val}, channel={msg.channel}")  # Console only
            if msg.type == 'note_on' and getattr(msg, 'velocity', 0) > 0:
                note = msg.note
                pitch = self.midi_to_picotron_pitch(note)
                vel = int((msg.velocity / 127) * 255)
                channel = self.get_free_channel()
                if channel is not None:
                    msg_str = f"NOTE_ON:{note}:{vel}:{channel}"
                    self.send_message(msg_str)
                    self.active_notes[note] = channel
                    self.channels_in_use.add(channel)
                    self.log(f"Processed NOTE_ON: {note} (pitch {pitch}, vol {vel}) on ch {channel}")
                else:
                    self.log(f"Warning: No free channel for note {note}—dropping.")
            elif msg.type == 'note_off' or (msg.type == 'note_on' and getattr(msg, 'velocity', 0) == 0):
                note = msg.note
                if note in self.active_notes:
                    channel = self.active_notes[note]
                    msg_str = f"NOTE_OFF:{note}:{channel}"
                    self.send_message(msg_str)
                    del self.active_notes[note]
                    self.release_channel(channel)
                    self.log(f"Processed NOTE_OFF: {note} on ch {channel}")
                else:
                    self.log(f"Warning: NOTE_OFF for {note} but not active—ignoring.")
        print("MIDI handler stopped.")  # Console only

    def monitor_ports(self):
        print("Port monitor thread started—checking for device changes...")  # Console only
        last_ports = set(mido.get_input_names())
        while not self.stop_event.is_set():
            time.sleep(2)
            current_ports = set(mido.get_input_names())
            if current_ports != last_ports:
                added = current_ports - last_ports
                removed = last_ports - current_ports
                if added:
                    print(f"*** MIDI devices connected: {added} ***")  # Console only
                if removed:
                    print(f"*** MIDI devices disconnected: {removed} ***")  # Console only
                last_ports = current_ports
        print("Port monitor stopped.")  # Console only

    def tcp_accept_thread(self):
        """Thread for non-blocking accept with reconnect on disconnect."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"Listening for Jazz Hands on {HOST}:{PORT}...")  # Console only
        while not self.stop_event.is_set():
            try:
                self.client_socket, addr = server_socket.accept()
                print(f"Connected by Jazz Hands: {addr}")  # Console only
                print(f"Active notes: {self.active_notes} | Channels in use: {self.channels_in_use}")  # Console only
                self.connected_event.set()
                self.flush_queue()  # Send any pre-connect msgs
                # Echo loop with better error handling
                while not self.stop_event.is_set():
                    try:
                        data = self.client_socket.recv(BUFFER_SIZE)
                        if not data:
                            print("Jazz Hands disconnected.")  # Console only
                            break
                        if data.strip():
                            print(f"Received from Jazz Hands: {data.decode('utf-8').strip()}")  # Console only
                    except (ConnectionError, OSError, ConnectionResetError) as conn_err:
                        print(f"Connection lost unexpectedly: {conn_err}")  # Console only
                        break
                    except Exception as e:
                        print(f"Echo loop error: {e}")  # Console only
                        break
                self.connected_event.clear()
                print("Disconnected from Jazz Hands.")  # Console only
                if self.client_socket:
                    self.client_socket.close()
                    self.client_socket = None
            except Exception as e:
                print(f"Server error: {e}")  # Console only
                if self.client_socket:
                    self.client_socket.close()
                    self.client_socket = None
                    self.connected_event.clear()
                time.sleep(1)  # Brief pause before retry
        print("TCP server stopped.")  # Console only
        if self.client_socket:
            self.client_socket.close()
        server_socket.close()

    def start_bridge(self):
        self.stop_event.clear()
        print("Starting MIDI Bridge...")  # Console only
        # Start monitor
        threading.Thread(target=self.monitor_ports, daemon=True).start()
        # Start MIDI input
        try:
            available_ports = mido.get_input_names()
            print(f"Available MIDI inputs: {available_ports}")  # Console only
            port_name = None
            for port in available_ports:
                if 'DONNER N32' in port.upper():  # Exact match for your device
                    port_name = port
                    break
            port_name = port_name or available_ports[0] if available_ports else None
            if port_name:
                self.inport = open_input(port_name)
                print(f"Listening to MIDI input: {self.inport.name}")  # Console only
                threading.Thread(target=self.handle_midi_messages, args=(self.inport,), daemon=True).start()
            else:
                print("No MIDI inputs found—plug in Donner N-32.")  # Console only
        except Exception as e:
            print(f"MIDI error: {e}. Check device.")  # Console only
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop_bridge(self):
        print("Stopping MIDI Bridge...")  # Console only
        self.stop_event.set()
        if self.inport:
            self.inport.close()
            self.inport = None
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            self.connected_event.clear()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        print("MIDI Bridge stopped.")  # Console only

    def on_closing(self):
        self.stop_bridge()
        self.root.destroy()

if __name__ == "__main__":
    app = MidiBridgeGUI()