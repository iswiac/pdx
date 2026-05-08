PROMPTS = {
    "cs": {
        "fallback_context": "Základní kontext: Rodina, výlety, sport.",
        "unknown_location": "Neznámá lokalita",
        "default_description": "Momentky",
        "default_description_singular": "Momentka",
        "default_folder": "Různé_aktivity",
        "home_label": "Domov",
        "various_check": "Různé",
        "photo_date_label": "Datum fotky",
        "recognized_persons_label": "Rozpoznané osoby",
        "error_ai_failed": "AI analýza selhala pro",

        "face_identified": (
            "Na fotce byly automaticky rozpoznány tyto osoby: {names}. "
            "Tuto identifikaci považuj za spolehlivou a použij tato jména v popisu."
        ),
        "face_not_identified": (
            "Neumíš rozpoznávat obličeje. Jména dětí používej POUZE když vidíš jednoznačný identifikátor "
            "(dres, vybavení, kontext aktivity). Jinak piš 'chlapec', 'dítě', 'kluci'."
        ),
        "system_prompt": "Jsi objektivní rodinný archivář. Odpovídej POUZE česky.",
        "user_request": (
            "{date_line}"
            "Lokalita: {location}.\n"
            "{names_line}"
            "Napiš stručný popis obsahu fotky (osoby, akce, objekty) v max 6 slovech.\n"
            "- Pokud jsou uvedeny rozpoznané osoby, použij jejich jména.\n"
            "- Bez rozpoznaných osob piš obecně: chlapec, dívka, dítě, kluci.\n"
            "- U sportu uveď druh sportu (rugby, florbal, běh).\n"
            "- Bez lidí buď technický.\n"
            "- NEPIŠ lokalitu, '{home}' ani datum.\n"
            "Odpověz POUZE popisem, nic jiného."
        ),
        "history_examples": "PŘÍKLADY EXISTUJÍCÍCH NÁZVŮ SLOŽEK (inspiruj se stylem): {examples}",
        "folder_summary": (
            "Lokalita: {location}\nFOTKY: {photos}\n"
            "{history_line}"
            "ÚKOL: JEDEN český název složky (2-4 slova).\n"
            "PRAVIDLO 1: Pokud je lokalita '{home}', v názvu ji ABSOLUTNĚ NEUVÁDĚJ "
            "(ani slova jako 'doma', 'u nás'). Soustřeď se jen na aktivitu.\n"
            "PRAVIDLO 2: Pokud je to jiná lokalita (např. Havířov, Itálie), "
            "v názvu ji zachovej v PŘESNÉM tvaru.\n"
            "PRAVIDLO 3: Odpověz POUZE výsledným názvem bez uvozovek a meta-textu."
        ),

        "meta_patterns": [
            r'^(zde (je|jsou) návrh[y]?|návrh[y]?|možné|seznam|složka|složky|název|popis)\s*(názvů|pro)?\s*[:\-–]*\s*',
            r'^(zde je popis obsahu fotografie|popis obsahu fotografie)\s*[:\-–]*\s*',
        ],
        "trailing_prepositions": ['v', 'na', 's', 'z', 'u', 'o'],
    },

    "en": {
        "fallback_context": "Basic context: Family, trips, sports.",
        "unknown_location": "Unknown location",
        "default_description": "Snapshots",
        "default_description_singular": "Snapshot",
        "default_folder": "Various_activities",
        "home_label": "Home",
        "various_check": "Various",
        "photo_date_label": "Photo date",
        "recognized_persons_label": "Recognized persons",
        "error_ai_failed": "AI analysis failed for",

        "face_identified": (
            "The following persons were automatically recognized in the photo: {names}. "
            "Treat this identification as reliable and use these names in the description."
        ),
        "face_not_identified": (
            "You cannot recognize faces. Use children's names ONLY when you see a clear identifier "
            "(jersey, equipment, activity context). Otherwise write 'boy', 'child', 'kids'."
        ),
        "system_prompt": "You are an objective family archivist. Respond ONLY in English.",
        "user_request": (
            "{date_line}"
            "Location: {location}.\n"
            "{names_line}"
            "Write a brief description of the photo content (people, action, objects) in max 6 words.\n"
            "- If recognized persons are listed, use their names.\n"
            "- Without recognized persons, write generically: boy, girl, child, kids.\n"
            "- For sports, mention the sport type (rugby, floorball, running).\n"
            "- Without people, be technical.\n"
            "- Do NOT write the location, '{home}', or date.\n"
            "Respond ONLY with the description, nothing else."
        ),
        "history_examples": "EXAMPLES OF EXISTING FOLDER NAMES (follow this style): {examples}",
        "folder_summary": (
            "Location: {location}\nPHOTOS: {photos}\n"
            "{history_line}"
            "TASK: ONE English folder name (2-4 words).\n"
            "RULE 1: If the location is '{home}', do NOT include it in the name at all "
            "(nor words like 'home', 'at home'). Focus only on the activity.\n"
            "RULE 2: If it is another location (e.g. Vienna, Italy), "
            "keep it in the name in its EXACT form.\n"
            "RULE 3: Respond ONLY with the resulting name, no quotes or meta-text."
        ),

        "meta_patterns": [
            r'^(here (is|are) (a |the )?(suggestion|proposal|name|description|list|folder)s?)\s*(of|for)?\s*[:\-–]*\s*',
            r'^(here is (a |the )?description of the photo content|photo content description)\s*[:\-–]*\s*',
        ],
        "trailing_prepositions": ['in', 'at', 'on', 'of', 'to', 'a'],
    },
}
