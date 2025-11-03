import socket
import threading
import os
import mido
from mido import open_input
import time
from collections import deque  # For send queue

# Force portmidi backend for MIDI handling (ensures compatibility across platforms)
os.environ['MIDO_BACKEND'] = 'mido.backends.portmidi'

# Configuration constants
HOST = '127.0.0.1'  # Localhost for TCP server binding
PORT = 8899         # Port for TCP connection to Jazz Hands
BUFFER_SIZE = 1024  # Buffer size for receiving data from client

# Global variables for state management
active_notes = {}              # Dictionary to track active notes: note -> channel
channels_in_use = set()        # Set of channels currently in use
free_channels = list(range(8)) # List of available channels (0-7 assumed for Picotron)
send_queue = deque()           # Queue for buffering messages until connection is established
connected_event = threading.Event()  # Event to signal when client is connected
client_socket = None           # Socket for connected client
inport = None                  # MIDI input port

# Log file for recording all MIDI messages
log_file = open("temp.txt", mode="a")

def get_free_channel():
    """
    Find and return the next available free channel from free_channels.
    Returns None if no channels are available.
    """
    for ch in free_channels:
        if ch not in channels_in_use:
            return ch
    return None

def release_channel(channel):
    """
    Release a channel back to available pool by removing from channels_in_use.
    """
    if channel in channels_in_use:
        channels_in_use.remove(channel)

def midi_to_picotron_pitch(note):
    """
    Convert MIDI note number to Picotron pitch value.
    MIDI notes range from 0-127, Picotron pitches from 0-120, offset by -12.
    Clamp to 0-120 to avoid out-of-range values.
    """
    pitch = note - 12
    return max(0, min(120, pitch))

def send_message(msg_str):
    """
    Thread-safe function to send a message over the TCP socket.
    If connected, send immediately; otherwise, queue the message.
    Appends a newline and comma as delimiter for the receiver.
    """
    if connected_event.is_set() and client_socket:
        try:
            client_socket.send(msg_str.encode('utf-8') + b'\n,')
            print(f"Sent: {msg_str} | Timestamp: {time.time()}")
        except Exception as e:
            print(f"Send error: {e} | Failed message: {msg_str}")
    else:
        send_queue.append(msg_str)
        print(f"Queued (not connected): {msg_str} | Queue size: {len(send_queue)}")

def flush_queue():
    """
    Flush all queued messages once connection is established.
    Sends messages in FIFO order.
    """
    while send_queue:
        send_message(send_queue.popleft())
    print("Queue flushed successfully.")

def handle_midi_messages(inport):
    """
    Thread function to handle incoming MIDI messages from the input port.
    Processes each message, logs it, prints verbose details, and sends formatted strings to Jazz Hands.
    Supports note_on/off, control_change, pitchwheel, program_change, channel_pressure, polytouch, and now sysex.
    For global messages like CC, pitchwheel, etc., applies to all active channels.
    For sysex, sends the data bytes as a comma-separated string for easy parsing.
    """
    print("MIDI handler thread started—waiting for notes (connect Jazz Hands to enable sends)...")
    global active_notes
    for msg in inport:
        # Log the full message to file
        log_file.write(str(msg) + "\n")
        log_file.flush()  # Ensure data is written immediately

        # Verbose output: Print full message details
        print(f"Received MIDI msg: {msg} | Type: {msg.type} | Channel: {getattr(msg, 'channel', 'N/A')} | Timestamp: {time.time()}")

        if msg.type == 'note_on' and msg.velocity > 0:
            note = msg.note
            pitch = midi_to_picotron_pitch(note)
            vel = int((msg.velocity / 127) * 255)
            channel = get_free_channel()
            if channel is not None:
                msg_str = f"NOTE_ON:{note}:{vel}:{channel}"
                send_message(msg_str)
                active_notes[note] = channel
                channels_in_use.add(channel)
                print(f"Processed NOTE_ON: Note={note}, Pitch={pitch}, Velocity={vel}, Channel={channel} | Active notes: {len(active_notes)}")
            else:
                print(f"Warning: No free channel for note {note}—dropping. | Channels in use: {channels_in_use}")
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            note = msg.note
            if note in active_notes:
                channel = active_notes[note]
                msg_str = f"NOTE_OFF:{note}:{channel}"
                send_message(msg_str)
                del active_notes[note]
                release_channel(channel)
                print(f"Processed NOTE_OFF: Note={note}, Channel={channel} | Active notes: {len(active_notes)}")
            else:
                print(f"Warning: NOTE_OFF for {note} but not active—ignoring. | Active notes: {active_notes}")
        elif msg.type == 'control_change':
            control = msg.control
            value = msg.value
            print(f"Processed CONTROL_CHANGE: Control={control}, Value={value} | Applying to {len(channels_in_use)} active channels")
            for channel in list(channels_in_use):
                msg_str = f"CC:{channel}:{control}:{value}"
                send_message(msg_str)
                break
            msg_str = f"CC:1:{control}:{value}"
            send_message(msg_str)
        elif msg.type == 'pitchwheel':
            pitch = msg.pitch
            print(f"Processed PITCHWHEEL: Pitch={pitch} (-8192 to 8191) | Applying to {len(channels_in_use)} active channels")
            for channel in list(channels_in_use):
                msg_str = f"PITCHWHEEL:{channel}:{pitch}"
                send_message(msg_str)
                break
            msg_str = f"PITCHWHEEL:1:{pitch}"
            send_message(msg_str)
        elif msg.type == 'program_change':
            program = msg.program
            print(f"Processed PROGRAM_CHANGE: Program={program} | Applying to {len(channels_in_use)} active channels")
            for channel in list(channels_in_use):
                msg_str = f"PROGRAM:{channel}:{program}"
                send_message(msg_str)
                break
            msg_str = f"PROGRAM:1:{program}"
            send_message(msg_str)
        elif msg.type == 'channel_pressure':
            value = msg.value
            print(f"Processed CHANNEL_PRESSURE (Aftertouch): Value={value} | Applying to {len(channels_in_use)} active channels")
            for channel in list(channels_in_use):
                msg_str = f"AFTERTOUCH:{channel}:{value}"
                send_message(msg_str)
        elif msg.type == 'polytouch':
            note = msg.note
            value = msg.value
            if note in active_notes:
                channel = active_notes[note]
                msg_str = f"POLYTOUCH:{channel}:{note}:{value}"
                send_message(msg_str)
                print(f"Processed POLYTOUCH: Note={note}, Value={value}, Channel={channel}")
            else:
                print(f"Warning: POLYTOUCH for {note} but not active—ignoring. | Active notes: {active_notes}")
        elif msg.type == 'sysex':
            data_str = ','.join(str(byte) for byte in msg.data)
            msg_str = f"SYSEX:{data_str}"
            send_message(msg_str)
            print(f"Processed SYSEX: Data bytes={list(msg.data)} (length={len(msg.data)}) | Sent as: {msg_str}")
        else:
            print(f"Ignored MIDI msg type: {msg.type} | Full msg: {msg}")

def monitor_ports():
    """
    Thread function to monitor MIDI port changes.
    Checks every 2 seconds for added or removed devices and prints notifications.
    """
    print("Port monitor thread started—checking for device changes...")
    last_ports = set(mido.get_input_names())
    while True:
        time.sleep(2)
        current_ports = set(mido.get_input_names())
        if current_ports != last_ports:
            added = current_ports - last_ports
            removed = last_ports - current_ports
            if added:
                print(f"*** MIDI devices connected: {added} *** | Timestamp: {time.time()}")
            if removed:
                print(f"*** MIDI devices disconnected: {removed} *** | Timestamp: {time.time()}")
            last_ports = current_ports

def tcp_accept_thread():
    """
    Thread function for accepting TCP connection from Jazz Hands.
    Listens on HOST:PORT, accepts one client, sets connection event, flushes queue.
    Then enters receive loop to echo any data from client (for debugging).
    Cleans up resources on disconnect or error.
    """
    global client_socket, connected_event
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Listening for Jazz Hands on {HOST}:{PORT}...")
    client_socket, addr = server_socket.accept()
    print(f"Connected by Jazz Hands: {addr} | Timestamp: {time.time()}")
    print(f"Active notes: {active_notes} | Channels in use: {channels_in_use}")
    connected_event.set()
    flush_queue()  # Send any pre-connect msgs
    # Receive loop for client data
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                print("Jazz Hands disconnected—exiting.")
                break
            if data.strip():
                print(f"Received from Jazz Hands: {data.decode('utf-8').strip()} | Timestamp: {time.time()}")
    except Exception as e:
        print(f"Server error: {e} | Timestamp: {time.time()}")
    finally:
        if inport:
            inport.close()
            print("MIDI input port closed.")
        if client_socket:
            client_socket.close()
            print("Client socket closed.")
        server_socket.close()
        print("Server socket closed.")
        log_file.close()
        print("Log file closed.")
        print("MIDI Bridge closed.")

# Startup sequence
print("Starting MIDI Bridge... | Timestamp: {time.time()}")
threading.Thread(target=tcp_accept_thread, daemon=True).start()
time.sleep(1)  # Brief delay to allow accept thread to bind socket

# Start MIDI port monitor thread
threading.Thread(target=monitor_ports, daemon=True).start()

# Initialize MIDI input
try:
    available_ports = mido.get_input_names()
    print(f"Available MIDI inputs: {available_ports}")
    port_name = None
    for port in available_ports:
        if 'Code 49' in port.upper():  # Prioritize exact match for Donner N-32 device
            port_name = port
            break
    port_name = port_name or available_ports[4] if available_ports else None
    if port_name:
        inport = open_input(port_name)
        print(f"Listening to MIDI input: {inport.name}")
        threading.Thread(target=handle_midi_messages, args=(inport,), daemon=True).start()
    else:
        print("No MIDI inputs found—plug in Donner N-32.")
except Exception as e:
    print(f"MIDI error: {e}. Check device.")

# Main thread idle loop for status printing and keeping program alive
try:
    while True:
        time.sleep(1)
        if connected_event.is_set():
            print(f"Status: Connected, Queue size: {len(send_queue)}, Active notes: {len(active_notes)}, Channels in use: {channels_in_use}")
        time.sleep(4)  # Print status every 5 seconds when connected
except KeyboardInterrupt:
    print("\nShutting down via Ctrl+C... | Timestamp: {time.time()}")
    log_file.close()
