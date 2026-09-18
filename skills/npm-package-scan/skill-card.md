## Description

Audit JavaScript and TypeScript repository dependencies for security, supply-chain, maintenance, version, lockfile, and cleanup risks across npm, pnpm, Yarn, and Bun projects.

## Publisher

[geoffrey-xiao](https://clawhub.ai/geoffrey-xiao)

## License

MIT-0

## Use case

Developers use this skill for an evidence-based, read-only dependency review before upgrades, releases, migrations, or security remediation. It supports single-package repositories and workspaces/monorepos.

## Known risks and mitigations

- Registry-backed audit and outdated checks can disclose dependency names and versions. The skill uses an offline-first workflow and requires that network use be disclosed before those commands run.
- Audit tools may produce noisy or context-free results. The skill requires dependency-path, resolved-version, production-reachability, and remediation checks before assigning high severity.
- Unused-package detection can miss dynamic imports, plugins, and framework conventions. Such findings remain `needs verification` unless those paths are checked.
- Automatic fixes can alter manifests and lockfiles or introduce breaking changes. The review forbids installs, upgrades, removals, lockfile regeneration, and audit fixes unless explicitly requested.

## Output

Prioritized Markdown report by default, with optional JSON export for CI, archiving, and future diffing. Reports include scope, confidence, network-check context, evidence, impact, verification commands, blast radius, and a sequenced upgrade or cleanup plan.

## Version

1.1.0
