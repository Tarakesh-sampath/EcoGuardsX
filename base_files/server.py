import socket
import tkinter as tk
import winsound  # For Windows sound; use pygame or playsound for cross-platform
import pickle

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
            conn.sendall("1".encode())
            image_size = int.from_bytes(conn.recv(4), 'big')
            data = b''
            while len(data) < image_size:
                packet = conn.recv(1024)
                if not packet:
                    break
                data += packet

            # Deserialize the image data
            image_buffer = pickle.loads(data)

            # Save the image on the server side (OpenCV)
            with open('saved_image/received_image.png', 'wb') as f:
                f.write(image_buffer)
            print(f"Received from client: {message}")
            
            # Check if the received message is an "alert"
            if "alert" in message.lower():
                show_alert(message)