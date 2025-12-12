"""
Mode B View - Smart Data Extraction.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import threading
from typing import Optional, List, Dict
import os

from .components import ImagePreview, ExportButton, LoadingSpinner, FieldDefinitionPanel, ResultsTable


class ModeBView(ctk.CTkFrame):
    """
    Smart data extraction view.
    User defines fields with examples, app extracts matching data.
    """
    
    def __init__(self, master, ocr_engine, **kwargs):
        super().__init__(master, **kwargs)
        
        self.ocr_engine = ocr_engine
        self.current_images: List[Image.Image] = []
        self.current_file_path: Optional[str] = None
        self.extracted_text: str = ""
        self.extraction_results: Dict[str, List[str]] = {}
        
        self.configure(fg_color="transparent")
        
        self._create_layout()
    
    def _create_layout(self):
        """Create the main layout with fixed panels."""
        # Three equal fixed columns
        self.grid_columnconfigure(0, weight=1, uniform="panel")
        self.grid_columnconfigure(1, weight=1, uniform="panel")
        self.grid_columnconfigure(2, weight=1, uniform="panel")
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel - Field definitions
        left_panel = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Left header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            left_header,
            text="⚙️ Nastavení polí",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Field definition panel
        self.field_panel = FieldDefinitionPanel(
            left_panel,
            on_fields_changed=self._on_fields_changed
        )
        self.field_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # Extract button
        self.extract_btn = ctk.CTkButton(
            left_panel,
            text="🔍 Extrahovat data",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._run_extraction,
            state="disabled"
        )
        self.extract_btn.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Middle panel - Document preview
        middle_panel = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        middle_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=0)
        middle_panel.grid_rowconfigure(1, weight=1)
        middle_panel.grid_columnconfigure(0, weight=1)
        
        # Middle header
        middle_header = ctk.CTkFrame(middle_panel, fg_color="transparent")
        middle_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            middle_header,
            text="📄 Dokument",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Image preview
        self.image_preview = ImagePreview(middle_panel, max_size=(400, 500))
        self.image_preview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Set callback for region selection
        self.image_preview.on_region_selected = self._on_region_selected
        
        # OCR status
        self.ocr_status = ctk.CTkLabel(
            middle_panel,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50")
        )
        self.ocr_status.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Right panel - Results
        right_panel = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=0)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Right header
        right_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        right_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            right_header,
            text="📊 Výsledky",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Results table
        self.results_table = ResultsTable(right_panel)
        self.results_table.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
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
            formats=["XLSX", "PDF"],
            on_export=self._export_results
        )
        self.export_btn.pack(side="left")
        self.export_btn.set_enabled(False)
        
        # Loading spinner
        self.loading = LoadingSpinner(self)
    
    def _on_fields_changed(self):
        """Handle field definition changes."""
        self._update_extract_button_state()
    
    def _update_extract_button_state(self):
        """Update extract button state based on available data."""
        has_file = len(self.current_images) > 0
        has_fields = len(self.field_panel.get_fields()) > 0
        
        if has_file and has_fields:
            self.extract_btn.configure(state="normal")
        else:
            self.extract_btn.configure(state="disabled")
    
    def load_file(self, file_path: str):
        """Load a single file for processing."""
        self.load_files([file_path])
    
    def load_files(self, file_paths: List[str]):
        """Load multiple files for processing."""
        if not file_paths:
            return
        
        self.current_file_paths = file_paths
        self.current_file_path = file_paths[0]  # For backward compatibility
        self.extracted_text = ""
        
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
        self.ocr_status.configure(text="Dokument načten. Spusťte extrakci.")
        self._update_extract_button_state()
    
    def _on_load_error(self, error: str):
        """Handle load error."""
        self.loading.hide()
        messagebox.showerror("Chyba", f"Nelze načíst soubor:\n{error}")
    
    def _on_region_selected(self, cropped_image, bbox):
        """Handle region selection - OCR the region and offer to save as preset."""
        import customtkinter as ctk
        
        # Run OCR on the cropped region
        self.loading.show("Čtu vybranou oblast...")
        
        def ocr_region():
            try:
                from src.image_utils import preprocess_for_ocr
                processed = preprocess_for_ocr(cropped_image.copy())
                text = self.ocr_engine.extract_text_from_image(processed)
                text = text.strip()
                self.after(0, lambda: self._show_region_result(text, cropped_image))
            except Exception as e:
                self.after(0, lambda: self._on_region_ocr_error(str(e)))
        
        threading.Thread(target=ocr_region, daemon=True).start()
    
    def _on_region_ocr_error(self, error: str):
        """Handle OCR error for region."""
        self.loading.hide()
        messagebox.showerror("Chyba OCR", f"Nepodařilo se přečíst vybranou oblast:\n{error}")
    
    def _show_region_result(self, text: str, cropped_image):
        """Show dialog with OCR result and option to save as preset."""
        import customtkinter as ctk
        
        self.loading.hide()
        
        if not text:
            messagebox.showwarning("Upozornění", "Ve vybrané oblasti nebyl nalezen žádný text.")
            return
        
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Extrahovaný text z oblasti")
        dialog.geometry("450x320")
        dialog.grab_set()
        
        # Label
        ctk.CTkLabel(
            dialog,
            text="🎯 Text nalezený ve vybrané oblasti:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(15, 5))
        
        # Text display
        text_frame = ctk.CTkFrame(dialog, fg_color=("white", "gray20"))
        text_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            text_frame,
            text=text,
            font=ctk.CTkFont(size=14),
            wraplength=400
        ).pack(pady=15, padx=10)
        
        # Field name input
        ctk.CTkLabel(
            dialog,
            text="Název pole (pro uložení jako předvolbu):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=20, pady=(10, 2))
        
        field_name_entry = ctk.CTkEntry(dialog, placeholder_text="např. Číslo faktury")
        field_name_entry.pack(fill="x", padx=20, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        def add_field():
            """Add as current field for extraction."""
            name = field_name_entry.get().strip() or "Vybraná oblast"
            self.field_panel.fields[name] = text
            self.field_panel._update_fields_list()
            if self.field_panel.on_fields_changed:
                self.field_panel.on_fields_changed()
            dialog.destroy()
            self.ocr_status.configure(text=f"Pole '{name}' přidáno k extrakci.")
        
        def save_as_preset():
            """Save as preset for future use."""
            name = field_name_entry.get().strip()
            if not name:
                messagebox.showwarning("Upozornění", "Zadejte název pole pro předvolbu.")
                return
            
            # Check if exists
            for existing_name, _ in self.field_panel.presets:
                if existing_name == name:
                    messagebox.showwarning("Upozornění", f"Předvolba '{name}' již existuje.")
                    return
            
            self.field_panel.presets.append((name, text))
            self.field_panel._save_presets()
            self.field_panel._update_preset_buttons()
            
            # Also add to current fields
            self.field_panel.fields[name] = text
            self.field_panel._update_fields_list()
            if self.field_panel.on_fields_changed:
                self.field_panel.on_fields_changed()
            
            dialog.destroy()
            messagebox.showinfo("Úspěch", f"Předvolba '{name}' byla uložena a přidána k extrakci.")
        
        ctk.CTkButton(
            btn_frame,
            text="➕ Přidat k extrakci",
            command=add_field,
            width=130
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Uložit jako předvolbu",
            command=save_as_preset,
            width=150,
            fg_color=("green", "darkgreen")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Zrušit",
            command=dialog.destroy,
            width=80,
            fg_color=("gray70", "gray40")
        ).pack(side="right", padx=5)
    
    def _run_extraction(self):
        """Run smart extraction on the document."""
        if not self.current_images:
            return
        
        fields = self.field_panel.get_fields()
        if not fields:
            messagebox.showwarning("Upozornění", "Nejprve definujte alespoň jedno pole pro extrakci.")
            return
        
        self.loading.show("Probíhá rozpoznávání a extrakce...")
        self.extract_btn.configure(state="disabled")
        
        def process_extraction():
            try:
                # First, run OCR on all pages
                all_text = []
                total = len(self.current_images)
                
                for i, image in enumerate(self.current_images):
                    self.after(0, lambda i=i, t=total: self.loading.show(
                        f"OCR stránka {i+1}/{t}..."
                    ))
                    
                    from src.image_utils import preprocess_for_ocr
                    processed = preprocess_for_ocr(image.copy())
                    text = self.ocr_engine.extract_text_from_image(processed)
                    all_text.append(text)
                
                full_text = "\n\n".join(all_text)
                self.extracted_text = full_text
                
                # Now run smart extraction
                self.after(0, lambda: self.loading.show("Hledání dat..."))
                
                from src.pattern_matcher import PatternMatcher, COMMON_PATTERNS
                import re
                matcher = PatternMatcher()
                
                results = {}
                
                # Check for special "DODACI_LIST_AUTO" mode
                if any(example == "DODACI_LIST_AUTO" for example in fields.values()):
                    # Use specialized delivery note extraction
                    dl_data = matcher.extract_delivery_note(full_text)
                    
                    # Convert to results format
                    results["Číslo dokladu"] = [dl_data['cislo_dokladu']] if dl_data['cislo_dokladu'] else []
                    results["Objednávka"] = [dl_data['objednavka']] if dl_data['objednavka'] else []
                    results["Datum pořízení"] = [dl_data['datum_porizeni']] if dl_data['datum_porizeni'] else []
                    results["Firma názov"] = [dl_data['dodavatel_nazev']] if dl_data['dodavatel_nazev'] else []
                    results["Firma adresa"] = [dl_data.get('dodavatel_adresa')] if dl_data.get('dodavatel_adresa') else []
                    results["Firma IČ"] = [dl_data['dodavatel_ic']] if dl_data['dodavatel_ic'] else []
                    results["Firma DIČ"] = [dl_data['dodavatel_dic']] if dl_data['dodavatel_dic'] else []
                    results["Vystavil"] = [dl_data.get('vystavil')] if dl_data.get('vystavil') else []
                    
                    # Format items
                    if dl_data['polozky']:
                        items_text = []
                        for item in dl_data['polozky']:
                            items_text.append(f"{item['oznaceni']}: {item['popis']} ({item['mnozstvi']} {item['jednotka']})")
                        results["Položky"] = items_text
                        results["Počet položek"] = [str(len(dl_data['polozky']))]
                else:
                    # PROBABILITY INFERENCE ENGINE (Smart AI Assistant) for generic fields
                    from src.inference_engine import InferenceEngine
                    inference = InferenceEngine()
                    
                    for field_name, example in fields.items():
                        field_lower = field_name.lower()
                        example_lower = example.lower()
                        
                        # Determine known type automatically
                        field_type = 'general'
                        if any(x in field_lower or x in example_lower for x in ['ič', 'ico', 'ičo']):
                            field_type = 'ico'
                        elif any(x in field_lower or x in example_lower for x in ['dič', 'dic']):
                            field_type = 'dic'
                        elif any(x in field_lower or x in example_lower for x in ['datum', 'date', 'pořízení']):
                            field_type = 'date'
                        elif any(x in field_lower for x in ['číslo dokladu', 'doklad']):
                            field_type = 'doc_number'
                        
                        # Determine section preference
                        section = None
                        if 'dodavatel' in field_lower or 'dodavatel' in example_lower:
                            section = 'supplier'
                        elif 'odběratel' in field_lower or 'odběratel' in example_lower:
                            section = 'customer'

                        # Use Inference Engine for supported types
                        if field_type != 'general':
                            keywords = [field_name, example] # Use field name and example as context keywords
                            best = inference.find_best(full_text, field_type, keywords, preferred_section=section)
                            
                            if best:
                                value = best['value']
                                # Add visual indicator for low confidence
                                if best['confidence'] == 'LOW':
                                    value += " ⚠️"
                                    
                                results[field_name] = [value]
                                continue # Found it, skip to next field
                        
                        # Fallback to standard PatternMatcher for others or if Inference failed
                        # Decide extraction strategy based on example type
                        
                        # Check if example is a label (for label-based extraction)
                        label_keywords = ['číslo', 'datum', 'objednávka', 'dodavatel', 'odběratel',
                                         'faktura', 'doklad', 'ič', 'dič', 'sklad', 'popis', 
                                         'množství', 'označení', 'název']
                        
                        is_label = any(kw in example_lower for kw in label_keywords)
                        
                        if is_label:
                            # Use label-based extraction
                            matches = matcher.find_by_label(full_text, example, max_length=60)
                            results[field_name] = matches if matches else []
                        else:
                            # Fallback to pattern learning
                            matcher.learn_pattern(field_name, example)
                            matches = matcher.find_matches(full_text, field_name)
                            results[field_name] = matches
                
                self.after(0, lambda: self._on_extraction_complete(results))
                
            except Exception as e:
                self.after(0, lambda: self._on_extraction_error(str(e)))
        
        threading.Thread(target=process_extraction, daemon=True).start()
    
    def _on_extraction_complete(self, results: Dict[str, List[str]]):
        """Handle extraction completion."""
        self.loading.hide()
        self.extraction_results = results
        
        # Count total matches
        total_matches = sum(len(v) for v in results.values())
        
        # Update status
        self.ocr_status.configure(
            text=f"Extrakce dokončena. Nalezeno {total_matches} hodnot."
        )
        
        # Display results
        self.results_table.display_results(results)
        
        self.extract_btn.configure(state="normal")
        self.export_btn.set_enabled(total_matches > 0)
    
    def _on_extraction_error(self, error: str):
        """Handle extraction error."""
        self.loading.hide()
        self.extract_btn.configure(state="normal")
        messagebox.showerror("Chyba", f"Nepodařilo se provést extrakci:\n{error}")
    
    def _export_results(self, format_type: str):
        """Export extraction results."""
        if not self.extraction_results:
            messagebox.showwarning("Upozornění", "Nejsou k dispozici žádné výsledky pro export.")
            return
        
        # Get file extension
        ext_map = {"XLSX": ".xlsx", "PDF": ".pdf"}
        extension = ext_map.get(format_type, ".xlsx")
        
        # Default filename
        if self.current_file_path:
            default_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        else:
            default_name = "extrakce"
        
        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=extension,
            initialfile=f"{default_name}_data{extension}",
            filetypes=[(format_type, f"*{extension}")]
        )
        
        if not filepath:
            return
        
        try:
            from src.exporters import export_matches_to_xlsx, export_table_to_pdf
            
            if format_type == "XLSX":
                export_matches_to_xlsx(self.extraction_results, filepath)
            elif format_type == "PDF":
                # Convert to list of dicts for PDF export
                columns = list(self.extraction_results.keys())
                max_rows = max(len(v) for v in self.extraction_results.values()) if self.extraction_results else 0
                
                data = []
                for i in range(max_rows):
                    row = {}
                    for col in columns:
                        values = self.extraction_results[col]
                        row[col] = values[i] if i < len(values) else ""
                    data.append(row)
                
                export_table_to_pdf(data, columns, filepath, title="Extrahovaná data")
            
            messagebox.showinfo("Úspěch", f"Soubor byl uložen:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Chyba exportu", f"Nepodařilo se uložit soubor:\n{e}")
    
    def clear(self):
        """Clear everything."""
        self.current_images = []
        self.current_file_path = None
        self.extracted_text = ""
        self.extraction_results = {}
        self.image_preview.clear()
        self.results_table.clear()
        self.ocr_status.configure(text="")
        self.extract_btn.configure(state="disabled")
        self.export_btn.set_enabled(False)
