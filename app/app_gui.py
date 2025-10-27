import tkinter as tk
from tkinter import filedialog, messagebox, Menu, simpledialog, ttk
from test_definitions import Eth0Test, USBTest, RTCTest, XbeeTest, BatteryTest, RelayTest, SIMTest, BLETest, WiFiTest  # Importing our test classes
from excel_writer import append_test_results, get_next_available_mac
from label_create import create_label
import os
import subprocess
import configparser
from appdirs import user_config_dir
from help_gui import HelpCenter
from _version import __version__
from mac_generator import MACGeneratorFrame
from log import logger,initialize_logging # Custom logging setup
# import re
# import time

# Global configurations
patter_state = 0;
OPENWRT_PROMPT = "Please press Enter to activate this console."
OPENWRT_PROMPT_2 = "nuc980-emac0 b0012000.emac0: eth0 is"
# UBOOT_PROMPT = "Hit any key to stop autoboot"       # old prompt
UBOOT_PROMPT = "Autoboot in 1 seconds"               # new prompt
# Load configuration file
cfg = configparser.ConfigParser()
path = os.path.join(user_config_dir("IGTestApp","ECSI"), "settings.ini")

class HardwareTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Test Application")
        self.root.minsize(800, 600)
        
        # Default serial port (configurable via the menu)
        self.serial_port = "/dev/ttyUSB0"
        self.minipcie_slot = 'ttyS0'  # Default mini PCIe slot
        self.model_number = "IG4-1000"
        self.mac_addr = get_next_available_mac(False)
        if self.mac_addr is None:
            # Handle the case where no MAC address is available
            logger.error("Warning: No available MAC address found!")

        self.server_ip = "192.168.0.1"
        self.auto_advance = True
        self.print_labels = True
        # WiFi settings
        self.wifi_ssid = "SSID"
        self.wifi_password = "Password"
        self.wifi_security = "WPA-PSK"  # Options: OPEN, WEP, WPA, WPA2
        # Load configuration settings
        self.load_config()

        
        # Store test results: "Pending", "PASS", or "FAIL"
        self.test_results = {}
        # Test definitions are stored here along with the reference to the test class.
        self.tests = [
            {"name": "Ethernet Test", "requires_input": False, "os":"uboot", "class": Eth0Test},
            {"name": "RTC Test", "requires_input": False, "os":"uboot", "class": RTCTest},
            {"name": "Xbee Test", "requires_input": False,  "os":"uboot","class": XbeeTest},
            {"name": "Battery Test", "requires_input": False, "os":"uboot", "class": BatteryTest},
            {"name": "Relay Test", "requires_input": True, "os":"uboot", "class": RelayTest},
            {"name": "BLE Test", "requires_input": True, "os":"openwrt", "class": BLETest},
            {"name": "WiFi Test", "requires_input": False, "os":"openwrt", "class": WiFiTest},
            {"name": "USB Test", "requires_input": False, "os":"openwrt", "class": USBTest},
            {"name": "SIM Test", "requires_input": False, "os":"openwrt", "class": SIMTest},
            # {"name": "Button Test", "requires_input": False, "class": ButtonTest},
        ]
        
        # Dictionary to store button widgets (for UI updates)
        self.test_buttons = {}

        # Create GUI elements
        self.help_window = None
        # single-instance popup reference
        self.mac_window = None
        # DuT connection status 
        self.connection_status = False
        self.terminal_state = "Disconnected"  # "Disconnected", "Uboot", "Linux"
        
        # Serial connection handle (used for GUI-based serial connection monitoring)
        self.serial_conn = None
        
        self.create_menu()
        self.create_widgets()
        
        # Begin periodic serial checking via tkinter's after() method (no threading)
        self.check_serial()
    
    def create_menu(self):
        """Creates a File menu with options to open/save results, configure test parameters, and access help."""
        menu_bar = Menu(self.root)
        
        # File menu
        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open Results", command=self.open_results)
        file_menu.add_command(label="Save Results", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Reset", command=self.reset_tests)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Configure menu
        menu_bar.add_command(label="Configure", command=self.configure_parameters)

        # MAC Generator menu
        menu_bar.add_command(label="MAC Generator", command=self.show_mac_generator_popup)

        # Help Menu
        help_menu = Menu(menu_bar, tearoff=0)        
        help_menu.add_command(label="Help Center", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Contact Support", command=self.contact_support)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def create_widgets(self):
        """Creates the main GUI layout with a reconnect button, left-pane test buttons, and right-pane status."""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame holds the reconnect button and its indicator.
        top_frame = tk.Frame(main_frame)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Reconnect button for manual reconnecting to the serial port.
        self.reconnect_button = tk.Button(top_frame, text="Reconnect", command=self.manual_reconnect)
        self.reconnect_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Canvas for a colored circle indicator (red = disconnected, green = connected).
        self.reconnect_indicator = tk.Canvas(top_frame, width=20, height=20)
        self.indicator_circle = self.reconnect_indicator.create_oval(2, 2, 18, 18, fill="red")
        self.reconnect_indicator.pack(side=tk.RIGHT, padx=5)
        
        # Label adjacent to the reconnect indicator
        self.status_text = tk.Label(top_frame, text="Disconnected")
        self.status_text.pack(side=tk.RIGHT, padx=5)

        # Define the control variables
        self.auto_advance_var = tk.BooleanVar(value=self.auto_advance)
        self.print_labels_var = tk.BooleanVar(value=self.print_labels)
        
        # whenever the var is written (toggled), call our handler
        self.auto_advance_var.trace_add('write', self._on_toggle_auto) 
        self.print_labels_var.trace_add('write', self._on_toggle_print)
        # Create the Checkbuttons
        auto_cb = tk.Checkbutton(top_frame,
                                text="Auto-advance",
                                variable=self.auto_advance_var,
                                onvalue=True, offvalue=False)
        auto_cb.pack(side=tk.LEFT, padx=5)

        print_cb = tk.Checkbutton(top_frame,
                                    text="Print Labels",
                                    variable=self.print_labels_var,
                                    onvalue=True, offvalue=False)
        print_cb.pack(side=tk.LEFT, padx=5)

        # Save the current state of the checkboxes to the config file
        self.save_config()

        # Content area split into left and right frames
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left frame: one button per test.
        left_frame = tk.Frame(content_frame, bd=2, relief=tk.SUNKEN)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        for test in self.tests:
            test_name = test["name"]
            btn = tk.Button(left_frame, text=f"{test_name}: Pending", width=20, 
                            state=tk.DISABLED,
                            command=lambda name=test_name: self.run_test(name))
            btn.pack(pady=5)
            self.test_buttons[test_name] = btn
            self.test_results[test_name] = "Pending"
        
        # Right frame: shows detailed test status and, for manual tests, pass/fail buttons.
        self.right_frame = tk.Frame(content_frame, bd=2, relief=tk.SUNKEN)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_label = tk.Label(self.right_frame, text="Select a test to view details", anchor="w")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a Text widget for logging:
        self.log_text = tk.Text(self.right_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Frame for pass/fail buttons for tests requiring user input.
        self.input_frame = tk.Frame(self.right_frame)
        self.input_frame.pack(padx=5, pady=5)
        
        self.pass_button = tk.Button(self.input_frame, text="Pass", command=self.user_pass)
        self.fail_button = tk.Button(self.input_frame, text="Fail", command=self.user_fail)
        
        # By default, hide manual input buttons.
        self.disable_user_input()
    
    def disable_user_input(self):
        """Hide and disable the pass/fail buttons."""
        self.pass_button.config(state=tk.DISABLED)
        self.fail_button.config(state=tk.DISABLED)
        self.pass_button.pack_forget()
        self.fail_button.pack_forget()
    
    def enable_user_input(self):
        """Show and enable the pass/fail buttons."""
        self.pass_button.config(state=tk.NORMAL)
        self.fail_button.config(state=tk.NORMAL)
        self.pass_button.pack(side=tk.LEFT, padx=5)
        self.fail_button.pack(side=tk.LEFT, padx=5)

    def log_message(self, msg):
        """Append a message to the log text widget in the GUI."""
        logger.info(msg)
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            # Force GUI to update
            self.root.update_idletasks()        
        except Exception:
            logger.warning("Could not update GUI log widget", exc_info=True)

    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
    def os_selection_popup(self, test_name, os_name):
        if self.serial_conn is None or os_name not in ["U-Boot", "OpenWRT"]:
            logger.error("Serial connection not established.")
            messagebox.showerror("Error", "Serial connection not established.")
            return
        
        response = messagebox.askyesno("Confirm", f"{test_name} requires the device to be in {os_name}. Proceed ?")
        if response:
            # User clicked Yes
            if os_name == "U-Boot":
                try:
                    self.status_text.config(text="Sending reboot command to device...")
                    self.serial_conn.write(b'reboot\r\n')
                    self.serial_conn.flush()                
                    self.check_uboot_prompt()
                except Exception as e:
                    messagebox.showerror("Serial Error", f"Failed to send reboot command: {e}")
                    self.status_text.config(text="Failed to send reboot command.")
                    return
            elif os_name == "OpenWRT":
                try:
                    self.status_text.config(text="Sending boot command to device...")
                    self.serial_conn.write(b'boot\r\n')
                    self.serial_conn.flush()
                
                except Exception as e:
                    messagebox.showerror("Serial Error", f"Failed to send boot command: {e}")
                    self.status_text.config(text="Failed to send boot command.")
                    return
                self.check_openwrt_prompt()
            else:
                logger.error(f"Unknown OS name: {os_name}")
                return
        else:
            # User clicked No
            # Do nothing (popup closes automatically)
            print("User chose No — API not called.")
    
    def run_test(self, test_name):
        """
        Invoked when a test button is clicked.
        For automatic tests (no manual input required), it instantiates and runs the test.
        For tests requiring manual verification, enable the pass/fail buttons.
        """
        selected_test = next((t for t in self.tests if t["name"] == test_name), None)
        if not selected_test:
            return
        
        # Clear the log widget after the test completes.
        self.clear_log()

        if selected_test["os"] == "uboot" and self.terminal_state != "uboot":
            self.os_selection_popup(test_name, "U-Boot")
            return
        
        if selected_test["os"] == "openwrt" and self.terminal_state != "linux":
            self.os_selection_popup(test_name, "OpenWRT")
            return

        self.status_label.config(text=f"Running {test_name}...")
        if selected_test["requires_input"]:
            # For tests like LED test: Show manual input UI.
            self.enable_user_input()
            # Instantiate the test class passing the current serial port.
            test_class = selected_test["class"]
            self.status_label.config(text=f"{test_name} requires manual verification.\nClick Pass or Fail when ready.")
            tester = test_class(port=self.serial_port, debug=True, log_callback=self.log_message)
            tester.run()
        else:
            self.disable_user_input()
            # Instantiate the test class passing the current serial port.
            test_class = selected_test["class"]
            if test_class is Eth0Test:
                self.mac_addr = get_next_available_mac(False)  # Read the MAC address from the Excel file
                if self.mac_addr is None:
                    messagebox.showerror("Error", "No available MAC address found! Please generate MAC file.")
                    return
                tester = test_class(port=self.serial_port, slot=self.minipcie_slot, mac_addr=self.mac_addr,  server_ip=self.server_ip, debug=True, log_callback=self.log_message)
            elif test_class is WiFiTest:
                tester = test_class(port=self.serial_port, wifi_ssid=self.wifi_ssid, wifi_password=self.wifi_password, wifi_security=self.wifi_security, debug=True, log_callback=self.log_message)
            elif test_class is XbeeTest:
                tester = test_class(port=self.serial_port, slot=self.minipcie_slot, debug=True, log_callback=self.log_message)
            else:
                tester = test_class(port=self.serial_port, debug=True, log_callback=self.log_message)
            # Running the test (this call is blocking—use caution if test duration is long)
            success = tester.run()
            self.complete_test(test_name, success)
    
    def complete_test(self, test_name, passed):
        """Update UI elements once the test completes."""
        if passed is None:
            # For tests where execution is deferred to manual input.
            self.status_label.config(text=f"{test_name} awaiting manual result.")
            return
        result_str = "PASS" if passed else "FAIL"
        self.test_results[test_name] = result_str
        
        btn = self.test_buttons.get(test_name)
        if btn:
            btn.config(text=f"{test_name}: {result_str}",
                       fg="green" if passed else "red")
        
        self.status_label.config(text=f"{test_name} completed: {result_str}")
        self.log_message(f"{test_name} completed: {result_str}") #Show result in log also
        self.disable_user_input()
        
        # If all tests have finished, prompt to save results.
        if all(res in ["PASS", "FAIL"]
               for t, res in zip(self.tests, self.test_results.values())):
            self.prompt_save_results()
            
        # If auto-advance is enabled, automatically run the next test.
        if self.auto_advance_var.get() and passed:
            names = [t["name"] for t in self.tests]
            idx = names.index(test_name)
            if idx + 1 < len(names):
                next_test = names[idx + 1]
                self.root.after(200, lambda nt=next_test: self.run_test(nt))
    
    def user_pass(self):
        """User marks a manual test as passed."""
        current_text = self.status_label.cget("text")
        current_test = current_text.split("requires")[0].strip()
        self.complete_test(current_test, True)
    
    def user_fail(self):
        """User marks a manual test as failed."""
        current_text = self.status_label.cget("text")
        current_test = current_text.split("requires")[0].strip()
        self.complete_test(current_test, False)
    
    def prompt_save_results(self):
        """Prompt the user to save test results once all tests are completed."""
        if messagebox.askyesno("Save Results", "All tests completed. Do you want to save the results?"):
            self.save_results()
    
    def open_results(self):
        """Open a previously saved results file."""
        file_path = filedialog.askopenfilename(title="Open Test Results", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r") as f:
                data = f.read()
            messagebox.showinfo("Test Results", data)

    def print_label(self):
        self.status_label.config(text=f"Creating label for {self.model_number} with {self.mac_addr}\n")
        # self._log(f"Creating label with {self.mac_addr}\n")
        img = create_label(self.mac_addr, self.model_number)
        # Define the target directory and file path for label
        output_dir = os.path.join(os.getcwd(), "Res/img")
        output_path = os.path.join(output_dir, "label.png")

        os.makedirs(output_dir, exist_ok=True)
        img.save(output_path)
        self.status_label.config(text="Label created. Printing...\n")

        def _run_printer():
            cmd = [
                "Res/ptouch-print/build/ptouch-print",
                "--image",
                "Res/img/label.png"
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
            except Exception as e:
                # Could not even launch the process
                return False, f"Execution error: {e}"

            if result.returncode != 0:
                # Printing failed; include stdout/stderr
                err = result.stderr.strip() or result.stdout.strip()
                return False, f"Printer error (code {result.returncode}): {err}"
            return True, None

    # Try printing, loop on user retry
        while True:
            success, err_msg = _run_printer()
            if success:
                self.status_label.config(text="Print succeeded.\n")
                break
            else:
                # Show error + “Retry / Cancel”
                ans = messagebox.askretrycancel("Print Error", f"Printing failed:\n{err_msg}\n\nRetry?")
                if ans:
                    # User chose Retry — repeat the loop
                    continue
                else:
                    # Cancel – break out and indicate failure
                    self.status_label.config(text="Print cancelled by user.\n")
                    break
    
    def save_results(self):
        """
        Save test results to a file.
        The default filename is configurable.
        After saving, the tests are reset for a new device.
        """
        # default_filename = self.mac_addr + ".txt"  # Configurable default filename.
        # file_path = filedialog.asksaveasfilename(defaultextension=".txt",
        #                                          initialfile=default_filename,
        #                                          filetypes=[("Text Files", "*.txt")])
        # if file_path:
        #     with open(file_path, "w") as f:
        #         for test, result in self.test_results.items():
        #             f.write(f"{test}: {result}\n")
        #     messagebox.showinfo("Save Results", "Test results saved successfully.")
        self.mac_addr = get_next_available_mac(False) # Mark the current MAC address as read
        current_mac = self.mac_addr
        expected = current_mac[-4:]  # last 4 hex digits
        if self.print_labels_var.get(): # Print labels if the checkbox is checked
            self.print_label()
        
        # Ask user with retries
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            prompt = f"Enter last 4 hex digits of MAC ({expected[:1]}…):"
            user_input = simpledialog.askstring("Verify MAC", prompt)

            if user_input is None:
                # User pressed Cancel
                messagebox.showinfo("Save Results", "Save cancelled by user.")
                return

            user_input = user_input.strip().upper()
            if user_input == expected:
                # Verification succeeded
                break
            else:
                # Wrong entry
                if attempt < MAX_RETRIES - 1:
                    messagebox.showwarning("Incorrect Entry",
                        f"Incorrect. You have {MAX_RETRIES - attempt - 1} retries left.")
                    continue
                else:
                    messagebox.showerror("Verification Failed", "MAC verification failed. Not saving results.")
                    return
        
        append_test_results(self.test_results, self.mac_addr) 
        logger.info(f"Test results saved for MAC {self.mac_addr}")
        self.reset_tests()
        # Get a new mac address for the next device
        self.mac_addr = get_next_available_mac(True)
    
    def reset_tests(self):
        """Reset all tests for the next device."""
        self.clear_log()
        for test in self.tests:
            self.test_results[test["name"]] = "Pending"
            btn = self.test_buttons.get(test["name"])
            if btn:
                btn.config(text=f"{test['name']}: Pending", fg="black")
        self.status_label.config(text="Select a test to view details")
    
    def configure_parameters(self):
        """Popup a window to allow user to edit MAC address, serial port, and model number simultaneously."""
        
        # Create a new Toplevel window (acts as a modal dialog)
        window = tk.Toplevel(self.root)
        window.title("Configure Test Parameters")
        
        # --- MAC Address field (first parameter) ---
        self.mac_addr = get_next_available_mac(False)  # Read the MAC address from the Excel file
        tk.Label(window, text="MAC Address:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        mac_entry = tk.Entry(window, width=30, state="normal")
        mac_entry.insert(0, self.mac_addr)  # Pre-fill with the current MAC address
        mac_entry.config(state="disabled")                # now greyed out, contents fixed
        mac_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # --- Server IP Address field ---
        tk.Label(window, text="Server IP:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        sip_entry = tk.Entry(window, width=30)
        sip_entry.insert(0, self.server_ip)  # Pre-fill with the current IP address
        sip_entry.grid(row=1, column=1, padx=5, pady=5)

        # --- Serial Port field ---
        tk.Label(window, text="Serial Port:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        serial_entry = tk.Entry(window, width=30)
        serial_entry.insert(0, self.serial_port)
        serial_entry.grid(row=2, column=1, padx=5, pady=5)

        # --- Mini PCIe Slot field ---
        tk.Label(window, text="Mini PCIe Slot:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        slot_combobox = ttk.Combobox(window, width=28, values=["Slot 1", "Slot 2"])
        slot_combobox.set(self.minipcie_slot)  # Set to current value or default
        slot_combobox.grid(row=3, column=1, padx=5, pady=5)
        
        # --- Model Number field ---
        tk.Label(window, text="Model Number:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        model_entry = tk.Entry(window, width=30)
        model_entry.insert(0, self.model_number)
        model_entry.grid(row=4, column=1, padx=5, pady=5)

        # --- SSID field ---
        tk.Label(window, text="WiFi SSID:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        ssid_entry = tk.Entry(window, width=30)
        ssid_entry.insert(0, self.wifi_ssid)
        ssid_entry.grid(row=5, column=1, padx=5, pady=5)

        # --- WiFi Password field ---
        tk.Label(window, text="WiFi Password:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        wifi_pass_entry = tk.Entry(window, width=30, show="*")
        wifi_pass_entry.insert(0, self.wifi_password)
        wifi_pass_entry.grid(row=6, column=1, padx=5, pady=5)

        # --- WiFi Security Type field ---
        tk.Label(window, text="WiFi Security:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        security_entry = tk.Entry(window, width=30)
        security_entry.insert(0, self.wifi_security)
        security_entry.grid(row=7, column=1, padx=5, pady=5)
        
        # --- OK Button to save changes ---
        def on_ok():
            # self.mac_addr = mac_entry.get()   # MAC address is fixed and not editable
            self.server_ip = sip_entry.get()
            self.serial_port = serial_entry.get()
            self.minipcie_slot = slot_combobox.get()
            self.model_number = model_entry.get()
            self.wifi_ssid = ssid_entry.get()
            self.wifi_password = wifi_pass_entry.get()
            self.wifi_security = security_entry.get().upper()
            if self.wifi_security not in ["OPEN", "WEP", "WPA", "WPA2", "WPA-PSK"]:
                messagebox.showerror("Invalid Security Type", "WiFi Security must be one of: OPEN, WEP, WPA, WPA2")
                return
            # Update the config file with new values
            self.save_config()  # Save current settings to disk
            # Optionally, you can show a message box or log the changes
            # For example:
            # messagebox.showinfo("Parameters Set",
            #                     f"MAC Address: {self.mac_addr}\n"
            #                     f"IP Address: {self.server_ip}\n"
            #                     f"Serial Port: {self.serial_port}\n"
            #                     f"Model Number: {self.model_number}")
            window.destroy()

        tk.Button(window, text="OK", command=on_ok).grid(row=8, column=0, columnspan=2, pady=10)
        
        # Update window to ensure its size is computed.
        window.update_idletasks()

        # Calculate position: top center relative to self.root
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        win_width = window.winfo_reqwidth()
        # Place the popup centered horizontally relative to the main window,
        # and at the top (or a few pixels offset from the top).
        x = root_x + (root_width // 2) - (win_width // 2)
        y = root_y + 10  # 10 pixels below the top edge of the main window
        window.geometry(f"+{x}+{y}")

        # Make the window modal
        window.grab_set()
    def _on_toggle_auto(self, *args):
        self.auto_advance = self.auto_advance_var.get()              # 
        self.save_config()                                           # write to disk 

    def _on_toggle_print(self, *args):
        self.print_labels = self.print_labels_var.get()
        self.save_config()
        
    def save_config(self):
        # Save the current settings to the config file
        cfg["network"]["sip"] = self.server_ip
        cfg["device"]["serial_port"] = self.serial_port
        cfg["device"]["minipcie_slot"] = self.minipcie_slot
        cfg["device"]["model_number"] = self.model_number
        cfg["device"]["wifi_ssid"] = self.wifi_ssid
        cfg["device"]["wifi_password"] = self.wifi_password
        cfg["device"]["wifi_security"] = self.wifi_security
        cfg["ui"]["auto_advance"] = str(self.auto_advance_var.get())
        cfg["ui"]["print_label"] = str(self.print_labels_var.get())
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            cfg.write(f)

    
    def load_config(self):
        # read settings.ini
        # Load or create defaults
        if os.path.exists(path):
            cfg.read(path)
        else:
            cfg["network"] = {"sip": "192.168.0.1"}
            cfg["device"] = {"serial_port": "/dev/ttyUSB0", "model_number": "IG4-1000", "minipcie_slot": "Slot 1",
                             "wifi_ssid": "SSID", "wifi_password": "Password", "wifi_security": "WPA-PSK"}
            cfg["ui"] = {"auto_advance": "True", "print_label": "True"}
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                cfg.write(f)

        self.server_ip = cfg["network"]["sip"]
        self.serial_port = cfg["device"]["serial_port"]
        self.minipcie_slot = cfg["device"]["minipcie_slot"]
        self.model_number = cfg["device"]["model_number"]
        self.wifi_ssid = cfg["device"]["wifi_ssid"]
        self.wifi_password = cfg["device"]["wifi_password"]
        self.wifi_security = cfg["device"]["wifi_security"]
        self.auto_advance = cfg.getboolean("ui", "auto_advance")
        self.print_labels = cfg.getboolean("ui", "print_label")
    
    def show_mac_generator_popup(self):
        # If already exists, bring to front
        if self.mac_window is not None and self.mac_window.winfo_exists():
            if self.mac_window.state() == "iconic":
                self.mac_window.deiconify()
            self.mac_window.lift()
            self.mac_window.focus_force()
            return

        # create the Toplevel
        window = tk.Toplevel(self.root)
        self.mac_window = window
        window.title("MAC Generator")
        window.resizable(False, False)
        window.transient(self.root)

        # embed the MACGeneratorFrame (pure tk)
        mac_frame = MACGeneratorFrame(window)
        mac_frame.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

        close_btn = tk.Button(window, text="Close", command=window.destroy)
        close_btn.grid(row=1, column=0, sticky="e", padx=12, pady=(0,12))

        def _on_close():
            try:
                self.mac_window = None
            finally:
                window.destroy()

        window.protocol("WM_DELETE_WINDOW", _on_close)

        window.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        win_width = window.winfo_reqwidth()
        x = root_x + (root_width // 2) - (win_width // 2)
        y = root_y + 10
        window.geometry(f"+{x}+{y}")

        window.grab_set()
        window.focus_force()

    def show_help(self):
        """Display help information."""
        if self.help_window is not None and self.help_window.winfo_exists():
            # Window already open, just bring it to front
            self.help_window.lift()
            self.help_window.focus_force()
        else:
            # Create new help window
            self.help_window = HelpCenter(self.root)
    
    def show_about(self):
        """Display help information."""
        messagebox.showinfo(
            f"About",  # Title in title case, no end punctuation
            f"IGv4_test_app_{__version__} application tests IGv4 Boards\n\n"                  
        )

    def contact_support(self):
        """Display help information."""
        messagebox.showinfo(
            "Support",  # Title in title case, no end punctuation
            "email the developer at nafih.ahammed@econtrolsystems.com\n\n"                  
        )

    def manual_reconnect(self):
        """Manually reconnect to the serial port."""
        self.connect_serial()
    
    def connect_serial(self):
        """Attempt to open the serial port and wait for U-Boot prompt before showing device as connected."""
        try:
            if self.serial_conn:
                self.serial_conn.close()
            import serial  # Import here since pyserial is needed for connecting
            self.serial_conn = serial.Serial(self.serial_port, baudrate=115200, timeout=0.1)
            self.status_text.config(text="Waiting for U-Boot prompt...")
            # Initially, do not mark as connected (use red indicator)
            self.update_reconnect_indicator(False)
            self.root.after(100, self.check_uboot_prompt)
        except Exception:
            self.serial_conn = None
            self.status_text.config(text="Disconnected")
            self.update_reconnect_indicator(False)

    
    def update_reconnect_indicator(self, connected):
        """Update the reconnect indicator (green if connected, red if not)."""
        color = "green" if connected else "red"
        self.reconnect_indicator.itemconfig(self.indicator_circle, fill=color)
    
    def check_openwrt_prompt(self):
        # print("Checking for OpenWRT prompt...")
        p1 = '.'
        p2 = '..'
        p3 = '...'
        global patter_state;
        patter_state = patter_state + 1 if patter_state < 3 else 0
        # print("Device connected to OpenWRT.")
        self.status_label.config(text=f"Checking for OpenWRT prompt{p1 if patter_state == 0 else p2 if patter_state == 1 else p3}")
        color = "yellow" if patter_state == 0 else "orange" if patter_state == 1 else "red"
        self.reconnect_indicator.itemconfig(self.indicator_circle, fill=color)
        if self.serial_conn:
            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore").strip()
                if line == "":
                    # If the line is empty, skip processing
                    self.root.after(50, self.check_openwrt_prompt)
                    return
                
                print(f"debug:{line}")
                if OPENWRT_PROMPT in line or line.startswith(OPENWRT_PROMPT_2):
                    print("OpenWRT prompt detected, opening console.")
                    self.serial_conn.write(('\r\n').encode())
                    self.status_text.config(text="Openwrt detected; device connected")
                    self.update_reconnect_indicator(True)
                    self.connection_status = True  # Mark as connected
                    self.terminal_state = "linux"
                    # Enable all test buttons now that the device is connected
                    # for test in self.tests:
                    #     test_name = test["name"]
                    #     btn = self.test_buttons.get(test_name)
                    #     if btn:
                    #         btn.config(state=tk.ACTIVE)
                    # return  # Exit after successful connection
                    self.status_label.config(text="Now you can run tests.")
                    return  # Exit after successful connection
                
                self.root.after(100, self.check_openwrt_prompt)
            except Exception as e:
                print("Error reading serial:", e)
                self.root.after(100, self.check_openwrt_prompt)
        else:
            # If no data is available, check again after a short delay
            print("No serial connection available, retrying...")
            self.root.after(100, self.check_openwrt_prompt)

    
    def check_uboot_prompt(self):
        """
        Look for the "Hit any key to stop autoboot:" prompt.
        When found, send a key to interrupt autoboot and update the status to 'device connected'.
        """
        # print("Checking for U-Boot prompt...")
        if self.serial_conn and self.serial_conn.in_waiting:
            
            # print("Device connected to U-Boot.")
            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore")
                if UBOOT_PROMPT in line:
                # if "Hit any key to stop autoboot" in line: # old prompt 
                    print("U-Boot prompt detected, sending interrupt command.")
                    self.serial_conn.write(('ecsi25').encode())  # Send magic key to interrupt autoboot
                    self.status_text.config(text="U-Boot detected; device connected")
                    self.update_reconnect_indicator(True)
                    self.connection_status = True  # Mark as connected
                    self.terminal_state = "uboot"
                    # Enable all test buttons now that the device is connected
                    for test in self.tests:
                        test_name = test["name"]
                        btn = self.test_buttons.get(test_name)
                        if btn:
                            btn.config(state=tk.NORMAL)
                    return  # Exit after successful connection
            except Exception as e:
                print("Error reading serial:", e)
        self.root.after(100, self.check_uboot_prompt)
    
    def check_serial(self):
        """
        Periodically check every 2 seconds if the serial port is connected.
        If not, try reconnecting.
        """
        if not self.serial_conn:
            self.connect_serial()
            # print("Attempting to connect to serial port...")
        else:
            self.check_uboot_prompt()
        # else:
        #     # terminal_state = self.detect_terminal_state()
        #     # if terminal_state == "uboot":
        #     #     # print("Connected: U-Boot terminal detected")
        #     #     self.connection_status = True
        #     #     self.terminal_state = "uboot"
        #     # elif terminal_state == "linux":
        #     #     # print("Connected: Linux terminal detected")
        #     #     self.connection_status = True
        #     #     self.terminal_state = "linux"
        #     # elif terminal_state == "unknown":
        #     #     # print("Connected: Terminal type unknown")
        #     #     self.connection_status = True
        #     #     self.terminal_state = "unknown"
        #     # else:
        #     #     # print("Serial port connected but no terminal detected")
        #     #     self.connection_status = False
        #     #     self.terminal_state = "unknown"
    
        self.root.after(2000, self.check_serial)

    # def detect_terminal_state(self):
    #     """
    #     Detect whether we're at U-Boot terminal or Linux terminal
    #     Returns: "uboot", "linux", "unknown", or "disconnected"
    #     """
    #     if not self.serial_conn:
    #         return "disconnected"
        
    #     try:
    #         # Send a newline to trigger a prompt
    #         self.serial_conn.write(b'\r\n')
    #         time.sleep(0.1)  # Small delay for response
            
    #         # Read available data
    #         if self.serial_conn.in_waiting > 0:
    #             data = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                
    #             # Check for U-Boot patterns
    #             uboot_patterns = [
    #                 r'=>\s*$',
    #                 r'U-Boot #'
    #             ]
                
    #             # Check for Linux patterns
    #             linux_patterns = [
    #                 r'root@',
    #                 r'#\s*$',
    #             ]
                
    #             # Test patterns                
    #             self.check_uboot_prompt()  # Try to re-establish U-Boot connection
    #             for pattern in uboot_patterns:
    #                 if re.search(pattern, data, re.IGNORECASE):
    #                     return "uboot"
                
    #             for pattern in linux_patterns:
    #                 if re.search(pattern, data, re.IGNORECASE):
    #                     return "linux"
                
    #         return "disconnected"
        
    #     except Exception as e:
    #         print(f"Error detecting terminal state: {e}")
    #         return "unknown"

if __name__ == "__main__":
    success = initialize_logging(clean_logs=True)
    if not success:
        print("Warning: log setup failed, check stderr for details", file=sys.stderr)
    
    logger.info("Starting IGv4 Test Application")
    root = tk.Tk()
    app = HardwareTestApp(root)
    root.mainloop()
