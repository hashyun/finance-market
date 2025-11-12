"""
실시간 알림 시스템
"""
from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod


class NotificationLevel(Enum):
    """알림 레벨"""
    INFO = "INFO"
    WARNING = "WARNING"
    ALERT = "ALERT"
    ERROR = "ERROR"


@dataclass
class Notification:
    """알림 데이터"""
    level: NotificationLevel
    title: str
    message: str
    timestamp: str
    data: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class NotificationChannel(ABC):
    """알림 채널 추상 클래스"""

    @abstractmethod
    def send(self, notification: Notification):
        """알림 전송"""
        pass


class Notifier:
    """
    알림 관리자
    여러 채널을 통해 알림 전송
    """

    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self.notification_history: List[Notification] = []

    def add_channel(self, channel: NotificationChannel):
        """알림 채널 추가"""
        self.channels.append(channel)

    def remove_channel(self, channel: NotificationChannel):
        """알림 채널 제거"""
        if channel in self.channels:
            self.channels.remove(channel)

    def notify(
        self,
        level: NotificationLevel,
        title: str,
        message: str,
        data: Dict[str, Any] = None
    ):
        """
        알림 전송

        Args:
            level: 알림 레벨
            title: 제목
            message: 메시지
            data: 추가 데이터
        """
        notification = Notification(
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            data=data or {}
        )

        # 히스토리에 저장
        self.notification_history.append(notification)

        # 모든 채널로 전송
        for channel in self.channels:
            try:
                channel.send(notification)
            except Exception as e:
                print(f"[알림 전송 실패] {channel.__class__.__name__}: {e}")

    def info(self, title: str, message: str, data: Dict = None):
        """정보 알림"""
        self.notify(NotificationLevel.INFO, title, message, data)

    def warning(self, title: str, message: str, data: Dict = None):
        """경고 알림"""
        self.notify(NotificationLevel.WARNING, title, message, data)

    def alert(self, title: str, message: str, data: Dict = None):
        """중요 알림"""
        self.notify(NotificationLevel.ALERT, title, message, data)

    def error(self, title: str, message: str, data: Dict = None):
        """오류 알림"""
        self.notify(NotificationLevel.ERROR, title, message, data)

    def get_history(self, level: NotificationLevel = None, limit: int = 100) -> List[Notification]:
        """
        알림 히스토리 조회

        Args:
            level: 특정 레벨만 조회 (None이면 전체)
            limit: 최대 개수

        Returns:
            알림 리스트
        """
        if level:
            filtered = [n for n in self.notification_history if n.level == level]
        else:
            filtered = self.notification_history

        return filtered[-limit:]

    def clear_history(self):
        """히스토리 초기화"""
        self.notification_history.clear()
