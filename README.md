# awesome-skills

A monorepo of reusable Agent Skills for Codex-compatible agents.

## Skills

- [`npm-package-scan`](skills/npm-package-scan/): audit JavaScript and TypeScript dependencies.
- [`safe-clawhub-publisher`](skills/safe-clawhub-publisher/): validate, publish, and verify ClawHub skills and OpenClaw plugins.

Each Skill is independently versioned in the `metadata.version` field of its `SKILL.md`.

## Local testing

The canonical source is `skills/`. The local `.agents/skills` path is a symlink to that directory so the Skills can be tested without maintaining duplicate copies.

## Releases

This repository uses Release Please Manifest with Conventional Commits. Tags use the format `<skill-name>-v<version>`, and each Skill gets its own generated changelog and release PR.
