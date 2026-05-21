#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-}"
TARGET="${2:-}"
OUT_ROOT="${3:-$HOME/Desktop}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
STATE_DB="$CODEX_HOME_DIR/state_5.sqlite"
SESSION_INDEX="$CODEX_HOME_DIR/session_index.jsonl"
ARCHIVED_DIR="$CODEX_HOME_DIR/archived_sessions"
SESSIONS_DIR="$CODEX_HOME_DIR/sessions"

usage() {
  cat <<'EOF'
Usage:
  export_codex_thread_for_windows.sh thread <thread_id> [output_root]
  export_codex_thread_for_windows.sh cwd <workspace_path> [output_root]

Example:
  export_codex_thread_for_windows.sh thread 019e1fef-d0a9-7281-9d30-3f6e056e5c68
  export_codex_thread_for_windows.sh cwd "/Users/medusa/Desktop/snap Extract"
EOF
}

if [[ -z "$MODE" || -z "$TARGET" ]]; then
  usage
  exit 1
fi

if [[ ! -f "$STATE_DB" ]]; then
  echo "Missing state db: $STATE_DB" >&2
  exit 1
fi

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "sqlite3 is required" >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "zip is required" >&2
  exit 1
fi

export_single_thread() {
  local thread_id="$1"
  local pkg_dir="$2"
  local thread_row

  thread_row="$(sqlite3 -tabs "$STATE_DB" "select id, title, cwd, rollout_path, created_at_ms, updated_at_ms, git_sha, git_branch, git_origin_url from threads where id = '$thread_id' limit 1;")"

  if [[ -z "$thread_row" ]]; then
    echo "Thread not found: $thread_id" >&2
    exit 1
  fi

  local id title cwd rollout_path created_at_ms updated_at_ms git_sha git_branch git_origin_url
  IFS=$'\t' read -r id title cwd rollout_path created_at_ms updated_at_ms git_sha git_branch git_origin_url <<<"$thread_row"

  mkdir -p "$pkg_dir"
  mkdir -p "$pkg_dir/raw"

  sqlite3 -json "$STATE_DB" "select * from threads where id = '$thread_id';" > "$pkg_dir/thread-row.json"
  sqlite3 -json "$STATE_DB" "select * from thread_goals where thread_id = '$thread_id';" > "$pkg_dir/thread-goals.json"
  sqlite3 -json "$STATE_DB" "select * from thread_dynamic_tools where thread_id = '$thread_id';" > "$pkg_dir/thread-dynamic-tools.json"
  sqlite3 -json "$STATE_DB" "select * from thread_spawn_edges where parent_thread_id = '$thread_id' or child_thread_id = '$thread_id';" > "$pkg_dir/thread-spawn-edges.json"

  if [[ -f "$rollout_path" ]]; then
    cp "$rollout_path" "$pkg_dir/raw/"
  fi

  if [[ -f "$SESSION_INDEX" ]]; then
    rg -n "\"id\":\"$thread_id\"" "$SESSION_INDEX" > "$pkg_dir/session-index-match.jsonl" || true
  fi

  if [[ -d "$SESSIONS_DIR" ]]; then
    local thread_dir_hint
    thread_dir_hint="$(dirname "$rollout_path")"
    if [[ -d "$thread_dir_hint" ]]; then
      find "$thread_dir_hint" -maxdepth 1 -type f -name "*$thread_id*" -exec cp {} "$pkg_dir/raw/" \;
    fi
  fi

  if [[ -d "$ARCHIVED_DIR" ]]; then
    find "$ARCHIVED_DIR" -type f -name "*$thread_id*" -exec cp {} "$pkg_dir/raw/" \; 2>/dev/null || true
  fi

  cat > "$pkg_dir/README-WINDOWS-RESTORE.md" <<EOF
# Codex thread export

This package contains a single Codex thread exported from macOS for inspection or partial restore on Windows.

## Exported thread

- Thread ID: $id
- Title: $title
- Original cwd: $cwd
- Original rollout path: $rollout_path
- Created at ms: $created_at_ms
- Updated at ms: $updated_at_ms
- Git branch: ${git_branch:-}
- Git sha: ${git_sha:-}
- Git origin: ${git_origin_url:-}

## Files

- \`thread-row.json\`: row from \`state_5.sqlite -> threads\`
- \`thread-goals.json\`: thread goals rows
- \`thread-dynamic-tools.json\`: dynamic tool rows
- \`thread-spawn-edges.json\`: parent/child thread links
- \`session-index-match.jsonl\`: matching line from \`session_index.jsonl\`
- \`raw/\`: original rollout jsonl and any matching raw files

## Recommended Windows restore flow

1. Install and open Codex once on Windows, then fully quit it.
2. Back up \`%USERPROFILE%\\.codex\`.
3. Copy only the exported thread payload into the Windows Codex data directory.
4. Do not overwrite Windows-local \`config.toml\`, \`.codex-global-state.json\`, or \`auth.json\`.
5. If Codex does not auto-index the thread, keep this package as a readable archive and use the raw rollout jsonl directly.

## Important caveats

- macOS absolute paths in the original thread will not map cleanly to Windows.
- Plugin runtime paths, login state, and trusted project paths are platform-local.
- This package is intended to preserve thread content and metadata with minimal risk to the Windows install.
EOF
}

export_workspace_threads() {
  local workspace_cwd="$1"
  local stamp pkg_dir zip_path manifest_ids_path manifest_meta_path
  stamp="$(date +%Y%m%d-%H%M%S)"
  pkg_dir="$OUT_ROOT/codex-workspace-export-$stamp"
  zip_path="$OUT_ROOT/codex-workspace-export-$stamp.zip"
  manifest_ids_path="$pkg_dir/workspace-thread-ids.txt"
  manifest_meta_path="$pkg_dir/workspace-threads.json"

  mkdir -p "$pkg_dir/threads"

  sqlite3 "$STATE_DB" "select id from threads where cwd = '$workspace_cwd' order by updated_at_ms desc;" > "$manifest_ids_path"
  sqlite3 -json "$STATE_DB" "select id, title, cwd, rollout_path, created_at_ms, updated_at_ms from threads where cwd = '$workspace_cwd' order by updated_at_ms desc;" > "$manifest_meta_path"

  if [[ ! -s "$manifest_ids_path" ]]; then
    echo "No threads found for cwd: $workspace_cwd" >&2
    exit 1
  fi

  while IFS= read -r thread_id; do
    [[ -z "$thread_id" ]] && continue
    export_single_thread "$thread_id" "$pkg_dir/threads/$thread_id"
  done < "$manifest_ids_path"

  cat > "$pkg_dir/README-WINDOWS-RESTORE.md" <<EOF
# Codex workspace export

This package contains all Codex threads whose recorded cwd matches:

\`$workspace_cwd\`

## Contents

- \`workspace-thread-ids.txt\`: exported thread ids
- \`workspace-threads.json\`: workspace thread metadata
- \`threads/<thread_id>/\`: per-thread export payload

## Recommended use on Windows

1. Treat this package as a workspace-scoped archive.
2. Open the per-thread raw rollout jsonl files if UI import is incomplete.
3. If you want to try direct restore, do it on a backed-up Windows \`.codex\` directory.
4. Keep Windows-local \`config.toml\`, \`.codex-global-state.json\`, and \`auth.json\`.

## Caveats

- The workspace path is macOS-specific and will not map directly to Windows.
- Codex may not automatically rebind these threads to a Windows workspace path.
- This export is intended to preserve all thread content for this workspace with low migration risk.
EOF

  (cd "$OUT_ROOT" && zip -qry "$(basename "$zip_path")" "$(basename "$pkg_dir")")

  echo "WORKSPACE_CWD=$workspace_cwd"
  echo "PACKAGE_DIR=$pkg_dir"
  echo "ZIP_PATH=$zip_path"
}

case "$MODE" in
  thread)
    stamp="$(date +%Y%m%d-%H%M%S)"
    pkg_dir="$OUT_ROOT/codex-thread-export-$TARGET-$stamp"
    zip_path="$OUT_ROOT/codex-thread-export-$TARGET-$stamp.zip"
    export_single_thread "$TARGET" "$pkg_dir"
    (cd "$OUT_ROOT" && zip -qry "$(basename "$zip_path")" "$(basename "$pkg_dir")")
    echo "THREAD_ID=$TARGET"
    echo "PACKAGE_DIR=$pkg_dir"
    echo "ZIP_PATH=$zip_path"
    ;;
  cwd)
    export_workspace_threads "$TARGET"
    ;;
  *)
    usage
    exit 1
    ;;
esac
