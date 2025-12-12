"""
UI Components Module - Reusable CustomTkinter components.
"""
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
from typing import Callable, Optional, List, Tuple
import os


class FileDropZone(ctk.CTkFrame):
    """
    A drop zone for file upload with drag & drop support.
    Supports multiple file selection.
    """
    
    def __init__(self, master, on_file_drop: Callable[[List[str]], None], 
                 supported_formats: List[str] = None, 
                 multiple: bool = True, **kwargs):
        super().__init__(master, **kwargs)
        
        # Callback now receives a list of files
        self.on_file_drop = on_file_drop
        self.supported_formats = supported_formats or ['.jpg', '.jpeg', '.png', '.pdf', '.bmp', '.tiff']
        self.multiple = multiple
        
        self.configure(
            fg_color=("gray90", "gray20"),
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray40")
        )
        
        # Icon and text
        self.label_icon = ctk.CTkLabel(
            self,
            text="📄",
            font=ctk.CTkFont(size=48)
        )
        self.label_icon.pack(pady=(30, 10))
        
        multi_text = "soubory" if multiple else "soubor"
        self.label_text = ctk.CTkLabel(
            self,
            text=f"Přetáhněte {multi_text} sem\nnebo klikněte pro výběr",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        )
        self.label_text.pack(pady=(0, 10))
        
        self.label_formats = ctk.CTkLabel(
            self,
            text=f"Podporované formáty: {', '.join(self.supported_formats)}",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50")
        )
        self.label_formats.pack(pady=(0, 30))
        
        # Bind click event
        self.bind("<Button-1>", self._on_click)
        self.label_icon.bind("<Button-1>", self._on_click)
        self.label_text.bind("<Button-1>", self._on_click)
        self.label_formats.bind("<Button-1>", self._on_click)
        
        # Bind hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Try to enable drag and drop
        self._setup_dnd()
    
    def _setup_dnd(self):
        """Setup drag and drop if available."""
        try:
            # Try to register for drag and drop
            self.drop_target_register('DND_Files')
            self.dnd_bind('<<Drop>>', self._on_dnd_drop)
            self.dnd_bind('<<DragEnter>>', self._on_dnd_enter)
            self.dnd_bind('<<DragLeave>>', self._on_dnd_leave)
        except Exception:
            # DnD not available, fall back to click only
            pass
    
    def _on_dnd_drop(self, event):
        """Handle file drop via drag and drop."""
        # Parse the dropped files (format depends on OS)
        data = event.data
        
        # Windows returns paths in curly braces if they contain spaces
        files = []
        if '{' in data:
            # Parse paths with spaces
            import re
            files = re.findall(r'\{([^}]+)\}|(\S+)', data)
            files = [f[0] or f[1] for f in files if f[0] or f[1]]
        else:
            files = data.split()
        
        # Filter by supported formats
        valid_files = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in self.supported_formats:
                valid_files.append(f)
        
        # Reset visual state
        self.set_active(False)
        
        if valid_files:
            if not self.multiple:
                valid_files = valid_files[:1]
            self.on_file_drop(valid_files)
    
    def _on_dnd_enter(self, event):
        """Visual feedback when dragging over."""
        self.set_active(True)
        return event.action
    
    def _on_dnd_leave(self, event):
        """Reset visual state when leaving."""
        self.set_active(False)
    
    def _on_click(self, event=None):
        """Handle click to open file dialog."""
        filetypes = [
            ("Podporované soubory", " ".join(f"*{ext}" for ext in self.supported_formats)),
            ("Obrázky", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif"),
            ("PDF", "*.pdf"),
            ("Všechny soubory", "*.*")
        ]
        
        if self.multiple:
            filepaths = filedialog.askopenfilenames(filetypes=filetypes)
            if filepaths:
                self.on_file_drop(list(filepaths))
        else:
            filepath = filedialog.askopenfilename(filetypes=filetypes)
            if filepath:
                self.on_file_drop([filepath])
    
    def _on_enter(self, event=None):
        """Hover effect."""
        self.configure(border_color=("blue", "lightblue"))
    
    def _on_leave(self, event=None):
        """Remove hover effect."""
        self.configure(border_color=("gray70", "gray40"))
    
    def set_active(self, active: bool):
        """Set visual state when file is being dragged over."""
        if active:
            self.configure(
                fg_color=("lightblue", "darkblue"),
                border_color=("blue", "lightblue")
            )
            self.label_icon.configure(text="📥")
        else:
            self.configure(
                fg_color=("gray90", "gray20"),
                border_color=("gray70", "gray40")
            )
            self.label_icon.configure(text="📄")


class ImagePreview(ctk.CTkFrame):
    """
    Image preview panel with zoom controls and page navigation.
    """
    
    ZOOM_LEVELS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
    DEFAULT_ZOOM_INDEX = 3  # 1.0 = 100%
    
    def __init__(self, master, max_size: Tuple[int, int] = (600, 500), **kwargs):
        super().__init__(master, **kwargs)
        
        self.max_size = max_size
        self.original_images: List[Image.Image] = []
        self.current_image = None
        self.photo_image = None
        self.zoom_index = self.DEFAULT_ZOOM_INDEX
        
        self.configure(fg_color=("gray95", "gray15"))
        
        # Top controls - zoom
        self.zoom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.zoom_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Zoom out button
        self.zoom_out_btn = ctk.CTkButton(
            self.zoom_frame,
            text="🔍−",
            width=40,
            height=28,
            command=self._zoom_out,
            state="disabled"
        )
        self.zoom_out_btn.pack(side="left", padx=2)
        
        # Zoom level label
        self.zoom_label = ctk.CTkLabel(
            self.zoom_frame,
            text="100%",
            font=ctk.CTkFont(size=12),
            width=50
        )
        self.zoom_label.pack(side="left", padx=5)
        
        # Zoom in button
        self.zoom_in_btn = ctk.CTkButton(
            self.zoom_frame,
            text="🔍+",
            width=40,
            height=28,
            command=self._zoom_in,
            state="disabled"
        )
        self.zoom_in_btn.pack(side="left", padx=2)
        
        # Fit to window button
        self.fit_btn = ctk.CTkButton(
            self.zoom_frame,
            text="⊞ Přizpůsobit",
            width=90,
            height=28,
            command=self._fit_to_window,
            state="disabled"
        )
        self.fit_btn.pack(side="left", padx=5)
        
        # Region selection button
        self.select_btn = ctk.CTkButton(
            self.zoom_frame,
            text="✏️ Označit oblast",
            width=110,
            height=28,
            command=self._toggle_selection_mode,
            state="disabled",
            fg_color=("gray70", "gray40")
        )
        self.select_btn.pack(side="left", padx=5)
        
        # Selection mode variables
        self.selection_mode = False
        self.selection_start = None
        self.selection_rect_id = None
        self.on_region_selected = None  # Callback: (image_crop, bbox) -> None
        
        # Scrollable canvas for image
        self.canvas_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        self.canvas_frame.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Create canvas with scrollbars
        import tkinter as tk
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="#2b2b2b",
            highlightthickness=0
        )
        
        self.v_scrollbar = ctk.CTkScrollbar(self.canvas_frame, command=self.canvas.yview)
        self.h_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Grid layout for canvas and scrollbars
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Placeholder text
        self.placeholder_id = self.canvas.create_text(
            200, 150, text="Náhled dokumentu", fill="gray", font=("Arial", 14)
        )
        
        # Bind mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_mouse_wheel)
        
        # Bind mouse drag for panning (click and drag)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._drag_data = {"x": 0, "y": 0, "dragging": False}
        
        # Change cursor when hovering over canvas with image
        self.canvas.bind("<Enter>", lambda e: self.canvas.configure(cursor="fleur") if self.images else None)
        self.canvas.bind("<Leave>", lambda e: self.canvas.configure(cursor=""))
        
        # Bottom controls - page navigation
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # First page button
        self.first_btn = ctk.CTkButton(
            self.nav_frame,
            text="⏮",
            width=35,
            height=28,
            command=self._first_page,
            state="disabled"
        )
        self.first_btn.pack(side="left", padx=1)
        
        # Previous page button
        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="◀",
            width=35,
            height=28,
            command=self._prev_page,
            state="disabled"
        )
        self.prev_btn.pack(side="left", padx=1)
        
        # Page label
        self.page_label = ctk.CTkLabel(
            self.nav_frame,
            text="",
            font=ctk.CTkFont(size=12),
            width=100
        )
        self.page_label.pack(side="left", padx=5)
        
        # Next page button
        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="▶",
            width=35,
            height=28,
            command=self._next_page,
            state="disabled"
        )
        self.next_btn.pack(side="left", padx=1)
        
        # Last page button
        self.last_btn = ctk.CTkButton(
            self.nav_frame,
            text="⏭",
            width=35,
            height=28,
            command=self._last_page,
            state="disabled"
        )
        self.last_btn.pack(side="left", padx=1)
        
        # Page tracking
        self.current_page = 0
        self.total_pages = 0
        self.images: List[Image.Image] = []
        self.on_page_change = None
        self._tk_image = None  # Keep reference to prevent garbage collection
    
    def display_image(self, image: Image.Image):
        """Display a single image."""
        self.display_images([image])
    
    def display_images(self, images: List[Image.Image]):
        """Display multiple images (pages)."""
        self.images = images
        self.original_images = images
        self.current_page = 0
        self.total_pages = len(images)
        self.zoom_index = self.DEFAULT_ZOOM_INDEX
        self._update_display()
        self._update_controls()
    
    def _update_display(self):
        """Update the displayed image with current zoom."""
        if not self.images:
            return
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Get current image
        original = self.images[self.current_page]
        
        # Apply zoom
        zoom = self.ZOOM_LEVELS[self.zoom_index]
        new_width = int(original.width * zoom)
        new_height = int(original.height * zoom)
        
        # Limit size to prevent memory issues
        max_dim = 4000
        if new_width > max_dim or new_height > max_dim:
            scale = max_dim / max(new_width, new_height)
            new_width = int(new_width * scale)
            new_height = int(new_height * scale)
        
        # Resize image
        resized = original.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage (using tkinter's PhotoImage for canvas)
        from PIL import ImageTk
        self._tk_image = ImageTk.PhotoImage(resized)
        
        # Display on canvas
        self.canvas.create_image(0, 0, anchor="nw", image=self._tk_image)
        
        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
        
        # Update zoom label
        self.zoom_label.configure(text=f"{int(zoom * 100)}%")
    
    def _update_controls(self):
        """Update all control states."""
        has_images = len(self.images) > 0
        
        # Zoom controls
        zoom_state = "normal" if has_images else "disabled"
        self.zoom_in_btn.configure(state=zoom_state if self.zoom_index < len(self.ZOOM_LEVELS) - 1 else "disabled")
        self.zoom_out_btn.configure(state=zoom_state if self.zoom_index > 0 else "disabled")
        self.fit_btn.configure(state=zoom_state)
        self.select_btn.configure(state=zoom_state)
        
        # Page navigation
        if self.total_pages > 1:
            self.page_label.configure(text=f"Stránka {self.current_page + 1} / {self.total_pages}")
            self.first_btn.configure(state="normal" if self.current_page > 0 else "disabled")
            self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
            self.last_btn.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
        else:
            self.page_label.configure(text="" if self.total_pages == 0 else "1 stránka")
            self.first_btn.configure(state="disabled")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            self.last_btn.configure(state="disabled")
    
    def _zoom_in(self):
        """Increase zoom level."""
        if self.zoom_index < len(self.ZOOM_LEVELS) - 1:
            self.zoom_index += 1
            self._update_display()
            self._update_controls()
    
    def _zoom_out(self):
        """Decrease zoom level."""
        if self.zoom_index > 0:
            self.zoom_index -= 1
            self._update_display()
            self._update_controls()
    
    def _fit_to_window(self):
        """Fit image to window size."""
        if not self.images:
            return
        
        original = self.images[self.current_page]
        
        # Calculate zoom to fit
        canvas_width = self.canvas.winfo_width() or self.max_size[0]
        canvas_height = self.canvas.winfo_height() or self.max_size[1]
        
        zoom_w = canvas_width / original.width
        zoom_h = canvas_height / original.height
        target_zoom = min(zoom_w, zoom_h) * 0.95  # 95% to leave margin
        
        # Find closest zoom level
        best_index = 0
        best_diff = abs(self.ZOOM_LEVELS[0] - target_zoom)
        for i, z in enumerate(self.ZOOM_LEVELS):
            diff = abs(z - target_zoom)
            if diff < best_diff:
                best_diff = diff
                best_index = i
        
        self.zoom_index = best_index
        self._update_display()
        self._update_controls()
    
    def _on_mouse_wheel(self, event):
        """Scroll with mouse wheel."""
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
    
    def _on_ctrl_mouse_wheel(self, event):
        """Zoom with Ctrl + mouse wheel."""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
    
    def _on_drag_start(self, event):
        """Start drag or selection operation."""
        if self.selection_mode:
            self._on_selection_start(event)
            return
        
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["dragging"] = True
        self.canvas.configure(cursor="fleur")
    
    def _on_drag_move(self, event):
        """Handle drag movement - pan the image or draw selection."""
        if self.selection_mode:
            self._on_selection_drag(event)
            return
        
        if not self._drag_data["dragging"]:
            return
        
        # Calculate delta - reduce speed by dividing
        dx = (event.x - self._drag_data["x"]) / 3
        dy = (event.y - self._drag_data["y"]) / 3
        
        # Scroll canvas using moveto for smoother scrolling
        # Get current scroll position
        x_pos = self.canvas.xview()[0]
        y_pos = self.canvas.yview()[0]
        
        # Calculate scroll region size
        scroll_region = self.canvas.cget("scrollregion").split()
        if scroll_region and len(scroll_region) == 4:
            width = float(scroll_region[2]) - float(scroll_region[0])
            height = float(scroll_region[3]) - float(scroll_region[1])
            
            # Calculate new position as fraction
            new_x = x_pos - (dx / width) if width > 0 else x_pos
            new_y = y_pos - (dy / height) if height > 0 else y_pos
            
            # Clamp to valid range
            new_x = max(0, min(1, new_x))
            new_y = max(0, min(1, new_y))
            
            self.canvas.xview_moveto(new_x)
            self.canvas.yview_moveto(new_y)
        
        # Update drag position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
    
    def _on_drag_end(self, event):
        """End drag or selection operation."""
        if self.selection_mode:
            self._on_selection_end(event)
            return
        
        self._drag_data["dragging"] = False
        if self.images:
            self.canvas.configure(cursor="fleur")
        else:
            self.canvas.configure(cursor="")
    
    def _first_page(self):
        """Go to first page."""
        if self.current_page != 0:
            self.current_page = 0
            self._update_display()
            self._update_controls()
            if self.on_page_change:
                self.on_page_change(self.current_page)
    
    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_display()
            self._update_controls()
            if self.on_page_change:
                self.on_page_change(self.current_page)
    
    def _next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_display()
            self._update_controls()
            if self.on_page_change:
                self.on_page_change(self.current_page)
    
    def _last_page(self):
        """Go to last page."""
        if self.current_page != self.total_pages - 1:
            self.current_page = self.total_pages - 1
            self._update_display()
            self._update_controls()
            if self.on_page_change:
                self.on_page_change(self.current_page)
    
    def clear(self):
        """Clear the preview."""
        self.images = []
        self.original_images = []
        self.current_page = 0
        self.total_pages = 0
        self.zoom_index = self.DEFAULT_ZOOM_INDEX
        self._tk_image = None
        self.selection_mode = False
        self.selection_start = None
        if self.selection_rect_id:
            self.canvas.delete(self.selection_rect_id)
            self.selection_rect_id = None
        self.canvas.delete("all")
        self.placeholder_id = self.canvas.create_text(
            200, 150, text="Náhled dokumentu", fill="gray", font=("Arial", 14)
        )
        self._update_controls()
    
    def get_current_page(self) -> int:
        """Get current page index."""
        return self.current_page
    
    def _toggle_selection_mode(self):
        """Toggle region selection mode."""
        self.selection_mode = not self.selection_mode
        
        if self.selection_mode:
            self.select_btn.configure(fg_color=("green", "darkgreen"), text="✏️ Vybírám...")
            self.canvas.configure(cursor="crosshair")
            # Clear any existing selection
            if self.selection_rect_id:
                self.canvas.delete(self.selection_rect_id)
                self.selection_rect_id = None
        else:
            self.select_btn.configure(fg_color=("gray70", "gray40"), text="✏️ Označit oblast")
            self.canvas.configure(cursor="fleur" if self.images else "")
    
    def _on_selection_start(self, event):
        """Start drawing selection rectangle."""
        if not self.selection_mode:
            return
        
        # Get canvas coordinates
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        self.selection_start = (x, y)
        
        # Remove old rectangle
        if self.selection_rect_id:
            self.canvas.delete(self.selection_rect_id)
        
        # Create new rectangle
        self.selection_rect_id = self.canvas.create_rectangle(
            x, y, x, y,
            outline="red", width=2, dash=(4, 4)
        )
    
    def _on_selection_drag(self, event):
        """Update selection rectangle while dragging."""
        if not self.selection_mode or not self.selection_start:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Update rectangle
        self.canvas.coords(
            self.selection_rect_id,
            self.selection_start[0], self.selection_start[1], x, y
        )
    
    def _on_selection_end(self, event):
        """Complete selection and extract region."""
        if not self.selection_mode or not self.selection_start:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Get selection bounds
        x1, y1 = self.selection_start
        x2, y2 = x, y
        
        # Normalize coordinates (ensure x1 < x2, y1 < y2)
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Ignore tiny selections
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            self.selection_start = None
            return
        
        # Convert canvas coords to original image coords
        zoom = self.ZOOM_LEVELS[self.zoom_index]
        orig_x1 = int(x1 / zoom)
        orig_y1 = int(y1 / zoom)
        orig_x2 = int(x2 / zoom)
        orig_y2 = int(y2 / zoom)
        
        # Get current original image
        if self.images and self.current_page < len(self.images):
            original = self.images[self.current_page]
            
            # Clamp to image bounds
            orig_x1 = max(0, min(original.width, orig_x1))
            orig_y1 = max(0, min(original.height, orig_y1))
            orig_x2 = max(0, min(original.width, orig_x2))
            orig_y2 = max(0, min(original.height, orig_y2))
            
            # Crop image
            cropped = original.crop((orig_x1, orig_y1, orig_x2, orig_y2))
            bbox = (orig_x1, orig_y1, orig_x2, orig_y2)
            
            # Call callback if set
            if self.on_region_selected:
                self.on_region_selected(cropped, bbox)
        
        # Reset selection
        self.selection_start = None
        self._toggle_selection_mode()  # Exit selection mode


class ExportButton(ctk.CTkFrame):
    """
    Export button with format dropdown.
    """
    
    def __init__(self, master, formats: List[str], on_export: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.on_export = on_export
        self.formats = formats
        
        # Format selector
        self.format_var = ctk.StringVar(value=formats[0] if formats else "")
        
        self.format_menu = ctk.CTkOptionMenu(
            self,
            values=formats,
            variable=self.format_var,
            width=100
        )
        self.format_menu.pack(side="left", padx=(0, 5))
        
        # Export button
        self.export_btn = ctk.CTkButton(
            self,
            text="Exportovat",
            command=self._on_export_click,
            width=100
        )
        self.export_btn.pack(side="left")
    
    def _on_export_click(self):
        """Handle export button click."""
        format_type = self.format_var.get()
        self.on_export(format_type)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the export controls."""
        state = "normal" if enabled else "disabled"
        self.export_btn.configure(state=state)
        self.format_menu.configure(state=state)


class LoadingSpinner(ctk.CTkFrame):
    """
    Loading indicator overlay.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color=("white", "gray20"))
        
        self.label = ctk.CTkLabel(
            self,
            text="⏳ Zpracování...",
            font=ctk.CTkFont(size=16)
        )
        self.label.pack(expand=True)
        
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate", width=200)
        self.progress.pack(pady=10)
        
        # Hidden by default
        self.place_forget()
    
    def show(self, message: str = "Zpracování..."):
        """Show the loading spinner."""
        self.label.configure(text=f"⏳ {message}")
        self.progress.start()
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.lift()
    
    def hide(self):
        """Hide the loading spinner."""
        self.progress.stop()
        self.place_forget()


class FieldDefinitionPanel(ctk.CTkFrame):
    """
    Panel for defining extraction fields with examples.
    All presets are editable and deletable, stored persistently.
    """
    
    # Initial presets (used only if no saved presets exist)
    INITIAL_PRESETS = [
        ("IČO", "12345678"),
        ("DIČ", "CZ12345678"),
        ("Datum", "01.01.2024"),
    ]
    
    def __init__(self, master, on_fields_changed: Callable[[], None] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.on_fields_changed = on_fields_changed
        self.fields = {}  # field_name -> example
        self.presets = []  # All presets (editable)
        
        self.configure(fg_color=("gray95", "gray15"))
        
        # Load presets from file (or use initial if none exist)
        self._load_presets()
        
        # Header
        header = ctk.CTkLabel(
            self,
            text="Definice polí pro extrakci",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(pady=(10, 15), padx=10, anchor="w")
        
        # Input frame
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Field name input
        ctk.CTkLabel(input_frame, text="Název pole:").pack(anchor="w")
        self.field_name_entry = ctk.CTkEntry(input_frame, placeholder_text="např. Číslo faktury")
        self.field_name_entry.pack(fill="x", pady=(2, 5))
        
        # Example input
        ctk.CTkLabel(input_frame, text="Příklad formátu:").pack(anchor="w")
        self.example_entry = ctk.CTkEntry(input_frame, placeholder_text="např. 2023001")
        self.example_entry.pack(fill="x", pady=(2, 5))
        
        # Buttons row
        btn_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=5)
        
        # Add field button
        self.add_btn = ctk.CTkButton(
            btn_row,
            text="➕ Přidat pole",
            command=self._add_field,
            width=100
        )
        self.add_btn.pack(side="left", padx=2)
        
        # Save as preset button
        self.save_preset_btn = ctk.CTkButton(
            btn_row,
            text="💾 Uložit jako předvolbu",
            command=self._save_as_preset,
            width=140,
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50")
        )
        self.save_preset_btn.pack(side="left", padx=2)
        
        # Preset patterns section
        preset_frame = ctk.CTkFrame(self, fg_color="transparent")
        preset_frame.pack(fill="x", padx=10, pady=5)
        
        preset_header = ctk.CTkFrame(preset_frame, fg_color="transparent")
        preset_header.pack(fill="x")
        
        ctk.CTkLabel(preset_header, text="Rychlé předvolby:", font=ctk.CTkFont(size=12)).pack(side="left", anchor="w")
        
        # Manage presets button
        self.manage_btn = ctk.CTkButton(
            preset_header,
            text="⚙️ Spravovat",
            width=80,
            height=24,
            command=self._show_preset_manager,
            fg_color="transparent",
            hover_color=("gray80", "gray30")
        )
        self.manage_btn.pack(side="right")
        
        # Presets area - auto-adjusts to content (not scrollable)
        self.presets_frame = ctk.CTkFrame(preset_frame, fg_color="transparent")
        self.presets_frame.pack(fill="x", pady=2)
        
        self._update_preset_buttons()
        
        # Separator
        ctk.CTkFrame(self, height=2, fg_color=("gray80", "gray40")).pack(fill="x", padx=10, pady=5)
        
        # Fields list - large area to show all selected extraction fields
        ctk.CTkLabel(
            self,
            text="Pole k extrakci:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 0))
        
        self.fields_list_frame = ctk.CTkScrollableFrame(self)
        self.fields_list_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        self._update_fields_list()
    
    def _get_presets_file_path(self) -> str:
        """Get the path to the presets storage file."""
        import os
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(app_dir, "presets.json")
    
    def _load_presets(self):
        """Load presets from file, or use initial presets if none exist."""
        import json
        try:
            filepath = self._get_presets_file_path()
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.presets = [tuple(p) for p in data.get("presets", [])]
            else:
                # First run - use initial presets
                self.presets = list(self.INITIAL_PRESETS)
                self._save_presets()
        except Exception:
            self.presets = list(self.INITIAL_PRESETS)
    
    def _save_presets(self):
        """Save all presets to file."""
        import json
        try:
            filepath = self._get_presets_file_path()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"presets": self.presets}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _update_preset_buttons(self):
        """Update the preset buttons display."""
        for widget in self.presets_frame.winfo_children():
            widget.destroy()
        
        if not self.presets:
            ctk.CTkLabel(
                self.presets_frame,
                text="Žádné předvolby",
                text_color=("gray50", "gray50")
            ).pack(pady=5)
            return
        
        row = ctk.CTkFrame(self.presets_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        for i, (name, example) in enumerate(self.presets):
            if i > 0 and i % 4 == 0:
                row = ctk.CTkFrame(self.presets_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
            
            btn = ctk.CTkButton(
                row,
                text=name,
                width=70,
                height=26,
                command=lambda n=name, e=example: self._add_preset(n, e)
            )
            btn.pack(side="left", padx=2)
    
    def _save_as_preset(self):
        """Save current field input as a new preset."""
        from tkinter import messagebox
        
        name = self.field_name_entry.get().strip()
        example = self.example_entry.get().strip()
        
        if not name or not example:
            messagebox.showwarning("Upozornění", "Vyplňte název pole a příklad formátu.")
            return
        
        # Check if preset already exists
        for existing_name, _ in self.presets:
            if existing_name == name:
                messagebox.showwarning("Upozornění", f"Předvolba '{name}' již existuje.")
                return
        
        self.presets.append((name, example))
        self._save_presets()
        self._update_preset_buttons()
        
        self.field_name_entry.delete(0, "end")
        self.example_entry.delete(0, "end")
        
        messagebox.showinfo("Úspěch", f"Předvolba '{name}' byla uložena.")
    
    def _show_preset_manager(self):
        """Show dialog to manage all presets."""
        from tkinter import messagebox
        
        if not self.presets:
            messagebox.showinfo("Info", "Nemáte žádné předvolby.")
            return
        
        popup = ctk.CTkToplevel(self)
        popup.title("Správa předvoleb")
        popup.geometry("450x350")
        popup.grab_set()
        
        ctk.CTkLabel(
            popup,
            text="Všechny předvolby",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            popup,
            text="Klikněte na 🗑️ pro smazání předvolby",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50")
        ).pack()
        
        list_frame = ctk.CTkScrollableFrame(popup)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        def delete_preset(name):
            self.presets = [(n, e) for n, e in self.presets if n != name]
            self._save_presets()
            self._update_preset_buttons()
            popup.destroy()
            messagebox.showinfo("Úspěch", f"Předvolba '{name}' byla smazána.")
        
        for name, example in self.presets:
            row = ctk.CTkFrame(list_frame, fg_color=("white", "gray25"))
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(weight="bold"), width=100).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(row, text=f"({example})", text_color=("gray40", "gray60")).pack(side="left", padx=5)
            
            ctk.CTkButton(
                row,
                text="🗑️",
                width=35,
                height=28,
                fg_color=("red", "darkred"),
                hover_color=("darkred", "red"),
                command=lambda n=name: delete_preset(n)
            ).pack(side="right", padx=5, pady=5)
        
        ctk.CTkButton(
            popup,
            text="Zavřít",
            command=popup.destroy
        ).pack(pady=10)
    
    def _add_field(self):
        """Add a new field definition."""
        name = self.field_name_entry.get().strip()
        example = self.example_entry.get().strip()
        
        if name and example:
            self.fields[name] = example
            self.field_name_entry.delete(0, "end")
            self.example_entry.delete(0, "end")
            self._update_fields_list()
            
            if self.on_fields_changed:
                self.on_fields_changed()
    
    def _add_preset(self, name: str, example: str):
        """Add a preset field."""
        self.fields[name] = example
        self._update_fields_list()
        
        if self.on_fields_changed:
            self.on_fields_changed()
    
    def _remove_field(self, name: str):
        """Remove a field definition."""
        if name in self.fields:
            del self.fields[name]
            self._update_fields_list()
            
            if self.on_fields_changed:
                self.on_fields_changed()
    
    def _update_fields_list(self):
        """Update the displayed fields list."""
        # Clear existing
        for widget in self.fields_list_frame.winfo_children():
            widget.destroy()
        
        if not self.fields:
            ctk.CTkLabel(
                self.fields_list_frame,
                text="Žádná pole nejsou definována",
                text_color=("gray50", "gray50")
            ).pack(pady=20)
            return
        
        for name, example in self.fields.items():
            row = ctk.CTkFrame(self.fields_list_frame, fg_color=("white", "gray25"))
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                row,
                text=f"{name}",
                font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=10, pady=5)
            
            ctk.CTkLabel(
                row,
                text=f"(příklad: {example})",
                text_color=("gray40", "gray60")
            ).pack(side="left", padx=5, pady=5)
            
            ctk.CTkButton(
                row,
                text="✕",
                width=30,
                height=25,
                fg_color="transparent",
                hover_color=("red", "darkred"),
                command=lambda n=name: self._remove_field(n)
            ).pack(side="right", padx=5, pady=5)
    
    def get_fields(self) -> dict:
        """Get all defined fields."""
        return self.fields.copy()
    
    def clear_fields(self):
        """Clear all fields."""
        self.fields.clear()
        self._update_fields_list()


class ResultsTable(ctk.CTkFrame):
    """
    Table for displaying extraction results.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color=("gray95", "gray15"))
        self.data = {}
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="Výsledky extrakce",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        # Table area
        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._show_empty_message()
    
    def _show_empty_message(self):
        """Show message when no data."""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.table_frame,
            text="Nejsou k dispozici žádné výsledky.\nNahrajte dokument a spusťte extrakci.",
            text_color=("gray50", "gray50"),
            justify="center"
        ).pack(expand=True, pady=40)
    
    def display_results(self, results: dict):
        """Display extraction results."""
        self.data = results
        
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        if not results or all(len(v) == 0 for v in results.values()):
            self._show_empty_message()
            return
        
        # Create header row
        header_row = ctk.CTkFrame(self.table_frame, fg_color=("blue", "darkblue"))
        header_row.pack(fill="x", pady=(0, 2))
        
        for field_name in results.keys():
            ctk.CTkLabel(
                header_row,
                text=field_name,
                font=ctk.CTkFont(weight="bold"),
                text_color="white",
                width=150
            ).pack(side="left", padx=5, pady=5)
        
        # Find max rows
        max_rows = max(len(v) for v in results.values()) if results else 0
        
        # Create data rows
        for i in range(max_rows):
            row_color = ("gray90", "gray30") if i % 2 == 0 else ("gray85", "gray25")
            row = ctk.CTkFrame(self.table_frame, fg_color=row_color)
            row.pack(fill="x", pady=1)
            
            for field_name, values in results.items():
                value = values[i] if i < len(values) else ""
                ctk.CTkLabel(
                    row,
                    text=value,
                    width=150
                ).pack(side="left", padx=5, pady=5)
    
    def get_data(self) -> dict:
        """Get the current data."""
        return self.data.copy()
    
    def clear(self):
        """Clear results."""
        self.data = {}
        self._show_empty_message()
