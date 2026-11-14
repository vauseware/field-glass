# Security policy

## Report a problem

Report security problems privately through GitHub:
[open a private vulnerability report](https://github.com/dvause/field-glass/security/advisories/new).
Don't open a public issue, pull request or discussion for them.

Say what you found, how to reproduce it and what it affects. We aim to reply within 7 days, and to agree with you
when to disclose it once a fix is out.

## Scope

Field Glass is a static site: HTML, JavaScript and JSON served from Cloudflare Workers static assets at
https://fieldglass.vause.io. It has no accounts, server code or user data. In scope:

- Script injection through battle data, URL fragments or the Sources dialog.
- Anything in this repo that runs on a contributor's machine: `tools/`, the battles' `make.py` scripts and
  `.claude/` scripts.
- Secrets or personal data committed to this repo.

Out of scope: problems in Cloudflare, Google Fonts or the terrain services themselves (report those to them),
and denial-of-service against the live site.

## Supported versions

Only the current `main` branch and the live site get fixes.
