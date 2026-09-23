"""Download the BBQ files this study sampled from, and check them against the copy we used.

BBQ is not re-hosted here. It comes from https://github.com/nyu-mll/BBQ (CC-BY-4.0).
The hashes are of the files downloaded on 2026-09-22 from the main branch. If upstream
changes, a hash will not match and bbq_cells.py may sample different items.
"""
import hashlib
import sys
from pathlib import Path

import requests

BASE = "https://raw.githubusercontent.com/nyu-mll/BBQ/main"
FILES = {
    "data/Age.jsonl": "46e805b3fc2d8cbd26eeb8e8430d98cf7b2dc9c83574ff3674e8ce4f0fca2a60",
    "data/Disability_status.jsonl": "375d40d9b71f056150264445ec189b13934998f3f49a1e311aa7578eb3b45e5f",
    "data/Gender_identity.jsonl": "8b5adbb368510a97d5775dc43e1c719e0249fe2da33f13c83e3e29edafec7a00",
    "data/Nationality.jsonl": "a583e74666aec0341ded8aa3983e7cad694eb24de72c254d28b2df3035720090",
    "data/Physical_appearance.jsonl": "e48d7e13508565f4801574e611043470c25c95a0a62af3699cb5ee7cb02608fb",
    "data/Race_ethnicity.jsonl": "4a9f1214cfaa115ce7f0bdb40609122e431f5152c71b8ca64d665e483b946ae6",
    "data/Race_x_SES.jsonl": "af8e2ae3d0e5be9ebcbfe7149e591d47ff649e263307f4548f7fb12f6a6d83e8",
    "data/Race_x_gender.jsonl": "e5dbba782f8c4e25b99dd5470b5136e2db73dbf401cf6d4a5a3ed31b02f95696",
    "data/Religion.jsonl": "cb9555f9f3454a52cd2df85956b59bd7fcca5aa922c8527693b1164d08417616",
    "data/SES.jsonl": "9f92754bb037b0982604b9112705fb81d60a19d9e759c67e4a85e484a070f528",
    "data/Sexual_orientation.jsonl": "2c71036b9e7584fe589c42aef32c1a42bc01b9a5e9b1b8704342630cdb08cefd",
    "analysis_scripts/additional_metadata.csv": "f36708416b0e7adb81b47ad1926f9c39c2beb611702b73b01e06c9b6c9ffbd3d",
}

out = Path("data/bbq")
out.mkdir(parents=True, exist_ok=True)
bad = 0
for src, want in FILES.items():
    dest = out / Path(src).name
    if not dest.exists():
        r = requests.get(f"{BASE}/{src}", timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
    got = hashlib.sha256(dest.read_bytes()).hexdigest()
    ok = got == want
    bad += not ok
    print(f"{'ok ' if ok else 'MISMATCH'}  {dest.name}")
if bad:
    sys.exit(f"{bad} file(s) differ from the copy used in the study")
