# TECHA Security Baseline

- Secrets and credentials are prohibited from source control.
- Runtime configuration is supplied through environment variables or a secret manager.
- Financial inputs are validated at the API boundary and again by the calculation engine.
- Currency conversion requires an explicit rate and source.
- Evidence status is retained as metadata and is never silently promoted.
- Database foreign keys are enabled for the SQLite persistence layer.
- Production deployment must terminate TLS at the edge and restrict administrative endpoints.
- Dependency versions are bounded in the package manifest; CI must test every push and pull request.
