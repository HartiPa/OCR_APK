"""
Mode A View - Full Document Digitization.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import threading
from typing import Optional, Callable, List
import os

from .components import ImagePreview, ExportButton, LoadingSpinner


class ModeAView(ctk.CTkFrame):
    """
    Full document digitization view.
    Displays document preview on left, extracted text on right.
    """
    
    def __init__(self, master, ocr_engine, **kwargs):
        super().__init__(master, **kwargs)
        
        self.ocr_engine = ocr_engine
        self.current_images: List[Image.Image] = []
        self.current_file_path: Optional[str] = None
        self.extracted_text: str = ""
        
        self.configure(fg_color="transparent")
        
        self._create_layout()
    
    def _create_layout(self):
        """Create the main layout with fixed panels."""
        # Main container with two equal fixed columns
        self.grid_columnconfigure(0, weight=1, uniform="panel")
        self.grid_columnconfigure(1, weight=1, uniform="panel")
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - Document preview
        left_panel = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Left header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            left_header,
            text="📄 Náhled dokumentu",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Image preview
        self.image_preview = ImagePreview(left_panel, max_size=(500, 600))
        self.image_preview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # OCR button
        self.ocr_btn = ctk.CTkButton(
            left_panel,
            text="🔍 Přečíst vše",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._run_ocr,
            state="disabled"
        )
        self.ocr_btn.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Right panel - Extracted text
        right_panel = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Right header
        right_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        right_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            right_header,
            text="📝 Extrahovaný text",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Text area
        self.text_area = ctk.CTkTextbox(
            right_panel,
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Export panel
        export_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        export_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            export_frame,
            text="Exportovat jako:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))
        
        self.export_btn = ExportButton(
            export_frame,
            formats=["TXT", "DOCX", "PDF"],
            on_export=self._export_text
        )
        self.export_btn.pack(side="left")
        self.export_btn.set_enabled(False)
        
        # Loading spinner (overlay)
        self.loading = LoadingSpinner(self)
    
    def load_file(self, file_path: str):
        """Load a single file for OCR processing."""
        self.load_files([file_path])
    
    def load_files(self, file_paths: List[str]):
        """Load multiple files for OCR processing."""
        if not file_paths:
            return
        
        self.current_file_paths = file_paths
        self.current_file_path = file_paths[0]  # For backward compatibility
        
        self.loading.show(f"Načítání {len(file_paths)} souborů...")
        
        def load_all_files():
            try:
                all_images = []
                
                for file_path in file_paths:
                    if file_path.lower().endswith('.pdf'):
                        from src.pdf_handler import pdf_to_images, check_pdf_support
                        
                        if check_pdf_support():
                            images = pdf_to_images(file_path)
                            all_images.extend(images)
                    else:
                        # Load image directly
                        image = Image.open(file_path)
                        all_images.append(image)
                
                self.after(0, lambda: self._on_images_loaded(all_images))
                
            except Exception as e:
                self.after(0, lambda: self._on_load_error(str(e)))
        
        threading.Thread(target=load_all_files, daemon=True).start()
    
    def _on_images_loaded(self, images: List[Image.Image]):
        """Handle loaded images."""
        self.loading.hide()
        self.current_images = images
        self.image_preview.display_images(images)
        self.ocr_btn.configure(state="normal")
    
    def _on_load_error(self, error: str):
        """Handle load error."""
        self.loading.hide()
        messagebox.showerror("Chyba", f"Nelze načíst soubor:\n{error}")
    
    def _run_ocr(self):
        """Run OCR on the loaded document."""
        if not self.current_images:
            return
        
        self.loading.show("Probíhá rozpoznávání textu...")
        self.ocr_btn.configure(state="disabled")
        
        def process_ocr():
            try:
                all_text = []
                total = len(self.current_images)
                
                for i, image in enumerate(self.current_images):
                    # Update loading message
                    self.after(0, lambda i=i, t=total: self.loading.show(
                        f"Rozpoznávání stránky {i+1}/{t}..."
                    ))
                    
                    # Process with preprocessing
                    from src.image_utils import preprocess_for_ocr
                    processed = preprocess_for_ocr(image.copy())
                    text = self.ocr_engine.extract_text_from_image(processed)
                    
                    if total > 1:
                        all_text.append(f"--- Stránka {i+1} ---\n{text}")
                    else:
                        all_text.append(text)
                
                full_text = "\n\n".join(all_text)
                self.after(0, lambda: self._on_ocr_complete(full_text))
                
            except Exception as e:
                self.after(0, lambda: self._on_ocr_error(str(e)))
        
        threading.Thread(target=process_ocr, daemon=True).start()
    
    def _on_ocr_complete(self, text: str):
        """Handle OCR completion."""
        self.loading.hide()
        self.extracted_text = text
        
        # Clear and insert text
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", text)
        
        self.ocr_btn.configure(state="normal")
        self.export_btn.set_enabled(True)
    
    def _on_ocr_error(self, error: str):
        """Handle OCR error."""
        self.loading.hide()
        self.ocr_btn.configure(state="normal")
        messagebox.showerror("Chyba OCR", f"Nepodařilo se rozpoznat text:\n{error}")
    
    def _export_text(self, format_type: str):
        """Export the extracted text."""
        if not self.extracted_text:
            messagebox.showwarning("Upozornění", "Není k dispozici žádný text pro export.")
            return
        
        # Get text from text area (may have been edited)
        current_text = self.text_area.get("1.0", "end-1c")
        
        # Get file extension
        ext_map = {"TXT": ".txt", "DOCX": ".docx", "PDF": ".pdf"}
        extension = ext_map.get(format_type, ".txt")
        
        # Default filename
        if self.current_file_path:
            default_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        else:
            default_name = "dokument"
        
        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=extension,
            initialfile=f"{default_name}_text{extension}",
            filetypes=[(format_type, f"*{extension}")]
        )
        
        if not filepath:
            return
        
        try:
            from src.exporters import export_to_txt, export_to_docx, export_to_pdf
            
            if format_type == "TXT":
                export_to_txt(current_text, filepath)
            elif format_type == "DOCX":
                export_to_docx(current_text, filepath, title="Extrahovaný dokument")
            elif format_type == "PDF":
                export_to_pdf(current_text, filepath, title="Extrahovaný dokument")
            
            messagebox.showinfo("Úspěch", f"Soubor byl uložen:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Chyba exportu", f"Nepodařilo se uložit soubor:\n{e}")
    
    def clear(self):
        """Clear the current document."""
        self.current_images = []
        self.current_file_path = None
        self.extracted_text = ""
        self.image_preview.clear()
        self.text_area.delete("1.0", "end")
        self.ocr_btn.configure(state="disabled")
        self.export_btn.set_enabled(False)
