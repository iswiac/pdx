import yaml
import os
import re
import json
import base64
import requests
import shutil
import logging
import subprocess
import reverse_geocoder as rg
from io import BytesIO
from pathlib import Path
from datetime import datetime
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()
from pdx.qdrant import VDB
from pdx.prompts import PROMPTS

class Organizer:
    def __init__(self, collection: str, target_dir: str, config_path: str = "config.yaml"):
        """Initializes the organizer with database access, VLM configuration and configuration file."""
        self.config_path = Path(config_path)
        self.vdb = VDB(cname=collection)
        self.target_dir = Path(target_dir)

        # Load Configuration
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Offloaded Personal Data
        self.ollama_url = config["ai"]["ollama_url"]
        self.model_name = config["ai"]["model_name"]
        self.home_locations = config["location"]["home_names"]
        self.lang = PROMPTS[config["ai"].get("language", "cs")]

        # Offloaded Paths
        self.context_file = Path(config["storage"]["context_file"])
        self.history_file = Path(config["storage"]["history_file"])

        # Face recognition (optional)
        self.face_recognizer = None
        faces_config = config.get("faces", {})
        ref_dir = faces_config.get("reference_dir")
        if ref_dir:
            ref_path = Path(ref_dir).expanduser()
            if not ref_path.is_absolute():
                ref_path = self.config_path.parent / ref_path
            if ref_path.is_dir():
                try:
                    from pdx.faces import FaceRecognizer
                    self.face_recognizer = FaceRecognizer(
                        str(ref_path),
                        similarity_threshold=faces_config.get("similarity_threshold", 0.4),
                        det_size=tuple(faces_config.get("det_size", [640, 640])),
                        name_map=faces_config.get("name_map", {}),
                    )
                except ImportError:
                    logging.warning("insightface not installed, face recognition disabled")
            else:
                logging.warning(f"Face reference dir not found: {ref_path}")

    def load_context(self):
        if self.context_file.exists():
            return self.context_file.read_text(encoding="utf-8")
        return self.lang["fallback_context"]

    def get_history(self, max_examples=25):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    history.sort()
                    return history[-max_examples:]
            except Exception:
                return []
        return []

    def get_exif_metadata(self, file_path):
        """Modified: Distinctly handles Home, Known, and Unknown locations."""
        try:
            cmd = ["exiftool", "-s", "-DateTimeOriginal", "-City", "-State", "-Country",
                   "-GPSLatitude", "-GPSLongitude", "-n", str(file_path)]
            output = subprocess.check_output(cmd).decode().strip()
            meta = {l.split(':', 1)[0].strip(): l.split(':', 1)[1].strip() for l in output.split('\n') if ':' in l}

            d_str = meta.get('DateTimeOriginal') or meta.get('Date/Time Original')
            date_obj = datetime.strptime(d_str, "%Y:%m:%d %H:%M:%S") if d_str else datetime.fromtimestamp(file_path.stat().st_mtime)

            lat, lon = meta.get('GPSLatitude'), meta.get('GPSLongitude')
            city_tag = meta.get('City', '')

            location_str = ""

            if lat and lon:
                res = rg.search((float(lat), float(lon)))[0]
                city_name = res.get('name', '')
                if not any(h.lower() == city_name.lower() for h in self.home_locations):
                    location_str = f"{city_name}, {res.get('cc', '')}"

            if not location_str and city_tag:
                if not any(h.lower() == city_tag.lower() for h in self.home_locations):
                    location_str = city_tag

            if not location_str:
                if city_tag or (lat and lon):
                    return date_obj, ""
                return date_obj, self.lang["unknown_location"]

            return date_obj, location_str
        except Exception:
            return datetime.fromtimestamp(file_path.stat().st_mtime), self.lang["unknown_location"]

    def polish_description(self, text):
        if not text or self.lang["various_check"] in text:
            return self.lang["default_description"]
        combined_pattern = "|".join(self.lang["meta_patterns"])
        text = re.sub(combined_pattern, '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d{2,8}\s*[-–:]*\s*', '', text)
        text = text.replace(",", " ").replace(".", " ")
        text = re.sub(r'(.)\1{2,}', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
        text = re.sub(r'\s+', ' ', text).strip()
        words = text.split()
        if not words:
            return self.lang["default_description"]
        words[0] = words[0][:1].upper() + words[0][1:]
        trailing = self.lang["trailing_prepositions"]
        if len(words) > 1 and words[-1].lower() in trailing:
            words.pop()
        return " ".join(words[:7]).strip()

    def get_ai_description(self, image_path, location, date_obj=None, identified_names=None):
        try:
            if Path(image_path).suffix.lower() in ('.heic', '.heif'):
                buf = BytesIO()
                Image.open(image_path).convert("RGB").save(buf, format="JPEG", quality=85)
                img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
            else:
                with open(image_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
            home = self.lang["home_label"]
            if identified_names:
                face_instruction = self.lang["face_identified"].format(names=', '.join(identified_names))
            else:
                face_instruction = self.lang["face_not_identified"]
            system_instruction = (
                f"{self.lang['system_prompt']}\n"
                f"{self.load_context()}\n"
                f"{face_instruction}"
            )
            date_line = f"{self.lang['photo_date_label']}: {date_obj.strftime('%Y-%m-%d')}.\n" if date_obj else ""
            names_line = f"{self.lang['recognized_persons_label']}: {', '.join(identified_names)}.\n" if identified_names else ""
            user_request = self.lang["user_request"].format(
                date_line=date_line,
                location=location or home,
                names_line=names_line,
                home=home,
            )
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_request, "images": [img_data]},
                ],
                "stream": False,
                "think": False,
                "options": {"temperature": 0.1, "num_predict": 50}
            }
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            description = response.json().get('message', {}).get('content', '').strip()
            return self.polish_description(description)
        except Exception as e:
            logging.error(f"❌ {self.lang['error_ai_failed']} {image_path}: {e}")
            return self.lang["default_description_singular"]

    def get_folder_summary(self, descriptions, location, day):
        unique_descs = list(dict.fromkeys(descriptions))
        home = self.lang["home_label"]
        history = self.get_history()
        history_line = ""
        if history:
            examples = ", ".join(h.split(" - ", 1)[1] for h in history if " - " in h)
            history_line = self.lang["history_examples"].format(examples=examples) + "\n"
        user_request = self.lang["folder_summary"].format(
            location=location or home,
            photos=', '.join(unique_descs),
            home=home,
            history_line=history_line,
        )
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": user_request}],
            "stream": False, "think": False,
            "options": {"temperature": 0.1, "stop": ["\n"]}
        }
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            summary = response.json().get('message', {}).get('content', '').strip()
            return self.polish_description(summary)
        except Exception: return self.lang["default_folder"]

    def organize(self):
        """Main Loop: Corrected to handle 'is None' vs 'empty string' for Home logic."""
        logging.info(f"Retrieving points from: {self.vdb.cname}")
        response = self.vdb.client.scroll(collection_name=self.vdb.cname, limit=10000, with_payload=True)[0]

        days = {}
        for point in response:
            path = Path(point.payload["path"])
            if not path.exists(): continue

            s_date = point.payload.get("date")
            s_loc = point.payload.get("location")
            description = point.payload.get("description")

            if s_date is None or s_loc is None:
                date_obj, location = self.get_exif_metadata(path)
                date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                logging.info(f"   🔍 Extraction for {path.name}: 📍 {location if location else self.lang['home_label']}")
            else:
                date_obj = datetime.strptime(s_date, "%Y-%m-%d %H:%M:%S")
                location = s_loc
                date_str = s_date

            if not description:
                identified_names = []
                if self.face_recognizer:
                    identified_names = self.face_recognizer.identify_faces(str(path))
                    if identified_names:
                        logging.info(f"   👤 Faces: {', '.join(identified_names)} in {path.name}")
                logging.info(f"   🧠 AI analyzing: {path.name} | Loc: {location if location else self.lang['home_label']}")
                description = self.get_ai_description(path, location, date_obj, identified_names)
                logging.info(f"      ✨ Result: {description}")
                self.vdb.update_payload(point.id, {"description": description, "location": location, "date": date_str})

            day_key = date_obj.strftime("%y%m%d")
            if day_key not in days:
                days[day_key] = {"year": date_obj.strftime("%Y"), "locations": [], "descriptions": [], "files": []}
            if location and location not in days[day_key]["locations"]:
                days[day_key]["locations"].append(location)
            days[day_key]["descriptions"].append(description)
            days[day_key]["files"].append(path)

        # Discover videos in the same source directories
        source_dirs = {Path(point.payload["path"]).parent for point in response if Path(point.payload["path"]).exists()}
        total_videos = 0
        if source_dirs:
            from pdx.find import find_videos
            for video_path in find_videos(source_dirs):
                date_obj, _ = self.get_exif_metadata(video_path)
                day_key = date_obj.strftime("%y%m%d")
                total_videos += 1
                if day_key in days:
                    days[day_key]["files"].append(video_path)
                    logging.info(f"   🎬 Video matched to {day_key}: {video_path.name}")
                else:
                    year = date_obj.strftime("%Y")
                    days[day_key] = {"year": year, "locations": [], "descriptions": ["Video"], "files": [video_path]}
                    logging.info(f"   🎬 Video (new day {day_key}): {video_path.name}")

        total_photos = sum(1 for p in response if Path(p.payload["path"]).exists())
        total_files = total_photos + total_videos
        total_organized = 0

        for day, info in sorted(days.items()):
            location = " / ".join(info["locations"]) if info["locations"] else ""
            folder_desc = self.get_folder_summary(info["descriptions"], location, day)
            dest = self.target_dir / info["year"] / f"{day} - {folder_desc}"
            dest.mkdir(parents=True, exist_ok=True)
            for f in info["files"]: shutil.copy2(f, dest / f.name)
            total_organized += len(info["files"])
            loc = f" 📍 {location}" if location else ""
            logging.info(f"   Done: {day} - {folder_desc} ({len(info['files'])} files){loc}")

        logging.info(f"📊 Summary: {total_organized}/{total_files} files organized "
                     f"({total_photos} photos, {total_videos} videos) into {len(days)} folders")
