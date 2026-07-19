"""Task 6 — wire it together. Task 7 — and then make sure only two of these run at once."""
from __future__ import annotations
from importlib.resources import path
import json
from logging import exception
import logging
from pathlib import Path
import psycopg
from trip_ingest.loader import load_trips
from trip_ingest.model import Report
from trip_ingest.reader import parse_row
from trip_ingest.settings import database_url

def ingest_drop(conn: psycopg.Connection, path: Path, rejects_dir: Path) -> Report:
    """Read one drop, load the good rows, write the bad ones aside, and report what happened.

    A rejected row must not stop the job, and it must not vanish either: write it to
    `rejects_dir/<drop-name>.rejects.jsonl`, one JSON object per line, each carrying the original row
    and why it was rejected. Somebody will have to fix these in the morning.
    """
    trips = []
    read = 0
    rejected = 0

    with path.open("r") as f: # פותח את הקובץ לקריאה
        for line in f: # קורא כל שורה בקובץ
            read += 1 # כל שורה שקוראים, מגדילים את המונה
            try: # מנסה לקרוא את השורה, אם יש שגיאה הוא עובר לאקספט
                raw = json.loads(line) # הופך את השורה למילון
                trip = parse_row(raw) # הופך את המילון לאובייקט טריפ
                trips.append(trip) # מוסיף את האובייקט לרשימת הטריפים
            except Exception as e: # exception אומרת כל שגיאה אפשרית ( יש הרבה שגיאות בתוכה )
                rejected += 1
                reject_path = rejects_dir / f"{path.name}.rejects.jsonl" # יוצר את הנתיב לקובץ הדחיות
                with reject_path.open("a") as reject_file: # פותח את הקובץ במצב של הוספה
                    reject_file.write(json.dumps({"row": line, "error": str(e)}) + "\n") # כותב את השורה הדחויה ואת השגיאה לקובץ הדחיות
                                                # row זה רק משתנה שלוקח את השורה המקורית   # error זה משתנה שמכיל בתוכו את המשתנה e שמכיל את השגיאה
    loaded = load_trips(conn, trips) # טוען את כל הטריפים שהצלחנו לקרוא למסד הנתונים 
    return Report(read=read,
                  rejected=rejected,
                  loaded=loaded
                  ) # מייצר דוח עם כל המידע על מה שקראנו, מה נדחה ומה נטען למסד הנתונים

def run_job(drop_dir: Path, rejects_dir: Path = Path("rejects")) -> Report:
    """Ingest every `*.jsonl` in `drop_dir` and return the totals across all of them.

    Task 6. Log a structured summary — one line, at INFO, naming the counts — so that a person on
    call at 3am can tell what happened without opening the database.

    Task 7. Two of these may run at once. A third must wait.
    """
    with psycopg.connect(database_url()) as conn: # פותח חיבור למסד הנתונים
        total_drops = 0 # מונה של כל הקבצים שקראנו
        total_read = 0 # מונה של כל השורות שקראנו
        total_rejected = 0 # מונה של כל השורות שנדחו
        total_loaded = 0 # מונה של כל השורות שהצליחו להיטען למסד הנתונים
        for drop_path in drop_dir.glob("*.jsonl"): # מחפש את כל הקבצים עם סיומת jsonl בתיקייה
            total_drops += 1
            report = ingest_drop(conn, drop_path, rejects_dir) # קורא את הקובץ ומחזיר דוח על מה שקראנו
            total_read += report.read # מוסיף את המונה של השורות שקראנו למונה הכללי
            total_rejected += report.rejected # מוסיף את המונה של השורות שנדחו למונה הכללי
            total_loaded += report.loaded # מוסיף את המונה של השורות שהצליחו להיטען למסד הנתונים למונה הכללי

    logging.info(
        "Ingest complete: drops=%d read=%d loaded=%d rejected=%d",
        total_drops,total_read,total_loaded,total_rejected,
            ) # מדפיס לוג עם כל המידע על מה שקראנו, מה נדחה ומה נטען למסד הנתונים   

    return Report(read=total_read,
                  rejected=total_rejected,
                  loaded=total_loaded
    )