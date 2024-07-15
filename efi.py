import os
import subprocess
from urllib.request import urlretrieve, urlopen
from urllib.error import HTTPError
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QComboBox, QLabel, QFileDialog, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor

class DownloadThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename
        self.stopped = False

    def run(self):
        self.stopped = False
        try:
            urlretrieve(self.url, self.filename, self.report_progress)
        except HTTPError as e:
            print(f"HTTP Error: {e}")
            self.cleanup()
        except Exception as e:
            print(f"Download error: {e}")
            self.cleanup()

    def stop(self):
        self.stopped = True
        self.cleanup()

    def cleanup(self):
        if self.stopped and os.path.exists(self.filename):
            os.remove(self.filename)

    def report_progress(self, block_num, block_size, total_size):
        if self.stopped:
            return
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            self.progress.emit(int(percent))

class USBInstallerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DOTMINI SOFTWARE")
        self.setGeometry(300, 300, 600, 400)
        self.setStyleSheet(
            "QWidget { background-color: #f0f0f0; }"
            "QLabel { color: #333; }"
            "QPushButton { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #0056b3; }"
            "QProgressBar { text-align: center; }"
            "QComboBox { padding: 5px; }"
        )
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.intro_label = QLabel("DOTMINI DSS", self)
        self.intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.intro_label.setStyleSheet("font-size: 24px; font-weight: bold; color: black;")
        layout.addWidget(self.intro_label)

        self.label = QLabel("Select macOS Version", self)
        layout.addWidget(self.label)

        self.combo = QComboBox(self)
        self.combo.addItem("macOS Big Sur")
        self.combo.addItem("macOS Monterey")
        self.combo.addItem("macOS Ventura")
        layout.addWidget(self.combo)

        self.download_button = QPushButton("Start Download", self)
        self.download_button.clicked.connect(self.toggle_download)
        layout.addWidget(self.download_button)

        self.progress = QProgressBar(self)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress)

        self.usb_button = QPushButton("Create USB Installer", self)
        self.usb_button.clicked.connect(self.create_usb)
        layout.addWidget(self.usb_button)

        self.setLayout(layout)

        self.download_thread = None
        self.filename = ""  # Initialize filename attribute

    def toggle_download(self):
        if self.download_thread is None or not self.download_thread.isRunning():
            self.start_download()
        else:
            self.stop_download()

    def start_download(self):
        selected_version = self.combo.currentIndex()
        if selected_version == 0:
            self.url = "https://download2364.mediafire.com/oave9rz6zulgdItRhYxhL3W7RLD6GfduuvYUwW6NWfDwDS5KG2BOXkg-s0VBXXIPgng1xoMeyPbwwHVJOETJ7YRxYANb8tvFuJrYtLs3R5eD7hsgK7pfoohwDMgO5JgGd8I327eNLEVc_sZTneNqj_Ml2iYAGKXlCIlj8IHptq0/bp5it8zrindw3hf/Olarila+BigSur+11.7.10.raw"
            self.filename = "bigsur.raw"
        elif selected_version == 1:
            self.url = "https://download2325.mediafire.com/kf7h329mzkcgFUns0t4zbNQO9JfAZRMbMe9mHAjVGZZyWYxe9cVl0_bB-r-zsW5RIY9YmYlXs244u38f1T7_XFgiLRonEhnFu3sR4bLerxtmIvril6G2mCCr6pbOvi2jkB1m6GkzsBHz3an1SNq3nAbIa6UOZoa3BiBNL5v_fZM/fer5pagguuk0kvl/Olarila+Monterey+12.7.5.raw"
            self.filename = "monterey.raw"
        elif selected_version == 2:
            self.url = "https://download2389.mediafire.com/fhbhesufoa7g37dPwVRZUCWhfKJMj0cqsOXSPlmfusHmZqYZ2tXdBVxvfhNAmu8idztUlRnxS-GhT62g-w-PKIYstHJXxUQzgN3WgnR00p00zakj-MHycoRrn8lTgHaGymBj0bCKgsibqjhAdmW8najBiTYFNlObjqI5tEiV-HI/a54wd640ayuvq5o/Olarila+Ventura+13.6.7.raw"
            self.filename = "ventura.raw"

        self.download_thread = DownloadThread(self.url, self.filename)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.start()

        self.download_button.setText("Stop Download")

    def stop_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_button.setText("Start Download")

    def update_progress(self, value):
        self.progress.setValue(value)

    def create_usb(self):
        device, _ = QFileDialog.getOpenFileName(self, "Select USB Device", "/dev", "Device Files (*)")
        if not device:
            QMessageBox.warning(self, "Error", "No USB device selected.")
            return

        if not os.path.exists(self.filename):
            QMessageBox.warning(self, "Error", f"{self.filename} not found. Download it first.")
            return

        try:
            self.format_usb(device)
            self.write_image_to_usb(self.filename, device)
            QMessageBox.information(self, "Success", "USB installer creation complete!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def format_usb(self, device):
        """Format the USB device to HFS+."""
        print(f"Formatting USB device {device}...")
        command = f"sudo diskutil eraseDisk HFS+ USB_INSTALLER MBRFormat {device}"
        subprocess.run(command, shell=True, check=True)

    def write_image_to_usb(self, img_path, device):
        """Write the raw disk image to the USB device."""
        print(f"Writing disk image to USB device {device}...")
        command = f"sudo dd if={img_path} of={device} bs=1m status=progress"
        subprocess.run(command, shell=True, check=True)
        subprocess.run("sudo sync", shell=True, check=True)

if __name__ == "__main__":
    app = QApplication([])
    window = USBInstallerApp()
    window.show()
    app.exec()
