from uboot_tester import UBootTester
import time

# Ethernet Tester
class Eth0Test(UBootTester):
    def __init__(self, mac_addr=None, server_ip=None, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        # Define the setup and test commands for a Ethernet test
        self.mac_addr = mac_addr
        self.server_ip = server_ip
        formatted_mac = ":".join(self.mac_addr[i:i+2] for i in range(0, 12, 2))
        self.setup_cmds = [
            f'setenv ethaddr {formatted_mac}',
            f'setenv bootargs "console=ttyS1,115200 ethaddr0={formatted_mac}"',
            'setenv ipaddr 192.168.0.218',
            f'setenv serverip {self.server_ip}',
            'setenv netmask 255.255.255.0',
            'saveenv',
        ]
        self.test_cmd = f'dhcp'
        self.expect = 'DHCP client bound to address'

    def run(self):
        try:
            self.connect()
           
            # self._log(result.stdout)

            success = self.run_test_case(self.setup_cmds, self.test_cmd, self.expect)
        except Exception as e:
            print("Error during Ethernet test:", e)
            success = False
        finally:
            self.disconnect()
        return success
    
# RTC Tester
class RTCTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing RTC Test")
        # Define the setup and test commands for a USB test
        self.test_cmd = 'date'

    def run(self):
        try:
            self.connect()
            success = self.run_rtc_test_case(self.test_cmd, 3)
        except Exception as e:
            print("Error during RTC test:", e)
            success = False
        finally:
            self.disconnect()
        return success
    
# Xbee Tester
class XbeeTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing Xbee Test")
        # Define the setup and test commands for a USB test
        self.setup_cmds = [
            'setenv stdin nuc980_serial1,nuc980_serial2',
            'setenv stdout nuc980_serial1,nuc980_serial2',
            'setenv stdin nuc980_serial1',
            'setenv stdout nuc980_serial1',
        ]
        # self.test_cmd = 'AT\r'

    def run(self):
        try:
            self.connect()
            success = self.run_xbee_test_case(self.setup_cmds, 2)
        except Exception as e:
            print("Error during Xbee test:", e)
            success = False
        finally:
            self.disconnect()
        return success
    
# BatteryTest
class BatteryTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing Battery Test")
        # Define the setup and test commands for a Battery test
        self.setup_cmds = [
            # 'mw 0xb000007c 0x00000000',   # Set MFP to GPIO on PB.13 (SYS_BA+0x07C)  SYS_BA=0xB000_0000 
            # 'md 0xb000007c 1',            # Read back to check if it is set
            'mw 0xb0004030 0x4000000',    # Enable pullup on PB.13 (GPIO_BA + 0x070)     GPIO_BA=0xB000_4000 
            'md 0xb0004030 1',            # Read back to check if it is set
        ]

    def run(self):
        try:
            self.connect()
            success = self.run_batt_test_case(self.setup_cmds, 10)
        except Exception as e:
            print("Error during Battery test:", e)
            success = False
        finally:
            self.disconnect()
        return success
    
# RelayTest
class RelayTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing Relay Test")
        # Define the setup and test commands for a Relay test
        # Global GPIO Number = (Port Index × 32) + Pin Number
        self.setup_cmds = 'gpio toggle 166' # GPIO PF.6 (5x32 + 13)

    def run(self):
        try:
            self.connect()
            # success = self.run_batt_test_case(self.setup_cmds, 10)
            for i in range(2):
                self.send_command_quick(self.setup_cmds)
                self._log("Relay toggled, (can you hear?)\n")
                time.sleep(1.0)
            return True
        except Exception as e:
            print("Error during Relay test:", e)
            success = False
        finally:
            self.disconnect()
        return success
    
    
# SIMTest
class SIMTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing SIM Test")
        self.setup_cmds = []           # No extra setup needed
        self.test_cmd = "boot"         # U-Boot boot command
        self.expect  = "kmodloader: done loading kernel modules from /etc/modules.d/*"
        self.shell_prompt = "root@(none):"  # Adjust based on your DUT's prompt

    def run(self):
        try:
            # self.connect_openWRT()    #Connect from inside the test script as we need to switch baudrate
            self.connect()  #baudrate 9600 for U-boot
            success = self.run_sim_test_case(self.setup_cmds,  self.test_cmd, self.expect, self.shell_prompt, 10)
        except Exception as e:
            print("Error during Battery test:", e)
            success = False
        finally:
            self.disconnect()
        return success
    
       
# USB Tester
class USBTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing USB Test")
        # Define the setup and test commands for a USB test
        self.setup_cmds = 'lsusb'
        self.expect = [
            'SimTech',
            'Raspberry Pi',
            'ZEPHYR ECS USB',
        ]

    def run(self):
        try:
            self.connect_openWRT()
            success = self.run_usb_test_case(self.setup_cmds, self.expect)
        except Exception as e:
            print("Error during USB test:", e)
            success = False
        finally:
            self.disconnect()
        return success
       
# BLE Tester
# To-Do: Make it automatic
class BLETest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing BLE Test")
        # Define the setup and test commands for a USB test
        self.setup_cmds = ''
        self.expect = []

    def run(self):
        try:
            self._log("Check nRF BLE is available")
            return True
        except Exception as e:
            print("Error during USB test:", e)
            success = False
        finally:
            self.disconnect()
        return success
    