"""房屋租赁管理系统 - 数据模型定义"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Property:
    """房源信息"""
    id: Optional[int] = None
    name: str = ""
    address: str = ""
    property_type: str = "住宅"          # 住宅/商铺/写字楼/公寓
    bedrooms: int = 0
    bathrooms: int = 0
    area: float = 0.0                   # 面积（平方米）
    monthly_rent: float = 0.0           # 月租金
    deposit: float = 0.0               # 押金
    status: str = "待出租"              # 待出租/已出租/已下架
    description: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_tuple(self) -> tuple:
        return (self.name, self.address, self.property_type, self.bedrooms,
                self.bathrooms, self.area, self.monthly_rent, self.deposit,
                self.status, self.description)

    @staticmethod
    def from_row(row: tuple) -> "Property":
        return Property(
            id=row[0], name=row[1], address=row[2],
            property_type=row[3], bedrooms=row[4], bathrooms=row[5],
            area=row[6], monthly_rent=row[7], deposit=row[8],
            status=row[9], description=row[10],
            created_at=row[11], updated_at=row[12]
        )


@dataclass
class Tenant:
    """租客信息"""
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: str = ""
    id_card: str = ""                   # 身份证号
    emergency_contact: str = ""         # 紧急联系人
    emergency_phone: str = ""           # 紧急联系电话
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


@dataclass
class Lease:
    """租赁合同"""
    id: Optional[int] = None
    property_id: int = 0
    tenant_id: int = 0
    property_name: str = ""             # 冗余字段，便于显示
    tenant_name: str = ""               # 冗余字段，便于显示
    start_date: str = ""
    end_date: str = ""
    monthly_rent: float = 0.0
    deposit_amount: float = 0.0
    payment_day: int = 1                # 每月几号交租
    status: str = "生效中"              # 生效中/已到期/已解约
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

    @staticmethod
    def from_row(row: tuple) -> "Lease":
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
    tenant_name: str = ""               # 冗余字段，便于显示
    property_name: str = ""             # 冗余字段，便于显示
    amount: float = 0.0
    payment_date: str = ""
    payment_type: str = "租金"           # 租金/押金/水费/电费/燃气费/物业费/其他
    payment_method: str = "微信支付"     # 微信支付/支付宝/银行转账/现金/其他
    status: str = "已支付"              # 已支付/待支付/已逾期
    notes: str = ""
    created_at: str = ""

    @staticmethod
    def from_row(row: tuple) -> "Payment":
        return Payment(
            id=row[0], lease_id=row[1], tenant_name=row[2],
            property_name=row[3], amount=row[4], payment_date=row[5],
            payment_type=row[6], payment_method=row[7],
            status=row[8], notes=row[9], created_at=row[10]
        )
