# Security and operations checklist (Day 18)

## Implemented and checked

- Project, conversation, message, Run, Artifact, Reflection and activity queries are scoped to the signed-in owner; cross-project Artifact detail/download returns 404.
- Artifact content is database JSON. Download does not accept a filesystem path, fixes the response MIME type to JSON, sets an attachment name and `X-Content-Type-Options: nosniff`.
- API JSON bodies in project/execution endpoints are capped at 64 KiB. Planning output is capped at 100 KiB and validated by schema before persistence.
- Mutating browser requests pass Django CSRF middleware. Session cookies are HttpOnly and SameSite=Lax; production mode enables Secure session/CSRF cookies and content sniffing/referrer protections.
- Unexpected Planning exceptions are logged with run/execution IDs and exception class only; raw exception text/stack is not emitted by this handler or returned to users.
- Production mode requires `DJANGO_SECRET_KEY`; development-generated keys stay in the ignored local secret file. `DJANGO_ALLOWED_HOSTS` is configurable.
- Duplicate Run submission is protected by a database uniqueness constraint and client idempotency key. Retry calls are capped at three.

## Required before production

- Replace the current SQLite-only database configuration with a supported production database and configure concurrent worker locking. Do not run multiple workers against SQLite as a production queue.
- Configure HTTPS at the ingress, `DJANGO_SECURE_SSL_REDIRECT=1` where the proxy setup supports it, and a deliberate `DJANGO_SECURE_HSTS_SECONDS` only after HTTPS is verified.
- Configure database backup cadence, encrypted backup storage, restore drills, retention periods and account/data deletion procedures. These are not automated in this MVP.
- Add an actual external provider adapter only with secret-manager injection, network timeouts, request redaction, per-user/project quotas and a spend cap. No external provider is configured now.
- Add alerting and durable queue recovery/dead-letter handling before relying on long-running background work.

## Out of scope in this MVP

- User file uploads, malware scanning and file retention are absent; current Artifact downloads contain validated JSON stored in the database.
- OAuth, email invitations, production identity verification and enterprise audit retention are not implemented.
