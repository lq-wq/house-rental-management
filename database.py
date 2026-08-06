"""房屋租赁管理系统 - 数据库操作层"""
import sqlite3
import os
import shutil
from datetime import datetime, date
from typing import List, Optional, Tuple
from models import Property, Tenant, Lease, Payment, PAYMENT_FREQUENCIES


def get_data_dir() -> str:
    """获取用户数据目录（保证数据持久化，不受 PyInstaller 临时目录影响）"""
    if os.name == 'nt':  # Windows
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    else:
        base = os.path.expanduser('~')
    data_dir = os.path.join(base, '房屋租赁管理系统')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


DB_PATH = os.path.join(get_data_dir(), "rental_management.db")


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
        # 迁移旧数据库
        self._migrate_old_db()
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._migrate_schema()

    def _migrate_old_db(self):
        """将旧位置（程序目录）的数据库迁移到新位置（用户文档目录）"""
        old_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rental_management.db")
        if os.path.exists(old_path) and not os.path.exists(DB_PATH):
            shutil.copy2(old_path, DB_PATH)
            print(f"数据库已从 {old_path} 迁移到 {DB_PATH}")
        # 也检查当前工作目录
        cwd_path = os.path.join(os.getcwd(), "rental_management.db")
        if os.path.exists(cwd_path) and not os.path.exists(DB_PATH):
            shutil.copy2(cwd_path, DB_PATH)
            print(f"数据库已从 {cwd_path} 迁移到 {DB_PATH}")

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

    def _migrate_schema(self):
        """数据库迁移：兼容旧表结构"""
        cursor = self.conn.cursor()

        # 检查 building_unit_room
        try:
            cursor.execute("SELECT building_unit_room FROM properties LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE properties ADD COLUMN building_unit_room TEXT DEFAULT ''")
            self.conn.commit()

        # 检查 house_type
        try:
            cursor.execute("SELECT house_type FROM properties LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE properties ADD COLUMN house_type TEXT DEFAULT '一室一厅一卫'")
            self.conn.commit()

        # 检查 payment_frequency
        try:
            cursor.execute("SELECT payment_frequency FROM leases LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE leases ADD COLUMN payment_frequency TEXT DEFAULT '月付'")
            self.conn.commit()

        # 检查 next_payment_date
        try:
            cursor.execute("SELECT next_payment_date FROM payments LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE payments ADD COLUMN next_payment_date TEXT DEFAULT ''")
            self.conn.commit()

        # 检查 community_name，兼容旧表 name 字段
        try:
            cursor.execute("SELECT community_name FROM properties LIMIT 1")
        except sqlite3.OperationalError:
            try:
                cursor.execute("SELECT name FROM properties LIMIT 1")
                cursor.execute("ALTER TABLE properties RENAME COLUMN name TO community_name")
                self.conn.commit()
            except sqlite3.OperationalError:
                pass

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

    # ==================== 新增：按楼栋统计 ====================

    def get_building_statistics(self) -> List[dict]:
        """按楼栋（栋/单元/号 的第一段）统计房源和收入"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN building_unit_room != '' AND building_unit_room IS NOT NULL 
                    THEN substr(building_unit_room, 1, instr(building_unit_room || '栋', '栋') - 1) || '栋'
                    ELSE '未指定楼栋'
                END as building,
                COUNT(*) as total_properties,
                SUM(CASE WHEN status='已出租' THEN 1 ELSE 0 END) as rented_count,
                SUM(CASE WHEN status='待出租' THEN 1 ELSE 0 END) as available_count,
                COALESCE(SUM(monthly_rent), 0) as total_rent
            FROM properties
            GROUP BY building
            ORDER BY building
        """)
        results = []
        for row in cursor.fetchall():
            results.append({
                "building": row[0],
                "total_properties": row[1],
                "rented_count": row[2],
                "available_count": row[3],
                "total_rent": row[4]
            })
        return results

    # ==================== 新增：自定义时间统计 ====================

    def get_custom_time_statistics(self, start_date: str, end_date: str) -> dict:
        """按自定义时间范围统计"""
        cursor = self.conn.cursor()
        result = {}

        # 时间段内收款总额
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) 
            FROM payments 
            WHERE payment_date >= ? AND payment_date <= ? AND status='已支付'
        """, (start_date, end_date))
        result["total_income"] = cursor.fetchone()[0]

        # 时间段内各类型收款
        cursor.execute("""
            SELECT payment_type, COALESCE(SUM(amount), 0)
            FROM payments
            WHERE payment_date >= ? AND payment_date <= ? AND status='已支付'
            GROUP BY payment_type
            ORDER BY payment_type
        """, (start_date, end_date))
        result["income_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

        # 时间段内收款笔数
        cursor.execute("""
            SELECT COUNT(*) FROM payments
            WHERE payment_date >= ? AND payment_date <= ? AND status='已支付'
        """, (start_date, end_date))
        result["payment_count"] = cursor.fetchone()[0]

        # 时间段内逾期笔数
        cursor.execute("""
            SELECT COUNT(*) FROM payments
            WHERE payment_date >= ? AND payment_date <= ? AND status='已逾期'
        """, (start_date, end_date))
        result["overdue_count"] = cursor.fetchone()[0]

        # 时间段内新增合同数
        cursor.execute("""
            SELECT COUNT(*) FROM leases
            WHERE created_at >= ? AND created_at <= ?
        """, (start_date, end_date))
        result["new_leases"] = cursor.fetchone()[0]

        # 时间段内新增房源数
        cursor.execute("""
            SELECT COUNT(*) FROM properties
            WHERE created_at >= ? AND created_at <= ?
        """, (start_date, end_date))
        result["new_properties"] = cursor.fetchone()[0]

        return result

    # ==================== 新增：备份和导入导出 ====================

    def backup_database(self) -> str:
        """备份数据库到备份目录"""
        backup_dir = os.path.join(get_data_dir(), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
        shutil.copy2(DB_PATH, backup_path)
        return backup_path

    def list_backups(self) -> List[Tuple[str, str, float]]:
        """列出所有备份文件"""
        backup_dir = os.path.join(get_data_dir(), "backup")
        if not os.path.exists(backup_dir):
            return []
        backups = []
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith(".db"):
                fpath = os.path.join(backup_dir, f)
                size = os.path.getsize(fpath) / 1024  # KB
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                backups.append((fpath, mtime.strftime("%Y-%m-%d %H:%M:%S"), size))
        return backups

    def restore_database(self, backup_path: str) -> bool:
        """从备份文件恢复数据库"""
        if not os.path.exists(backup_path):
            return False
        # 先备份当前数据库
        self.backup_database()
        # 关闭当前连接
        self.conn.close()
        # 恢复
        shutil.copy2(backup_path, DB_PATH)
        # 重新连接
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        return True

    def export_to_csv(self, table: str, filepath: str) -> bool:
        """导出指定表到 CSV 文件"""
        import csv
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if not rows:
                return False
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([desc[0] for desc in cursor.description])
                for row in rows:
                    writer.writerow(row)
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

    def import_from_csv(self, table: str, filepath: str) -> int:
        """从 CSV 文件导入到指定表"""
        import csv
        try:
            cursor = self.conn.cursor()
            # 获取表列信息（排除 id 自增列）
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall() if row[1] != 'id']

            count = 0
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    placeholders = ', '.join(['?'] * len(columns))
                    col_names = ', '.join(columns)
                    values = [row.get(col, '') for col in columns]
                    cursor.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values)
                    count += 1
            self.conn.commit()
            return count
        except Exception as e:
            print(f"导入失败: {e}")
            return 0

    def get_db_path(self) -> str:
        """获取数据库路径"""
        return DB_PATH

    def get_data_dir(self) -> str:
        """获取数据目录"""
        return get_data_dir()

    def close(self):
        if self.conn:
            self.conn.close()
