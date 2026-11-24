# Repository Notes

- Keep the site GitHub Pages compatible. Anything required at runtime must be served as checked-in static assets from the repository; do not depend on `node_modules` or a build step existing on Pages.
- The site must make no requests to third-party hosts (privacy; see README "Self-hosted dependencies"). Vendor browser libraries, fonts and runtime files under `vendor/`; never load them from a CDN, not even as a fallback. `tests/frontend/e2e/no-third-party.spec.js` enforces this.
- The browser runtime is served from `runtime/`; update it with `scripts/sync-runtime.sh` after changing the vendored dice runtime or `webbridge.py`.
