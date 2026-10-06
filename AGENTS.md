# Neys Newsletter Assistant

Read `docs/development_workflow.md`, `docs/django_architecture_baseline.md` and `docs/ROADMAP.md` before edits. `project.config.json` owns project metadata.

- Inspect branch, HEAD, working tree and remote before changes. Pull only with `--ff-only`; never force-push or reset user work.
- Complete one context before starting another. `main` is the integration truth.
- Domain writes belong in services, complex reads in selectors. Views/tasks are thin. No speculative fallbacks or empty layers.
- Gate: Django check, migration check, pytest, Ruff lint/format. Tests use PostgreSQL.
- Document implemented state, actual validations and limitations in the same work package. Never commit secrets or customer data.
- `docs/userGuide.md` documents user workflows; `docs/technicalDescription.md` architecture/operation. Notion views are generated; no Notion sync until explicit project mapping exists.
- No customer mailing, real import or production deployment during bootstrap. Tracking stays off until D05 is resolved.
