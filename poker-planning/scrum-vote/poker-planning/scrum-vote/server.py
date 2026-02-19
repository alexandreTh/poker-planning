from __future__ import annotations

import hashlib
import os
from collections import Counter
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
PUBLIC_DIR = Path(__file__).parent / "public"
ALLOWED_VOTES = ["0", "1", "2", "3", "5", "8", "13", "21", "?"]

app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path="")

state: dict[str, Any] = {
    "revealed": False,
    "participants": {},
    "votes_by_participant": {},
}


def sanitize_name(value: str) -> str:
    return value.strip()[:30]


def participant_key(name: str) -> str:
    normalized = sanitize_name(name).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def all_participants_voted() -> bool:
    participants = state["participants"]
    votes_by_participant = state["votes_by_participant"]
    return bool(participants) and all(key in votes_by_participant for key in participants)


def build_public_state() -> dict[str, Any]:
    participants = state["participants"]
    votes_by_participant = state["votes_by_participant"]
    votes = list(votes_by_participant.values())
    participants_status = [
        {
            "firstName": participants[key],
            "hasVoted": key in votes_by_participant,
        }
        for key in sorted(participants, key=lambda item: participants[item].lower())
    ]
    total_participants = len(participants_status)
    votes_submitted = len(votes)

    if not state["revealed"]:
        return {
            "revealed": False,
            "totalParticipants": total_participants,
            "votesSubmitted": votes_submitted,
            "participantsStatus": participants_status,
        }

    counts = Counter(votes)
    distribution = {vote: counts.get(vote, 0) for vote in ALLOWED_VOTES if counts.get(vote, 0) > 0}
    numeric_votes = [int(vote) for vote in votes if vote.isdigit()]
    average = round(sum(numeric_votes) / len(numeric_votes), 2) if numeric_votes else None
    return {
        "revealed": True,
        "totalParticipants": total_participants,
        "votesSubmitted": votes_submitted,
        "participantsStatus": participants_status,
        "distribution": distribution,
        "average": average,
    }


@app.get("/api/state")
def get_state() -> Any:
    return jsonify(build_public_state())


@app.post("/api/register")
def register() -> Any:
    payload = request.get_json(silent=True) or {}
    first_name = payload.get("firstName")

    if not isinstance(first_name, str) or len(sanitize_name(first_name)) < 2:
        return jsonify({"error": "Le prenom est requis (2 caracteres min)."}), 400

    safe_name = sanitize_name(first_name)
    key = participant_key(safe_name)
    state["participants"][key] = safe_name
    if key not in state["votes_by_participant"]:
        state["revealed"] = False
    return jsonify({"ok": True, "state": build_public_state()})


@app.post("/api/vote")
def vote() -> Any:
    payload = request.get_json(silent=True) or {}
    first_name = payload.get("firstName")
    vote_value = payload.get("vote")

    if not isinstance(first_name, str) or len(sanitize_name(first_name)) < 2:
        return jsonify({"error": "Le prenom est requis (2 caracteres min)."}), 400

    if vote_value not in ALLOWED_VOTES:
        return jsonify({"error": "Vote invalide."}), 400

    safe_name = sanitize_name(first_name)
    key = participant_key(safe_name)
    state["participants"][key] = safe_name
    state["votes_by_participant"][key] = vote_value
    if all_participants_voted():
        state["revealed"] = True
    return jsonify({"ok": True, "state": build_public_state()})


@app.post("/api/reveal")
def reveal() -> Any:
    state["revealed"] = True
    return jsonify({"ok": True, "state": build_public_state()})


@app.post("/api/reset")
def reset() -> Any:
    state["revealed"] = False
    state["participants"].clear()
    state["votes_by_participant"].clear()
    return jsonify({"ok": True, "state": build_public_state()})


@app.get("/")
def index() -> Any:
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str) -> Any:
    return send_from_directory(PUBLIC_DIR, path)


if __name__ == "__main__":
    print(f"Scrum vote app running on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT)
