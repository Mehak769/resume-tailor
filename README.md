# resume-tailor

<div align="center">

[![CI](https://github.com/Mehak769/resume-tailor/actions/workflows/ci.yml/badge.svg)](https://github.com/Mehak769/resume-tailor/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Powered by: Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini%203-8E75C2.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**An intelligent, production-grade CLI tool that tailors software engineering resumes for specific job descriptions using LLMs and native LaTeX compilation.**

[Architecture](#architecture) • [Features](#features) • [Quick Start](#quick-start) • [Usage Options](#usage-options) • [Testing](#testing)

</div>

---

## Architecture

`resume-tailor` is built with a clean ports-and-adapters architecture, ensuring complete separation between input ingestion, LLM orchestration, and typesetting engines:

```mermaid
flowchart TD
    subgraph Ingestion ["1. Ingestion Layer"]
        A1["Base Resume<br><code>base_resume/resume.tex</code><br><i>(.tex, .pdf, .docx)</i>"] --> P1["Parser Factory<br>(LaTeX / PDF / DOCX)"]
        A2["Job Posting<br>URL / Text / File"] --> P2["Resilient Scraper<br>• Schema.org JSON-LD<br>• Browser UA & SSRF Guard"]
    end

    subgraph Intelligence ["2. Reasoning & Tailoring Engine"]
        P1 --> LLM["LLM Orchestrator (Google Gemini 3)<br>• Structured Output Schema<br>• Google X-Y-Z Bullet Framework<br>• Strict Anti-Hallucination Controls<br>• Automatic Exponential Fallback"]
        P2 --> LLM
    end

    subgraph Synthesis ["3. Synthesis & Typesetting"]
        LLM --> EX["LaTeX Typesetting Engine<br>• Character Escaping (&, %, $, _)<br>• Hyperlink Protocol Normalization<br>• Auto pdflatex Compilation"]
    end

    subgraph Output ["4. Organized Application Package"]
        EX --> PKG["applications/&lt;Company&gt;/<br>├── resume.tex (Tailored LaTeX Source)<br>├── resume.pdf (Compiled Production Resume PDF)<br>├── cover_letter.tex (Matching Cover Letter Source)<br>├── cover_letter.pdf (Compiled Cover Letter PDF)<br>├── analysis.md (Match Analysis & Interview Prep Kit)<br>└── job_description.txt (Archived JD)"]
    end
```

---

## Features

- **Multi-Format Ingestion**: Ingests master resumes in **LaTeX (`.tex`)**, **PDF (`.pdf`)**, or **Word (`.docx`)**.
- **Enterprise Career Portal Scraper**: Extracts jobs from career sites (Allianz, Workday, Greenhouse, Lever) via Schema.org `JobPosting` JSON-LD, with automated fallback for bot-protected pages.
- **Google X-Y-Z Bullet Optimization**: Restructures experience bullets to follow the *"Accomplished [X] as measured by [Y], by doing [Z]"* framework.
- **Strict Anti-Hallucination**: Tailors vocabulary and emphasis without inventing unheld job titles, false degrees, or fake accomplishments.
- **Native LaTeX Workflow**: Automatically updates your `.tex` source and compiles a publication-ready `.pdf` via `pdflatex` with verified, clickable web links.
- **Automated Cover Letter Generator**: Crafts an articulate, matching 1-page cover letter connecting your technical background to the target company's challenges, compiled directly to `cover_letter.pdf`.
- **Match Analysis & Interview Prep Kit**: Generates a strategic dossier (`analysis.md`) featuring ATS match metrics, skill gaps, resume change audit logs, targeted technical/behavioral interview questions with talking points, and smart questions to ask the interviewer.
- **Clean Application Tree**: Organizes each job application into its own dedicated folder (`applications/<Company>/`) with tailored resume, cover letter, analysis report, and archived job description.
- **Interactive Terminal Assistant**: Zero-friction wizard for new users—no long flags required.



---

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone git@github.com:Mehak769/resume-tailor.git
cd resume-tailor

# Install dependencies using uv
uv sync --all-extras
```

### 2. Configure Your Gemini API Key

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Add your Gemini API key in `.env`:

```dotenv
LLM_MODEL=gemini/gemini-3.6-flash
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_OUTPUT_DIR=./applications
```

---

## Usage Options

### Option A: The Interactive Wizard (Recommended)
Run the launcher without any arguments:
```bash
./run.sh
```

```text
╭──────────────────────────────────────────────────────────────────╮
│ 🎯 Resume Tailor — Quick Assistant                               │
│ Easily optimize your resume for any role in seconds.             │
╰──────────────────────────────────────────────────────────────────╯
1. Path to your resume (base_resume/resume.tex): [Press Enter]
2. Paste Job Posting URL or Job Description: https://careers.company.com/job/123
3. Target Company Name (Optional, auto-detected if empty): Google
4. Preview optimizations first (dry-run)? [y/N]: n
```

---

### Option B: 1-Command Shorthand
Pass the job URL, a text string, or a local text file directly:

```bash
# Via URL
./run.sh "https://careers.allianz.com/de/de/job/102747/AI-Engineer-f-m-d"

# Via saved job description file
./run.sh job.txt -c "Allianz"
```

---

### Option C: Advanced CLI Flags
```bash
resume-tailor \
  --resume ./base_resume/resume.tex \
  --jd-url "https://careers.company.com/job/12345" \
  --company "Allianz" \
  --dry-run
```

---

## Output Structure

Every application is neatly organized in its own company folder:

```text
applications/
└── Allianz/
    ├── resume.tex           # Tailored LaTeX source code
    ├── resume.pdf           # Compiled production resume PDF
    ├── cover_letter.tex     # Matching LaTeX cover letter source
    ├── cover_letter.pdf     # Compiled 1-page cover letter PDF
    ├── analysis.md          # Strategic match analysis & interview prep kit
    └── job_description.txt  # Archived job requirements for interview prep
```

---

## CLI Reference

| Option | Flag | Default | Description |
|---|---|---|---|
| `job` | *(Arg)* | `None` | Shorthand: Job URL, text file path, or raw JD text |
| `--company` | `-c` | Auto-detected | Company name for the application folder |
| `--resume` | `-r` | `base_resume/resume.tex` | Path to master resume (`.tex`, `.pdf`, `.docx`) |
| `--jd-url` | `-u` | `None` | URL of the job posting |
| `--jd-text` | `-t` | `None` | Raw text of the job description |
| `--cover-letter` | | `True` | Generate matching tailored cover letter (`.tex` & `.pdf`) |
| `--analysis` | | `True` | Generate match analysis & interview prep kit (`analysis.md`) |
| `--output` | `-o` | `applications/<Company>/` | Custom destination file or directory |
| `--model` | `-m` | `gemini/gemini-3.6-flash` | Override default LLM model |
| `--dry-run` | | `False` | Preview match score and diff table without writing files |
| `--debug` | | `False` | Enable verbose debug logs and stack traces |

---

## Testing & Quality Assurance

The codebase enforces strict type safety and code quality:

```bash
# Run the test suite (17/17 passing)
uv run pytest

# Check code formatting & linting with Ruff
uv run ruff check .
uv run ruff format --check .

# Run strict type checking with MyPy
uv run mypy src


```

---

## Community & Contributing

Contributions are welcome! Please check our community guidelines:
- [Contributing Guide](CONTRIBUTING.md) — Setup instructions and development standards
- [Code of Conduct](CODE_OF_CONDUCT.md) — Community standards and enforcement
- [Security Policy](SECURITY.md) — Responsible vulnerability disclosure

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

