# DDR Pack Downloader v0.4
# Created by: void
#
# v0.4 changes:
# - Progress bars now actually track download percentage (previously stuck at 0%)
# - Recency labels and progress/status labels no longer overlap in the grid
# - All Tkinter widget updates from background threads now go through root.after()
#   (fixes intermittent freezes/crashes caused by cross-thread Tk calls)
# - Progress UI updates are throttled (~10/sec) instead of firing on every 1KB chunk
# - Larger download chunk size (64KB) for fewer, cheaper progress updates
# - Handles missing/zero Content-Length (switches that pack's bar to indeterminate mode)
# - Download errors are now caught and shown in the status label instead of hanging silently

import os
import tkinter as tk
from tkinter import ttk, Entry, StringVar
import requests
from lxml import html
import zipfile
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor
import time
import threading
import datetime

# Dictionary of DDR packs
DDRPacks = {
    'Dance Dance Revolution': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=37',
    'Dance Dance Revolution 2ndMIX': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=32',
    'Dance Dance Revolution 3rdMIX': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=38',
    'Dance Dance Revolution 4thMIX': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=39',
    'Dance Dance Revolution 5thMIX': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=30',
    'Dance Dance Revolution 6thMIX DDRMAX': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=40',
    'Dance Dance Revolution 7thMIX DDRMAX2': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=31',
    'Dance Dance Revolution EXTREME': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=41',
    'Dance Dance Revolution SuperNOVA': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1',
    'Dance Dance Revolution SuperNOVA 2': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=77',
    'Dance Dance Revolution X': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=295',
    'Dance Dance Revolution X2': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=546',
    'Dance Dance Revolution X3 vs 2ndMIX': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=802',
    'Dance Dance Revolution 2013': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=845',
    'Dance Dance Revolution 2014': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=864',
    'Dance Dance Revolution A': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1148',
    'Dance Dance Revolution A20': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1292',
    'Dance Dance Revolution A20 PLUS': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1293',
    'Dance Dance Revolution A3': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1509',
    'Dance Dance Revolution GRAND PRIX': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1456',
    'Dance Dance Revolution WORLD': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1709'
 }

# Dictionary of DDR Pages
DDRInfo = {
    'Dance Dance Revolution': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=37',
    'Dance Dance Revolution 2ndMIX': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=32',
    'Dance Dance Revolution 3rdMIX': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=38',
    'Dance Dance Revolution 4thMIX': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=39',
    'Dance Dance Revolution 5thMIX': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=30',
    'Dance Dance Revolution 6thMIX DDRMAX': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=40',
    'Dance Dance Revolution 7thMIX DDRMAX2': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=31',
    'Dance Dance Revolution EXTREME': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=41',
    'Dance Dance Revolution SuperNOVA': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1',
    'Dance Dance Revolution SuperNOVA 2': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=77',
    'Dance Dance Revolution X': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=295',
    'Dance Dance Revolution X2': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=546',
    'Dance Dance Revolution X3 vs 2ndMIX': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=802',
    'Dance Dance Revolution 2013': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=845',
    'Dance Dance Revolution 2014': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=864',
    'Dance Dance Revolution A': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1148',
    'Dance Dance Revolution A20': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1292',
    'Dance Dance Revolution A20 PLUS': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1293',
    'Dance Dance Revolution A3': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1509',
    'Dance Dance Revolution GRAND PRIX': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1456',
    'Dance Dance Revolution WORLD': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1709'
 }

# Create a function to scrape recency from DDR Info Pages
def scrape_recency_lxml(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            parsed_page = html.fromstring(response.text)
            recency_elements = parsed_page.xpath('/html/body/div[4]/div[2]/div[1]/div/a/span')  # Update XPath
            if recency_elements:
                recency = recency_elements[0].text_content().strip()
                return recency
    except Exception as e:
        print(f"Error scraping recency: {e}")
    return "N/A"

# Create the main window
root = tk.Tk()
root.title("DDR Pack Downloader")

# Set window icon
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, 'assets\\icon.ico')  # Icon
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# Function to save the last run date to a file
def save_last_run_date(last_run_date):
    try:
        # Specify a relative path to the file
        file_path = os.path.join(os.path.dirname(__file__), 'assets\\last_run_date.txt')
        with open(file_path, 'w') as file:
            file.write(last_run_date.strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"Error saving last run date: {e}")

# Function to load the last run date from a file
def load_last_run_date():
    try:
        # Specify a relative path to the file
        file_path = os.path.join(os.path.dirname(__file__), 'assets\\last_run_date.txt')
        with open(file_path, 'r') as file:
            date_str = file.read()
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading last run date: {e}")
        return None

# Function to manually set the last run date
def set_last_run_date():
    manual_date = manual_date_entry.get()
    try:
        last_run_date = datetime.datetime.strptime(manual_date, '%Y-%m-%d').date()
        save_last_run_date(last_run_date)
        last_run_label.config(text=f"Last Run Date: {last_run_date.strftime('%Y-%m-%d')}")
        manual_date_entry.delete(0, tk.END)  # Clear the entry widget after setting the date
    except ValueError:
        print("Invalid date format. Please use the format 'YYYY-MM-DD'.")

# Function to reset progress UI for the packs about to download and record the run date
def create_progress_bars():
    selected_packs = [pack_name for pack_name, pack_var in pack_vars.items() if pack_var.get()]

    for pack_name in selected_packs:
        progress_bar_var[pack_name].stop()
        progress_bar_var[pack_name]['mode'] = 'determinate'
        progress_bar_var[pack_name]['value'] = 0
        progress_label_var[pack_name].set("Queued...")

    # Update the last run date when creating progress bars
    last_run_date = datetime.date.today()
    save_last_run_date(last_run_date)
    last_run_label.config(text=f"Last Run Date: {last_run_date.strftime('%Y-%m-%d')}")

# How often we're willing to push a UI update to the main thread, in seconds.
# 1024-byte chunks can fire thousands of updates/sec on a fast connection, which
# floods the Tkinter event queue and is what causes the UI to appear to "freeze"
# (it's not actually frozen, it's just working through a huge backlog of queued
# callbacks). Throttling to ~10/sec keeps it smooth and responsive.
UI_UPDATE_INTERVAL = 0.1


def _set_progress_ui(pack_name, text, percent=None, indeterminate=False):
    """Thread-safe helper: schedules a widget update on the main thread.
    Never touch progress_label_var / progress_bar_var directly from a
    worker thread -- Tkinter is not thread-safe and doing so is what
    caused the intermittent freezes/crashes."""
    def _apply():
        progress_label_var[pack_name].set(text)
        bar = progress_bar_var[pack_name]
        if indeterminate:
            if str(bar['mode']) != 'indeterminate':
                bar['mode'] = 'indeterminate'
                bar.start(15)
        else:
            if str(bar['mode']) != 'determinate':
                bar.stop()
                bar['mode'] = 'determinate'
            if percent is not None:
                bar['value'] = percent
    root.after(0, _apply)


# Function to download and extract a pack
def download_and_extract(pack_name, pack_url, destination_folder):
    filename = os.path.join(destination_folder, f'{pack_name}.zip')
    extract_folder = os.path.join(destination_folder, pack_name)

    try:
        response = requests.get(pack_url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 64 * 1024  # 64KB chunks instead of 1KB -- far fewer UI updates
        downloaded_size = 0
        start_time = time.time()
        last_ui_update = 0.0

        with open(filename, 'wb') as file:
            for data in response.iter_content(block_size):
                if not data:
                    continue
                file.write(data)
                downloaded_size += len(data)

                now = time.time()
                if now - last_ui_update < UI_UPDATE_INTERVAL:
                    continue  # throttle: skip this update, not worth pushing to the UI yet
                last_ui_update = now

                elapsed_time = now - start_time
                download_speed = downloaded_size / (1024 * 1024 * elapsed_time) if elapsed_time > 0 else 0

                if total_size > 0:
                    percent = 100 * downloaded_size / total_size
                    if download_speed > 0:
                        remaining_size = total_size - downloaded_size
                        eta_seconds = remaining_size / (download_speed * 1024 * 1024)
                        eta_minutes = int(eta_seconds // 60)
                        eta_seconds = int(eta_seconds % 60)
                        eta_text = f"(ETA: {eta_minutes:02d} min {eta_seconds:02d} sec)"
                    else:
                        eta_text = "(ETA: calculating...)"
                    text = (f"Downloading: {downloaded_size / (1024 * 1024):.2f} MB / "
                            f"{total_size / (1024 * 1024):.2f} MB ({percent:.0f}%) "
                            f"@ {download_speed:.2f} MB/s {eta_text}")
                    _set_progress_ui(pack_name, text, percent=percent)
                else:
                    # No Content-Length header from the server -- we don't know the
                    # total size, so show an indeterminate bar instead of dividing by
                    # zero (which used to silently kill this download's thread).
                    text = (f"Downloading: {downloaded_size / (1024 * 1024):.2f} MB "
                            f"(size unknown) @ {download_speed:.2f} MB/s")
                    _set_progress_ui(pack_name, text, indeterminate=True)

        _set_progress_ui(pack_name, "Extracting...", percent=100)

        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)

        # Delete the ZIP file once the extraction is successful
        os.remove(filename)

        _set_progress_ui(pack_name, "Download completed!", percent=100)

    except Exception as e:
        # Previously an error here (bad URL, zero-byte response, corrupt zip, etc.)
        # would just die silently inside the thread pool and the progress bar would
        # sit there forever looking "frozen". Now it's surfaced to the user.
        error_text = f"Error: {e}"
        print(f"Error downloading {pack_name}: {e}")
        root.after(0, progress_label_var[pack_name].set, error_text)

# Function to start the download and extraction process
def start_download():
    destination_folder = filedialog.askdirectory(title="Select Destination Folder")
    if not destination_folder:
        return

    selected_packs = [pack_name for pack_name, pack_var in pack_vars.items() if pack_var.get()]
    if not selected_packs:
        return

    # Progress labels and bars already exist for every pack (created once at
    # startup, in their own dedicated grid cells) -- we just reset and reuse
    # them here instead of creating new widgets on top of old ones each run,
    # which is what used to cause things to drift out of alignment.
    create_progress_bars()

    for pack_name, pack_url in DDRPacks.items():
        if pack_name in selected_packs:
            download_executor.submit(download_and_extract, pack_name, pack_url, destination_folder)

# Function to select or deselect all packs
def toggle_select_all():
    select_all_state = select_all_var.get()
    for pack_name, pack_var in pack_vars.items():
        pack_var.set(select_all_state)

# Create a thread pool for concurrent downloads and extractions
download_executor = ThreadPoolExecutor(max_workers=20)

# Create and configure the GUI elements
# Add an image above the GUI title
script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, 'assets\\banner.png')  # Image banner
if os.path.exists(image_path):
    img = tk.PhotoImage(file=image_path)
    image_label = ttk.Label(root, image=img)
    image_label.grid(row=0, column=0, columnspan=4, pady=10)

# Title label
title_label = ttk.Label(root, text="DDR Pack Downloader (v0.4) \n Created by: void", font=("Helvetica", 16), justify='center')
title_label.grid(row=1, column=0, columnspan=4, pady=(0, 5), padx=10)  # Adjust pady and padx for spacing

download_button = ttk.Button(root, text="Select Directory to Start", command=start_download)
download_button.grid(row=2, column=0, columnspan=4, pady=10)

# Create a dictionary to store pack variables (checkboxes)
pack_vars = {}
row_numbers = {}  # Dictionary to store row numbers for each pack
recency_labels = {}
progress_label_var = {}
progress_bar_var = {}

# Function to compute the recency label (safe to run on a background thread --
# it does no Tkinter work itself, it only returns data)
def _compute_recency(pack_name):
    recency_str = scrape_recency_lxml(DDRInfo[pack_name])

    try:
        recency_duration = float(recency_str.split()[0])
        recency_unit = recency_str.split()[1].lower()

        if recency_unit == "months":
            recency_timedelta = datetime.timedelta(days=recency_duration * 30)
        elif recency_unit == "weeks":
            recency_timedelta = datetime.timedelta(weeks=recency_duration)
        elif recency_unit == "days":
            recency_timedelta = datetime.timedelta(days=recency_duration)
        else:
            recency_timedelta = datetime.timedelta()
    except (ValueError, IndexError):
        recency_timedelta = datetime.timedelta()

    recency_date = datetime.date.today() - recency_timedelta
    last_run_date = load_last_run_date()
    is_new = bool(last_run_date and recency_date >= last_run_date)
    return recency_str, is_new


def _apply_recency_ui(pack_name, recency_str, is_new):
    """Runs on the main thread via root.after. Updates the two pre-created,
    fixed-position labels for this row instead of creating new frames/labels
    each time -- the old code created a brand-new Frame+Labels on top of the
    grid cell every single call (every checkbox click, every startup scan),
    which is what caused rows to visually drift out of alignment over time."""
    recency_labels[pack_name].config(text=f"(Recency: {recency_str})", foreground="black")
    new_flag_labels[pack_name].config(text="New!" if is_new else "")


# Function to update the recency label with comparison (safe to call from any thread)
def update_recency_label(pack_name):
    def worker():
        recency_str, is_new = _compute_recency(pack_name)
        root.after(0, _apply_recency_ui, pack_name, recency_str, is_new)
    threading.Thread(target=worker, daemon=True).start()

# Create checkboxes, and dedicated status/progress widgets, for each pack.
# Everything is created ONCE here with a fixed grid position:
#   col 0-1: checkbox            col 2: recency text        col 3: "New!" flag
#   col 4-5: progress bar
#   col 6-7: progress/status label (downloading %, errors, "completed", etc.)
# Recency and progress no longer share a cell, so nothing overlaps, and
# nothing needs to be re-gridded (and potentially stacked) later.
new_flag_labels = {}
for i, (pack_name, pack_url) in enumerate(DDRPacks.items(), start=3):
    pack_var = tk.BooleanVar()
    pack_checkbox = ttk.Checkbutton(root, text=pack_name, variable=pack_var)
    pack_checkbox.grid(row=i, column=0, columnspan=2, sticky='w')
    pack_vars[pack_name] = pack_var
    row_numbers[pack_name] = i

    recency_label = ttk.Label(root, text="(Recency: ...)")
    recency_label.grid(row=i, column=2, sticky='w', padx=(10, 0))
    recency_labels[pack_name] = recency_label

    new_flag_label = ttk.Label(root, text="", foreground="red")
    new_flag_label.grid(row=i, column=3, sticky='w')
    new_flag_labels[pack_name] = new_flag_label

    progress_bar_var[pack_name] = ttk.Progressbar(root, length=200, mode="determinate")
    progress_bar_var[pack_name].grid(row=i, column=4, columnspan=2, sticky='w', padx=(10, 0))

    progress_label_var[pack_name] = tk.StringVar(value="")
    progress_label = ttk.Label(root, textvariable=progress_label_var[pack_name])
    progress_label.grid(row=i, column=6, columnspan=2, sticky='w', padx=(10, 0))

    # Kick off recency scraping in the background (thread-safe now: the worker
    # thread only computes data, root.after does the actual widget update)
    update_recency_label(pack_name)

    # Bind the update_recency_label function to the checkbox
    pack_checkbox.config(command=lambda pack_name=pack_name: update_recency_label(pack_name))

# Create a "Select All" checkbox
select_all_var = tk.BooleanVar()
select_all_checkbox = ttk.Checkbutton(root, text="Select All", variable=select_all_var, command=toggle_select_all)
select_all_checkbox.grid(row=2, column=0, columnspan=2, sticky='w')

# Create an entry widget for manual entry of the last run date
manual_date_var = StringVar()
manual_date_entry = Entry(root, textvariable=manual_date_var)
manual_date_entry.grid(row=2, column=5, columnspan=2, padx=(10, 0), sticky='w')
manual_date_button = ttk.Button(root, text="Set Last Run Date", command=set_last_run_date)
manual_date_button.grid(row=2, column=7, padx=(5, 10), sticky='w')

# Add a label to display the last run date
last_run_label = ttk.Label(root, text="")
last_run_label.grid(row=2, column=3, columnspan=2, sticky='w')

# Load the last run date when the program starts
last_run_date = load_last_run_date()
if last_run_date:
    last_run_label.config(text=f"Last Run: {last_run_date.strftime('%Y-%m-%d')}")

# Start the tkinter main loop
root.mainloop()