import re
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from resume_tailor.config import settings
from resume_tailor.core.exceptions import JobDescriptionScraperError, ResumeTailorError
from resume_tailor.core.logging import setup_logging
from resume_tailor.core.models import JobDescription
from resume_tailor.exporters.base import BaseResumeExporter
from resume_tailor.exporters.docx_exporter import DocxResumeExporter
from resume_tailor.exporters.latex_exporter import LaTeXResumeExporter
from resume_tailor.exporters.pdf_exporter import PDFResumeExporter
from resume_tailor.llm.client import LLMTailorService
from resume_tailor.parsers.base import BaseResumeParser
from resume_tailor.parsers.docx_parser import DocxResumeParser
from resume_tailor.parsers.latex_parser import LaTeXResumeParser
from resume_tailor.parsers.pdf_parser import PDFResumeParser
from resume_tailor.scrapers.web_scraper import WebJDScraper

app = typer.Typer(
    name="resume-tailor",
    help="Intelligently tailor your resume for any job description via LLM.",
    add_completion=False,
)
console = Console()


def get_default_base_resume() -> Path | None:
    """Finds the default base resume in base_resume/ or root directory."""
    for candidate in [
        Path("base_resume/resume.tex"),
        Path("base_resume/base_resume.tex"),
        Path("base_resume.tex"),
    ]:
        if candidate.exists():
            return candidate
    return None


def read_multiline_input(prompt_text: str) -> str:
    """Reads multiline input from stdin until EOF (Ctrl+D) or 'END' keyword."""
    console.print(prompt_text)
    console.print(
        "[dim](Paste your text below. When finished, press [bold]Enter[/bold] and [bold]Ctrl+D[/bold], or type [bold]END[/bold] on a new line):[/dim]"
    )
    lines: list[str] = []
    try:
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines).strip()


@app.command()
def tailor(
    job: Annotated[
        str | None,
        typer.Argument(
            help="Shorthand: Job posting URL or raw text",
        ),
    ] = None,
    company: Annotated[
        str | None,
        typer.Option("--company", "-c", help="Company name (e.g. Allianz, Google)"),
    ] = None,
    resume_path: Annotated[
        Path | None,
        typer.Option(
            "--resume",
            "-r",
            help="Path to input resume (.tex, .pdf, or .docx)",
        ),
    ] = None,
    jd_url: Annotated[
        str | None,
        typer.Option("--jd-url", "-u", help="URL of the job posting"),
    ] = None,
    jd_text: Annotated[
        str | None,
        typer.Option("--jd-text", "-t", help="Raw job description text"),
    ] = None,
    output_path: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Custom output path"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Override LLM model name"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Display tailoring diff and score without writing file",
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable verbose debug logs"),
    ] = False,
) -> None:
    """Analyze, align, and generate a tailored resume for a specific job."""
    setup_logging(level="DEBUG" if debug else settings.log_level)

    # 1. Shorthand resolution: resume-tailor "https://...", "job.txt", or raw text
    if job:
        job_candidate = Path(job)
        if job.startswith(("http://", "https://")):
            jd_url = job
        elif job_candidate.is_file():
            jd_text = job_candidate.read_text(encoding="utf-8")
        else:
            jd_text = job

    # 2. Interactive Wizard if no job description was passed and running interactively
    is_interactive = sys.stdin.isatty()

    if not jd_url and not jd_text:
        if is_interactive:
            console.print(
                Panel(
                    "[bold cyan]🎯 Resume Tailor — Quick Assistant[/bold cyan]\n"
                    "[dim]Easily optimize your resume for any role in seconds.[/dim]",
                    border_style="cyan",
                )
            )

            # Resolve resume path interactively
            default_res_path = get_default_base_resume()
            default_res = str(default_res_path) if default_res_path else "base_resume/resume.tex"
            res_input = Prompt.ask(
                "[bold green]1.[/bold green] Path to your resume",
                default=default_res,
            )
            resume_path = Path(res_input)

            # Resolve Job Description interactively
            jd_input = Prompt.ask(
                "[bold green]2.[/bold green] Paste Job Posting URL or Job Description"
            ).strip()

            if jd_input.startswith(("http://", "https://")):
                jd_url = jd_input
            else:
                jd_text = jd_input

            # Optional company name
            if not company:
                company_input = Prompt.ask(
                    "[bold green]3.[/bold green] Target Company Name (Optional, auto-detected if empty)",
                    default="",
                ).strip()
                if company_input:
                    company = company_input

            # Ask about dry-run
            if not dry_run:
                dry_run = Confirm.ask(
                    "[bold green]4.[/bold green] Preview optimizations first (dry-run)?",
                    default=False,
                )
        else:
            console.print(
                "[bold red]Error:[/bold red] You must provide either a Job URL, text, or use interactive mode."
            )
            console.print('Usage: [bold cyan]resume-tailor "<job-url-or-text>"[/bold cyan]')
            raise typer.Exit(code=1)

    # 3. Default resume to base_resume/resume.tex if omitted and file exists
    if resume_path is None:
        default_res_path = get_default_base_resume()
        if default_res_path:
            resume_path = default_res_path
        else:
            console.print(
                "[bold red]Error:[/bold red] No resume specified and base resume not found in base_resume/. Use --resume."
            )
            raise typer.Exit(code=1)

    if not resume_path.exists():
        console.print(f"[bold red]Error:[/bold red] Resume file not found: {resume_path}")
        raise typer.Exit(code=1)

    try:
        # 1. Parse Resume
        with console.status(f"[bold cyan]Parsing original resume ({resume_path.name})..."):
            ext = resume_path.suffix.lower()
            parser: BaseResumeParser
            if ext == ".pdf":
                parser = PDFResumeParser()
            elif ext == ".docx":
                parser = DocxResumeParser()
            elif ext in {".tex", ".latex"}:
                parser = LaTeXResumeParser()
            else:
                console.print(
                    f"[bold red]Unsupported file extension:[/bold red] {ext} (supported: .pdf, .docx, .tex)"
                )
                raise typer.Exit(code=1)

            parsed_resume = parser.parse(resume_path)

        # 2. Extract Job Description
        scraper = WebJDScraper()
        jd_source = jd_url if jd_url else (jd_text or "")
        job_desc: JobDescription

        try:
            with console.status("[bold cyan]Extracting job description..."):
                job_desc = scraper.scrape(jd_source)
        except JobDescriptionScraperError as scrape_err:
            if is_interactive:
                console.print(f"\n[bold yellow]Notice:[/bold yellow] {scrape_err}")
                pasted_jd = read_multiline_input(
                    "[bold green]Paste Job Description text:[/bold green]"
                )
                if not pasted_jd.strip():
                    raise typer.Exit(code=1) from scrape_err
                job_desc = JobDescription(source="raw_text", raw_text=pasted_jd.strip())
            else:
                raise

        # 3. LLM Orchestration
        with console.status("[bold cyan]Structuring and tailoring resume with Gemini..."):
            llm_service = LLMTailorService(model_name=model)
            # Hydrate structure if raw text only
            if not parsed_resume.experience and parsed_resume.raw_text:
                parsed_resume = llm_service.parse_raw_resume_to_structure(parsed_resume.raw_text)

            tailored_resume = llm_service.tailor(parsed_resume, job_desc)

        # 4. Display Summary Table
        console.print(
            Panel(
                f"[bold green]Estimated ATS Alignment Score:[/bold green] {tailored_resume.ats_score_estimate}/100\n"
                f"[bold blue]Target Role:[/bold blue] {tailored_resume.target_job_title}\n"
                f"[bold cyan]Target Company:[/bold cyan] {company or tailored_resume.target_company or job_desc.company or 'General'}",
                title="Analysis Summary",
            )
        )

        if tailored_resume.changes:
            table = Table(
                title="Applied Optimizations",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Section", style="dim", width=16)
            table.add_column("Tailored Content", style="green")
            table.add_column("Reasoning", style="cyan")

            for change in tailored_resume.changes[:6]:  # Show top changes
                table.add_row(change.section, change.tailored[:120] + "...", change.reasoning)
            console.print(table)

        if dry_run:
            console.print("[bold yellow]Dry-run enabled. Skipping file export.[/bold yellow]")
            return

        # 5. Export to dedicated Company folder
        with console.status("[bold cyan]Exporting tailored resume package..."):
            target_ext = output_path.suffix.lower() if output_path else ext

            raw_company = company or tailored_resume.target_company or job_desc.company or "General"
            # Clean folder name (e.g. "Allianz Insurance" -> "Allianz" or "Allianz_Insurance")
            clean_company = re.sub(r"[^\w\s-]", "", raw_company).strip().replace(" ", "_")
            if not clean_company:
                clean_company = "General"

            if output_path:
                out_file = output_path
                company_folder = out_file.parent
            else:
                company_folder = settings.default_output_dir / clean_company
                company_folder.mkdir(parents=True, exist_ok=True)
                out_file = company_folder / f"resume{target_ext}"

            company_folder.mkdir(parents=True, exist_ok=True)

            exporter: BaseResumeExporter
            if target_ext in {".tex", ".latex"}:
                exporter = LaTeXResumeExporter(compile_pdf=True)
            elif target_ext == ".docx":
                exporter = DocxResumeExporter()
            else:
                if ext in {".tex", ".latex"}:
                    exporter = LaTeXResumeExporter(compile_pdf=True)
                else:
                    exporter = PDFResumeExporter()

            final_path = exporter.export(tailored_resume, out_file)

            # Archive the exact Job Description inside the company folder
            jd_archive_path = company_folder / "job_description.txt"
            jd_archive_content = (
                f"Target Role: {tailored_resume.target_job_title}\n"
                f"Company: {raw_company}\n"
                f"Source: {job_desc.source}\n\n"
                f"Job Description:\n"
                f"{job_desc.raw_text}\n"
            )
            jd_archive_path.write_text(jd_archive_content, encoding="utf-8")

        # Visual Folder Tree
        tree = Tree(f"📁 [bold cyan]{company_folder}[/bold cyan]")
        tree.add(f"📄 [green]{final_path.name}[/green] (Tailored Resume Source)")
        if target_ext in {".tex", ".latex"}:
            pdf_path = final_path.with_suffix(".pdf")
            if pdf_path.exists():
                tree.add(f"📑 [green]{pdf_path.name}[/green] (Compiled Production PDF)")
        tree.add("📝 [dim]job_description.txt[/dim] (Archived Job Description)")

        console.print(
            "\n[bold green]✔ Successfully created company application package:[/bold green]"
        )
        console.print(tree)

    except ResumeTailorError as e:
        console.print(f"[bold red]Application Error:[/bold red] {e}")
        if debug:
            console.print_exception()
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[bold red]Unexpected Failure:[/bold red] {e}")
        if debug:
            console.print_exception()
        raise typer.Exit(code=1) from e


def main() -> None:
    app()


if __name__ == "__main__":
    main()
