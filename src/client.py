import socket
import tkinter as tk
from tkinter import font, ttk, messagebox, simpledialog
import threading
import requests
from PIL import Image, ImageTk
from PIL import ImageSequence
import io
import random
import json

PORT = 12345

class AlertClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.sent_count = 0
        self.received_count = 0
        self.username = "Anonymous"
        self.other_clients = []  # List of other connected clients
        self.target_client_id = None  # For targeted messages
        
        # Alert definitions (same as original)
        self.alerts = {
            'STOP': {
                'message': "Stop Scrolling! 😊",
                'bg': "#ff4500",
                'gif_url': 'https://media1.tenor.com/m/DafLbvYgt50AAAAC/trump-donald-trump.gif'
            },
            'COLD': {
                'message': "Turning off the AC, it's freezing! ❄️🥶❄️",
                'bg': "#1e90ff",
                'gif_url': 'https://media1.tenor.com/m/ShXWuFDDZ8wAAAAd/vtactor007-rwmartin.gif'
            },
            'ALERT1': {
                'message': "Working hard!",
                'bg': "#00ff00",
                'gif_url': 'https://media1.tenor.com/m/yHhqdtTladoAAAAC/cat-typing-typing.gif'
            },
            'ALERT2': {
                'message': "Hardly working!",
                'bg': "#ffff00",
                'gif_url': 'https://media1.tenor.com/m/3pwRCgEnqN8AAAAC/sleeping-at-work-fail.gif'
            },
            'ALERT3': {
                'message': "Ansys!",
                'bg': "#ff00ff",
                'gif_url': 'https://media1.tenor.com/m/7zrtEDHtArcAAAAC/ronswanson-parksandrec.gif'
            },
        }
    
    def connect_to_server(self, host='127.0.0.1'):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, PORT))
            self.connected = True
            print(f"Connected to server at {host}:{PORT}")
            
            # Start receiver thread
            receiver_thread = threading.Thread(target=self.receiver, daemon=True)
            receiver_thread.start()
            
            # Request client list
            self.request_client_list()
            
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            return False
    
    def receiver(self):
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    message_data = json.loads(data)
                    self.process_received_message(message_data)
                except json.JSONDecodeError:
                    # Handle legacy messages if any
                    print(f"Received non-JSON data: {data}")
                    
            except Exception as e:
                if self.connected:
                    print(f"Receiver error: {e}")
                break
        
        self.connected = False
        if hasattr(self, 'root'):
            self.root.after(0, self.on_disconnected)
    
    def process_received_message(self, message_data):
        message_type = message_data.get('type')
        
        if message_type == 'CUSTOM':
            # Custom alert
            message = message_data['message']
            bg = message_data['bg']
            gif_url = message_data.get('gif_url')
            sender = message_data.get('sender_username', 'Unknown')
            
            self.received_count += 1
            self.root.after(0, lambda: self.show_popup(f"From {sender}:\n{message}", bg, gif_url))
            self.root.after(0, self.update_counters)
            
        elif message_type == 'LEGACY_ALERT':
            # Legacy alert (STOP, COLD, etc.)
            alert_type = message_data['alert_type']
            sender = message_data.get('sender_username', 'Unknown')
            
            if alert_type in self.alerts:
                info = self.alerts[alert_type]
                self.received_count += 1
                self.root.after(0, lambda: self.show_popup(f"From {sender}:\n{info['message']}", info['bg'], info['gif_url']))
                self.root.after(0, self.update_counters)
                
        elif message_type == 'CLIENT_LIST_RESPONSE':
            # Update client list
            self.other_clients = message_data['clients']
            self.root.after(0, self.update_client_dropdown)
    
    def request_client_list(self):
        if self.connected:
            request = {'type': 'CLIENT_LIST_REQUEST'}
            self.send_message(request)
    
    def send_message(self, data):
        if self.connected:
            try:
                message = json.dumps(data)
                self.socket.send(message.encode('utf-8'))
                return True
            except Exception as e:
                print(f"Failed to send message: {e}")
                return False
        return False
    
    def send_alert(self, alert_type):
        self.sent_count += 1
        
        if self.connected:
            # Send to server for broadcasting/targeting
            self.socket.send(alert_type.encode('utf-8'))
        else:
            # Dev mode - show locally
            info = self.alerts[alert_type]
            self.show_popup(info['message'], info['bg'], info['gif_url'])
        
        self.update_counters()
    
    def send_custom(self, msg, gif):
        if not msg or msg == "Enter custom message":
            print("Skipping send_custom - invalid message")
            return
        
        bg = random.choice(['#ff4500', '#1e90ff', '#00ff00', '#ffff00', '#ff00ff'])
        gif_url = gif if gif != "GIF URL (optional)" else None
        
        self.sent_count += 1
        
        if self.connected:
            custom_data = {
                'type': 'CUSTOM',
                'message': msg,
                'bg': bg,
                'gif_url': gif_url,
                'target_id': self.target_client_id  # None for broadcast, specific ID for targeted
            }
            self.send_message(custom_data)
        else:
            # Dev mode - show locally
            self.show_popup(msg, bg, gif_url)
        
        self.update_counters()
        
        # Clear entries
        self.msg_entry.delete(0, tk.END)
        self.msg_entry.insert(0, "Enter custom message")
        self.gif_entry.delete(0, tk.END)
        self.gif_entry.insert(0, "GIF URL (optional)")
    
    def set_username(self):
        new_username = simpledialog.askstring("Username", "Enter your username:", initialvalue=self.username)
        if new_username:
            self.username = new_username
            if self.connected:
                username_data = {
                    'type': 'SET_USERNAME',
                    'username': new_username
                }
                self.send_message(username_data)
            
            # Update window title
            self.root.title(f"Alert App - {self.username}")
    
    def on_target_changed(self, event=None):
        selection = self.target_var.get()
        if selection == "All Clients":
            self.target_client_id = None
        else:
            # Extract client ID from selection
            for client in self.other_clients:
                if f"{client['username']} (ID: {client['id']})" == selection:
                    self.target_client_id = client['id']
                    break
    
    def update_client_dropdown(self):
        # Update the dropdown with connected clients
        client_options = ["All Clients"]
        for client in self.other_clients:
            client_options.append(f"{client['username']} (ID: {client['id']})")
        
        self.target_dropdown['values'] = client_options
        if not self.target_var.get() in client_options:
            self.target_var.set("All Clients")
        
        # Update status label
        self.status_var.set(f"Connected clients: {len(self.other_clients)}")
    
    def on_disconnected(self):
        messagebox.showwarning("Disconnected", "Connection to server lost!")
        self.status_var.set("Disconnected")
        self.target_dropdown['values'] = ["All Clients"]
        self.target_var.set("All Clients")
    
    def wrap_text(self, text, font_obj, max_width):
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
    
    def show_popup(self, message, bg_color="#ff4500", gif_url=None):
        popup = tk.Toplevel(self.root)
        popup.title("ALERT!")
        
        # Make it big and center it
        width = 800
        height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        popup.attributes('-topmost', True)
        popup.focus_force()
        popup.grab_set()
        popup.lift()
        
        # Canvas for background
        canvas = tk.Canvas(popup, bg=bg_color, highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        # Handle GIF background
        if gif_url:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(gif_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    gif_data = io.BytesIO(response.content)
                    im = Image.open(gif_data)
                    img_w, img_h = im.size
                    ratio = max(width / img_w, height / img_h)
                    new_w = int(img_w * ratio)
                    new_h = int(img_h * ratio)
                    
                    resized_frames = []
                    for frame in ImageSequence.Iterator(im):
                        frame = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        resized_frames.append(ImageTk.PhotoImage(frame))
                    
                    if resized_frames:
                        duration = im.info.get('duration', 100)
                        image_id = canvas.create_image(width / 2, height / 2, anchor='center')
                        
                        def update_gif(ind=0):
                            if popup.winfo_exists():
                                frame = resized_frames[ind]
                                canvas.itemconfig(image_id, image=frame)
                                canvas.image = frame
                                ind = (ind + 1) % len(resized_frames)
                                popup.after(duration, update_gif, ind)
                        
                        update_gif()
                        canvas.frames = resized_frames
                        
            except Exception as e:
                print(f"Error loading GIF: {e}")
        
        # Message text with shadow
        label_font = font.Font(family="Arial", size=36, weight="bold")
        lines = self.wrap_text(message, label_font, width - 100)
        y = 100
        linespace = label_font.metrics("linespace")
        for line in lines:
            canvas.create_text(width / 2 + 2, y + 2, text=line, font=label_font, fill="black", anchor='center')
            canvas.create_text(width / 2, y, text=line, font=label_font, fill="white", anchor='center')
            y += linespace
        
        # OK button
        button_font = font.Font(family="Arial", size=20)
        button = tk.Button(popup, text="OK", command=popup.destroy, font=button_font,
                           bg="#32cd32", fg="white", activebackground="#228b22", padx=30, pady=15)
        canvas.create_window(width / 2, height - 80, window=button, anchor='center')
        
        # Snowfall effect for cold alerts
        if "freezing" in message.lower() or "cold" in message.lower():
            snowflakes = []
            for _ in range(50):
                x = random.randint(0, width)
                y = random.randint(0, height)
                size = random.randint(2, 5)
                flake = canvas.create_oval(x, y, x + size, y + size, fill="white", outline="")
                speed = random.uniform(1, 3)
                snowflakes.append((flake, speed))
            
            def animate_snow():
                if popup.winfo_exists():
                    for flake, speed in snowflakes:
                        canvas.move(flake, random.uniform(-1, 1), speed)
                        pos = canvas.coords(flake)
                        if pos and len(pos) >= 4 and pos[3] > height:
                            canvas.move(flake, 0, -height - size)
                            canvas.move(flake, random.randint(-50, 50), 0)
                    popup.after(50, animate_snow)
            
            animate_snow()
    
    def update_counters(self):
        self.my_received_var.set(f"Alerts Received: {self.received_count}")
        self.opponent_received_var.set(f"Alerts Sent: {self.sent_count}")
    
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title(f"Alert App - {self.username}")
        self.root.geometry("1200x900")
        self.root.configure(bg="#f0f8ff")
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', foreground='#ff4500', background='#f0f8ff')
        
        # Fonts
        title_font = font.Font(family="Arial", size=16, weight="bold")
        button_font = font.Font(family="Arial", size=12)
        
        # Title and connection info
        title_frame = tk.Frame(self.root, bg="#f0f8ff")
        title_frame.pack(pady=10)
        
        title_label = ttk.Label(title_frame, text="Multi-User Alert App", font=title_font)
        title_label.pack()
        
        # Username and connection controls
        control_frame = tk.Frame(self.root, bg="#f0f8ff")
        control_frame.pack(pady=5)
        
        tk.Button(control_frame, text="Set Username", command=self.set_username, 
                 bg="#4CAF50", fg="white", font=button_font, padx=10).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="Refresh Clients", command=self.request_client_list,
                 bg="#2196F3", fg="white", font=button_font, padx=10).pack(side='left', padx=5)
        
        # Status and counters
        self.status_var = tk.StringVar(value="Connecting...")
        self.my_received_var = tk.StringVar(value="Alerts Received: 0")
        self.opponent_received_var = tk.StringVar(value="Alerts Sent: 0")
        
        ttk.Label(self.root, textvariable=self.status_var).pack(pady=2)
        ttk.Label(self.root, textvariable=self.my_received_var).pack(pady=2)
        ttk.Label(self.root, textvariable=self.opponent_received_var).pack(pady=2)
        
        # Target selection
        target_frame = tk.Frame(self.root, bg="#f0f8ff")
        target_frame.pack(pady=10)
        
        tk.Label(target_frame, text="Send to:", bg="#f0f8ff", font=button_font).pack(side='left', padx=5)
        
        self.target_var = tk.StringVar(value="All Clients")
        self.target_dropdown = ttk.Combobox(target_frame, textvariable=self.target_var, 
                                          values=["All Clients"], state="readonly", width=25)
        self.target_dropdown.pack(side='left', padx=5)
        self.target_dropdown.bind('<<ComboboxSelected>>', self.on_target_changed)
        
        # Custom message frame
        custom_frame = tk.Frame(self.root, bg="#f0f8ff")
        custom_frame.pack(pady=15)
        
        self.msg_entry = tk.Entry(custom_frame, width=35, font=button_font)
        self.msg_entry.pack(side='left', padx=5)
        self.msg_entry.insert(0, "Enter custom message")
        self.msg_entry.bind("<FocusIn>", lambda e: self.msg_entry.delete(0, tk.END) if self.msg_entry.get() == "Enter custom message" else None)
        self.msg_entry.bind("<FocusOut>", lambda e: self.msg_entry.insert(0, "Enter custom message") if not self.msg_entry.get() else None)
        
        self.gif_entry = tk.Entry(custom_frame, width=35, font=button_font)
        self.gif_entry.pack(side='left', padx=5)
        self.gif_entry.insert(0, "GIF URL (optional)")
        self.gif_entry.bind("<FocusIn>", lambda e: self.gif_entry.delete(0, tk.END) if self.gif_entry.get() == "GIF URL (optional)" else None)
        self.gif_entry.bind("<FocusOut>", lambda e: self.gif_entry.insert(0, "GIF URL (optional)") if not self.gif_entry.get() else None)
        
        tk.Button(custom_frame, text="Send Custom", command=lambda: self.send_custom(self.msg_entry.get(), self.gif_entry.get()),
                 bg="#FF9800", fg="white", font=button_font, padx=15, pady=5).pack(side='left', padx=5)
        
        # Alert buttons
        button_frame = tk.Frame(self.root, bg="#f0f8ff")
        button_frame.pack(pady=20)
        
        # Row 1
        row1 = tk.Frame(button_frame, bg="#f0f8ff")
        row1.pack(pady=5)
        
        tk.Button(row1, text="Stop Scrolling! 😊", command=lambda: self.send_alert('STOP'),
                 bg="#ff4500", fg="white", font=button_font, padx=20, pady=10, width=20).pack(side='left', padx=10)
        
        tk.Button(row1, text="It's Cold! ❄️", command=lambda: self.send_alert('COLD'),
                 bg="#1e90ff", fg="white", font=button_font, padx=20, pady=10, width=20).pack(side='left', padx=10)
        
        # Row 2  
        row2 = tk.Frame(button_frame, bg="#f0f8ff")
        row2.pack(pady=5)
        
        tk.Button(row2, text="Working Hard!", command=lambda: self.send_alert('ALERT1'),
                 bg="#00ff00", fg="white", font=button_font, padx=20, pady=10, width=20).pack(side='left', padx=10)
        
        tk.Button(row2, text="Hardly Working!", command=lambda: self.send_alert('ALERT2'),
                 bg="#ffff00", fg="black", font=button_font, padx=20, pady=10, width=20).pack(side='left', padx=10)
        
        # Row 3
        row3 = tk.Frame(button_frame, bg="#f0f8ff")
        row3.pack(pady=5)
        
        tk.Button(row3, text="Ansys!", command=lambda: self.send_alert('ALERT3'),
                 bg="#ff00ff", fg="white", font=button_font, padx=20, pady=10, width=20).pack(side='left', padx=10)
        
        return self.root
    
    def run(self, server_host='127.0.0.1', dev_mode=False):
        # Create GUI first
        root = self.create_gui()
        
        if not dev_mode:
            # Try to connect to server
            if not self.connect_to_server(server_host):
                self.status_var.set("Failed to connect - Running in offline mode")
            else:
                self.status_var.set("Connected to server")
        else:
            self.status_var.set("Developer Mode - Offline")
        
        # Start the GUI
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        root.mainloop()
    
    def on_closing(self):
        if self.connected:
            self.connected = False
            try:
                self.socket.close()
            except:
                pass
        self.root.destroy()

def main():
    client = AlertClient()
    
    print("Alert App Client")
    print("================")
    mode = input("Select mode:\n1. Connect to server\n2. Developer mode (offline)\nEnter choice (1/2): ").strip()
    
    if mode == '2':
        print("Starting in developer mode...")
        client.run(dev_mode=True)
    else:
        server_host = input("Enter server IP (press Enter for localhost): ").strip()
        if not server_host:
            server_host = '127.0.0.1'
        
        username = input("Enter your username (optional): ").strip()
        if username:
            client.username = username
        
        print(f"Connecting to server at {server_host}...")
        client.run(server_host=server_host, dev_mode=False)

if __name__ == "__main__":
    main()