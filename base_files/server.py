import socket
import tkinter as tk
from tkinter import messagebox
import winsound  # For Windows sound; use pygame or playsound for cross-platform

# Replace with the actual IP address of the server machine
HOST = '192.168.137.76'  # Example: '192.168.1.100'
PORT = 65432  # Keep the port same as before

# Function to play an alarm sound (For cross-platform, replace with pygame/playsound)
def play_alarm():
    winsound.Beep(2000, 2000)  # Frequency and duration of the beep (in ms)

# Function to trigger notification
def show_alert(message):
    # Initialize a Tkinter root window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Show the notification pop-up
    messagebox.showwarning("Alert", message)
    
    # Play the alarm sound
    play_alarm()
    
    # Close the Tkinter window
    root.destroy()

# Server code to listen and respond
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}")
    
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            message = data.decode()
            print(f"Received from client: {message}")
            
            # Check if the received message is an "alert"
            if "alert" in message.lower():
                show_alert(message)