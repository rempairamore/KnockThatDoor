#!/usr/bin/env python3
# KnockThatDoor - A port knocking utility for Windows
# Copyright (C) rempairamore
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Import necessary modules
import json
import os
import threading
import time
import sys
import socket
import subprocess
import traceback
import logging
from datetime import datetime
from PIL import Image, ImageTk
import pystray
import tkinter as tk
from tkinter import ttk, messagebox, font

# Helper function to determine if running as a bundled app
def is_bundled_app():
    return getattr(sys, 'frozen', False)

# Get the appropriate base directory based on runtime environment
def get_base_dir():
    if is_bundled_app():
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.realpath(__file__))

# Get resource path for bundled app or development
def get_resource_path(relative_path):
    base_dir = get_base_dir()
    path = os.path.join(base_dir, relative_path)
    print(f"Resolving resource path for: {relative_path}")
    print(f"Path: {path}")
    print(f"Path exists: {os.path.exists(path)}")
    return path

# Setup logging
base_dir = get_base_dir()
log_dir = os.path.join(base_dir, "log")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"knockthatdoor_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add console logging as well
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# Colors and styles
COLORS = {
    "bg": "#f0f0f0",           # Main background
    "card": "#ffffff",         # Card background
    "text": "#333333",         # Main text
    "text_light": "#777777",   # Secondary text
    "accent": "#4a86e8",       # Blue accent color
    "success": "#4CAF50",      # Green for success
    "warning": "#FF9800",      # Yellow/orange for warning/in-progress
    "error": "#F44336",        # Red for error
    "button": "#e6e6e6",       # Button background
    "button_hover": "#d9d9d9", # Button hover
    "slider_bg": "#e0e0e0",    # Slider background
    "menu_hover": "#f5f5f5",   # Menu hover background
    "close_button": "#ff5252"  # Close button hover color
}

# For rounded corners and other custom styles
class RoundedButton(tk.Button):
    def __init__(self, master=None, text="Button", command=None, bg=COLORS["button"], fg=COLORS["text"], 
                 hover_bg=COLORS["button_hover"], font=None, corner_radius=15, width=None, **kwargs):
        self.hover_bg = hover_bg
        super().__init__(master, text=text, command=command, bg=bg, fg=fg, font=font, 
                        relief=tk.FLAT, bd=0, padx=10, pady=5, width=width, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        self.config(background=self.hover_bg)
    
    def on_leave(self, e):
        self.config(background=COLORS["button"])

# Try to import win10toast for nice Windows 10/11 notifications
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    HAVE_TOAST = True
except ImportError:
    HAVE_TOAST = False

# Show Windows notification (only used for critical errors now)
def show_notification(title, message, duration=1):
    """Show a notification using Windows toast notifications if available"""
    try:
        # Log the notification
        logging.info(f"Notification: {title} - {message}")
        
        # Try using win10toast
        if HAVE_TOAST:
            try:
                toaster.show_toast(
                    title,
                    message,
                    icon_path=None,
                    duration=duration,
                    threaded=True
                )
                return True
            except Exception as e:
                logging.error(f"Toast notification error: {e}")
        
        # Fall back to tkinter messagebox as a last resort
        # But just log it rather than showing to avoid UI issues
        logging.info(f"Would show messagebox: {title} - {message}")
        return True
            
    except Exception as e:
        # Just log if showing the notification fails
        logging.error(f"Error showing notification: {e}")
        return False

class PopupWindow(tk.Toplevel):
    """A popup window for KnockThatDoor inspired by f.lux design"""
    def __init__(self, parent, app, close_callback):
        tk.Toplevel.__init__(self, parent)
        
        self.app = app
        self.close_callback = close_callback
        
        # Configure window
        self.title("KnockThatDoor")
        self.geometry("350x480")  # Slightly larger for better spacing
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        
        # Remove window decorations for a cleaner look
        self.overrideredirect(True)
        
        # Make window appear in bottom right corner
        self.position_window()
        
        # Bind Escape key to close the window
        self.bind("<Escape>", self.on_close)
        
        # Set up custom fonts
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.header_font = font.Font(family="Segoe UI", size=11, weight="bold")
        self.normal_font = font.Font(family="Segoe UI", size=10)
        self.small_font = font.Font(family="Segoe UI", size=9)
        
        # Create UI elements
        self.create_widgets()
        
        # Update service status
        self.update_service_status()
        
        # Add a better close button - centered at top right
        close_button = tk.Button(self, text="×", command=self.on_close, 
                                bg=COLORS["bg"], fg=COLORS["text"], bd=0, 
                                font=("Segoe UI", 20, "bold"), relief=tk.FLAT,
                                width=2, height=1)
        close_button.place(x=315, y=0)
        
        # Add hover effect to close button
        close_button.bind("<Enter>", lambda e: close_button.configure(bg=COLORS["close_button"], fg="white"))
        close_button.bind("<Leave>", lambda e: close_button.configure(bg=COLORS["bg"], fg=COLORS["text"]))
        
        # Add a subtle border around the window
        border_frame = tk.Frame(self, bg="#d0d0d0", bd=1, relief=tk.FLAT)
        border_frame.place(x=0, y=0, width=350, height=480)
        border_frame.lower()  # Put it behind everything else
        
        # Lift the window to the top
        self.attributes('-topmost', True)
        
        # Update window
        self.update()
        
    def position_window(self):
        """Position the window in the bottom right corner of the screen"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Window size
        window_width = 350
        window_height = 480
        
        # Calculate position for bottom right
        x = screen_width - window_width - 20  # 20px margin from right
        y = screen_height - window_height - 50  # 50px margin from bottom (for taskbar)
        
        # Set position
        self.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")
    
    def create_widgets(self):
        """Create the UI elements inspired by f.lux"""
        # Main frame with padding
        main_frame = tk.Frame(self, bg=COLORS["bg"], padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Application header with logo and title
        header_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Try to load and display app logo
        logo_image = None
        try:
            logo_path = get_resource_path('img/icona.png')
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo = logo.resize((24, 24), Image.LANCZOS)
                logo_image = ImageTk.PhotoImage(logo)
                
                logo_label = tk.Label(header_frame, image=logo_image, bg=COLORS["bg"])
                logo_label.image = logo_image  # Keep a reference
                logo_label.pack(side=tk.LEFT)
            else:
                # If logo not found, just leave space
                spacer = tk.Label(header_frame, text="", width=3, bg=COLORS["bg"])
                spacer.pack(side=tk.LEFT)
        except Exception as e:
            logging.error(f"Error loading logo: {e}")
            # If error loading logo, just leave space
            spacer = tk.Label(header_frame, text="", width=3, bg=COLORS["bg"])
            spacer.pack(side=tk.LEFT)
        
        # Title
        title_label = tk.Label(header_frame, text="KnockThatDoor", 
                              font=self.title_font, bg=COLORS["bg"], fg=COLORS["text"])
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Button area at the bottom
        button_container = tk.Frame(main_frame, bg=COLORS["bg"])
        button_container.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        
        # First row of buttons
        button_frame1 = tk.Frame(button_container, bg=COLORS["bg"])
        button_frame1.pack(fill=tk.X, pady=(5, 2))
        
        # Second row of buttons
        button_frame2 = tk.Frame(button_container, bg=COLORS["bg"])
        button_frame2.pack(fill=tk.X, pady=(2, 5))
        
        # Create buttons with the custom style - all with same width (12)
        check_button = RoundedButton(button_frame1, text="Check All", command=self.app.check_all_services,
                                  bg=COLORS["button"], fg=COLORS["text"], font=self.normal_font, width=12)
        check_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        refresh_button = RoundedButton(button_frame1, text="Reload Config", command=self.app.refresh_config,
                                    bg=COLORS["button"], fg=COLORS["text"], font=self.normal_font, width=12)
        refresh_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        edit_button = RoundedButton(button_frame2, text="Edit Config", command=self.app.edit_config,
                                 bg=COLORS["button"], fg=COLORS["text"], font=self.normal_font, width=12)
        edit_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        logs_button = RoundedButton(button_frame2, text="View Logs", command=self.app.view_logs,
                                 bg=COLORS["button"], fg=COLORS["text"], font=self.normal_font, width=12)
        logs_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Services status area - con altezza fissa per garantire lo scrolling
        status_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        status_frame.pack(fill=tk.BOTH, expand=True)

        # "Services" label
        services_header = tk.Label(status_frame, text="Services", 
                                font=self.header_font, bg=COLORS["bg"], fg=COLORS["text"],
                                anchor="w")
        services_header.pack(anchor="w", pady=(0, 10))

        # Create scrollable frame for services - IMPORTANTE: altezza fissa definita esplicitamente
        services_container = tk.Frame(status_frame, bg=COLORS["bg"])
        services_container.pack(fill=tk.BOTH, expand=True)
        services_container.config(height=260)  # Altezza fissa per garantire spazio per lo scrolling

        # Canvas for scrolling - anche qui altezza fissa
        services_canvas = tk.Canvas(services_container, bg=COLORS["bg"], highlightthickness=0, height=260)
        services_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar styling
        style = ttk.Style()
        style.theme_use('clam')  # Use the 'clam' theme as a base
        style.configure("Custom.Vertical.TScrollbar", 
                       troughcolor=COLORS["bg"], 
                       background=COLORS["button"], 
                       arrowcolor=COLORS["text"])

        # Add scrollbar
        scrollbar = ttk.Scrollbar(services_container, orient=tk.VERTICAL, command=services_canvas.yview,
                                style="Custom.Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure canvas
        services_canvas.configure(yscrollcommand=scrollbar.set)

        # Create frame for services inside canvas
        self.services_inner_frame = tk.Frame(services_canvas, bg=COLORS["bg"])
        canvas_window = services_canvas.create_window((0, 0), window=self.services_inner_frame, anchor="nw", width=services_canvas.winfo_width())

        # Crea service cards
        self.service_cards = {}
        self.service_status_indicators = {}
        self.service_knock_buttons = {}

        for i, service in enumerate(self.app.config.get("services", [])):
            service_name = service.get("service_name", "Unknown Service")
            
            # Create a card-style container for each service
            card = tk.Frame(self.services_inner_frame, bg=COLORS["card"], bd=1, relief=tk.SOLID,
                        padx=10, pady=10)
            card.pack(fill=tk.X, pady=5, padx=2)
            
            # Add service name
            name_label = tk.Label(card, text=service_name, font=self.normal_font, 
                                bg=COLORS["card"], fg=COLORS["text"], anchor="w")
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Status indicator (colored circle)
            status_indicator = tk.Label(card, text="●", font=("Segoe UI", 14), 
                                    bg=COLORS["card"], fg=COLORS["text_light"])
            status_indicator.pack(side=tk.RIGHT, padx=(5, 0))
            
            # Knock button
            knock_button = RoundedButton(card, text="Knock", font=self.small_font,
                                        command=lambda sn=service_name: self.app.knock_service(sn))
            knock_button.pack(side=tk.RIGHT)
            
            # Store references
            self.service_cards[service_name] = card
            self.service_status_indicators[service_name] = status_indicator
            self.service_knock_buttons[service_name] = knock_button

        # Versione FISSA e MIGLIORATA per l'aggiornamento della regione di scrolling
        def update_scroll_region(event=None):
            # Configura la regione di scrolling per includere tutti i contenuti
            services_canvas.configure(scrollregion=services_canvas.bbox("all"))
            # Imposta la larghezza della finestra interna per adattarsi al canvas
            services_canvas.itemconfig(canvas_window, width=services_canvas.winfo_width())
            services_canvas.update()

        # Aggiungi binding all'evento di configurazione per aggiornare la regione di scrolling
        self.services_inner_frame.bind("<Configure>", update_scroll_region)

        # Binding all'evento di configurazione del canvas per aggiornare la larghezza della finestra interna
        services_canvas.bind("<Configure>", lambda e: services_canvas.itemconfig(canvas_window, width=e.width))

        # Chiamata iniziale per configurare correttamente lo scrolling
        self.services_inner_frame.update_idletasks()
        update_scroll_region()

        # Versione migliorata dell'handler della rotellina del mouse
        def _on_mousewheel(event):
            services_canvas.yview_scroll(int(-1 * (event.delta/120)), "units")

        # Binding della rotellina del mouse - IMPORTANTE: binding diretto al canvas
        services_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Clean up dei binding
        def _cleanup_bindings():
            try:
                services_canvas.unbind_all("<MouseWheel>")
            except:
                pass

        self.bind("<Destroy>", lambda e: _cleanup_bindings())
    
    def update_service_status(self):
        """Update the service status indicators in the UI"""
        for service_name, status in self.app.service_status.items():
            if service_name in self.service_status_indicators:
                indicator = self.service_status_indicators[service_name]
                if status:  # Service is accessible
                    indicator.config(fg=COLORS["success"])
                else:  # Service is not accessible
                    indicator.config(fg=COLORS["error"])
    
    def on_close(self, event=None):
        """Handle window close event"""
        self.withdraw()  # Hide the window
        if self.close_callback:
            self.close_callback()  # Call the close callback

class KnockThatDoorApp:
    """The main application class that handles the system tray icon and core functionality"""
    def __init__(self):
        self.script_dir = get_base_dir()
        
        # Get path for icons
        if is_bundled_app():
            self.icon_path = get_resource_path('img/icona.png')
        else:
            self.icon_path = os.path.join(self.script_dir, 'img', 'icona.png')
        
        logging.info(f"Starting KnockThatDoor from {self.script_dir}")
        
        # Load configuration
        self.config = self.load_config()
        
        # Service status tracking
        self.service_status = {}
        
        # Setup the root tkinter window (hidden)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Set the window icon
        if os.path.exists(self.icon_path):
            icon = ImageTk.PhotoImage(Image.open(self.icon_path))
            self.root.iconphoto(True, icon)
        
        # Initialize the popup window (but don't show it yet)
        self.popup = None
        
        # Load icon for system tray
        self.load_icon()
        
        # Flag for clean shutdown
        self.is_shutting_down = False
        
        # Setup system tray icon
        self.setup_tray_icon()
        
        # Check initial service status
        self.check_all_services()
        
        # Start automatic service checking
        self.start_auto_check_timer()
    
    def load_config(self):
        """Load the configuration from conf.json"""
        try:
            config_path = get_resource_path('conf.json')
            
            logging.info(f"Loading config from: {config_path}")
            
            if not os.path.exists(config_path):
                logging.warning(f"Config file not found: {config_path}")
                return {"services": []}
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            logging.info(f"Loaded config with {len(config.get('services', []))} services")
            return config
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return {"services": []}
    
    def load_icon(self):
        """Load the application icon for system tray"""
        try:
            if os.path.exists(self.icon_path):
                self.app_icon = Image.open(self.icon_path)
                logging.info(f"Loaded icon from: {self.icon_path}")
            else:
                # Create a default icon if the icon file is not found
                self.app_icon = Image.new('RGB', (64, 64), color=(73, 109, 137))
                logging.warning(f"Icon not found: {self.icon_path}, using default")
        except Exception as e:
            # Create a default icon if there's an error
            self.app_icon = Image.new('RGB', (64, 64), color=(73, 109, 137))
            logging.error(f"Error loading icon: {e}")
    
    def setup_tray_icon(self):
        """Set up the system tray icon"""
        def on_left_click(icon, item):
            self.toggle_popup()
        
        # Simple menu for right-click
        menu = pystray.Menu(
            pystray.MenuItem("Show/Hide", on_left_click),
            pystray.MenuItem("Check All", self.check_all_services),
            pystray.MenuItem("Edit Config", self.edit_config),
            pystray.MenuItem("View Logs", self.view_logs),
            pystray.MenuItem("Exit", self.exit_app)
        )
        
        # Create the icon
        self.icon = pystray.Icon(
            "KnockThatDoor",
            self.app_icon,
            "KnockThatDoor",
            menu
        )
        
        # Set left-click action
        self.icon.on_click = on_left_click
    
    def toggle_popup(self):
        """Show or hide the popup window"""
        if self.popup is None or not self.popup.winfo_exists():
            self.popup = PopupWindow(self.root, self, self.popup_closed)
        else:
            if self.popup.winfo_viewable():
                self.popup.withdraw()
            else:
                self.popup.deiconify()
                self.popup.position_window()
                self.popup.lift()
                self.popup.update_service_status()
    
    def popup_closed(self):
        """Callback when popup is closed"""
        pass  # We just let it close
    
    def run(self):
        """Run the application"""
        # Start the system tray icon in a separate thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Run the tkinter main loop
        self.root.mainloop()
    
    def exit_app(self, icon=None, item=None):
        """Exit the application properly"""
        logging.info("Exiting application")
        
        # Set shutdown flag
        self.is_shutting_down = True
        
        # First, stop the icon if it exists
        # We need to schedule this to run after the current event has processed
        def stop_icon():
            if hasattr(self, 'icon'):
                try:
                    # Stop the icon safely
                    self.icon.stop()
                except Exception as e:
                    logging.error(f"Error stopping icon: {e}")
        
        # Use after to schedule the icon stopping
        self.root.after(100, stop_icon)
        
        # Close any open popups
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        
        # Schedule the app to quit after icon is stopped
        def quit_app():
            try:
                # Destroy the root window and exit mainloop
                self.root.quit()
                self.root.destroy()
            except Exception as e:
                logging.error(f"Error during application exit: {e}")
        
        # Schedule quit to happen after icon is stopped
        self.root.after(200, quit_app)
    
    def check_all_services(self, icon=None, item=None):
        """Check the status of all services"""
        logging.info("Checking all services")
        
        # Set all service indicators to yellow (warning) while checking
        if self.popup and self.popup.winfo_exists():
            for indicator in self.popup.service_status_indicators.values():
                indicator.config(fg=COLORS["warning"])
            self.popup.update()
        
        # Check each service in a separate thread
        for service in self.config.get("services", []):
            threading.Thread(target=self.check_service, args=(service,), daemon=True).start()
        
        # Update popup after a delay to allow checks to complete
        if self.popup and self.popup.winfo_exists():
            self.root.after(2000, self.popup.update_service_status)
    
    def refresh_config(self, icon=None, item=None):
        """Reload the configuration file"""
        logging.info("Refreshing configuration")
        self.config = self.load_config()
        
        # Recreate the popup if it exists
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
            self.popup = PopupWindow(self.root, self, self.popup_closed)
        
        # Check service status
        self.check_all_services()
    
    def edit_config(self, icon=None, item=None):
        """Open the configuration file in the default editor"""
        try:
            config_path = get_resource_path('conf.json')
            logging.info(f"Opening config file: {config_path}")
            
            # Use the appropriate command to open the file with default editor
            if os.name == 'nt':  # Windows
                os.startfile(config_path)
            else:
                subprocess.run(["start", config_path], shell=True, check=True)
            
        except Exception as e:
            logging.error(f"Error opening config file: {e}")
    
    def view_logs(self, icon=None, item=None):
        """Open the log folder in File Explorer"""
        try:
            logging.info(f"Opening log directory: {log_dir}")
            
            # Use the appropriate command to open the folder
            if os.name == 'nt':  # Windows
                os.startfile(log_dir)
            else:
                subprocess.run(["start", log_dir], shell=True, check=True)
            
        except Exception as e:
            logging.error(f"Error opening log directory: {e}")
    
    def knock_service(self, service_name):
        """Perform port knocking on the specified service"""
        logging.info(f"Knocking service: {service_name}")
        
        # Find the service in the config
        service = next((s for s in self.config.get("services", []) if s.get("service_name") == service_name), None)
        
        if not service:
            logging.error(f"Service {service_name} not found in configuration")
            return
        
        # Update the UI
        if self.popup and self.popup.winfo_exists():
            if service_name in self.popup.service_status_indicators:
                self.popup.service_status_indicators[service_name].config(fg=COLORS["warning"])
                self.popup.service_knock_buttons[service_name].config(text="Knocking...", state=tk.DISABLED)
                self.popup.update()
        
        # Start the knock in a separate thread
        threading.Thread(target=self.perform_knock, args=(service,), daemon=True).start()
    
    def perform_knock(self, service):
        """Perform the actual port knocking and status check"""
        service_name = service.get("service_name", "Unknown Service")
        target_address = service.get("target_address")
        ports_to_knock = service.get("ports_to_knock", [])
        testing_address_and_port = service.get("testing_address_and_port")
        
        # Get the delay in milliseconds from the service configuration
        delay_ms = service.get("delay_in_milliseconds", 300)  # Default to 300ms if not specified
        delay_sec = delay_ms / 1000.0  # Convert to seconds
        
        logging.info(f"Performing knock for service: {service_name}")
        logging.info(f"Target: {target_address}, Ports: {ports_to_knock}, Delay: {delay_ms}ms")
        
        # Update the UI to show knocking in progress
        if self.popup and self.popup.winfo_exists():
            if service_name in self.popup.service_status_indicators:
                self.popup.service_status_indicators[service_name].config(fg=COLORS["warning"])
                self.popup.service_knock_buttons[service_name].config(text="Knocking...", state=tk.DISABLED)
                self.popup.update()
        
        # Resolve target address
        target_ip = self.resolve_address(target_address)
        if not target_ip:
            logging.error(f"Could not resolve target address: {target_address}")
            self.update_service_ui(service_name, False, "Knock")
            return
        
        # Perform the port knocking
        knock_successful = True  # Assume success unless error occurs
        
        for i, port_spec in enumerate(ports_to_knock):
            # Parse port and protocol
            use_udp = False  # Default to TCP
            port_num = None
            
            # Handle format with colon: port:protocol
            if ":" in port_spec:
                parts = port_spec.split(":")
                port_num = parts[0]
                protocol = parts[1].lower() if len(parts) > 1 else "tcp"
                use_udp = (protocol == "udp")
            # Handle format with protocol suffix: portudp or porttcp
            elif "udp" in port_spec.lower():
                port_num = port_spec.lower().replace("udp", "")
                use_udp = True
            elif "tcp" in port_spec.lower():
                port_num = port_spec.lower().replace("tcp", "")
                use_udp = False
            else:
                # Just a port number - default to TCP
                port_num = port_spec
                use_udp = False
            
            try:
                port_num = int(port_num)
            except ValueError:
                logging.error(f"Invalid port number: {port_num} from spec {port_spec}")
                continue
            
            # Log the knock
            logging.info(f"Knocking {target_ip}:{port_num} via {'UDP' if use_udp else 'TCP'}")
            
            # Send the knock
            try:
                # Create appropriate socket
                address_family = socket.AF_INET6 if ':' in target_ip else socket.AF_INET
                s = socket.socket(address_family, socket.SOCK_DGRAM if use_udp else socket.SOCK_STREAM)
                s.setblocking(False)
                
                try:
                    if use_udp:
                        # For UDP, send empty datagram
                        s.sendto(b'', (target_ip, port_num))
                    else:
                        # For TCP, initiate connection
                        s.connect_ex((target_ip, port_num))
                except Exception as e:
                    logging.error(f"Error during knock: {e}")
                    # Continue with next knock even if this one fails
                finally:
                    s.close()
                
                # Add delay between knocks (essential for proper port knocking)
                if i < len(ports_to_knock) - 1:
                    time.sleep(delay_sec)
                    
            except Exception as e:
                logging.error(f"Error knocking port {port_num}: {e}")
                knock_successful = False
        
        # Allow some time for firewall to process the knocks
        time.sleep(0.5)
        
        # Check if the service is now accessible
        accessible = False
        if testing_address_and_port:
            try:
                host, port = testing_address_and_port.split(':')
                
                # Try with progressively increasing timeouts - this is important!
                for timeout in [0.5, 1.0, 2.0, 5.0]:  # Added a longer 5-second timeout
                    logging.info(f"Testing connection to {host}:{port} with timeout {timeout}s")
                    if self.test_connection(host, int(port), timeout):
                        accessible = True
                        break
                    # Add a small delay between connection attempts
                    time.sleep(0.2)
            except Exception as e:
                logging.error(f"Error testing connection: {e}")
        
        # Update service status
        self.service_status[service_name] = accessible
        
        # Update UI
        self.update_service_ui(service_name, accessible, "Knock")
    
    def update_service_ui(self, service_name, status, button_text):
        """Update the UI elements for a service"""
        if self.popup and self.popup.winfo_exists():
            # Use after() to schedule UI updates on the main thread
            self.root.after(0, lambda: self._update_service_ui_internal(service_name, status, button_text))
    
    def _update_service_ui_internal(self, service_name, status, button_text):
        """Internal method to update UI elements (must be called on main thread)"""
        if service_name in self.popup.service_status_indicators:
            indicator = self.popup.service_status_indicators[service_name]
            button = self.popup.service_knock_buttons[service_name]
            
            # Update status indicator
            indicator.config(fg=COLORS["success"] if status else COLORS["error"])
            
            # Re-enable button
            button.config(text=button_text, state=tk.NORMAL)
    
    def check_service(self, service):
        """Check if a service is accessible without knocking"""
        service_name = service.get("service_name", "Unknown Service")
        testing_address_and_port = service.get("testing_address_and_port")
        
        logging.info(f"Checking service: {service_name}")
        
        # Update UI to show checking in progress
        if self.popup and self.popup.winfo_exists():
            if service_name in self.popup.service_status_indicators:
                self.popup.service_status_indicators[service_name].config(fg=COLORS["warning"])
                self.popup.update()
        
        # Check connection
        accessible = False
        if testing_address_and_port:
            try:
                host, port = testing_address_and_port.split(':')
                accessible = self.test_connection(host, int(port), 2.0)
            except Exception as e:
                logging.error(f"Error checking service {service_name}: {e}")
        
        # Update service status
        self.service_status[service_name] = accessible
        
        # Update UI
        self.update_service_ui(service_name, accessible, "Knock")
        
        logging.info(f"Service {service_name} is {'accessible' if accessible else 'not accessible'}")
    
    def resolve_address(self, host):
        """Resolve hostname to IP address"""
        try:
            # Check if already an IP
            try:
                socket.inet_pton(socket.AF_INET, host)
                return host  # It's an IPv4 address
            except socket.error:
                try:
                    socket.inet_pton(socket.AF_INET6, host)
                    return host  # It's an IPv6 address
                except socket.error:
                    pass  # Not an IP address, try to resolve
            
            # Resolve hostname
            ip = socket.gethostbyname(host)
            logging.info(f"Resolved {host} to {ip}")
            return ip
        except Exception as e:
            logging.error(f"Error resolving address {host}: {e}")
            return None
    
    def test_connection(self, host, port, timeout=1.0):
        """Test if a connection can be established to host:port"""
        try:
            # Resolve hostname
            ip = self.resolve_address(host)
            if not ip:
                return False
            
            # Create socket
            address_family = socket.AF_INET6 if ':' in ip else socket.AF_INET
            s = socket.socket(address_family, socket.SOCK_STREAM)
            s.settimeout(timeout)
            
            # Log the connection attempt
            logging.info(f"Attempting connection to {ip}:{port} with timeout {timeout}s")
            
            # Attempt connection
            result = s.connect_ex((ip, port))
            s.close()
            
            # Log the result
            if result == 0:
                logging.info(f"Connection to {ip}:{port} successful")
            else:
                logging.info(f"Connection to {ip}:{port} failed with error code {result}")
            
            return result == 0
            
        except Exception as e:
            logging.error(f"Error testing connection to {host}:{port}: {e}")
            return False
    
    def start_auto_check_timer(self):
        """Start a timer to periodically check services"""
        # Check every 5 minutes
        check_interval = 5 * 60 * 1000  # In milliseconds for tkinter
        
        def check_services():
            # Don't perform check if we're shutting down
            if not self.is_shutting_down:
                self.check_all_services()
                # Schedule next check only if we're not shutting down
                self.root.after(check_interval, check_services)
        
        # Schedule first check
        self.root.after(check_interval, check_services)
        logging.info(f"Automatic service checking scheduled every {check_interval/60000} minutes")

def main():
    """Main entry point for the application"""
    try:
        # Create and run the app
        app = KnockThatDoorApp()
        app.run()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        logging.critical(traceback.format_exc())
        
        try:
            # Show error messagebox
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
        except:
            pass
        
        # Exit without using sys.exit() to avoid issues
        os._exit(1)

if __name__ == "__main__":
    main()