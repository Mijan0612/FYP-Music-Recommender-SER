from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from SpotipyGUI import SpotifyClient
import requests
import pyaudio
import wave
import threading


class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self, client_id, client_secret):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret

        self.stack = QtWidgets.QStackedWidget(self)
        self.setCentralWidget(self.stack)
        self.resize(500, 700)
        self.setStyleSheet("background-color: lightblue")


        self.page1 = HomePage(self)
        self.page2 = SpotifyPage(self, client_id, client_secret)

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)

       #self.pushButton = QtWidgets.QPushButton("Go to Spotify Page", self)
        #self.pushButton.setStyleSheet("background-color: white")
        #self.pushButton.clicked.connect(self.go_to_spotify_page)
        #self.page1.layout.addWidget(self.pushButton)

    def go_to_spotify_page(self):
        self.stack.setCurrentWidget(self.page2)
        self.page2.fetch_song_details()  # Automatically fetch song details upon switching to Spotify page

    def return_to_home_page(self):
        self.stack.setCurrentWidget(self.page1)


class HomePage(QtWidgets.QWidget):

    recordingFinished = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("Home Page", self)
        self.layout.addWidget(self.label)

        self.recordingFinished.connect(parent.go_to_spotify_page)

        self.recordButton = QtWidgets.QPushButton("Start Recording", self)
        self.recordButton.clicked.connect(self.toggle_recording)
        self.layout.addWidget(self.recordButton)

        self.is_recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.recording_thread = None

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.recordButton.setText("Stop Recording")
            self.is_recording = True
            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self.start_recording)
            self.recording_thread.start()

    def start_recording(self):
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=44100,
                                  input=True,
                                  frames_per_buffer=1024)
        while self.is_recording:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.frames.append(data)

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread is not None:
            self.recording_thread.join()  # Wait for recording thread to finish

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        # Save recording to a file
        wf = wave.open("output.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        self.recordButton.setText("Start Recording")
        self.recordingFinished.emit()  # Emit signal to indicate recording has finished
class SpotifyPage(QtWidgets.QWidget):
    def __init__(self, parent, client_id, client_secret):
        super().__init__(parent)
        self.spotify_client = SpotifyClient(client_id, client_secret)
        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.songLabel = QtWidgets.QLabel("", self)  # Placeholder text
        self.layout.addWidget(self.songLabel)

        self.songImageLabel = QtWidgets.QLabel(self)
        self.layout.addWidget(self.songImageLabel)

        self.returnButton = QtWidgets.QPushButton("Return to Home Page", self)
        self.returnButton.clicked.connect(parent.return_to_home_page)  # Connect to the parent's method
        self.layout.addWidget(self.returnButton)

        self.fetch_song_details()  # Automatically fetch song details upon initialization

    def fetch_song_details(self):
        song_details = self.spotify_client.get_recommended_song('sad')  # For example, using 'happy'
        if song_details:
            self.songLabel.setText(f"{song_details['name']} by {song_details['artist']}")
            self.display_song_image(song_details['image_link'])
        else:
            self.songLabel.setText("Failed to fetch song.")

    def display_song_image(self, image_url):
        image_data = requests.get(image_url).content
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(image_data)
        self.songImageLabel.setPixmap(pixmap)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    client_id = 'fd8268198c88420db0343ca9b067cc15'
    client_secret = '44fbe87c03bf483496089d56206da509'

    ui = Ui_MainWindow(client_id, client_secret)
    ui.show()
    sys.exit(app.exec_())
