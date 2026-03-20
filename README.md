# Remember The Milk MCP

This repository contains a Python MCP server for [Remember The Milk](https://www.rememberthemilk.com/).

## What it does

The server exposes tools to:

- start the RTM auth flow
- finish the auth flow and persist the auth token locally
- inspect auth status
- manage lists
- list tasks
- add, complete, uncomplete, postpone, move, rename, reprioritize, and delete tasks
- set task due dates, start dates, estimates, recurrences, URLs, locations, tags, and parents
- add, edit, and delete task notes
- manage contacts and groups
- inspect tags, locations, settings, timezones, API methods, and transactions
- use RTM time parsing and time conversion helpers
- call any RTM API method directly through a raw escape hatch

## Setup

1. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   py -m pip install -e .
   ```

3. The local `.env` file is already present in this workspace and is ignored by Git.

4. Run the MCP server:

   ```powershell
   py -m rtmmcp.server
   ```

## Authentication flow

1. Call `rtm_auth_begin` with the desired permissions, usually `delete`.
2. Open the returned `auth_url` in a browser and approve the app.
3. Call `rtm_auth_complete` to exchange the saved `frob` for a permanent auth token.
4. Use `rtm_auth_status` to confirm the token is available.

The auth token is stored in the file configured by `RTM_AUTH_STATE_FILE`, defaulting to `.rtm_auth.json`.

## Suggested MCP config

Example `mcpServers` entry:

```json
{
  "mcpServers": {
    "remember-the-milk": {
      "command": "py",
      "args": ["-m", "rtmmcp.server"],
      "cwd": "C:\\temp\\rtmmcp"
    }
  }
}
```

## Notes

- RTM enforces a rate limit of roughly 1 request per second per IP plus API key.
- The server signs every request with the shared secret and supports RTM's JSON response format.
- Most commonly used RTM APIs now have dedicated MCP tools.
- `rtm_raw_call` remains available for any methods not wrapped yet.
