from pathlib import Path
import unittest

from rtmmcp.rtm_api import AuthState, build_auth_url, ensure_list, sign_params


class RtmApiTests(unittest.TestCase):
    def test_sign_params_ignores_none_and_sorts_keys(self) -> None:
        signature = sign_params(
            "secret",
            {"b": "2", "a": "1", "skip": None},
        )
        self.assertEqual(signature, "aaf433dbd21b3b11d1e0b7477e52300d")

    def test_build_auth_url_contains_signature(self) -> None:
        url = build_auth_url(
            "secret",
            {"api_key": "abc", "perms": "read", "frob": "xyz"},
        )
        self.assertIn("api_key=abc", url)
        self.assertIn("perms=read", url)
        self.assertIn("frob=xyz", url)
        self.assertIn("api_sig=", url)

    def test_ensure_list_normalizes_scalars(self) -> None:
        self.assertEqual(ensure_list(None), [])
        self.assertEqual(ensure_list("x"), ["x"])
        self.assertEqual(ensure_list(["x", "y"]), ["x", "y"])

    def test_auth_state_round_trip(self) -> None:
        workspace_tmp = Path("test_auth_state.json")
        state = AuthState(frob="f123", perms="delete", auth_token="t123", user={"id": "1"})
        state.save(workspace_tmp)
        loaded = AuthState.load(workspace_tmp)
        self.assertEqual(loaded.frob, "f123")
        self.assertEqual(loaded.perms, "delete")
        self.assertEqual(loaded.auth_token, "t123")
        self.assertEqual(loaded.user, {"id": "1"})


if __name__ == "__main__":
    unittest.main()
