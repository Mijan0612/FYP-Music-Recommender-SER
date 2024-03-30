import sys
import os
import sounddevice as sd
import soundfile as sf
import noisereduce as nr
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel


class VoiceRecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice Recorder")
        self.setGeometry(100, 100, 400, 200)

        self.record_button = QPushButton("Record", self)
        self.record_button.setGeometry(50, 50, 100, 30)
        self.record_button.clicked.connect(self.start_recording)

        self.status_label = QLabel("", self)
        self.status_label.setGeometry(50, 100, 300, 30)

        self.output_file = "recording2.wav"

    def start_recording(self):
        self.status_label.setText("Recording...")
        duration = 5  # Recording duration in seconds

        # Record audio
        recording = sd.rec(int(duration * 44100), samplerate=44100, channels=2)
        sd.wait()  # Wait for recording to finish

        # Save recording to WAV file
        sf.write(self.output_file, recording, samplerate=44100)

        self.status_label.setText("Applying noise reduction...")
        data, _ = sf.read(self.output_file)
        reduced_noise = nr.reduce_noise(y=data, sr=44100)

        sf.write(self.output_file, reduced_noise, samplerate=44100)

        self.status_label.setText("Recording saved to {}".format(self.output_file))


def main():
    # Delete previous recording file if exists
    output_file = "recording.wav"
    if os.path.exists(output_file):
        os.remove(output_file)

    app = QApplication(sys.argv)
    window = VoiceRecorderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
