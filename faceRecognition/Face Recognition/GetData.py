import tkinter as tk
from tkinter import messagebox
import cv2
import os
from datetime import datetime
import threading
from imutils import paths
import face_recognition
import pickle
from PIL import Image, ImageTk

def create_folder(name):
    dataset_folder = "/home/pi/Desktop/faceRecognition/Face Recognition/dataset"
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)
    person_folder = os.path.join(dataset_folder, name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    return person_folder


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition System")
        self.geometry("640x480")
        self.current_frame = None
        self.show_password_frame()

    def show_password_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = tk.Frame(self)
        
        tk.Label(self.current_frame, text="ENTER ADMIN PASSWORD:").pack()
        self.password_entry = tk.Entry(self.current_frame, show="*")
        self.password_entry.pack()
        tk.Button(self.current_frame, text="CONFIRM", 
                 command=self.check_password).pack()
        
        self.current_frame.pack()

    def check_password(self):
        password = self.password_entry.get()
        if password == "123456":  
            self.show_name_frame()
        else:
            messagebox.showerror("Error", "Incorrect password")

    # Display name input form
    def show_name_frame(self):
        self.current_frame.destroy()
        self.current_frame = tk.Frame(self)
        
        tk.Label(self.current_frame, text="ENTER NEW USER'S NAME:").pack()
        self.name_entry = tk.Entry(self.current_frame)
        self.name_entry.pack()
        tk.Button(self.current_frame, text="Start Capture", 
                 command=self.start_capture).pack()
        
        self.current_frame.pack()

    # Start capturing images
    def start_capture(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Enter a valid name")
            return
        
        self.name = name
        self.folder = create_folder(name)
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera")
            return
        
        self.current_frame.destroy()
        self.current_frame = tk.Frame(self)
        
        self.label = tk.Label(self.current_frame)
        self.label.pack()
        tk.Label(self.current_frame, 
                text="Press Space to capture, 'q' to exit").pack()
        
        self.bind("<space>", self.save_photo)
        self.bind("q", self.quit_capture)
        self.frame = None
        self.update_frame()
        
        self.current_frame.pack()

    # Update the camera frame
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.label.imgtk = imgtk
            self.label.configure(image=imgtk)
        self.after(10, self.update_frame)

    # Save image when SPACE is pressed
    def save_photo(self, event):
        if self.frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name}_{timestamp}.jpg"
            dataset_folder = "/home/pi/Desktop/faceRecognition/Face Recognition/dataset"
            folder_path = os.path.join(dataset_folder, self.name)

            # Ensure the folder exists
            os.makedirs(folder_path, exist_ok=True)

            filepath = os.path.join(folder_path, filename)
            cv2.imwrite(filepath, self.frame)

            print(f"Saved photo: {filepath}")

    # Exit capturing when 'q' is pressed
    def quit_capture(self, event):
        self.cap.release()
        self.unbind("<space>")
        self.unbind("q")
        self.current_frame.destroy()
        self.show_training_frame()

    # Show training message
    def show_training_frame(self):
        self.current_frame = tk.Frame(self)
        tk.Label(self.current_frame, text="Training model...").pack()
        self.current_frame.pack()
        threading.Thread(target=self.train_model).start()

    # Train the model
    def train_model(self):
        dataset_folder = "/home/pi/Desktop/faceRecognition/Face Recognition/dataset"
        encoding_file = os.path.join("/home/pi/Desktop/faceRecognition/Face Recognition", "encodings.pickle")

        imagePaths = list(paths.list_images(dataset_folder))
        knownEncodings = []
        knownNames = []

        for (i, imagePath) in enumerate(imagePaths):
            print(f"[INFO] Processing image {i + 1}/{len(imagePaths)}")
            name = imagePath.split(os.path.sep)[-2]
            image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)
            
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(name)

        print("[INFO] Saving encodings...")
        data = {"encodings": knownEncodings, "names": knownNames}

        with open(encoding_file, "wb") as f:
            f.write(pickle.dumps(data))

        print(f"[INFO] Training completed. Saved to {encoding_file}")
        self.after(0, self.show_completion_message)

    # Show completion message
    def show_completion_message(self):
        messagebox.showinfo("Notification", "Training completed. Saved to 'encodings.pickle'")
        self.destroy()

# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()
