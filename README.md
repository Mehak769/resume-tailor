# resume-tailor

A production-grade CLI tool that intelligently tailors software engineering resumes for specific job descriptions using LLMs (optimized for Google Gemini).

## Features

- **Multi-Format Ingestion**: Ingests resumes in **LaTeX (`.tex`)**, **PDF (`.pdf`)**, or **Word (`.docx`)**.
- **Job Description Extraction**: Ingests job postings directly from career portal **URLs** or **raw text** with built-in SSRF protection.
- **ATS & Skills Optimization**: Analyzes requirements and restructures experience bullets following the Google **Action + Context + Measurable Result (X-Y-Z)** framework.
- **Strict Anti-Hallucination**: Tailors narrative and vocabulary to the target JD without inventing unheld roles, degrees, or false accomplishments.
- **Native LaTeX Workflow**: Reads your `.tex` resume and exports both a tailored `.tex` source and a compiled, publication-ready `.pdf` via `pdflatex`.
- **ATS Alignment Scoring**: Displays estimated ATS match score and a breakdown table of applied changes and rationales.

---

## Quick Start

### 1. Installation

```bash
# Clone and enter the repository
cd resume-tailor

# Install dependencies using uv
uv sync --all-extras
```

### 2. Configure Your Gemini API Key

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```dotenv
LLM_MODEL=gemini/gemini-3.6-flash
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Simple & Frictionless Usage

You don't need to remember long flags. You have three simple ways to run:

### Option A: The Interactive Wizard (Recommended for New Users)
Simply run:
```bash
./run.sh
```
or
```bash
resume-tailor
```
The wizard will guide you step-by-step:
1. Automatically detects `base_resume/resume.tex` (or prompts for your custom file)
2. Asks for the Job URL or raw text
3. Optionally asks for the company name (auto-detected if empty)
4. Previews optimizations or generates output

---

### Option B: 1-Command Shorthand
Simply pass the job posting URL or text directly:
```bash
resume-tailor "https://careers.google.com/jobs/results/12345"
```
*(Automatically uses `base_resume/resume.tex` and creates `applications/<Company>/`)*

---

### Option C: Advanced Flags (for Power Users & Scripts)
```bash
resume-tailor \
  --resume ./base_resume/resume.tex \
  --jd-url "https://careers.company.com/job/12345" \
  --company "Google"
```

> **Note:** Every application is neatly saved into its own company directory (e.g. `applications/Google/`) containing both `resume.tex`, `resume.pdf` (compiled with pdflatex), and `job_description.txt`!

---

## CLI Options

| Option | Flag | Description |
|---|---|---|
| `--resume` | `-r` | Path to original resume (`.tex`, `.pdf`, `.docx`) **[Required]** |
| `--jd-url` | `-u` | URL of the job posting |
| `--jd-text` | `-t` | Raw text of the job description |
| `--output` | `-o` | Custom output file destination |
| `--model` | `-m` | Override default LLM model (e.g. `gemini/gemini-2.0-flash`) |
| `--dry-run` | | Preview ATS score and changes table without exporting files |
| `--debug` | | Enable verbose stack traces and debug logs |

---

## Development & Testing

```bash
# Run tests
uv run pytest

# Check formatting & linting
uv run ruff check .
uv run ruff format --check .

# Strict type checking
uv run mypy src
```
