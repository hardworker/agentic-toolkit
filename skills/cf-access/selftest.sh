#!/bin/sh
# selftest.sh — the browser-resolution branch, the one piece of logic here that can fail
# silently (a wrong profile still opens *a* browser). Run it after touching cf-access.
set -eu

CF="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/cf-access"
fails=0

check() {
  what=$1
  want=$2
  got=$3
  if [ "$got" = "$want" ]; then
    echo "ok    $what"
  else
    echo "FAIL  $what"
    echo "        want: $want"
    echo "        got:  $got"
    fails=$((fails + 1))
  fi
}

# A command passes through untouched.
cmd='open -na "Firefox"'
check "command passes through" "$cmd" "$(CF_ACCESS_BROWSER="$cmd" "$CF" browser)"

# Nothing configured means the default browser, and CF_ACCESS_BROWSER_FILE is honoured
# so this test never reads the real config.
empty=$(mktemp)
check "unset falls back" "<default browser>" "$(CF_ACCESS_BROWSER= CF_ACCESS_BROWSER_FILE="$empty" "$CF" browser)"

# An unknown account must fall back rather than fail the login.
check "unknown account falls back" "<default browser>" \
  "$(CF_ACCESS_BROWSER=nobody@nowhere.invalid "$CF" browser 2>/dev/null)"

# An account that owns a Chrome profile resolves to that profile's directory. Skipped
# when Chrome has no profiles on this machine.
state="$HOME/Library/Application Support/Google/Chrome/Local State"
if [ -f "$state" ]; then
  account=$(node -e '
    const fs = require("fs");
    const cache = JSON.parse(fs.readFileSync(process.argv[1], "utf8")).profile?.info_cache || {};
    for (const v of Object.values(cache)) {
      const who = v.user_name || v.gaia_name;
      if (who) { process.stdout.write(who); break }
    }
  ' "$state")
  dir=$(node -e '
    const fs = require("fs");
    const want = process.argv[2].toLowerCase();
    const cache = JSON.parse(fs.readFileSync(process.argv[1], "utf8")).profile?.info_cache || {};
    for (const [d, v] of Object.entries(cache)) {
      if ((v.user_name || v.gaia_name || "").toLowerCase() === want) { process.stdout.write(d); break }
    }
  ' "$state" "$account")
  check "account resolves to its profile" \
    "open -na \"Google Chrome\" --args --profile-directory=\"$dir\"" \
    "$(CF_ACCESS_BROWSER="$account" "$CF" browser)"
else
  echo "skip  account resolution (no Chrome profiles here)"
fi

rm -f "$empty"
[ "$fails" -eq 0 ] || exit 1
echo "all good"
