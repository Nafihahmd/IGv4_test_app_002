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
            f'setenv bootargs "console=ttyS0,115200 ethaddr0={formatted_mac}"',
            'setenv ipaddr 192.168.0.218',
            f'setenv serverip {self.server_ip}',
            'setenv netmask 255.255.255.0',
            'saveenv',
        ]
        self.test_cmd = f'ping {self.server_ip}'
        self.expect = 'host 192.168.0.1 is alive'

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
    
    
# USB Tester
class USBTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        print("Initializing USB Test")
        # Define the setup and test commands for a USB test
        self.setup_cmds = [
            'usb start',
        ]
        self.test_cmd = 'usb tree'
        self.expect = 'u-boot EHCI Host Controller'

    def run(self):
        try:
            self.connect()
            success = self.run_test_case(self.setup_cmds, self.test_cmd, self.expect)
        except Exception as e:
            print("Error during USB test:", e)
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
            'setenv stdin nuc980_serial0,nuc980_serial2',
            'setenv stdout nuc980_serial0,nuc980_serial2',
            'setenv stdin nuc980_serial0',
            'setenv stdout nuc980_serial0',
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
        # Define the setup and test commands for a USB test
        self.setup_cmds = [
            'mw 0xb00041b0 0x40000',
            'md 0xb00041b0 1',
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
        self.setup_cmds = 'gpio toggle 166' # GPIO PF.6

    def run(self):
        try:
            self.connect()
            # success = self.run_batt_test_case(self.setup_cmds, 10)
            for i in range(3):
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