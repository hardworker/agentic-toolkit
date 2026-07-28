#!/bin/sh
# install.sh — wire cf-access into this machine: symlink the three scripts into a bin
# dir, seed the config files, and (macOS) run cf-access-proxy under launchd.
#
#   ./install.sh [install] [--bin-dir DIR] [--no-daemon]
#   ./install.sh status
#   ./install.sh uninstall [--bin-dir DIR]
#
# Symlinks, not copies: edits in the skill directory go live with no update step.
# Idempotent — safe to re-run after editing any of the scripts.
set -eu

SKILL_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR="${CF_ACCESS_BIN_DIR:-$HOME/.claude/bin}"
CONFIG_DIR="${CF_ACCESS_CONFIG_DIR:-$HOME/.config/cloudflare-access}"
LABEL=local.cf-access-proxy
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/cf-access-proxy.log"
DYNAMIC_PORT="${CF_ACCESS_PROXY_DYNAMIC_PORT:-8780}"
SCRIPTS="cf-access cf-access-proxy cf-access-preload.cjs"

cmd=install
daemon=yes
while [ $# -gt 0 ]; do
  case "$1" in
    install | status | uninstall) cmd=$1 ;;
    --bin-dir)
      BIN_DIR=$2
      shift
      ;;
    --no-daemon) daemon=no ;;
    -h | --help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      echo "install.sh: unknown argument: $1" >&2
      exit 2
      ;;
  esac
  shift
done

say() { printf '%s\n' "$*"; }

link_scripts() {
  mkdir -p "$BIN_DIR"
  for s in $SCRIPTS; do
    ln -sfn "$SKILL_DIR/$s" "$BIN_DIR/$s"
    say "linked  $BIN_DIR/$s -> $SKILL_DIR/$s"
  done
  chmod +x "$SKILL_DIR/cf-access" "$SKILL_DIR/cf-access-proxy"
}

seed_configs() {
  mkdir -p "$CONFIG_DIR"
  for f in apps hosts; do
    if [ -f "$CONFIG_DIR/$f" ]; then
      say "kept    $CONFIG_DIR/$f"
    else
      cp "$SKILL_DIR/$f.example" "$CONFIG_DIR/$f"
      say "seeded  $CONFIG_DIR/$f (edit it: the examples are placeholders)"
    fi
  done
}

write_plist() {
  node_bin=$(command -v node || true)
  [ -n "$node_bin" ] || {
    echo "install.sh: node not found in PATH — cf-access-proxy needs it" >&2
    exit 1
  }

  mkdir -p "$(dirname "$PLIST")" "$(dirname "$LOG")"
  # launchd starts with a bare PATH; the proxy shells out to cf-access, which needs
  # both cloudflared and node.
  cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>$node_bin</string>
    <string>$BIN_DIR/cf-access-proxy</string>
  </array>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>$(dirname "$node_bin"):/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key>
    <string>$HOME</string>
    <key>CF_ACCESS_BIN</key>
    <string>$BIN_DIR/cf-access</string>
  </dict>

  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>$LOG</string>
  <key>StandardErrorPath</key>
  <string>$LOG</string>
</dict>
</plist>
EOF
  say "wrote   $PLIST"
}

load_daemon() {
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  say "loaded  $LABEL (log: $LOG)"
}

proxy_alive() {
  # 400 "missing x-cf-access-upstream" is the dynamic port's healthy answer to a bare GET.
  code=$(curl -s -o /dev/null -m 2 -w '%{http_code}' "http://127.0.0.1:$DYNAMIC_PORT/" || echo 000)
  [ "$code" = 400 ]
}

case "$cmd" in
  install)
    link_scripts
    seed_configs
    command -v cloudflared >/dev/null 2>&1 ||
      say "WARNING cloudflared not installed — run: brew install cloudflared"

    if [ "$daemon" = yes ] && [ "$(uname -s)" = Darwin ]; then
      write_plist
      load_daemon
      i=0
      while [ $i -lt 10 ]; do
        proxy_alive && break
        i=$((i + 1))
        sleep 0.3
      done
      proxy_alive && say "proxy   listening on 127.0.0.1:$DYNAMIC_PORT" ||
        say "WARNING proxy not answering on 127.0.0.1:$DYNAMIC_PORT — see $LOG"
    elif [ "$daemon" = yes ]; then
      say "note    launchd is macOS-only; supervise it yourself: $BIN_DIR/cf-access-proxy"
    fi

    say ""
    say "next    cf-access login          # one browser tap warms every configured app"
    ;;

  status)
    say "bin     $BIN_DIR"
    for s in $SCRIPTS; do
      if [ -L "$BIN_DIR/$s" ]; then
        say "  $s -> $(readlink "$BIN_DIR/$s")"
      elif [ -f "$BIN_DIR/$s" ]; then
        say "  $s (plain file, not a link to this skill)"
      else
        say "  $s MISSING"
      fi
    done

    say "config  $CONFIG_DIR"
    for f in apps hosts; do
      if [ -f "$CONFIG_DIR/$f" ]; then
        n=$(grep -cvE '^\s*(#|$)' "$CONFIG_DIR/$f" || true)
        say "  $f ($n entries)"
      else
        say "  $f MISSING"
      fi
    done

    command -v cloudflared >/dev/null 2>&1 && say "cloudflared $(cloudflared --version 2>&1 | head -1)" ||
      say "cloudflared MISSING"

    if [ "$(uname -s)" = Darwin ]; then
      if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
        pid=$(launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | awk '/^\tpid = /{print $3}')
        say "daemon  loaded${pid:+ (pid $pid)}"
      else
        say "daemon  not loaded"
      fi
    fi
    proxy_alive && say "proxy   answering on 127.0.0.1:$DYNAMIC_PORT" ||
      say "proxy   NOT answering on 127.0.0.1:$DYNAMIC_PORT"

    say "tokens"
    if [ -f "$CONFIG_DIR/apps" ]; then
      "$BIN_DIR/cf-access" list 2>&1 | sed 's/^/  /' || true
    else
      say "  no apps file"
    fi
    ;;

  uninstall)
    if [ "$(uname -s)" = Darwin ]; then
      launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
      rm -f "$PLIST"
      say "removed $LABEL and $PLIST"
    fi
    for s in $SCRIPTS; do
      # Only ever unlink our own symlink; a hand-placed copy is the user's file.
      if [ -L "$BIN_DIR/$s" ] && [ "$(readlink "$BIN_DIR/$s")" = "$SKILL_DIR/$s" ]; then
        rm -f "$BIN_DIR/$s"
        say "removed $BIN_DIR/$s"
      fi
    done
    say "kept    $CONFIG_DIR and ~/.cloudflared (tokens)"
    ;;
esac
