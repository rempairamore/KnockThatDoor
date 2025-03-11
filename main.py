#!/usr/bin/env python3
# KnockThatDoor - A port knocking utility for macOS
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
import rumps
import json
import os
import threading
import time
import sys
import socket
import select
import subprocess
import traceback
import logging
from datetime import datetime

# Helper function to determine if running as a bundled app
def is_bundled_app():
    return getattr(sys, 'frozen', False)

# Get the appropriate base directory based on runtime environment
def get_base_dir():
    if is_bundled_app():
        # Running as bundled app
        executable_dir = os.path.dirname(os.path.abspath(sys.executable))
        if executable_dir.endswith('MacOS'):
            # We're in .app/Contents/MacOS
            return os.path.dirname(executable_dir)  # Return Contents dir
        else:
            return executable_dir
    else:
        # Running as script
        return os.path.dirname(os.path.realpath(__file__))

# Get resource path for bundled app or development
def get_resource_path(relative_path):
    base_dir = get_base_dir()
    
    if is_bundled_app():
        # For bundled app, check in Resources folder
        resources_dir = os.path.join(base_dir, 'Resources')
        path = os.path.join(resources_dir, relative_path)
    else:
        # For development, use the direct path
        path = os.path.join(base_dir, relative_path)
    
    # Debug output
    print(f"Resolving resource path for: {relative_path}")
    print(f"Path: {path}")
    print(f"Path exists: {os.path.exists(path)}")
    
    return path

# Setup logging
base_dir = get_base_dir()
if is_bundled_app():
    # For bundled app, use the MacOS folder for logs
    executable_dir = os.path.dirname(os.path.abspath(sys.executable))
    log_dir = os.path.join(executable_dir, "log")
else:
    # For development, use local log folder
    log_dir = os.path.join(base_dir, "log")

os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"knockthatdoor_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PortKnockerApp(rumps.App):
    def __init__(self):
        self.script_dir = get_base_dir()
        
        # Get paths for icons
        if is_bundled_app():
            # For bundled app
            icon_path = get_resource_path('img/icona.png')
            self.error_icon_path = get_resource_path('img/error.png')
            self.connected_icon_path = get_resource_path('img/connected.png')
            self.loading_icon_path = get_resource_path('img/loading1.png')
            self.closed_icon_path = get_resource_path('img/closed.png')
        else:
            # For development
            icon_path = os.path.join(self.script_dir, 'img', 'icona.png')
            self.error_icon_path = os.path.join(self.script_dir, 'img', 'error.png')
            self.connected_icon_path = os.path.join(self.script_dir, 'img', 'connected.png')
            self.loading_icon_path = os.path.join(self.script_dir, 'img', 'loading1.png')
            self.closed_icon_path = os.path.join(self.script_dir, 'img', 'closed.png')
        
        logging.info(f"Starting KnockThatDoor from {self.script_dir}")
        print(f"Starting KnockThatDoor from {self.script_dir}")
        
        # Initialize app with menu bar icon
        if os.path.exists(icon_path):
            logging.info(f"Using app icon: {icon_path}")
            print(f"Using app icon: {icon_path}")
            super(PortKnockerApp, self).__init__("KnockThatDoor", icon=icon_path, quit_button=None)
        else:
            logging.warning(f"WARNING: App icon not found: {icon_path}")
            print(f"WARNING: App icon not found: {icon_path}")
            super(PortKnockerApp, self).__init__("KnockThatDoor", quit_button=None)
        
        self.config = self.load_config()
        self.setup_menu()
        
        # Flag to indicate when services have been verified
        self.services_verified = False
        
        # Perform an initial check of all services when the app starts
        self.initial_check()
    
    def load_config(self):
        try:
            if is_bundled_app():
                # For bundled app
                config_path = get_resource_path('conf.json')
            else:
                # For development
                config_path = os.path.join(self.script_dir, 'conf.json')
            
            logging.info(f"Loading config from: {config_path}")
            print(f"Loading config from: {config_path}")
            
            if not os.path.exists(config_path):
                logging.warning(f"Config file not found: {config_path}")
                print(f"Config file not found: {config_path}")
                return {"services": []}
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            print(f"Error loading config: {e}")
            return {"services": []}
    
    def setup_menu(self):
        self.menu.clear()
        self.services_menu_items = {}
        
        # Verify that icons exist
        self.check_icons_exist()
        
        # Add services from configuration file
        for service in self.config.get("services", []):
            service_name = service.get("service_name", "Unknown Service")
            menu_item = rumps.MenuItem(service_name, callback=self.on_service_click)
            self.menu.add(menu_item)
            self.services_menu_items[service_name] = menu_item
        
        self.menu.add(None)
        #check_button = rumps.MenuItem("Check Connections", callback=self.on_check_connections)
        #self.menu.add(check_button)
        self.menu.add(rumps.MenuItem("Refresh Config", callback=self.on_refresh_click))
        self.menu.add(rumps.MenuItem("Edit Config", callback=self.on_edit_config))
        self.menu.add(None)
        self.menu.add(rumps.MenuItem("View Logs", callback=self.on_view_logs))
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))
    
    def check_icons_exist(self):
        """Verify that all icons exist and print a warning if missing"""
        icons_to_check = [
            self.error_icon_path,
            self.connected_icon_path,
            self.loading_icon_path,
            self.closed_icon_path
        ]
        
        for icon_path in icons_to_check:
            if not os.path.exists(icon_path):
                logging.warning(f"WARNING: Missing icon: {icon_path}")
                print(f"WARNING: Missing icon: {icon_path}")
            else:
                logging.info(f"Icon found: {icon_path}")
                print(f"Icon found: {icon_path}")
    
    def on_edit_config(self, _):
        """Open the configuration file in TextEdit"""
        try:
            if is_bundled_app():
                # For bundled app
                config_path = get_resource_path('conf.json')
            else:
                # For development
                config_path = os.path.join(self.script_dir, 'conf.json')
                
            logging.info(f"Opening config file: {config_path}")
            print(f"Opening config file: {config_path}")
            
            # Use the 'open' command to open the file with default editor
            subprocess.run(["open", config_path], check=True)
            
        except Exception as e:
            logging.error(f"Error opening config file: {e}")
            print(f"Error opening config file: {e}")
            self.show_notification(
                title="Error",
                subtitle=f"Could not open config file: {e}"
            )
    
    def on_view_logs(self, _):
        """Open the log folder in Finder"""
        try:
            if is_bundled_app():
                # For bundled app, use the MacOS folder for logs
                executable_dir = os.path.dirname(os.path.abspath(sys.executable))
                log_dir = os.path.join(executable_dir, "log")
            else:
                # For development, use local log folder
                log_dir = os.path.join(self.script_dir, "log")
                
            logging.info(f"Opening log directory: {log_dir}")
            print(f"Opening log directory: {log_dir}")
            
            # Create the log directory if it doesn't exist yet
            os.makedirs(log_dir, exist_ok=True)
            
            # Use the 'open' command to open the folder in Finder
            subprocess.run(["open", log_dir], check=True)
            
        except Exception as e:
            logging.error(f"Error opening log directory: {e}")
            print(f"Error opening log directory: {e}")
            self.show_notification(
                title="Error",
                subtitle=f"Could not open log directory: {e}"
            )

    def initial_check(self):
        """Perform an initial check of all services when the app starts"""
        logging.info("Performing initial check of all services")
        print("Performing initial check of all services")
        
        # Don't show notifications for the initial check
        for service in self.config.get("services", []):
            threading.Thread(target=self.check_service, args=(service, True), daemon=True).start()
            
        # Set flag to True after initial verification
        self.services_verified = True
    
    def on_refresh_click(self, _):
        """Update configuration"""
        self.config = self.load_config()
        self.setup_menu()
        self.show_info_notification(
            "Loading new configuration",
            f"Reopen menu to see updated services"
        )
        # Perform an initial check of all services when the app starts
        self.initial_check()
    
    def on_check_connections(self, _):
        """Check the status of all connections"""
        # Set loading icons
        for service_name, menu_item in self.services_menu_items.items():
            menu_item.icon = self.loading_icon_path
            print(f"Set loading icon for {service_name}")
        
        # Show notification informing the user checks are in progress
        self.show_info_notification(
            "Connection Check",
            "Checking connections... reopen menu to see results"
        )
        
        # Start threads to check services with the 'from_check_connections' flag set to True
        for service in self.config.get("services", []):
            threading.Thread(target=self.check_service, args=(service, True), daemon=True).start()
        
        # Set flag to true
        self.services_verified = True
    
    def test_connection(self, hostname, port, timeout=0.2):
        """Test connection to a specified host and port using Python sockets
        
        Args:
            hostname: The hostname or IP to connect to
            port: The port number to connect to
            timeout: Timeout in seconds
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Resolve the hostname to get the address family and IP
            address_family, _, _, _, ip = socket.getaddrinfo(
                host=hostname,
                port=None,
                flags=socket.AI_ADDRCONFIG
            )[0]
            ip_address = ip[0]
            
            # Create a TCP socket
            s = socket.socket(address_family, socket.SOCK_STREAM)
            s.settimeout(timeout)
            
            # Try to connect
            result = s.connect_ex((ip_address, int(port)))
            s.close()
            
            # If result is 0, connection succeeded
            return result == 0
        except Exception as e:
            logging.error(f"Error testing connection to {hostname}:{port} - {e}")
            print(f"Error testing connection to {hostname}:{port} - {e}")
            return False
    
    def check_service(self, service, from_check_connections=False):
        """Check the status of a single service
        
        Args:
            service: The service configuration to check
            from_check_connections: If True, use closed.png for timeouts, if False use error.png
        """
        service_name = service.get("service_name")
        testing_address_and_port = service.get("testing_address_and_port")
        
        if not testing_address_and_port or service_name not in self.services_menu_items:
            return
            
        menu_item = self.services_menu_items[service_name]
        
        try:
            parts = testing_address_and_port.split(':')
            if len(parts) != 2:
                return
            
            address, port = parts
            
            # Test connection with Python sockets instead of netcat
            logging.info(f"Testing {service_name}: socket connection to {address}:{port}")
            print(f"Testing {service_name}: socket connection to {address}:{port}")
            
            # Use a 1-second timeout for the connection test
            connection_successful = self.test_connection(address, port, timeout=0.5)
            
            # Update icon based on result
            if connection_successful:
                logging.info(f"Service {service_name} is accessible")
                print(f"Service {service_name} is accessible")
                menu_item.icon = self.connected_icon_path
                print(f"Set connected icon for {service_name}")
            else:
                logging.info(f"Service {service_name} is not accessible")
                print(f"Service {service_name} is not accessible")
                if from_check_connections:
                    menu_item.icon = self.closed_icon_path
                    print(f"Set closed icon for {service_name}")
                else:
                    menu_item.icon = self.error_icon_path
                    print(f"Set error icon for {service_name}")
            
        except Exception as e:
            logging.error(f"Error checking status for {service_name}: {e}")
            print(f"Error checking status for {service_name}: {e}")
            menu_item.icon = self.error_icon_path
            print(f"Set error icon for {service_name} error")
    
    def perform_port_knock(self, host, ports, timeout=0.2, delay=0.2, default_udp=False, verbose=True):
        """Perform port knocking on the specified host and ports
        
        Args:
            host: Hostname or IP to knock on
            ports: List of ports to knock on, format: ["8006:tcp", "8080:udp", ...]
            timeout: Timeout in seconds for each knock
            delay: Delay in seconds between knocks
            default_udp: Whether to use UDP by default (if protocol not specified)
            verbose: Whether to print verbose information
            
        Returns:
            bool: True if all knocks were sent, False if an error occurred
        """
        try:
            # Resolve the hostname to get the address family and IP
            address_family, _, _, _, ip = socket.getaddrinfo(
                host=host,
                port=None,
                flags=socket.AI_ADDRCONFIG
            )[0]
            ip_address = ip[0]
            
            if verbose:
                logging.info(f"Knocking on {host} ({ip_address})")
                print(f"Knocking on {host} ({ip_address})")
            
            # Process each port
            for i, port_spec in enumerate(ports):
                # Parse port and protocol using the new format "port:protocol"
                use_udp = default_udp  # Default protocol (typically TCP)
                
                # Check if port specification includes the new format (port:protocol)
                if ":" in port_spec:
                    parts = port_spec.split(":")
                    port_num = parts[0]
                    protocol = parts[1].lower() if len(parts) > 1 else ""
                    
                    if protocol == "udp":
                        use_udp = True
                    elif protocol == "tcp":
                        use_udp = False
                else:
                    # Backward compatibility with old format or default if no protocol specified
                    if "tcp" in port_spec.lower():
                        port_num = port_spec.lower().replace("tcp", "")
                        use_udp = False
                    elif "udp" in port_spec.lower():
                        port_num = port_spec.lower().replace("udp", "")
                        use_udp = True
                    else:
                        port_num = port_spec
                
                try:
                    port_num = int(port_num)
                except ValueError:
                    logging.error(f"Invalid port number: {port_num}")
                    print(f"Invalid port number: {port_num}")
                    continue
                
                if verbose:
                    logging.info(f"Hitting {ip_address}:{port_num} via {'UDP' if use_udp else 'TCP'}")
                    print(f"Hitting {ip_address}:{port_num} via {'UDP' if use_udp else 'TCP'}")
                
                # Create the appropriate socket
                s = socket.socket(address_family, socket.SOCK_DGRAM if use_udp else socket.SOCK_STREAM)
                s.setblocking(False)
                
                try:
                    socket_address = (ip_address, port_num)
                    if use_udp:
                        # For UDP, just send an empty datagram
                        s.sendto(b'', socket_address)
                    else:
                        # For TCP, initiate a connection but don't wait for it to complete
                        s.connect_ex(socket_address)
                        # Wait for the socket to be readable or writable with timeout
                        select.select([s], [s], [s], timeout)
                except Exception as e:
                    if verbose:
                        logging.error(f"  Error during knock: {e}")
                        print(f"  Error during knock: {e}")
                finally:
                    s.close()
                
                # Add delay between knocks (except for the last one)
                if delay > 0 and i < len(ports) - 1:
                    time.sleep(delay)
            
            return True
        except Exception as e:
            logging.error(f"Error performing port knock: {e}")
            print(f"Error performing port knock: {e}")
            return False
    
    def on_service_click(self, sender):
        """Handle click on a service"""
        service_name = sender.title
        service = next((s for s in self.config.get("services", []) if s.get("service_name") == service_name), None)
        
        if not service:
            return
        
        # Set loading icon
        sender.icon = self.loading_icon_path
        print(f"Set loading icon for {service_name}")
        
        # Show notification that port knocking is in progress
        self.show_info_notification(
            "Port Knocking in Progress",
            f"Executing knock for {service_name}... reopen menu to see results"
        )
        
        # Start process in a separate thread to avoid blocking UI
        # Pass False to indicate this is not from Check Connections
        threading.Thread(target=self.check_service_after_knock, args=(service, sender), daemon=True).start()
        
    def check_service_after_knock(self, service, menu_item):
        """First perform port knocking, then check the service connection"""
        service_name = service.get("service_name")
        target_address = service.get("target_address")
        ports_to_knock = service.get("ports_to_knock", [])
        testing_address_and_port = service.get("testing_address_and_port")
        
        # Get the delay in milliseconds from the service configuration
        delay_ms = service.get("delay_in_milliseconds", 300)  # Default to 300ms if not specified
        delay_sec = delay_ms / 1000.0  # Convert to seconds
        
        logging.info(f"\n\nProcessing service: {service_name} with delay: {delay_ms}ms")
        print(f"\n\nProcessing service: {service_name} with delay: {delay_ms}ms")
        
        # Perform port knocking using the socket implementation
        knock_successful = self.perform_port_knock(
            host=target_address,
            ports=ports_to_knock,
            timeout=0.2,
            delay=delay_sec,  # Use the delay from the service configuration
            default_udp=False,
            verbose=True
        )
        
        if not knock_successful:
            logging.error(f"Port knocking failed for {service_name}")
            print(f"Port knocking failed for {service_name}")
            self.show_failure_notification(service_name)
            menu_item.icon = self.error_icon_path
            return
        
        # Now check the connection
        if testing_address_and_port:
            try:
                parts = testing_address_and_port.split(':')
                if len(parts) != 2:
                    return
                
                address, port = parts
                
                # Test connection using Python sockets
                logging.info(f"Testing connection to {address}:{port}")
                print(f"Testing connection to {address}:{port}")
                
                # Use a 2-second timeout for the connection test
                connection_successful = self.test_connection(address, port, timeout=2.0)
                
                # Update icon based on result and show notification
                if connection_successful:
                    logging.info(f"Service {service_name} is accessible")
                    print(f"Service {service_name} is accessible")
                    self.show_success_notification(service_name)
                    menu_item.icon = self.connected_icon_path
                    print(f"Set connected icon for {service_name}")
                else:
                    logging.info(f"Service {service_name} is not accessible")
                    print(f"Service {service_name} is not accessible")
                    self.show_failure_notification(service_name)
                    menu_item.icon = self.error_icon_path
                    print(f"Set error icon for {service_name}")
                
            except Exception as e:
                logging.error(f"Error testing connection: {e}")
                print(f"Error testing connection: {e}")
                self.show_failure_notification(service_name)
                menu_item.icon = self.error_icon_path
                print(f"Set error icon for {service_name} error")
    
    def will_show_menu(self):
        """Method called before showing the menu"""
        logging.info("Menu is about to be displayed")
        print("Menu is about to be displayed")
        return True
    
    def show_notification(self, title, subtitle, message=""):
        """Show a notification using rumps functionality"""
        logging.info(f"Showing notification: {title} - {subtitle}")
        print(f"Showing notification: {title} - {subtitle}")
        
        # First, try the standard rumps notification
        try:
            # Use rumps.notification with the standard parameters
            rumps.notification(
                title=title,
                subtitle=subtitle,
                message=message
            )
            logging.info("Sent notification using rumps.notification")
            print("Sent notification using rumps.notification")
            return
        except Exception as e:
            logging.error(f"Error with rumps.notification: {e}")
            print(f"Error with rumps.notification: {e}")
        
        # Alternative method 1: using alert
        try:
            # This will show the alert in a window instead of a notification
            # It won't be as nice but at least gives feedback
            rumps.alert(
                title=title,
                message=subtitle
            )
            logging.info("Showed alert as fallback")
            print("Showed alert as fallback")
            return
        except Exception as e:
            logging.error(f"Error with rumps.alert: {e}")
            print(f"Error with rumps.alert: {e}")
        
        logging.error("All notification methods failed!")
        print("All notification methods failed!")
    
    def show_success_notification(self, service_name):
        """Show a success notification"""
        self.show_notification(
            title="Connection Successful", 
            subtitle=f"{service_name} is now accessible"
        )
    
    def show_failure_notification(self, service_name):
        """Show a failure notification"""
        self.show_notification(
            title="Connection Failed",
            subtitle=f"{service_name} not accessible"
        )
    
    def show_info_notification(self, title, message):
        """Show an informational notification"""
        self.show_notification(
            title=title,
            subtitle=message
        )


def run_app_with_restart():
    """Run the app with automatic restart on crash"""
    MAX_RESTARTS = 5  # Maximum number of restarts to prevent infinite loop
    restart_count = 0
    restart_timeout = 3  # Seconds to wait between restarts
    
    while restart_count < MAX_RESTARTS:
        try:
            logging.info(f"Starting app (restart count: {restart_count})")
            print(f"Starting app (restart count: {restart_count})")
            
            # Create and run the app
            app = PortKnockerApp()
            app.run()
            
            # If app.run() returns normally (e.g. through quit button),
            # we should exit without restarting
            logging.info("App exited normally")
            print("App exited normally")
            break
            
        except Exception as e:
            restart_count += 1
            logging.error(f"App crashed with error: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            print(f"App crashed with error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Show a notification about the crash and restart if possible
            try:
                rumps.notification(
                    title="KnockThatDoor Crashed",
                    subtitle=f"Restarting in {restart_timeout} seconds...",
                    message=f"Error: {str(e)[:50]}..."
                )
            except:
                # If notification fails, just continue with restart
                pass
            
            logging.info(f"Waiting {restart_timeout} seconds before restart...")
            print(f"Waiting {restart_timeout} seconds before restart...")
            time.sleep(restart_timeout)
            
            # Increase timeout for subsequent restarts to avoid rapid restart cycles
            restart_timeout = min(restart_timeout * 2, 30)  # Cap at 30 seconds
    
    if restart_count >= MAX_RESTARTS:
        logging.critical(f"Reached maximum restart limit ({MAX_RESTARTS}). Exiting.")
        print(f"Reached maximum restart limit ({MAX_RESTARTS}). Exiting.")
        # Try to show one final notification
        try:
            rumps.notification(
                title="KnockThatDoor",
                subtitle=f"Too many crashes ({MAX_RESTARTS}). Please check logs.",
                message="The app will now exit."
            )
        except:
            pass


if __name__ == "__main__":
    run_app_with_restart()