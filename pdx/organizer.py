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
from pathlib import Path
from datetime import datetime
from pdx.qdrant import VDB

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

        # Offloaded Paths
        self.context_file = Path(config["storage"]["context_file"])
        self.history_file = Path(config["storage"]["history_file"])

    def load_context(self):
        if self.context_file.exists():
            return self.context_file.read_text(encoding="utf-8")
        return "Základní kontext: Rodina, výlety, sport."

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
                return date_obj, "Neznámá lokalita"

            return date_obj, location_str
        except Exception:
            return datetime.fromtimestamp(file_path.stat().st_mtime), "Neznámá lokalita"

    def polish_description(self, text):
        if not text or "Různé" in text: return "Momentky"
        meta_patterns = [
            r'^(zde (je|jsou) návrh[y]?|návrh[y]?|možné|seznam|složka|složky|název|popis)\s*(názvů|pro)?\s*[:\-–]*\s*',
            r'^(zde je popis obsahu fotografie|popis obsahu fotografie)\s*[:\-–]*\s*'
        ]
        combined_pattern = "|".join(meta_patterns)
        text = re.sub(combined_pattern, '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d{2,8}\s*[-–:]*\s*', '', text)
        text = text.replace(",", " ").replace(".", " ")
        text = re.sub(r'([áčďéěíňóřšťúůýž])\1+', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'[^a-zA-Z0-9 áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]', '', text)
        words = text.split()
        if not words: return "Momentky"
        words[0] = words[0][:1].upper() + words[0][1:]
        if len(words) > 1 and len(words[-1]) <= 2 and words[-1].lower() in ['v', 'na', 's', 'z', 'u', 'o']:
            words.pop()
        return " ".join(words[:7]).strip()

    def get_ai_description(self, image_path, location):
        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            system_instruction = (
                "Jsi objektivní rodinný archivář. Pro identifikaci osob a pravidla použij následující kontext: \n"
                f"KONTEXT: {self.load_context()}\n"
                "PŘÍSNÉ PRAVIDLO: Popisuj jen to, co je skutečně vidět. Nevymýšlej si jména, pokud osoba na fotce není."
                "PŘÍSNÉ PRAVIDLO: Pužívej pouze češtinu."
            )
            user_request = (
                f"KONTEXT - Lokalita: {location}. "
                "ÚKOL: Napiš stručný popis obsahu (osoby, akce, objekty) v max 6 slovech."
                "1. IDENTITY: Používej jména z kontextu pro viditelné osoby, pokud jsi si identifikací jistý."
                "2. CIZÍ LIDÉ: Pokud postavy nepoznáš, popiš je obecně (např. 'muž', 'žena', 'skupina lidí', 'diváci')."
                "3. SPORTY: Pokud je vidět dres nebo vybavení, uveď o který sport se jedná."
                "4. TECHNIKA: Když na fotce nejsou lidé buď věcný a technický."
                "PŘÍSNÉ PRAVIDLO: Do popisu NEPIŠ slovo 'Domov', název lokality ani datum."
                "PŘÍSNÉ PRAVIDLO: Nepřiřazuj jména rodiny cizím lidem."
                "Pokud na fotce nikdo z rodiny není, popiš jen dění."
            )
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": f"{system_instruction}\n\n{user_request}", "images": [img_data]}],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 35}
            }
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            description = response.json().get('message', {}).get('content', '').strip()
            return self.polish_description(description)
        except Exception as e:
            logging.error(f"❌ AI analýza selhala pro {image_path}: {e}")
            return "Momentka"

    def get_folder_summary(self, descriptions, location, day):
        unique_descs = list(dict.fromkeys(descriptions))
        user_request = (
            f"Lokalita: {location or 'Domov'}\nFOTKY: {', '.join(unique_descs)}\n"
            "ÚKOL: JEDEN český název složky (2-4 slova).\n"
            "PRAVIDLO 1: Pokud je lokalita 'Domov', v názvu ji ABSOLUTNĚ NEUVÁDĚJ (ani slova jako 'doma', 'u nás'). Soustřeď se jen na aktivitu.\n"
            "PRAVIDLO 2: Pokud je to jiná lokalita (např. Havířov, Itálie), v názvu ji zachovej v PŘESNÉM tvaru.\n"
            "PRAVIDLO 3: Odpověz POUZE výsledným názvem bez uvozovek a meta-textu."
        )
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": user_request}],
            "stream": False, "options": {"temperature": 0.1, "stop": ["\n"]}
        }
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            summary = response.json().get('message', {}).get('content', '').strip()
            return self.polish_description(summary)
        except Exception: return "Různé_aktivity"

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
                logging.info(f"   🔍 Extraction for {path.name}: 📍 {location if location else 'Domov'}")
            else:
                date_obj = datetime.strptime(s_date, "%Y-%m-%d %H:%M:%S")
                location = s_loc
                date_str = s_date

            if not description:
                logging.info(f"   🧠 AI analyzing: {path.name} | Loc: {location if location else 'Domov'}")
                description = self.get_ai_description(path, location)
                logging.info(f"      ✨ Result: {description}")
                self.vdb.update_payload(point.id, {"description": description, "location": location, "date": date_str})

            day_key = date_obj.strftime("%y%m%d")
            if day_key not in days:
                days[day_key] = {"year": date_obj.strftime("%Y"), "location": location, "descriptions": [], "files": []}
            days[day_key]["descriptions"].append(description)
            days[day_key]["files"].append(path)

        for day, info in sorted(days.items()):
            folder_desc = self.get_folder_summary(info["descriptions"], info["location"], day)
            dest = self.target_dir / info["year"] / f"{day} - {folder_desc}"
            dest.mkdir(parents=True, exist_ok=True)
            for f in info["files"]: shutil.copy2(f, dest / f.name)
            logging.info(f"   Done: {day} - {folder_desc}")
