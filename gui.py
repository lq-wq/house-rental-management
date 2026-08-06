"""房屋租赁管理系统 - 图形界面（v2.0 合并版）"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import Optional, List

from models import Property, Tenant, Lease, Payment, PAYMENT_FREQUENCIES, FREQUENCY_MONTHS, HOUSE_TYPES
from database import Database
from utils import (
    validate_phone, validate_email, validate_amount, validate_date,
    format_currency, get_status_color, get_today_str
)


# ==================== 颜色主题 ====================
class Theme:
    PRIMARY = "#2C3E50"
    PRIMARY_LIGHT = "#34495E"
    ACCENT = "#3498DB"
    ACCENT_LIGHT = "#5DADE2"
    SUCCESS = "#27AE60"
    SUCCESS_LIGHT = "#2ECC71"
    WARNING = "#F39C12"
    WARNING_LIGHT = "#F1C40F"
    DANGER = "#E74C3C"
    DANGER_LIGHT = "#EC7063"
    BG = "#F0F2F5"
    BG_DARK = "#E8ECF0"
    CARD = "#FFFFFF"
    TEXT = "#2C3E50"
    TEXT_SECONDARY = "#7F8C8D"
    BORDER = "#D5D8DC"
    HEADER_BG = "#2C3E50"
    HEADER_TEXT = "#FFFFFF"
    ROW_ALT = "#F8F9FA"


class RentalManagementApp:
    """房屋租赁管理系统主窗口"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("房屋租赁管理系统")
        self.root.geometry("1280x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg=Theme.BG)
        self.db = Database()

        self._setup_styles()
        self._create_header()
        self._create_notebook()
        self._create_status_bar()

        self.refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center_window()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=Theme.BG, font=("Microsoft YaHei", 10))

        style.configure("Treeview",
            background=Theme.CARD, foreground=Theme.TEXT, rowheight=30,
            fieldbackground=Theme.CARD, font=("Microsoft YaHei", 10), borderwidth=0)
        style.map("Treeview",
            background=[("selected", Theme.ACCENT)],
            foreground=[("selected", "white")])
        style.configure("Treeview.Heading",
            background=Theme.HEADER_BG, foreground=Theme.HEADER_TEXT,
            font=("Microsoft YaHei", 10, "bold"), borderwidth=0, relief="flat")
        style.map("Treeview.Heading",
            background=[("active", Theme.PRIMARY_LIGHT)])

        style.configure("TNotebook", background=Theme.BG, borderwidth=0)
        style.configure("TNotebook.Tab",
            background=Theme.CARD, foreground=Theme.TEXT,
            padding=[15, 8], font=("Microsoft YaHei", 10), borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", Theme.ACCENT)],
            foreground=[("selected", "white")])

        for name, bg, fg, active in [
            ("Primary.TButton", Theme.ACCENT, "white", Theme.ACCENT_LIGHT),
            ("Success.TButton", Theme.SUCCESS, "white", Theme.SUCCESS_LIGHT),
            ("Danger.TButton", Theme.DANGER, "white", Theme.DANGER_LIGHT),
        ]:
            style.configure(name, background=bg, foreground=fg,
                          font=("Microsoft YaHei", 10), padding=(15, 7), borderwidth=0)
            style.map(name, background=[("active", active), ("pressed", Theme.PRIMARY)])

        style.configure("Flat.TButton",
            background=Theme.CARD, foreground=Theme.TEXT,
            font=("Microsoft YaHei", 10), padding=(12, 7),
            borderwidth=1, relief="solid")
        style.map("Flat.TButton", background=[("active", Theme.BG)])

        style.configure("TCombobox", background=Theme.CARD, foreground=Theme.TEXT,
                       fieldbackground=Theme.CARD, arrowcolor=Theme.ACCENT, borderwidth=1)
        style.map("TCombobox", fieldbackground=[("readonly", Theme.CARD)])

        style.configure("TEntry", fieldbackground=Theme.CARD, foreground=Theme.TEXT, borderwidth=1)
        style.configure("TSpinbox", fieldbackground=Theme.CARD, foreground=Theme.TEXT)

    def _create_header(self):
        header = tk.Frame(self.root, bg=Theme.HEADER_BG, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="房屋租赁管理系统 - v2.0",
                font=("Microsoft YaHei", 18, "bold"),
                bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT, anchor="w"
        ).pack(side=tk.LEFT, padx=25, pady=12)
        self.header_time = tk.Label(header, font=("Microsoft YaHei", 10),
                                   bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT, anchor="e")
        self.header_time.pack(side=tk.RIGHT, padx=25, pady=15)
        self._update_header_time()

    def _update_header_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.header_time.config(text=now)
        self.root.after(1000, self._update_header_time)

    def _create_notebook(self):
        main_container = tk.Frame(self.root, bg=Theme.BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 0))
        self._create_仪表盘_tab()
        self._create_property_tab()
        # 合同管理标签页（合并了租客管理）
        self._create_contract_tab()
        self._create_payment_tab()

    def _create_status_bar(self):
        status_frame = tk.Frame(self.root, bg=Theme.BG_DARK, height=28)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        self.status_label = tk.Label(status_frame, text="就绪",
                                    font=("Microsoft YaHei", 9),
                                    bg=Theme.BG_DARK, fg=Theme.TEXT_SECONDARY, anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=15, pady=3)

    def set_status(self, message: str):
        self.status_label.config(text=message)

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ==================== 创建卡片工具 ====================

    def _create_card(self, parent, title, value, color=Theme.ACCENT, **kwargs):
        """创建统计卡片"""
        card = tk.Frame(parent, bg=Theme.CARD, highlightbackground=Theme.BORDER,
                       highlightthickness=1, **kwargs)
        color_bar = tk.Frame(card, bg=color, height=4)
        color_bar.pack(fill=tk.X)
        content = tk.Frame(card, bg=Theme.CARD)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(12, 15))

        # 存储 value_label 引用以便后续更新
        value_label = tk.Label(content, text=value,
                              font=("Microsoft YaHei", 22, "bold"),
                              bg=Theme.CARD, fg=color, anchor="w")
        value_label.pack(fill=tk.X)

        title_label = tk.Label(content, text=title,
                              font=("Microsoft YaHei", 9),
                              bg=Theme.CARD, fg=Theme.TEXT_SECONDARY, anchor="w")
        title_label.pack(fill=tk.X, pady=(2, 0))

        # 存引用
        card._value_label = value_label
        card._title_label = title_label
        card._color = color
        return card

    def _update_card(self, card, title, value, color):
        """更新卡片内容"""
        if hasattr(card, '_value_label'):
            card._value_label.config(text=value, fg=color)
        if hasattr(card, '_title_label'):
            card._title_label.config(text=title)
        card._color = color

    # ==================== 仪表盘 ====================

    def _create_dashboard_tab(self):
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="Dashboard")

        tk.Label(frame, text="系统概览",
                font=("Microsoft YaHei", 16, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(15, 5), padx=15)

        cards_frame = tk.Frame(frame, bg=Theme.BG)
        cards_frame.pack(fill=tk.X, padx=15, pady=5)

        self._stat_cards = {}
        stats_info = [
            ("total_properties", "总房源", "0", Theme.ACCENT),
            ("available_properties", "Available", "0", Theme.SUCCESS),
            ("rented_properties", "Rented", "0", Theme.PRIMARY),
            ("total_tenants", "Total Tenants", "0", Theme.ACCENT),
            ("active_leases", "Active Leases", "0", Theme.SUCCESS),
            ("monthly_income", "Monthly Income", "0.00", Theme.WARNING),
            ("total_income", "Total Income", "0.00", Theme.DANGER),
            ("overdue_payments", "Overdue", "0", Theme.DANGER),
        ]

        for i, (key, title, init_val, color) in enumerate(stats_info):
            card = self._create_card(cards_frame, title, init_val, color, width=150, height=95)
            card.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="nsew")
            cards_frame.columnconfigure(i%4, weight=1)
            self._stat_cards[key] = card

        # Payment reminders
        tk.Label(frame, text="Payment Reminders",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(20, 5), padx=15)

        self.reminder_frame = tk.Frame(frame, bg=Theme.BG)
        self.reminder_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self._refresh_reminders()

        # Quick actions
        tk.Label(frame, text="Quick Actions",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(15, 5), padx=15)

        btn_frame = tk.Frame(frame, bg=Theme.BG)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Button(btn_frame, text="+ Add Property", command=self._show_add_property,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="+ New Contract", command=self._show_add_lease,
                   style="Success.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Record Payment", command=self._show_add_payment,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_dashboard,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=3)

    def _refresh_reminders(self):
        for w in self.reminder_frame.winfo_children():
            w.destroy()

        leases = self.db.get_active_leases_with_reminders()
        reminders = []
        for lease in leases:
            days = lease.get_days_until_next_payment()
            next_date = lease.get_next_payment_date()
            amount = lease.get_payment_amount()
            if next_date:
                if days is None:
                    continue
                elif days < 0:
                    status_text = f"Overdue {-days} days"
                    color = Theme.DANGER
                elif days == 0:
                    status_text = "Due Today!"
                    color = Theme.WARNING
                elif days <= 3:
                    status_text = f"{days} days left"
                    color = Theme.WARNING
                elif days <= 7:
                    status_text = f"{days} days left"
                    color = Theme.ACCENT
                else:
                    continue
                reminders.append((days, lease, next_date, amount, status_text, color))

        if not reminders:
            if leases:
                tk.Label(self.reminder_frame, text="All payments are up to date",
                        font=("Microsoft YaHei", 11),
                        bg=Theme.BG, fg=Theme.SUCCESS).pack(anchor=tk.W, pady=10)
            else:
                tk.Label(self.reminder_frame, text="No active contracts",
                        font=("Microsoft YaHei", 11),
                        bg=Theme.BG, fg=Theme.TEXT_SECONDARY).pack(anchor=tk.W, pady=10)
            return

        reminders.sort(key=lambda x: x[0])
        for days, lease, next_date, amount, status_text, color in reminders[:6]:
            card = tk.Frame(self.reminder_frame, bg=Theme.CARD,
                          highlightbackground=color, highlightthickness=1, padx=15, pady=8)
            card.pack(fill=tk.X, pady=3)
            color_bar = tk.Frame(card, bg=color, width=4)
            color_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
            info_frame = tk.Frame(card, bg=Theme.CARD)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            top_row = tk.Frame(info_frame, bg=Theme.CARD)
            top_row.pack(fill=tk.X)
            tk.Label(top_row, text=f"{lease.property_name}",
                    font=("Microsoft YaHei", 11, "bold"),
                    bg=Theme.CARD, fg=Theme.PRIMARY).pack(side=tk.LEFT)
            tk.Label(top_row, text=f"  |  {lease.tenant_name}",
                    font=("Microsoft YaHei", 10),
                    bg=Theme.CARD, fg=Theme.TEXT_SECONDARY).pack(side=tk.LEFT)
            bottom_row = tk.Frame(info_frame, bg=Theme.CARD)
            bottom_row.pack(fill=tk.X, pady=(3, 0))
            tk.Label(bottom_row, text=f"Due: {next_date}  |  Amount: {format_currency(amount)}  |  {lease.payment_frequency}",
                    font=("Microsoft YaHei", 9),
                    bg=Theme.CARD, fg=Theme.TEXT_SECONDARY).pack(side=tk.LEFT)
            tk.Label(card, text=f" {status_text} ",
                    font=("Microsoft YaHei", 10, "bold"),
                    bg=color, fg="white", padx=10, pady=2).pack(side=tk.RIGHT)

    def _refresh_dashboard(self):
        stats = self.db.get_statistics()
        mapping = {
            "total_properties": ("总房源", str(stats.get("total_properties", 0)), Theme.ACCENT),
            "available_properties": ("Available", str(stats.get("available_properties", 0)), Theme.SUCCESS),
            "rented_properties": ("Rented", str(stats.get("rented_properties", 0)), Theme.PRIMARY),
            "total_tenants": ("Total Tenants", str(stats.get("total_tenants", 0)), Theme.ACCENT),
            "active_leases": ("Active Leases", str(stats.get("active_leases", 0)), Theme.SUCCESS),
            "monthly_income": ("Monthly Income", format_currency(stats.get("monthly_income", 0)), Theme.WARNING),
            "total_income": ("Total Income", format_currency(stats.get("total_income", 0)), Theme.DANGER),
            "overdue_payments": ("Overdue", str(stats.get("overdue_payments", 0)), Theme.DANGER),
        }
        for key, (title, value, color) in mapping.items():
            if key in self._stat_cards:
                self._update_card(self._stat_cards[key], title, value, color)
        self._refresh_reminders()
        self.set_status("Dashboard refreshed")

    # ==================== 房源管理（更新字段） ====================

    def _create_property_tab(self):
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="Properties")

        toolbar = tk.Frame(frame, bg=Theme.BG)
        toolbar.pack(fill=tk.X, pady=8, padx=10)

        ttk.Button(toolbar, text="+ Add Property", command=self._show_add_property,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit", command=self._edit_property,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete", command=self._delete_property,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self._refresh_property_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Search:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.prop_search_var = tk.StringVar()
        self.prop_search_var.trace("w", lambda *a: self._refresh_property_list())
        ttk.Entry(toolbar, textvariable=self.prop_search_var, width=20).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Status:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(10, 2))
        self.prop_status_var = tk.StringVar(value="All")
        combo = ttk.Combobox(toolbar, textvariable=self.prop_status_var,
                            values=["All", "Available", "Rented", "Off-market"],
                            state="readonly", width=8)
        combo.pack(side=tk.LEFT, padx=2)
        combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_property_list())

        table_frame = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "Community", "Address", "Bldg/Unit/Room", "Type", "Size", "Layout", "Rent", "Deposit", "Status")
        self.prop_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                      selectmode="browse", height=15)
        for col in columns:
            self.prop_tree.heading(col, text=col)
        self.prop_tree.column("id", width=40, anchor=tk.CENTER)
        self.prop_tree.column("Community", width=100)
        self.prop_tree.column("Address", width=150)
        self.prop_tree.column("Bldg/Unit/Room", width=120)
        self.prop_tree.column("Type", width=60, anchor=tk.CENTER)
        self.prop_tree.column("Size", width=60, anchor=tk.CENTER)
        self.prop_tree.column("Layout", width=100, anchor=tk.CENTER)
        self.prop_tree.column("Rent", width=100, anchor=tk.E)
        self.prop_tree.column("Deposit", width=100, anchor=tk.E)
        self.prop_tree.column("Status", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.prop_tree.yview)
        self.prop_tree.configure(yscrollcommand=scrollbar.set)
        self.prop_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.prop_tree.bind("<Double-1>", lambda e: self._edit_property())
        self.prop_tree.tag_configure("odd", background=Theme.ROW_ALT)
        self.prop_tree.tag_configure("even", background=Theme.CARD)

    def _refresh_property_list(self):
        for item in self.prop_tree.get_children():
            self.prop_tree.delete(item)
        keyword = self.prop_search_var.get().strip()
        status = self.prop_status_var.get()
        if status == "All":
            status = ""
        else:
            status_map = {"Available": "待出租", "Rented": "已出租", "Off-market": "已下架"}
            status = status_map.get(status, "")
        properties = self.db.search_properties(keyword, status)
        for i, prop in enumerate(properties):
            tag = "odd" if i % 2 == 1 else "even"
            self.prop_tree.insert("", tk.END, tags=(tag,), values=(
                prop.id, prop.community_name, prop.address,
                prop.building_unit_room, prop.property_type,
                f"{prop.area:.1f}", prop.house_type,
                format_currency(prop.monthly_rent),
                format_currency(prop.deposit), prop.status
            ))

    def _show_add_property(self):
        dialog = PropertyDialog(self.root, "Add Property")
        if dialog.result:
            prop_id = self.db.add_property(dialog.result)
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status(f"Property added (ID: {prop_id})")

    def _edit_property(self):
        selected = self.prop_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a property first")
            return
        values = self.prop_tree.item(selected[0])["values"]
        prop = self.db.get_property(values[0])
        if prop:
            dialog = PropertyDialog(self.root, "Edit Property", prop)
            if dialog.result:
                self.db.update_property(dialog.result)
                self._refresh_property_list()
                self._refresh_dashboard()
                self.set_status(f"Property updated (ID: {values[0]})")

    def _delete_property(self):
        selected = self.prop_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a property first")
            return
        values = self.prop_tree.item(selected[0])["values"]
        if messagebox.askyesno("Confirm Delete", f"Delete property '{values[1]}'?"):
            self.db.delete_property(values[0])
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status("Property deleted")

    # ==================== 合同管理（合并租客管理） ====================

    def _create_contract_tab(self):
        """合同管理标签页，包含租客管理"""
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="Contracts & Tenants")

        # 上部：合同列表
        tk.Label(frame, text="Contracts",
                font=("Microsoft YaHei", 13, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, padx=10, pady=(10, 0))

        toolbar = tk.Frame(frame, bg=Theme.BG)
        toolbar.pack(fill=tk.X, pady=5, padx=10)

        ttk.Button(toolbar, text="+ New Contract", command=self._show_add_lease,
                   style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="View Details", command=self._view_lease,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Terminate", command=self._terminate_lease,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Search:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.lease_search_var = tk.StringVar()
        self.lease_search_var.trace("w", lambda *a: self._refresh_lease_list())
        ttk.Entry(toolbar, textvariable=self.lease_search_var, width=15).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Status:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(10, 2))
        self.lease_status_var = tk.StringVar(value="All")
        lc = ttk.Combobox(toolbar, textvariable=self.lease_status_var,
                          values=["All", "Active", "Expired", "Terminated"],
                          state="readonly", width=8)
        lc.pack(side=tk.LEFT, padx=2)
        lc.bind("<<ComboboxSelected>>", lambda e: self._refresh_lease_list())

        ttk.Button(toolbar, text="Refresh", command=self._refresh_lease_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        table_frame = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)

        columns = ("id", "Property", "Tenant", "Start", "End", "Frequency", "Rent", "Deposit", "Status")
        self.lease_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                       selectmode="browse", height=6)
        for col in columns:
            self.lease_tree.heading(col, text=col)
        self.lease_tree.column("id", width=40, anchor=tk.CENTER)
        self.lease_tree.column("Property", width=120)
        self.lease_tree.column("Tenant", width=100)
        self.lease_tree.column("Start", width=90, anchor=tk.CENTER)
        self.lease_tree.column("End", width=90, anchor=tk.CENTER)
        self.lease_tree.column("Frequency", width=70, anchor=tk.CENTER)
        self.lease_tree.column("Rent", width=90, anchor=tk.E)
        self.lease_tree.column("Deposit", width=90, anchor=tk.E)
        self.lease_tree.column("Status", width=80, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.lease_tree.yview)
        self.lease_tree.configure(yscrollcommand=scrollbar.set)
        self.lease_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lease_tree.bind("<Double-1>", lambda e: self._view_lease())
        self.lease_tree.tag_configure("odd", background=Theme.ROW_ALT)
        self.lease_tree.tag_configure("even", background=Theme.CARD)

        # 分隔线
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # 下部：租客管理
        tk.Label(frame, text="Tenants",
                font=("Microsoft YaHei", 13, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, padx=10, pady=(5, 0))

        tenant_toolbar = tk.Frame(frame, bg=Theme.BG)
        tenant_toolbar.pack(fill=tk.X, pady=5, padx=10)

        ttk.Button(tenant_toolbar, text="+ Add Tenant", command=self._show_add_tenant,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(tenant_toolbar, text="Edit", command=self._edit_tenant,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(tenant_toolbar, text="Delete", command=self._delete_tenant,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(tenant_toolbar, text="Search:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.tenant_search_var = tk.StringVar()
        self.tenant_search_var.trace("w", lambda *a: self._refresh_tenant_list())
        ttk.Entry(tenant_toolbar, textvariable=self.tenant_search_var, width=15).pack(side=tk.LEFT, padx=2)

        ttk.Button(tenant_toolbar, text="Refresh", command=self._refresh_tenant_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        tenant_table = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        tenant_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 10))

        tcolumns = ("id", "Name", "Phone", "Email", "ID Card", "Emergency Contact", "Emergency Phone")
        self.tenant_tree = ttk.Treeview(tenant_table, columns=tcolumns, show="headings",
                                        selectmode="browse", height=5)
        for col in tcolumns:
            self.tenant_tree.heading(col, text=col)
        self.tenant_tree.column("id", width=40, anchor=tk.CENTER)
        self.tenant_tree.column("Name", width=80)
        self.tenant_tree.column("Phone", width=110)
        self.tenant_tree.column("Email", width=150)
        self.tenant_tree.column("ID Card", width=150)
        self.tenant_tree.column("Emergency Contact", width=100)
        self.tenant_tree.column("Emergency Phone", width=110)
        ts = ttk.Scrollbar(tenant_table, orient=tk.VERTICAL, command=self.tenant_tree.yview)
        self.tenant_tree.configure(yscrollcommand=ts.set)
        self.tenant_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ts.pack(side=tk.RIGHT, fill=tk.Y)
        self.tenant_tree.bind("<Double-1>", lambda e: self._edit_tenant())
        self.tenant_tree.tag_configure("odd", background=Theme.ROW_ALT)
        self.tenant_tree.tag_configure("even", background=Theme.CARD)

    def _refresh_lease_list(self):
        for item in self.lease_tree.get_children():
            self.lease_tree.delete(item)
        keyword = self.lease_search_var.get().strip()
        status = self.lease_status_var.get()
        sm = {"All": "", "Active": "生效中", "Expired": "已到期", "Terminated": "已解约"}
        status = sm.get(status, "")
        leases = self.db.search_leases(keyword, status)
        for i, lease in enumerate(leases):
            tag = "odd" if i % 2 == 1 else "even"
            self.lease_tree.insert("", tk.END, tags=(tag,), values=(
                lease.id, lease.property_name, lease.tenant_name,
                lease.start_date, lease.end_date, lease.payment_frequency,
                format_currency(lease.monthly_rent),
                format_currency(lease.deposit_amount), lease.status
            ))

    def _refresh_tenant_list(self):
        for item in self.tenant_tree.get_children():
            self.tenant_tree.delete(item)
        keyword = self.tenant_search_var.get().strip()
        tenants = self.db.search_tenants(keyword)
        for i, tenant in enumerate(tenants):
            tag = "odd" if i % 2 == 1 else "even"
            self.tenant_tree.insert("", tk.END, tags=(tag,), values=(
                tenant.id, tenant.name, tenant.phone, tenant.email,
                tenant.id_card, tenant.emergency_contact, tenant.emergency_phone
            ))

    def _show_add_lease(self):
        properties = self.db.get_all_properties()
        available_props = [p for p in properties if p.status == "待出租"]
        if not available_props:
            messagebox.showwarning("Warning", "No available properties. Please add one first.")
            return
        tenants = self.db.get_all_tenants()
        if not tenants:
            if messagebox.askyesno("No Tenants", "No tenants found. Add a tenant now?"):
                self._show_add_tenant()
                tenants = self.db.get_all_tenants()
                if not tenants:
                    return
            else:
                return
        dialog = LeaseDialog(self.root, "New Contract", available_props, tenants)
        if dialog.result:
            lease_id = self.db.add_lease(dialog.result)
            self._refresh_lease_list()
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status(f"Contract created (ID: {lease_id})")

    def _view_lease(self):
        selected = self.lease_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a contract")
            return
        values = self.lease_tree.item(selected[0])["values"]
        lease = self.db.get_lease(values[0])
        if lease:
            LeaseDetailDialog(self.root, lease)

    def _terminate_lease(self):
        selected = self.lease_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a contract")
            return
        values = self.lease_tree.item(selected[0])["values"]
        if values[8] != "生效中":
            messagebox.showinfo("Info", "Only active contracts can be terminated")
            return
        if messagebox.askyesno("Confirm", f"Terminate contract '{values[1]} - {values[2]}'?"):
            self.db.terminate_lease(values[0])
            self._refresh_lease_list()
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status("Contract terminated")

    def _show_add_tenant(self):
        dialog = TenantDialog(self.root, "Add Tenant")
        if dialog.result:
            tenant_id = self.db.add_tenant(dialog.result)
            self._refresh_tenant_list()
            self._refresh_dashboard()
            self.set_status(f"Tenant added (ID: {tenant_id})")

    def _edit_tenant(self):
        selected = self.tenant_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a tenant")
            return
        values = self.tenant_tree.item(selected[0])["values"]
        tenant = self.db.get_tenant(values[0])
        if tenant:
            dialog = TenantDialog(self.root, "Edit Tenant", tenant)
            if dialog.result:
                self.db.update_tenant(dialog.result)
                self._refresh_tenant_list()
                self.set_status(f"Tenant updated (ID: {values[0]})")

    def _delete_tenant(self):
        selected = self.tenant_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a tenant")
            return
        values = self.tenant_tree.item(selected[0])["values"]
        if messagebox.askyesno("Confirm Delete", f"Delete tenant '{values[1]}'?"):
            self.db.delete_tenant(values[0])
            self._refresh_tenant_list()
            self._refresh_dashboard()
            self.set_status("Tenant deleted")

    # ==================== 缴费管理（新增：下次缴费时间自动生成） ====================

    def _create_payment_tab(self):
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="Payments")

        toolbar = tk.Frame(frame, bg=Theme.BG)
        toolbar.pack(fill=tk.X, pady=8, padx=10)

        ttk.Button(toolbar, text="Record Payment", command=self._show_add_payment,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit", command=self._edit_payment,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete", command=self._delete_payment,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self._refresh_payment_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Search:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.pay_search_var = tk.StringVar()
        self.pay_search_var.trace("w", lambda *a: self._refresh_payment_list())
        ttk.Entry(toolbar, textvariable=self.pay_search_var, width=20).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Type:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(10, 2))
        self.pay_type_var = tk.StringVar(value="All")
        pc = ttk.Combobox(toolbar, textvariable=self.pay_type_var,
                          values=["All", "Rent", "Deposit", "Water", "Electricity", "Gas", "Property", "Other"],
                          state="readonly", width=8)
        pc.pack(side=tk.LEFT, padx=2)
        pc.bind("<<ComboboxSelected>>", lambda e: self._refresh_payment_list())

        table_frame = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "Tenant", "Property", "Amount", "Pay Date", "Next Due", "Type", "Method", "Status")
        self.pay_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.pay_tree.heading(col, text=col)
        self.pay_tree.column("id", width=40, anchor=tk.CENTER)
        self.pay_tree.column("Tenant", width=90)
        self.pay_tree.column("Property", width=110)
        self.pay_tree.column("Amount", width=90, anchor=tk.E)
        self.pay_tree.column("Pay Date", width=90, anchor=tk.CENTER)
        self.pay_tree.column("Next Due", width=90, anchor=tk.CENTER)
        self.pay_tree.column("Type", width=70, anchor=tk.CENTER)
        self.pay_tree.column("Method", width=90, anchor=tk.CENTER)
        self.pay_tree.column("Status", width=70, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.pay_tree.yview)
        self.pay_tree.configure(yscrollcommand=scrollbar.set)
        self.pay_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pay_tree.bind("<Double-1>", lambda e: self._edit_payment())
        self.pay_tree.tag_configure("odd", background=Theme.ROW_ALT)
        self.pay_tree.tag_configure("even", background=Theme.CARD)

    def _refresh_payment_list(self):
        for item in self.pay_tree.get_children():
            self.pay_tree.delete(item)
        keyword = self.pay_search_var.get().strip()
        pay_type = self.pay_type_var.get()
        if pay_type == "All":
            pay_type = ""
        else:
            pt_map = {"Rent": "租金", "Deposit": "押金", "Water": "水费", "Electricity": "电费",
                      "Gas": "燃气费", "Property": "物业费", "Other": "其他"}
            pay_type = pt_map.get(pay_type, "")
        payments = self.db.search_payments(keyword, payment_type=pay_type)
        for i, pay in enumerate(payments):
            tag = "odd" if i % 2 == 1 else "even"
            self.pay_tree.insert("", tk.END, tags=(tag,), values=(
                pay.id, pay.tenant_name, pay.property_name,
                format_currency(pay.amount), pay.payment_date,
                pay.next_payment_date or "-",
                pay.payment_type, pay.payment_method, pay.status
            ))

    def _show_add_payment(self):
        leases = self.db.search_leases(status="生效中")
        if not leases:
            messagebox.showwarning("Warning", "No active contracts found")
            return
        dialog = PaymentDialog(self.root, "Record Payment", leases)
        if dialog.result:
            # 自动生成下次缴费时间
            pay_id = self.db.add_payment(dialog.result)
            self._refresh_payment_list()
            self._refresh_dashboard()
            self.set_status(f"Payment recorded (ID: {pay_id})")

    def _edit_payment(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a payment record")
            return
        values = self.pay_tree.item(selected[0])["values"]
        payment = None
        for p in self.db.get_all_payments():
            if p.id == values[0]:
                payment = p
                break
        if payment:
            leases = self.db.search_leases(status="生效中")
            dialog = PaymentDialog(self.root, "Edit Payment", leases, payment)
            if dialog.result:
                self.db.update_payment(dialog.result)
                self._refresh_payment_list()
                self._refresh_dashboard()
                self.set_status("Payment updated")

    def _delete_payment(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a payment")
            return
        values = self.pay_tree.item(selected[0])["values"]
        if messagebox.askyesno("Confirm Delete", f"Delete payment {values[3]}?"):
            self.db.delete_payment(values[0])
            self._refresh_payment_list()
            self._refresh_dashboard()
            self.set_status("Payment deleted")

    # ==================== 工具方法 ====================

    def refresh_all(self):
        self._refresh_dashboard()
        self._refresh_property_list()
        self._refresh_lease_list()
        self._refresh_tenant_list()
        self._refresh_payment_list()
        self.set_status("All data refreshed")

    def _backup_db(self):
        import shutil
        from datetime import datetime
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy2("rental_management.db", backup_name)
            messagebox.showinfo("Backup", f"Database backed up to: {backup_name}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def _show_about(self):
        messagebox.showinfo("About",
            "House Rental Management System v2.0\n\n"
            "Features:\n"
            "  - Property management (add/edit/delete/search)\n"
            "  - Contract & Tenant management (merged)\n"
            "  - Payment records with auto-generated next due date\n"
            "  - Payment frequency: Monthly/Quarterly/Semi-Annual/Annual\n"
            "  - Dashboard with payment reminders\n"
            "  - Database backup\n\n"
            "Tech: Python + Tkinter + SQLite")

    def _on_close(self):
        if messagebox.askokcancel("Exit", "Exit the application?"):
            self.db.close()
            self.root.destroy()


# ==================== 对话框类 ====================

class PropertyDialog:
    """房源添加/编辑对话框（更新字段）"""

    def __init__(self, parent, title: str, prop: Optional[Property] = None):
        self.result: Optional[Property] = None
        self.prop = prop or Property()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("520x520")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Theme.CARD)

        self._create_widgets()
        self._load_data()
        parent.wait_window(self.dialog)

    def _create_widgets(self):
        main_frame = tk.Frame(self.dialog, bg=Theme.CARD, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Property Info",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 更新后的字段布局
        fields = [
            ("Community *", "community_name", 1),
            ("Address *", "address", 2),
            ("Bldg/Unit/Room", "building_unit_room", 3),  # 新增：栋/单元/号
            ("Type", "property_type", 4),
            ("Layout", "house_type", 5),                   # 新增：户型
            ("Area (sqm)", "area", 6),
            ("Monthly Rent *", "monthly_rent", 7),
            ("Deposit", "deposit", 8),
            ("Status", "status", 9),
        ]

        self.entries = {}
        for label, key, row in fields:
            tk.Label(main_frame, text=label,
                    font=("Microsoft YaHei", 10),
                    bg=Theme.CARD, fg=Theme.TEXT).grid(
                row=row, column=0, sticky=tk.W, pady=4, padx=(0, 10))
            if key in ("property_type", "status", "house_type"):
                values_map = {
                    "property_type": ["住宅", "商铺", "写字楼", "公寓"],
                    "status": ["待出租", "已出租", "已下架"],
                    "house_type": HOUSE_TYPES,
                }
                entry = ttk.Combobox(main_frame, values=values_map[key], state="readonly", width=32)
                entry.grid(row=row, column=1, sticky=tk.W, pady=4)
            else:
                entry = ttk.Entry(main_frame, width=35)
                entry.grid(row=row, column=1, sticky=tk.W, pady=4)
            self.entries[key] = entry

        # Description
        tk.Label(main_frame, text="Description",
                font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=10, column=0, sticky=tk.W, pady=4)
        self.desc_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.desc_text.grid(row=10, column=1, sticky=tk.W, pady=4)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="OK", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=8)

    def _load_data(self):
        if self.prop.id:
            self.entries["community_name"].insert(0, self.prop.community_name)
            self.entries["address"].insert(0, self.prop.address)
            self.entries["building_unit_room"].insert(0, self.prop.building_unit_room)
            self.entries["property_type"].set(self.prop.property_type)
            self.entries["house_type"].set(self.prop.house_type)
            self.entries["area"].insert(0, str(self.prop.area))
            self.entries["monthly_rent"].insert(0, str(self.prop.monthly_rent))
            self.entries["deposit"].insert(0, str(self.prop.deposit))
            self.entries["status"].set(self.prop.status)
            self.desc_text.insert("1.0", self.prop.description)

    def _confirm(self):
        data = {}
        for key, entry in self.entries.items():
            if isinstance(entry, ttk.Combobox):
                data[key] = entry.get()
            else:
                data[key] = entry.get().strip()

        if not data["community_name"]:
            messagebox.showwarning("Validation", "Community name is required")
            return
        if not data["address"]:
            messagebox.showwarning("Validation", "Address is required")
            return
        if not data["monthly_rent"] or not validate_amount(data["monthly_rent"]):
            messagebox.showwarning("Validation", "Please enter a valid monthly rent")
            return

        self.result = Property(
            id=self.prop.id,
            community_name=data["community_name"],
            address=data["address"],
            building_unit_room=data["building_unit_room"],
            property_type=data["property_type"] or "住宅",
            house_type=data["house_type"] or "一室一厅一卫",
            area=float(data["area"]) if data["area"] else 0.0,
            monthly_rent=float(data["monthly_rent"]),
            deposit=float(data["deposit"]) if data["deposit"] else 0.0,
            status=data["status"] or "待出租",
            description=self.desc_text.get("1.0", tk.END).strip()
        )
        self.dialog.destroy()


class TenantDialog:
    """租客添加/编辑对话框"""

    def __init__(self, parent, title: str, tenant: Optional[Tenant] = None):
        self.result: Optional[Tenant] = None
        self.tenant = tenant or Tenant()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("480x420")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Theme.CARD)

        self._create_widgets()
        self._load_data()
        parent.wait_window(self.dialog)

    def _create_widgets(self):
        main_frame = tk.Frame(self.dialog, bg=Theme.CARD, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="Tenant Info",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        fields = [("Name *", "name", 1), ("Phone *", "phone", 2),
                  ("Email", "email", 3), ("ID Card", "id_card", 4),
                  ("Emergency Contact", "emergency_contact", 5),
                  ("Emergency Phone", "emergency_phone", 6)]
        self.entries = {}
        for label, key, row in fields:
            tk.Label(main_frame, text=label, font=("Microsoft YaHei", 10),
                    bg=Theme.CARD, fg=Theme.TEXT).grid(row=row, column=0, sticky=tk.W, pady=4, padx=(0, 10))
            entry = ttk.Entry(main_frame, width=35)
            entry.grid(row=row, column=1, sticky=tk.W, pady=4)
            self.entries[key] = entry
        tk.Label(main_frame, text="Notes", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=7, column=0, sticky=tk.W, pady=4)
        self.notes_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.notes_text.grid(row=7, column=1, sticky=tk.W, pady=4)
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="OK", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=8)

    def _load_data(self):
        if self.tenant.id:
            self.entries["name"].insert(0, self.tenant.name)
            self.entries["phone"].insert(0, self.tenant.phone)
            self.entries["email"].insert(0, self.tenant.email)
            self.entries["id_card"].insert(0, self.tenant.id_card)
            self.entries["emergency_contact"].insert(0, self.tenant.emergency_contact)
            self.entries["emergency_phone"].insert(0, self.tenant.emergency_phone)
            self.notes_text.insert("1.0", self.tenant.notes)

    def _confirm(self):
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        if not data["name"]:
            messagebox.showwarning("Validation", "Name is required")
            return
        if not data["phone"]:
            messagebox.showwarning("Validation", "Phone is required")
            return
        if data["email"] and not validate_email(data["email"]):
            messagebox.showwarning("Validation", "Invalid email format")
            return
        self.result = Tenant(
            id=self.tenant.id, name=data["name"], phone=data["phone"],
            email=data["email"], id_card=data["id_card"],
            emergency_contact=data["emergency_contact"],
            emergency_phone=data["emergency_phone"],
            notes=self.notes_text.get("1.0", tk.END).strip()
        )
        self.dialog.destroy()


class LeaseDialog:
    """合同新建对话框"""

    def __init__(self, parent, title: str, properties: List[Property], tenants: List[Tenant],
                 lease: Optional[Lease] = None):
        self.result: Optional[Lease] = None
        self.lease = lease or Lease()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("520x520")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Theme.CARD)

        self.properties = properties
        self.tenants = tenants
        self._create_widgets()
        self._load_data()
        parent.wait_window(self.dialog)

    def _create_widgets(self):
        main_frame = tk.Frame(self.dialog, bg=Theme.CARD, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Contract Info",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Property
        tk.Label(main_frame, text="Property *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.prop_combo = ttk.Combobox(main_frame, width=35, state="readonly")
        self.prop_combo.grid(row=1, column=1, sticky=tk.W, pady=4)
        self.prop_names = [f"{p.id} - {p.community_name} ({p.address})" for p in self.properties]
        self.prop_combo["values"] = self.prop_names

        # Tenant
        tk.Label(main_frame, text="Tenant *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.tenant_combo = ttk.Combobox(main_frame, width=35, state="readonly")
        self.tenant_combo.grid(row=2, column=1, sticky=tk.W, pady=4)
        self.tenant_names = [f"{t.id} - {t.name} ({t.phone})" for t in self.tenants]
        self.tenant_combo["values"] = self.tenant_names

        # Dates
        tk.Label(main_frame, text="Start Date * (YYYY-MM-DD)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=3, column=0, sticky=tk.W, pady=4)
        self.start_entry = ttk.Entry(main_frame, width=35)
        self.start_entry.grid(row=3, column=1, sticky=tk.W, pady=4)

        tk.Label(main_frame, text="End Date * (YYYY-MM-DD)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=4, column=0, sticky=tk.W, pady=4)
        self.end_entry = ttk.Entry(main_frame, width=35)
        self.end_entry.grid(row=4, column=1, sticky=tk.W, pady=4)

        # Amounts
        tk.Label(main_frame, text="Monthly Rent *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=5, column=0, sticky=tk.W, pady=4)
        self.rent_entry = ttk.Entry(main_frame, width=35)
        self.rent_entry.grid(row=5, column=1, sticky=tk.W, pady=4)

        tk.Label(main_frame, text="Deposit", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=6, column=0, sticky=tk.W, pady=4)
        self.deposit_entry = ttk.Entry(main_frame, width=35)
        self.deposit_entry.grid(row=6, column=1, sticky=tk.W, pady=4)

        # Payment day
        tk.Label(main_frame, text="Payment Day (1-28)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=7, column=0, sticky=tk.W, pady=4)
        self.pay_day_spin = ttk.Spinbox(main_frame, from_=1, to=28, width=32)
        self.pay_day_spin.grid(row=7, column=1, sticky=tk.W, pady=4)

        # Payment frequency
        freq_frame = tk.Frame(main_frame, bg=Theme.CARD, highlightbackground=Theme.ACCENT,
                             highlightthickness=1, padx=10, pady=8)
        freq_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E, pady=8)

        tk.Label(freq_frame, text="Payment Frequency",
                font=("Microsoft YaHei", 11, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(0, 5))

        self.freq_var = tk.StringVar(value="Monthly")
        freq_row = tk.Frame(freq_frame, bg=Theme.CARD)
        freq_row.pack(fill=tk.X)
        for freq in ["Monthly", "Quarterly", "Semi-Annual", "Annual"]:
            rb = tk.Radiobutton(freq_row, text=freq, variable=self.freq_var, value=freq,
                               font=("Microsoft YaHei", 10),
                               bg=Theme.CARD, fg=Theme.TEXT,
                               selectcolor=Theme.ACCENT,
                               activebackground=Theme.CARD,
                               command=self._on_freq_change)
            rb.pack(side=tk.LEFT, padx=8)

        self.freq_amount_label = tk.Label(freq_frame, text="Amount per period: 0.00",
                                         font=("Microsoft YaHei", 10),
                                         bg=Theme.CARD, fg=Theme.SUCCESS)
        self.freq_amount_label.pack(anchor=tk.W, pady=(3, 0))
        self.rent_entry.bind("<KeyRelease>", self._on_freq_change)

        # Notes
        tk.Label(main_frame, text="Notes", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=9, column=0, sticky=tk.W, pady=4)
        self.notes_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.notes_text.grid(row=9, column=1, sticky=tk.W, pady=4)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="OK", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=8)

    def _on_freq_change(self, event=None):
        freq = self.freq_var.get()
        freq_map = {"Monthly": 1, "Quarterly": 3, "Semi-Annual": 6, "Annual": 12}
        months = freq_map.get(freq, 1)
        try:
            rent = float(self.rent_entry.get().strip() or 0)
            self.freq_amount_label.config(text=f"Amount per period: {format_currency(rent * months)} ({freq})")
        except ValueError:
            pass

    def _load_data(self):
        if self.lease.id:
            for i, pn in enumerate(self.prop_names):
                if str(self.lease.property_id) in pn:
                    self.prop_combo.current(i)
                    break
            for i, tn in enumerate(self.tenant_names):
                if str(self.lease.tenant_id) in tn:
                    self.tenant_combo.current(i)
                    break
            self.start_entry.insert(0, self.lease.start_date)
            self.end_entry.insert(0, self.lease.end_date)
            self.rent_entry.insert(0, str(self.lease.monthly_rent))
            self.deposit_entry.insert(0, str(self.lease.deposit_amount))
            self.pay_day_spin.set(str(self.lease.payment_day))
            freq_map_rev = {"月付": "Monthly", "季付": "Quarterly", "半年付": "Semi-Annual", "年付": "Annual"}
            self.freq_var.set(freq_map_rev.get(self.lease.payment_frequency, "Monthly"))
            self.notes_text.insert("1.0", self.lease.notes)
        else:
            self.pay_day_spin.set("1")
            self.freq_var.set("Monthly")
        self._on_freq_change()

    def _confirm(self):
        prop_idx = self.prop_combo.current()
        tenant_idx = self.tenant_combo.current()
        if prop_idx < 0:
            messagebox.showwarning("Validation", "Please select a property")
            return
        if tenant_idx < 0:
            messagebox.showwarning("Validation", "Please select a tenant")
            return

        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        rent = self.rent_entry.get().strip()

        if not validate_date(start):
            messagebox.showwarning("Validation", "Invalid start date format (YYYY-MM-DD)")
            return
        if not validate_date(end):
            messagebox.showwarning("Validation", "Invalid end date format (YYYY-MM-DD)")
            return
        if not rent or not validate_amount(rent):
            messagebox.showwarning("Validation", "Please enter a valid rent amount")
            return

        prop = self.properties[prop_idx]
        tenant = self.tenants[tenant_idx]
        freq_map = {"Monthly": "月付", "Quarterly": "季付", "Semi-Annual": "半年付", "Annual": "年付"}

        self.result = Lease(
            id=self.lease.id, property_id=prop.id, tenant_id=tenant.id,
            property_name=prop.community_name, tenant_name=tenant.name,
            start_date=start, end_date=end,
            monthly_rent=float(rent),
            deposit_amount=float(self.deposit_entry.get().strip() or 0),
            payment_day=int(self.pay_day_spin.get()),
            payment_frequency=freq_map.get(self.freq_var.get(), "月付"),
            status="生效中", notes=self.notes_text.get("1.0", tk.END).strip()
        )
        self.dialog.destroy()


class PaymentDialog:
    """缴费记录对话框（自动生成下次缴费时间）"""

    def __init__(self, parent, title: str, leases: List[Lease],
                 payment: Optional[Payment] = None):
        self.result: Optional[Payment] = None
        self.payment = payment or Payment()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("480x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Theme.CARD)

        self.leases = leases
        # 预加载对应合同的下次缴费时间
        self.lease_next_dates = {}
        for l in leases:
            nd = l.get_next_payment_date()
            self.lease_next_dates[l.id] = nd or ""

        self._create_widgets()
        self._load_data()
        parent.wait_window(self.dialog)

    def _create_widgets(self):
        main_frame = tk.Frame(self.dialog, bg=Theme.CARD, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Payment Record",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Contract
        tk.Label(main_frame, text="Contract *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.lease_combo = ttk.Combobox(main_frame, width=35, state="readonly")
        self.lease_combo.grid(row=1, column=1, sticky=tk.W, pady=4)
        self.lease_names = [f"{l.id} - {l.property_name} / {l.tenant_name}" for l in self.leases]
        self.lease_combo["values"] = self.lease_names
        self.lease_combo.bind("<<ComboboxSelected>>", self._on_lease_selected)

        # Amount
        tk.Label(main_frame, text="Amount *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.amount_entry = ttk.Entry(main_frame, width=35)
        self.amount_entry.grid(row=2, column=1, sticky=tk.W, pady=4)

        # Date
        tk.Label(main_frame, text="Pay Date * (YYYY-MM-DD)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=3, column=0, sticky=tk.W, pady=4)
        self.date_entry = ttk.Entry(main_frame, width=35)
        self.date_entry.grid(row=3, column=1, sticky=tk.W, pady=4)

        # ====== 新增：下次缴费时间（自动生成）======
        next_frame = tk.Frame(main_frame, bg=Theme.CARD, highlightbackground=Theme.SUCCESS,
                             highlightthickness=1, padx=10, pady=6)
        next_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=6)

        tk.Label(next_frame, text="Next Due Date (Auto)",
                font=("Microsoft YaHei", 10, "bold"),
                bg=Theme.CARD, fg=Theme.SUCCESS).pack(anchor=tk.W)

        self.next_date_var = tk.StringVar(value="Select a contract to auto-generate")
        tk.Label(next_frame, textvariable=self.next_date_var,
                font=("Microsoft YaHei", 11),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(3, 0))

        # Type
        tk.Label(main_frame, text="Type", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=5, column=0, sticky=tk.W, pady=4)
        self.type_combo = ttk.Combobox(main_frame,
            values=["Rent", "Deposit", "Water", "Electricity", "Gas", "Property", "Other"],
            state="readonly", width=32)
        self.type_combo.grid(row=5, column=1, sticky=tk.W, pady=4)

        # Method
        tk.Label(main_frame, text="Method", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=6, column=0, sticky=tk.W, pady=4)
        self.method_combo = ttk.Combobox(main_frame,
            values=["WeChat", "Alipay", "Bank Transfer", "Cash", "Other"],
            state="readonly", width=32)
        self.method_combo.grid(row=6, column=1, sticky=tk.W, pady=4)

        # Status
        tk.Label(main_frame, text="Status", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=7, column=0, sticky=tk.W, pady=4)
        self.status_combo = ttk.Combobox(main_frame,
            values=["Paid", "Pending", "Overdue"],
            state="readonly", width=32)
        self.status_combo.grid(row=7, column=1, sticky=tk.W, pady=4)

        # Notes
        tk.Label(main_frame, text="Notes", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=8, column=0, sticky=tk.W, pady=4)
        self.notes_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.notes_text.grid(row=8, column=1, sticky=tk.W, pady=4)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="OK", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=8)

    def _on_lease_selected(self, event=None):
        """选择合同后自动生成下次缴费时间"""
        idx = self.lease_combo.current()
        if idx >= 0:
            lease = self.leases[idx]
            next_date = lease.get_next_payment_date()
            amount = lease.get_payment_amount()
            if next_date:
                self.next_date_var.set(f"{next_date}  (Amount: {format_currency(amount)})")
            else:
                self.next_date_var.set("Contract expired or ended")
            # 自动填入建议金额
            if not self.amount_entry.get().strip():
                self.amount_entry.insert(0, str(amount))

    def _load_data(self):
        if self.payment.id:
            for i, ln in enumerate(self.lease_names):
                if str(self.payment.lease_id) in ln:
                    self.lease_combo.current(i)
                    break
            self.amount_entry.insert(0, str(self.payment.amount))
            self.date_entry.insert(0, self.payment.payment_date)
            self.next_date_var.set(self.payment.next_payment_date or "Not set")
            pt_map = {"租金": "Rent", "押金": "Deposit", "水费": "Water", "电费": "Electricity",
                      "燃气费": "Gas", "物业费": "Property", "其他": "Other"}
            self.type_combo.set(pt_map.get(self.payment.payment_type, "Rent"))
            pm_map = {"微信支付": "WeChat", "支付宝": "Alipay", "银行转账": "Bank Transfer", "现金": "Cash", "其他": "Other"}
            self.method_combo.set(pm_map.get(self.payment.payment_method, "WeChat"))
            ps_map = {"已支付": "Paid", "待支付": "Pending", "已逾期": "Overdue"}
            self.status_combo.set(ps_map.get(self.payment.status, "Paid"))
            self.notes_text.insert("1.0", self.payment.notes)
        else:
            self.date_entry.insert(0, get_today_str())
            self.type_combo.set("Rent")
            self.method_combo.set("WeChat")
            self.status_combo.set("Paid")

    def _confirm(self):
        idx = self.lease_combo.current()
        if idx < 0:
            messagebox.showwarning("Validation", "Please select a contract")
            return
        amount = self.amount_entry.get().strip()
        date_str = self.date_entry.get().strip()
        if not amount or not validate_amount(amount):
            messagebox.showwarning("Validation", "Please enter a valid amount")
            return
        if not validate_date(date_str):
            messagebox.showwarning("Validation", "Invalid date format (YYYY-MM-DD)")
            return

        lease = self.leases[idx]

        # 自动生成下次缴费时间
        next_date = lease.get_next_payment_date()

        pt_map = {"Rent": "租金", "Deposit": "押金", "Water": "水费", "Electricity": "电费",
                  "Gas": "燃气费", "Property": "物业费", "Other": "其他"}
        pm_map = {"WeChat": "微信支付", "Alipay": "支付宝", "Bank Transfer": "银行转账", "Cash": "现金", "Other": "其他"}
        ps_map = {"Paid": "已支付", "Pending": "待支付", "Overdue": "已逾期"}

        self.result = Payment(
            id=self.payment.id, lease_id=lease.id,
            tenant_name=lease.tenant_name, property_name=lease.property_name,
            amount=float(amount), payment_date=date_str,
            next_payment_date=next_date or "",
            payment_type=pt_map.get(self.type_combo.get(), "租金"),
            payment_method=pm_map.get(self.method_combo.get(), "微信支付"),
            status=ps_map.get(self.status_combo.get(), "已支付"),
            notes=self.notes_text.get("1.0", tk.END).strip()
        )
        self.dialog.destroy()


class LeaseDetailDialog:
    """合同详情查看对话框"""

    def __init__(self, parent, lease: Lease):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Contract Details - {lease.property_name} / {lease.tenant_name}")
        self.dialog.geometry("520x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Theme.CARD)

        main_frame = tk.Frame(self.dialog, bg=Theme.CARD, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Contract Details",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(0, 10))

        info = [
            ("ID", str(lease.id)),
            ("Property", lease.property_name),
            ("Tenant", lease.tenant_name),
            ("Start", lease.start_date),
            ("End", lease.end_date),
            ("Duration", f"{lease.duration_days} days"),
            ("Monthly Rent", format_currency(lease.monthly_rent)),
            ("Deposit", format_currency(lease.deposit_amount)),
            ("Frequency", lease.payment_frequency),
            ("Period Amount", format_currency(lease.get_payment_amount())),
            ("Next Due", lease.get_next_payment_date() or "Expired"),
            ("Payment Day", f"Day {lease.payment_day}"),
            ("Status", lease.status),
            ("Notes", lease.notes or "None"),
        ]

        for i, (label, value) in enumerate(info):
            row_frame = tk.Frame(main_frame, bg=Theme.CARD)
            row_frame.pack(fill=tk.X, pady=1)
            tk.Label(row_frame, text=f"{label}:",
                    font=("Microsoft YaHei", 10, "bold"),
                    bg=Theme.CARD, fg=Theme.PRIMARY,
                    width=16, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row_frame, text=value,
                    font=("Microsoft YaHei", 10),
                    bg=Theme.CARD, fg=Theme.TEXT).pack(side=tk.LEFT)

        ttk.Button(main_frame, text="Close", command=self.dialog.destroy,
                   style="Flat.TButton").pack(pady=(15, 0))


# ==================== 主入口 ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = RentalManagementApp(root)
    root.mainloop()
