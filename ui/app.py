"""
Main Application Window - OCR Desktop App.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import TkinterDnD for drag and drop
try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from .components import FileDropZone
from .mode_a_view import ModeAView
from .mode_b_view import ModeBView
from .settings_dialog import SettingsDialog
from src.config import get_config


# Create base class that supports DnD if available
if DND_AVAILABLE:
    class AppBase(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    AppBase = ctk.CTk


class OCRApp(AppBase):
    """
    Main OCR Application Window.
    """
    
    APP_NAME = "OCR Dokument"
    APP_VERSION = "1.0.0"
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = get_config()
        
        # Configure window
        self.title(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.geometry("1400x800")
        self.minsize(1000, 600)
        
        # Set appearance from config
        saved_theme = self.config.get_theme()
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("blue")
        
        # Initialize OCR engine with config
        self.ocr_engine = None
        self._init_ocr_engine()
        
        # Current loaded files (supports multiple)
        self.current_files: List[str] = []
        
        # Create main layout
        self._create_layout()
        
        # Bind window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _init_ocr_engine(self):
        """Initialize the OCR engine."""
        try:
            from src.ocr_engine import OCREngine
            tesseract_path = self.config.get_tesseract_path()
            ocr_language = self.config.get_ocr_language()
            self.ocr_engine = OCREngine(tesseract_path=tesseract_path, language=ocr_language)
        except Exception as e:
            messagebox.showerror(
                "Chyba inicializace",
                f"Nepodařilo se inicializovat OCR engine:\n{e}\n\n"
                "Zkontrolujte cestu k Tesseract v Nastavení."
            )
            self.ocr_engine = None
    
    def _create_layout(self):
        """Create the main application layout."""
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        self._create_header()
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Tab view for modes
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=0, column=0, sticky="nsew")
        
        # Create tabs
        self.tab_upload = self.tab_view.add("📁 Nahrát soubor")
        self.tab_mode_a = self.tab_view.add("📝 Režim A: Digitalizace")
        self.tab_mode_b = self.tab_view.add("📊 Režim B: Chytrá extrakce")
        
        # Configure tabs
        for tab in [self.tab_upload, self.tab_mode_a, self.tab_mode_b]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)
        
        # Upload tab content
        self._create_upload_tab()
        
        # Mode A tab content
        if self.ocr_engine:
            self.mode_a_view = ModeAView(self.tab_mode_a, self.ocr_engine)
            self.mode_a_view.grid(row=0, column=0, sticky="nsew")
        else:
            self._create_error_placeholder(self.tab_mode_a)
        
        # Mode B tab content
        if self.ocr_engine:
            self.mode_b_view = ModeBView(self.tab_mode_b, self.ocr_engine)
            self.mode_b_view.grid(row=0, column=0, sticky="nsew")
        else:
            self._create_error_placeholder(self.tab_mode_b)
        
        # Footer / Status bar
        self._create_footer()
    
    def _create_header(self):
        """Create the header with controls."""
        header = ctk.CTkFrame(self, height=50, fg_color=("gray90", "gray20"))
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        # App title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            title_frame,
            text="📄 OCR Dokument",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text=f"v{self.APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray50")
        ).pack(side="left", padx=(10, 0))
        
        # Right side controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right", padx=10)
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            controls,
            text="⚙️",
            width=40,
            command=self._open_settings
        )
        self.settings_btn.pack(side="left", padx=5)
        
        # Theme toggle
        saved_theme = self.config.get_theme()
        self.theme_var = ctk.StringVar(value=saved_theme)
        self.theme_switch = ctk.CTkSwitch(
            controls,
            text="🌙 Tmavý režim" if saved_theme == "dark" else "☀️ Světlý režim",
            variable=self.theme_var,
            onvalue="dark",
            offvalue="light",
            command=self._toggle_theme
        )
        self.theme_switch.pack(side="left", padx=10)
        if saved_theme == "dark":
            self.theme_switch.select()
        
        # Open file button
        self.open_btn = ctk.CTkButton(
            controls,
            text="📂 Otevřít soubor",
            command=self._open_file
        )
        self.open_btn.pack(side="left", padx=5)
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            controls,
            text="🗑️ Vymazat",
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self._clear_all
        )
        self.clear_btn.pack(side="left", padx=5)
    
    def _create_upload_tab(self):
        """Create the file upload tab."""
        # Center container
        center_frame = ctk.CTkFrame(self.tab_upload, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Welcome text
        ctk.CTkLabel(
            center_frame,
            text="Vítejte v OCR Dokument",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            center_frame,
            text="Nahrajte naskenovaný dokument a převeďte ho na digitální text",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        ).pack(pady=(0, 30))
        
        # File drop zone
        from src.pdf_handler import get_supported_formats
        self.drop_zone = FileDropZone(
            center_frame,
            on_file_drop=self._on_files_loaded,
            supported_formats=get_supported_formats(),
            multiple=True
        )
        self.drop_zone.pack(ipadx=100, ipady=50)
        
        # Modes description
        modes_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        modes_frame.pack(pady=30)
        
        # Mode A description
        mode_a_frame = ctk.CTkFrame(modes_frame, fg_color=("gray95", "gray20"))
        mode_a_frame.pack(side="left", padx=10, ipadx=20, ipady=15)
        
        ctk.CTkLabel(
            mode_a_frame,
            text="📝 Režim A: Digitalizace",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack()
        ctk.CTkLabel(
            mode_a_frame,
            text="Přečte veškerý text z dokumentu.\nVýstup: TXT, Word, PDF",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        ).pack(pady=5)
        
        # Mode B description
        mode_b_frame = ctk.CTkFrame(modes_frame, fg_color=("gray95", "gray20"))
        mode_b_frame.pack(side="left", padx=10, ipadx=20, ipady=15)
        
        ctk.CTkLabel(
            mode_b_frame,
            text="📊 Režim B: Chytrá extrakce",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack()
        ctk.CTkLabel(
            mode_b_frame,
            text="Najde konkrétní hodnoty podle vzorů.\nVýstup: Excel, PDF",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            justify="center"
        ).pack(pady=5)
    
    def _create_error_placeholder(self, parent):
        """Create error placeholder when OCR is not available."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(
            frame,
            text="⚠️ OCR Engine není dostupný",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("red", "orange")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            frame,
            text="Nainstalujte Tesseract-OCR a restartujte aplikaci.",
            font=ctk.CTkFont(size=14)
        ).pack()
    
    def _create_footer(self):
        """Create the status bar footer."""
        footer = ctk.CTkFrame(self, height=30, fg_color=("gray95", "gray15"))
        footer.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            footer,
            text="Připraveno",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50")
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # OCR engine status
        if self.ocr_engine:
            ocr_status = "✅ Tesseract připraven"
        else:
            ocr_status = "❌ Tesseract není dostupný"
        
        ctk.CTkLabel(
            footer,
            text=ocr_status,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50")
        ).pack(side="right", padx=10, pady=5)
    
    def _toggle_theme(self):
        """Toggle between dark and light theme - optimized."""
        mode = self.theme_var.get()
        
        # Update label immediately for responsiveness
        if mode == "dark":
            self.theme_switch.configure(text="🌙 Tmavý režim")
        else:
            self.theme_switch.configure(text="☀️ Světlý režim")
        
        # Save to config
        self.config.set_theme(mode)
        
        # Defer the heavy theme change to avoid UI freeze
        self.after(10, lambda: self._apply_theme(mode))
    
    def _apply_theme(self, mode: str):
        """Apply theme change with optimization."""
        # Temporarily disable updates
        self.update_idletasks()
        
        # Apply the theme
        ctk.set_appearance_mode(mode)
    
    def _open_settings(self):
        """Open settings dialog."""
        SettingsDialog(self, self.config, on_save=self._on_settings_saved)
    
    def _on_settings_saved(self):
        """Handle settings saved - reinitialize OCR engine."""
        self._init_ocr_engine()
        
        # Update footer status
        if self.ocr_engine:
            self.status_label.configure(text="✅ OCR engine aktualizován")
        else:
            self.status_label.configure(text="❌ OCR engine není dostupný")
    
    def _open_file(self):
        """Open file dialog to select documents."""
        from src.pdf_handler import get_supported_formats
        
        formats = get_supported_formats()
        filetypes = [
            ("Podporované soubory", " ".join(f"*{ext}" for ext in formats)),
            ("Obrázky", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("PDF", "*.pdf"),
            ("Všechny soubory", "*.*")
        ]
        
        filepaths = filedialog.askopenfilenames(filetypes=filetypes)
        if filepaths:
            self._on_files_loaded(list(filepaths))
    
    def _on_files_loaded(self, filepaths: List[str]):
        """Handle files loaded event (supports multiple files)."""
        valid_files = [f for f in filepaths if os.path.exists(f)]
        
        if not valid_files:
            messagebox.showerror("Chyba", "\u017dádné platné soubory nebyly nalezeny.")
            return
        
        self.current_files = valid_files
        
        # Update status
        if len(valid_files) == 1:
            self.status_label.configure(text=f"Načten: {os.path.basename(valid_files[0])}")
        else:
            self.status_label.configure(text=f"Načteno {len(valid_files)} souborů")
        
        # Load files into views
        if self.ocr_engine:
            self.mode_a_view.load_files(valid_files)
            self.mode_b_view.load_files(valid_files)
            
            # Switch to Mode A tab
            self.tab_view.set("📝 Režim A: Digitalizace")
    

    
    def _clear_all(self):
        """Clear all loaded data."""
        self.current_files = []
        self.status_label.configure(text="Připraveno")
        
        if self.ocr_engine:
            self.mode_a_view.clear()
            self.mode_b_view.clear()
        
        self.tab_view.set("📁 Nahrát soubor")
    
    def _on_close(self):
        """Handle window close."""
        self.destroy()


def run_app():
    """Run the OCR application."""
    app = OCRApp()
    app.mainloop()
