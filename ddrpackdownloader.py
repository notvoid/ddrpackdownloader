# DDR Pack Downloader v0.2
# Created by: void (and chatGPT!)

import os
import tkinter as tk
from tkinter import ttk
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
    'Dance Dance Revolution A3': 'https://zenius-i-vanisher.com/v5.2/download.php?type=ddrpack&categoryid=1509'
 }

# Dictionary of DDR Pages
DDRInfo = {
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
    'Dance Dance Revolution A3': 'https://zenius-i-vanisher.com/v5.2/viewsimfilecategory.php?categoryid=1509'
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
icon_path = os.path.join(script_dir, 'icon.ico')  # Icon
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# Function to save the last run date to a file
def save_last_run_date(last_run_date):
    try:
        # Specify a relative path to the file
        file_path = os.path.join(os.path.dirname(__file__), 'last_run_date.txt')
        with open(file_path, 'w') as file:
            file.write(last_run_date.strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"Error saving last run date: {e}")

# Function to load the last run date from a file
def load_last_run_date():
    try:
        # Specify a relative path to the file
        file_path = os.path.join(os.path.dirname(__file__), 'last_run_date.txt')
        with open(file_path, 'r') as file:
            date_str = file.read()
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading last run date: {e}")
        return None


# Function to create and update progress bars
def create_progress_bars():
    selected_packs = [pack_name for pack_name, pack_var in pack_vars.items() if pack_var.get()]
    
    for pack_name in selected_packs:
        progress_label_var[pack_name].set(f"Downloading...")
        progress_bar_var[pack_name]['value'] = 0
    
    # Update the last run date when creating progress bars
    last_run_date = datetime.date.today()
    save_last_run_date(last_run_date)
    last_run_label.config(text=f"Last Run Date: {last_run_date.strftime('%Y-%m-%d')}")

# Function to download and extract a pack
def download_and_extract(pack_name, pack_url, destination_folder):
    filename = os.path.join(destination_folder, f'{pack_name}.zip')
    extract_folder = os.path.join(destination_folder, pack_name)

    response = requests.get(pack_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    downloaded_size = 0
    start_time = time.time()

    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)
            downloaded_size += len(data)
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                download_speed = downloaded_size / (1024 * 1024 * elapsed_time)
                remaining_size = total_size - downloaded_size
                eta_seconds = remaining_size / (download_speed * 1024 * 1024)
                eta_minutes = int(eta_seconds // 60)
                eta_seconds = int(eta_seconds % 60)
                # Update the label text using the main thread
                root.after(10, progress_label_var[pack_name].set, f"Downloading: {downloaded_size / (1024 * 1024):.2f} MB / {total_size / (1024 * 1024):.2f} MB ({int(100 * downloaded_size / total_size)}%) @ {download_speed:.2f} Mbps (ETA: {eta_minutes:02d} min {eta_seconds:02d} sec)")

    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)

    # Delete the ZIP file once the extraction is successful
    os.remove(filename)

    # Update the progress label to indicate completion
    progress_label_var[pack_name].set(f"Download completed!")

# Function to start the download and extraction process
def start_download():
    destination_folder = filedialog.askdirectory(title="Select Destination Folder")
    if not destination_folder:
        return

    # Initialize progress labels and progress bars for selected packs
    selected_packs = [pack_name for pack_name, pack_var in pack_vars.items() if pack_var.get()]
    if not selected_packs:
        return

    for pack_name in selected_packs:
        progress_label_var[pack_name] = tk.StringVar()
        progress_label = ttk.Label(root, textvariable=progress_label_var[pack_name])
        progress_label.grid(row=row_numbers[pack_name], column=2, columnspan=2, sticky='w')

        progress_bar_var[pack_name] = ttk.Progressbar(root, length=300, mode="determinate")
        progress_bar_var[pack_name].grid(row=row_numbers[pack_name], column=4, columnspan=2, sticky='w')
        progress_bar_var[pack_name].update()  # Initialize the progress bar

        progress_label_var[pack_name].set(f"Downloading...")

    create_progress_bars()  # Create progress bars before downloading

    for pack_name, pack_url in DDRPacks.items():
        if pack_name in selected_packs:
            download_executor.submit(download_and_extract, pack_name, pack_url, destination_folder)

# Function to select or deselect all packs
def toggle_select_all():
    select_all_state = select_all_var.get()
    for pack_name, pack_var in pack_vars.items():
        pack_var.set(select_all_state)

# Create a thread pool for concurrent downloads and extractions
download_executor = ThreadPoolExecutor(max_workers=5)

# Create and configure the GUI elements
# Add an image above the GUI title
script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, 'banner.png')  # Image banner
if os.path.exists(image_path):
    img = tk.PhotoImage(file=image_path)
    image_label = ttk.Label(root, image=img)
    image_label.grid(row=0, column=0, columnspan=4, pady=10)

# Title label
title_label = ttk.Label(root, text="DDR Pack Downloader (v0.2) \n Created by: void (and chatGPT!)", font=("Helvetica", 16), justify='center')
title_label.grid(row=1, column=0, columnspan=4, pady=(0, 5), padx=10)  # Adjust pady and padx for spacing

download_button = ttk.Button(root, text="Select Directory to Start", command=start_download)
download_button.grid(row=2, column=0, columnspan=4, pady=10)

# Create a dictionary to store pack variables (checkboxes)
pack_vars = {}
row_numbers = {}  # Dictionary to store row numbers for each pack
recency_labels = {}

# Function to update the recency label with comparison
def update_recency_label(pack_name):
    recency_str = scrape_recency_lxml(DDRInfo[pack_name])
    
    # Calculate the recency date relative to the current date
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
            recency_timedelta = datetime.timedelta()  # Default to zero timedelta
    except ValueError:
        recency_timedelta = datetime.timedelta()  # Default to zero timedelta
    
    recency_date = datetime.date.today() - recency_timedelta
    
    last_run_date = load_last_run_date()
    if last_run_date and recency_date >= last_run_date:
        # Create a frame to contain two labels
        recency_frame = ttk.Frame(root)
        recency_frame.grid(row=row_numbers[pack_name], column=2, columnspan=2, sticky='w')
        
        # Label for the recency string in black
        recency_label = ttk.Label(recency_frame, text=f"(Recency: {recency_str})", foreground="black")
        recency_label.grid(row=0, column=0, sticky='w')
        
        # Label for "Newer!" in red
        newer_label = ttk.Label(recency_frame, text="New!", foreground="red")
        newer_label.grid(row=0, column=1, sticky='w')
    else:
        recency_labels[pack_name].config(text=f"(Recency: {recency_str})", foreground="black")

# Create checkboxes for packs and update recency labels
for i, (pack_name, pack_url) in enumerate(DDRPacks.items(), start=3):
    pack_var = tk.BooleanVar()
    pack_checkbox = ttk.Checkbutton(root, text=pack_name, variable=pack_var)
    pack_checkbox.grid(row=i, column=0, columnspan=2, sticky='w')
    pack_vars[pack_name] = pack_var
    row_numbers[pack_name] = i

    recency_label = ttk.Label(root, text="(Recency: ...)")
    recency_label.grid(row=i, column=2, columnspan=2, sticky='w')
    recency_labels[pack_name] = recency_label

    # Start a separate thread to scrape recency
    threading.Thread(target=update_recency_label, args=(pack_name,)).start()

    # Bind the update_recency_label function to the checkbox
    pack_checkbox.config(command=lambda pack_name=pack_name: update_recency_label(pack_name))

# Create a "Select All" checkbox
select_all_var = tk.BooleanVar()
select_all_checkbox = ttk.Checkbutton(root, text="Select All", variable=select_all_var, command=toggle_select_all)
select_all_checkbox.grid(row=2, column=0, columnspan=2, sticky='w')

# Initialize dictionaries to store progress labels and progress bars for each pack
progress_label_var = {}
progress_bar_var = {}

# Add a label to display the last run date
last_run_label = ttk.Label(root, text="")
last_run_label.grid(row=2, column=3, columnspan=2, sticky='w')

# Load the last run date when the program starts
last_run_date = load_last_run_date()
if last_run_date:
    last_run_label.config(text=f"Last Run: {last_run_date.strftime('%Y-%m-%d')}")

# Start the tkinter main loop
root.mainloop()
