# Agent Instructions for tonie-podcast-sync

## Project Overview
tonie-podcast-sync is a Python package that syncs podcast episodes to creative tonies (Toniebox). It downloads podcast episodes and uploads them to Tonie Cloud, which then syncs to physical Tonie figurines.

## Agent Guidelines

### Reoccuring Tasks
This project uses [mise-en-place](https://mise.jdx.dev) for task running. Inspect `mise.toml` for available tasks.
**Key tasks:**
- Run `mise build` to build the project
- Run `mise test` to run tests
- Run `mise lint` and `mise format` for code quality
Execute tasks with: `mise <task-name>` or `mise run <task-name>`
