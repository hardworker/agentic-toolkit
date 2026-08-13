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

# An account that owns a browser profile resolves to that browser and profile directory.
# Skipped when no Chromium browser on this machine has a signed-in profile.
state="$HOME/Library/Application Support/Google/Chrome/Local State"
if [ -f "$state" ]; then
  # One pass for both halves of the fixture: an account and its directory read separately
  # could disagree, and the expectation below is only meaningful if they match.
  pair=$(node -e '
    const fs = require("fs");
    const cache = JSON.parse(fs.readFileSync(process.argv[1], "utf8")).profile?.info_cache || {};
    for (const [d, v] of Object.entries(cache)) {
      const who = v.user_name || v.gaia_name;
      if (who) { process.stdout.write(`${who}|${d}`); break }
    }
  ' "$state")
  account=${pair%%|*}
  dir=${pair#*|}
  check "account resolves to its profile" \
    "open -na \"Google Chrome\" --args --profile-directory=\"$dir\"" \
    "$(CF_ACCESS_BROWSER="$account" "$CF" browser)"

  # The app search list is overridable, so an account can be pinned to another browser.
  check "app search list is overridable" \
    "open -na \"Brave Browser\" --args --profile-directory=\"$dir\"" \
    "$(CF_ACCESS_BROWSER_APPS="Brave Browser:Google/Chrome" CF_ACCESS_BROWSER="$account" "$CF" browser)"
else
  echo "skip  account resolution (no signed-in browser profiles here)"
fi

# The login path must report the URL and hand it to the opener. A stub cloudflared stands
# in for the real one so this never starts an SSO round-trip.
stub=$(mktemp -d)
cat >"$stub/cloudflared" <<'STUB'
#!/bin/sh
case "$*" in
  *"access login"*)
    echo "Please open the following URL and log in with your Cloudflare account:"
    echo ""
    echo "https://example.cloudflareaccess.com/cdn-cgi/access/cli?token=stub"
    sleep 1
    ;;
esac
exit 0
STUB
chmod +x "$stub/cloudflared"

# The opener's own output is silenced (browsers must not spam the terminal), so the
# recorded argument is what proves it ran.
opened=$(mktemp)
login_out=$(PATH="$stub:$PATH" CF_ACCESS_BROWSER="/bin/sh -c 'printf %s \"\$1\" >\"$opened\"' opener" \
  "$CF" login https://stub.example 2>&1 || true)

case "$login_out" in
  *"cdn-cgi/access/cli?token=stub"*) echo "ok    login reports the url" ;;
  *)
    echo "FAIL  login reports the url"
    echo "        got: $login_out"
    fails=$((fails + 1))
    ;;
esac

check "login hands the url to the opener" \
  "https://example.cloudflareaccess.com/cdn-cgi/access/cli?token=stub" "$(cat "$opened")"

rm -rf "$stub"
rm -f "$opened"
rm -f "$empty"
[ "$fails" -eq 0 ] || exit 1
echo "all good"
