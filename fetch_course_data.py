#!/usr/bin/env python3
"""
Fetch each tutor's public course profile from Wise and write assets/tutors-data.json
that the static website loads at runtime.

Run after onboard_tutors.py (which produces onboard_results.json).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from onboard_tutors import WISE_API, WISE_HEADERS, INSTITUTE_ID, NAMESPACE  # noqa: E402

OUT = Path("assets/tutors-data.json")
RESULTS = Path("onboard_results.json")


def fetch_course(class_id: str) -> dict:
    r = requests.get(
        f"{WISE_API}/institutes/{INSTITUTE_ID}/classes/{class_id}/publicProfile"
        "?showClassroomFee=true&showTeacherPublicProfile=true",
        headers=WISE_HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data") or {}


def main():
    results = json.loads(RESULTS.read_text())
    out = []
    for item in results:
        cid = item.get("class_id")
        t = item["tutor"]
        if not cid:
            print(f"! skip {t['name']} — no class_id")
            continue
        print(f"Fetching {t['name']}...")
        d = fetch_course(cid)
        classroom = d.get("classroom") or {}
        public = d.get("classroomPublicProfile") or {}
        fee_doc = d.get("classroomFee") or {}
        teachers = d.get("teachers") or []
        teacher = teachers[0] if teachers else {}
        amount = {}
        for opt in fee_doc.get("paymentOptions") or []:
            amount = (opt.get("metadata") or {}).get("amount") or {}
            if amount:
                break

        out.append({
            "name": t["name"],
            "country": t["country"],
            "language": t["language"],
            "photo": teacher.get("profilePicture") or t["photo_url"],
            "bio": public.get("description") or t.get("bio", ""),
            "tagline": public.get("subTitle") or t.get("short_tagline", ""),
            "title": public.get("title") or classroom.get("name") or f"1:1 with {t['name']}",
            "highlights": (public.get("highlights") or {}).get("points") or [
                "1:1 live sessions over video",
                "Personalized lesson plan",
                "Homework and progress tracking",
            ],
            "price": {
                "value": amount.get("value", 0) / 100 if amount.get("value") else 0,
                "currency": amount.get("currency", "USD"),
            },
            "class_id": cid,
            "course_link": d.get("publicLink") or f"https://{NAMESPACE}.wise.live/courses/{cid}",
            "consultation_booking_link": item.get("consultation_booking_link"),
            "demo_class_id": item.get("demo_class_id"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {len(out)} tutors → {OUT}")


if __name__ == "__main__":
    main()
