import soundfile as sf
import numpy as np
import collections
import threading
import tkinter as tk
import serial
import struct
import time
import os
# Global variables
notfirst_time = False
is_recording = False
recording_thread = None  # Added to keep track of the recording thread
pcm_buffer = collections.deque(maxlen=16000)
click_start_time = 0
duration = 0
# Setup GUI
root = tk.Tk()
root.geometry("300x200")
root.title("RP2040 Audio Recorder")

# Recording functions
def record_thread():
    global pcm_buffer
    while is_recording:
        data = ser.readline().strip()  # Adjust the number of bytes based on your data format
        pcm_buffer.append(data.decode())
        if len(pcm_buffer) == 16000:
            append_to_text(pcm_buffer)
            pcm_buffer.clear()

def write_wav():
    loaded_array = np.loadtxt('recording.txt', dtype=np.int32)
    sf.write('recording.wav', loaded_array, 8000, 'PCM_32')  # Adjust format if needed


def append_to_text(pcm_buffer):
    with open('recording.txt', 'a') as file:
        new_data = []
        hex_buffer = [hex_str for hex_str in pcm_buffer if hex_str]
        for hex_str in hex_buffer:
            # Check if hex_str is a valid 32-bit hex representation
            if len(hex_str) == 8:  # Assuming each hex_str should be 8 characters long (4 bytes)
                # Unpack 32-bit signed integer in big-endian byte order
                value = np.int32(struct.unpack('>l', bytes.fromhex(hex_str))[0])
                new_data.append(value)
            else:
                # Handle invalid hex_str (optional, depending on your requirements)
                print(f"Invalid hex string: {hex_str}")

        new_data = np.array(new_data, dtype='int32')
        np.savetxt(file, new_data, fmt='%d')

def start_recording():
    return threading.Thread(target=record_thread)

def toggle_recording():
    global is_recording
    global recording_thread
    global pcm_buffer
    global notfirst_time
    global click_start_time
    global duration
    duration = time.time() - click_start_time
    click_start_time = time.time()
    print("Time duration:" + str(duration))

    if notfirst_time:
        runChecking(duration)
        notfirst_time = False


    if is_recording:
        pcm_buffer.clear()
        is_recording = False
        btn['text'] = 'Start Recording'
        write_wav()
        print("Recording Saved...")
       
    else:
        notfirst_time = True
        pcm_buffer.clear()
        is_recording = True
        btn['text'] = 'Stop Recording'
        recording_thread = start_recording()
        recording_thread.start()
        print("Recording is in progress")
        print(recording_thread)
        
def runChecking(duration):
    btn['text'] = 'Saving...'
    if not os.path.exists('recording.txt'):
        open('recording.txt', 'w').close()

    while True:
        with open('recording.txt', 'r') as file:
            lines = file.readlines()
            num_entries = len(lines)
            seconds_recorded = (num_entries / 8000) -2

        print(f"Seconds recorded: {seconds_recorded} vs Duration: {duration}")
        if seconds_recorded >= duration:
            print("Recording duration reached. Stopping the loop.")
            return True
        time.sleep(1)

btn = tk.Button(root, text='Start Recording', command=toggle_recording)
btn.pack(pady=50)
btn.configure(
    bg="black",
    fg="white",
    borderwidth=10,  # Adjust the borderwidth for smooth corners
    relief=tk.FLAT  # Adjust the relief for smooth corners (options: FLAT, RAISED, SUNKEN, GROOVE, RIDGE)
)
# Create a serial connection (replace 'COM9' with the correct port)
ser = serial.Serial('COM14', 115200)

# Close the serial connection when done
root.protocol("WM_DELETE_WINDOW", lambda: [ser.close(), root.destroy()])
root.mainloop()