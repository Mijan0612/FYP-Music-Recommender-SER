# main.py
import sys
import sounddevice as sd
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


# Define a thread to handle background recording to prevent GUI freezing
class RecordThread(QThread):
    finished = pyqtSignal(np.ndarray)

    def run(self):
        recording = sd.rec(int(5 * 44100), samplerate=44100, channels=2)
        sd.wait()
        self.finished.emit(recording)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Recorder")
        self.setGeometry(100, 100, 300, 100)

        layout = QVBoxLayout()

        self.recordButton = QPushButton("Record")
        self.recordButton.clicked.connect(self.on_record)
        layout.addWidget(self.recordButton)

        self.recording_status = QLabel("Press Record to start recording")
        layout.addWidget(self.recording_status)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.record_thread = RecordThread()
        self.record_thread.finished.connect(self.on_record_finished)

        self.record_count = 0

    def on_record(self):
        if self.record_count == 0:
            self.recording_status.setText("Recording... Press again to stop.")
            self.record_thread.start()
            self.recordButton.setEnabled(False)  # Prevent multiple clicks
            self.record_count += 1
        elif self.record_count == 1:
            self.record_thread.terminate()  # Not the best way to stop, but simple for this demo
            self.record_count += 1

    def on_record_finished(self, recording):
        self.recordButton.setEnabled(True)
        # Proceed to switch window or handle recording data
        if self.record_count == 2:
            self.hide()  # Hide the current window
            self.spotify_window = SpotifyWindow()  # Assuming you have a SpotifyWindow class
            self.spotify_window.show()
            # You can pass the recording or its filename to SpotifyWindow if needed


# Placeholder for SpotifyWindow definition
class SpotifyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Data")
        self.setGeometry(100, 100, 500, 300)
        # Setup Spotipy and display data
        # For the purpose of this example, let's just use a label
        self.label = QLabel("Spotify data would be displayed here.", self)
        self.setCentralWidget(self.label)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
