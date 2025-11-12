"""
다양한 알림 채널 구현
"""
import os
from datetime import datetime
from .notifier import NotificationChannel, Notification, NotificationLevel


class ConsoleChannel(NotificationChannel):
    """콘솔 출력 채널"""

    def __init__(self, colored: bool = True):
        self.colored = colored

    def send(self, notification: Notification):
        """콘솔에 출력"""
        # 레벨별 색상 (ANSI 색상 코드)
        if self.colored:
            colors = {
                NotificationLevel.INFO: '\033[94m',     # 파란색
                NotificationLevel.WARNING: '\033[93m',  # 노란색
                NotificationLevel.ALERT: '\033[95m',    # 보라색
                NotificationLevel.ERROR: '\033[91m'     # 빨간색
            }
            reset = '\033[0m'
            color = colors.get(notification.level, '')
        else:
            color = ''
            reset = ''

        # 레벨별 이모지
        emojis = {
            NotificationLevel.INFO: 'ℹ️',
            NotificationLevel.WARNING: '⚠️',
            NotificationLevel.ALERT: '🔔',
            NotificationLevel.ERROR: '❌'
        }
        emoji = emojis.get(notification.level, '')

        print(f"\n{color}[{notification.level.value}] {emoji} {notification.title}{reset}")
        print(f"{color}{notification.message}{reset}")
        if notification.data:
            print(f"{color}데이터: {notification.data}{reset}")
        print(f"{color}시간: {notification.timestamp}{reset}")


class FileChannel(NotificationChannel):
    """파일 로깅 채널"""

    def __init__(self, log_file: str = "notifications.log"):
        self.log_file = log_file

    def send(self, notification: Notification):
        """파일에 기록"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{notification.level.value}] {notification.title}\n")
            f.write(f"시간: {notification.timestamp}\n")
            f.write(f"메시지: {notification.message}\n")
            if notification.data:
                f.write(f"데이터: {notification.data}\n")


class EmailChannel(NotificationChannel):
    """이메일 채널 (구현 예시)"""

    def __init__(self, smtp_server: str = None, recipient: str = None):
        self.smtp_server = smtp_server
        self.recipient = recipient
        self.enabled = False  # 실제 SMTP 설정 필요

    def send(self, notification: Notification):
        """이메일 전송"""
        if not self.enabled:
            # 실제 이메일 전송 로직은 SMTP 설정이 필요
            # 여기서는 로그만 출력
            print(f"[Email] {notification.title} (실제 전송되지 않음)")
            return

        # 실제 이메일 전송 로직
        # import smtplib
        # from email.mime.text import MIMEText
        # ...


class SlackChannel(NotificationChannel):
    """Slack 웹훅 채널 (구현 예시)"""

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.enabled = False  # 실제 웹훅 URL 필요

    def send(self, notification: Notification):
        """Slack으로 전송"""
        if not self.enabled or not self.webhook_url:
            print(f"[Slack] {notification.title} (실제 전송되지 않음)")
            return

        # 실제 Slack 웹훅 전송 로직
        # import requests
        # requests.post(self.webhook_url, json={...})
