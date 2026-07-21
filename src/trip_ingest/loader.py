"""Task 5 — put the trips in the database."""
from __future__ import annotations
from itertools import batched
from typing import Iterable
import psycopg
from trip_ingest.model import Trip

def load_trips(conn, trips, batch_size=1000):
    inserted_count = 0

    with conn.cursor() as cur:
        for batch in batched(trips, batch_size): # לוקח את כל הטיולים ומחלק אותם למנות בגודל של batch_size
            rows = []
            for trip in batch:
                row = (trip.trip_id,trip.station_id,trip.started_at,trip.distance_m,) #מגדיר טאפל (ליסט שלא משתנה ) עם כל הערכים של טריפ (הפסיק בסוף זה מה שמגדיר את הטאפל )
                rows.append(row) #מכניס את כל הערכים של כל טריפ למערך אחד
            if not rows:
                continue # אם אין יותר רשומות בבאטצ׳ הוא עובר לבאטצ׳ הבא 

            placeholders = ",".join(["(%s, %s, %s, %s)"] * len(rows)) # מייצר מערך לפי כמות השורות שיש לי כאשר כל מערך מוגדר מ4 שדות כמו שהגדרנו בטבלה 
            values = []
            for row in rows:
                values.extend(row)# מכניס את כל הערכים של כל טריפ למערך אחד

            cur.execute(
                f"""
                INSERT INTO trips (trip_id,station_id,started_at,distance_m)
                VALUES {placeholders}ON CONFLICT (trip_id) DO NOTHING """,values,) # מכניס את כל הערכים של כל טריפ לטבלה לפי המערך שהגדרנו למעלה 
            inserted_count += cur.rowcount # כל ריצה הוא מוסיף את כמות הרשומות שנכנסו לדאטה בייס לקאונטר למעלה 
    return inserted_count