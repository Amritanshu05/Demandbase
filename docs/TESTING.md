# Testing

## Automated integration tests

From the project root, activate the environment installed in SETUP.md:

```bash
python -m unittest discover -s tests -v
```

Tests use Flask's real request client, a temporary on-disk SQLite database and upload directory, and an injected server clock. They never use or delete normal application data.

Coverage includes:

- Create, preview, download, and code-whitespace preservation.
- XSS-safe text/code/document preview.
- Required values and enum/length checks.
- Safe links and closed-link destination protection.
- Upload signatures, extension allowlist, and oversize rejection.
- Owner isolation, cross-session revoke denial, and CSRF failure.
- Expiry at the exact timestamp on preview/download.
- Document revocation and physical payload removal.
- Search and per-browser private workspace.
- Security response headers and host restrictions.
- Cleanup and restart persistence.
- Persistent per-owner creation quota.

No coverage-percentage threshold is claimed. Tests are predominantly integration-sized because authorization, lifecycle, SQLite, and filesystem boundaries are the core product risks.

## Dependency checks

Runtime dependencies and their transitive versions are pinned in `requirements.txt`; no frontend dependency tree exists.

To check published advisories:

```bash
python -m pip install pip-audit
python -m pip_audit -r requirements.txt
```

The audit tool is development-only and is not required to run the app. Audit results are point-in-time signals, not proof of security.

## Browser checklist

- Owner creates text/code/link/document; recipient can open and download.
- Owner revokes; subsequent recipient preview and download both fail.
- One-minute share expires without changing client time.
- Error states render correctly; invalid fields preserve values.
- JavaScript has no console errors on normal successful flows.
- Copy works or gives actionable fallback feedback.
- At a mobile viewport, there is no horizontal page overflow.
- Keyboard can reach all controls, and focus remains visible.
- With JS disabled, creation and revocation still work; type-specific fields are all visible with explanatory labels.
- Refreshing a successful creation does not create another share.

## Known untested boundaries

Formal accessibility compliance, screen-reader/device coverage, Windows/macOS startup, sustained load, crash recovery, simultaneous quota races, and adversarial PDF parsing are not claimed as verified by this suite.

## Implementation verification

Verified on Linux with Python 3.14 and Chromium on 19 November 2026:

- 23 automated tests, including first-start signing-key generation/reuse.
- Runtime dependency audit reported no known vulnerabilities.
- Desktop dashboard and creation form visually inspected; mobile dashboard and document page inspected at 390 px.
- Browser-created code preview and document upload; recipient preview and document download verified.
- Separate recipient context had neither owner controls nor owner's resources in its workspace.
- After browser revocation, both resource page and download returned 410.
- With JavaScript disabled, link creation and revocation succeeded.
- Mobile dashboard and share page had no horizontal overflow.

These observations are not a formal accessibility or performance certification. Run the commands again after changes.
