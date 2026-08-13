'use strict';
// cf-access-hosts — the domain-suffix allowlist, owned in one place.
//
// This matcher is the security boundary: it decides which hosts the preload diverts and
// which upstreams the proxy will forward to. A second copy would let the two drift into
// either half of the failure — traffic the proxy refuses, or an open forwarder.
//
// Re-read at most every TTL ms rather than watched: a preloaded process must still be
// able to exit, and fs.watchFile would hold its event loop open forever.

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOSTS_FILE =
  process.env.CF_ACCESS_HOSTS_FILE || path.join(os.homedir(), '.config/cloudflare-access/hosts');
const PORT = Number(process.env.CF_ACCESS_PROXY_DYNAMIC_PORT || 8780);
const TTL = 2000;

let cached = [];
let readAt = 0;

function suffixes() {
  if (readAt && Date.now() - readAt < TTL) return cached;
  readAt = Date.now();
  try {
    cached = fs
      .readFileSync(HOSTS_FILE, 'utf8')
      .split('\n')
      .map((l) => l.replace(/#.*/, '').trim().replace(/^\*?\./, ''))
      .filter(Boolean);
  } catch {
    cached = []; // no hosts file: forward nothing rather than guess at a domain
  }
  return cached;
}

const matches = (host) => {
  const bare = (host || '').split(':')[0].toLowerCase();
  return suffixes().some((s) => bare === s || bare.endsWith(`.${s}`));
};

module.exports = { HOSTS_FILE, PORT, suffixes, matches };
