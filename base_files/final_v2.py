import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
#define logo image
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

def update_canvas():
    global after_id
    ret, frame = vid.read()
    if not ret:
        print("Error: Failed to capture image")
        return

    results1 = model(frame)
    filtered_results1 = results1[0].boxes

    annotated_frame = frame.copy()
    for box in filtered_results1:
        xyxy = box.xyxy[0].cpu().numpy()
        conf = box.conf[0].cpu().numpy()
        if conf > 0.5:
            cls = int(box.cls[0].cpu().numpy())
            cv2.rectangle(annotated_frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
            label = f'{model.names[cls]} {conf:.2f}'
            cv2.putText(annotated_frame, label, (int(xyxy[0]), int(xyxy[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
    captured_image = Image.fromarray(rgb_frame)
    photo_image = ImageTk.PhotoImage(image=captured_image)

    canvas.create_image(0, 0, anchor=tk.NW, image=photo_image)
    canvas.photo_image = photo_image

    after_id = canvas.after(10, update_canvas)

def start_camera():
    canvas.pack(pady=50)
    update_canvas()
    app.title('Camera ON')
    image_label.pack_forget()
    button1.pack_forget()
    button2.pack()

def stop_camera():
    app.title('YOLOv8 Poacher Detection App')
    image_label.pack(pady=120)
    canvas.after_cancel(after_id)
    canvas.delete("all")
    canvas.pack_forget()
    button2.pack_forget()
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
button1.pack(pady=20)
button1.bind("<Enter>", lambda e: on_hover(e, button1))
button1.bind("<Leave>", lambda e: off_hover(e, button1))
create_tooltip(button1, "Click to open the camera feed")

button2 = tk.Button(app, text="Close Camera", command=stop_camera, **button_style)
button2.bind("<Enter>", lambda e: on_hover(e, button2))
button2.bind("<Leave>", lambda e: off_hover(e, button2))
create_tooltip(button2, "Click to close the camera feed")

# Exit button
tk.Button(app, text="Close", command=on_closing, **button_style).place(x=0, y=0)

# Start the Tkinter main loop
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()