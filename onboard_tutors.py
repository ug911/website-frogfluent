#!/usr/bin/env python3
"""
Scrape tutors from frogfluent.com and onboard each into the Wise instance
(frogfluent-sample namespace).

Steps per tutor:
  1. Scrape: name, country, language, photo URL, bio from frogfluent.com
  2. Wise: invite teacher via sendBulkInvite
  3. Wise: look up teacherId by email from /teachers
  4. Wise: upload photo via presigned URL
  5. Wise: set default payout settings
  6. Wise: create public profile
  7. Wise: create a class template, assign to teacher, add public profile (course page),
           enable student slot booking (consultation), set pricing.

Usage:
  python3 onboard_tutors.py --dry-run            # scrape + print plan only
  python3 onboard_tutors.py --scrape-only        # just dump tutors.json
  python3 onboard_tutors.py                      # actually call Wise APIs

Env:
  WISE_BEARER_TOKEN    Bearer JWT (defaults to the one captured in the HAR)
  WISE_INSTITUTE_ID    Defaults to 6a10430bf464d10720e4f6be (frogfluent-sample)
  EMAIL_DOMAIN         Dummy email domain (default: tutors.frogfluent.test)
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FROG_BASE = "https://frogfluent.com"
WISE_API = "https://api.wiseapp.live"
NAMESPACE = "frogfluent-sample"

INSTITUTE_ID = os.environ.get("WISE_INSTITUTE_ID", "6a10430bf464d10720e4f6be")
BEARER = os.environ.get(
    "WISE_BEARER_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2YTEwNDMwYjVjOTFlOTQ4ZGY5NmQ1Y2UiLCJuYW1lIjoiRnJvZ2ZsdWVudCBBZG1pbiIsInR5cGUiOiJTRVNTSU9OX1RPS0VOIiwic2Vzc2lvbklkIjoiNmExMDQzMGJmNDY0ZDEwNzIwZTRmNmI5IiwiaWF0IjoxNzc5NDUwNjM1LCJleHAiOjE3ODcyMjY2MzV9.N8aG7uIJdYwWFMhb1frGzDGih75kPUKE1QQ6on3ynSs",
)
EMAIL_DOMAIN = os.environ.get("EMAIL_DOMAIN", "tutors.frogfluent.test")

WISE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {BEARER}",
    "content-type": "application/json",
    "origin": f"https://{NAMESPACE}.wise.live",
    "referer": f"https://{NAMESPACE}.wise.live/",
    "user-agent": "Mozilla/5.0 onboard-tutors-script",
    "x-api-key": "web:aff7589260fd9f8ba437674d25225728",
    "x-wise-app-version": "release_1779439224",
    "x-wise-namespace": NAMESPACE,
    "x-wise-platform": "web",
    "x-wise-timezone": "Asia/Calcutta",
}

DEFAULT_PAYOUT = {
    "generatePastSessionInvoice": False,
    "payoutSettings": {
        "type": "AMOUNT_PER_CREDIT",
        "amount": {"value": 1200, "currency": "USD"},
    },
}

DEFAULT_PRICE = {"value": 10000, "currency": "USD"}  # $10 trial


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Tutor:
    slug: str
    name: str
    country: str = ""
    language: str = ""
    photo_url: str = ""
    short_tagline: str = ""
    bio: str = ""
    rating: float = 0.0

    @property
    def email(self) -> str:
        local = re.sub(r"[^a-z0-9]+", ".", self.name.lower()).strip(".")
        return f"{local}@{EMAIL_DOMAIN}"


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def scrape_tutors() -> list[Tutor]:
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0 scraper"})

    # 1. Hit /tutors to get a session + csrf token
    r = sess.get(f"{FROG_BASE}/tutors", timeout=30)
    r.raise_for_status()
    csrf = re.search(r'csrf-token"\s+content="([^"]+)"', r.text).group(1)

    # 2. POST to /get-tutors-data — returns rendered HTML cards
    r = sess.post(
        f"{FROG_BASE}/get-tutors-data",
        headers={
            "X-CSRF-TOKEN": csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html, */*",
            "Content-Type": "application/json",
        },
        data="{}",
        timeout=30,
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select(".tp-course-item")
    tutors: dict[str, Tutor] = {}
    for card in cards:
        link = card.select_one("a[href*='/tutor-details/']")
        if not link:
            continue
        slug = link["href"].rstrip("?/").split("/tutor-details/")[-1].split("?")[0]
        if slug in tutors:
            continue
        name = card.select_one(".tp-course-title a")
        img = card.select_one("img.tutor-photo")
        meta_spans = card.select(".tp-course-meta span")
        country = lang = ""
        if len(meta_spans) >= 1:
            country = meta_spans[0].get_text(strip=True)
        if len(meta_spans) >= 2:
            lang = meta_spans[1].get_text(strip=True)
        tagline = card.select_one(".tp-course-content p")
        tutors[slug] = Tutor(
            slug=slug,
            name=name.get_text(strip=True) if name else slug,
            country=country,
            language=lang,
            photo_url=urljoin(FROG_BASE, img["src"]) if img and img.get("src") else "",
            short_tagline=tagline.get_text(" ", strip=True).strip(".") if tagline else "",
        )

    # 3. Visit each detail page for full bio
    for slug, t in tutors.items():
        try:
            d = sess.get(f"{FROG_BASE}/tutor-details/{slug}", timeout=30)
            d.raise_for_status()
            dsoup = BeautifulSoup(d.text, "html.parser")
            # Bio: first <p> inside the instructor content block
            holder = dsoup.select_one(".tp-skills-2-instructor-content") or dsoup
            paragraphs = holder.find_all("p")
            SKIP_PATTERNS = ("sign up", "sign in", "log in", "glad to have you")
            chunks = []
            for p in paragraphs:
                text = p.get_text(" ", strip=True)
                text = re.sub(r"\s+", " ", text)
                low = text.lower()
                if len(text) < 40:
                    continue
                if any(s in low for s in SKIP_PATTERNS):
                    continue
                chunks.append(text)
            t.bio = " ".join(chunks).strip()
            # Derive a clean tagline: first sentence of bio, or fallback
            if t.bio:
                first = re.split(r"(?<=[.!?])\s+", t.bio, maxsplit=1)[0]
                t.short_tagline = first[:160]
            if not t.short_tagline.strip():
                t.short_tagline = f"Teaches {t.language}".strip()
        except Exception as e:
            print(f"  ! detail fetch failed for {slug}: {e}", file=sys.stderr)

    return list(tutors.values())


# ---------------------------------------------------------------------------
# Wise API helpers
# ---------------------------------------------------------------------------


class Wise:
    def __init__(self, dry: bool = False):
        self.dry = dry
        self.s = requests.Session()
        self.s.headers.update(WISE_HEADERS)

    def _do(self, method: str, path: str, tolerate_400=False, **kwargs) -> dict:
        url = path if path.startswith("http") else f"{WISE_API}{path}"
        if self.dry:
            body = kwargs.get("json") or kwargs.get("data")
            print(f"    DRY {method} {url}  body={json.dumps(body)[:160] if body else ''}")
            return {}
        r = self.s.request(method, url, timeout=60, **kwargs)
        if r.status_code >= 400:
            print(f"    {'WARN' if tolerate_400 else 'ERR'} {method} {url} -> {r.status_code}: {r.text[:200]}", file=sys.stderr)
            if not tolerate_400:
                r.raise_for_status()
            return {"_error": r.text, "_status": r.status_code}
        if not r.text:
            return {}
        try:
            return r.json()
        except ValueError:
            return {"_text": r.text}

    # 1. Invite
    def invite_teacher(self, name: str, email: str) -> dict:
        return self._do(
            "POST",
            f"/institutes/{INSTITUTE_ID}/sendBulkInvite",
            json={
                "type": "TEACHER",
                "jsonData": True,
                "users": [{"name": name, "isAdmin": False, "email": email}],
            },
            tolerate_400=True,  # already-invited returns 400
        )

    _teachers_cache: Optional[list] = None

    def _list_teachers(self, refresh=False):
        if self._teachers_cache is None or refresh:
            res = self._do("GET", f"/institutes/{INSTITUTE_ID}/teachers?showOwner=true")
            data = res.get("data") if isinstance(res, dict) else None
            if isinstance(data, dict):
                self._teachers_cache = data.get("teachers") or []
            elif isinstance(data, list):
                self._teachers_cache = data
            else:
                self._teachers_cache = []
        return self._teachers_cache

    # 2. Find teacher by email -> (participant_id, user_id)
    def find_teacher_ids(self, email: str, refresh=False) -> tuple[Optional[str], Optional[str]]:
        if self.dry:
            return "<teacherId>", "<userId>"
        for t in self._list_teachers(refresh=refresh):
            user = t.get("userId") if isinstance(t.get("userId"), dict) else None
            user_email = (user or {}).get("email") or t.get("email")
            if (user_email or "").lower() == email.lower():
                participant_id = t.get("_id")
                user_id = (user or {}).get("_id") or (t.get("userId") if isinstance(t.get("userId"), str) else None)
                return participant_id, user_id
        return None, None

    # 3. Upload photo -> returns (fileLocation, uploadToken)
    def upload_photo(self, url: str) -> tuple[Optional[str], Optional[str]]:
        if not url:
            return None, None
        if self.dry:
            print(f"    DRY upload photo from {url}")
            return "<photoUrl>", "<uploadToken>"
        try:
            img = requests.get(url, timeout=60)
            img.raise_for_status()
        except Exception as e:
            print(f"    ! photo download failed: {e}", file=sys.stderr)
            return None, None
        filename = Path(url).name or f"photo-{int(time.time())}.jpg"
        mime = mimetypes.guess_type(filename)[0] or "image/jpeg"
        size = len(img.content)
        pres = self._do(
            "GET",
            f"/user/uploadURL?filename={filename}&type={mime}&size={size}",
        )
        if isinstance(pres.get("data"), dict):
            pres = pres["data"]
        upload_url = pres.get("uploadURL")
        file_location = pres.get("fileLocation")
        upload_token = pres.get("uploadToken")
        if not upload_url:
            print(f"    ! no upload URL returned: {pres}", file=sys.stderr)
            return None, None
        # The presigned URL has an x-amz-acl signed header — we must send it on the PUT
        put_headers = {"Content-Type": mime, "x-amz-acl": "public-read"}
        put = requests.put(upload_url, data=img.content, headers=put_headers, timeout=120)
        if put.status_code >= 400:
            print(f"    ! S3 upload failed: {put.status_code}: {put.text[:200]}", file=sys.stderr)
            return None, None
        return file_location, upload_token

    # 3b. Attach uploaded photo to the participant (sets profilePicture)
    def set_participant_photo(self, user_id: str, upload_token: str, tags: list[str] | None = None):
        body: dict = {"uploadToken": upload_token}
        if tags:
            body["tags"] = tags
        return self._do(
            "PUT",
            f"/institutes/{INSTITUTE_ID}/participants/{user_id}",
            json=body,
        )

    # 4. Payout
    def set_payout(self, teacher_id: str):
        return self._do(
            "POST",
            f"/institutes/{INSTITUTE_ID}/teachers/{teacher_id}/payoutSettings",
            json=DEFAULT_PAYOUT,
        )

    # 5. Public profile
    def set_public_profile(self, teacher_id: str, tutor: Tutor):
        return self._do(
            "POST",
            f"/institutes/{INSTITUTE_ID}/teachers/{teacher_id}/publicProfile",
            json={
                "tagline": (tutor.short_tagline or f"Teaches {tutor.language}")[:200],
                "description": (tutor.bio or tutor.short_tagline)[:4900],
                "displayTags": [tag for tag in [tutor.language, tutor.country] if tag],
                "reviews": [],
            },
        )

    # 6. Course / class
    def create_class_template(self, name: str) -> Optional[str]:
        res = self._do(
            "POST",
            f"/institutes/{INSTITUTE_ID}/classTemplates",
            json={"name": name},
        )
        if self.dry:
            return "<classId>"
        data = res.get("data") if isinstance(res, dict) else None
        if isinstance(data, dict):
            # Could be the class object itself, or wrapped further
            for key in ("_id", "classId", "id"):
                if key in data:
                    return data[key]
            # Some APIs wrap as { classTemplate: {...} }
            for sub in data.values():
                if isinstance(sub, dict) and "_id" in sub:
                    return sub["_id"]
        return None

    def assign_class(self, class_id: str, teacher_id: str):
        return self._do(
            "POST",
            f"/institutes/{INSTITUTE_ID}/assignClassToTeacher",
            json={"classId": class_id, "userId": teacher_id},
        )

    def set_class_public_profile(self, class_id: str, tutor: Tutor, photo_url: Optional[str]):
        return self._do(
            "POST",
            f"/institutes/{INSTITUTE_ID}/classes/{class_id}/publicProfile",
            json={
                "title": f"1:1 {tutor.language} with {tutor.name}",
                "subTitle": tutor.short_tagline or f"Personalized {tutor.language} lessons",
                "description": f"<p>{tutor.bio}</p>" if tutor.bio else f"<p>Learn {tutor.language} with {tutor.name}.</p>",
                "highlights": {
                    "title": "What's Included",
                    "points": [
                        "1:1 live sessions over video",
                        "Personalized lesson plan",
                        "Homework and progress tracking",
                    ],
                },
                "reviews": [],
                "classCovers": [{"link": photo_url, "type": "image"}] if photo_url else [],
            },
        )

    def enable_slot_booking(self, class_id: str):
        return self._do(
            "PUT",
            "/teacher/editClass",
            json={
                "classId": class_id,
                "learnerManagedFlow": True,
                "settings": {
                    "studentSlotBooking": {
                        "enabled": True,
                        "slotDurations": [30, 60],
                        "cancellationPolicyNote": "Cancel at least 12 hours before the session.",
                    }
                },
            },
        )

    # DEMO class — Wise "consultation booking" / demoRoom
    def create_demo_room(self, tutor_name: str, user_id: str, language: str = "") -> Optional[str]:
        slug_base = re.sub(r"[^a-z0-9]+", "-", tutor_name.lower()).strip("-")
        slug = f"trial-with-{slug_base}"
        desc = f"Book a free trial with {tutor_name}" + (f" ({language})" if language else "")
        body = {
            "instituteId": INSTITUTE_ID,
            "name": f"Trial with {tutor_name}",
            "description": desc,
            "settings": {"studentSlotBooking": {"slotDurations": [30]}},
            "slug": slug,
            "teachers": [{"_id": user_id}],
            "classType": "DEMO",
        }
        res = self._do("POST", "/teacher/addClass?json_data=true", json=body)
        if self.dry:
            return "<demoClassId>"
        data = res.get("data") if isinstance(res, dict) else None
        if isinstance(data, dict):
            return data.get("_id")
        return None

    def enable_demo_slot_booking(self, class_id: str):
        return self._do(
            "PUT",
            "/teacher/editClass",
            json={
                "classId": class_id,
                "learnerManagedFlow": True,
                "settings": {
                    "studentSlotBooking": {
                        "enabled": True,
                        "slotDurations": [30],
                        "cancellationPolicyNote": "Cancel at least 12 hours before the session.",
                    }
                },
            },
        )

    # Store publish: read current store, add classIds to the ALL section, write back
    def get_store(self) -> dict:
        res = self._do("GET", f"/institutes/{INSTITUTE_ID}/store")
        data = res.get("data") if isinstance(res, dict) else {}
        if isinstance(data, dict):
            return data.get("institutePublicProfile") or data
        return {}

    def publish_classes_to_store(self, class_ids: list[str]):
        store = self.get_store() if not self.dry else {}
        sections = store.get("sections") or [{"title": "All Courses", "sectionType": "ALL", "classIds": []}]
        for sec in sections:
            if sec.get("sectionType") == "ALL":
                existing: list[str] = []
                for c in sec.get("classIds") or []:
                    cid = c.get("_id") if isinstance(c, dict) else c
                    if cid:
                        existing.append(cid)
                merged = existing + [c for c in class_ids if c and c not in existing]
                sec["classIds"] = merged
                break
        body = {
            "instituteId": INSTITUTE_ID,
            "isPublic": True,
            "namespace": NAMESPACE,
            "sections": sections,
        }
        for k in ("backgroundColor", "ctaText", "instituteCovers", "socialProfile", "subdomain", "textColor", "title"):
            if k in store:
                body[k] = store[k]
        if store.get("_id"):
            body["_id"] = store["_id"]
        return self._do("POST", f"/institutes/{INSTITUTE_ID}/store", json=body)

    def set_class_fees(self, class_id: str):
        return self._do(
            "POST",
            f"/institutes/classes/{class_id}/fees",
            json={
                "paymentOptions": [
                    {
                        "type": "PACKAGE",
                        "title": "Single Session",
                        "installments": [],
                        "metadata": {"amount": DEFAULT_PRICE, "sessionCredits": 1},
                    }
                ],
                "currency": DEFAULT_PRICE["currency"],
            },
        )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_photos_only(dry: bool, limit: Optional[int]):
    results_path = Path("onboard_results.json")
    if not results_path.exists():
        print("onboard_results.json not found — run the full flow first", file=sys.stderr)
        sys.exit(1)
    prev = json.loads(results_path.read_text())
    work = prev[:limit] if limit else prev
    wise = Wise(dry=dry)
    for i, item in enumerate(work, 1):
        t = item.get("tutor", {})
        user_id = item.get("user_id")
        photo_url = t.get("photo_url")
        name = t.get("name", "?")
        print(f"\n[{i}/{len(prev)}] {name}")
        if not user_id:
            print("  ! no user_id in results, skipping")
            continue
        if not photo_url:
            print("  ! no photo_url, skipping")
            continue
        print("  → uploading photo...")
        file_loc, token = wise.upload_photo(photo_url)
        item["photo"] = file_loc
        if not token:
            print("  ! no upload token returned")
            continue
        tags = [tag for tag in [t.get("language"), t.get("country")] if tag]
        print("  → attaching to profile...")
        wise.set_participant_photo(user_id, token, tags=tags)
    results_path.write_text(json.dumps(prev, indent=2))
    print(f"\nDone. Updated {results_path}")


def onboard(tutors: list[Tutor], dry: bool):
    wise = Wise(dry=dry)
    results = []
    for i, t in enumerate(tutors, 1):
        print(f"\n[{i}/{len(tutors)}] {t.name} <{t.email}>")
        out: dict = {"tutor": asdict(t)}
        try:
            print("  → inviting...")
            wise.invite_teacher(t.name, t.email)

            print("  → resolving teacherId...")
            teacher_id, user_id = wise.find_teacher_ids(t.email, refresh=(i == 1))
            if not teacher_id:
                # Maybe just got invited — refresh the cache once
                teacher_id, user_id = wise.find_teacher_ids(t.email, refresh=True)
            if not teacher_id:
                print("  ! could not resolve teacherId, skipping rest")
                out["error"] = "teacher_id not found"
                results.append(out)
                continue
            out["teacher_id"] = teacher_id
            out["user_id"] = user_id
            print(f"    teacherId = {teacher_id}  userId = {user_id}")

            print("  → uploading photo...")
            photo, upload_token = wise.upload_photo(t.photo_url)
            out["photo"] = photo

            # The teachers/{id} routes expect the inner userId._id, not the participant _id
            tid = user_id or teacher_id

            if upload_token and tid:
                print("  → attaching photo to profile...")
                tags = [tag for tag in [t.language, t.country] if tag]
                wise.set_participant_photo(tid, upload_token, tags=tags)

            print("  → payout settings...")
            wise.set_payout(tid)

            print("  → public profile...")
            wise.set_public_profile(tid, t)

            print("  → course template...")
            class_id = wise.create_class_template(f"1:1 {t.language} with {t.name}")
            out["class_id"] = class_id
            if class_id:
                print(f"    classId = {class_id}")
                wise.assign_class(class_id, user_id or teacher_id)
                wise.set_class_public_profile(class_id, t, photo)
                wise.enable_slot_booking(class_id)
                wise.set_class_fees(class_id)
                out["course_link"] = f"https://{NAMESPACE}.wise.live/courses/{class_id}"
                out["booking_link"] = out["course_link"] + "?book=true"

        except Exception as e:
            out["error"] = str(e)
            print(f"  ! failed: {e}", file=sys.stderr)
        results.append(out)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the API calls without making them")
    ap.add_argument("--scrape-only", action="store_true", help="just write tutors.json and exit")
    ap.add_argument("--input", help="skip scraping, load tutors from this JSON file")
    ap.add_argument("--limit", type=int, help="only process first N tutors")
    ap.add_argument("--photos-only", action="store_true", help="re-upload + attach photos using onboard_results.json")
    args = ap.parse_args()

    if args.photos_only:
        return run_photos_only(args.dry_run, args.limit)

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
        tutors = [Tutor(**t) for t in data]
    else:
        print("Scraping tutors from frogfluent.com…")
        tutors = scrape_tutors()
        Path("tutors.json").write_text(json.dumps([asdict(t) for t in tutors], indent=2))
        print(f"Saved {len(tutors)} tutors → tutors.json")

    if args.limit:
        tutors = tutors[: args.limit]

    if args.scrape_only:
        return

    if not args.dry_run:
        print(f"\nAbout to onboard {len(tutors)} tutors into Wise (institute {INSTITUTE_ID}).")
        print("Re-run with --dry-run to preview, or Ctrl-C to abort.")
        try:
            input("Press Enter to continue… ")
        except EOFError:
            pass

    results = onboard(tutors, dry=args.dry_run)
    out_path = "onboard_results.json"
    Path(out_path).write_text(json.dumps(results, indent=2))
    print(f"\nDone. Results → {out_path}")


if __name__ == "__main__":
    main()
