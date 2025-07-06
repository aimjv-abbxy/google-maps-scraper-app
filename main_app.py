# main_app.py (Updated with Animation Fix)

import customtkinter
import threading
import os
import math
from tkinter import filedialog
from PIL import Image, ImageTk
from scraper_engine import run_scraper, load_processed_addresses

# Set appearance and color theme for the application.
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("Google Maps Lead Scraper")
        self.geometry(f"1000x700")

        # --- Layout Configuration ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar Frame for Controls ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Scraper Controls", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Input Fields ---
        self.keyword_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Keyword (e.g., Med Spa)")
        self.keyword_entry.grid(row=1, column=0, padx=20, pady=10)
        self.location_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Location (City, State)")
        self.location_entry.grid(row=2, column=0, padx=20, pady=10)
        self.country_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Country")
        self.country_entry.grid(row=3, column=0, padx=20, pady=10)
        self.leads_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Number of Leads")
        self.leads_entry.grid(row=4, column=0, padx=20, pady=10)
        self.folder_path_label = customtkinter.CTkLabel(self.sidebar_frame, text="Output Folder Path:", anchor="w")
        self.folder_path_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.folder_path_frame = customtkinter.CTkFrame(self.sidebar_frame)
        self.folder_path_frame.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.folder_path_frame.grid_columnconfigure(0, weight=1)
        self.folder_path_entry = customtkinter.CTkEntry(self.folder_path_frame, placeholder_text="e.g., C:/Users/YourUser/Desktop")
        self.folder_path_entry.grid(row=0, column=0, sticky="ew")
        self.folder_path_entry.insert(0, os.path.join(os.getcwd(), "scraped_leads"))
        self.browse_button = customtkinter.CTkButton(self.folder_path_frame, text="...", width=30, command=self.browse_folder)
        self.browse_button.grid(row=0, column=1, padx=(5, 0))
        self.filename_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Output Filename (e.g., leads.csv)")
        self.filename_entry.grid(row=7, column=0, padx=20, pady=10)
        
        # --- Buttons & Options ---
        self.start_button = customtkinter.CTkButton(self.sidebar_frame, text="Start Scraping", command=self.start_scraping_thread)
        self.start_button.grid(row=8, column=0, padx=20, pady=10)
        self.stop_button = customtkinter.CTkButton(self.sidebar_frame, text="Stop Scraper", state="disabled", command=self.stop_scraping)
        self.stop_button.grid(row=9, column=0, padx=20, pady=10)
        self.headless_checkbox = customtkinter.CTkCheckBox(self.sidebar_frame, text="Run Headless (no browser)")
        self.headless_checkbox.grid(row=10, column=0, padx=20, pady=(10, 20), sticky="w")

        # --- Main Content Area (Animation + Log) ---
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- Animation Canvas ---
        self.animation_canvas = customtkinter.CTkCanvas(self.main_frame, bg="#2B2B2B", highlightthickness=0)
        self.animation_canvas.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        # --- Log Textbox ---
        self.log_textbox = customtkinter.CTkTextbox(self.main_frame, height=150)
        self.log_textbox.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")

        # --- Animation & Scraper Control Variables ---
        self.animation_state = "idle"
        self.angle = 0
        self.setup_animation()
        # --- FIX: Delay the first animation call to allow the window to render ---
        self.after(100, self.animate)
        
        self.scraper_thread = None
        self.stop_event = threading.Event()

    def setup_animation(self):
        """Loads images but does not resize them yet."""
        try:
            # Load the original PIL images
            self.earth_pil_image = Image.open("earth.png")
            self.robot_orbit_pil_image = Image.open("robot.png")
            self.robot_idle_pil_image = Image.open("robot_idle.png")
            self.robot_success_pil_image = Image.open("robot_success.png")
            
            # These will hold the PhotoImage objects after resizing
            self.earth_tk_image = None
            self.robot_orbit_tk_image = None
            self.robot_idle_tk_image = None
            self.robot_success_tk_image = None

            # Create the canvas items, they will be configured in the animate() loop
            self.earth_id = self.animation_canvas.create_image(0, 0, anchor="center", state='hidden')
            self.robot_orbit_id = self.animation_canvas.create_image(0, 0, anchor="center", state='hidden')
            self.robot_idle_id = self.animation_canvas.create_image(0, 0, anchor="center", state='hidden')
            self.robot_success_id = self.animation_canvas.create_image(0, 0, anchor="center", state='hidden')
            
            self.update_log("Animation assets loaded successfully.")
        except Exception as e:
            self.update_log(f"Error loading animation assets: {e}")

    def animate(self):
        """The main animation loop that resizes, positions, and updates based on state."""
        canvas_width = self.animation_canvas.winfo_width()
        canvas_height = self.animation_canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # --- FIX: Dynamic resizing based on canvas size ---
        # Ensure the canvas has a valid size before doing calculations
        if canvas_width < 50 or canvas_height < 50:
            self.after(100, self.animate) # If not ready, check again shortly
            return

        # Calculate dynamic sizes
        earth_size = int(canvas_height * 0.4)
        robot_orbit_size = int(canvas_height * 0.25)
        robot_idle_size = int(canvas_height * 0.3)
        robot_success_size = int(canvas_height * 0.5)

        # Create resized PhotoImage objects
        self.earth_tk_image = ImageTk.PhotoImage(self.earth_pil_image.resize((earth_size, earth_size), Image.Resampling.LANCZOS))
        self.robot_orbit_tk_image = ImageTk.PhotoImage(self.robot_orbit_pil_image.resize((robot_orbit_size, robot_orbit_size), Image.Resampling.LANCZOS))
        self.robot_idle_tk_image = ImageTk.PhotoImage(self.robot_idle_pil_image.resize((robot_idle_size, robot_idle_size), Image.Resampling.LANCZOS))
        self.robot_success_tk_image = ImageTk.PhotoImage(self.robot_success_pil_image.resize((robot_success_size, robot_success_size), Image.Resampling.LANCZOS))

        # Update the canvas items with the newly sized images
        self.animation_canvas.itemconfig(self.earth_id, image=self.earth_tk_image)
        self.animation_canvas.itemconfig(self.robot_orbit_id, image=self.robot_orbit_tk_image)
        self.animation_canvas.itemconfig(self.robot_idle_id, image=self.robot_idle_tk_image)
        self.animation_canvas.itemconfig(self.robot_success_id, image=self.robot_success_tk_image)

        # --- State Machine for Animation ---
        if self.animation_state == 'idle':
            self.animation_canvas.itemconfig(self.robot_orbit_id, state='hidden')
            self.animation_canvas.itemconfig(self.robot_success_id, state='hidden')
            self.animation_canvas.itemconfig(self.earth_id, state='normal')
            self.animation_canvas.itemconfig(self.robot_idle_id, state='normal')
            self.animation_canvas.coords(self.earth_id, center_x - (earth_size * 0.6), center_y)
            self.animation_canvas.coords(self.robot_idle_id, center_x + (earth_size * 0.7), center_y)

        elif self.animation_state == 'running':
            self.animation_canvas.itemconfig(self.robot_idle_id, state='hidden')
            self.animation_canvas.itemconfig(self.robot_success_id, state='hidden')
            self.animation_canvas.itemconfig(self.earth_id, state='normal')
            self.animation_canvas.itemconfig(self.robot_orbit_id, state='normal')
            
            self.animation_canvas.coords(self.earth_id, center_x, center_y)
            radius_x = (canvas_width / 2) - (robot_orbit_size)
            radius_y = (canvas_height / 2) - (robot_orbit_size)
            robot_x = center_x + radius_x * math.cos(self.angle)
            robot_y = center_y + radius_y * math.sin(self.angle)
            self.animation_canvas.coords(self.robot_orbit_id, robot_x, robot_y)
            self.angle += 0.02
            self.after(33, self.animate) # Continue the loop

        elif self.animation_state == 'finished':
            self.animation_canvas.itemconfig(self.robot_orbit_id, state='hidden')
            self.animation_canvas.itemconfig(self.robot_idle_id, state='hidden')
            self.animation_canvas.itemconfig(self.earth_id, state='hidden')
            self.animation_canvas.itemconfig(self.robot_success_id, state='normal')
            self.animation_canvas.coords(self.robot_success_id, center_x, center_y)
            
    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path_entry.delete(0, "end")
            self.folder_path_entry.insert(0, folder_path)

    def update_log(self, text):
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")
        self.update_idletasks()

    def start_scraping_thread(self):
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.stop_event.clear()
        
        self.animation_state = 'running'
        self.animate()
        
        self.scraper_thread = threading.Thread(target=self.run_scraper_logic)
        self.scraper_thread.daemon = True
        self.scraper_thread.start()

    def stop_scraping(self):
        if self.scraper_thread and self.scraper_thread.is_alive():
            self.update_log("--- STOP SIGNAL SENT ---")
            self.stop_event.set()
            self.stop_button.configure(state="disabled")

    def run_scraper_logic(self):
        try:
            output_dir = self.folder_path_entry.get()
            filename = self.filename_entry.get()
            if not output_dir or not filename:
                self.update_log("ERROR: Output folder path and filename cannot be empty.")
                self.animation_state = 'idle'
                self.animate()
                return
            if not filename.lower().endswith('.csv'):
                filename += '.csv'
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
            self.animation_state = 'finished'
            self.animate()
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()