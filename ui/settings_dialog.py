"""
Settings Dialog - User configuration interface.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from typing import Optional, Callable


class SettingsDialog(ctk.CTkToplevel):
    """
    Settings dialog for configuring application options.
    """
    
    def __init__(self, master, config, on_save: Optional[Callable] = None):
        super().__init__(master)
        
        self.config = config
        self.on_save = on_save
        
        # Window setup
        self.title("⚙️ Nastavení")
        self.geometry("550x400")
        self.resizable(False, False)
        
        # Make modal
        self.transient(master)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - 550) // 2
        y = master.winfo_y() + (master.winfo_height() - 400) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_ui()
        
        # Focus
        self.focus_set()
    
    def _create_ui(self):
        """Create the settings UI."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame,
            text="⚙️ Nastavení aplikace",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 20))
        
        # ===== Tesseract Section =====
        tesseract_frame = ctk.CTkFrame(main_frame)
        tesseract_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            tesseract_frame,
            text="🔧 Tesseract OCR",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Path input row
        path_row = ctk.CTkFrame(tesseract_frame, fg_color="transparent")
        path_row.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            path_row,
            text="Cesta k tesseract.exe:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        path_input_row = ctk.CTkFrame(path_row, fg_color="transparent")
        path_input_row.pack(fill="x", pady=(5, 0))
        
        self.tesseract_path_var = ctk.StringVar(value=self.config.get_tesseract_path())
        self.tesseract_entry = ctk.CTkEntry(
            path_input_row,
            textvariable=self.tesseract_path_var,
            width=380
        )
        self.tesseract_entry.pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            path_input_row,
            text="📂",
            width=40,
            command=self._browse_tesseract
        ).pack(side="left")
        
        # Test button
        ctk.CTkButton(
            tesseract_frame,
            text="🔍 Otestovat připojení",
            command=self._test_tesseract
        ).pack(anchor="w", padx=10, pady=(0, 10))
        
        # ===== Language Section =====
        lang_frame = ctk.CTkFrame(main_frame)
        lang_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            lang_frame,
            text="🌐 Jazyk OCR",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        lang_row = ctk.CTkFrame(lang_frame, fg_color="transparent")
        lang_row.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            lang_row,
            text="Jazykový kód (např. ces, eng, ces+eng):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w")
        
        self.language_var = ctk.StringVar(value=self.config.get_ocr_language())
        self.language_entry = ctk.CTkEntry(
            lang_row,
            textvariable=self.language_var,
            width=200
        )
        self.language_entry.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkLabel(
            lang_row,
            text="💡 Více jazyků oddělte znakem + (např. ces+eng)",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50")
        ).pack(anchor="w", pady=(5, 0))
        
        # ===== Buttons =====
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(
            button_frame,
            text="💾 Uložit",
            command=self._save_settings,
            width=120
        ).pack(side="right", padx=(5, 0))
        
        ctk.CTkButton(
            button_frame,
            text="Zrušit",
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self.destroy,
            width=100
        ).pack(side="right")
    
    def _browse_tesseract(self):
        """Open file browser for Tesseract executable."""
        current_path = self.tesseract_path_var.get()
        initial_dir = os.path.dirname(current_path) if os.path.exists(os.path.dirname(current_path)) else "C:\\"
        
        filepath = filedialog.askopenfilename(
            title="Vyberte tesseract.exe",
            initialdir=initial_dir,
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        
        if filepath:
            self.tesseract_path_var.set(filepath)
    
    def _test_tesseract(self):
        """Test if Tesseract is accessible."""
        path = self.tesseract_path_var.get()
        
        if not os.path.exists(path):
            messagebox.showerror(
                "Chyba",
                f"Soubor neexistuje:\n{path}"
            )
            return
        
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = path
            version = pytesseract.get_tesseract_version()
            
            # Also try to get available languages
            try:
                languages = pytesseract.get_languages()
                lang_list = ', '.join(languages[:10])
                if len(languages) > 10:
                    lang_list += f"... (+{len(languages)-10} dalších)"
            except:
                lang_list = "Nelze zjistit"
            
            messagebox.showinfo(
                "Úspěch ✅",
                f"Tesseract je funkční!\n\n"
                f"Verze: {version}\n"
                f"Dostupné jazyky: {lang_list}"
            )
        except Exception as e:
            messagebox.showerror(
                "Chyba",
                f"Tesseract není funkční:\n{e}"
            )
    
    def _save_settings(self):
        """Save settings and close."""
        # Validate tesseract path
        tesseract_path = self.tesseract_path_var.get().strip()
        if not os.path.exists(tesseract_path):
            result = messagebox.askyesno(
                "Upozornění",
                f"Cesta k Tesseract neexistuje:\n{tesseract_path}\n\n"
                "Chcete přesto uložit nastavení?"
            )
            if not result:
                return
        
        # Save settings
        self.config.set_tesseract_path(tesseract_path)
        self.config.set_ocr_language(self.language_var.get().strip())
        
        messagebox.showinfo("Uloženo", "Nastavení bylo uloženo.")
        
        # Callback
        if self.on_save:
            self.on_save()
        
        self.destroy()
