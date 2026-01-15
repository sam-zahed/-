
import face_recognition
import os
import cv2
import numpy as np
import logging

class FaceRecognizer:
    def __init__(self, faces_dir: str = "/code/app/data/faces"):
        self.faces_dir = faces_dir
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Ensure directory exists
        if not os.path.exists(self.faces_dir):
            try:
                os.makedirs(self.faces_dir, exist_ok=True)
            except Exception as e:
                logging.warning(f"Could not create faces dir: {e}")
            
        self.load_known_faces()

    def load_known_faces(self):
        """Loads all valid face images from the faces directory."""
        self.known_face_encodings = []
        self.known_face_names = []
        
        if not os.path.exists(self.faces_dir):
            # logging.warning(f"Faces directory {self.faces_dir} not found.")
            return

        print(f"Loading faces from {self.faces_dir}...")
        for filename in os.listdir(self.faces_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    path = os.path.join(self.faces_dir, filename)
                    name = os.path.splitext(filename)[0]
                    
                    # Load and encode
                    image = face_recognition.load_image_file(path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_names.append(name)
                        print(f"Loaded face: {name}")
                    else:
                        print(f"No face found in {filename}")
                except Exception as e:
                    print(f"Error loading face {filename}: {e}")
        
        print(f"Total faces loaded: {len(self.known_face_names)}")

    def register_face(self, name: str, image_bytes: bytes) -> bool:
        """Saves a new face image and reloads encodings."""
        try:
            file_path = os.path.join(self.faces_dir, f"{name}.jpg")
            
            # Write bytes to file
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            # Verify if it has a face
            image = face_recognition.load_image_file(file_path)
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                os.remove(file_path)
                return False
                
            # Reload to update memory
            self.load_known_faces()
            return True
        except Exception as e:
            print(f"Failed to register face {name}: {e}")
            return False

    def identify_faces(self, image_numpy: np.ndarray) -> list:
        """
        Identifies faces in the provided RGB numpy image.
        Returns a list of names found (e.g., ['Ahmed', 'Unknown']).
        """
        if not self.known_face_encodings:
            return []

        # Find faces in the frame
        # We assume image_numpy is RGB. If BGR (from cv2), convert it?
        # Typically YOLO/Detector passes RGB. We'll ensure that.
        
        face_locations = face_recognition.face_locations(image_numpy)
        face_encodings = face_recognition.face_encodings(image_numpy, face_locations)

        found_names = []
        
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]

            found_names.append(name)
            
        return found_names
