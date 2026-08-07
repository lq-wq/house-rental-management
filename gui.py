"""房屋租赁管理系统 - 图形界面（完整中文版）"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
from typing import Optional, List
import os

from models import Property, Tenant, Lease, Payment, PAYMENT_FREQUENCIES, FREQUENCY_MONTHS, HOUSE_TYPES
from database import Database
from utils import (
    validate_phone, validate_email, validate_amount, validate_date,
    format_currency, get_status_color, get_today_str
)


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

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("房屋租赁管理系统")
        self.root.geometry("1280x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg=Theme.BG)
        self.db = Database()

        self._setup_styles()
        self._create_menu()
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

    def _create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="备份数据库", command=self._backup_db)
        file_menu.add_command(label="恢复数据库", command=self._restore_db)
        file_menu.add_separator()
        file_menu.add_command(label="导出数据到 CSV", command=self._export_csv)
        file_menu.add_command(label="从 CSV 导入数据", command=self._import_csv)
        file_menu.add_separator()
        file_menu.add_command(label="打开数据目录", command=self._open_data_dir)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)
        menubar.add_cascade(label="文件", menu=file_menu)

        stats_menu = tk.Menu(menubar, tearoff=0)
        stats_menu.add_command(label="按楼栋统计", command=self._show_building_stats)
        stats_menu.add_command(label="自定义时间统计", command=self._show_custom_time_stats)
        stats_menu.add_separator()
        stats_menu.add_command(label="月度收入报表", command=self._show_monthly_report)
        menubar.add_cascade(label="统计", menu=stats_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="刷新所有数据", command=self.refresh_all)
        menubar.add_cascade(label="视图", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)

    def _create_header(self):
        header = tk.Frame(self.root, bg=Theme.HEADER_BG, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="房屋租赁管理系统 v2.0",
                font=("Microsoft YaHei", 18, "bold"),
                bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT, anchor="w"
        ).pack(side=tk.LEFT, padx=25, pady=12)
        self.header_time = tk.Label(header, font=("Microsoft YaHei", 10),
                                   bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT, anchor="e")
        self.header_time.pack(side=tk.RIGHT, padx=25, pady=15)
        self._update_header_time()

    def _update_header_time(self):
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        self.header_time.config(text=now)
        self.root.after(1000, self._update_header_time)

    def _create_notebook(self):
        main_container = tk.Frame(self.root, bg=Theme.BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 0))
        self._create_dashboard_tab()
        self._create_property_tab()
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

    def _create_card(self, parent, title, value, color=Theme.ACCENT, **kwargs):
        card = tk.Frame(parent, bg=Theme.CARD, highlightbackground=Theme.BORDER,
                       highlightthickness=1, **kwargs)
        color_bar = tk.Frame(card, bg=color, height=4)
        color_bar.pack(fill=tk.X)
        content = tk.Frame(card, bg=Theme.CARD)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(12, 15))
        value_label = tk.Label(content, text=value,
                              font=("Microsoft YaHei", 22, "bold"),
                              bg=Theme.CARD, fg=color, anchor="w")
        value_label.pack(fill=tk.X)
        title_label = tk.Label(content, text=title,
                              font=("Microsoft YaHei", 9),
                              bg=Theme.CARD, fg=Theme.TEXT_SECONDARY, anchor="w")
        title_label.pack(fill=tk.X, pady=(2, 0))
        card._value_label = value_label
        card._title_label = title_label
        card._color = color
        return card

    def _update_card(self, card, title, value, color):
        if hasattr(card, '_value_label'):
            card._value_label.config(text=value, fg=color)
        if hasattr(card, '_title_label'):
            card._title_label.config(text=title)

    def _create_dashboard_tab(self):
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="仪表盘")

        tk.Label(frame, text="系统概览",
                font=("Microsoft YaHei", 16, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(15, 5), padx=15)

        cards_frame = tk.Frame(frame, bg=Theme.BG)
        cards_frame.pack(fill=tk.X, padx=15, pady=5)

        self._stat_cards = {}
        stats_info = [
            ("total_properties", "总房源", "0", Theme.ACCENT),
            ("available_properties", "待出租", "0", Theme.SUCCESS),
            ("rented_properties", "已出租", "0", Theme.PRIMARY),
            ("total_tenants", "租客总数", "0", Theme.ACCENT),
            ("active_leases", "生效合同", "0", Theme.SUCCESS),
            ("monthly_income", "本月收入", "0.00", Theme.WARNING),
            ("total_income", "总收入", "0.00", Theme.DANGER),
            ("overdue_payments", "逾期缴费", "0", Theme.DANGER),
        ]

        for i, (key, title, init_val, color) in enumerate(stats_info):
            if key in ("monthly_income", "total_income"):
                card = self._create_card(cards_frame, title, "0.00", color, width=150, height=95)
            else:
                card = self._create_card(cards_frame, title, init_val, color, width=150, height=95)
            card.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="nsew")
            cards_frame.columnconfigure(i%4, weight=1)
            self._stat_cards[key] = card

        tk.Label(frame, text="缴费提醒",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(20, 5), padx=15)

        self.reminder_frame = tk.Frame(frame, bg=Theme.BG)
        self.reminder_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self._refresh_reminders()

        tk.Label(frame, text="快捷操作",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(15, 5), padx=15)

        btn_frame = tk.Frame(frame, bg=Theme.BG)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Button(btn_frame, text="+ 添加房源", command=self._show_add_property,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="+ 新建合同", command=self._show_add_lease,
                   style="Success.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="记录缴费", command=self._show_add_payment,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="统计报表", command=self._show_building_stats,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="刷新数据", command=self._refresh_dashboard,
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
                    status_text = f"已逾期 {-days} 天"
                    color = Theme.DANGER
                elif days == 0:
                    status_text = "今天到期"
                    color = Theme.WARNING
                elif days <= 3:
                    status_text = f"还剩 {days} 天"
                    color = Theme.WARNING
                elif days <= 7:
                    status_text = f"还剩 {days} 天"
                    color = Theme.ACCENT
                else:
                    continue
                reminders.append((days, lease, next_date, amount, status_text, color))

        if not reminders:
            if leases:
                tk.Label(self.reminder_frame, text="所有缴费均在正常周期内",
                        font=("Microsoft YaHei", 11),
                        bg=Theme.BG, fg=Theme.SUCCESS).pack(anchor=tk.W, pady=10)
            else:
                tk.Label(self.reminder_frame, text="暂无生效合同",
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
            tk.Label(bottom_row, text=f"缴费日: {next_date}  |  金额: {format_currency(amount)}  |  {lease.payment_frequency}",
                    font=("Microsoft YaHei", 9),
                    bg=Theme.CARD, fg=Theme.TEXT_SECONDARY).pack(side=tk.LEFT)
            tk.Label(card, text=f" {status_text} ",
                    font=("Microsoft YaHei", 10, "bold"),
                    bg=color, fg="white", padx=10, pady=2).pack(side=tk.RIGHT)

    def _refresh_dashboard(self):
        stats = self.db.get_statistics()
        mapping = {
            "total_properties": ("总房源", str(stats.get("total_properties", 0)), Theme.ACCENT),
            "available_properties": ("待出租", str(stats.get("available_properties", 0)), Theme.SUCCESS),
            "rented_properties": ("已出租", str(stats.get("rented_properties", 0)), Theme.PRIMARY),
            "total_tenants": ("租客总数", str(stats.get("total_tenants", 0)), Theme.ACCENT),
            "active_leases": ("生效合同", str(stats.get("active_leases", 0)), Theme.SUCCESS),
            "monthly_income": ("本月收入", format_currency(stats.get("monthly_income", 0)), Theme.WARNING),
            "total_income": ("总收入", format_currency(stats.get("total_income", 0)), Theme.DANGER),
            "overdue_payments": ("逾期缴费", str(stats.get("overdue_payments", 0)), Theme.DANGER),
        }
        for key, (title, value, color) in mapping.items():
            if key in self._stat_cards:
                self._update_card(self._stat_cards[key], title, value, color)
        self._refresh_reminders()
        self.set_status("仪表盘数据已刷新")

    def _create_property_tab(self):
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="房源管理")

        toolbar = tk.Frame(frame, bg=Theme.BG)
        toolbar.pack(fill=tk.X, pady=8, padx=10)

        ttk.Button(toolbar, text="+ 添加房源", command=self._show_add_property,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="编辑", command=self._edit_property,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除", command=self._delete_property,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="刷新", command=self._refresh_property_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="搜索:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.prop_search_var = tk.StringVar()
        self.prop_search_var.trace("w", lambda *a: self._refresh_property_list())
        ttk.Entry(toolbar, textvariable=self.prop_search_var, width=20).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="状态:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(10, 2))
        self.prop_status_var = tk.StringVar(value="全部")
        combo = ttk.Combobox(toolbar, textvariable=self.prop_status_var,
                            values=["全部", "待出租", "已出租", "已下架"],
                            state="readonly", width=8)
        combo.pack(side=tk.LEFT, padx=2)
        combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_property_list())

        table_frame = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "小区名称", "地址", "栋/单元/号", "类型", "面积", "户型", "月租金", "押金", "状态")
        self.prop_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                      selectmode="browse", height=15)
        for col in columns:
            self.prop_tree.heading(col, text=col)
        self.prop_tree.column("id", width=40, anchor=tk.CENTER)
        self.prop_tree.column("小区名称", width=100)
        self.prop_tree.column("地址", width=150)
        self.prop_tree.column("栋/单元/号", width=120)
        self.prop_tree.column("类型", width=60, anchor=tk.CENTER)
        self.prop_tree.column("面积", width=60, anchor=tk.CENTER)
        self.prop_tree.column("户型", width=100, anchor=tk.CENTER)
        self.prop_tree.column("月租金", width=100, anchor=tk.E)
        self.prop_tree.column("押金", width=100, anchor=tk.E)
        self.prop_tree.column("状态", width=80, anchor=tk.CENTER)

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
        if status == "全部":
            status = ""
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
        dialog = PropertyDialog(self.root, "添加房源")
        if dialog.result:
            prop_id = self.db.add_property(dialog.result)
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status(f"房源添加成功 (ID: {prop_id})")

    def _edit_property(self):
        selected = self.prop_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个房源")
            return
        values = self.prop_tree.item(selected[0])["values"]
        prop = self.db.get_property(values[0])
        if prop:
            dialog = PropertyDialog(self.root, "编辑房源", prop)
            if dialog.result:
                self.db.update_property(dialog.result)
                self._refresh_property_list()
                self._refresh_dashboard()
                self.set_status(f"房源已更新 (ID: {values[0]})")

    def _delete_property(self):
        selected = self.prop_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个房源")
            return
        values = self.prop_tree.item(selected[0])["values"]
        if messagebox.askyesno("确认删除", f"确定要删除房源 [{values[1]}] 吗?"):
            self.db.delete_property(values[0])
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status("房源已删除")

    def _create_contract_tab(self):
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="合同与租客管理")

        tk.Label(frame, text="合同管理",
                font=("Microsoft YaHei", 13, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, padx=10, pady=(10, 0))

        toolbar = tk.Frame(frame, bg=Theme.BG)
        toolbar.pack(fill=tk.X, pady=5, padx=10)

        ttk.Button(toolbar, text="+ 新建合同", command=self._show_add_lease,
                   style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="查看详情", command=self._view_lease,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="编辑", command=self._edit_lease,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="解约合同", command=self._terminate_lease,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="搜索:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.lease_search_var = tk.StringVar()
        self.lease_search_var.trace("w", lambda *a: self._refresh_lease_list())
        ttk.Entry(toolbar, textvariable=self.lease_search_var, width=15).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="状态:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(10, 2))
        self.lease_status_var = tk.StringVar(value="全部")
        lc = ttk.Combobox(toolbar, textvariable=self.lease_status_var,
                          values=["全部", "生效中", "已到期", "已解约"],
                          state="readonly", width=8)
        lc.pack(side=tk.LEFT, padx=2)
        lc.bind("<<ComboboxSelected>>", lambda e: self._refresh_lease_list())

        ttk.Button(toolbar, text="刷新", command=self._refresh_lease_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        table_frame = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)

        columns = ("id", "房源", "租客", "起始日期", "结束日期", "缴费周期", "月租金", "押金", "状态")
        self.lease_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                       selectmode="browse", height=8)
        for col in columns:
            self.lease_tree.heading(col, text=col)
        self.lease_tree.column("id", width=40, anchor=tk.CENTER)
        self.lease_tree.column("房源", width=120)
        self.lease_tree.column("租客", width=100)
        self.lease_tree.column("起始日期", width=90, anchor=tk.CENTER)
        self.lease_tree.column("结束日期", width=90, anchor=tk.CENTER)
        self.lease_tree.column("缴费周期", width=70, anchor=tk.CENTER)
        self.lease_tree.column("月租金", width=90, anchor=tk.E)
        self.lease_tree.column("押金", width=90, anchor=tk.E)
        self.lease_tree.column("状态", width=80, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.lease_tree.yview)
        self.lease_tree.configure(yscrollcommand=scrollbar.set)
        self.lease_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lease_tree.bind("<Double-1>", lambda e: self._view_lease())
        self.lease_tree.tag_configure("odd", background=Theme.ROW_ALT)
        self.lease_tree.tag_configure("even", background=Theme.CARD)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame, text="租客管理",
                font=("Microsoft YaHei", 13, "bold"),
                bg=Theme.BG, fg=Theme.PRIMARY).pack(anchor=tk.W, padx=10, pady=(5, 0))

        tenant_toolbar = tk.Frame(frame, bg=Theme.BG)
        tenant_toolbar.pack(fill=tk.X, pady=5, padx=10)

        ttk.Button(tenant_toolbar, text="+ 添加租客", command=self._show_add_tenant,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(tenant_toolbar, text="编辑", command=self._edit_tenant,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(tenant_toolbar, text="删除", command=self._delete_tenant,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(tenant_toolbar, text="搜索:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.tenant_search_var = tk.StringVar()
        self.tenant_search_var.trace("w", lambda *a: self._refresh_tenant_list())
        ttk.Entry(tenant_toolbar, textvariable=self.tenant_search_var, width=15).pack(side=tk.LEFT, padx=2)

        ttk.Button(tenant_toolbar, text="刷新", command=self._refresh_tenant_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        tenant_table = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        tenant_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 10))

        tcolumns = ("id", "姓名", "电话", "邮箱", "身份证号", "紧急联系人", "紧急电话")
        self.tenant_tree = ttk.Treeview(tenant_table, columns=tcolumns, show="headings",
                                        selectmode="browse", height=6)
        for col in tcolumns:
            self.tenant_tree.heading(col, text=col)
        self.tenant_tree.column("id", width=40, anchor=tk.CENTER)
        self.tenant_tree.column("姓名", width=80)
        self.tenant_tree.column("电话", width=110)
        self.tenant_tree.column("邮箱", width=150)
        self.tenant_tree.column("身份证号", width=150)
        self.tenant_tree.column("紧急联系人", width=100)
        self.tenant_tree.column("紧急电话", width=110)
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
        if status == "全部":
            status = ""
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
            messagebox.showwarning("提示", "没有可用的房源，请先添加房源")
            return
        tenants = self.db.get_all_tenants()
        if not tenants:
            if messagebox.askyesno("提示", "没有租客信息，现在添加一个?"):
                self._show_add_tenant()
                tenants = self.db.get_all_tenants()
                if not tenants:
                    return
            else:
                return
        dialog = LeaseDialog(self.root, "新建合同", available_props, tenants)
        if dialog.result:
            lease_id = self.db.add_lease(dialog.result)
            self._refresh_lease_list()
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status(f"合同创建成功 (ID: {lease_id})")

    def _view_lease(self):
        selected = self.lease_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        values = self.lease_tree.item(selected[0])["values"]
        lease = self.db.get_lease(values[0])
        if lease:
            LeaseDetailDialog(self.root, lease)

    def _terminate_lease(self):
        selected = self.lease_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        values = self.lease_tree.item(selected[0])["values"]
        if values[8] != "生效中":
            messagebox.showinfo("提示", "只有生效中的合同可以解约")
            return
        if messagebox.askyesno("确认解约", f"确定要解约 [{values[1]} - {values[2]}] 的合同吗?"):
            self.db.terminate_lease(values[0])
            self._refresh_lease_list()
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status("合同已解约")

        def _edit_lease(self):
        """编辑合同"""
        selected = self.lease_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个合同")
            return
        values = self.lease_tree.item(selected[0])["values"]
        lease = self.db.get_lease(values[0])
        if not lease:
            messagebox.showwarning("提示", "合同不存在")
            return

        # 获取所有房源和租客用于编辑选择
        properties = self.db.get_all_properties()
        tenants = self.db.get_all_tenants()

        dialog = LeaseDialog(self.root, "编辑合同", properties, tenants, lease)
        if dialog.result:
            self.db.update_lease(dialog.result)
            self._refresh_lease_list()
            self._refresh_property_list()
            self._refresh_dashboard()
            self.set_status(f"合同已更新 (ID: {dialog.result.id})")

    def _show_add_tenant(self):
        dialog = TenantDialog(self.root, "添加租客")
        if dialog.result:
            tenant_id = self.db.add_tenant(dialog.result)
            self._refresh_tenant_list()
            self._refresh_dashboard()
            self.set_status(f"租客添加成功 (ID: {tenant_id})")

    def _edit_tenant(self):
        selected = self.tenant_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个租客")
            return
        values = self.tenant_tree.item(selected[0])["values"]
        tenant = self.db.get_tenant(values[0])
        if tenant:
            dialog = TenantDialog(self.root, "编辑租客", tenant)
            if dialog.result:
                self.db.update_tenant(dialog.result)
                self._refresh_tenant_list()
                self.set_status(f"租客已更新 (ID: {values[0]})")

    def _delete_tenant(self):
        selected = self.tenant_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个租客")
            return
        values = self.tenant_tree.item(selected[0])["values"]
        if messagebox.askyesno("确认删除", f"确定要删除租客 [{values[1]}] 吗?"):
            self.db.delete_tenant(values[0])
            self._refresh_tenant_list()
            self._refresh_dashboard()
            self.set_status("租客已删除")

    def _create_payment_tab(self):
        frame = tk.Frame(self.notebook, bg=Theme.BG)
        self.notebook.add(frame, text="缴费管理")

        toolbar = tk.Frame(frame, bg=Theme.BG)
        toolbar.pack(fill=tk.X, pady=8, padx=10)

        ttk.Button(toolbar, text="记录缴费", command=self._show_add_payment,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="编辑", command=self._edit_payment,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="删除", command=self._delete_payment,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="刷新", command=self._refresh_payment_list,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="搜索:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 2))
        self.pay_search_var = tk.StringVar()
        self.pay_search_var.trace("w", lambda *a: self._refresh_payment_list())
        ttk.Entry(toolbar, textvariable=self.pay_search_var, width=20).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="类型:", bg=Theme.BG, fg=Theme.TEXT,
                font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(10, 2))
        self.pay_type_var = tk.StringVar(value="全部")
        pc = ttk.Combobox(toolbar, textvariable=self.pay_type_var,
                          values=["全部", "租金", "押金", "水费", "电费", "燃气费", "物业费", "其他"],
                          state="readonly", width=8)
        pc.pack(side=tk.LEFT, padx=2)
        pc.bind("<<ComboboxSelected>>", lambda e: self._refresh_payment_list())

        table_frame = tk.Frame(frame, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("id", "租客", "房源", "金额", "缴费日期", "下次缴费", "类型", "方式", "状态")
        self.pay_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.pay_tree.heading(col, text=col)
        self.pay_tree.column("id", width=40, anchor=tk.CENTER)
        self.pay_tree.column("租客", width=90)
        self.pay_tree.column("房源", width=110)
        self.pay_tree.column("金额", width=90, anchor=tk.E)
        self.pay_tree.column("缴费日期", width=90, anchor=tk.CENTER)
        self.pay_tree.column("下次缴费", width=90, anchor=tk.CENTER)
        self.pay_tree.column("类型", width=70, anchor=tk.CENTER)
        self.pay_tree.column("方式", width=90, anchor=tk.CENTER)
        self.pay_tree.column("状态", width=70, anchor=tk.CENTER)

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
        if pay_type == "全部":
            pay_type = ""
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
            messagebox.showwarning("提示", "没有生效中的合同，无法记录缴费")
            return
        dialog = PaymentDialog(self.root, "记录缴费", leases)
        if dialog.result:
            pay_id = self.db.add_payment(dialog.result)
            self._refresh_payment_list()
            self._refresh_dashboard()
            self.set_status(f"缴费记录成功 (ID: {pay_id})")

    def _edit_payment(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一条缴费记录")
            return
        values = self.pay_tree.item(selected[0])["values"]
        payment = None
        for p in self.db.get_all_payments():
            if p.id == values[0]:
                payment = p
                break
        if payment:
            leases = self.db.search_leases(status="生效中")
            dialog = PaymentDialog(self.root, "编辑缴费", leases, payment)
            if dialog.result:
                self.db.update_payment(dialog.result)
                self._refresh_payment_list()
                self._refresh_dashboard()
                self.set_status("缴费记录已更新")

    def _delete_payment(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一条缴费记录")
            return
        values = self.pay_tree.item(selected[0])["values"]
        if messagebox.askyesno("确认删除", f"确定要删除金额为 {values[3]} 的缴费记录吗?"):
            self.db.delete_payment(values[0])
            self._refresh_payment_list()
            self._refresh_dashboard()
            self.set_status("缴费记录已删除")

    def refresh_all(self):
        self._refresh_dashboard()
        self._refresh_property_list()
        self._refresh_lease_list()
        self._refresh_tenant_list()
        self._refresh_payment_list()
        self.set_status("所有数据已刷新")

    def _backup_db(self):
        try:
            path = self.db.backup_database()
            messagebox.showinfo("备份成功", f"数据库已备份到: {path}")
            self.set_status("数据库备份完成")
        except Exception as e:
            messagebox.showerror("备份失败", str(e))

    def _restore_db(self):
        backups = self.db.list_backups()
        if not backups:
            messagebox.showinfo("提示", "没有找到备份文件")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("选择备份文件恢复")
        dialog.geometry("550x350")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=Theme.CARD)

        tk.Label(dialog, text="选择要恢复的备份:",
                font=("Microsoft YaHei", 12, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, padx=15, pady=(10, 5))

        frame = tk.Frame(dialog, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("序号", "备份时间", "大小(KB)")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            tree.heading(col, text=col)
        tree.column("序号", width=50, anchor=tk.CENTER)
        tree.column("备份时间", width=200, anchor=tk.CENTER)
        tree.column("大小(KB)", width=100, anchor=tk.E)

        for i, (path, mtime, size) in enumerate(backups, 1):
            tree.insert("", tk.END, values=(i, mtime, f"{size:.1f}"))

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def on_restore():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("提示", "请选择一个备份文件")
                return
            idx = tree.index(sel[0])
            path, mtime, size = backups[idx]
            if messagebox.askyesno("确认恢复", "恢复备份将覆盖当前所有数据，建议先备份当前数据。确定要恢复吗?"):
                self.db.restore_database(path)
                self.refresh_all()
                dialog.destroy()
                messagebox.showinfo("恢复成功", "数据已从备份恢复")
                self.set_status("数据库已恢复")

        btn_frame = tk.Frame(dialog, bg=Theme.CARD)
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        ttk.Button(btn_frame, text="恢复", command=on_restore,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=5)

    def _export_csv(self):
        from tkinter import filedialog
        table = simpledialog.askstring("导出数据", "请输入要导出的表名:\n(properties / tenants / leases / payments)", initialvalue="payments")
        if not table:
            return
        if table not in ("properties", "tenants", "leases", "payments"):
            messagebox.showwarning("提示", "表名无效")
            return
        filepath = filedialog.asksaveasfilename(
            title="保存为 CSV 文件",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv")],
            initialfile=f"{table}_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not filepath:
            return
        if self.db.export_to_csv(table, filepath):
            messagebox.showinfo("导出成功", f"数据已导出到: {filepath}")
            self.set_status(f"{table} 数据已导出")
        else:
            messagebox.showerror("导出失败", "导出失败，可能表中没有数据")

    def _import_csv(self):
        from tkinter import filedialog
        import os.path
        filepath = filedialog.askopenfilename(title="选择 CSV 文件", filetypes=[("CSV 文件", "*.csv")])
        if not filepath:
            return
        filename = os.path.basename(filepath).lower()
        table = ""
        for t in ("properties", "tenants", "leases", "payments"):
            if t in filename:
                table = t
                break
        if not table:
            table = simpledialog.askstring("导入数据", "未能从文件名识别表名，请手动输入:\n(properties / tenants / leases / payments)")
            if not table:
                return
        if table not in ("properties", "tenants", "leases", "payments"):
            messagebox.showwarning("提示", "表名无效")
            return
        count = self.db.import_from_csv(table, filepath)
        if count > 0:
            self.refresh_all()
            messagebox.showinfo("导入成功", f"成功导入 {count} 条记录到 {table}")
            self.set_status(f"已导入 {count} 条记录")
        else:
            messagebox.showerror("导入失败", "导入失败，请检查文件格式")

    def _open_data_dir(self):
        import subprocess
        data_dir = self.db.get_data_dir()
        try:
            if os.name == 'nt':
                os.startfile(data_dir)
            else:
                subprocess.Popen(['xdg-open', data_dir])
        except Exception:
            messagebox.showinfo("数据目录", f"数据目录: {data_dir}")

    def _show_building_stats(self):
        stats = self.db.get_building_statistics()
        if not stats:
            messagebox.showinfo("提示", "没有房源数据可供统计")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("按楼栋统计")
        dialog.geometry("650x400")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=Theme.CARD)

        tk.Label(dialog, text="楼栋统计报表",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, padx=15, pady=(10, 5))

        frame = tk.Frame(dialog, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("楼栋", "总房源", "已出租", "待出租", "月租金总额")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
        tree.column("楼栋", width=150)
        tree.column("总房源", width=80, anchor=tk.CENTER)
        tree.column("已出租", width=80, anchor=tk.CENTER)
        tree.column("待出租", width=80, anchor=tk.CENTER)
        tree.column("月租金总额", width=120, anchor=tk.E)

        total_props = 0
        total_rented = 0
        total_rent = 0
        for s in stats:
            tree.insert("", tk.END, values=(
                s["building"], s["total_properties"], s["rented_count"],
                s["available_count"], format_currency(s["total_rent"])
            ))
            total_props += s["total_properties"]
            total_rented += s["rented_count"]
            total_rent += s["total_rent"]

        tree.insert("", tk.END, values=("合计", total_props, total_rented, total_props - total_rented, format_currency(total_rent)), tags=("total",))
        tree.tag_configure("total", background="#E8F0FE")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(dialog, text="关闭", command=dialog.destroy, style="Flat.TButton").pack(pady=10)

    def _show_custom_time_stats(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("自定义时间统计")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=Theme.CARD)

        main_frame = tk.Frame(dialog, bg=Theme.CARD, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="自定义时间统计",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(0, 10))

        tk.Label(main_frame, text="开始日期 (YYYY-MM-DD):", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).pack(anchor=tk.W, pady=3)
        start_entry = ttk.Entry(main_frame, width=30)
        start_entry.pack(anchor=tk.W, pady=3)
        start_entry.insert(0, datetime.now().strftime("%Y-%m-01"))

        tk.Label(main_frame, text="结束日期 (YYYY-MM-DD):", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).pack(anchor=tk.W, pady=3)
        end_entry = ttk.Entry(main_frame, width=30)
        end_entry.pack(anchor=tk.W, pady=3)
        end_entry.insert(0, get_today_str())

        result_frame = tk.Frame(main_frame, bg=Theme.CARD, highlightbackground=Theme.BORDER,
                               highlightthickness=1, padx=15, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        result_vars = {}
        labels = [
            ("total_income", "时间段内收款总额:"),
            ("payment_count", "收款笔数:"),
            ("overdue_count", "逾期笔数:"),
            ("new_leases", "新增合同数:"),
            ("new_properties", "新增房源数:"),
        ]

        for key, label_text in labels:
            row = tk.Frame(result_frame, bg=Theme.CARD)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label_text,
                    font=("Microsoft YaHei", 10, "bold"),
                    bg=Theme.CARD, fg=Theme.PRIMARY,
                    width=20, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="-")
            result_vars[key] = var
            tk.Label(row, textvariable=var,
                    font=("Microsoft YaHei", 10),
                    bg=Theme.CARD, fg=Theme.TEXT).pack(side=tk.LEFT)

        type_frame = tk.Frame(result_frame, bg=Theme.CARD)
        type_frame.pack(fill=tk.X, pady=5)
        tk.Label(type_frame, text="各类型收入明细:",
                font=("Microsoft YaHei", 10, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W)

        def on_query():
            start = start_entry.get().strip()
            end = end_entry.get().strip()
            if not validate_date(start):
                messagebox.showwarning("验证失败", "开始日期格式不正确")
                return
            if not validate_date(end):
                messagebox.showwarning("验证失败", "结束日期格式不正确")
                return
            stats = self.db.get_custom_time_statistics(start, end)
            result_vars["total_income"].set(format_currency(stats["total_income"]))
            result_vars["payment_count"].set(str(stats["payment_count"]))
            result_vars["overdue_count"].set(str(stats["overdue_count"]))
            result_vars["new_leases"].set(str(stats["new_leases"]))
            result_vars["new_properties"].set(str(stats["new_properties"]))
            for w in type_frame.winfo_children():
                if w != type_frame.winfo_children()[0]:
                    w.destroy()
            for ptype, pamount in stats["income_by_type"].items():
                row = tk.Frame(type_frame, bg=Theme.CARD)
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=f"  {ptype}:",
                        font=("Microsoft YaHei", 9),
                        bg=Theme.CARD, fg=Theme.TEXT).pack(side=tk.LEFT, padx=(10, 0))
                tk.Label(row, text=format_currency(pamount),
                        font=("Microsoft YaHei", 9),
                        bg=Theme.CARD, fg=Theme.SUCCESS).pack(side=tk.LEFT)

        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="查询统计", command=on_query,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=5)

    def _show_monthly_report(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("月度收入报表")
        dialog.geometry("550x400")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=Theme.CARD)

        tk.Label(dialog, text="月度收入报表",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, padx=15, pady=(10, 5))

        year = datetime.now().year
        data = self.db.get_monthly_income_report(year)

        if not data:
            tk.Label(dialog, text=f"{year}年暂无收入数据",
                    font=("Microsoft YaHei", 11),
                    bg=Theme.CARD, fg=Theme.TEXT_SECONDARY).pack(expand=True)
        else:
            frame = tk.Frame(dialog, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
            frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

            columns = ("月份", "收入金额")
            tree = ttk.Treeview(frame, columns=columns, show="headings")
            tree.heading("月份", text="月份")
            tree.heading("收入金额", text="收入金额")
            tree.column("月份", width=200, anchor=tk.CENTER)
            tree.column("收入金额", width=200, anchor=tk.E)

            total = 0
            for month, amount in data:
                tree.insert("", tk.END, values=(month, format_currency(amount)))
                total += amount

            tree.insert("", tk.END, values=(f"{year}年 合计", format_currency(total)), tags=("total",))
            tree.tag_configure("total", background="#E8F0FE")

            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            summary_frame = tk.Frame(dialog, bg=Theme.CARD, padx=15, pady=8)
            summary_frame.pack(fill=tk.X)
            tk.Label(summary_frame, text=f"{year}年总收入: {format_currency(total)}",
                    font=("Microsoft YaHei", 12, "bold"),
                    bg=Theme.CARD, fg=Theme.SUCCESS).pack(anchor=tk.W)

        ttk.Button(dialog, text="关闭", command=dialog.destroy, style="Flat.TButton").pack(pady=10)

    def _show_about(self):
        messagebox.showinfo("关于", "房屋租赁管理系统 v2.0\n\n功能:\n- 房源管理 (小区名称/栋单元号/户型)\n- 合同与租客管理\n- 缴费记录 (自动生成下次缴费时间)\n- 缴费周期: 月付/季付/半年付/年付\n- 数据仪表盘 (含缴费提醒)\n- 数据库备份与恢复\n- CSV 导入导出\n- 按楼栋统计/自定义时间统计\n\n技术栈: Python + Tkinter + SQLite")

    def _on_close(self):
        if messagebox.askokcancel("退出", "确定要退出系统吗?"):
            self.db.close()
            self.root.destroy()


class PropertyDialog:

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
        tk.Label(main_frame, text="房源信息",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        fields = [
            ("小区名称 *", "community_name", 1),
            ("地址 *", "address", 2),
            ("栋/单元/号", "building_unit_room", 3),
            ("类型", "property_type", 4),
            ("户型", "house_type", 5),
            ("面积 (m2)", "area", 6),
            ("月租金 *", "monthly_rent", 7),
            ("押金", "deposit", 8),
            ("状态", "status", 9),
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
        tk.Label(main_frame, text="描述",
                font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=10, column=0, sticky=tk.W, pady=4)
        self.desc_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.desc_text.grid(row=10, column=1, sticky=tk.W, pady=4)
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="确定", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy,
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
            messagebox.showwarning("验证失败", "小区名称不能为空")
            return
        if not data["address"]:
            messagebox.showwarning("验证失败", "地址不能为空")
            return
        if not data["monthly_rent"] or not validate_amount(data["monthly_rent"]):
            messagebox.showwarning("验证失败", "请输入有效的月租金")
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
        tk.Label(main_frame, text="租客信息",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        fields = [("姓名 *", "name", 1), ("电话 *", "phone", 2),
                  ("邮箱", "email", 3), ("身份证号", "id_card", 4),
                  ("紧急联系人", "emergency_contact", 5),
                  ("紧急电话", "emergency_phone", 6)]
        self.entries = {}
        for label, key, row in fields:
            tk.Label(main_frame, text=label, font=("Microsoft YaHei", 10),
                    bg=Theme.CARD, fg=Theme.TEXT).grid(row=row, column=0, sticky=tk.W, pady=4, padx=(0, 10))
            entry = ttk.Entry(main_frame, width=35)
            entry.grid(row=row, column=1, sticky=tk.W, pady=4)
            self.entries[key] = entry
        tk.Label(main_frame, text="备注", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=7, column=0, sticky=tk.W, pady=4)
        self.notes_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.notes_text.grid(row=7, column=1, sticky=tk.W, pady=4)
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="确定", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy,
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
            messagebox.showwarning("验证失败", "姓名不能为空")
            return
        if not data["phone"]:
            messagebox.showwarning("验证失败", "电话不能为空")
            return
        if data["email"] and not validate_email(data["email"]):
            messagebox.showwarning("验证失败", "邮箱格式不正确")
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
        tk.Label(main_frame, text="合同信息",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        tk.Label(main_frame, text="房源 *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.prop_combo = ttk.Combobox(main_frame, width=35, state="readonly")
        self.prop_combo.grid(row=1, column=1, sticky=tk.W, pady=4)
        self.prop_names = [f"{p.id} - {p.community_name} ({p.address})" for p in self.properties]
        self.prop_combo["values"] = self.prop_names
        tk.Label(main_frame, text="租客 *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.tenant_combo = ttk.Combobox(main_frame, width=35, state="readonly")
        self.tenant_combo.grid(row=2, column=1, sticky=tk.W, pady=4)
        self.tenant_names = [f"{t.id} - {t.name} ({t.phone})" for t in self.tenants]
        self.tenant_combo["values"] = self.tenant_names
        tk.Label(main_frame, text="起始日期 * (YYYY-MM-DD)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=3, column=0, sticky=tk.W, pady=4)
        self.start_entry = ttk.Entry(main_frame, width=35)
        self.start_entry.grid(row=3, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="结束日期 * (YYYY-MM-DD)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=4, column=0, sticky=tk.W, pady=4)
        self.end_entry = ttk.Entry(main_frame, width=35)
        self.end_entry.grid(row=4, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="月租金 *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=5, column=0, sticky=tk.W, pady=4)
        self.rent_entry = ttk.Entry(main_frame, width=35)
        self.rent_entry.grid(row=5, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="押金金额", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=6, column=0, sticky=tk.W, pady=4)
        self.deposit_entry = ttk.Entry(main_frame, width=35)
        self.deposit_entry.grid(row=6, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="每月缴费日 (1-28)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=7, column=0, sticky=tk.W, pady=4)
        self.pay_day_spin = ttk.Spinbox(main_frame, from_=1, to=28, width=32)
        self.pay_day_spin.grid(row=7, column=1, sticky=tk.W, pady=4)
        freq_frame = tk.Frame(main_frame, bg=Theme.CARD, highlightbackground=Theme.ACCENT,
                             highlightthickness=1, padx=10, pady=8)
        freq_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E, pady=8)
        tk.Label(freq_frame, text="缴费周期",
                font=("Microsoft YaHei", 11, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(0, 5))
        self.freq_var = tk.StringVar(value="月付")
        freq_row = tk.Frame(freq_frame, bg=Theme.CARD)
        freq_row.pack(fill=tk.X)
        for freq in ["月付", "季付", "半年付", "年付"]:
            rb = tk.Radiobutton(freq_row, text=freq, variable=self.freq_var, value=freq,
                               font=("Microsoft YaHei", 10),
                               bg=Theme.CARD, fg=Theme.TEXT,
                               selectcolor=Theme.ACCENT,
                               activebackground=Theme.CARD,
                               command=self._on_freq_change)
            rb.pack(side=tk.LEFT, padx=8)
        self.freq_amount_label = tk.Label(freq_frame, text="每期缴费金额: 0.00",
                                         font=("Microsoft YaHei", 10),
                                         bg=Theme.CARD, fg=Theme.SUCCESS)
        self.freq_amount_label.pack(anchor=tk.W, pady=(3, 0))
        self.rent_entry.bind("<KeyRelease>", self._on_freq_change)
        tk.Label(main_frame, text="备注", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=9, column=0, sticky=tk.W, pady=4)
        self.notes_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.notes_text.grid(row=9, column=1, sticky=tk.W, pady=4)
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="确定", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=8)

    def _on_freq_change(self, event=None):
        freq = self.freq_var.get()
        freq_map = {"月付": 1, "季付": 3, "半年付": 6, "年付": 12}
        months = freq_map.get(freq, 1)
        try:
            rent = float(self.rent_entry.get().strip() or 0)
            self.freq_amount_label.config(text=f"每期缴费金额: {format_currency(rent * months)} ({freq})")
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
            self.freq_var.set(self.lease.payment_frequency)
            self.notes_text.insert("1.0", self.lease.notes)
        else:
            self.pay_day_spin.set("1")
            self.freq_var.set("月付")
        self._on_freq_change()

    def _confirm(self):
        prop_idx = self.prop_combo.current()
        tenant_idx = self.tenant_combo.current()
        if prop_idx < 0:
            messagebox.showwarning("验证失败", "请选择房源")
            return
        if tenant_idx < 0:
            messagebox.showwarning("验证失败", "请选择租客")
            return
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        rent = self.rent_entry.get().strip()
        if not validate_date(start):
            messagebox.showwarning("验证失败", "起始日期格式不正确 (YYYY-MM-DD)")
            return
        if not validate_date(end):
            messagebox.showwarning("验证失败", "结束日期格式不正确 (YYYY-MM-DD)")
            return
        if not rent or not validate_amount(rent):
            messagebox.showwarning("验证失败", "请输入有效的月租金")
            return
        prop = self.properties[prop_idx]
        tenant = self.tenants[tenant_idx]
        self.result = Lease(
            id=self.lease.id, property_id=prop.id, tenant_id=tenant.id,
            property_name=prop.community_name, tenant_name=tenant.name,
            start_date=start, end_date=end,
            monthly_rent=float(rent),
            deposit_amount=float(self.deposit_entry.get().strip() or 0),
            payment_day=int(self.pay_day_spin.get()),
            payment_frequency=self.freq_var.get(),
            status="生效中", notes=self.notes_text.get("1.0", tk.END).strip()
        )
        self.dialog.destroy()


class PaymentDialog:

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
        tk.Label(main_frame, text="缴费记录",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        tk.Label(main_frame, text="关联合同 *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.lease_combo = ttk.Combobox(main_frame, width=35, state="readonly")
        self.lease_combo.grid(row=1, column=1, sticky=tk.W, pady=4)
        self.lease_names = [f"{l.id} - {l.property_name} / {l.tenant_name}" for l in self.leases]
        self.lease_combo["values"] = self.lease_names
        self.lease_combo.bind("<<ComboboxSelected>>", self._on_lease_selected)
        tk.Label(main_frame, text="金额 *", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.amount_entry = ttk.Entry(main_frame, width=35)
        self.amount_entry.grid(row=2, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="缴费日期 * (YYYY-MM-DD)", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=3, column=0, sticky=tk.W, pady=4)
        self.date_entry = ttk.Entry(main_frame, width=35)
        self.date_entry.grid(row=3, column=1, sticky=tk.W, pady=4)
        next_frame = tk.Frame(main_frame, bg=Theme.CARD, highlightbackground=Theme.SUCCESS,
                             highlightthickness=1, padx=10, pady=6)
        next_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=6)
        tk.Label(next_frame, text="下次缴费时间 (自动生成)",
                font=("Microsoft YaHei", 10, "bold"),
                bg=Theme.CARD, fg=Theme.SUCCESS).pack(anchor=tk.W)
        self.next_date_var = tk.StringVar(value="选择合同后自动生成")
        tk.Label(next_frame, textvariable=self.next_date_var,
                font=("Microsoft YaHei", 11),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(3, 0))
        tk.Label(main_frame, text="缴费类型", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=5, column=0, sticky=tk.W, pady=4)
        self.type_combo = ttk.Combobox(main_frame,
            values=["租金", "押金", "水费", "电费", "燃气费", "物业费", "其他"],
            state="readonly", width=32)
        self.type_combo.grid(row=5, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="缴费方式", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=6, column=0, sticky=tk.W, pady=4)
        self.method_combo = ttk.Combobox(main_frame,
            values=["微信支付", "支付宝", "银行转账", "现金", "其他"],
            state="readonly", width=32)
        self.method_combo.grid(row=6, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="状态", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=7, column=0, sticky=tk.W, pady=4)
        self.status_combo = ttk.Combobox(main_frame,
            values=["已支付", "待支付", "已逾期"],
            state="readonly", width=32)
        self.status_combo.grid(row=7, column=1, sticky=tk.W, pady=4)
        tk.Label(main_frame, text="备注", font=("Microsoft YaHei", 10),
                bg=Theme.CARD, fg=Theme.TEXT).grid(row=8, column=0, sticky=tk.W, pady=4)
        self.notes_text = tk.Text(main_frame, height=3, width=38, font=("Microsoft YaHei", 10))
        self.notes_text.grid(row=8, column=1, sticky=tk.W, pady=4)
        btn_frame = tk.Frame(main_frame, bg=Theme.CARD)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="确定", command=self._confirm,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                   style="Flat.TButton").pack(side=tk.LEFT, padx=8)

    def _on_lease_selected(self, event=None):
        idx = self.lease_combo.current()
        if idx >= 0:
            lease = self.leases[idx]
            next_date = lease.get_next_payment_date()
            amount = lease.get_payment_amount()
            if next_date:
                self.next_date_var.set(f"{next_date} (金额: {format_currency(amount)})")
            else:
                self.next_date_var.set("合同已到期或已结束")
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
            self.next_date_var.set(self.payment.next_payment_date or "未设置")
            self.type_combo.set(self.payment.payment_type)
            self.method_combo.set(self.payment.payment_method)
            self.status_combo.set(self.payment.status)
            self.notes_text.insert("1.0", self.payment.notes)
        else:
            self.date_entry.insert(0, get_today_str())
            self.type_combo.set("租金")
            self.method_combo.set("微信支付")
            self.status_combo.set("已支付")

    def _confirm(self):
        idx = self.lease_combo.current()
        if idx < 0:
            messagebox.showwarning("验证失败", "请选择关联合同")
            return
        amount = self.amount_entry.get().strip()
        date_str = self.date_entry.get().strip()
        if not amount or not validate_amount(amount):
            messagebox.showwarning("验证失败", "请输入有效的金额")
            return
        if not validate_date(date_str):
            messagebox.showwarning("验证失败", "日期格式不正确 (YYYY-MM-DD)")
            return
        lease = self.leases[idx]
        next_date = lease.get_next_payment_date()
        self.result = Payment(
            id=self.payment.id, lease_id=lease.id,
            tenant_name=lease.tenant_name, property_name=lease.property_name,
            amount=float(amount), payment_date=date_str,
            next_payment_date=next_date or "",
            payment_type=self.type_combo.get(),
            payment_method=self.method_combo.get(),
            status=self.status_combo.get(),
            notes=self.notes_text.get("1.0", tk.END).strip()
        )
        self.dialog.destroy()


class LeaseDetailDialog:

    def __init__(self, parent, lease: Lease):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"合同详情 - {lease.property_name} / {lease.tenant_name}")
        self.dialog.geometry("520x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=Theme.CARD)
        main_frame = tk.Frame(self.dialog, bg=Theme.CARD, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="合同详情",
                font=("Microsoft YaHei", 14, "bold"),
                bg=Theme.CARD, fg=Theme.PRIMARY).pack(anchor=tk.W, pady=(0, 10))
        info = [
            ("合同编号", str(lease.id)),
            ("房源", lease.property_name),
            ("租客", lease.tenant_name),
            ("起始日期", lease.start_date),
            ("结束日期", lease.end_date),
            ("合同期限", f"{lease.duration_days} 天"),
            ("月租金", format_currency(lease.monthly_rent)),
            ("押金", format_currency(lease.deposit_amount)),
            ("缴费周期", lease.payment_frequency),
            ("每期金额", format_currency(lease.get_payment_amount())),
            ("下次缴费日", lease.get_next_payment_date() or "已到期"),
            ("每月缴费日", f"每月 {lease.payment_day} 日"),
            ("状态", lease.status),
            ("备注", lease.notes or "无"),
        ]
        for i, (label, value) in enumerate(info):
            row_frame = tk.Frame(main_frame, bg=Theme.CARD)
            row_frame.pack(fill=tk.X, pady=1)
            tk.Label(row_frame, text=f"{label}:",
                    font=("Microsoft YaHei", 10, "bold"),
                    bg=Theme.CARD, fg=Theme.PRIMARY,
                    width=12, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row_frame, text=value,
                    font=("Microsoft YaHei", 10),
                    bg=Theme.CARD, fg=Theme.TEXT).pack(side=tk.LEFT)
        ttk.Button(main_frame, text="关闭", command=self.dialog.destroy,
                   style="Flat.TButton").pack(pady=(15, 0))


if __name__ == "__main__":
    root = tk.Tk()
    app = RentalManagementApp(root)
    root.mainloop()
