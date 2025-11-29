# Contributing

Thank you for considering contributing to tonie-podcast-sync! This project welcomes contributions from everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please [open an issue](https://github.com/alexhartm/tonie-podcast-sync/issues) with:

- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Features

Feature requests are welcome! Please [open an issue](https://github.com/alexhartm/tonie-podcast-sync/issues) describing:

- The feature you'd like to see
- Why it would be useful
- Any implementation ideas you have

### Code Contributions

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/your-username/tonie-podcast-sync.git
   cd tonie-podcast-sync
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

4. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

5. **Make your changes**
   - Write clear, documented code
   - Follow the existing code style (Ruff is used for linting)
   - Add tests for new functionality

6. **Run tests and linting**
   ```bash
   pytest
   ruff check .
   ```

7. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description of feature"
   ```

8. **Push to your fork**
   ```bash
   git push origin feature/my-new-feature
   ```

9. **Open a Pull Request** on GitHub

## Development Setup

### Prerequisites

- Python >= 3.10.11
- ffmpeg (for testing volume adjustment features)

### Install Development Environment

```bash
# Clone the repository
git clone https://github.com/alexhartm/tonie-podcast-sync.git
cd tonie-podcast-sync

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tonie_podcast_sync

# Run specific test file
pytest tests/test_specific.py
```

### Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check code style
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

## Code Review Process

All contributions go through code review:

1. A maintainer will review your pull request
2. They may request changes or ask questions
3. Once approved, your changes will be merged
4. You'll be added to the contributors list!

## Recognition

Contributors are recognized using the [all-contributors](https://allcontributors.org/) specification.

After your first contribution, comment on your PR with:

```
@all-contributors please add @your-username for code
```

Replace `code` with your contribution type (code, docs, bug reports, ideas, etc.).

## Current Contributors

<!-- ALL-CONTRIBUTORS-LIST:START -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/alexhartm"><img src="https://avatars.githubusercontent.com/u/16985220?v=4?s=100" width="100px;" alt="Alexander Hartmann"/><br /><sub><b>Alexander Hartmann</b></sub></a><br /><a href="https://github.com/alexhartm/tonie-podcast-sync/commits?author=alexhartm" title="Code">💻</a> <a href="#ideas-alexhartm" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-alexhartm" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Wilhelmsson177"><img src="https://avatars.githubusercontent.com/u/16141053?v=4?s=100" width="100px;" alt="Wilhelmsson177"/><br /><sub><b>Wilhelmsson177</b></sub></a><br /><a href="https://github.com/alexhartm/tonie-podcast-sync/commits?author=Wilhelmsson177" title="Code">💻</a> <a href="#ideas-Wilhelmsson177" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-Wilhelmsson177" title="Maintenance">🚧</a> <a href="https://github.com/alexhartm/tonie-podcast-sync/commits?author=Wilhelmsson177" title="Tests">⚠️</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://cv.maltebaer.vercel.app/"><img src="https://avatars.githubusercontent.com/u/29504917?v=4?s=100" width="100px;" alt="Malte Bär"/><br /><sub><b>Malte Bär</b></sub></a><br /><a href="https://github.com/alexhartm/tonie-podcast-sync/issues?q=author%3Amaltebaer" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/einvalentin"><img src="https://avatars.githubusercontent.com/u/230592?v=4?s=100" width="100px;" alt="Valentin v. Seggern"/><br /><sub><b>Valentin v. Seggern</b></sub></a><br /><a href="https://github.com/alexhartm/tonie-podcast-sync/commits?author=einvalentin" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/stefan14808"><img src="https://avatars.githubusercontent.com/u/79793534?v=4?s=100" width="100px;" alt="stefan14808"/><br /><sub><b>stefan14808</b></sub></a><br /><a href="https://github.com/alexhartm/tonie-podcast-sync/commits?author=stefan14808" title="Code">💻</a> <a href="#ideas-stefan14808" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/goldbricklemon"><img src="https://avatars.githubusercontent.com/u/9368670?v=4?s=100" width="100px;" alt="GoldBrickLemon"/><br /><sub><b>GoldBrickLemon</b></sub></a><br /><a href="https://github.com/alexhartm/tonie-podcast-sync/issues?q=author%3Agoldbricklemon" title="Bug reports">🐛</a> <a href="https://github.com/alexhartm/tonie-podcast-sync/commits?author=goldbricklemon" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>
<!-- ALL-CONTRIBUTORS-LIST:END -->

## Acknowledgments

This project builds upon:

- [tonie_api](https://github.com/moritzj29/tonie_api) by @moritzj29
- Blog posts by [Tobias Raabe](https://tobiasraabe.github.io/blog/how-to-download-files-with-python.html)
- Articles by [Matthew Wimberly](https://codeburst.io/building-an-rss-feed-scraper-with-python-73715ca06e1f)

## Questions?

Feel free to ask questions by [opening an issue](https://github.com/alexhartm/tonie-podcast-sync/issues) or starting a [discussion](https://github.com/alexhartm/tonie-podcast-sync/discussions).
