from uboot_tester import UBootTester
import time
from log import logger

# Ethernet Tester
class Eth0Test(UBootTester):
    def __init__(self, mac_addr=None, server_ip=None, port='/dev/ttyUSB0', slot='Slot 1', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        # Define the setup and test commands for a Ethernet test
        self.mac_addr = mac_addr
        self.server_ip = server_ip
        linux_port = 'ttyS0' if slot.startswith('Slot 1') else 'ttyS1'
        logger.info(f"Initializing Linux Tests on {linux_port}")
        formatted_mac = ":".join(self.mac_addr[i:i+2] for i in range(0, 12, 2))
        self.setup_cmds = [
            f'setenv ethaddr {formatted_mac}',
            f'setenv bootargs "console={linux_port},115200 ethaddr0={formatted_mac}"',
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
            logger.exception("Error during Ethernet test:")
            success = False
        finally:
            self.disconnect()
        return success
    
# RTC Tester
class RTCTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing RTC Test")
        # Define the setup and test commands for a USB test
        self.test_cmd = 'date'

    def run(self):
        try:
            self.connect()
            success = self.run_rtc_test_case(self.test_cmd, 3)
        except Exception as e:
            logger.exception("Error during RTC test:")
            success = False
        finally:
            self.disconnect()
        return success
    
# Xbee Tester
class XbeeTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', slot='Slot 1', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing Xbee Test")
        # Define the setup and test commands for a USB test
        uboot_port = 'nuc980_serial0' if slot.startswith('Slot 1') else 'nuc980_serial1'
        self.setup_cmds = [
            f'setenv stdin {uboot_port},nuc980_serial2',
            f'setenv stdout {uboot_port},nuc980_serial2',
            'mw 0xb0000080 0x33333300',  # Set MFP RST PIN 0
            'gpio set 65',               # Set RST PIN (PC1) high
            'mw 0xb0072024 0x300004e0',  # Set UART2 to 9600 baud rate
            f'setenv stdin {uboot_port}',
            f'setenv stdout {uboot_port}',
        ]
        # self.test_cmd = 'AT\r'

    def run(self):
        try:
            self.connect()
            success = self.run_xbee_test_case(self.setup_cmds, 2)
        except Exception as e:
            logger.exception("Error during Xbee test:")
            success = False
        finally:
            self.disconnect()
        return success
    
# BatteryTest
class BatteryTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing Battery Test")
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
            logger.exception("Error during Battery test:")
            success = False
        finally:
            self.disconnect()
        return success
    
# RelayTest
class RelayTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing Relay Test")
        # Define the setup and test commands for a Relay test
        # Global GPIO Number = (Port Index × 32) + Pin Number
        self.setup_cmds = 'gpio toggle 12' # GPIO PA.12 (0x32 + 12)

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
            logger.exception("Error during Relay test:")
            success = False
        finally:
            self.disconnect()
        return success
    
    
# SIMTest
class SIMTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing SIM Test")
        self.setup_cmds = []           # No extra setup needed
        # self.test_cmd = "boot"         # U-Boot boot command
        # self.expect  = "kmodloader: done loading kernel modules from /etc/modules.d/*"
        # self.shell_prompt = "root@(none):"  # Adjust based on your DUT's prompt

    def run(self):
        try:
            self.connect()
            success = self.run_sim_test_case() #,  self.test_cmd, self.expect, self.shell_prompt, 10)
        except Exception as e:
            logger.exception("Error during SIM test:")
            success = False
        finally:
            self.disconnect()
        return success
    
       
# USB Tester
class USBTest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing USB Test")
        # Define the setup and test commands for a USB test
        self.setup_cmds = 'lsusb'
        self.expect = [
            r"SimTech",
            r"Raspberry Pi",
            r"ZEPHYR ECS[_ ]USB",   # [_ ] means “underscore or space”
        ]

    def run(self):
        try:
            self.connect()
            success = self.run_usb_test_case(self.setup_cmds, self.expect)
        except Exception as e:
            logger.exception("Error during USB test:")
            success = False
        finally:
            self.disconnect()
        return success

# WiFi Tester
class WiFiTest(UBootTester):
    def __init__(self, wifi_ssid=None, wifi_password=None, wifi_security=None, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing WiFi Test")
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.wifi_security = wifi_security  # Options: OPEN, WEP, WPA, WPA2
        # Define the setup and test commands for a WiFi test
        self.setup_cmds = [
            'devmem 0xB00040B0 32 0x02000000', # Reset Esp32
            '''cat > /etc/config/network << 'EOF'
config interface 'loopback'
        option ifname 'lo'
        option proto 'static'
        option netmask '255.0.0.0'

config interface 'lan'
        option ifname 'eth0'
        option proto 'dhcp'
        option netmask '255.255.255.0'

config interface 'wwan'
        option proto 'dhcp'
EOF''',
            f'''cat > /etc/config/wireless <<EOF
config wifi-device 'radio0'
        option type 'mac80211'
        option path 'platform/ahb/b0019000.fmi/mmc_host/mmc1/mmc1:0001/mmc1:0001:1'
        option band '2g'
        option country 'IN'
        option cell_density '0'
        option legacy_rates '1'
        option channel '11'

config wifi-iface 'wifinet0'
        option device 'radio0'
        option mode 'sta'
        option network 'wwan'
        option ssid '{wifi_ssid}'
        option encryption 'psk2'
        option key '{wifi_password}'
EOF''',
            'wifi',               # run in background
            # 'udhcpc -i wlan0 -q -t 5',  # request an IP via udhcpc (OpenWrt's DHCP client)
        ]
        self.test_cmd =['iw dev wlan0 link', # check connection status
                        'ifconfig wlan0',
                        'ifdown wlan0 2>/dev/null || true',  # bring down wlan0 interface
                        ]
        self.expect = ['Connected to',]

    def run(self):
        try:
            self._log("Check WiFi is available")
            self.connect()
            success = self.run_wifi_test_case(self.setup_cmds, self.test_cmd, self.expect, 10)
            return success
        except Exception as e:
            logger.exception("Error during WiFi test:")
            success = False
        finally:
            self.disconnect()
        return success
# BLE Tester
# To-Do: Make it automatic
class BLETest(UBootTester):
    def __init__(self, port='/dev/ttyUSB0', debug=False, log_callback=None):
        super().__init__(port=port, debug=debug, log_callback=log_callback)
        logger.info("Initializing BLE Test")
        # Define the setup and test commands for a USB test
        self.setup_cmds = ''
        self.expect = []

    def run(self):
        try:
            self._log("Check nRF BLE is available")
            return True
        except Exception as e:
            logger.exception("Error during USB test:")
            success = False
        finally:
            self.disconnect()
        return success
    