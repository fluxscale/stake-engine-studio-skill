# Publishing this skill on skills.sh

This guide publishes the agent skill, not a casino game. Game submission guidance lives in [Studio publishing](skills/stake-engine-studio/references/publishing.md).

## How discovery works

The [skills.sh FAQ](https://skills.sh/docs/faq) says skills are hosted on GitHub and become listed through installs recorded by the skills CLI. There is no separate npm package or skills.sh upload required for this repository. A successful local discovery check does not establish a live leaderboard listing. Do not manufacture install counts or promise immediate indexing.

The distributable skill is `skills/stake-engine-studio/`. Keep all required runtime references, scripts, and templates inside that folder. Root maintenance files do not need to be installed with it.

## Prepare a release

1. Review the skill, helpers, source dates, links, and license. Confirm that no credentials, session URLs, downloaded vendor manuals, or generated game artifacts are included.
2. Run the checks below and resolve failures. Review the behavioral scenarios, especially unit conversion, replay isolation, source conflicts, and authorization boundaries.
3. Update skill metadata version and relevant source-verification dates only when those sources have actually been checked. Preserve a record of upstream commits in `upstream-lock.json`.
4. Publish the reviewed commit to the public GitHub repository through the maintainer's usual Git/PR process. A release tag is useful for provenance but not required for CLI discovery. Preparation does not push or create a release automatically.

```sh
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s tests -v
DISABLE_TELEMETRY=1 npx skills add . --list
```

## Verify installation

After the public branch contains the skill, list remote discovery:

```sh
DISABLE_TELEMETRY=1 npx skills add fluxscale/stake-engine-studio-skill --list
```

In a disposable project, install and inspect the complete folder:

```sh
DISABLE_TELEMETRY=1 npx skills add fluxscale/stake-engine-studio-skill --skill stake-engine-studio --agent claude-code codex --copy -y
```

Do not perform the smoke installation in an unrelated working project. Confirm that both agents discover the skill, references resolve, helper `--help` works, and example prompts select the intended workflow. The root README gives normal user installation commands without disabling telemetry; users may opt out with `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1`. Sources: [skills CLI](https://github.com/vercel-labs/skills), [telemetry documentation](https://skills.sh/docs/cli).

Once an actual listing exists, verify its URL before adding a listing badge or claiming publication. A public Git repository, a successful install, and a visible skills.sh listing are separate pieces of evidence.

## Release evidence

Record commit/tag, validation results, CLI version, remote discovery, agent installation checks, and the observed listing URL if available. State exactly what was completed; leave account-dependent or unpublished steps explicit.
