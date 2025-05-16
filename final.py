import csv
import os
import sys
import cv2
import pygame
from PIL.Image import Image
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QPushButton, QTextEdit, \
    QListWidget, QGraphicsDropShadowEffect
from PyQt5.QtGui import QImage, QPixmap, QColor, QTextCharFormat, QTextCursor, QTextImageFormat, QFont, QPalette, \
    QLinearGradient, QBrush
from PyQt5.QtCore import QTimer, Qt, QElapsedTimer


class VideoPlayer(QMainWindow):

    def __init__(self, video_path, audio_path, csv_path, transcription_file):
        super().__init__()
        self.attentiveness_all_class = None
        self.cumulative_streak_data = []
        self.displayed_images = []
        self.cumulative_interval_processed = set()
        self.display_data = []
        self.word_subtitles = []
        self.video_path = video_path
        self.audio_path = audio_path
        self.interval_processed = set()
        self.csv_path = csv_path
        self.cap = None  # Video capture object
        self.timer = None  # Timer for updating video frames
        self.fps = 30  # Default frame rate (will be updated from the video)

        # Initialize the UI
        self.init_ui()
        self.attention_data = self.load_attention_data()
        self.load_word_subtitles(transcription_file)
        self.display_inattentive_students()
        self.calculate_cumulative_data()

    def set_dark_theme(app):
        """Set a dark theme for the application."""
        # Set dark palette
        dark_palette = QPalette()

        # Base colors
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)

        # Disabled colors
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

        # Set the palette
        app.setPalette(dark_palette)

        # Set stylesheet
        app.setStyleSheet("""
            QToolTip {
                color: #ffffff;
                background-color: #2a82da;
                border: 1px solid white;
            }
            QPushButton {
                background-color: #353535;
                border: 1px solid #555;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
        """)

    def init_ui(self):
        """Initialize the user interface with 3D effects."""
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget and layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        # Set a gradient background for the main window
        self.set_gradient_background()

        # Video display area (row 0, column 0)
        self.video_frame = QLabel(self)
        self.video_frame.setAlignment(Qt.AlignCenter)
        self.video_frame.setStyleSheet(
            """
            QLabel {
                background-color: black;
                border-radius: 15px;
                border: 2px solid #555;
            }
            """
        )

        # Add shadow effect to video_frame
        video_shadow = QGraphicsDropShadowEffect()
        video_shadow.setBlurRadius(20)  # Soften the shadow
        video_shadow.setColor(QColor(0, 0, 0, 150))  # Black with 60% opacity
        video_shadow.setOffset(5, 5)  # Shadow offset (x, y)
        self.video_frame.setGraphicsEffect(video_shadow)

        self.layout.addWidget(self.video_frame, 0, 0, 2, 1)  # Row 0, Column 0

        # Textbox under the video (row 1, column 0)
        self.subtitle_listbox = QListWidget(self)
        self.subtitle_listbox.setStyleSheet(
            """
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f0f0, stop:1 #d0d0d0);
                font-size: 14px;
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #888;
            }
            QListWidget:hover {
                border: 2px solid #555;
            }
            """
        )

        # Add shadow effect to subtitle_listbox
        listbox_shadow = QGraphicsDropShadowEffect()
        listbox_shadow.setBlurRadius(15)
        listbox_shadow.setColor(QColor(0, 0, 0, 100))
        listbox_shadow.setOffset(5, 5)
        self.subtitle_listbox.setGraphicsEffect(listbox_shadow)

        self.layout.addWidget(self.subtitle_listbox, 3, 0, 2, 1)  # Row 4, Column 0

        # Textbox 1 (row 0, column 1) - Takes 25% of the column height
        self.attentiveness_all_class = QTextEdit(self)
        self.attentiveness_all_class.setPlaceholderText("General Alerts")
        self.attentiveness_all_class.setStyleSheet(
            """
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f0f0, stop:1 #d0d0d0);
                font-size: 14px;
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #888;
            }
            QTextEdit:hover {
                border: 2px solid #555;
            }
            """
        )

        # Add shadow effect to attentiveness_all_class
        textbox1_shadow = QGraphicsDropShadowEffect()
        textbox1_shadow.setBlurRadius(15)
        textbox1_shadow.setColor(QColor(0, 0, 0, 100))
        textbox1_shadow.setOffset(5, 5)
        self.attentiveness_all_class.setGraphicsEffect(textbox1_shadow)

        self.layout.addWidget(self.attentiveness_all_class, 0, 1)  # Row 0, Column 1

        # Textbox 2 (row 1, column 1) - Takes 75% of the column height
        self.attentiveness_text = QTextEdit(self)
        self.attentiveness_text.setPlaceholderText("Students Alerts")
        self.attentiveness_text.setStyleSheet(
            """
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f0f0, stop:1 #d0d0d0);
                font-size: 14px;
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #888;
            }
            QTextEdit:hover {
                border: 2px solid #555;
            }
            """
        )

        # Add shadow effect to attentiveness_text
        textbox2_shadow = QGraphicsDropShadowEffect()
        textbox2_shadow.setBlurRadius(15)
        textbox2_shadow.setColor(QColor(0, 0, 0, 100))
        textbox2_shadow.setOffset(5, 5)
        self.attentiveness_text.setGraphicsEffect(textbox2_shadow)

        self.layout.addWidget(self.attentiveness_text, 1, 1, 4, 1)  # Row 1, Column 1

        # Play button (row 2, column 0)
        self.play_button = QPushButton("Play", self)
        self.play_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00796b, stop:1 #004d40);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #004d40;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #004d40, stop:1 #00796b);
            }
            """
        )

        # Add shadow effect to play_button
        play_shadow = QGraphicsDropShadowEffect()
        play_shadow.setBlurRadius(10)
        play_shadow.setColor(QColor(0, 0, 0, 100))
        play_shadow.setOffset(3, 3)
        self.play_button.setGraphicsEffect(play_shadow)

        self.play_button.clicked.connect(self.play_video)
        self.layout.addWidget(self.play_button, 5, 0)

        # Stop button (row 2, column 1)
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e57373, stop:1 #d32f2f);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #d32f2f;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d32f2f, stop:1 #e57373);
            }
            """
        )

        # Add shadow effect to stop_button
        stop_shadow = QGraphicsDropShadowEffect()
        stop_shadow.setBlurRadius(10)
        stop_shadow.setColor(QColor(0, 0, 0, 100))
        stop_shadow.setOffset(3, 3)
        self.stop_button.setGraphicsEffect(stop_shadow)

        self.stop_button.clicked.connect(self.stop_video)
        self.layout.addWidget(self.stop_button, 5, 1)

        # Set row stretch factors to control the height of Textbox 1 and Textbox 2
        self.layout.setRowStretch(0, 2)  # Textbox 1 gets 25% (1 part)
        self.layout.setRowStretch(1, 3)  # Textbox 2 gets 75% (3 parts)
        self.layout.setRowStretch(4, 2)
        # Set column stretch factors to control the width of the columns
        self.layout.setColumnStretch(0, 3)  # Column 0 (video and textbox under video) gets 2 parts
        self.layout.setColumnStretch(1, 2)  # Column 1 (textboxes) gets 1 part

    def set_gradient_background(self):
        """Set a gradient background for the main window."""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(240, 240, 240))  # Light gray at the top
        gradient.setColorAt(1, QColor(200, 200, 200))  # Dark gray at the bottom
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)
    def play_video(self):
        """Start playing the video and audio."""
        # Open the video file
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            print("Error: Could not open video.")
            return

        # Get video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps  # Total duration of the video in seconds
        print(f"duration=>{self.duration}")
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Video loaded: {width}x{height} at {self.fps} FPS")

        # Initialize Pygame for audio playback
        pygame.mixer.init()
        pygame.mixer.music.load(self.audio_path)
        pygame.mixer.music.play()

        self.elapsed_timer = QElapsedTimer()
        self.elapsed_timer.start()  # Start the timer

        # Start the timer to update video frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / self.fps))


    def update_frame(self):
        """Update the video frame displayed in the QLabel."""
        if not pygame.mixer.music.get_busy():  # Stop if audio is not playing
            self.timer.stop()
            self.cap.release()
            return

        # Get the current audio playback time in seconds
        audio_time_ms = pygame.mixer.music.get_pos()  # Audio time in milliseconds
        if audio_time_ms == -1:  # Audio is not playing
            return
        current_time = audio_time_ms / 1000.0  # Convert to seconds

        # Seek the video to the frame corresponding to the current audio time
        target_frame = int(current_time * self.fps)
        if target_frame >= self.total_frames:  # End of video
            self.timer.stop()
            self.cap.release()
            pygame.mixer.music.stop()
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

        # Read the frame
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            pygame.mixer.music.stop()
            return

        # Display words based on the current time
        self.display_words(current_time)

        # Display interval text
        interval_start = ((current_time // 60) * 60)-60
        interval_end = interval_start + 60
        interval_label = f"[{interval_start // 60:.0f}-{interval_end // 60:.0f}] min"

        self.display_text_for_selected_interval(interval_label)
        self.display_text_for_selected_interval_cumulative(interval_label)

        # Resize and convert the frame to RGB
        original_height, original_width = frame.shape[:2]
        target_width = 1100  # Set your desired width here
        aspect_ratio = original_width / original_height
        target_height = int(target_width / aspect_ratio)
        frame = cv2.resize(frame, (target_width, target_height))  # Resize to fit the window
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert the frame to QImage
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # Convert QImage to QPixmap and display it in the QLabel
        pixmap = QPixmap.fromImage(q_image)
        self.video_frame.setPixmap(pixmap)

    def stop_video(self):
        """Stop the video and audio playback."""
        if self.cap:
            self.cap.release()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        if self.timer and self.timer.isActive():
            self.timer.stop()
        self.video_frame.clear()  # Clear the video display

    def aggregate_attention_seconds_percentage(self, start_time, end_time):
        """
           Calculate the percentage of 'Attentive' or 'Confused' records
           within the specified time interval [start_time, end_time].
           """
        attentive_count = 0
        total_count = 0

        for entry in self.attention_data:
            timestamp = entry["timestamp"]
            state = entry["state"]

            # Check if the timestamp is within the interval
            if start_time <= timestamp <= end_time:
                total_count += 1  # Count all records in the interval
                if state in {"Attentive", "Confused"}:
                    attentive_count += 1  # Count only attentive or confused states

        # Calculate percentage
        if total_count > 0:
            percentage_attentive = (attentive_count / total_count) * 100
        else:
            percentage_attentive = 0  # Avoid division by zero

        return percentage_attentive

    def load_word_subtitles(self, word_file):
        """Load word-by-word subtitles and map to phrase-level colors."""
        with open(word_file, 'r', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                start_time = float(row['Start Time'])
                end_time = float(row['End Time'])
                word = row['Word'].strip()

                # Find the phrase this word belongs to
                phrase_color = "#ffffff"  # Default color (white)
                '''for subtitle in self.subtitles:
                    if subtitle['start'] <= start_time < subtitle['end']:
                        phrase_color = subtitle['color']
                        break
                '''
                # Append the word with its phrase's color
                self.word_subtitles.append({
                    "start": start_time,
                    "end": end_time,
                    "word": word,
                    # "color": phrase_color,
                    'processed': False
                })

    def display_words(self, current_time):
        """Display words in the QListWidget based on the current time."""
        # Determine the interval based on the 10-second blocks
        interval_start = (current_time // 10) * 10
        interval_end = interval_start + 10
        cell_index = int(interval_start) // 10

        # Calculate the percentage of attentiveness (replace with your logic)
        percentage_attentive = self.aggregate_attention_seconds_percentage(interval_start, interval_end)

        # Determine color based on attentiveness percentage
        if percentage_attentive >= 70:
            color = '#4CAF50'  # High attentiveness
        elif percentage_attentive >= 50:
            color = '#FFB300'  # Moderate attentiveness
        else:
            color = '#F44336'  # Low attentiveness

        # Build the text for the current interval
        current_interval_text = ""
        for word in self.word_subtitles:
            word_start = word['start']
            word_end = word['end']

            # Only consider the words within the current 10-second interval
            if interval_start <= word_start < interval_end:
                if word_start <= current_time:  # Display the word if its start time has passed
                    current_interval_text += word['word'] + " "

        # Update the QListWidget
        if hasattr(self, 'subtitle_listbox'):
            if cell_index >= 0:  # If the cell index is valid
                if cell_index < self.subtitle_listbox.count():  # If the cell already exists
                    item = self.subtitle_listbox.item(cell_index)
                    if item is not None:
                        item.setText(current_interval_text.strip())
                        item.setBackground(QColor(color))
                    else:
                        print(f"Warning: Item at index {cell_index} is None.")
                else:  # If the cell does not exist, add a new item
                    self.subtitle_listbox.addItem(current_interval_text.strip())
                    item = self.subtitle_listbox.item(cell_index)
                    if item is not None:
                        item.setBackground(QColor(color))
                    else:
                        print(f"Warning: Failed to add item at index {cell_index}.")

                # Scroll to the current item
                item = self.subtitle_listbox.item(cell_index)
                if item is not None:
                    self.subtitle_listbox.scrollToItem(item)
                else:
                    print(f"Warning: Item at index {cell_index} is None, cannot scroll.")
            else:
                print(f"Warning: Invalid cell_index {cell_index}.")
        else:
            print("Warning: subtitle_listbox is not initialized.")

    def load_attention_data(self):
        """ Load attentiveness data from the CSV file. """
        attention_data = []
        with open(self.csv_path, 'r', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Clean up column names by stripping extra spaces
            reader.fieldnames = [field.strip() for field in reader.fieldnames]

            for row in reader:
                # Make sure the column exists
                if 'Timestamp' in row:
                    timestamp = int(float(row['Timestamp']))  # Convert '1.0' to 1
                else:
                    print("Timestamp not found in row:", row)
                    continue  # Skip this row if 'Timestamp' is missing

                person_id = row['Name']
                state = row['State']
                attention_data.append({
                    "timestamp": timestamp,
                    "person_id": person_id,
                    "state": state
                })
        return attention_data

    def display_inattentive_students(self):
        """Display inattentive students with descriptive phrases, streak tracking, and colored intervals, storing the data."""
        # Clear the previous stored data (if any)
        self.display_data = []  # This will store the formatted data for later use

        grouped_data = self.group_attentiveness_by_interval(interval=60)
        print("grouped_data=>", grouped_data)
        # Initialize state tracking for streaks
        if not hasattr(self, "student_streaks"):
            self.student_streaks = {}

        # Process each interval and store the data
        for interval, students in grouped_data.items():
            interval_text = []  # Collect all text for this interval
            for student, stats in students.items():
                total_count = stats["total_count"]
                attentive_count = stats["attentive_count"]
                attentiveness_percentage = (attentive_count / total_count * 100) if total_count > 0 else 0

                # Initialize streak tracking if needed
                if student not in self.student_streaks:
                    self.student_streaks[student] = {"streak": 0, "last_state": "Attentive"}

                # Determine the symbol, tag, and phrase based on attentiveness percentage
                if attentiveness_percentage <= 50:
                    # symbol = " 🚨"
                    tag = "red"
                    current_state = "Inattentive"
                    phrase = f" {student}"
                elif attentiveness_percentage <= 70:
                    # symbol = "⚠️"
                    tag = "yellow"
                    current_state = "Inconsistent"
                    phrase = f" {student}"
                else:
                    # symbol = "⬤"
                    tag = "green"
                    current_state = "Attentive"
                    phrase = f" {student}"

                # Update streak based on state
                if current_state == self.student_streaks[student]["last_state"]:
                    self.student_streaks[student]["streak"] += 1  # Increment streak by interval (e.g., 5 minutes)
                else:
                    self.student_streaks[student]["streak"] = 1  # Reset streak on state change

                self.student_streaks[student]["last_state"] = current_state

                # Adjust phrase to include streak information
                streak_minutes = self.student_streaks[student]["streak"]
                if current_state == "Inattentive":
                    phrase += f"  totally inattentive for {streak_minutes} minutes."
                elif current_state == "Attentive":
                    phrase += f"  has been attentive for {streak_minutes} minutes."
                elif current_state == "Inconsistent":  # Handle yellow state streak
                    phrase += f"  partially inattentive for {streak_minutes} minutes."

                # Append this phrase to the interval_text
                interval_text.append((phrase, tag))

            # Store the interval's data into the main display data list
            self.display_data.append((interval, interval_text))

        print(f"Stored Data: {self.display_data}")  # Optional: Debugging to check the stored data

    def group_attentiveness_by_interval(self, interval=300):
        """Group attentiveness data into intervals for each student."""
        grouped_data = {}
        for entry in self.attention_data:
            student = entry["person_id"]
            timestamp = entry["timestamp"]
            state = entry["state"]

            # Determine the interval in seconds (e.g., 300-600 seconds)
            interval_start = (timestamp // interval) * interval
            interval_end = interval_start + interval
            interval_label = f"[{interval_start // 60}-{interval_end // 60}] min"

            # Initialize interval structure
            if interval_label not in grouped_data:
                grouped_data[interval_label] = {}

            # Initialize student data
            if student not in grouped_data[interval_label]:
                grouped_data[interval_label][student] = {"attentive_count": 0, "total_count": 0}

            # Update counts
            if state in ["Attentive", "Confused"]:  # Treat "Confused" as "Attentive"
                grouped_data[interval_label][student]["attentive_count"] += 1
            grouped_data[interval_label][student]["total_count"] += 1

        return grouped_data

    from PIL import Image
    from PyQt5.QtGui import QImage, QPixmap, QTextCursor, QTextCharFormat, QColor
    import os
    from PIL import Image
    import os
    '''
    def display_text_for_selected_interval(self, interval_label):
        """Display text related to the selected interval (e.g., 0-5, 5-10, etc.)."""
        print(f"Selected interval {interval_label}")

        # Ensure `self.displayed_images` is initialized
        if not hasattr(self, 'displayed_images'):
            self.displayed_images = set()

        if interval_label in self.interval_processed:
            return

        # Find the corresponding interval data from self.display_data
        for interval, interval_text in self.display_data:
            if interval == interval_label:
                self.attentiveness_text.clear()  # Clear the text box before displaying new content
                self.interval_processed.add(interval_label)

                for phrase, tag in interval_text:
                    try:
                        cursor = self.attentiveness_text.textCursor()
                        cursor.movePosition(QTextCursor.End)

                        # Insert the image if required
                        if tag in ["red", "yellow"]:  # Example: Add images for specific tags
                            image_file = "alert.png" if tag == "red" else "warning.png"
                            pixmap = QPixmap(image_file)

                            # Scale the image to 40x40 pixels
                            pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                            # Insert the image
                            image_format = QTextImageFormat()
                            image_format.setName(image_file)
                            image_format.setWidth(pixmap.width())  # Set the width of the image
                            image_format.setHeight(pixmap.height())  # Set the height of the image
                            cursor.insertImage(image_format)

                            # Store the image reference to avoid garbage collection
                            if not hasattr(self.attentiveness_text, 'image_refs'):
                                self.attentiveness_text.image_refs = []
                            self.attentiveness_text.image_refs.append(pixmap)

                        # Create a QTextCharFormat for styling the text
                        char_format = QTextCharFormat()

                        # Set the text color based on the tag
                        if tag == "red":
                            char_format.setForeground(QColor("red"))
                        elif tag == "yellow":
                            char_format.setForeground(QColor("orange"))
                        else:
                            char_format.setForeground(QColor("black"))  # Default color

                        # Set the text size to be larger (e.g., 14 points)
                        font = QFont()
                        font.setPointSize(25)
                        char_format.setFont(font)

                        # Apply the char format to the text
                        cursor.insertText(f"{phrase}\n\n", char_format)

                    except Exception as e:
                        print(f"Error handling phrase '{phrase}' with tag '{tag}': {e}")

                break
    '''
    '''
    def display_text_for_selected_interval(self, interval_label):
        """Display text related to the selected interval (e.g., 0-5, 5-10, etc.)."""
        print(f"Selected interval {interval_label}")

        # Ensure `self.displayed_images` is initialized
        if not hasattr(self, 'displayed_images'):
            self.displayed_images = set()

        if interval_label in self.interval_processed:
            return

        # Find the corresponding interval data from self.display_data
        for interval, interval_text in self.display_data:
            if interval == interval_label:
                self.attentiveness_text.clear()  # Clear the text box before displaying new content
                self.interval_processed.add(interval_label)

                for phrase, tag in interval_text:
                    try:
                        cursor = self.attentiveness_text.textCursor()
                        cursor.movePosition(QTextCursor.End)

                        # Create a QTextCharFormat for styling the text and emoji
                        char_format = QTextCharFormat()

                        # Set the text color based on the tag
                        if tag == "red":
                            char_format.setForeground(QColor("#D21F3C"))
                        elif tag == "yellow":
                            char_format.setForeground(QColor("#F28500"))
                        else:
                            char_format.setForeground(QColor("black"))  # Default color

                        # Set the text size to be larger (e.g., 23 points)
                        font = QFont()
                        font.setPointSize(23)
                        char_format.setFont(font)

                        # Insert an emoji based on the tag
                        if tag in ("red", "yellow"):
                            if tag == "red":  # Use alert emoji for "red"
                                emoji = "🚨"  # Alert emoji
                            elif tag == "yellow":  # Use warning emoji for "yellow"
                                emoji = "⚠️"  # Warning emoji

                            # Apply the char format to the emoji
                            cursor.insertText(emoji + " ", char_format)

                            # Apply the char format to the text
                            cursor.insertText(f"{phrase}\n\n", char_format)

                    except Exception as e:
                        print(f"Error handling phrase '{phrase}' with tag '{tag}': {e}")

                break
    '''
    from PyQt5.QtGui import QPixmap, QTextCursor, QTextCharFormat, QColor, QTextImageFormat, QFont
    from PyQt5.QtCore import Qt

    def display_text_for_selected_interval(self, interval_label):
        """Display text related to the selected interval (e.g., 0-5, 5-10, etc.)."""
        print(f"Selected interval {interval_label}")

        # Ensure `self.displayed_images` is initialized
        if not hasattr(self, 'displayed_images'):
            self.displayed_images = set()

        if interval_label in self.interval_processed:
            return

        # Find the corresponding interval data from self.display_data
        for interval, interval_text in self.display_data:
            if interval == interval_label:
                self.attentiveness_text.clear()  # Clear the text box before displaying new content
                self.interval_processed.add(interval_label)

                for phrase, tag in interval_text:
                    try:
                        cursor = self.attentiveness_text.textCursor()
                        cursor.movePosition(QTextCursor.End)

                        # Create a QTextCharFormat for styling the text
                        char_format = QTextCharFormat()

                        # Set the text color based on the tag
                        if tag == "red":
                            char_format.setForeground(QColor("#D21F3C"))
                        elif tag == "yellow":
                            char_format.setForeground(QColor("#F28500"))
                        else:
                            char_format.setForeground(QColor("black"))  # Default color

                        # Set the text size to be larger (e.g., 23 points)
                        font = QFont()
                        font.setPointSize(23)
                        char_format.setFont(font)

                        # Load 3D icons based on the tag
                        icon_path = ""
                        if tag == "red":
                            icon_path = "alert.png"  # Path to red alert icon
                        elif tag == "yellow":
                            icon_path = "warning.png"  # Path to yellow warning icon

                        # Insert the icon if the tag is "red" or "yellow"
                        if tag in ("red", "yellow"):
                            # Load the icon as a QPixmap
                            icon_pixmap = QPixmap(icon_path)

                            # Insert the icon
                            icon_format = QTextImageFormat()
                            icon_format.setName(icon_path)  # Set the icon path
                            icon_format.setWidth(45)  # Set icon width (adjust as needed)
                            icon_format.setHeight(45)  # Set icon height (adjust as needed)
                            cursor.insertImage(icon_format)

                            # Insert a space after the icon
                            cursor.insertText(" ", char_format)

                            # Insert the text with the char format
                            cursor.insertText(f"{phrase}\n\n", char_format)

                    except Exception as e:
                        print(f"Error handling phrase '{phrase}' with tag '{tag}': {e}")

                break

    def calculate_cumulative_data(self):
        """Calculate and store cumulative performance data for all intervals."""
        if not hasattr(self, "cumulative_streak_data"):
            self.cumulative_streak_data = []  # Initialize array

        # Clear and recalculate cumulative data
        self.cumulative_streak_data.clear()

        grouped_data = self.group_attentiveness_by_interval(interval=60)

        # Variables to store cumulative counts
        cumulative_attentive_count = 0
        cumulative_total_count = 0

        for interval_label, students in grouped_data.items():
            interval_attentive_count = 0
            interval_total_count = 0

            # Sum counts for the current interval
            for stats in students.values():
                interval_total_count += stats["total_count"]
                interval_attentive_count += stats["attentive_count"]

            cumulative_total_count += interval_total_count
            cumulative_attentive_count += interval_attentive_count

            if cumulative_total_count == 0:
                attentiveness_percentage = 0
                current_state = "No data"
                streak = 0
            else:
                attentiveness_percentage = (cumulative_attentive_count / cumulative_total_count) * 100

                # Determine the current state
                if attentiveness_percentage <= 50:
                    current_state = "Inattentive"
                elif attentiveness_percentage <= 70:
                    current_state = "Inconsistent"
                else:
                    current_state = "Attentive"

                # Determine streak
                if not self.cumulative_streak_data:
                    streak = 1  # First interval
                else:
                    _, _, last_state, last_streak = self.cumulative_streak_data[-1]
                    streak = last_streak + 1 if current_state == last_state else 1

            # Store cumulative data
            self.cumulative_streak_data.append(
                (interval_label, attentiveness_percentage, current_state, streak)
            )
            print("cumulative_streak_data=>", self.cumulative_streak_data)
    '''
    def display_text_for_selected_interval_cumulative(self, interval_label):
        """Display text related to the selected interval (e.g., 0-5, 5-10, etc.)."""
        print('cumulative_interval=>>', interval_label)

        # Initialize a set to track displayed images
        if not hasattr(self, 'displayed_images'):
            self.displayed_images = set()  # Initialize as a set, not a list

        if interval_label in self.cumulative_interval_processed:
            return

        # Find the corresponding interval in cumulative data
        for interval, attentiveness_percentage, state, streak in self.cumulative_streak_data:
            if interval == interval_label:
                self.cumulative_interval_processed.add(interval_label)
                self.attentiveness_all_class.clear()  # Clear existing content

                if state == "No data":
                    phrase = "No data available for this interval."
                    tag = "red"
                elif state == "Inattentive":
                    phrase = f"The class is mostly inattentive ({attentiveness_percentage:.2f}% only attentive) for {streak} minutes."
                    tag = "red"
                elif state == "Inconsistent":
                    phrase = f"The class is partially inattentive ({attentiveness_percentage:.2f}% only attentive) for {streak} minutes."
                    tag = "yellow"
                else:
                    phrase = f"The class is highly attentive ({attentiveness_percentage:.2f}% attentive) for {streak} minutes."
                    tag = "green"

                # Check if an image needs to be inserted for this tag
                image_file = None
                if tag == "red":
                    image_file = "alert.png"  # Replace with your image file
                elif tag == "yellow":
                    image_file = "warning.png"  # Replace with your image file
                elif tag == "green":
                    image_file = "success.png"  # Replace with your image file

                # Insert image and text
                cursor = self.attentiveness_all_class.textCursor()
                cursor.movePosition(QTextCursor.End)

                if image_file:
                    try:
                        # Load and scale the image
                        pixmap = QPixmap(image_file)
                        pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                        # Insert the image
                        image_format = QTextImageFormat()
                        image_format.setName(image_file)
                        image_format.setWidth(pixmap.width())
                        image_format.setHeight(pixmap.height())
                        cursor.insertImage(image_format)

                        # Store the image reference to prevent garbage collection
                        if not hasattr(self.attentiveness_all_class, 'image_refs'):
                            self.attentiveness_all_class.image_refs = []
                        self.attentiveness_all_class.image_refs.append(pixmap)
                    except Exception as e:
                        print(f"Error displaying image: {e}")

                # Create a QTextCharFormat for styling the text
                char_format = QTextCharFormat()

                # Set the text color based on the tag
                if tag == "red":
                    char_format.setForeground(QColor("red"))
                elif tag == "yellow":
                    char_format.setForeground(QColor("orange"))
                elif tag == "green":
                    char_format.setForeground(QColor("green"))
                else:
                    char_format.setForeground(QColor("black"))  # Default color

                # Set the text size to be larger (e.g., 20 points)
                font = self.attentiveness_all_class.font()
                font.setPointSize(25)  # Increase the font size to 20 points
                char_format.setFont(font)

                # Insert the text with the char format
                cursor.insertText(f" {phrase}\n", char_format)

                break

      '''
    '''
    def display_text_for_selected_interval_cumulative(self, interval_label):
        """Display text related to the selected interval (e.g., 0-5, 5-10, etc.)."""
        print('cumulative_interval=>>', interval_label)

        # Initialize a set to track displayed images
        if not hasattr(self, 'displayed_images'):
            self.displayed_images = set()  # Initialize as a set, not a list

        if interval_label in self.cumulative_interval_processed:
            return

        # Find the corresponding interval in cumulative data
        for interval, attentiveness_percentage, state, streak in self.cumulative_streak_data:
            if interval == interval_label:
                self.cumulative_interval_processed.add(interval_label)
                self.attentiveness_all_class.clear()  # Clear existing content

                if state == "No data":
                    phrase = "No data available for this interval."
                    tag = "red"
                elif state == "Inattentive":
                    phrase = f"The class is mostly inattentive ({attentiveness_percentage:.2f}% only attentive) for {streak} minutes."
                    tag = "red"
                elif state == "Inconsistent":
                    phrase = f"The class is partially inattentive ({attentiveness_percentage:.2f}% only attentive) for {streak} minutes."
                    tag = "yellow"
                else:
                    phrase = f"The class is highly attentive ({attentiveness_percentage:.2f}% attentive) for {streak} minutes."
                    tag = "green"

                # Insert emoji based on the tag
                emoji = ""
                if tag == "red":
                    emoji = "🚨"  # Alert emoji
                elif tag == "yellow":
                    emoji = "⚠️"  # Warning emoji
                elif tag == "green":
                    emoji = "✅"  # Success emoji

                # Insert emoji and text
                cursor = self.attentiveness_all_class.textCursor()
                cursor.movePosition(QTextCursor.End)

                # Create a QTextCharFormat for styling the text
                char_format = QTextCharFormat()

                # Set the text color based on the tag
                if tag == "red":
                    char_format.setForeground(QColor("#D21F3C"))
                elif tag == "yellow":
                    char_format.setForeground(QColor("#F28500"))
                elif tag == "green":
                    char_format.setForeground(QColor("green"))
                else:
                    char_format.setForeground(QColor("black"))  # Default color

                # Set the text size to be larger (e.g., 20 points)
                font = self.attentiveness_all_class.font()
                font.setPointSize(23)  # Increase the font size to 20 points
                char_format.setFont(font)

                # Insert the emoji and text with the char format
                cursor.insertText(f"{emoji} {phrase}\n", char_format)

                break
    '''
    from PyQt5.QtGui import QPixmap, QTextCursor, QTextCharFormat, QColor, QTextDocument, QTextImageFormat
    from PyQt5.QtCore import Qt

    def display_text_for_selected_interval_cumulative(self, interval_label):
        """Display text related to the selected interval (e.g., 0-5, 5-10, etc.)."""
        print('cumulative_interval=>>', interval_label)

        # Initialize a set to track displayed images
        if not hasattr(self, 'displayed_images'):
            self.displayed_images = set()  # Initialize as a set, not a list

        if interval_label in self.cumulative_interval_processed:
            return

        # Find the corresponding interval in cumulative data
        for interval, attentiveness_percentage, state, streak in self.cumulative_streak_data:
            if interval == interval_label:
                self.cumulative_interval_processed.add(interval_label)
                self.attentiveness_all_class.clear()  # Clear existing content

                if state == "No data":
                    phrase = "No data available for this interval."
                    tag = "red"
                elif state == "Inattentive":
                    phrase = f"The class is mostly inattentive ({attentiveness_percentage:.2f}% only attentive) for {streak} minutes."
                    tag = "red"
                elif state == "Inconsistent":
                    phrase = f"The class is partially inattentive ({attentiveness_percentage:.2f}% only attentive) for {streak} minutes."
                    tag = "yellow"
                else:
                    phrase = f"The class is highly attentive ({attentiveness_percentage:.2f}% attentive) for {streak} minutes."
                    tag = "green"

                # Load 3D icons based on the tag
                icon_path = ""
                if tag == "red":
                    icon_path = "alert.png"  # Path to red alert icon
                elif tag == "yellow":
                    icon_path = "warning.png"  # Path to yellow warning icon
                elif tag == "green":
                    icon_path = "success_3d.png"  # Path to green success icon

                # Load the icon as a QPixmap
                icon_pixmap = QPixmap(icon_path)

                # Insert the icon and text into the QTextEdit
                cursor = self.attentiveness_all_class.textCursor()
                cursor.movePosition(QTextCursor.End)

                # Create a QTextCharFormat for styling the text
                char_format = QTextCharFormat()

                # Set the text color based on the tag
                if tag == "red":
                    char_format.setForeground(QColor("#D21F3C"))
                elif tag == "yellow":
                    char_format.setForeground(QColor("#F28500"))
                elif tag == "green":
                    char_format.setForeground(QColor("green"))
                else:
                    char_format.setForeground(QColor("black"))  # Default color

                # Set the text size to be larger (e.g., 20 points)
                font = self.attentiveness_all_class.font()
                font.setPointSize(23)  # Increase the font size to 20 points
                char_format.setFont(font)

                # Insert the icon
                icon_format = QTextImageFormat()
                icon_format.setName(icon_path)  # Set the icon path
                icon_format.setWidth(45)  # Set icon width (adjust as needed)
                icon_format.setHeight(45)  # Set icon height (adjust as needed)
                cursor.insertImage(icon_format)

                # Insert the text with the char format
                cursor.insertText(f" {phrase}\n", char_format)

                break

def set_dark_theme(app):
    """Set a dark theme for the application."""
    # Set dark palette
    dark_palette = QPalette()

    # Base colors
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    # Disabled colors
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

    # Set the palette
    app.setPalette(dark_palette)

    # Set stylesheet
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a82da;
            border: 1px solid white;
        }
        QPushButton {
            background-color: #353535;
            border: 1px solid #555;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #454545;
        }
        QPushButton:pressed {
            background-color: #252525;
        }
    """)


if __name__ == "__main__":
    # Paths to video and audio files
    video_path = "D:/Jan9_cropped_video_First_Grade_Zoom_try2.mp4"
    audio_path = "D:/cropped_video_First_Grade_Zoom_7_minutes_audio.mp3"
    csv_path = "D:/YOLO model/Jan9_cropped_video_First_Grade_Zoom_try2.csv"
    transcription = "D:/YOLO model/First_Grade_Zoom_transcription.csv"

    # Create the application
    app = QApplication(sys.argv)
    #set_dark_theme(app)
    player = VideoPlayer(video_path, audio_path, csv_path=csv_path, transcription_file=transcription)
    player.show()
    sys.exit(app.exec_())
