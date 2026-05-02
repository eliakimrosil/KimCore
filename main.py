import customtkinter as ctk
import os
import subprocess
import glob

class CPUManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("kimcore - Master Kim")
        self.geometry("400x580")
        
        # Set transparency (Alpha works better on XWayland/X11)
        self.attributes("-alpha", 0.9) 
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.cpu_path = "/sys/devices/system/cpu"
        self.cores = self.get_all_cores()
        self.total_cores = len(self.cores)
        
        # CPU Freq limits
        self.min_freq = self.read_freq_limit("cpuinfo_min_freq")
        self.max_freq = self.read_freq_limit("cpuinfo_max_freq")

        # UI Components
        self.label_title = ctk.CTkLabel(self, text="kimcore", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=(20, 10))

        # --- SECTION: CORES ---
        self.section_core = ctk.CTkLabel(self, text="Core Management", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3b8ed0")
        self.section_core.pack(pady=(10, 5))

        self.status_label = ctk.CTkLabel(self, text=self.get_status_text())
        self.status_label.pack(pady=5)

        self.slider_label = ctk.CTkLabel(self, text=f"Active Cores: {self.get_online_count()}")
        self.slider_label.pack(pady=0)

        self.slider = ctk.CTkSlider(self, from_=1, to=self.total_cores, number_of_steps=self.total_cores-1, command=self.update_slider_label)
        self.slider.set(self.get_online_count())
        self.slider.pack(pady=10, padx=30, fill="x")

        # --- SECTION: SCALING ---
        self.section_scaling = ctk.CTkLabel(self, text="Performance & Scaling", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3b8ed0")
        self.section_scaling.pack(pady=(20, 5))

        self.label_profile = ctk.CTkLabel(self, text="Performance Profile:")
        self.label_profile.pack(pady=0)
        
        self.profile_menu = ctk.CTkOptionMenu(self, values=["Performance", "Balanced", "Power Save"])
        self.profile_menu.set("Balanced")
        self.profile_menu.pack(pady=10)

        self.freq_label = ctk.CTkLabel(self, text="Max Frequency Limit: 100%")
        self.freq_label.pack(pady=0)

        self.freq_slider = ctk.CTkSlider(self, from_=0, to=100, number_of_steps=100, command=self.update_freq_label)
        self.freq_slider.set(100)
        self.freq_slider.pack(pady=10, padx=30, fill="x")

        self.freq_info = ctk.CTkLabel(self, text=f"Target: {self.max_freq // 1000} MHz", font=ctk.CTkFont(size=11))
        self.freq_info.pack(pady=0)

        # --- ACTIONS ---
        self.apply_button = ctk.CTkButton(self, text="Apply All Changes", font=ctk.CTkFont(weight="bold"), command=self.apply_changes)
        self.apply_button.pack(pady=(30, 10))

        self.refresh_button = ctk.CTkButton(self, text="Refresh Status", fg_color="transparent", border_width=1, command=self.refresh_status)
        self.refresh_button.pack(pady=5)

    def read_freq_limit(self, filename):
        try:
            with open(os.path.join(self.cpu_path, "cpu0", "cpufreq", filename), "r") as f:
                return int(f.read().strip())
        except:
            return 1000000 # Fallback

    def get_all_cores(self):
        core_dirs = glob.glob(os.path.join(self.cpu_path, "cpu[0-9]*"))
        core_dirs.sort(key=lambda x: int(os.path.basename(x)[3:]))
        return [os.path.basename(d) for d in core_dirs]

    def get_online_count(self):
        online_count = 0
        for core in self.cores:
            if core == "cpu0":
                online_count += 1
                continue
            try:
                with open(os.path.join(self.cpu_path, core, "online"), "r") as f:
                    if f.read().strip() == "1":
                        online_count += 1
            except FileNotFoundError:
                online_count += 1
        return online_count

    def get_status_text(self):
        count = self.get_online_count()
        return f"System State: {count} / {self.total_cores} Cores Online"

    def update_slider_label(self, value):
        self.slider_label.configure(text=f"Active Cores: {int(value)}")

    def update_freq_label(self, value):
        percent = int(value)
        self.freq_label.configure(text=f"Max Frequency Limit: {percent}%")
        target = self.min_freq + (self.max_freq - self.min_freq) * (percent / 100)
        self.freq_info.configure(text=f"Target: {int(target // 1000)} MHz")

    def refresh_status(self):
        self.status_label.configure(text=self.get_status_text())
        self.slider.set(self.get_online_count())
        self.slider_label.configure(text=f"Active Cores: {self.get_online_count()}")

    def apply_changes(self):
        # 1. Apply Cores
        target_cores = int(self.slider.get())
        for i in range(1, self.total_cores):
            core = f"cpu{i}"
            online_file = os.path.join(self.cpu_path, core, "online")
            if os.path.exists(online_file):
                new_state = "1" if i < target_cores else "0"
                subprocess.run(f"sudo sh -c 'echo {new_state} > {online_file}'", shell=True)
        
        # 2. Apply Scaling
        percent = int(self.freq_slider.get())
        target_freq = int(self.min_freq + (self.max_freq - self.min_freq) * (percent / 100))
        
        profile = self.profile_menu.get()
        governor = "performance" if profile == "Performance" else "powersave"
        
        energy_pref = "balance_performance"
        if profile == "Performance": energy_pref = "performance"
        elif profile == "Power Save": energy_pref = "power"

        # Apply to all cores that are currently online
        for i in range(self.total_cores):
            core = f"cpu{i}"
            freq_dir = os.path.join(self.cpu_path, core, "cpufreq")
            
            if os.path.exists(freq_dir):
                # Set Governor
                subprocess.run(f"sudo sh -c 'echo {governor} > {freq_dir}/scaling_governor'", shell=True)
                # Set Max Freq
                subprocess.run(f"sudo sh -c 'echo {target_freq} > {freq_dir}/scaling_max_freq'", shell=True)
                # Set Energy Preference (if supported)
                epp_file = f"{freq_dir}/energy_performance_preference"
                if os.path.exists(epp_file):
                    subprocess.run(f"sudo sh -c 'echo {energy_pref} > {epp_file}'", shell=True)
            
        self.refresh_status()

if __name__ == "__main__":
    app = CPUManagerApp()
    app.mainloop()
