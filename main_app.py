# main_app.py (Updated Version)

import customtkinter
import threading
import os
from tkinter import filedialog # <-- New import for the folder browser dialog
from scraper_engine import run_scraper, load_processed_addresses

# Set appearance and color theme for the application.
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("Google Maps Lead Scraper")
        self.geometry(f"800x650") # Increased height for new widgets

        # --- Layout Configuration ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar Frame for Controls ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1) # Adjust row weight for spacing

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Scraper Controls", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Input Fields for Scraper Settings ---
        self.keyword_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Keyword (e.g., Med Spa)")
        self.keyword_entry.grid(row=1, column=0, padx=20, pady=10)
        
        self.location_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Location (City, State)")
        self.location_entry.grid(row=2, column=0, padx=20, pady=10)
        
        self.country_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Country")
        self.country_entry.grid(row=3, column=0, padx=20, pady=10)
        
        self.leads_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Number of Leads")
        self.leads_entry.grid(row=4, column=0, padx=20, pady=10)
        
        # --- NEW: Folder Path Selection ---
        self.folder_path_label = customtkinter.CTkLabel(self.sidebar_frame, text="Output Folder Path:", anchor="w")
        self.folder_path_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        
        self.folder_path_frame = customtkinter.CTkFrame(self.sidebar_frame)
        self.folder_path_frame.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.folder_path_frame.grid_columnconfigure(0, weight=1)

        self.folder_path_entry = customtkinter.CTkEntry(self.folder_path_frame, placeholder_text="e.g., C:/Users/YourUser/Desktop")
        self.folder_path_entry.grid(row=0, column=0, sticky="ew")
        # Set a default path
        self.folder_path_entry.insert(0, os.path.join(os.getcwd(), "scraped_leads"))

        self.browse_button = customtkinter.CTkButton(self.folder_path_frame, text="Browse...", width=70, command=self.browse_folder)
        self.browse_button.grid(row=0, column=1, padx=(5, 0))
        
        self.filename_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Output Filename (e.g., leads.csv)")
        self.filename_entry.grid(row=7, column=0, padx=20, pady=10)
        
        # --- Buttons ---
        self.start_button = customtkinter.CTkButton(self.sidebar_frame, text="Start Scraping", command=self.start_scraping_thread)
        self.start_button.grid(row=8, column=0, padx=20, pady=10)
        
        self.stop_button = customtkinter.CTkButton(self.sidebar_frame, text="Stop Scraper", state="disabled", command=self.stop_scraping)
        self.stop_button.grid(row=9, column=0, padx=20, pady=10)
        
        # --- Options ---
        self.headless_checkbox = customtkinter.CTkCheckBox(self.sidebar_frame, text="Run Headless (no browser)")
        self.headless_checkbox.grid(row=10, column=0, padx=20, pady=(10, 20), sticky="w")

        # --- Main Textbox for Scraper Output/Log ---
        self.log_textbox = customtkinter.CTkTextbox(self, width=250)
        self.log_textbox.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # --- Scraper Control Variables ---
        self.scraper_thread = None
        self.stop_event = threading.Event()

    # --- NEW: Function to handle the "Browse..." button click ---
    def browse_folder(self):
        """ Opens a folder selection dialog and updates the entry field. """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path_entry.delete(0, "end")
            self.folder_path_entry.insert(0, folder_path)

    def update_log(self, text):
        """ Appends a new line of text to the log textbox from any thread """
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")
        self.update_idletasks()

    def start_scraping_thread(self):
        """ Starts the scraper in a separate thread to prevent GUI freezing """
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.stop_event.clear()
        
        self.scraper_thread = threading.Thread(target=self.run_scraper_logic)
        self.scraper_thread.daemon = True
        self.scraper_thread.start()

    def stop_scraping(self):
        """ Signals the scraper thread to stop """
        if self.scraper_thread and self.scraper_thread.is_alive():
            self.update_log("--- STOP SIGNAL SENT ---")
            self.stop_event.set()
            self.stop_button.configure(state="disabled")

    def run_scraper_logic(self):
        """ 
        This function runs in the background thread. 
        It gathers all the settings from the UI and calls the scraper engine.
        """
        try:
            # --- UPDATED: Use the custom folder path from the new input field ---
            output_dir = self.folder_path_entry.get()
            filename = self.filename_entry.get()
            
            # Basic validation
            if not output_dir or not filename:
                self.update_log("ERROR: Output folder path and filename cannot be empty.")
                return

            if not filename.lower().endswith('.csv'):
                filename += '.csv'
                
            # Create the output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, filename)

            params = {
                'keyword': self.keyword_entry.get(),
                'location': self.location_entry.get(),
                'country': self.country_entry.get(),
                'target_leads': int(self.leads_entry.get()),
                'headless': self.headless_checkbox.get(),
                'filepath': filepath,
                'processed_addresses': set()
            }
            
            if os.path.exists(params['filepath']):
                self.update_log(f"File exists. Will append new unique leads to: {params['filepath']}")
                params['processed_addresses'] = load_processed_addresses(params['filepath'])
                self.update_log(f"Loaded {len(params['processed_addresses'])} previously scraped addresses.")

            run_scraper(params, self.update_log, self.stop_event)
            
        except ValueError:
            self.update_log("ERROR: 'Number of Leads' must be a valid number.")
        except Exception as e:
            self.update_log(f"An unexpected error occurred: {e}")
        finally:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()