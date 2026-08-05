"""房屋租赁管理系统 - 工具函数"""
import re
from datetime import datetime, date


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    return bool(re.match(r'^1[3-9]\d{9}$', phone))


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))


def validate_id_card(id_card: str) -> bool:
    """验证身份证号（18位）"""
    return bool(re.match(r'^\d{17}[\dXx]$', id_card))


def validate_amount(amount: str) -> bool:
    """验证金额格式"""
    try:
        val = float(amount)
        return val >= 0
    except ValueError:
        return False


def validate_date(date_str: str) -> bool:
    """验证日期格式 YYYY-MM-DD"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_currency(amount: float) -> str:
    """格式化金额"""
    return f"¥{amount:,.2f}"


def get_status_color(status: str) -> str:
    """根据状态返回颜色"""
    colors = {
        "待出租": "#2196F3",
        "已出租": "#4CAF50",
        "已下架": "#9E9E9E",
        "生效中": "#4CAF50",
        "已到期": "#FF9800",
        "已解约": "#F44336",
        "已支付": "#4CAF50",
        "待支付": "#FF9800",
        "已逾期": "#F44336",
    }
    return colors.get(status, "#000000")


def get_today_str() -> str:
    """获取今天的日期字符串"""
    return date.today().strftime("%Y-%m-%d")


def get_current_month_str() -> str:
    """获取当前月份字符串"""
    return date.today().strftime("%Y-%m")
