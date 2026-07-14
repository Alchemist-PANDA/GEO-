# Credential exposure runbook

Use this process whenever a credential appears in a tracked file or Git history.

1. Revoke or rotate the credential in its provider console immediately. Treat it as compromised even if the repository
   was private.
2. Remove the credential from the current tree and verify with `python scripts/check_secrets.py`.
3. Identify affected commits and access logs without copying the credential into tickets, chat, or reports.
4. Obtain repository-owner approval before rewriting shared history. Use `git filter-repo` with a replacement map,
   force-push protected branches deliberately, and require every collaborator to re-clone.
5. Invalidate caches, build artifacts, CI logs, and releases containing the old object.
6. Confirm the revoked credential fails and the replacement is stored only in the deployment secret manager.
7. Document timestamps, scope, owner, rotation evidence, and follow-up controls.

History rewriting does not revoke a credential. Rotation is the hard security boundary.
