import serial
import time
import re

class UBootTester:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=0.1, debug=False, log_callback=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.debug = debug
        self.log_callback = log_callback

    def _log(self, msg):
        # Optionally log to GUI status and/or console
        if self.debug:
            print("[DEBUG]", msg)
        if self.log_callback:
            self.log_callback(msg)
            
    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        time.sleep(0.5)
            
    def connect_openWRT(self):
        self.ser = serial.Serial(self.port, 115200, timeout=self.timeout)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        time.sleep(0.5)

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _debug_print(self, msg):
        if self.debug:
            print("[DEBUG]", msg, end='')

    def send_command_quick(self, command):
        """Send config/setup commands quickly. Print any received output if debug is on."""
        if not self.ser or not self.ser.is_open:
            raise Exception("Serial port not open")

        self.ser.write((command + '\r\n').encode())
        time.sleep(0.2)

        end_time = time.time() + 0.2
        while time.time() < end_time:
            if self.ser.in_waiting:
                self._log(".")
                data = self.ser.read(self.ser.in_waiting)
                self._debug_print(data.decode(errors='ignore'))
            time.sleep(0.05)

    def send_and_wait_for_output(self, command, expect, timeout=10):
        if not self.ser or not self.ser.is_open:
            raise Exception("Serial port not open")

        self.ser.reset_input_buffer()
        self.ser.write((command + '\r\n').encode())
        self._log(f"Waiting for result (up to {timeout} seconds)...\n")

        output = b''
        end_time = time.time() + timeout

        while time.time() < end_time:
            if self.ser.in_waiting:
                self._log(".")
                chunk = self.ser.read(self.ser.in_waiting)
                output += chunk
                self._debug_print(chunk.decode(errors='ignore'))
                if expect.encode() in output:
                    self.ser.write(b'\x03')  # Send Ctrl+C to stop the command
                    return output.decode(), True
            time.sleep(0.2)

        return output.decode(), False

    def run_test_case(self, setup_cmds, test_cmd, expect, wait_time=10):
        self._log("Sending setup commands...\n")
        for cmd in setup_cmds:
            print(f"  -> {cmd}")
            self.send_command_quick(cmd)
            
        time.sleep(1.0)  # Guard time
        self._log(f"\nRunning test command: {test_cmd}\n")
        output, success = self.send_and_wait_for_output(test_cmd, expect, timeout=wait_time)

        self._log("Final Output:\n")
        self._log(output)

        return success
    
    # RTC Tester
    def check_time_difference_within_tolerance(self, text, time_elapsed):
        # Extract time strings using regular expression
        time_pattern = r'Time:\s*(\d+:\d+:\d+)'
        times = re.findall(time_pattern, text)
        self._log(text)
    
        if len(times) != 2:
            raise ValueError("Expected exactly two time instances in the text.")
    
        # Function to convert time string to total seconds
        def to_seconds(time_str):
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
    
        # Calculate time difference in seconds
        time1 = to_seconds(times[0])
        time2 = to_seconds(times[1])
        delta = abs(time2 - time1)
        
        # Check if delta is within +/-10% of time_elapsed
        lower_bound = 0.5 * time_elapsed
        upper_bound = 1.5 * time_elapsed
        success = lower_bound <= delta <= upper_bound
        
        output = f"Time 1: {times[0]}, Time 2: {times[1]}, Delta: {delta} seconds\n"
        # self._log(output)
        
        return output, success
    
    def run_rtc_test_case(self, test_cmd, wait_time=2):
        self._log("Reading time...\n")
        self.ser.write((test_cmd + '\n').encode())
        for i in range(wait_time, 0, -1):
            self._log(f"Wait {i} seconds\n")
            time.sleep(1)
            
        self._log("Reading time again\n")
        self.ser.write((test_cmd + '\n').encode())       
        time.sleep(0.5)
        # Reading the output
        output = self.ser.read(self.ser.in_waiting)
        output_decoded = output.decode(errors='ignore')
        # self._log(output_decoded)

        output, success = self.check_time_difference_within_tolerance(output_decoded, wait_time)

        self._log("Final Output:\n")
        self._log(output)

        return success

#Xbee Tester    
    def run_xbee_test_case(self, setup_cmds, wait_time=2):
        self._log("Sending setup command \n")
        for cmd in setup_cmds[:2]:
            print(f"  -> {cmd}")
            self.send_command_quick(cmd)

        time.sleep(1.2)   # Guard time
        self._log("Sending setup command +++\n")
        self.ser.write(('+++').encode())
        time.sleep(1.2)   # Guard time
        self.ser.write(('\n').encode())
        for i in range(wait_time, 0, -1):
            self._log(f"Wait {i} seconds\n")
            time.sleep(1)
            
        self._log("Sending AT\n")
        self.ser.write(('AT\r').encode())       
        time.sleep(0.5)
        # Reading the output
        output = self.ser.read(self.ser.in_waiting)
        output_decoded = output.decode(errors='ignore')
        # self._log(output_decoded)

        # self._log("Final Output:\n")
        # self._log(output_decoded)
        time.sleep(0.5)
        #self._log("Undoing Configurations \n")
        for cmd in setup_cmds[2:]:
            print(f"  -> {cmd}")
            self.send_command_quick(cmd)
        time.sleep(0.5)

        if "=> OK" in output_decoded:
            return True
        else:
            return False


#Battery Tester    
    def run_batt_test_case(self, setup_cmds, wait_time=2):
        self._log("Sending setup command \n")
        for cmd in setup_cmds:
            print(f"  -> {cmd}")
            self.send_command_quick(cmd)

        time.sleep(.2)   # Guard time
        self._log("Remove power, checking Power fail:\n")
        self.ser.write(('\n').encode())
        for i in range(wait_time, 0, -1):
            self._log(f"Waiting for power removal (auto timeout in {i} seconds)\n")            
            self.ser.write(('gpio input 201\n').encode())
            output = self.ser.read(self.ser.in_waiting)
            output_decoded = output.decode(errors='ignore')
            if "value is 0" in output_decoded:
                self._log("Power fail detected\n")
                break
            time.sleep(1)
            
        # Reading the output
        # output = self.ser.read(self.ser.in_waiting)
        # output_decoded = output.decode(errors='ignore')

        self._log("Final Output:\n")
        self._log(output_decoded)
        time.sleep(0.5)

        if "value is 0" in output_decoded:
            return True
        else:
            return False
        
# SIM tester
    def run_sim_test_case(self, setup_cmds, test_cmd, expect, shell_prompt, wait_time=10):
        # 1) Issue the boot command
        self._log(f">>> Sending boot command\n")
        self.ser.write((test_cmd + '\r\n').encode())
        time.sleep(0.5)  # Guard time

        self.disconnect()  # Disconnect from U-Boot
        self.connect_openWRT()
        # 2) Wait for OpenWRT to finish loading modules
        self._log(">>> Waiting for OpenWRT modules to finish loading...\n")
        if not self._wait_for_expected(expect, timeout=300):
            self._log(">>> ERROR: Timed out waiting for kmodloader\n")
            return False

        # 3) Get a shell prompt
        self._log(">>> Sending Enter to get shell prompt...\n")
        self.ser.write(b'\r\n')
        # Wait for shell prompt
        if not self._wait_for_expected(shell_prompt, timeout=120):
            self._log(">>> ERROR: Timed out waiting for shell prompt\n")
            return False

        # 4) Set up ttyUSB2 and send AT commands
        self._log(">>> Configuring /dev/ttyUSB2 and sending AT commands...\n")
        # Set baud rate (adjust if necessary)
        # self.ser.write(b'stty -F /dev/ttyUSB2 115200 cs8 -cstopb -parenb\r\n')
        time.sleep(0.1)
        
        # Start background process to read from ttyUSB2
        self.ser.write(b'cat /dev/ttyUSB2 &\r\n')
        time.sleep(0.1)  # Allow time for background process to start

        # Send AT commands
        self.ser.write(b'echo -e "AT\\r" > /dev/ttyUSB2\r\n')
        time.sleep(0.1)
        self.ser.write(b'echo -e "AT+CCID\\r" > /dev/ttyUSB2\r\n')
        time.sleep(0.1)

        # 5) Capture output and check for responses
        output = self._read_serial(timeout=10)
        # self._log(f"Output received:\n{output}")   #Uncomment for debugging

        # Check for the CCID pattern (e.g., "+CCID: 89919509129689902417")
        ccid_pattern = r'\+CCID:\s*\d+'  # Matches "+CCID:" followed by optional whitespace and digits
        match = re.search(ccid_pattern, output)

        if match:
            self._log(f">>> SIM card detected (CCID: {match.group()})\n")
            return True
        else:
            self._log(">>> ERROR: SIM card not detected (no valid CCID found)\n")
            return False

    def _wait_for_expected(self, expect_pattern, timeout=30):
        """Wait for expected pattern in serial output."""
        end_time = time.time() + timeout
        while time.time() < end_time:
            line = self.ser.readline().decode('utf-8', errors='ignore')
            if line:
                if self.debug:
                    print(line.strip())
                if expect_pattern in line:
                    return True
        return False

    def _read_serial(self, timeout=10):
        """Read all available serial data for a specified duration."""
        output = []
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                output.append(data)
            time.sleep(0.1)
        return ''.join(output)

# USB Tester
    def run_usb_test_case(self, setup_cmds, expect):
        # 1) Issue the boot command
        self._log(f">>> Sending lsusb command\n")
        self.ser.write((setup_cmds + '\r\n').encode())
        self.ser.flush()
        time.sleep(0.5)     # Guard time
        output = self._read_serial(timeout=1)        
        self._log(f"Output received:\n{output}")   #Uncomment for debugging

        # 2) Check MPCIe slot 1
        if expect[0] not in output:
            self._log(">>> ERROR: no SimCOM device found\n")
            return False
        self._log("[.] Found SIMCom USB\n")
        
        # 3) Check MPCIe slot 2
        if expect[1] not in output:
            self._log(">>> ERROR: no Rpi Pico device found\n")
            return False
        self._log("[.] Found Rpi Pico USB\n")

        # 4) nRF device
        if expect[2] not in output:
            self._log(">>> ERROR: no NRF device found\n")
            return False
        self._log("[.] Found nRF USB\n")
                
        self._log(">>> Test Passed\n")
        return True

    def _read_serial(self, timeout=10):
        """Read all available serial data for a specified duration."""
        output = []
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                output.append(data)
            time.sleep(0.1)
        return ''.join(output)