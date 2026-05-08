import logging
import warnings
from pathlib import Path

import cv2
import numpy as np

warnings.filterwarnings("ignore", message=".*estimate.*deprecated.*", category=FutureWarning)
from insightface.app import FaceAnalysis


PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}


class FaceRecognizer:
    def __init__(self, reference_dir, similarity_threshold=0.4, det_size=(640, 640), name_map=None):
        self.similarity_threshold = similarity_threshold
        self.name_map = name_map or {}

        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=-1, det_size=det_size)

        self.centroids = self._load_references(Path(reference_dir))
        if self.centroids:
            logging.info(f"Face recognition: loaded {len(self.centroids)} persons: {', '.join(self.centroids.keys())}")
        else:
            logging.warning("Face recognition: no reference embeddings loaded")

    def _load_references(self, reference_dir):
        centroids = {}
        for person_dir in sorted(reference_dir.iterdir()):
            if not person_dir.is_dir():
                continue
            embeddings = []
            for img_file in sorted(person_dir.iterdir()):
                if img_file.suffix.lower() not in PHOTO_EXTENSIONS:
                    continue
                img = cv2.imread(str(img_file))
                if img is None:
                    logging.warning(f"Face ref: cannot read {img_file}")
                    continue
                faces = self.app.get(img)
                if len(faces) == 0:
                    logging.warning(f"Face ref: no face in {img_file}")
                elif len(faces) > 1:
                    logging.warning(f"Face ref: multiple faces in {img_file}, skipping")
                else:
                    embeddings.append(faces[0].embedding)
            if embeddings:
                centroids[person_dir.name] = np.mean(embeddings, axis=0)
            else:
                logging.warning(f"Face ref: no usable faces for '{person_dir.name}'")
        return centroids

    def _resolve_name(self, folder_name):
        if folder_name in self.name_map:
            return self.name_map[folder_name]
        return folder_name[0].upper() + folder_name[1:]

    def identify_faces(self, image_path):
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return []
            faces = self.app.get(img)
            if not faces:
                return []
        except Exception as e:
            logging.warning(f"Face detection failed for {image_path}: {e}")
            return []

        identified = []
        for face in faces:
            best_name = None
            best_score = -1
            for name, centroid in self.centroids.items():
                score = np.dot(face.embedding, centroid) / (
                    np.linalg.norm(face.embedding) * np.linalg.norm(centroid)
                )
                if score > best_score:
                    best_score = score
                    best_name = name
            if best_name and best_score >= self.similarity_threshold:
                display_name = self._resolve_name(best_name)
                if display_name not in identified:
                    identified.append(display_name)

        return identified
