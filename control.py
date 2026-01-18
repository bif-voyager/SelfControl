import tkinter as tk
from tkinter import messagebox
import psutil
import time
import threading
import sys
import os

# Путь к файлу hosts в Windows
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"


class FocusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Режим Фокусировки")
        self.root.geometry("400x350")
        self.root.resizable(False, False)

        # Переменная для контроля цикла блокировки
        self.is_running = False

        # --- Интерфейс ---

        # 1. Приложения
        tk.Label(root, text="Приложения для бана (формат name.exe):").pack(pady=5)
        self.apps_entry = tk.Entry(root, width=50)
        self.apps_entry.insert(0, "steam.exe, discord.exe, telegram.exe")  # Пример
        self.apps_entry.pack(pady=5)

        # 2. Сайты
        tk.Label(root, text="Сайты для бана (без http, просто name.com):").pack(pady=5)
        self.sites_entry = tk.Entry(root, width=50)
        self.sites_entry.insert(0, "")  # Пример
        self.sites_entry.pack(pady=5)

        # 3. Время
        tk.Label(root, text="Время фокусировки (минуты):").pack(pady=5)
        self.time_entry = tk.Entry(root, width=10)
        self.time_entry.insert(0, "45")
        self.time_entry.pack(pady=5)

        # 4. Кнопка Старт
        self.start_btn = tk.Button(root, text="НАЧАТЬ УЧЕБУ", bg="red", fg="white", font=("Arial", 12, "bold"),
                                   command=self.start_focus)
        self.start_btn.pack(pady=20)

        # Статус
        self.status_label = tk.Label(root, text="Готов к работе", fg="green")
        self.status_label.pack()

    def block_websites(self, sites_list):
        """Добавляет сайты в файл hosts"""
        try:
            with open(HOSTS_PATH, 'r+') as file:
                content = file.read()
                for site in sites_list:
                    if site not in content:
                        file.write(f"\n{REDIRECT_IP} {site}")
                        file.write(f"\n{REDIRECT_IP} www.{site}")
        except PermissionError:
            messagebox.showerror("Ошибка", "Запустите скрипт от имени АДМИНИСТРАТОРА!")
            return False
        return True

    def unblock_websites(self, sites_list):
        """Убирает сайты из файла hosts"""
        try:
            with open(HOSTS_PATH, 'r+') as file:
                lines = file.readlines()
                file.seek(0)
                for line in lines:
                    if not any(site in line for site in sites_list):
                        file.write(line)
                file.truncate()
        except Exception as e:
            print(f"Ошибка разблокировки: {e}")

    def blocking_process(self, minutes, apps, sites):
        """Основной цикл блокировки в отдельном потоке"""
        end_time = time.time() + minutes * 60

        # 1. Блокируем сайты
        if not self.block_websites(sites):
            self.stop_focus(sites)  # Если нет прав, отменяем
            return

        while time.time() < end_time:
            remaining = int(end_time - time.time())
            self.status_label.config(text=f"Осталось: {remaining // 60} мин {remaining % 60} сек")

            # 2. Убиваем приложения
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in apps:
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            time.sleep(1)

        # Конец времени
        self.stop_focus(sites)
        messagebox.showinfo("Успех", "Фокусировка завершена! Ты молодец.")

    def start_focus(self):
        # Получаем данные
        try:
            minutes = float(self.time_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число в поле времени")
            return

        raw_apps = self.apps_entry.get().split(',')
        apps = [app.strip().lower() for app in raw_apps if app.strip()]

        raw_sites = self.sites_entry.get().split(',')
        sites = [site.strip().lower() for site in raw_sites if site.strip()]

        # Визуальная блокировка интерфейса
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED, text="ПРИЛОЖЕНИЯ ЗАБЛОКИРОВАНЫ, УЧИСЬ!")
        self.apps_entry.config(state=tk.DISABLED)
        self.sites_entry.config(state=tk.DISABLED)
        self.time_entry.config(state=tk.DISABLED)

        # ОТКЛЮЧАЕМ КРЕСТИК ЗАКРЫТИЯ ОКНА
        self.root.protocol("WM_DELETE_WINDOW", self.disable_event)

        # Запускаем в отдельном потоке, чтобы окно не зависло
        threading.Thread(target=self.blocking_process, args=(minutes, apps, sites), daemon=True).start()

    def stop_focus(self, sites):
        self.unblock_websites(sites)
        self.is_running = False
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)  # Возвращаем крестик
        self.start_btn.config(state=tk.NORMAL, text="НАЧАТЬ УЧЕБУ")
        self.apps_entry.config(state=tk.NORMAL)
        self.sites_entry.config(state=tk.NORMAL)
        self.time_entry.config(state=tk.NORMAL)
        self.status_label.config(text="Свобода")

    def disable_event(self):
        pass  # Ничего не делаем при нажатии на крестик


if __name__ == "__main__":
    # Проверка на админа
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        import ctypes

        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    if not is_admin:
        import ctypes

        executable = sys.executable.replace("python.exe", "pythonw.exe")

        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, " ".join(sys.argv), None, 1)
        sys.exit()

    root = tk.Tk()
    app = FocusApp(root)
    root.mainloop()