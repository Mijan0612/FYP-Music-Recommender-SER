from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QRect
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
        self.setWindowTitle("MuSeek!")

        self.stack = QtWidgets.QStackedWidget(self)
        self.setCentralWidget(self.stack)
        self.setFixedSize(500, 700)
        self.setStyleSheet("background-color: lemonchiffon")

        self.page1 = HomePage(self)
        self.page2 = SpotifyPage(self, client_id, client_secret)
        self.loadingPage = LoadingScreen(self)
        self.infoPage = InfoPage(self)
        self.infoPage.requestHomePage.connect(self.return_to_home_page)
        self.page1.recordingFinished.connect(self.handle_emotion)

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.loadingPage)
        self.stack.addWidget(self.page2)
        self.stack.addWidget(self.infoPage)
        self.loadingPage.predictedEmotion.connect(self.page2.fetch_song_details)

        self.recorded_songs = []  # List to store recorded songs' details

    def handle_emotion(self, emotion):
        # Use the detected emotion to decide what to do next
        print(f"Detected emotion: {emotion}")  # For demonstration
        self.show_loading_screen(emotion)

    def show_loading_screen(self, emotion):
        self.stack.setCurrentWidget(self.loadingPage)
        QtCore.QTimer.singleShot(2000, lambda: self.go_to_spotify_page(emotion))

    def go_to_spotify_page(self, emotion):
        self.stack.setCurrentWidget(self.page2)
        self.page2.fetch_song_details(emotion)  # Automatically fetch song details upon switching to Spotify page

    def return_to_home_page(self):
        self.stack.setCurrentWidget(self.page1)

    def close_application(self):
        self.close()

    def go_to_info_page(self):
        # Switch to the new page
        self.stack.setCurrentWidget(self.infoPage)


class HomePage(QtWidgets.QWidget):
    recordingFinished = pyqtSignal(str)
    goToNewPage = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Add some margins

        labelLayout = QtWidgets.QHBoxLayout()

        labelLayout.addSpacing(20)
        leftIcon = QtWidgets.QLabel(self)
        leftPixmap = QtGui.QPixmap("feather/headphones.png")  # Replace "left_icon.png" with your icon path
        scaledLeft = leftPixmap.scaled(45, 45, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        leftIcon.setPixmap(scaledLeft)
        labelLayout.addWidget(leftIcon, alignment=QtCore.Qt.AlignLeft)

        self.label = QtWidgets.QLabel("MuSeek!", self)
        self.label.setStyleSheet("font-family: Papyrus; font-size: 30px; font-weight: bold;")
        labelLayout.addWidget(self.label, alignment=QtCore.Qt.AlignCenter)

        rightIcon = QtWidgets.QLabel(self)
        rightPixmap = QtGui.QPixmap("feather/music-note.png")
        scaledRight = rightPixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        rightIcon.setPixmap(scaledRight)
        labelLayout.addWidget(rightIcon, alignment=QtCore.Qt.AlignRight)

        labelLayout.addSpacing(20)

        self.layout.addLayout(labelLayout)  # Add labelLayout to the main layout

        anotherLabel = QtWidgets.QLabel("<center>Emotion-based<br>Music Recommender</center>", self)
        anotherLabel.setStyleSheet("font-family: Arial; font-size: 16px; color: red;")  # Example style
        anotherLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(anotherLabel)

        # Add a new label below the existing labels
        newLabel = QtWidgets.QLabel("Record now to get songs recommendation!", self)
        newLabel.setStyleSheet("font-family: Arial; font-size: 10px; color: blue;")  # Example style
        newLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)
        self.layout.addWidget(newLabel)

        self.recordingFinished.connect(parent.show_loading_screen)

        self.is_recording = False
        self.frames = []
        self.p = None
        self.stream = None
        self.recording_thread = None

        self.feature_extraction = FeatureExtraction()
        self.feature_extraction.load_model()

        self.record_button()

        self.info_button()

        self.close_button()

    def record_button(self):
        # Create a QFrame widget to wrap the icon
        self.recordButtonFrame = QtWidgets.QFrame(self)
        self.recordButtonFrame.setObjectName("RecordButtonFrame")  # Set object name for styling

        self.layout.addWidget(self.recordButtonFrame, alignment=QtCore.Qt.AlignCenter)

        # Create a QHBoxLayout for the button layout
        buttonLayout = QtWidgets.QHBoxLayout(self.recordButtonFrame)

        RecordIcon = QIcon("feather/mic.svg")
        self.recordButton = QtWidgets.QPushButton(self.recordButtonFrame)
        self.recordButton.setIcon(RecordIcon)
        self.recordButton.setIconSize(QtCore.QSize(50, 50))  # Set the size of the icon
        self.recordButton.setFixedSize(50, 50)  # Set a fixed size for the button
        self.recordButton.setStyleSheet("border: none;")  # Remove border from the button
        self.recordButton.clicked.connect(self.toggle_recording)  # Connect to the appropriate method
        self.recordButton.setToolTip("Start Recording")

        # Add the button to the button layout
        buttonLayout.addWidget(self.recordButton, alignment=QtCore.Qt.AlignCenter)

        # Apply padding to the QFrame
        self.recordButtonFrame.setStyleSheet("padding: 5px; border-radius: 25px; border: 3px solid black; "
                                             "background-color: white;")
        self.setStyleSheet("""QToolTip { background-color: white; color: grey; border: groove 2px; }""")

    def info_button(self):

        InfoIcon = QIcon("feather/info.svg")
        InfoButton = QtWidgets.QPushButton(self)
        InfoButton.setIcon(InfoIcon)
        InfoButton.setIconSize(QtCore.QSize(30, 30))  # Set the size of the icon
        InfoButton.setFixedSize(30, 30)  # Set a fixed size to make it circular
        InfoButton.setStyleSheet("border-radius: 60px;")  # Circular button style
        InfoButton.clicked.connect(self.parent().go_to_info_page)  # Connect to the appropriate method
        InfoButton.setToolTip("Information")

        self.layout.addWidget(InfoButton)

    def close_button(self):

        closeIcon = QIcon("feather/close.svg")

        # Create the QPushButton with the close icon
        closeButton = QtWidgets.QPushButton(self)
        closeButton.setIcon(closeIcon)
        closeButton.setIconSize(QtCore.QSize(30, 30))  # Set the size of the icon
        closeButton.setFixedSize(30, 30)  # Set a fixed size to make it circular
        closeButton.setStyleSheet("border-radius: 60px;")  # Circular button style
        closeButton.clicked.connect(self.parent().close_application)
        closeButton.setToolTip("Close Application")  # Add a tooltip

        self.layout.insertWidget(0, closeButton, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.recordButton.setIcon(QIcon("feather/square.svg"))
            self.recordButton.setIconSize(QtCore.QSize(50, 50))  # Set the size of the icon
            self.recordButton.setFixedSize(50, 50)  # Set a fixed size to make it circular
            self.recordButton.setToolTip("Stop Recording")
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

        self.recordButton.setIcon(QIcon("feather/mic.svg"))

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

    '''
    def predict_emotion_from_recording(self, audio_file_path):
        pipeline = FeatureExtraction()
        pipeline.load_model()
        features = pipeline.extract_features(audio_file_path, mfcc=True, chroma=False, mel=False)
        prediction = pipeline.predict_emotion(features)
        return prediction
    '''


class InfoPage(QtWidgets.QWidget):
    requestHomePage = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)

        label_text = self.read_text("info.txt")

        label = QtWidgets.QLabel(label_text, self)  # Use the read text as label text
        label.setStyleSheet("font-family: Arial; font-size: 16px;")
        self.layout.addWidget(label, alignment=QtCore.Qt.AlignCenter)

        self.add_home_button()

    def read_text(self, file_path):
        try:
            with open(file_path, "r") as file:
                label_text = file.read()
            return label_text
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return "Label Text Not Found"

    def add_home_button(self):

        returnIcon = QtGui.QIcon("feather/return.svg")

        # Create the QPushButton with the close icon
        homeButton = QtWidgets.QPushButton("\tBack to Home Page", self)
        homeButton.setIcon(returnIcon)
        homeButton.setIconSize(QtCore.QSize(20, 20))
        homeButton.setFixedSize(140, 50)
        homeButton.setStyleSheet("padding: 5px; border-radius: 20px; border: 1px solid black; "
                                 "background-color: white;")
        homeButton.clicked.connect(self.on_home_button_clicked)

        self.layout.addWidget(homeButton, alignment=QtCore.Qt.AlignCenter)

    def on_home_button_clicked(self):
        # Emit the signal when the button is clicked
        self.requestHomePage.emit()


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
    songIdentified = pyqtSignal(dict)

    def __init__(self, parent, client_id, client_secret):
        super().__init__(parent)
        self.spotify_client = SpotifyClient(client_id, client_secret)
        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.layout.addWidget(self.label)

        self.songLayout = QtWidgets.QHBoxLayout()

        self.songImageLabel = QtWidgets.QLabel(self)
        self.songImageLabel.setAlignment(QtCore.Qt.AlignCenter)  # Center the image
        self.layout.addWidget(self.songImageLabel)

        self.textLayout = QtWidgets.QVBoxLayout()

        self.songLabel = QtWidgets.QLabel("", self)  # Placeholder text
        self.layout.addWidget(self.songLabel)

        self.artistLabel = QtWidgets.QLabel("", self)  # Placeholder text
        self.textLayout.addWidget(self.artistLabel)

        self.songLayout.addLayout(self.textLayout)  # Add text layout to song layout
        self.layout.addLayout(self.songLayout)

        self.add_return_button(parent.return_to_home_page)
        self.add_close_button()

    def add_return_button(self, function):
        self.returnButton = QtWidgets.QPushButton("Return to Home Page", self)
        self.returnButton.setFixedSize(140, 50)
        self.returnButton.setStyleSheet("padding: 5px; border-radius: 20px; border: 1px solid black; "
                                        "background-color: white;")
        self.returnButton.clicked.connect(function)  # Connect to the provided function
        self.layout.addWidget(self.returnButton, alignment=QtCore.Qt.AlignCenter)

    def add_close_button(self):
        closeIcon = QIcon("feather/x-circle.svg")

        # Create the QPushButton with the close icon
        closeButton = QtWidgets.QPushButton(self)
        closeButton.setIcon(closeIcon)
        closeButton.setIconSize(QtCore.QSize(30, 30))  # Set the size of the icon
        closeButton.setFixedSize(30, 30)  # Set a fixed size to make it circular
        closeButton.setStyleSheet("border-radius: 15px;")  # Circular button style
        closeButton.clicked.connect(self.parent().close_application)
        closeButton.setToolTip("Close Application")  # Add a tooltip

        self.layout.insertWidget(0, closeButton, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)

    def fetch_song_details(self, emotion):
        song_details, playlist_message = self.spotify_client.get_recommended_song(emotion)
        if song_details:
            song_link = f"https://open.spotify.com/track/{song_details['spotify_uri'].split(':')[-1]}"
            self.songLabel.setText(f"<div style='text-align: center; font-size: 16px;'>"
                                   f"{song_details['name']} by {song_details['artist']}</div>")
            self.display_song_image(song_details['image_link'])
            if playlist_message:
                self.label.setText(f"<div style='text-align: center; font-size: 16px;'>"
                                   f"{playlist_message}</div>")
            self.songIdentified.emit(song_details)

        else:
            self.songLabel.setText("Failed to fetch song.")

    def display_song_image(self, image_url):
        image_data = requests.get(image_url).content
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(image_data)

        # Scale the image while maintaining aspect ratio and using smooth transformation
        scaled_pixmap = pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio,
                                      QtCore.Qt.SmoothTransformation)

        self.songImageLabel.setPixmap(scaled_pixmap)
        self.songImageLabel.resize(scaled_pixmap.size())  # Adjust the label size to fit the scaled image


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    client_id = 'fd8268198c88420db0343ca9b067cc15'
    client_secret = '44fbe87c03bf483496089d56206da509'

    ui = Ui_MainWindow(client_id, client_secret)
    ui.show()
    sys.exit(app.exec_())
