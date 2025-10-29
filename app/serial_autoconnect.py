# serial_autoconnect.py
"""
Serial auto-connector using pyserial.
- Matches device by VID/PID (you provide these).
- No threading: uses a Tkinter-style root.after polling loop.
- Minimal, easy-to-read API for importing into main code.
"""

from typing import Optional, Tuple, Callable, Sequence
import re
import time
import logging

import serial
import serial.tools.list_ports

__all__ = ["SerialAutoConnector"]

logger = logging.getLogger("SerialAutoConnector")
logger.addHandler(logging.NullHandler())


class SerialAutoConnector:
    """
    Simple auto connector for a USB-serial device identified by VID/PID.

    Usage:
        connector = SerialAutoConnector(
            vid_pid=(0x0403, 0x6001),
            baudrate=115200,
            prompt_patterns=[r"=>", r"U-Boot"],
            reconnect_interval_ms=2000,
            on_connected=your_callback,
            on_disconnected=your_callback_disconnected,
        )
        connector.start_polling(root)   # root is a tkinter.Tk or similar with .after
        ...
        connector.stop()
    """

    def __init__(
        self,
        vid_pid: Tuple[int, int],
        baudrate: int = 115200,
        timeout: float = 0.1,
        reconnect_interval_ms: int = 500,
        prompt_patterns: Optional[Sequence[str]] = None,
        on_connected: Optional[Callable[[serial.Serial], None]] = None,
        on_disconnected: Optional[Callable[[], None]] = None,
    ):
        if not isinstance(vid_pid, tuple) or len(vid_pid) != 2:
            raise ValueError("vid_pid must be a tuple (vid, pid) of integers")

        self.vid_pid = vid_pid
        self.baudrate = baudrate
        self.timeout = timeout
        self.reconnect_interval_ms = int(reconnect_interval_ms)
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected

        if prompt_patterns is None:
            prompt_patterns = [r"=>", r"U-Boot", r"uboot"]

        self.prompt_re = re.compile("|".join(f"(?:{p})" for p in prompt_patterns), re.IGNORECASE)

        self.serial_conn: Optional[serial.Serial] = None
        self._running = False
        self._seen_prompt = False
        self._last_port: Optional[str] = None

    # ------- device discovery -------
    def _find_port_for_vidpid(self) -> Optional[str]:
        """Return device path (eg /dev/ttyUSB0 or COM3) matching the configured VID/PID."""
        vid, pid = self.vid_pid
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # Some platforms report vid/pid as ints, some as None.
            if getattr(p, "vid", None) == vid and getattr(p, "pid", None) == pid:
                logger.info("Found device %s (vid:pid=%04x:%04x)", p.device, vid, pid)
                return p.device
        return None

    # ------- connect / disconnect -------
    def connect_serial(self) -> bool:
        """Try to open the serial port for the configured VID/PID. Returns True on success."""
        port = self._find_port_for_vidpid()
        if not port:
            logger.debug("No matching serial device found for VID:PID %04x:%04x", *self.vid_pid)
            return False

        # If already connected to same port and open, do nothing
        if self.serial_conn and getattr(self.serial_conn, "port", None) == port and self.serial_conn.is_open:
            return True

        # Close any previous connection
        self.close()

        try:
            logger.info("Opening %s @ %d", port, self.baudrate)
            conn = serial.Serial(port=port, baudrate=self.baudrate, timeout=self.timeout)
            # small delay so device can stabilize
            time.sleep(0.05)
            # flush any existing data
            try:
                conn.reset_input_buffer()
            except Exception:
                pass
            self.serial_conn = conn
            self._last_port = port
            self._seen_prompt = False
            self.on_connected(conn) # Call the callback
            return True
        except Exception as e:
            logger.warning("Failed to open serial port %s: %s", port, e)
            self.serial_conn = None
            return False

    def close(self):
        """Close open serial connection, if any."""
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        self.serial_conn = None
        self._seen_prompt = False
        self._last_port = None

    # ------- prompt detection -------
    def _check_for_prompt(self):
        """Read available data and look for prompt patterns. Call on_connected once."""
        if not self.serial_conn:
            return

        try:
            data = self.serial_conn.read(1024)
            if not data:
                return
            try:
                text = data.decode(errors="ignore")
            except Exception:
                text = str(data)
            logger.debug("Serial read: %r", text.strip())

            if self.prompt_re.search(text):
                if not self._seen_prompt:
                    self._seen_prompt = True
                    logger.info("Prompt detected on %s", self.serial_conn.port)
                    if self.on_connected:
                        try:
                            self.on_connected(self.serial_conn)
                        except Exception as cb_e:
                            logger.exception("on_connected callback raised: %s", cb_e)
        except serial.serialutil.SerialException as e:
            logger.warning("Serial exception while reading: %s", e)
            # treat as disconnect
            self._handle_disconnect()
        except Exception:
            logger.exception("Unexpected error while reading serial")

    def _handle_disconnect(self):
        """Internal: handle disconnect event."""
        was_connected = self.serial_conn is not None
        self.close()
        if was_connected and self.on_disconnected:
            try:
                self.on_disconnected()
            except Exception:
                logger.exception("on_disconnected callback raised")

    # ------- periodic / polling -------
    def periodic_check(self):
        """
        Single iteration check:
         - if not connected, try connecting
         - if connected, read for prompt and check health
        """
        # try to connect when there is no open port
        if not self.serial_conn or not getattr(self.serial_conn, "is_open", False):
            connected = self.connect_serial()
            if not connected:
                # nothing to read this pass
                return

        # connected: check prompt and basic health
        #self._check_for_prompt()

        # simple health probe: access in_waiting to detect sudden removal on some platforms
        try:
            _ = self.serial_conn.in_waiting
        except Exception as e:
            logger.info("Serial port probably removed: %s", e)
            self._handle_disconnect()

    def start_polling(self, root):
        """
        Start polling using root.after. `root` must support .after(ms, callable).
        Safe to call from UI/main thread only.
        """
        if self._running:
            logger.debug("Polling already running")
            return

        self._running = True

        def _tick():
            if not self._running:
                return
            try:
                self.periodic_check()
            finally:
                root.after(self.reconnect_interval_ms, _tick)

        # first immediate call, then scheduled calls
        root.after(0, _tick)

    def stop(self):
        """Stop polling and close connection."""
        self._running = False
        # do not call callbacks from stop; just close
        self.close()
