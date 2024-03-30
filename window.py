from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from SpotipyGUI import SpotifyClient
import requests
import pyaudio
import wave
import threading
from extract import FeatureExtraction
import os
from datetime import datetime
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings

# Suppress deprecated warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

RECORDING_FOLDER = "outputs"
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
        self.loadingPage = LoadingScreen(self)
        self.page1.recordingFinished.connect(self.handle_emotion)

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.loadingPage)
        self.stack.addWidget(self.page2)
        self.loadingPage.predictedEmotion.connect(self.page2.fetch_song_details)


    def handle_emotion(self, emotion):
        # Use the detected emotion to decide what to do next
        print(f"Detected emotion: {emotion}")  # For demonstration
        self.show_loading_screen(emotion)

    def show_loading_screen(self, emotion):
        self.stack.setCurrentWidget(self.loadingPage)
        QtCore.QTimer.singleShot(3000, lambda: self.go_to_spotify_page(emotion))

    def go_to_spotify_page(self, emotion):
        self.stack.setCurrentWidget(self.page2)
        self.page2.fetch_song_details(emotion) # Automatically fetch song details upon switching to Spotify page

    def return_to_home_page(self):
        self.stack.setCurrentWidget(self.page1)

    def close_application(self):
        self.close()

class HomePage(QtWidgets.QWidget):
    recordingFinished = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("Home Page", self)
        self.layout.addWidget(self.label)

        self.recordingFinished.connect(parent.show_loading_screen)

        self.recordButton = QtWidgets.QPushButton("Start Recording", self)
        self.recordButton.clicked.connect(self.toggle_recording)
        self.layout.addWidget(self.recordButton, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)

        self.is_recording = False
        self.frames = []
        self.p = None
        self.stream = None
        self.recording_thread = None

        self.feature_extraction = FeatureExtraction()
        self.feature_extraction.load_model()

        self.add_close_button()

    def add_close_button(self):
        closeButton = QtWidgets.QPushButton("Close", self)
        closeButton.setFixedSize(120, 30)
        closeButton.clicked.connect(self.parent().close_application)
        self.layout.addWidget(closeButton, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.recordButton.setText("Stop Recording")
            self.is_recording = True
            self.frames = []  # Reset frames list for a new recording
            try:
                self.p = pyaudio.PyAudio()  # Initialize PyAudio
                self.recording_thread = threading.Thread(target=self.start_recording)
                self.recording_thread.start()
            except Exception as e:
                print(f"Error initializing PyAudio: {e}")

    def start_recording(self):
        # Check if PyAudio is properly initialized
        if self.p is None:
            print("PyAudio is not initialized.")
            return

        # Generate a unique filename for the new recording
        audio_filename = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=44100,
                                  input=True,
                                  input_device_index=1,
                                  frames_per_buffer=2048)
        while self.is_recording:
            data = self.stream.read(2048, exception_on_overflow=False)
            self.frames.append(data)


    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread is not None:
            self.recording_thread.join()  # Wait for recording thread to finish
        if self.stream is not None and self.stream.is_active():
            self.stream.stop_stream()
            self.stream.close()
        if self.p is not None:
            self.p.terminate()

        self.recordButton.setText("Start Recording")

        # Save recording to a new file with a unique name
        audio_filename = os.path.join(RECORDING_FOLDER, f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        wf = wave.open(audio_filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        features = self.feature_extraction.extract_features(audio_filename, mfcc=True, chroma=False, mel=False)
        predicted_emotion = self.feature_extraction.predict_emotion(features)
        self.recordingFinished.emit(predicted_emotion)
    def predict_emotion_from_recording(self, audio_file_path):
        pipeline = FeatureExtraction()
        pipeline.load_model()
        features = pipeline.extract_features(audio_file_path, mfcc=True, chroma=False, mel=False)
        prediction = pipeline.predict_emotion(features)
        return prediction



class LoadingScreen(QtWidgets.QWidget):
    # Define the predictedEmotion signal
    predictedEmotion = QtCore.pyqtSignal(str)  # Adjust the data type based on your requirements

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("Loading...", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)


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

        self.add_close_button()

    def add_close_button(self):
        closeButton = QtWidgets.QPushButton("Close", self)
        closeButton.clicked.connect(self.parent().close_application)

        # Create a horizontal layout for the close button
        closeLayout = QtWidgets.QHBoxLayout()
        closeLayout.addWidget(closeButton)
        closeLayout.addStretch()  # Add a stretch to push the button to the right

        # Add the horizontal layout to the top of the page's layout
        self.layout.addLayout(closeLayout)

    def fetch_song_details(self, emotion):
        song_details, playlist_message = self.spotify_client.get_recommended_song(emotion)
        if song_details:
            self.songLabel.setText(f"{song_details['name']} by {song_details['artist']}")
            self.display_song_image(song_details['image_link'])
            if playlist_message:
                self.label.setText(playlist_message)
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
