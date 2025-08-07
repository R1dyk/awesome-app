import socket
import tkinter as tk
from tkinter import font, ttk
import threading
import requests
from PIL import Image, ImageTk
from PIL import ImageSequence
import io
import random
import json

PORT = 12345

sent_count = 0
received_count = 0

alerts = {
    'STOP': {
        'message': "Stop Scrolling! 😊",
        'bg': "#ff4500",
        'gif_url': 'https://media1.tenor.com/m/DafLbvYgt50AAAAC/trump-donald-trump.gif'  # Valid GIF URL
    },
    'COLD': {
        'message': "Turning off the AC, it's freezing! ❄️🥶❄️",
        'bg': "#1e90ff",
        'gif_url': 'https://media1.tenor.com/m/ShXWuFDDZ8wAAAAd/vtactor007-rwmartin.gif'  # User's Home Alone GIF
    },
    'ALERT1': {
        'message': "Working hard!",
        'bg': "#00ff00",
        'gif_url': 'https://media1.tenor.com/m/yHhqdtTladoAAAAC/cat-typing-typing.gif'  # Add a GIF URL if desired
    },
    'ALERT2': {
        'message': "Hardly working!",
        'bg': "#ffff00",
        'gif_url': 'https://media1.tenor.com/m/3pwRCgEnqN8AAAAC/sleeping-at-work-fail.gif'  # Add a GIF URL if desired
    },
    'ALERT3': {
        'message': "Ansys!",
        'bg': "#ff00ff",
        'gif_url': 'https://media1.tenor.com/m/7zrtEDHtArcAAAAC/ronswanson-parksandrec.gif'  # Add a GIF URL if desired
    },
}

def start_server():
    s = socket.socket()
    s.bind(('', PORT))
    s.listen(1)
    print("Waiting for connection...")
    conn, addr = s.accept()
    print(f"Connected to {addr}")
    return conn

def start_client(host):
    s = socket.socket()
    s.connect((host, PORT))
    print(f"Connected to {host}")
    return s

def wrap_text(text, font_obj, max_width):
    lines = []
    words = text.split()
    current = ""
    for word in words:
        test = current + " " + word if current else word
        w = font_obj.measure(test)
        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def show_popup(message, bg_color="#ff4500", gif_url=None):
    print(f"DEBUG: show_popup starting with message: '{message}', bg: {bg_color}, gif: {gif_url}")  # NEW: Entry point check
    popup = tk.Toplevel(root)
    popup.title("ALERT!")
    
    # Make it big and center it
    width = 1000
    height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    popup.geometry(f"{width}x{height}+{x}+{y}")
    
    popup.attributes('-topmost', True)  # Always on top
    popup.focus_force()  # Force focus
    popup.grab_set()  # Grab input (modal)
    popup.lift()  # NEW: Lift it to the front, just in case
    print("DEBUG: Popup window created and attributes set")  # NEW: Did we make the window?
    
    # Use canvas for background GIF
    canvas = tk.Canvas(popup, bg=bg_color, highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    
    # GIF as background if provided (cover whole)
    gif_path = None
    frames = None
    if gif_url:
        print(f"DEBUG: Attempting to download GIF from {gif_url}")  # NEW: GIF fetch start
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(gif_url, headers=headers)
            if response.status_code == 200:
                gif_path = io.BytesIO(response.content)
            
        except Exception as e:
            print(f"Error downloading GIF: {e}")
        
    
    if gif_path:
        try:
            print("DEBUG: GIF downloaded successfully")  # NEW: Inside the if gif_path
            im = Image.open(gif_path)
            img_w, img_h = im.size
            ratio = max(width / img_w, height / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            resized_frames = []
            for frame in ImageSequence.Iterator(im):
                frame = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)
                resized_frames.append(ImageTk.PhotoImage(frame))
            frames = resized_frames
            duration = im.info.get('duration', 100)
            
            image_id = canvas.create_image(width / 2, height / 2, anchor='center')
            
            def update(ind=0):
                frame = frames[ind]
                canvas.itemconfig(image_id, image=frame)
                canvas.image = frame  # Keep reference
                ind = (ind + 1) % len(frames)
                popup.after(duration, update, ind)
            
            update()
            canvas.frames = frames  # Keep reference
            print("DEBUG: GIF frames resized and animation started")  # NEW: After update()
        
        except Exception as e:
            print(f"Error animating GIF: {e}")
    
    # Large message text with shadow and wrapping
    label_font = font.Font(family="Arial", size=48, weight="bold")
    lines = wrap_text(message, label_font, width - 100)
    y = 100
    linespace = label_font.metrics("linespace")
    for line in lines:
        canvas.create_text(width / 2 + 2, y + 2, text=line, font=label_font, fill="black", anchor='center')
        canvas.create_text(width / 2, y, text=line, font=label_font, fill="white", anchor='center')
        y += linespace
    
    # OK button
    button_font = font.Font(family="Arial", size=24)
    button = tk.Button(popup, text="OK", command=popup.destroy, font=button_font,
                       bg="#32cd32", fg="white", activebackground="#228b22", padx=40, pady=20)
    canvas.create_window(width / 2, height - 100, window=button, anchor='center')
    
    # Snowfall effect for cold popup
    if "freezing" in message.lower():
        snowflakes = []
        for _ in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(2, 5)
            flake = canvas.create_oval(x, y, x + size, y + size, fill="white", outline="")
            speed = random.uniform(1, 3)
            snowflakes.append((flake, speed))
        
        def animate_snow():
            for flake, speed in snowflakes:
                canvas.move(flake, random.uniform(-1, 1), speed)  # Slight wind
                pos = canvas.coords(flake)
                if pos[3] > height:
                    canvas.move(flake, 0, -height - size)
                    canvas.move(flake, random.randint(-50, 50), 0)
            popup.after(50, animate_snow)
        
        animate_snow()

def receiver(conn):
    while True:
        try:
            data = conn.recv(1024).decode()
            try:
                json_data = json.loads(data)
                if json_data.get('type') == 'CUSTOM':
                    message = json_data['message']
                    bg = json_data['bg']
                    gif_url = json_data['gif_url']
                    root.after(0, lambda m=message, c=bg, g=gif_url: show_popup(m, c, g))
                    root.after(0, update_counters)
            except json.JSONDecodeError:
                if data in alerts:
                    info = alerts[data]
                    if data == 'STOP':
                        global received_count
                        received_count += 1
                    root.after(0, lambda m=info['message'], c=info['bg'], g=info['gif_url']: show_popup(m, c, g))
                    root.after(0, update_counters)
        except:
            break

def send_alert(alert_type):
    print(f"DEBUG: send_alert called with alert_type: {alert_type}")  # NEW: See if we even get here
    global sent_count
    sent_count += 1
    if dev_mode:
        print(f"DEBUG: In dev_mode, looking up alert: {alert_type}")  # NEW: Confirm dev path
        info = alerts[alert_type]
        print(f"DEBUG: Got info: {info}")  # NEW: Dump the alert dict to check message/bg/gif
        if alert_type == 'STOP':
            global received_count
            received_count += 1
        show_popup(info['message'], info['bg'], info['gif_url'])  # Your direct call
        print("DEBUG: show_popup called in dev_mode")  # NEW: Did we try to show it?
    else:
        conn.send(alert_type.encode())
    update_counters()
    print("DEBUG: Counters updated after send_alert")  # NEW: Always runs, good sanity check

def send_custom(msg, gif):
    if not msg or msg == "Enter custom message":
        print("DEBUG: Skipping send_custom - invalid message")
        return  # Skip if no valid message
    bg = random.choice(['#ff4500', '#1e90ff', '#00ff00', '#ffff00', '#ff00ff'])
    gif = gif if gif != "GIF URL (optional)" else None
    print(f"DEBUG: send_custom with message: '{msg}', bg: {bg}, gif: {gif}")
    global sent_count
    sent_count += 1
    if dev_mode:
        show_popup(msg, bg, gif)
        print("DEBUG: show_popup called in dev_mode for custom")
    else:
        send_data = json.dumps({'type': 'CUSTOM', 'message': msg, 'bg': bg, 'gif_url': gif})
        conn.send(send_data.encode())
    update_counters()
    print("DEBUG: Counters updated after send_custom")
    # Clear entries
    msg_entry.delete(0, tk.END)
    msg_entry.insert(0, "Enter custom message")
    gif_entry.delete(0, tk.END)
    gif_entry.insert(0, "GIF URL (optional)")

# Setup connection
is_host = input("Are you the host? (y/n): ").strip().lower()
dev_mode = False
conn = None
if is_host == 'd':
    dev_mode = True
    print("Developer mode activated (secret).")
    is_host = 'y'  # Enable host features like cold button
elif is_host == 'y':
    conn = start_server()
else:
    #host = input("Enter remote IP: ").strip()
    host = '10.84.151.16'
    conn = start_client(host)

# Start receiver thread only if not dev_mode
if not dev_mode:
    thread = threading.Thread(target=receiver, args=(conn,))
    thread.daemon = True
    thread.start()

# GUI
root = tk.Tk()
style = ttk.Style()
style.theme_use('clam')  # Use 'clam' theme for better custom color support

root.title("Awesome App" if not dev_mode else "Dev Mode")
root.geometry("1000x800")  # Larger to fit more buttons
root.configure(bg="#f0f8ff")  # Light blue background

# Custom font
title_font = font.Font(family="Arial", size=14, weight="bold")
button_font = font.Font(family="Arial", size=12)

# Configure label style
style.configure('TLabel', foreground='#ff4500', background='#f0f8ff')

# Title label
title_label = ttk.Label(root, text="Awesome App", font=title_font)
title_label.pack(pady=10)

# Counter labels
my_received_var = tk.StringVar(value="My Alerts Received: 0")
opponent_received_var = tk.StringVar(value="Opponent's Alerts Received: 0")

my_label = ttk.Label(root, textvariable=my_received_var)
my_label.pack(pady=5)

opp_label = ttk.Label(root, textvariable=opponent_received_var)
opp_label.pack(pady=5)

def update_counters():
    my_received_var.set(f"Hard worker: {received_count}")
    opponent_received_var.set(f"Favourite HiWi: {sent_count}")

update_counters()

# New frame for custom alert
custom_frame = tk.Frame(root, bg="#f0f8ff")  # Match the root bg for style points
custom_frame.pack(pady=10)

# Message entry
msg_entry = tk.Entry(custom_frame, width=30)
msg_entry.pack(side='left', padx=5)
msg_entry.insert(0, "Enter custom message")  # Placeholder text
msg_entry.bind("<FocusIn>", lambda e: msg_entry.delete(0, tk.END) if msg_entry.get() == "Enter custom message" else None)
msg_entry.bind("<FocusOut>", lambda e: msg_entry.insert(0, "Enter custom message") if not msg_entry.get() else None)

# GIF entry with placeholder
gif_entry = tk.Entry(custom_frame, width=30)
gif_entry.pack(side='left', padx=5)
gif_entry.insert(0, "GIF URL (optional)")  # Placeholder text
gif_entry.bind("<FocusIn>", lambda e: gif_entry.delete(0, tk.END) if gif_entry.get() == "GIF URL (optional)" else None)
gif_entry.bind("<FocusOut>", lambda e: gif_entry.insert(0, "GIF URL (optional)") if not gif_entry.get() else None)

# Send Custom button
send_custom_btn = ttk.Button(custom_frame, text="Send Custom", command=lambda: send_custom(msg_entry.get(), gif_entry.get()), style='Stop.TButton')
send_custom_btn.pack(side='left', padx=5)

# Configure button styles (fancy with more padding, rounded borders via focuscolor/width)
style.configure('Stop.TButton', background="#32cd32", foreground="white", font=button_font, padding=15, relief="flat", borderwidth=2, focusthickness=3, focuscolor="#228b22")
style.map('Stop.TButton', background=[('active', "#228b22")])

style.configure('Cold.TButton', background="blue", foreground="white", font=button_font, padding=15, relief="flat", borderwidth=2, focusthickness=3, focuscolor="darkblue")
style.map('Cold.TButton', background=[('active', "darkblue")])

style.configure('Alert1.TButton', background="#00ff00", foreground="white", font=button_font, padding=15, relief="flat", borderwidth=2, focusthickness=3, focuscolor="#008b00")
style.map('Alert1.TButton', background=[('active', "#008b00")])

style.configure('Alert2.TButton', background="#ffff00", foreground="black", font=button_font, padding=15, relief="flat", borderwidth=2, focusthickness=3, focuscolor="#cdcd00")
style.map('Alert2.TButton', background=[('active', "#cdcd00")])

style.configure('Alert3.TButton', background="#ff00ff", foreground="white", font=button_font, padding=15, relief="flat", borderwidth=2, focusthickness=3, focuscolor="#8b008b")
style.map('Alert3.TButton', background=[('active', "#8b008b")])

# Send Alert button
button = ttk.Button(root, text="Scrolling!", command=lambda: send_alert('STOP'), style='Stop.TButton')
button.pack(pady=20)

if is_host == 'y':
    cold_button = ttk.Button(root, text="It's Cold", command=lambda: send_alert('COLD'), style='Cold.TButton')
    cold_button.pack(pady=20)

# Extra buttons
alert1_button = ttk.Button(root, text="Working hard!", command=lambda: send_alert('ALERT1'), style='Alert1.TButton')
alert1_button.pack(pady=10)

alert2_button = ttk.Button(root, text="Hardly working!", command=lambda: send_alert('ALERT2'), style='Alert2.TButton')
alert2_button.pack(pady=10)

alert3_button = ttk.Button(root, text="Ansys!", command=lambda: send_alert('ALERT3'), style='Alert3.TButton')
alert3_button.pack(pady=10)

root.mainloop()

# Cleanup
if conn:
    conn.close()