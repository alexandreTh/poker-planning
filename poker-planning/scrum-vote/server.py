from __future__ import annotations

import hashlib
import json
from collections import Counter
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

HOST = "127.0.0.1"
PORT = 8000
PUBLIC_DIR = Path(__file__).parent / "public"
ALLOWED_VOTES = ["0", "1", "2", "3", "5", "8", "13", "21", "?"]

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


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def do_GET(self) -> None:
        if self.path == "/api/state":
            self._send_json(200, build_public_state())
            return
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/register":
            return self._handle_register()
        if self.path == "/api/vote":
            return self._handle_vote()
        if self.path == "/api/reveal":
            state["revealed"] = True
            self._send_json(200, {"ok": True, "state": build_public_state()})
            return
        if self.path == "/api/reset":
            state["revealed"] = False
            state["participants"].clear()
            state["votes_by_participant"].clear()
            self._send_json(200, {"ok": True, "state": build_public_state()})
            return
        self._send_json(404, {"error": "Not found"})

    def _handle_register(self) -> None:
        payload = self._read_json_body()
        first_name = payload.get("firstName")

        if not isinstance(first_name, str) or len(sanitize_name(first_name)) < 2:
            self._send_json(400, {"error": "Le prenom est requis (2 caracteres min)."})
            return

        safe_name = sanitize_name(first_name)
        key = participant_key(safe_name)
        state["participants"][key] = safe_name
        # If a new participant joins without voting, keep votes hidden.
        if key not in state["votes_by_participant"]:
            state["revealed"] = False
        self._send_json(200, {"ok": True, "state": build_public_state()})

    def _handle_vote(self) -> None:
        payload = self._read_json_body()
        first_name = payload.get("firstName")
        vote = payload.get("vote")

        if not isinstance(first_name, str) or len(sanitize_name(first_name)) < 2:
            self._send_json(400, {"error": "Le prenom est requis (2 caracteres min)."})
            return

        if vote not in ALLOWED_VOTES:
            self._send_json(400, {"error": "Vote invalide."})
            return

        safe_name = sanitize_name(first_name)
        key = participant_key(safe_name)
        state["participants"][key] = safe_name
        state["votes_by_participant"][key] = vote
        if all_participants_voted():
            state["revealed"] = True
        self._send_json(200, {"ok": True, "state": build_public_state()})


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Scrum vote app running on http://{HOST}:{PORT}")
    server.serve_forever()

import os

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))