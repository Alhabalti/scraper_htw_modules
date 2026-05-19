import json
import re
from pathlib import Path

p = Path(r"d:/Projekte/Python-script/htw_modules.json")
if not p.exists():
    print("File not found:", p)
    raise SystemExit(1)

data = json.loads(p.read_text(encoding='utf-8'))

# blacklist keywords indicating non-module entries
blacklist = re.compile(r'\b(Campus|Wilhelminenhof|Leistungspunkte|Bachelor(?: of)?|Master(?: of)?|Semester|Sommer|Wintersemester|Fachhochschulreife|Abschluss|Kolloquium|Bachelorarbeit|Masterarbeit|Deutsch,|Deutsch$|Credits|Leistungspunkte|www\.|http|Campus|Campus\b|Adresse|Telefon|E-Mail)\b', re.I)

cleaned = []
for entry in data:
    mods = entry.get('module', [])
    newmods = []
    for m in mods:
        if not isinstance(m, str):
            continue
        s = m.strip()
        # remove bullets or long descriptive paragraphs
        if '•' in s or '|' in s:
            continue
        if len(s) > 160:
            continue
        if blacklist.search(s):
            # allow some module-like phrases that contain numbers e.g., "Statik 1" but blacklist may match 'Bachelor' etc
            # skip entries that clearly look like qualifications or descriptions
            continue
        # remove entries that are just short words like 'Sommersemester' or 'Deutsch' or single words that are generic
        if re.fullmatch(r'[A-Za-zäöüÄÖÜß\- ]{1,20}', s) and s.lower() in ('deutsch', 'englisch', 'sommersemester', 'wintersemester', '4 semester', '3 semester', '7 semester', '6 semester', 'bachelor of science', 'master of science'):
            continue
        # if looks like a phrase describing program requirements
        if re.search(r'(erst[ea]r akademische|Leistungspunkte|Bachelorabschluss|Hochschuldiplom|Niveaustufe|Auswahlverfahren|Campus|Wilhelminenhof)', s, re.I):
            continue
        # otherwise keep
        newmods.append(s)
    entry['module'] = newmods
    cleaned.append(entry)

# backup
bak = p.with_suffix('.json.bak')
if not bak.exists():
    bak.write_text(p.read_text(encoding='utf-8'), encoding='utf-8')

p.write_text(json.dumps(cleaned, ensure_ascii=False, indent=4), encoding='utf-8')
print('Cleaned file written to', p)
