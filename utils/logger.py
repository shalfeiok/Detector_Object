"""Утилиты логирования"""

import logging
import os
from datetime import datetime


class AppLogger:
    """Централизованный менеджер логирования"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logging()
        return cls._instance

    def _setup_logging(self):
        """Настройка системы логирования"""
        self.logger = logging.getLogger('WildlifeTracker')
        self.logger.setLevel(logging.INFO)

        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Файловый обработчик
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = f'{log_dir}/wildlife_tracker_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)

        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Добавление обработчиков
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Получение экземпляра логгера"""
        return self.logger


# Глобальный логгер
logger = AppLogger().get_logger()