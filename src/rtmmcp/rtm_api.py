from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
import json
from pathlib import Path
import threading
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from .config import Settings

API_ENDPOINT = "https://api.rememberthemilk.com/services/rest/"
AUTH_ENDPOINT = "https://www.rememberthemilk.com/services/auth/"


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _coerce_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def sign_params(shared_secret: str, params: dict[str, Any]) -> str:
    parts: list[str] = [shared_secret]
    for key in sorted(params):
        if params[key] is None:
            continue
        parts.append(key)
        parts.append(_coerce_scalar(params[key]))
    return md5("".join(parts).encode("utf-8")).hexdigest()


def build_auth_url(shared_secret: str, params: dict[str, Any]) -> str:
    signed = {**params, "api_sig": sign_params(shared_secret, params)}
    return f"{AUTH_ENDPOINT}?{urlencode(signed)}"


@dataclass(slots=True)
class AuthState:
    frob: str | None = None
    perms: str | None = None
    auth_token: str | None = None
    user: dict[str, Any] | None = None

    @classmethod
    def load(cls, path: Path) -> "AuthState":
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            frob=payload.get("frob"),
            perms=payload.get("perms"),
            auth_token=payload.get("auth_token"),
            user=payload.get("user"),
        )

    def save(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "frob": self.frob,
                    "perms": self.perms,
                    "auth_token": self.auth_token,
                    "user": self.user,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


class RateLimiter:
    def __init__(self, min_interval_seconds: float = 1.05) -> None:
        self.min_interval_seconds = min_interval_seconds
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait_for = self.min_interval_seconds - (now - self._last_call)
            if wait_for > 0:
                time.sleep(wait_for)
            self._last_call = time.monotonic()


class RTMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.rate_limiter = RateLimiter()

    @property
    def auth_state(self) -> AuthState:
        return AuthState.load(self.settings.auth_state_file)

    def _token(self) -> str | None:
        return self.auth_state.auth_token or self.settings.auth_token

    def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "api_key": self.settings.api_key,
            "format": "json",
            "nojsoncallback": "1",
            "v": "2",
            **{key: value for key, value in params.items() if value is not None},
        }
        payload["api_sig"] = sign_params(self.settings.shared_secret, payload)
        self.rate_limiter.wait()
        url = f"{API_ENDPOINT}?{urlencode({k: _coerce_scalar(v) for k, v in payload.items()})}"
        with urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
        stat = data.get("rsp", {}).get("stat")
        if stat != "ok":
            err = data.get("rsp", {}).get("err", {})
            code = err.get("code", "unknown")
            msg = err.get("msg", "Unknown RTM error")
            raise RuntimeError(f"RTM API error {code}: {msg}")
        return data["rsp"]

    def call_method(
        self,
        method: str,
        *,
        params: dict[str, Any] | None = None,
        require_auth: bool = False,
    ) -> dict[str, Any]:
        params = dict(params or {})
        params["method"] = method
        if require_auth:
            token = self._token()
            if not token:
                raise RuntimeError("No RTM auth token found. Run rtm_auth_begin and rtm_auth_complete first.")
            params["auth_token"] = token
        return self._request(params)

    def start_auth(self, perms: str = "delete") -> dict[str, Any]:
        rsp = self.call_method("rtm.auth.getFrob")
        frob = rsp["frob"]
        state = self.auth_state
        state.frob = frob
        state.perms = perms
        state.save(self.settings.auth_state_file)
        auth_url = build_auth_url(
            self.settings.shared_secret,
            {"api_key": self.settings.api_key, "perms": perms, "frob": frob},
        )
        return {"frob": frob, "perms": perms, "auth_url": auth_url}

    def finish_auth(self, frob: str | None = None) -> dict[str, Any]:
        state = self.auth_state
        active_frob = frob or state.frob
        if not active_frob:
            raise RuntimeError("No frob found. Run rtm_auth_begin first or pass a frob explicitly.")
        rsp = self.call_method("rtm.auth.getToken", params={"frob": active_frob})
        auth = rsp["auth"]
        state.frob = active_frob
        state.auth_token = auth["token"]
        state.user = auth.get("user")
        state.save(self.settings.auth_state_file)
        return {
            "token": auth["token"],
            "perms": auth.get("perms"),
            "user": auth.get("user"),
        }

    def auth_status(self) -> dict[str, Any]:
        state = self.auth_state
        token = self._token()
        if not token:
            return {
                "authenticated": False,
                "has_saved_frob": bool(state.frob),
                "state_file": str(self.settings.auth_state_file),
            }
        login_rsp = self.call_method("rtm.test.login", require_auth=True)
        return {
            "authenticated": True,
            "state_file": str(self.settings.auth_state_file),
            "user": login_rsp.get("user"),
            "stored_user": state.user,
        }

    def get_timeline(self) -> str:
        rsp = self.call_method("rtm.timelines.create", require_auth=True)
        return rsp["timeline"]

    def timeline_method(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(params or {})
        payload["timeline"] = self.get_timeline()
        rsp = self.call_method(method, params=payload, require_auth=True)
        return {"timeline": payload["timeline"], "response": rsp}

    def get_lists(self) -> list[dict[str, Any]]:
        rsp = self.call_method("rtm.lists.getList", require_auth=True)
        return ensure_list(rsp.get("lists", {}).get("list"))

    def get_tasks(self, *, list_id: str | None = None, filter_text: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if list_id:
            params["list_id"] = list_id
        if filter_text:
            params["filter"] = filter_text
        rsp = self.call_method("rtm.tasks.getList", params=params, require_auth=True)
        lists = ensure_list(rsp.get("tasks", {}).get("list"))
        flattened: list[dict[str, Any]] = []
        for task_list in lists:
            series_items = ensure_list(task_list.get("taskseries"))
            for series in series_items:
                tasks = ensure_list(series.get("task"))
                flattened.append(
                    {
                        "list_id": task_list.get("id"),
                        "list_name": task_list.get("$t") or task_list.get("name"),
                        "taskseries_id": series.get("id"),
                        "name": series.get("name"),
                        "created": series.get("created"),
                        "modified": series.get("modified"),
                        "tags": ensure_list(series.get("tags", {}).get("tag") if isinstance(series.get("tags"), dict) else series.get("tags")),
                        "participants": ensure_list(
                            series.get("participants", {}).get("participant")
                            if isinstance(series.get("participants"), dict)
                            else series.get("participants")
                        ),
                        "notes": ensure_list(series.get("notes", {}).get("note") if isinstance(series.get("notes"), dict) else series.get("notes")),
                        "tasks": tasks,
                    }
                )
        return flattened

    def add_task(
        self,
        *,
        name: str,
        list_id: str | None = None,
        parse: bool = True,
    ) -> dict[str, Any]:
        timeline = self.get_timeline()
        params: dict[str, Any] = {"timeline": timeline, "name": name, "parse": parse}
        if list_id:
            params["list_id"] = list_id
        rsp = self.call_method("rtm.tasks.add", params=params, require_auth=True)
        return {
            "timeline": timeline,
            "list": rsp.get("list"),
            "taskseries": rsp.get("taskseries"),
            "transaction": rsp.get("transaction"),
        }

    def complete_task(
        self,
        *,
        list_id: str,
        taskseries_id: str,
        task_id: str,
    ) -> dict[str, Any]:
        timeline = self.get_timeline()
        rsp = self.call_method(
            "rtm.tasks.complete",
            params={
                "timeline": timeline,
                "list_id": list_id,
                "taskseries_id": taskseries_id,
                "task_id": task_id,
            },
            require_auth=True,
        )
        return {
            "timeline": timeline,
            "list": rsp.get("list"),
            "transaction": rsp.get("transaction"),
        }

    def create_list(self, *, name: str, filter_text: str | None = None) -> dict[str, Any]:
        timeline = self.get_timeline()
        params: dict[str, Any] = {"timeline": timeline, "name": name}
        if filter_text:
            params["filter"] = filter_text
        rsp = self.call_method("rtm.lists.add", params=params, require_auth=True)
        return {
            "timeline": timeline,
            "list": rsp.get("list"),
            "transaction": rsp.get("transaction"),
        }

    def update_list(self, method: str, *, list_id: str, name: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"list_id": list_id}
        if name is not None:
            params["name"] = name
        return self.timeline_method(method, params)

    def task_method(
        self,
        method: str,
        *,
        list_id: str,
        taskseries_id: str,
        task_id: str,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = {
            "list_id": list_id,
            "taskseries_id": taskseries_id,
            "task_id": task_id,
            **(extra_params or {}),
        }
        return self.timeline_method(method, params)

    def note_method(
        self,
        method: str,
        *,
        note_id: str | None = None,
        list_id: str,
        taskseries_id: str,
        task_id: str,
        title: str | None = None,
        note_text: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "list_id": list_id,
            "taskseries_id": taskseries_id,
            "task_id": task_id,
        }
        if note_id is not None:
            params["note_id"] = note_id
        if title is not None:
            params["note_title"] = title
        if note_text is not None:
            params["note_text"] = note_text
        return self.timeline_method(method, params)

    def contact_method(self, method: str, *, timeline: bool = False, **params: Any) -> dict[str, Any]:
        if timeline:
            return self.timeline_method(method, dict(params))
        return self.call_method(method, params=params, require_auth=True)

    def group_method(self, method: str, **params: Any) -> dict[str, Any]:
        return self.timeline_method(method, dict(params))
