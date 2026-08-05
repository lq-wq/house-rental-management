"""房屋租赁管理系统 - 数据模型定义"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from calendar import monthrange


@dataclass
class Property:
    """房源信息"""
    id: Optional[int] = None
    community_name: str = ""          # 小区名称（原 name）
    address: str = ""                 # 地址
    building_unit_room: str = ""      # 几栋几单元几号（新增）
    property_type: str = "住宅"       # 住宅/商铺/写字楼/公寓
    house_type: str = "一室一厅一卫"  # 户型（新增，替代 bedrooms/bathrooms）
    area: float = 0.0                 # 面积（平方米）
    monthly_rent: float = 0.0         # 月租金
    deposit: float = 0.0              # 押金
    status: str = "待出租"
    description: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_tuple(self) -> tuple:
        return (self.community_name, self.address, self.building_unit_room,
                self.property_type, self.house_type, self.area,
                self.monthly_rent, self.deposit, self.status, self.description)

    @staticmethod
    def from_row(row: tuple) -> "Property":
        return Property(
            id=row[0], community_name=row[1], address=row[2],
            building_unit_room=row[3] if len(row) > 3 and row[3] else "",
            property_type=row[4] if len(row) > 4 else "住宅",
            house_type=row[5] if len(row) > 5 else "一室一厅一卫",
            area=row[6] if len(row) > 6 else 0.0,
            monthly_rent=row[7] if len(row) > 7 else 0.0,
            deposit=row[8] if len(row) > 8 else 0.0,
            status=row[9] if len(row) > 9 else "待出租",
            description=row[10] if len(row) > 10 else "",
            created_at=row[11] if len(row) > 11 else "",
            updated_at=row[12] if len(row) > 12 else ""
        )


@dataclass
class Tenant:
    """租客信息"""
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: str = ""
    id_card: str = ""
    emergency_contact: str = ""
    emergency_phone: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_tuple(self) -> tuple:
        return (self.name, self.phone, self.email, self.id_card,
                self.emergency_contact, self.emergency_phone, self.notes)

    @staticmethod
    def from_row(row: tuple) -> "Tenant":
        return Tenant(
            id=row[0], name=row[1], phone=row[2], email=row[3],
            id_card=row[4], emergency_contact=row[5],
            emergency_phone=row[6], notes=row[7],
            created_at=row[8], updated_at=row[9]
        )


# 缴费频率常量
PAYMENT_FREQUENCIES = ["月付", "季付", "半年付", "年付"]
FREQUENCY_MONTHS = {"月付": 1, "季付": 3, "半年付": 6, "年付": 12}

# 户型列表
HOUSE_TYPES = [
    "开间", "一室一厅一卫", "一室一厅二卫", "二室一厅一卫",
    "二室一厅二卫", "二室二厅一卫", "二室二厅二卫",
    "三室一厅一卫", "三室一厅二卫", "三室二厅一卫", "三室二厅二卫",
    "四室二厅一卫", "四室二厅二卫", "四室及以上", "其他"
]


@dataclass
class Lease:
    """租赁合同"""
    id: Optional[int] = None
    property_id: int = 0
    tenant_id: int = 0
    property_name: str = ""
    tenant_name: str = ""
    start_date: str = ""
    end_date: str = ""
    monthly_rent: float = 0.0
    deposit_amount: float = 0.0
    payment_day: int = 1
    payment_frequency: str = "月付"
    status: str = "生效中"
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @property
    def duration_days(self) -> int:
        if self.start_date and self.end_date:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            return (end - start).days
        return 0

    def get_next_payment_date(self) -> Optional[str]:
        """计算下次缴费日期"""
        if not self.start_date or self.status != "生效中":
            return None
        start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        today = date.today()
        freq_months = FREQUENCY_MONTHS.get(self.payment_frequency, 1)

        total_months = (today.year - start.year) * 12 + (today.month - start.month)
        if today.day < self.payment_day:
            total_months -= 1

        periods_passed = total_months // freq_months
        next_period_start_month = start.month + (periods_passed + 1) * freq_months
        next_year = start.year + (next_period_start_month - 1) // 12
        next_month = (next_period_start_month - 1) % 12 + 1

        last_day = monthrange(next_year, next_month)[1]
        day = min(self.payment_day, last_day)
        next_date = date(next_year, next_month, day)

        end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        if next_date > end:
            return None

        return next_date.strftime("%Y-%m-%d")

    def get_payment_amount(self) -> float:
        """获取每期缴费金额"""
        freq_months = FREQUENCY_MONTHS.get(self.payment_frequency, 1)
        return self.monthly_rent * freq_months

    def get_days_until_next_payment(self) -> Optional[int]:
        """距离下次缴费还有多少天"""
        next_date_str = self.get_next_payment_date()
        if not next_date_str:
            return None
        next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
        delta = (next_date - date.today()).days
        return delta

    @staticmethod
    def from_row(row: tuple) -> "Lease":
        if len(row) >= 15:
            return Lease(
                id=row[0], property_id=row[1], tenant_id=row[2],
                property_name=row[3], tenant_name=row[4],
                start_date=row[5], end_date=row[6],
                monthly_rent=row[7], deposit_amount=row[8],
                payment_day=row[9], payment_frequency=row[10], status=row[11],
                notes=row[12], created_at=row[13], updated_at=row[14]
            )
        else:
            return Lease(
                id=row[0], property_id=row[1], tenant_id=row[2],
                property_name=row[3], tenant_name=row[4],
                start_date=row[5], end_date=row[6],
                monthly_rent=row[7], deposit_amount=row[8],
                payment_day=row[9], status=row[10],
                notes=row[11], created_at=row[12], updated_at=row[13]
            )


@dataclass
class Payment:
    """缴费记录"""
    id: Optional[int] = None
    lease_id: int = 0
    tenant_name: str = ""
    property_name: str = ""
    amount: float = 0.0
    payment_date: str = ""
    next_payment_date: str = ""       # 新增：下次缴费时间（自动生成）
    payment_type: str = "租金"
    payment_method: str = "微信支付"
    status: str = "已支付"
    notes: str = ""
    created_at: str = ""

    @staticmethod
    def from_row(row: tuple) -> "Payment":
        if len(row) >= 12:
            return Payment(
                id=row[0], lease_id=row[1], tenant_name=row[2],
                property_name=row[3], amount=row[4], payment_date=row[5],
                next_payment_date=row[6] if row[6] else "",
                payment_type=row[7], payment_method=row[8],
                status=row[9], notes=row[10], created_at=row[11]
            )
        else:
            return Payment(
                id=row[0], lease_id=row[1], tenant_name=row[2],
                property_name=row[3], amount=row[4], payment_date=row[5],
                payment_type=row[6], payment_method=row[7],
                status=row[8], notes=row[9], created_at=row[10]
            )
