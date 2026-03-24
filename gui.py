import os
import csv
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from makeModelClassificationDataOps import DataFolderAnalyzer


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None

        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tipwindow or not self.text:
            return

        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 10
        y = self.widget.winfo_rooty() + 8

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#111827",
            foreground="#f8fafc",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=4
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class FolderAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Klasör Analiz Aracı")
        self.root.geometry("1250x780")
        self.root.minsize(1050, 700)

        self.selected_folder = ""
        self.last_result = None

        self.sidebar_expanded = True
        self.sidebar_expanded_width = 240
        self.sidebar_collapsed_width = 78

        self.current_active = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.colors = {
            "bg_sidebar": "#111827",
            "bg_main": "#0f172a",
            "surface": "#1e293b",
            "surface_2": "#243041",
            "surface_3": "#2b3648",
            "border": "#334155",
            "text": "#f8fafc",
            "text_muted": "#94a3b8",
            "primary": "#1d4ed8",
            "primary_hover": "#2563eb",
            "accent": "#f59e0b",
            "accent_hover": "#fbbf24",
            "danger": "#b91c1c",
            "danger_hover": "#dc2626",
            "success": "#166534",
            "warning": "#92400e",
            "info": "#0f3d73",
            "purple": "#4c1d95",
        }

        self.is_busy = False
        self.search_var = tk.StringVar()
        self.current_filtered_data = []

        self.sort_column = None
        self.sort_reverse = False

        self.build_ui()

    def build_ui(self):
        self.root.configure(fg_color=self.colors["bg_main"])

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0, minsize=self.sidebar_expanded_width)
        self.root.grid_columnconfigure(1, weight=1)

        # ================= SIDEBAR =================
        self.sidebar_frame = ctk.CTkFrame(
            self.root,
            width=self.sidebar_expanded_width,
            corner_radius=0,
            fg_color=self.colors["bg_sidebar"]
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(1, weight=0)
        self.sidebar_frame.grid_rowconfigure(12, weight=1)

        # ================= MAIN =================
        self.main_frame = ctk.CTkFrame(
            self.root,
            corner_radius=18,
            fg_color=self.colors["bg_main"]
        )
        self.main_frame.grid(row=0, column=1, padx=(0, 18), pady=18, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_rowconfigure(4, weight=0)
        self.main_frame.grid_rowconfigure(5, weight=3)
        self.main_frame.grid_rowconfigure(6, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ================= SIDEBAR HEADER =================
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="🧠 Analyzer",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=24, pady=(24, 8), sticky="w")

        self.toggle_button = ctk.CTkButton(
            self.sidebar_frame,
            text="☰",
            width=40,
            height=40,
            command=self.toggle_sidebar,
            corner_radius=10,
            fg_color=self.colors["surface_2"],
            hover_color=self.colors["surface_3"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
            cursor="hand2"
        )
        self.toggle_button.grid(row=0, column=1, padx=14, pady=(24, 8), sticky="e")

        self.sidebar_subtitle = ctk.CTkLabel(
            self.sidebar_frame,
            text="Klasör analiz ve yönetim paneli",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        self.sidebar_subtitle.grid(row=1, column=0, padx=24, pady=(0, 20), sticky="w")

        self.nav_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="MENÜ",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.nav_title.grid(row=2, column=0, padx=24, pady=(10, 8), sticky="w")

        button_style = {
            "height": 42,
            "corner_radius": 12,
            "anchor": "w",
            "font": ctk.CTkFont(size=13, weight="bold"),
            "fg_color": self.colors["surface_2"],
            "hover_color": self.colors["surface_3"],
            "text_color": self.colors["text"],
            "border_width": 1,
            "border_color": self.colors["border"],
            "cursor": "hand2"
        }

        self.sidebar_select_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="📂 Klasör Seç",
            command=self.select_folder,
            **button_style
        )
        self.sidebar_select_btn.grid(row=3, column=0, columnspan=2, padx=14, pady=6, sticky="ew")

        self.sidebar_analyze_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🔍 Analiz Et",
            command=self.analyze_selected_folder,
            **button_style
        )
        self.sidebar_analyze_btn.grid(row=4, column=0, columnspan=2, padx=14, pady=6, sticky="ew")

        self.sidebar_open_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="📁 Seçiliyi Aç",
            command=self.open_selected_folder,
            **button_style
        )
        self.sidebar_open_btn.grid(row=5, column=0, columnspan=2, padx=14, pady=6, sticky="ew")

        self.sidebar_move_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🚚 Klasörü Taşı",
            command=self.move_selected_folder,
            **button_style
        )
        self.sidebar_move_btn.grid(row=6, column=0, columnspan=2, padx=14, pady=6, sticky="ew")

        self.export_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="DIŞA AKTAR",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.export_title.grid(row=7, column=0, padx=24, pady=(18, 8), sticky="w")

        self.sidebar_csv_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🧾 CSV Kaydet",
            command=self.export_to_csv,
            **button_style
        )
        self.sidebar_csv_btn.grid(row=8, column=0, columnspan=2, padx=14, pady=6, sticky="ew")

        self.sidebar_excel_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="📊 Excel Kaydet",
            command=self.export_to_excel,
            **button_style
        )
        self.sidebar_excel_btn.grid(row=9, column=0, columnspan=2, padx=14, pady=6, sticky="ew")

        self.actions_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="İŞLEMLER",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.actions_title.grid(row=10, column=0, padx=24, pady=(18, 8), sticky="w")

        self.sidebar_clear_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🧹 Tablo Temizle",
            command=self.clear_list,
            height=42,
            anchor="w",
            corner_radius=12,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3b1f24",
            hover_color="#4a2329",
            text_color=self.colors["text"],
            border_width=1,
            border_color="#6b2c35",
            cursor="hand2"
        )
        self.sidebar_clear_btn.grid(row=11, column=0, columnspan=2, padx=14, pady=6, sticky="ew")

        self.sidebar_info = ctk.CTkLabel(
            self.sidebar_frame,
            text="Beklemede\nBir klasör seçip analize başlayabilirsin.",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        self.sidebar_info.grid(row=12, column=0, padx=24, pady=(20, 24), sticky="sw")

        # ================= HEADER =================
        self.header_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=16,
            fg_color=self.colors["surface"]
        )
        self.header_frame.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🗂️ Klasör Analiz Aracı",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=18, pady=(14, 4), sticky="w")

        self.desc_label = ctk.CTkLabel(
            self.header_frame,
            text="Veri klasörlerini analiz et, kategorilere ayır, filtrele ve dışa aktar.",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=13)
        )
        self.desc_label.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="w")

        self.status_badge = ctk.CTkLabel(
            self.header_frame,
            text="Beklemede",
            width=120,
            corner_radius=12,
            fg_color="#1e293b",
            text_color="#e2e8f0",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.status_badge.grid(row=0, column=1, padx=(8, 18), pady=(14, 6), sticky="e")

        self.refresh_button = ctk.CTkButton(
            self.header_frame,
            text="↻",
            width=36,
            height=36,
            command=self.refresh_analysis,
            corner_radius=10,
            fg_color=self.colors["surface_2"],
            hover_color=self.colors["surface_3"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
            font=ctk.CTkFont(size=16, weight="bold"),
            cursor="hand2"
        )
        self.refresh_button.grid(row=1, column=1, padx=(8, 18), pady=(0, 14), sticky="e")

        self.progress = ctk.CTkProgressBar(
            self.header_frame,
            height=8,
            corner_radius=999,
            progress_color=self.colors["accent"],
            fg_color=self.colors["surface_2"]
        )
        self.progress.grid(row=2, column=0, columnspan=2, padx=18, pady=(0, 14), sticky="ew")
        self.progress.set(0)
        self.progress.grid_remove()

        # ================= PATH =================
        self.path_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=16,
            fg_color=self.colors["surface"]
        )
        self.path_frame.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)

        self.path_title = ctk.CTkLabel(
            self.path_frame,
            text="Seçilen Klasör",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_title.grid(row=0, column=0, padx=16, pady=(10, 2), sticky="w")

        self.folder_info_var = tk.StringVar(value="Henüz klasör seçilmedi.")
        self.folder_info_label = ctk.CTkLabel(
            self.path_frame,
            textvariable=self.folder_info_var,
            text_color=self.colors["text_muted"],
            anchor="w",
            justify="left",
            wraplength=1100,
            font=ctk.CTkFont(size=12)
        )
        self.folder_info_label.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")

        # ===== ANALİZ MODU =====
        self.analysis_mode_label = ctk.CTkLabel(
            self.path_frame,
            text="Analiz Modu",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.analysis_mode_label.grid(row=2, column=0, padx=16, pady=(4, 2), sticky="w")

        self.analysis_mode_row = ctk.CTkFrame(
            self.path_frame,
            fg_color="transparent"
        )
        self.analysis_mode_row.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="w")

        self.analysis_mode = ctk.CTkSegmentedButton(
            self.analysis_mode_row,
            values=["Standart", "Recursive"],
            fg_color=self.colors["surface_2"],
            selected_color=self.colors["accent"],
            selected_hover_color=self.colors["accent_hover"],
            unselected_color=self.colors["surface_2"],
            unselected_hover_color=self.colors["surface_3"],
            text_color="#111827",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=220
        )
        self.analysis_mode.pack(side="left")
        self.analysis_mode.set("Recursive")
        self.analysis_mode.configure(command=self.on_analysis_mode_change)

        self.analysis_mode_info = ctk.CTkLabel(
            self.analysis_mode_row,
            text="Seçilen klasörün alt klasörleri dahil tüm içeriğini gösterir.",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        self.analysis_mode_info.pack(side="left", padx=(12, 0))

        # ================= STATS =================
        self.stats_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=16,
            fg_color=self.colors["bg_main"]
        )
        self.stats_frame.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="ew")

        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1)

        self.total_folders_card = ctk.CTkFrame(
            self.stats_frame,
            corner_radius=14,
            fg_color="#1f2937",
            border_width=1,
            border_color="#334155"
        )
        self.total_folders_card.grid(row=0, column=0, padx=8, pady=10, sticky="ew")

        self.total_images_card = ctk.CTkFrame(
            self.stats_frame,
            corner_radius=14,
            fg_color="#1f2937",
            border_width=1,
            border_color="#334155"
        )
        self.total_images_card.grid(row=0, column=1, padx=8, pady=10, sticky="ew")

        self.low_count_card = ctk.CTkFrame(
            self.stats_frame,
            corner_radius=14,
            fg_color="#1f2937",
            border_width=1,
            border_color="#4b5563"
        )
        self.low_count_card.grid(row=0, column=2, padx=8, pady=10, sticky="ew")

        self.high_count_card = ctk.CTkFrame(
            self.stats_frame,
            corner_radius=14,
            fg_color="#1f2937",
            border_width=1,
            border_color="#4b5563"
        )
        self.high_count_card.grid(row=0, column=3, padx=8, pady=10, sticky="ew")

        self.bind_card_hover(self.total_folders_card, "#1f2937", "#273449")
        self.bind_card_hover(self.total_images_card, "#1f2937", "#2d304a")
        self.bind_card_hover(self.low_count_card, "#1f2937", "#3a2a2a")
        self.bind_card_hover(self.high_count_card, "#1f2937", "#23352d")

        self.total_folders_title = ctk.CTkLabel(
            self.total_folders_card,
            text="📁 Toplam Klasör",
            text_color="#93c5fd",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.total_folders_title.pack(anchor="w", padx=14, pady=(10, 2))

        self.total_folders_value = ctk.CTkLabel(
            self.total_folders_card,
            text="0",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.total_folders_value.pack(anchor="w", padx=14, pady=(0, 10))

        self.total_images_title = ctk.CTkLabel(
            self.total_images_card,
            text="🖼️ Toplam Görüntü",
            text_color="#c4b5fd",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.total_images_title.pack(anchor="w", padx=14, pady=(10, 2))

        self.total_images_value = ctk.CTkLabel(
            self.total_images_card,
            text="0",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.total_images_value.pack(anchor="w", padx=14, pady=(0, 10))

        self.low_count_title = ctk.CTkLabel(
            self.low_count_card,
            text="🔴 0-5 Kategorisi",
            text_color="#fca5a5",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.low_count_title.pack(anchor="w", padx=14, pady=(10, 2))

        self.low_count_value = ctk.CTkLabel(
            self.low_count_card,
            text="0",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.low_count_value.pack(anchor="w", padx=14, pady=(0, 10))

        self.high_count_title = ctk.CTkLabel(
            self.high_count_card,
            text="🟢 50+ Kategorisi",
            text_color="#86efac",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.high_count_title.pack(anchor="w", padx=14, pady=(10, 2))

        self.high_count_value = ctk.CTkLabel(
            self.high_count_card,
            text="0",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.high_count_value.pack(anchor="w", padx=14, pady=(0, 10))

        # ================= FILTER =================
        self.filter_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=16,
            fg_color=self.colors["surface"]
        )
        self.filter_frame.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.filter_frame.grid_columnconfigure(2, weight=1)

        self.filter_label = ctk.CTkLabel(
            self.filter_frame,
            text="Kategori Filtresi",
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.filter_label.grid(row=0, column=0, padx=(16, 10), pady=12, sticky="w")

        self.filter_segmented = ctk.CTkSegmentedButton(
            self.filter_frame,
            values=["Tümü", "0-5", "6-25", "26-50", "50+"],
            command=self.on_filter_change,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors["surface_2"],
            selected_color=self.colors["accent"],
            selected_hover_color=self.colors["accent_hover"],
            unselected_color=self.colors["surface_2"],
            unselected_hover_color=self.colors["surface_3"],
            text_color="#111827",
            text_color_disabled=self.colors["text_muted"]
        )
        self.filter_segmented.grid(row=0, column=1, padx=10, pady=12, sticky="w")
        self.filter_segmented.set("Tümü")

        self.search_container = ctk.CTkFrame(
            self.filter_frame,
            fg_color="transparent"
        )
        self.search_container.grid(row=0, column=2, padx=(10, 16), pady=12, sticky="e")

        self.search_label = ctk.CTkLabel(
            self.search_container,
            text="🔎 Arama",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.search_label.pack(side="left", padx=(0, 6))

        self.search_entry = ctk.CTkEntry(
            self.search_container,
            textvariable=self.search_var,
            placeholder_text="Klasör ara...",
            width=220,
            height=36,
            corner_radius=10,
            fg_color=self.colors["surface_2"],
            border_color=self.colors["border"],
            text_color=self.colors["text"]
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        self.search_entry.bind(
            "<FocusIn>",
            lambda e: self.search_entry.configure(border_color=self.colors["accent"])
        )
        self.search_entry.bind(
            "<FocusOut>",
            lambda e: self.search_entry.configure(border_color=self.colors["border"])
        )

        self.search_clear_btn = ctk.CTkButton(
            self.search_container,
            text="✕",
            width=30,
            height=30,
            corner_radius=8,
            fg_color=self.colors["surface_2"],
            hover_color="#7f1d1d",
            text_color=self.colors["text_muted"],
            border_width=1,
            border_color=self.colors["border"],
            command=self.clear_search,
            cursor="hand2"
        )
        self.search_clear_btn.pack(side="left", padx=(6, 0))

        # ================= TABLE CARD =================
        self.table_card = ctk.CTkFrame(
            self.main_frame,
            corner_radius=16,
            fg_color=self.colors["surface"]
        )
        self.table_card.grid(row=5, column=0, padx=16, pady=(0, 8), sticky="nsew")
        self.table_card.grid_rowconfigure(1, weight=1)
        self.table_card.grid_columnconfigure(0, weight=1)

        self.summary_var = tk.StringVar(value="Durum: Beklemede")
        self.summary_label = ctk.CTkLabel(
            self.table_card,
            textvariable=self.summary_var,
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.summary_label.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        self.table_frame = tk.Frame(
            self.table_card,
            bg="#1e293b",
            bd=0,
            highlightthickness=0
        )
        self.table_frame.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="nsew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#1e293b",
            foreground="white",
            fieldbackground="#1e293b",
            rowheight=36,
            font=("Segoe UI", 10),
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background="#243041",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        style.map(
            "Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "white")]
        )

        style.map(
            "Treeview.Heading",
            background=[("active", "#2b3648"), ("pressed", "#243041")],
            foreground=[("active", "white"), ("pressed", "white")]
        )

        self.tree = ttk.Treeview(
            self.table_frame,
            columns=("folder", "count", "category"),
            show="headings"
        )

        self.tree.heading("folder", text="Klasör", command=lambda: self.sort_treeview("folder"))
        self.tree.heading("count", text="Görüntü Sayısı", command=lambda: self.sort_treeview("count"))
        self.tree.heading("category", text="Kategori", command=lambda: self.sort_treeview("category"))

        self.tree.column("folder", width=700, anchor="w")
        self.tree.column("count", width=170, anchor="center")
        self.tree.column("category", width=170, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(
            self.table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.bind("<Double-1>", self.open_selected_folder)
        self.tree.bind("<Motion>", self.update_tree_cursor)
        self.tree.bind("<Leave>", lambda e: self.tree.configure(cursor=""))

        self.empty_placeholder = ctk.CTkLabel(
            self.table_card,
            text="Henüz analiz sonucu yok.\nBir klasör seçip analiz başlatabilirsin.",
            text_color=self.colors["text_muted"],
            font=ctk.CTkFont(size=15, weight="bold"),
            justify="center"
        )
        self.empty_placeholder.grid(row=1, column=0, sticky="")

        # ================= TOOLTIPS =================
        self.sidebar_select_tooltip = ToolTip(self.sidebar_select_btn, "Klasör Seç")
        self.sidebar_analyze_tooltip = ToolTip(self.sidebar_analyze_btn, "Analiz Et")
        self.sidebar_open_tooltip = ToolTip(self.sidebar_open_btn, "Seçiliyi Aç")
        self.sidebar_move_tooltip = ToolTip(self.sidebar_move_btn, "Klasörü Taşı")
        self.sidebar_csv_tooltip = ToolTip(self.sidebar_csv_btn, "CSV Kaydet")
        self.sidebar_excel_tooltip = ToolTip(self.sidebar_excel_btn, "Excel Kaydet")
        self.sidebar_clear_tooltip = ToolTip(self.sidebar_clear_btn, "Tablo Temizle")
        self.toggle_tooltip = ToolTip(self.toggle_button, "Sidebar Aç / Kapat")
        self.refresh_tooltip = ToolTip(self.refresh_button, "Analizi Yenile")

        self.refresh_button.bind(
            "<Enter>",
            lambda e: self.refresh_button.configure(border_color="#93c5fd")
        )
        self.refresh_button.bind(
            "<Leave>",
            lambda e: self.refresh_button.configure(border_color=self.colors["border"])
        )

        # ================= FOOTER =================
        self.footer_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=16,
            fg_color=self.colors["surface"]
        )
        self.footer_frame.grid(row=6, column=0, padx=16, pady=(0, 16), sticky="ew")
        self.footer_frame.grid_columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Uygulama başlatıldı.")
        self.status_label = ctk.CTkLabel(
            self.footer_frame,
            textvariable=self.status_var,
            text_color=self.colors["text_muted"],
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=16, pady=12, sticky="w")

        self.count_label = ctk.CTkLabel(
            self.footer_frame,
            text="0 kayıt",
            text_color=self.colors["text"]
        )
        self.count_label.grid(row=0, column=1, padx=16, pady=12, sticky="e")

        self.set_active_sidebar(None)
        self.set_sidebar_expanded_ui()

        buttons = [
            ("select", self.sidebar_select_btn, False),
            ("analyze", self.sidebar_analyze_btn, False),
            ("open", self.sidebar_open_btn, False),
            ("move", self.sidebar_move_btn, False),
            ("csv", self.sidebar_csv_btn, False),
            ("excel", self.sidebar_excel_btn, False),
            ("clear", self.sidebar_clear_btn, True),
        ]

        for name, btn, is_clear in buttons:
            self.bind_sidebar_button_hover(btn, name, is_clear=is_clear)

        self.update_empty_state()

    # ================= YARDIMCI =================
    def bind_card_hover(self, widget, normal_color, hover_color):
        widget.bind("<Enter>", lambda e: widget.configure(fg_color=hover_color))
        widget.bind("<Leave>", lambda e: widget.configure(fg_color=normal_color))

    def set_status(self, text, badge_text=None):
        self.status_var.set(text)

        if badge_text:
            self.status_badge.configure(text=badge_text)

            badge_map = {
                "Beklemede": ("#1e293b", "#e2e8f0"),
                "Seçildi": ("#0f3d73", "#dbeafe"),
                "Analiz": ("#92400e", "#fef3c7"),
                "Tamamlandı": ("#166534", "#dcfce7"),
                "Filtre": ("#4c1d95", "#ede9fe"),
                "Kaydedildi": ("#166534", "#dcfce7"),
                "Açıldı": ("#0f3d73", "#dbeafe"),
                "Taşındı": ("#166534", "#dcfce7"),
                "Uyarı": ("#92400e", "#fef3c7"),
                "Hata": ("#7f1d1d", "#fee2e2"),
            }

            fg, text_color = badge_map.get(badge_text, ("#1e293b", "#e2e8f0"))
            self.status_badge.configure(fg_color=fg, text_color=text_color)

    def apply_button_style(self, button, state="normal", is_clear=False):
        if is_clear:
            if state == "active":
                button.configure(
                    fg_color=self.colors["danger_hover"],
                    hover_color=self.colors["danger_hover"],
                    text_color="white",
                    border_width=1,
                    border_color="#fecaca"
                )
            elif state == "hover":
                button.configure(
                    fg_color="#7f1d1d",
                    hover_color="#7f1d1d",
                    text_color="white",
                    border_width=1,
                    border_color="#fca5a5"
                )
            else:
                button.configure(
                    fg_color="#3b1f24",
                    hover_color="#4a2329",
                    text_color=self.colors["text"],
                    border_width=1,
                    border_color="#6b2c35"
                )
            return

        if state == "active":
            button.configure(
                fg_color=self.colors["accent"],
                hover_color=self.colors["accent"],
                text_color="#111827",
                border_width=1,
                border_color="#fde68a"
            )
        elif state == "hover":
            button.configure(
                fg_color=self.colors["primary_hover"],
                hover_color=self.colors["primary_hover"],
                text_color="white",
                border_width=1,
                border_color="#93c5fd"
            )
        else:
            button.configure(
                fg_color=self.colors["surface_2"],
                hover_color=self.colors["surface_3"],
                text_color=self.colors["text"],
                border_width=1,
                border_color=self.colors["border"]
            )

    def bind_sidebar_button_hover(self, button, name, is_clear=False):
        def on_enter(event):
            if self.current_active == name:
                return
            self.apply_button_style(button, state="hover", is_clear=is_clear)

        def on_leave(event):
            if self.current_active == name:
                return
            self.apply_button_style(button, state="normal", is_clear=is_clear)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def populate_tree(self, folder_details):
        for row in self.tree.get_children():
            self.tree.delete(row)

        sorted_folders = self.get_sorted_filtered_data(folder_details)
        self.current_filtered_data = sorted_folders

        for index, item in enumerate(sorted_folders):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(item["folder"], item["count"], item["category"]),
                tags=(tag,)
            )

        self.tree.tag_configure("evenrow", background="#1e293b")
        self.tree.tag_configure("oddrow", background="#223046")

        self.count_label.configure(text=f"{len(sorted_folders)} kayıt")
        self.update_tree_headings()
        self.update_empty_state()

    def get_selected_tree_item(self):
        selected_item = self.tree.focus()

        if not selected_item:
            messagebox.showinfo("Bilgi", "Lütfen önce tablodan bir klasör seç.")
            return None

        values = self.tree.item(selected_item, "values")

        if not values:
            return None

        return values

    def refresh_analysis(self):
        if self.is_busy:
            return

        if not self.selected_folder:
            messagebox.showinfo("Bilgi", "Önce bir klasör seçmelisin.")
            self.set_status("Yenileme başlatılamadı.", "Uyarı")
            return

        try:
            self.set_busy_state(True, "Analiz yenileniyor...")
            self.root.update_idletasks()

            mode = self.analysis_mode.get()
            analyzer = DataFolderAnalyzer(self.selected_folder, mode=mode)
            result = analyzer.analyze()
            self.show_result(result)

            self.set_status("Analiz yenilendi.", "Tamamlandı")

        except Exception as error:
            messagebox.showerror("Hata", f"Analiz yenilenemedi:\n{error}")
            self.set_status("Yenileme başarısız.", "Hata")

        finally:
            self.set_busy_state(False)

    # ================= TEMEL İŞLEMLER =================
    def select_folder(self):
        self.flash_sidebar_action("select")
        selected = filedialog.askdirectory()

        if selected:
            self.selected_folder = selected
            self.folder_info_var.set(selected)
            self.set_status("Klasör seçildi.", "Seçildi")
        else:
            self.set_status("Klasör seçme işlemi iptal edildi.", "Beklemede")

    def analyze_selected_folder(self):
        if self.is_busy:
            return

        self.flash_sidebar_action("analyze")

        if not self.selected_folder:
            messagebox.showwarning("Uyarı", "Önce bir klasör seçmelisin.")
            self.set_status("Analiz başlatılamadı.", "Uyarı")
            return

        try:
            self.set_busy_state(True, "Analiz başlatıldı...")
            self.root.update_idletasks()

            mode = self.analysis_mode.get()
            analyzer = DataFolderAnalyzer(self.selected_folder, mode=mode)
            result = analyzer.analyze()

            self.show_result(result)
            self.set_status("Analiz tamamlandı.", "Tamamlandı")

        except Exception as error:
            messagebox.showerror("Hata", str(error))
            self.set_status(f"Hata oluştu: {error}", "Hata")

        finally:
            self.set_busy_state(False)

    def show_result(self, result):
        self.last_result = result
        self.sort_column = "count"
        self.sort_reverse = True
        categories, folder_details, total_images, total_folders = result

        self.total_folders_value.configure(text=str(total_folders))
        self.total_images_value.configure(text=str(total_images))
        self.low_count_value.configure(text=str(categories["0-5"]))
        self.high_count_value.configure(text=str(categories["50+"]))

        self.search_var.set("")
        self.filter_segmented.set("Tümü")

        self.populate_tree(folder_details)

        self.summary_var.set(
            f"{total_folders} klasör | {total_images} görüntü | "
            f"0-5: {categories['0-5']} | "
            f"6-25: {categories['6-25']} | "
            f"26-50: {categories['26-50']} | "
            f"50+: {categories['50+']}"
        )

        self.update_empty_state()

    def clear_list(self):
        self.flash_sidebar_action("clear")

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.last_result = None
        self.current_filtered_data = []
        self.search_var.set("")
        self.sort_column = None
        self.sort_reverse = False
        self.summary_var.set("Durum: Tablo temizlendi")
        self.count_label.configure(text="0 kayıt")
        self.filter_segmented.set("Tümü")
        self.set_status("Tablo temizlendi.", "Beklemede")

        self.total_folders_value.configure(text="0")
        self.total_images_value.configure(text="0")
        self.low_count_value.configure(text="0")
        self.high_count_value.configure(text="0")

        self.update_tree_headings()
        self.update_empty_state()

    # ================= FİLTRE =================
    def on_filter_change(self, value):
        self.apply_filters()

    # ================= KLASÖR AÇ =================
    def open_selected_folder(self, event=None):
        self.flash_sidebar_action("open")

        if not self.selected_folder:
            messagebox.showinfo("Bilgi", "Önce analiz yapılmış bir klasör seçmelisin.")
            return

        selected_values = self.get_selected_tree_item()
        if not selected_values:
            return

        folder_name = selected_values[0]
        folder_path = os.path.join(self.selected_folder, folder_name)

        if not os.path.exists(folder_path):
            messagebox.showerror("Hata", f"Klasör bulunamadı:\n{folder_path}")
            return

        try:
            os.startfile(folder_path)
            self.set_status(f"Klasör açıldı: {folder_name}", "Açıldı")
        except Exception as error:
            messagebox.showerror("Hata", f"Klasör açılamadı:\n{error}")

    # ================= CSV =================
    def export_to_csv(self):
        self.flash_sidebar_action("csv")

        if not self.last_result:
            messagebox.showinfo("Bilgi", "Önce analiz yapmalısın.")
            return

        categories, folder_details, total_images, total_folders = self.last_result
        # filtrelenmiş veri varsa onu kullan
        if self.current_filtered_data:
            folder_details = self.current_filtered_data
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyası", "*.csv")],
            title="CSV olarak kaydet"
        )

        if not file_path:
            self.set_status("CSV kaydetme iptal edildi.", "Beklemede")
            return

        try:
            sorted_folders = sorted(folder_details, key=lambda x: x["count"], reverse=True)

            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")

                writer.writerow(["Sıra No", "Klasör", "Görüntü Sayısı", "Kategori", "Tam Yol"])

                for index, item in enumerate(sorted_folders, start=1):
                    writer.writerow([
                        index,
                        item["folder"],
                        item["count"],
                        item["category"],
                        item["path"]
                    ])

            self.set_status(f"CSV kaydedildi: {os.path.basename(file_path)}", "Kaydedildi")
            messagebox.showinfo("Başarılı", f"CSV başarıyla kaydedildi:\n{file_path}")

        except Exception as error:
            messagebox.showerror("Hata", f"CSV kaydedilemedi:\n{error}")
            self.set_status("CSV dışa aktarma başarısız.", "Hata")

    # ================= EXCEL =================
    def export_to_excel(self):
        self.flash_sidebar_action("excel")

        if not self.last_result:
            messagebox.showinfo("Bilgi", "Önce analiz yapmalısın.")
            return

        categories, folder_details, total_images, total_folders = self.last_result
        # filtrelenmiş veri varsa onu kullan
        if self.current_filtered_data:
            folder_details = self.current_filtered_data
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Dosyası", "*.xlsx")],
            title="Excel olarak kaydet"
        )

        if not file_path:
            self.set_status("Excel kaydetme iptal edildi.", "Beklemede")
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Analiz Sonucu"

            header_fill = PatternFill(fill_type="solid", start_color="2D2D2D", end_color="2D2D2D")
            header_font = Font(bold=True, color="FFFFFF")
            title_font = Font(size=14, bold=True)
            center_align = Alignment(horizontal="center", vertical="center")
            left_align = Alignment(horizontal="left", vertical="center")

            ws["A1"] = "Klasör Analiz Raporu"
            ws["A1"].font = title_font

            ws["A3"] = "Seçilen Klasör"
            ws["B3"] = self.selected_folder

            ws["A4"] = "Toplam Klasör"
            ws["B4"] = total_folders

            ws["A5"] = "Toplam Görüntü"
            ws["B5"] = total_images

            ws["D3"] = "Kategori"
            ws["E3"] = "Klasör Sayısı"

            for cell in ["D3", "E3"]:
                ws[cell].fill = header_fill
                ws[cell].font = header_font
                ws[cell].alignment = center_align

            ws["D4"] = "0-5"
            ws["E4"] = categories["0-5"]
            ws["D5"] = "6-25"
            ws["E5"] = categories["6-25"]
            ws["D6"] = "26-50"
            ws["E6"] = categories["26-50"]
            ws["D7"] = "50+"
            ws["E7"] = categories["50+"]

            start_row = 10
            headers = ["Sıra No", "Klasör", "Görüntü Sayısı", "Kategori", "Tam Yol"]

            for col_num, header in enumerate(headers, start=1):
                cell = ws.cell(row=start_row, column=col_num, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center_align

            sorted_folders = sorted(folder_details, key=lambda x: x["count"], reverse=True)

            for index, item in enumerate(sorted_folders, start=1):
                row = start_row + index
                ws.cell(row=row, column=1, value=index)
                ws.cell(row=row, column=2, value=item["folder"])
                ws.cell(row=row, column=3, value=item["count"])
                ws.cell(row=row, column=4, value=item["category"])
                ws.cell(row=row, column=5, value=item["path"])

                ws.cell(row=row, column=1).alignment = center_align
                ws.cell(row=row, column=3).alignment = center_align
                ws.cell(row=row, column=4).alignment = center_align
                ws.cell(row=row, column=2).alignment = left_align
                ws.cell(row=row, column=5).alignment = left_align

            ws.column_dimensions["A"].width = 10
            ws.column_dimensions["B"].width = 35
            ws.column_dimensions["C"].width = 16
            ws.column_dimensions["D"].width = 14
            ws.column_dimensions["E"].width = 70

            last_row = start_row + len(sorted_folders)
            ws.auto_filter.ref = f"A{start_row}:E{last_row}"

            ws.row_dimensions[1].height = 24
            ws.row_dimensions[start_row].height = 22

            wb.save(file_path)

            self.set_status(f"Excel kaydedildi: {os.path.basename(file_path)}", "Kaydedildi")
            messagebox.showinfo("Başarılı", f"Excel başarıyla kaydedildi:\n{file_path}")

        except Exception as error:
            messagebox.showerror("Hata", f"Excel kaydedilemedi:\n{error}")
            self.set_status("Excel dışa aktarma başarısız.", "Hata")

    # ================= TAŞIMA =================
    def move_selected_folder(self):
        self.flash_sidebar_action("move")

        if not self.selected_folder:
            messagebox.showinfo("Bilgi", "Önce analiz yapılmış bir klasör seçmelisin.")
            return

        selected_values = self.get_selected_tree_item()
        if not selected_values:
            return

        folder_name = selected_values[0]
        source_path = os.path.join(self.selected_folder, folder_name)

        if not os.path.exists(source_path):
            messagebox.showerror("Hata", f"Kaynak klasör bulunamadı:\n{source_path}")
            return

        target_directory = filedialog.askdirectory(title="Hedef klasörü seç")
        if not target_directory:
            self.set_status("Taşıma işlemi iptal edildi.", "Beklemede")
            return

        destination_path = os.path.join(target_directory, folder_name)

        if os.path.exists(destination_path):
            messagebox.showwarning(
                "Uyarı",
                f"Hedefte aynı isimde klasör zaten var:\n{destination_path}"
            )
            return

        confirm = messagebox.askyesno(
            "Onay",
            f"'{folder_name}' klasörü taşınsın mı?\n\n"
            f"Kaynak:\n{source_path}\n\n"
            f"Hedef:\n{destination_path}"
        )

        if not confirm:
            self.set_status("Taşıma işlemi iptal edildi.", "Beklemede")
            return

        try:
            shutil.move(source_path, destination_path)
            self.set_status(f"Klasör taşındı: {folder_name}", "Taşındı")
            self.refresh_analysis()
            messagebox.showinfo("Başarılı", f"Klasör taşındı:\n{folder_name}")

        except Exception as error:
            messagebox.showerror("Hata", f"Klasör taşınamadı:\n{error}")
            self.set_status("Taşıma işlemi başarısız.", "Hata")

    # ================= SIDEBAR STYLE =================
    def set_active_sidebar(self, active_name=None):
        self.current_active = active_name

        button_map = {
            "select": self.sidebar_select_btn,
            "analyze": self.sidebar_analyze_btn,
            "open": self.sidebar_open_btn,
            "move": self.sidebar_move_btn,
            "csv": self.sidebar_csv_btn,
            "excel": self.sidebar_excel_btn,
            "clear": self.sidebar_clear_btn,
        }

        for name, button in button_map.items():
            is_clear = (name == "clear")
            if name == active_name:
                self.apply_button_style(button, state="active", is_clear=is_clear)
            else:
                self.apply_button_style(button, state="normal", is_clear=is_clear)

            button.grid_configure(padx=14, pady=6)

    def reset_sidebar_highlight(self):
        self.set_active_sidebar(None)

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.set_sidebar_collapsed_ui()
            self.sidebar_frame.configure(width=self.sidebar_collapsed_width)
            self.root.grid_columnconfigure(0, minsize=self.sidebar_collapsed_width)
            self.toggle_button.configure(text="⮞")
            self.sidebar_expanded = False
        else:
            self.set_sidebar_expanded_ui()
            self.sidebar_frame.configure(width=self.sidebar_expanded_width)
            self.root.grid_columnconfigure(0, minsize=self.sidebar_expanded_width)
            self.toggle_button.configure(text="☰")
            self.sidebar_expanded = True

        self.root.update_idletasks()

    def set_sidebar_collapsed_ui(self):
        self.logo_label.configure(text="🧠")
        self.sidebar_subtitle.configure(text="")
        self.nav_title.configure(text="")
        self.export_title.configure(text="")
        self.actions_title.configure(text="")
        self.sidebar_info.configure(text="")

        self.sidebar_select_btn.configure(text="📂", anchor="center")
        self.sidebar_analyze_btn.configure(text="🔍", anchor="center")
        self.sidebar_open_btn.configure(text="📁", anchor="center")
        self.sidebar_move_btn.configure(text="🚚", anchor="center")
        self.sidebar_csv_btn.configure(text="🧾", anchor="center")
        self.sidebar_excel_btn.configure(text="📊", anchor="center")
        self.sidebar_clear_btn.configure(text="🧹", anchor="center")

    def set_sidebar_expanded_ui(self):
        self.logo_label.configure(text="🧠 Analyzer")
        self.sidebar_subtitle.configure(text="Klasör analiz ve yönetim paneli")
        self.nav_title.configure(text="MENÜ")
        self.export_title.configure(text="DIŞA AKTAR")
        self.actions_title.configure(text="İŞLEMLER")
        self.sidebar_info.configure(text="Beklemede\nBir klasör seçip analize başlayabilirsin.")

        self.sidebar_select_btn.configure(text="📂 Klasör Seç", anchor="w")
        self.sidebar_analyze_btn.configure(text="🔍 Analiz Et", anchor="w")
        self.sidebar_open_btn.configure(text="📁 Seçiliyi Aç", anchor="w")
        self.sidebar_move_btn.configure(text="🚚 Klasörü Taşı", anchor="w")
        self.sidebar_csv_btn.configure(text="🧾 CSV Kaydet", anchor="w")
        self.sidebar_excel_btn.configure(text="📊 Excel Kaydet", anchor="w")
        self.sidebar_clear_btn.configure(text="🧹 Tablo Temizle", anchor="w")

    def flash_sidebar_action(self, name, duration=220):
        self.set_active_sidebar(name)
        self.root.after(duration, self.reset_sidebar_highlight)

    def get_action_buttons(self):
        return [
            self.sidebar_select_btn,
            self.sidebar_analyze_btn,
            self.sidebar_open_btn,
            self.sidebar_move_btn,
            self.sidebar_csv_btn,
            self.sidebar_excel_btn,
            self.sidebar_clear_btn,
            self.refresh_button,
        ]

    def set_busy_state(self, busy=True, message="İşlem devam ediyor..."):
        self.is_busy = busy

        if busy:
            self.set_status(message, "Analiz")
            self.status_badge.configure(text="Yükleniyor...")
            self.root.configure(cursor="watch")
            self.start_progress(indeterminate=True)
        else:
            self.root.configure(cursor="")
            self.stop_progress()

            if self.status_badge.cget("text") == "Yükleniyor...":
                self.status_badge.configure(text="Tamamlandı")

        for btn in self.get_action_buttons():
            if busy:
                btn.configure(state="disabled")
            else:
                btn.configure(state="normal")

        if not busy:
            self.set_active_sidebar(None)

    def update_empty_state(self):
        has_rows = len(self.tree.get_children()) > 0

        if has_rows:
            self.empty_placeholder.grid_remove()
        else:
            self.empty_placeholder.grid()

    def apply_filters(self):
        if not self.last_result:
            self.populate_tree([])
            return

        categories, folder_details, total_images, total_folders = self.last_result

        selected_filter = self.filter_segmented.get()
        search_text = self.search_var.get().strip().lower()

        filtered = folder_details

        if selected_filter != "Tümü":
            filtered = [item for item in filtered if item["category"] == selected_filter]

        if search_text:
            filtered = [
                item for item in filtered
                if search_text in item["folder"].lower()
            ]

        self.populate_tree(filtered)

        if selected_filter != "Tümü" or search_text:
            status_text = f"Filtre uygulandı"
            if search_text:
                status_text += f" | Arama: {self.search_var.get().strip()}"
            self.set_status(status_text, "Filtre")

    def on_search_change(self, event=None):
        self.apply_filters()

    def start_progress(self, indeterminate=True):
        self.progress.grid()
        self.progress.set(0)

        if indeterminate:
            self.progress.start()
        else:
            self.progress.stop()

    def stop_progress(self):
        self.progress.stop()
        self.progress.set(1)
        self.root.after(180, self.progress.grid_remove)

    def set_progress_value(self, value):
        self.progress.grid()
        self.progress.stop()
        self.progress.set(value)

    def clear_search(self):
        self.search_var.set("")
        self.search_entry.focus_set()
        self.apply_filters()

    def sort_treeview(self, column):
        if not self.last_result:
            return

        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        self.apply_filters()

    def get_sorted_filtered_data(self, data):
        if not self.sort_column:
            return sorted(data, key=lambda x: x["count"], reverse=True)

        if self.sort_column == "folder":
            return sorted(
                data,
                key=lambda x: x["folder"].lower(),
                reverse=self.sort_reverse
            )

        if self.sort_column == "count":
            return sorted(
                data,
                key=lambda x: x["count"],
                reverse=self.sort_reverse
            )

        if self.sort_column == "category":
            order_map = {
                "0-5": 0,
                "6-25": 1,
                "26-50": 2,
                "50+": 3
            }
            return sorted(
                data,
                key=lambda x: order_map.get(x["category"], 999),
                reverse=self.sort_reverse
            )

        return data

    def update_tree_headings(self):
        folder_text = "Klasör"
        count_text = "Görüntü Sayısı"
        category_text = "Kategori"

        if self.sort_column == "folder":
            folder_text += " ↓" if self.sort_reverse else " ↑"
        elif self.sort_column == "count":
            count_text += " ↓" if self.sort_reverse else " ↑"
        elif self.sort_column == "category":
            category_text += " ↓" if self.sort_reverse else " ↑"

        self.tree.heading("folder", text=folder_text, command=lambda: self.sort_treeview("folder"))
        self.tree.heading("count", text=count_text, command=lambda: self.sort_treeview("count"))
        self.tree.heading("category", text=category_text, command=lambda: self.sort_treeview("category"))

    def update_tree_cursor(self, event):
        region = self.tree.identify_region(event.x, event.y)

        if region == "heading":
            self.tree.configure(cursor="hand2")
        else:
            self.tree.configure(cursor="")

    def on_analysis_mode_change(self, value):
        if value == "Standart":
            self.analysis_mode_info.configure(text="Sadece seçilen klasörün içindeki klasörleri sayar.")
        elif value == "Recursive":
            self.analysis_mode_info.configure(text="Seçilen klasörün alt klasörleri dahil tüm içeriğini sayar.")