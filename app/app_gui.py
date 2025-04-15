import tkinter as tk
from tkinter import filedialog, messagebox, Menu, simpledialog
from test_definitions import Eth0Test, USBTest, RTCTest, XbeeTest, BatteryTest  # Importing our test classes

class HardwareTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Test Application")
        self.root.minsize(800, 600)
        
        # Default serial port (configurable via the menu)
        self.serial_port = "/dev/ttyUSB0"
        self.model_number = "IG4-1000"
        self.mac_addr = "00019D005000"

        
        # Store test results: "Pending", "PASS", or "FAIL"
        self.test_results = {}
        # Test definitions are stored here along with the reference to the test class.
        self.tests = [
            {"name": "Ethernet Test", "requires_input": False, "class": Eth0Test},
            {"name": "USB Test", "requires_input": False, "class": USBTest},
            {"name": "RTC Test", "requires_input": False, "class": RTCTest},
            {"name": "Xbee Test", "requires_input": False, "class": XbeeTest},
            {"name": "Battery Test", "requires_input": False, "class": BatteryTest},
            # {"name": "LED Test", "requires_input": True, "class": LedTest},
            # {"name": "Button Test", "requires_input": False, "class": ButtonTest},
        ]
        
        # Dictionary to store button widgets (for UI updates)
        self.test_buttons = {}
        
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
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Configure menu
        menu_bar.add_command(label="Configure", command=self.configure_parameters)

        # Help Menu
        help_menu = Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.show_help)
        # help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_separator()
        # help_menu.add_command(label="Contact Support", command=self.contact_support)
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
        
        # Content area split into left and right frames
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left frame: one button per test.
        left_frame = tk.Frame(content_frame, bd=2, relief=tk.SUNKEN)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        for test in self.tests:
            test_name = test["name"]
            btn = tk.Button(left_frame, text=f"{test_name}: Pending", width=20,
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
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        # Force the GUI to update immediately so that new log entries appear in real time.
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
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

        self.status_label.config(text=f"Running {test_name}...")
        if selected_test["requires_input"]:
            # For tests like LED test: Show manual input UI.
            self.enable_user_input()
            self.status_label.config(text=f"{test_name} requires manual verification.\nClick Pass or Fail when ready.")
        else:
            self.disable_user_input()
            # Instantiate the test class passing the current serial port.
            test_class = selected_test["class"]
            if test_class is Eth0Test:
                tester = test_class(port=self.serial_port,  mac_addr=self.mac_addr, debug=True, log_callback=self.log_message)
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
        
        # If all tests (automatic ones) have finished, prompt to save results.
        if all(res in ["PASS", "FAIL"] or (res == "Pending" and t["requires_input"])
               for t, res in zip(self.tests, self.test_results.values())):
            self.prompt_save_results()
    
    def user_pass(self):
        """User marks a manual test as passed."""
        current_test = self.status_label.cget("text").split(" ")[0]
        self.complete_test(current_test, True)
    
    def user_fail(self):
        """User marks a manual test as failed."""
        current_test = self.status_label.cget("text").split(" ")[0]
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
    
    def save_results(self):
        """
        Save test results to a file.
        The default filename is configurable.
        After saving, the tests are reset for a new device.
        """
        default_filename = "test_results.txt"  # Configurable default filename.
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 initialfile=default_filename,
                                                 filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w") as f:
                for test, result in self.test_results.items():
                    f.write(f"{test}: {result}\n")
            messagebox.showinfo("Save Results", "Test results saved successfully.")
            self.reset_tests()
    
    def reset_tests(self):
        """Reset all tests for the next device."""
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
        tk.Label(window, text="MAC Address:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        mac_entry = tk.Entry(window, width=30)
        mac_entry.insert(0, self.mac_addr)  # Pre-fill with the current MAC address
        mac_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # --- Serial Port field ---
        tk.Label(window, text="Serial Port:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        serial_entry = tk.Entry(window, width=30)
        serial_entry.insert(0, self.serial_port)
        serial_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # --- Model Number field ---
        tk.Label(window, text="Model Number:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        model_entry = tk.Entry(window, width=30)
        model_entry.insert(0, self.model_number)
        model_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # --- OK Button to save changes ---
        def on_ok():
            self.mac_addr = mac_entry.get()
            self.serial_port = serial_entry.get()
            self.model_number = model_entry.get()
            # Optionally, you can show a message box or log the changes
            # For example:
            # messagebox.showinfo("Parameters Set",
            #                     f"MAC Address: {self.mac_addr}\n"
            #                     f"Serial Port: {self.serial_port}\n"
            #                     f"Model Number: {self.model_number}")
            window.destroy()

        tk.Button(window, text="OK", command=on_ok).grid(row=3, column=0, columnspan=2, pady=10)
        
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
    
    def show_help(self):
        """Display help information."""
        messagebox.showinfo("Help", "This application conducts hardware tests via serial port.\n\n"
                             "• Use the File menu to open/save results and configure parameters.\n"
                             "• Use the buttons on the left to run tests.\n"
                             "• For tests requiring manual input, use the Pass/Fail buttons on the right.\n"
                             "• Use the Reconnect button to manually recheck the serial connection.")
    
    def manual_reconnect(self):
        """Manually reconnect to the serial port."""
        self.connect_serial()
    
    def connect_serial(self):
        """Attempt to open the serial port. Update the reconnect indicator accordingly."""
        try:
            if self.serial_conn:
                self.serial_conn.close()
            import serial  # Import here since pyserial is needed for connecting
            self.serial_conn = serial.Serial(self.serial_port, baudrate=115200, timeout=0.1)
            self.status_text.config(text="Connected")
            self.update_reconnect_indicator(True)
            self.root.after(100, self.check_uboot_prompt)
        except Exception:
            self.serial_conn = None
            self.status_text.config(text="Disconnected")
            self.update_reconnect_indicator(False)
    
    def update_reconnect_indicator(self, connected):
        """Update the reconnect indicator (green if connected, red if not)."""
        color = "green" if connected else "red"
        self.reconnect_indicator.itemconfig(self.indicator_circle, fill=color)
    
    def check_uboot_prompt(self):
        """
        Look for the "Hit any key to stop autoboot:" prompt.
        If found, send a key to interrupt autoboot.
        """
        if self.serial_conn and self.serial_conn.in_waiting:
            try:
                line = self.serial_conn.readline().decode("utf-8", errors="ignore")
                if "Hit any key to stop autoboot:" in line:
                    self.serial_conn.write(b'\n')
                    self.status_text.config(text="U-Boot detected, autoboot stopped")
            except Exception as e:
                print("Error reading serial:", e)
    
    def check_serial(self):
        """
        Periodically check every 2 seconds if the serial port is connected.
        If not, try reconnecting.
        """
        if not self.serial_conn:
            self.connect_serial()
        else:
            self.check_uboot_prompt()
        self.root.after(2000, self.check_serial)

if __name__ == "__main__":
    root = tk.Tk()
    app = HardwareTestApp(root)
    root.mainloop()
