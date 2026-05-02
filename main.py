import customtkinter as ctk
import os
import subprocess
import glob

class CPUManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("KimCore - Master Kim")
        self.geometry("400x350")
        self.attributes("-alpha", 0.9)  # Set transparency to 90%
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.cpu_path = "/sys/devices/system/cpu"
        self.cores = self.get_all_cores()
        self.total_cores = len(self.cores)

        # UI Components
        self.label_title = ctk.CTkLabel(self, text="KimCore", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text=self.get_status_text())
        self.status_label.pack(pady=10)

        self.slider_label = ctk.CTkLabel(self, text=f"Active Cores: {self.get_online_count()}")
        self.slider_label.pack(pady=5)

        self.slider = ctk.CTkSlider(self, from_=1, to=self.total_cores, number_of_steps=self.total_cores-1, command=self.update_slider_label)
        self.slider.set(self.get_online_count())
        self.slider.pack(pady=10, padx=20, fill="x")

        self.apply_button = ctk.CTkButton(self, text="Apply Changes", command=self.apply_changes)
        self.apply_button.pack(pady=20)

        self.refresh_button = ctk.CTkButton(self, text="Refresh", fg_color="transparent", border_width=1, command=self.refresh_status)
        self.refresh_button.pack(pady=5)

    def get_all_cores(self):
        core_dirs = glob.glob(os.path.join(self.cpu_path, "cpu[0-9]*"))
        # Sort them numerically
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
                # cpu0 doesn't have an online file, it's always online
                online_count += 1
        return online_count

    def get_status_text(self):
        count = self.get_online_count()
        return f"Current System State: {count} / {self.total_cores} Cores Online"

    def update_slider_label(self, value):
        self.slider_label.configure(text=f"Active Cores: {int(value)}")

    def refresh_status(self):
        self.status_label.configure(text=self.get_status_text())
        self.slider.set(self.get_online_count())
        self.slider_label.configure(text=f"Active Cores: {self.get_online_count()}")

    def apply_changes(self):
        target_count = int(self.slider.get())
        
        # We always keep cpu0 online. 
        # For cpu1 to cpu(target_count-1), set online=1
        # For cpu(target_count) to cpu(total_cores-1), set online=0
        
        for i in range(1, self.total_cores):
            core = f"cpu{i}"
            online_file = os.path.join(self.cpu_path, core, "online")
            
            if not os.path.exists(online_file):
                continue

            new_state = "1" if i < target_count else "0"
            
            # Execute with sudo
            cmd = f"sudo sh -c 'echo {new_state} > {online_file}'"
            subprocess.run(cmd, shell=True)
            
        self.refresh_status()

if __name__ == "__main__":
    app = CPUManagerApp()
    app.mainloop()
