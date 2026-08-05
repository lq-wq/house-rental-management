"""房屋租赁管理系统 - 数据库操作层"""
import sqlite3
import os
from datetime import datetime, date
from typing import List, Optional, Tuple
from models import Property, Tenant, Lease, Payment, PAYMENT_FREQUENCIES


DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "rental_management.db")


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._migrate()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                community_name TEXT DEFAULT '',
                address TEXT NOT NULL,
                building_unit_room TEXT DEFAULT '',
                property_type TEXT DEFAULT '住宅',
                house_type TEXT DEFAULT '一室一厅一卫',
                area REAL DEFAULT 0,
                monthly_rent REAL DEFAULT 0,
                deposit REAL DEFAULT 0,
                status TEXT DEFAULT '待出租',
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT DEFAULT '',
                id_card TEXT DEFAULT '',
                emergency_contact TEXT DEFAULT '',
                emergency_phone TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS leases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                tenant_id INTEGER NOT NULL,
                property_name TEXT DEFAULT '',
                tenant_name TEXT DEFAULT '',
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                monthly_rent REAL DEFAULT 0,
                deposit_amount REAL DEFAULT 0,
                payment_day INTEGER DEFAULT 1,
                payment_frequency TEXT DEFAULT '月付',
                status TEXT DEFAULT '生效中',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (property_id) REFERENCES properties(id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lease_id INTEGER NOT NULL,
                tenant_name TEXT DEFAULT '',
                property_name TEXT DEFAULT '',
                amount REAL DEFAULT 0,
                payment_date TEXT NOT NULL,
                next_payment_date TEXT DEFAULT '',
                payment_type TEXT DEFAULT '租金',
                payment_method TEXT DEFAULT '微信支付',
                status TEXT DEFAULT '已支付',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (lease_id) REFERENCES leases(id)
            );

            CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status);
            CREATE INDEX IF NOT EXISTS idx_leases_status ON leases(status);
            CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date);
            CREATE INDEX IF NOT EXISTS idx_payments_lease ON payments(lease_id);
        """)
        self.conn.commit()

    def _migrate(self):
        """数据库迁移：兼容旧表结构"""
        cursor = self.conn.cursor()
        # 检查旧表字段（name -> community_name）
        try:
            cursor.execute("SELECT community_name FROM properties LIMIT 1")
        except sqlite3.OperationalError:
            try:
                # 旧表有 name 字段，迁移到新字段
                cursor.execute("SELECT name FROM properties LIMIT 1")
                cursor.execute("ALTER TABLE properties RENAME COLUMN name TO community_name")
                self.conn.commit()
                print("迁移: properties.name -> community_name")
            except sqlite3.OperationalError:
                pass

        # 检查 building_unit_room
        try:
            cursor.execute("SELECT building_unit_room FROM properties LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE properties ADD COLUMN building_unit_room TEXT DEFAULT ''")
            self.conn.commit()
            print("迁移: properties 添加 building_unit_room")

        # 检查 house_type
        try:
            cursor.execute("SELECT house_type FROM properties LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE properties ADD COLUMN house_type TEXT DEFAULT '一室一厅一卫'")
            self.conn.commit()
            print("迁移: properties 添加 house_type")

        # 检查 payment_frequency
        try:
            cursor.execute("SELECT payment_frequency FROM leases LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE leases ADD COLUMN payment_frequency TEXT DEFAULT '月付'")
            self.conn.commit()
            print("迁移: leases 添加 payment_frequency")

        # 检查 next_payment_date
        try:
            cursor.execute("SELECT next_payment_date FROM payments LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE payments ADD COLUMN next_payment_date TEXT DEFAULT ''")
            self.conn.commit()
            print("迁移: payments 添加 next_payment_date")

    # ==================== 房源操作 ====================

    def add_property(self, prop: Property) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO properties (community_name, address, building_unit_room,
                property_type, house_type, area, monthly_rent, deposit, status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, prop.to_tuple())
        self.conn.commit()
        return cursor.lastrowid

    def update_property(self, prop: Property) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE properties SET community_name=?, address=?, building_unit_room=?,
                property_type=?, house_type=?, area=?, monthly_rent=?, deposit=?,
                status=?, description=?, updated_at=datetime('now','localtime')
            WHERE id=?
        """, (*prop.to_tuple(), prop.id))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_property(self, prop_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM properties WHERE id=?", (prop_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_property(self, prop_id: int) -> Optional[Property]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM properties WHERE id=?", (prop_id,))
        row = cursor.fetchone()
        return Property.from_row(tuple(row)) if row else None

    def search_properties(self, keyword: str = "", status: str = "") -> List[Property]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM properties WHERE 1=1"
        params = []
        if keyword:
            query += " AND (community_name LIKE ? OR address LIKE ? OR building_unit_room LIKE ? OR description LIKE ?)"
            params.extend([f"%{keyword}%"] * 4)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY updated_at DESC"
        cursor.execute(query, params)
        return [Property.from_row(tuple(row)) for row in cursor.fetchall()]

    def get_all_properties(self) -> List[Property]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM properties ORDER BY updated_at DESC")
        return [Property.from_row(tuple(row)) for row in cursor.fetchall()]

    # ==================== 租客操作 ====================

    def add_tenant(self, tenant: Tenant) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tenants (name, phone, email, id_card, emergency_contact,
                                 emergency_phone, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tenant.to_tuple())
        self.conn.commit()
        return cursor.lastrowid

    def update_tenant(self, tenant: Tenant) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tenants SET name=?, phone=?, email=?, id_card=?,
                emergency_contact=?, emergency_phone=?, notes=?,
                updated_at=datetime('now','localtime')
            WHERE id=?
        """, (*tenant.to_tuple(), tenant.id))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_tenant(self, tenant_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tenants WHERE id=?", (tenant_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_tenant(self, tenant_id: int) -> Optional[Tenant]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,))
        row = cursor.fetchone()
        return Tenant.from_row(row) if row else None

    def search_tenants(self, keyword: str = "") -> List[Tenant]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM tenants WHERE 1=1"
        params = []
        if keyword:
            query += " AND (name LIKE ? OR phone LIKE ? OR id_card LIKE ? OR notes LIKE ?)"
            params.extend([f"%{keyword}%"] * 4)
        query += " ORDER BY updated_at DESC"
        cursor.execute(query, params)
        return [Tenant.from_row(row) for row in cursor.fetchall()]

    def get_all_tenants(self) -> List[Tenant]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tenants ORDER BY updated_at DESC")
        return [Tenant.from_row(row) for row in cursor.fetchall()]

    # ==================== 合同操作 ====================

    def add_lease(self, lease: Lease) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO leases (property_id, tenant_id, property_name, tenant_name,
                                start_date, end_date, monthly_rent, deposit_amount,
                                payment_day, payment_frequency, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (lease.property_id, lease.tenant_id, lease.property_name,
              lease.tenant_name, lease.start_date, lease.end_date,
              lease.monthly_rent, lease.deposit_amount, lease.payment_day,
              lease.payment_frequency, lease.status, lease.notes))
        self.conn.commit()
        cursor.execute("UPDATE properties SET status='已出租', updated_at=datetime('now','localtime') WHERE id=?", (lease.property_id,))
        self.conn.commit()
        return cursor.lastrowid

    def update_lease(self, lease: Lease) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE leases SET property_id=?, tenant_id=?, property_name=?,
                tenant_name=?, start_date=?, end_date=?, monthly_rent=?,
                deposit_amount=?, payment_day=?, payment_frequency=?, status=?, notes=?,
                updated_at=datetime('now','localtime')
            WHERE id=?
        """, (lease.property_id, lease.tenant_id, lease.property_name,
              lease.tenant_name, lease.start_date, lease.end_date,
              lease.monthly_rent, lease.deposit_amount, lease.payment_day,
              lease.payment_frequency, lease.status, lease.notes, lease.id))
        self.conn.commit()
        return cursor.rowcount > 0

    def terminate_lease(self, lease_id: int) -> bool:
        cursor = self.conn.cursor()
        lease = self.get_lease(lease_id)
        if not lease:
            return False
        cursor.execute("UPDATE leases SET status='已解约', updated_at=datetime('now','localtime') WHERE id=?", (lease_id,))
        cursor.execute("UPDATE properties SET status='待出租', updated_at=datetime('now','localtime') WHERE id=?", (lease.property_id,))
        self.conn.commit()
        return True

    def delete_lease(self, lease_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM leases WHERE id=?", (lease_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_lease(self, lease_id: int) -> Optional[Lease]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leases WHERE id=?", (lease_id,))
        row = cursor.fetchone()
        if row:
            return Lease.from_row(tuple(row))
        return None

    def search_leases(self, keyword: str = "", status: str = "") -> List[Lease]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM leases WHERE 1=1"
        params = []
        if keyword:
            query += " AND (property_name LIKE ? OR tenant_name LIKE ? OR notes LIKE ?)"
            params.extend([f"%{keyword}%"] * 3)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY updated_at DESC"
        cursor.execute(query, params)
        return [Lease.from_row(tuple(row)) for row in cursor.fetchall()]

    def get_all_leases(self) -> List[Lease]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leases ORDER BY updated_at DESC")
        return [Lease.from_row(tuple(row)) for row in cursor.fetchall()]

    def get_active_leases_with_reminders(self) -> List[Lease]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leases WHERE status='生效中' ORDER BY updated_at DESC")
        return [Lease.from_row(tuple(row)) for row in cursor.fetchall()]

    # ==================== 缴费操作 ====================

    def add_payment(self, payment: Payment) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO payments (lease_id, tenant_name, property_name, amount,
                                  payment_date, next_payment_date, payment_type,
                                  payment_method, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (payment.lease_id, payment.tenant_name, payment.property_name,
              payment.amount, payment.payment_date, payment.next_payment_date,
              payment.payment_type, payment.payment_method, payment.status, payment.notes))
        self.conn.commit()
        return cursor.lastrowid

    def update_payment(self, payment: Payment) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE payments SET lease_id=?, tenant_name=?, property_name=?,
                amount=?, payment_date=?, next_payment_date=?, payment_type=?,
                payment_method=?, status=?, notes=?
            WHERE id=?
        """, (payment.lease_id, payment.tenant_name, payment.property_name,
              payment.amount, payment.payment_date, payment.next_payment_date,
              payment.payment_type, payment.payment_method, payment.status,
              payment.notes, payment.id))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_payment(self, payment_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM payments WHERE id=?", (payment_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def search_payments(self, keyword: str = "", start_date: str = "",
                        end_date: str = "", payment_type: str = "") -> List[Payment]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM payments WHERE 1=1"
        params = []
        if keyword:
            query += " AND (tenant_name LIKE ? OR property_name LIKE ? OR notes LIKE ?)"
            params.extend([f"%{keyword}%"] * 3)
        if start_date:
            query += " AND payment_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND payment_date <= ?"
            params.append(end_date)
        if payment_type:
            query += " AND payment_type=?"
            params.append(payment_type)
        query += " ORDER BY payment_date DESC"
        cursor.execute(query, params)
        return [Payment.from_row(row) for row in cursor.fetchall()]

    def get_all_payments(self) -> List[Payment]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM payments ORDER BY payment_date DESC")
        return [Payment.from_row(row) for row in cursor.fetchall()]

    # ==================== 统计功能 ====================

    def get_statistics(self) -> dict:
        cursor = self.conn.cursor()
        stats = {}

        cursor.execute("SELECT COUNT(*) FROM properties")
        stats["total_properties"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM properties WHERE status='待出租'")
        stats["available_properties"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM properties WHERE status='已出租'")
        stats["rented_properties"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tenants")
        stats["total_tenants"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leases WHERE status='生效中'")
        stats["active_leases"] = cursor.fetchone()[0]

        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_date LIKE ? AND status='已支付'",
            (f"{current_month}%",)
        )
        stats["monthly_income"] = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='已支付'")
        stats["total_income"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM payments WHERE status='已逾期'")
        stats["overdue_payments"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leases WHERE status='生效中'")
        stats["active_lease_count"] = cursor.fetchone()[0]

        stats["due_this_month"] = self._count_due_this_month()

        return stats

    def _count_due_this_month(self) -> int:
        from models import Lease as L
        count = 0
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leases WHERE status='生效中'")
        for row in cursor.fetchall():
            lease = L.from_row(tuple(row))
            days = lease.get_days_until_next_payment()
            if days is not None and 0 <= days <= 7:
                count += 1
        return count

    def get_monthly_income_report(self, year: int) -> List[Tuple[str, float]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT substr(payment_date, 1, 7) as month, COALESCE(SUM(amount), 0)
            FROM payments
            WHERE payment_date LIKE ? AND status='已支付'
            GROUP BY month
            ORDER BY month
        """, (f"{year}%",))
        return cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
