# depwatch

> Lightweight daemon that monitors dependency files and sends alerts when outdated or vulnerable packages are detected.

---

## Installation

```bash
pip install depwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/depwatch.git && cd depwatch && pip install .
```

---

## Usage

Start the daemon to watch a project directory:

```bash
depwatch start --path /path/to/your/project
```

depwatch will automatically detect supported dependency files (`requirements.txt`, `package.json`, `Pipfile`, etc.) and begin monitoring them. Alerts are sent to your configured channel when outdated or vulnerable packages are found.

**Example config (`depwatch.yml`):**

```yaml
watch:
  - requirements.txt
  - package.json
alerts:
  email: dev@example.com
  interval: 24h
```

Run a one-time scan without starting the daemon:

```bash
depwatch scan --path /path/to/your/project
```

View currently monitored files and their status:

```bash
depwatch status
```

---

## Supported Dependency Files

| File | Ecosystem |
|------|-----------|
| `requirements.txt` | Python |
| `package.json` | Node.js |
| `Pipfile` | Python |
| `Gemfile` | Ruby |

---

## License

This project is licensed under the [MIT License](LICENSE).