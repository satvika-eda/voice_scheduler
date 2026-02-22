import re
from datetime import datetime, timedelta, timezone

WORD_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12
}

def extract_user_details(session: dict, transcript: str) -> None:
    t = transcript.strip()
    tl = t.lower()
    details = session["userDetails"]

    # ---- name: handle "My name is Amy" OR single-word name "Forrest."
    if not details.get("name"):
        m = re.search(r"(?:i'm|i am|my name is|call me)\s+([A-Za-z]+)", t, re.I)
        if m:
            details["name"] = m.group(1).capitalize()
        else:
            # If the user utterance is just one word (letters only), treat it as a name
            m2 = re.match(r"^[A-Za-z]{2,30}[.!?]?$", t)
            if m2:
                details["name"] = re.sub(r"[.!?]$", "", t).capitalize()

    # ---- date
    if not details.get("date"):
        if "tomorrow" in tl:
            tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
            details["date"] = tomorrow.isoformat()
        elif "next week" in tl:
            next_week = datetime.now(timezone.utc).date() + timedelta(days=7)
            details["date"] = next_week.isoformat()
        else:
            m = re.search(r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})", t)
            if m:
                date_str = m.group(1)
                if "/" in date_str:
                    mm, dd, yy = date_str.split("/")
                    if len(yy) == 2:
                        yy = f"20{yy}"
                    details["date"] = f"{yy}-{int(mm):02d}-{int(dd):02d}"
                else:
                    details["date"] = date_str

    # ---- time: digits ("10 pm", "10:30") OR words ("ten pm")
    if not details.get("time"):
        # digits
        m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", tl, re.I)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2) or "0")
            mer = (m.group(3) or "").lower()
            if mer == "pm" and hour != 12:
                hour += 12
            if mer == "am" and hour == 12:
                hour = 0
            details["time"] = f"{hour:02d}:{minute:02d}"
        else:
            # word time like "ten pm"
            m2 = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b\s*(am|pm)\b", tl)
            if m2:
                hour = WORD_NUM[m2.group(1)]
                mer = m2.group(2)
                if mer == "pm" and hour != 12:
                    hour += 12
                if mer == "am" and hour == 12:
                    hour = 0
                details["time"] = f"{hour:02d}:00"

    # ---- duration
    if not details.get("duration"):
        m = re.search(r"\b(\d{1,3})\s*(minute|min|minutes|hour|hr|hours)\b", tl)
        if m:
            value = int(m.group(1))
            unit = m.group(2)
            details["duration"] = str(value * 60 if unit.startswith(("hour", "hr")) else value)

    # ---- title
    if not details.get("title"):
        m = re.search(r"(?:titled|title is|called)\s+([^.,!?]+)", t, re.I)
        if m:
            details["title"] = m.group(1).strip()