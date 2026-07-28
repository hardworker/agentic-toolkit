'use strict';
// cf-access-preload — makes any Node process reach Cloudflare Access apps without
// knowing it. Preloaded via NODE_OPTIONS=--require, it sends requests for allowed
// hostnames to cf-access-proxy's dynamic port, naming the real upstream in a header.
// The proxy injects and renews the token.
//
// Matching is by domain suffix (~/.config/cloudflare-access/hosts), never a list of
// apps — so a gated app that appears next month is already covered: no route entry,
// no config, no code change, in any client.

const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const https = require('https');

const HOSTS_FILE =
  process.env.CF_ACCESS_HOSTS_FILE || path.join(os.homedir(), '.config/cloudflare-access/hosts');
const PORT = Number(process.env.CF_ACCESS_PROXY_DYNAMIC_PORT || 8780);

let suffixes;
try {
  suffixes = fs
    .readFileSync(HOSTS_FILE, 'utf8')
    .split('\n')
    .map((l) => l.replace(/#.*/, '').trim().replace(/^\*?\./, ''))
    .filter(Boolean);
} catch {
  suffixes = []; // no hosts file: patch nothing rather than guess at a domain
}

const matches = (host) => {
  const bare = (host || '').split(':')[0].toLowerCase();
  return suffixes.some((s) => bare === s || bare.endsWith(`.${s}`));
};

// Never patch the proxy itself: it is the thing that reaches the real hosts, so
// rewriting its outbound requests would point it at its own port forever.
const isProxy = /(^|\/)cf-access-proxy$/.test(process.argv[1] || '');

if (suffixes.length > 0 && !isProxy) {
  const UP = 'x-cf-access-upstream';
  const SCHEME = 'x-cf-access-scheme';

  const patchModule = (mod, name) => {
    const original = mod[name];
    mod[name] = function (...args) {
      let opts = null;
      let rest = [];
      let host;
      let scheme;
      let target;

      if (typeof args[0] === 'string' || args[0] instanceof URL) {
        const u = new URL(args[0].toString());
        if (!matches(u.host)) return original.apply(this, args);
        host = u.host;
        scheme = u.protocol.replace(':', '');
        target = u.pathname + u.search;
        if (args[1] && typeof args[1] === 'object') {
          opts = { ...args[1] };
          rest = args.slice(2);
        } else {
          rest = args.slice(1);
        }
      } else if (args[0] && typeof args[0] === 'object') {
        const h = args[0].hostname || args[0].host;
        if (!matches(h)) return original.apply(this, args);
        opts = { ...args[0] };
        host = args[0].port ? `${h.split(':')[0]}:${args[0].port}` : h;
        scheme = (opts.protocol || (mod === https ? 'https:' : 'http:')).replace(':', '');
        target = opts.path || '/';
        rest = args.slice(1);
      } else {
        return original.apply(this, args);
      }

      opts = {
        ...(opts || {}),
        protocol: 'http:',
        hostname: '127.0.0.1',
        host: undefined,
        port: PORT,
        path: target,
        headers: { ...(opts?.headers || {}), [UP]: host, [SCHEME]: scheme },
      };
      delete opts.servername;
      delete opts.ca;
      delete opts.rejectUnauthorized;
      opts.agent = undefined; // an https.Agent cannot serve an http request
      return http[name].call(http, opts, ...rest);
    };
  };

  patchModule(https, 'request');
  patchModule(https, 'get');
  patchModule(http, 'request');
  patchModule(http, 'get');

  if (typeof globalThis.fetch === 'function') {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = function (input, init) {
      try {
        const href = typeof input === 'string' ? input : (input?.url ?? input?.href);
        const u = href ? new URL(href) : null;
        if (u && matches(u.host)) {
          const headers = new Headers(init?.headers || (input?.headers ?? undefined));
          headers.set(UP, u.host);
          headers.set(SCHEME, u.protocol.replace(':', ''));
          const local = `http://127.0.0.1:${PORT}${u.pathname}${u.search}`;
          // A Request instance carries method/body/etc; spread it, then override.
          const base = typeof input === 'string' || input instanceof URL ? {} : input;
          return originalFetch.call(this, local, { ...base, ...init, headers });
        }
      } catch {
        // Fall through: an unparseable input is the original fetch's problem.
      }
      return originalFetch.call(this, input, init);
    };
  }
}
