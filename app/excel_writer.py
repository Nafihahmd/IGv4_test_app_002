import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill

EXCEL_FILE = "test_results.xlsx"

# Define fill colors for pass and fail
GREEN_FILL = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
RED_FILL = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")

def initialize_workbook():
    """Creates a new workbook with headers if it doesn't exist."""
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = "TestResults"
        # Write headers: first column is a timestamp, then one per test.
        headers = ["Timestamp", "MAC Addr", "Ethernet", "USB", "RTC", "Xbee", "Battery", "Relay"]
        ws.append(headers)
        wb.save(EXCEL_FILE)
        print("Created new workbook with headers.")
    else:
        print("Workbook already exists.")

def append_test_results(test_results, mac_addr):
    """
    Appends a new row to the Excel workbook.
    
    test_results: list of tuples. Each tuple is (test_name, result, detail)
    For this example we assume test_results is in the same order as the header columns.
    Only the result value is written and colored.
    """
    if not os.path.exists(EXCEL_FILE):
        initialize_workbook()

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
     # Create a timestamp for this row
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Define the order in which tests should appear; adjust as needed.
    test_order = ["Ethernet Test", "USB Test", "RTC Test", "Xbee Test", "Battery Test", "Relay Test"]
    
    # Construct the row: first element is timestamp then one cell for each test.
    row_data = [timestamp] + [mac_addr] +[test_results.get(test, "N/A") for test in test_order]
    ws.append(row_data)
    row_index = ws.max_row  # the new row's index

    # Apply colors based on the results (columns start at 2 because col 1 is the timestamp)
    for col_index, test in enumerate(test_order, start=2):
        cell = ws.cell(row=row_index, column=col_index)
        result = cell.value.strip().upper() if cell.value else ""
        if result == "FAIL":
            cell.fill = RED_FILL

    wb.save(EXCEL_FILE)
    print(f"Test results appended to row {row_index}.")