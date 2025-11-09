import json
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict

from ..config import DATA_DIR

# ─── SUBJECT MAPPING ───
SUBJECT_MAP = {
    "Polity": "Polity",
    "History": "History", 
    "Geography": "Geography",
    "Economics": "Economics",
    "Environment": "Environment",
    "Science & Technology": "Science & Technology",
    "Current Affairs": "Current Affairs",
    "General Studies": "General Studies"
}

# ------------------- CLEANING UTILS -------------------
def clean_option_label(text: str) -> str:
    """Remove leading A) B. etc from options."""
    return re.sub(r"^[A-Da-d][\).\s]+", "", text.strip())

# ------------------- CLI ARGUMENT PARSING -------------------

parser = argparse.ArgumentParser(description="Merge raw PYQ files into base dataset.")
parser.add_argument(
    "--date", 
    type=str, 
    help="Date tag for output files (default: today's date in YYYYMMDD)", 
    default=datetime.now().strftime("%Y%m%d")
)
parser.add_argument(
    "--exam",
    type=str,
    action="append",
    help="Exam name to filter by (can be used multiple times for multiple exams)",
    default=None
)
args = parser.parse_args()

DATE_TAG = args.date
EXAM_FILTER = set(args.exam) if args.exam else None
print(f"🗓️  Using DATE_TAG = {DATE_TAG}")
if EXAM_FILTER:
    print(f"🔎 Filtering for exams: {', '.join(EXAM_FILTER)}")

# ─── PATHS ───
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BASE_FILE = PROCESSED_DIR / "v0_base.json"

# ------------------- UTILS -------------------

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def question_hash(q: dict) -> str:
    """Create a unique hash based on question text + options."""
    q_text = q.get("question", "").strip()
    options = q.get("options", [])
    combined = f"{q_text}::{'|'.join(options)}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

# ------------------- MERGE STEP -------------------

def merge_raw_jsons() -> list:
    merged = {}
    exam_counter = defaultdict(int)
    raw_files = list(RAW_DIR.glob("*_allpyq_clickversion.json"))
    total_loaded = 0

    print(f"🔍 Found {len(raw_files)} raw files to merge:")
    for file in raw_files:
        print(f"   - {file.name}")
        data = load_json(file)
        total_loaded += len(data)
        for q in data:
            # Rename "solve_hint" to "cot" if it exists
            if "solve_hint" in q:
                q["cot"] = q.pop("solve_hint")

            exam = q.get("exam", "Unknown")
            if EXAM_FILTER and exam not in EXAM_FILTER:
                continue

            key = question_hash(q)
            if key not in merged:
                merged[key] = q
                exam_counter[exam] += 1

    merged_list = list(merged.values())
    excluded = total_loaded - len(merged_list)

    # --- CLEANING STEP ---
    for q in merged_list:
        # Clean options
        if "options" in q and isinstance(q["options"], list):
            q["options"] = [clean_option_label(opt) for opt in q["options"]]
            # Update correct_answer_text to match cleaned option
            label = q.get("correct_answer_label")
            if label:
                idx = ord(label.upper()) - 65
                if 0 <= idx < len(q["options"]):
                    q["correct_answer_text"] = q["options"][idx]
        # Set default CoT if missing
        if not q.get("cot"):
            q["cot"] = "No explanation available"
        # Map subject names
        subj = q.get("subject")
        if subj in SUBJECT_MAP:
            q["subject"] = SUBJECT_MAP[subj]

    write_json(BASE_FILE, merged_list)

    print(f"\n📊 Question count by exam:")
    for exam, count in sorted(exam_counter.items()):
        print(f"   • {exam}: {count} questions")

    print(f"\n✅ Merged total: {len(merged_list)} unique questions")
    print(f"❌ Excluded due to duplicate question+options: {excluded} questions")
    print(f"📁 Output written to: {BASE_FILE.name}")

    return merged_list

# ------------------- MAIN -------------------

if __name__ == "__main__":
    # Merge all raw JSONs into a single, deduplicated base file.
    all_questions = merge_raw_jsons()
    
    # --- Final Summary ---
    print("\n---  النهائية (Final Summary) ---")
    print(f"Total questions in BASE file: {len(all_questions)}")
    print("---------------------------------")