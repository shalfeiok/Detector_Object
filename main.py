"""Точка входа приложения"""

import sys
import tkinter as tk
from tkinter import messagebox
from ui.main_window import MainApplication
from utils.logger import logger


# auto-py-to-exe


def check_dependencies():
    """Проверка зависимостей"""
    dependencies = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'pyautogui': 'pyautogui',
        'pygetwindow': 'pygetwindow'
    }

    missing = []
    for module, package in dependencies.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    return missing


def main():
    """Главная функция приложения"""
    try:
        # Проверка зависимостей
        missing = check_dependencies()
        if missing:
            print('Необходимо установить следующие пакеты:')
            for package in missing:
                print(f'  pip install {package}')

            # Показать диалог с инструкциями
            try:
                tk.Tk().withdraw()
                messagebox.showinfo(
                    'Необходимы зависимости',
                    f'Установите недостающие пакеты:\n\n' +
                    '\n'.join(f'pip install {p}' for p in missing)
                )
            except:
                pass

            return 1

        # Запуск приложения
        app = MainApplication()
        app.run()

        return 0

    except Exception as e:
        logger.critical(f'Application error: {e}', exc_info=True)

        # Показать сообщение об ошибке
        try:
            tk.Tk().withdraw()
            messagebox.showerror(
                'Ошибка',
                f'Произошла ошибка:\n{str(e)}\n\nПодробности в логах.'
            )
        except:
            print(f'Critical error: {e}')

        return 1

# pip install -r requirements.txt


if __name__ == '__main__':
    sys.exit(main())