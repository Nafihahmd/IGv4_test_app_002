"""
MAC generator UI and helpers (pure tkinter, no ttk).
Provides MACGeneratorFrame (tk.Frame) that can be embedded in a Toplevel.
"""
import re
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None


class MACGeneratorFrame(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)

        tk.Label(self, text="Start MAC:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.start_mac_var = tk.StringVar(value="00:01:9D:00:50:00")
        tk.Entry(self, textvariable=self.start_mac_var, width=30).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(self, text="Count (n):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.count_var = tk.StringVar(value="100")
        tk.Entry(self, textvariable=self.count_var, width=30).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(self, text="Output XLSX:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        path_frame = tk.Frame(self)
        path_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        path_frame.columnconfigure(0, weight=1)
        self.out_path_var = tk.StringVar(value="mac_addr.xlsx")
        tk.Entry(path_frame, textvariable=self.out_path_var).grid(row=0, column=0, sticky="ew")
        tk.Button(path_frame, text="Browse...", command=self.browse_output).grid(row=0, column=1, padx=5)

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        tk.Button(btn_frame, text="Generate & Save", command=self.generate_and_save).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Copy to Clipboard", command=self.copy_to_clipboard).grid(row=0, column=1, padx=5)

        self.status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_var, fg="green").grid(row=4, column=0, columnspan=2, pady=(8,0))

    # file dialog
    def browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel workbook","*.xlsx"), ("All files","*.*")])
        if path:
            self.out_path_var.set(path)

    # mac helpers
    def normalize_mac(self, mac_str: str) -> int:
        s = mac_str.strip().lower()
        s = re.sub(r"[^0-9a-f]", "", s)
        if len(s) != 12:
            raise ValueError("MAC must contain 12 hex digits")
        return int(s, 16)

    def format_mac(self, value: int) -> str:
        return "".join(f"{(value >> (8*(5-i))) & 0xff:02X}" for i in range(6))  # Formatting disabed

    def generate_macs(self, start_mac_int: int, count: int):
        max_mac = (1 << 48) - 1
        if start_mac_int + count - 1 > max_mac:
            raise ValueError("Requested range exceeds MAC address space")
        return [self.format_mac(start_mac_int + i) for i in range(count)]

    def get_mac_list(self):
        start = self.start_mac_var.get()
        try:
            start_int = self.normalize_mac(start)
        except ValueError as e:
            raise ValueError(f"Invalid start MAC: {e}")

        try:
            count = int(self.count_var.get())
            if count <= 0:
                raise ValueError("Count must be a positive integer")
        except Exception:
            raise ValueError("Count must be a positive integer")

        return self.generate_macs(start_int, count)

    # persistence
    def save_to_xlsx(self, macs, out_path: str):
        if Workbook is None:
            raise ImportError("openpyxl is required to export XLSX. Install via: pip install openpyxl")
        wb = Workbook()
        ws = wb.active
        ws.title = "MACs"
        ws.append(["Index", "MAC addr", "Status"])
        for i, mac in enumerate(macs, start=1):
            ws.append([i, mac, "available"])
        wb.save(out_path)

    # UI actions
    def generate_and_save(self):
        try:
            macs = self.get_mac_list()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        out_path = self.out_path_var.get().strip()
        if not out_path:
            messagebox.showerror("Output Path", "Please provide an output .xlsx file path")
            return

        try:
            self.save_to_xlsx(macs, out_path)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save XLSX: {e}")
            return

        self.status_var.set(f"Saved {len(macs)} MACs to {out_path}")
        messagebox.showinfo("Success", f"Saved {len(macs)} MAC addresses to:\n{out_path}")

    def copy_to_clipboard(self):
        try:
            macs = self.get_mac_list()
            text = "\n".join(macs)
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status_var.set(f"Copied {len(macs)} MACs to clipboard")
        except Exception as e:
            messagebox.showerror("Error", str(e))