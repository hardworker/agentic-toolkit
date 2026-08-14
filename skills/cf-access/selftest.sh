#!/bin/sh
# selftest.sh — the browser-resolution branch, the one piece of logic here that can fail
# silently (a wrong profile still opens *a* browser). Run it after touching cf-access.
set -eu

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CF="$DIR/cf-access"
fails=0

work=$(mktemp -d)
trap 'kill ${px_pid:-} ${up_pid:-} 2>/dev/null; rm -rf "$work"' EXIT INT TERM

wait_for() {
  i=0
  while [ $i -lt 40 ]; do
    eval "$1" && return 0
    i=$((i + 1))
    sleep 0.1
  done
  return 1
}

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

fail() {
  echo "FAIL  $1"
  echo "        got: ${2:-<empty>}"
  fails=$((fails + 1))
}

matches() {
  # shellcheck disable=SC2254
  case "$3" in $2) echo "ok    $1" ;; *) fail "$1" "$3" ;; esac
}

lacks() {
  # shellcheck disable=SC2254
  case "$3" in $2) fail "$1" "$3" ;; *) echo "ok    $1" ;; esac
}

# A command passes through untouched.
cmd='open -na "Firefox"'
check "command passes through" "$cmd" "$(CF_ACCESS_BROWSER="$cmd" "$CF" browser)"

# Nothing configured means the default browser, and CF_ACCESS_BROWSER_FILE is honoured
# so this test never reads the real config.
empty="$work/empty"; : >"$empty"
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
stub="$work/stub"; mkdir -p "$stub"
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
opened="$work/opened"; : >"$opened"
login_out=$(PATH="$stub:$PATH" CF_ACCESS_BROWSER="/bin/sh -c 'printf %s \"\$1\" >\"$opened\"' opener" \
  "$CF" login https://stub.example 2>&1 || true)

matches "login reports the url" '*cdn-cgi/access/cli?token=stub*' "$login_out"
check "login hands the url to the opener" \
  "https://example.cloudflareaccess.com/cdn-cgi/access/cli?token=stub" "$(cat "$opened")"

# The trace must reach the page as text, never markup. The session id names no record.
trace='GET "/probe" ← "pid=1 ppid=2 <script>alert(1)</script>"'
CF_ACCESS_TRACE="$trace" CF_ACCESS_SESSION=00000000-0000-0000-0000-000000000000 PATH="$stub:$PATH" \
  CF_ACCESS_BROWSER="/bin/sh -c 'printf %s \"\$1\" >\"$opened\"; cp \"\${1#file://}\" \"$work/page.html\" 2>/dev/null' opener" \
  "$CF" login https://stub.example >/dev/null 2>&1 || true

page=$(cat "$work/page.html" 2>/dev/null || true)
matches "a traced login opens the sign-in page" 'file://*sso.html' "$(cat "$opened")"
matches "the sign-in page escapes the trace" '*&lt;script&gt;*' "$page"
lacks "the trace never reaches the page as markup" '*<script>alert*' "$page"
matches "the sign-in page links to the sso url" '*cdn-cgi/access/cli?token=stub*' "$page"
matches "an unnameable session still yields a page" '*session=00000000-*' "$page"

# Asked for: fixed ports once collided with a real service, and the harness tested against it.
read -r UP_PORT PX_PORT <<PORTS
$(node -e '
  const net = require("net");
  const grab = () => new Promise((r) => {
    const s = net.createServer().listen(0, "127.0.0.1", () => {
      const { port } = s.address();
      s.close(() => r(port));
    });
  });
  Promise.all([grab(), grab()]).then((p) => process.stdout.write(p.join(" ")));
')
PORTS
JWT=eyJhbGciOiJub25lIn0.eyJleHAiOjQxMDI0NDQ4MDAsImF1ZCI6WyJ0ZXN0YXVkIl19.sig

cat >"$work/cf-access" <<STUB
#!/bin/sh
case "\$*" in
  *--no-login*) exit 1 ;;
  token*) echo "$JWT" ;;
esac
STUB
chmod +x "$work/cf-access"
echo localhost >"$work/hosts"
: >"$work/routes"

# Redirect first (forcing a mint), then echo headers. It records `x-cf-access-client` only when
# a request bypassed the proxy — the eval case below, so no third server is needed.
node -e '
  const fs = require("fs");
  let seen = 0;
  require("http").createServer((req, res) => {
    const client = req.headers["x-cf-access-client"];
    if (client) fs.writeFileSync(process.argv[2], String(client));
    if (seen++ === 0) {
      res.writeHead(302, { location: "https://team.cloudflareaccess.com/cdn-cgi/access/login/x" });
      return res.end();
    }
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify(req.headers));
  }).listen(Number(process.argv[1]), "127.0.0.1");
' "$UP_PORT" "$work/hdr" &
up_pid=$!

CF_ACCESS_BIN="$work/cf-access" CF_ACCESS_HOSTS_FILE="$work/hosts" \
  CF_ACCESS_PROXY_CONFIG="$work/routes" CF_ACCESS_PROXY_DYNAMIC_PORT="$PX_PORT" \
  node "$DIR/cf-access-proxy" >"$work/log" 2>&1 &
px_pid=$!

wait_for '[ "$(curl -s -o /dev/null -m 1 -w %{http_code} "http://127.0.0.1:$PX_PORT/" || true)" = 400 ]' ||
  echo "note  proxy never answered on $PX_PORT"

cat >"$work/selftest-client.js" <<CLIENT
fetch("http://localhost:$UP_PORT/probe?secret=leakcanary")
  .then((r) => r.text())
  .then((t) => require("fs").writeFileSync("$work/echo", t))
  .finally(() => process.exit(0));
CLIENT
CF_ACCESS_HOSTS_FILE="$work/hosts" CF_ACCESS_PROXY_DYNAMIC_PORT="$PX_PORT" \
  CLAUDE_CODE_SESSION_ID=11111111-2222-3333-4444-555555555555 \
  node --require "$DIR/cf-access-preload.cjs" "$work/selftest-client.js" >/dev/null 2>&1 || true
body=$(cat "$work/echo" 2>/dev/null || true)

# The name must never come from `node -e`'s first argument: a user value, path-shaped or not.
CF_ACCESS_HOSTS_FILE="$work/hosts" CF_ACCESS_PROXY_DYNAMIC_PORT="$UP_PORT" CLAUDE_CODE_SESSION_ID= \
  node --require "$DIR/cf-access-preload.cjs" \
  -e 'fetch("http://localhost:1/x").catch(() => {})' \
  /var/run/secrets/tok_AKIAIOSFODNN7EXAMPLE >/dev/null 2>&1 || true
wait_for '[ -s "$work/hdr" ]' || true

kill "$px_pid" "$up_pid" 2>/dev/null || true
wait "$px_pid" "$up_pid" 2>/dev/null || true

matches "the upstream is reached with an injected token" '*cf-access-token*' "$body"
lacks "identity header is stripped before the upstream" '*x-cf-access-client*' "$body"
matches "sso trace names the request, the client and its session" \
  '*GET "/probe"?…*selftest-client.js*session="11111111-2222-3333-4444-555555555555"*' \
  "$(grep 'sso ' "$work/log" || true)"
lacks "the query string never reaches the log" '*leakcanary*' "$(cat "$work/log")"
matches "an eval argument never becomes the client name" 'pid=* ppid=* node' \
  "$(cat "$work/hdr" 2>/dev/null || true)"
[ "$fails" -eq 0 ] || exit 1
echo "all good"
