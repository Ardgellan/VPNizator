from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class UserInfo:
    user_id: int
    username: str
    is_not_banned: str
    created_at: datetime


@dataclass
class VpnConfigDB:
    config_id: int
    user_id: int
    config_name: str
    config_uuid: str


@dataclass
class VpnConfigDB_N:
    config_id: int
    user_id: int
    config_name: str
    config_uuid: str
    country_code: str


class SubscriptionStatus(Enum):
    expired = "EXPIRED"
    last_day_left = "LAST_DAY_LEFT"


@dataclass
class GlobalStatistics:
    users_registered: int
    users_banned: int
    active_configs_count: int
