import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
import json
import os
import socket
# Use the server's actual IP address
HOST = '192.168.137.76'  # Example: '192.168.1.100'
PORT = 65432  # Same port as used by the server

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Define logo image
img_loc = "icon.png"
# Load YOLOv8 model
model = YOLO('../poacherdetection.pt')

# Define a video capture object
vid = cv2.VideoCapture(0)

if not vid.isOpened():
    print("Error: Could not open video stream from camera")
    exit()

# Declare the width and height
width, height = 1280, 720
vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

# Updated color scheme based on ECO GUARD icon
bg_color = "#3b2f2f"  # Deep brown background
button_bg = "#2e8b57"  # Dark green for buttons
button_fg = "#ffd700"  # Gold for button text
frame_bg = "#faebd7"  # Light cream frame background
highlight_color = "#ff8c00"  # Burnt orange for hover effect

button_style = {
    "bg": button_bg,
    "fg": button_fg,
    "font": ("Arial", 14, "bold"),
    "activebackground": highlight_color,
    "bd": 2,
    "relief": "raised"
}

label_style = {
    "bg": frame_bg,
    "fg": bg_color,
    "font": ("Arial", 12, "bold")
}

# Initialize global variables for tracking crossings
crossing_counts = {"ranger": 0, "poacher": 0}
previous_positions = {}

# Create a GUI app
app = tk.Tk()
app.minsize(1280, 720)
app.title('YOLOv8 Poacher Detection App')
app.configure(bg=bg_color)
app.bind('<Escape>', lambda e: app.quit())

# Add icon image (now from your ECO GUARD image)
img = tk.PhotoImage(file=img_loc)
app.iconphoto(False, img)

# Create a canvas for displaying the video feed
canvas = tk.Canvas(app, width=width, height=height, bg=bg_color)
detection_label = tk.Label(app, text="Detection Info: None", bg=frame_bg, fg=bg_color, font=("Arial", 14, "bold"))
detection_label.pack(pady=20)  # Place it below the canvas
detection_label.pack_forget()

# Directory for saving screenshots and JSON files
save_directory = "screenshots"
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# Crossing count display on bottom-right corner
crossing_label = tk.Label(app, text="Ranger Crossings: 0, Poacher Crossings: 0", bg=frame_bg, fg=bg_color, font=("Arial", 12, "bold"))
crossing_label.place(relx=1.0, rely=1.0, anchor='se')  # Position it at bottom-right

def update_crossing_counts(cls, current_position):
    """Track how many times a 'ranger' or 'poacher' has crossed left to right or right to left."""
    if cls not in previous_positions:
        previous_positions[cls] = current_position
        return

    prev_position = previous_positions[cls]
    previous_positions[cls] = current_position

    # Define crossing logic (e.g., has the object crossed left to right or vice versa)
    if current_position[0] > prev_position[0]:  # Object moved right
        crossing_counts[cls] += 1
    elif current_position[0] < prev_position[0]:  # Object moved left
        crossing_counts[cls] += 1

def update_crossing_label():
    """Update the display label for how many times 'ranger' and 'poacher' have crossed."""
    crossing_text = f"Ranger Crossings: {crossing_counts['ranger']}, Poacher Crossings: {crossing_counts['poacher']}"
    crossing_label.config(text=crossing_text)

def save_screenshot():
    global annotated_frame, detected_classes
    
    if annotated_frame is not None:
        # Save annotated image
        image_filename = os.path.join(save_directory, "screenshot.png")
        cv2.imwrite(image_filename, annotated_frame)
        print(f"Screenshot saved as {image_filename}")

        # Save detected class info as JSON
        detected_counts = {cls: detected_classes.count(cls) for cls in set(detected_classes)}
        json_filename = os.path.join(save_directory, "detected_info.json")
        with open(json_filename, 'w') as f:
            json.dump(detected_counts, f, indent=4)
        print(f"Detected info saved as {json_filename}")
    else:
        print("No frame to save!")

def update_canvas():
    global after_id, annotated_frame, detected_classes
    ret, frame = vid.read()
    if not ret:
        print("Error: Failed to capture image")
        return

    results1 = model(frame)
    filtered_results1 = results1[0].boxes

    detected_classes = []
    annotated_frame = frame.copy()
    for box in filtered_results1:
        xyxy = box.xyxy[0].cpu().numpy()
        conf = box.conf[0].cpu().numpy()
        if conf > 0.5:
            cls = int(box.cls[0].cpu().numpy())
            class_name = model.names[cls]
            cv2.rectangle(annotated_frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
            label = f'{model.names[cls]} {conf:.2f}'
            detected_classes.append(model.names[cls])
            cv2.putText(annotated_frame, label, (int(xyxy[0]), int(xyxy[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Check for 'ranger' or 'poacher' and update crossing counts
            if class_name in crossing_counts:
                update_crossing_counts(class_name, xyxy[:2])  # Use x, y coordinates
                # **Send a message to the server when a poacher is detected**
                if class_name == 'poacher':
                    try:
                        message = "Alert"
                        client_socket.sendall(message.encode())
                    except socket.timeout:
                        print("Timeout: No response from server.")
                    except Exception as e:
                        print(f"Error sending message to server: {e}")
                    finally:
                        continue

    # Update the label with crossing count
    update_crossing_label()

    rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
    captured_image = Image.fromarray(rgb_frame)
    photo_image = ImageTk.PhotoImage(image=captured_image)

    canvas.create_image(0, 0, anchor=tk.NW, image=photo_image)
    canvas.photo_image = photo_image
    # Update the detection label
    if detected_classes:
        detection_info = f"Detected: {', '.join(detected_classes)} (Total: {len(detected_classes)})"
    else:
        detection_info = "No objects detected"
    
    detection_label.config(text=detection_info)  # Update the label with detection info
    detection_label.pack(pady=20)
    after_id = canvas.after(10, update_canvas)

def start_camera():
    canvas.pack(pady=50)
    update_canvas()
    app.title('Camera ON')
    image_label.pack_forget()
    button1.pack_forget()
    button2.pack()
    save_button.pack()

def stop_camera():
    app.title('YOLOv8 Poacher Detection App')
    detection_label.pack_forget()
    image_label.pack(pady=120)
    canvas.after_cancel(after_id)
    canvas.delete("all")
    canvas.pack_forget()
    button2.pack_forget()
    save_button.pack_forget()
    button1.pack()

def on_hover(event, button):
    button.config(bg=highlight_color)

def off_hover(event, button):
    button.config(bg=button_bg)

def create_tooltip(widget, text):
    tooltip = tk.Toplevel(widget)
    tooltip.withdraw()
    tooltip.overrideredirect(True)
    label = tk.Label(tooltip, text=text, bg="yellow", fg="black", font=("Arial", 10))
    label.pack()

    def show_tooltip(event):
        tooltip.geometry(f"+{event.x_root + 20}+{event.y_root}")
        tooltip.deiconify()

    def hide_tooltip(event):
        tooltip.withdraw()

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to exit the app?"):
        vid.release()  # Release the video capture object
        app.quit()

# Smooth transition for UI elements
def smooth_transition():
    alpha = 0.0
    while alpha < 1.0:
        app.attributes('-alpha', alpha)
        app.update()
        alpha += 0.01

smooth_transition()

# Create buttons and labels
image = tk.PhotoImage(file=img_loc)
image_label = tk.Label(app, image=image, bg=bg_color)
image_label.pack(pady=120)

button1 = tk.Button(app, text="Open Camera", command=start_camera, **button_style)
button2 = tk.Button(app, text="Stop Camera", command=stop_camera, **button_style)
save_button = tk.Button(app, text="Save", command=save_screenshot, **button_style)

button1.pack()

# Hover effects
button1.bind("<Enter>", lambda event: on_hover(event, button1))
button1.bind("<Leave>", lambda event: off_hover(event, button1))
button2.bind("<Enter>", lambda event: on_hover(event, button2))
button2.bind("<Leave>", lambda event: off_hover(event, button2))
save_button.bind("<Enter>", lambda event: on_hover(event, save_button))
save_button.bind("<Leave>", lambda event: off_hover(event, save_button))

# Tooltips for buttons
create_tooltip(button1, "Open the camera to start detecting")
create_tooltip(button2, "Stop the camera")
create_tooltip(save_button, "Save the current frame and detected objects")

app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
