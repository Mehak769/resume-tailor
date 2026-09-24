import html
import json
import re
from urllib.parse import urlparse

import requests
import trafilatura

from resume_tailor.core.exceptions import JobDescriptionScraperError
from resume_tailor.core.models import JobDescription
from resume_tailor.scrapers.base import BaseJDScraper


class WebJDScraper(BaseJDScraper):
    BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    }

    def scrape(self, source: str) -> JobDescription:
        stripped_source = source.strip()

        # If not a URL, treat as raw text
        if not (stripped_source.startswith("http://") or stripped_source.startswith("https://")):
            return JobDescription(source="raw_text", raw_text=stripped_source)

        parsed_url = urlparse(stripped_source)
        if parsed_url.scheme not in {"http", "https"}:
            raise JobDescriptionScraperError(
                f"Unsupported URL scheme: {parsed_url.scheme}. Only http/https supported."
            )

        hostname = (parsed_url.hostname or "").lower()
        if not hostname or hostname in self.BLOCKED_HOSTS:
            raise JobDescriptionScraperError(f"Invalid or blocked target hostname: {hostname}")

        try:
            # 1. Fetch web page using desktop browser headers
            response = requests.get(
                stripped_source,
                headers=self.DEFAULT_HEADERS,
                timeout=15,
                allow_redirects=True,
            )
            if response.status_code != 200:
                raise JobDescriptionScraperError(
                    f"HTTP {response.status_code} received when fetching {stripped_source}."
                )

            html_content = response.text

            # 2. Priority 1: Check for standard Schema.org JobPosting JSON-LD
            # Used by major enterprise portals: Allianz, Workday, Greenhouse, Lever, Google Jobs
            json_ld_jd = self._extract_json_ld(html_content, stripped_source)
            if json_ld_jd:
                return json_ld_jd

            # 3. Priority 2: Fall back to DOM article extraction with Trafilatura
            extracted_text = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                favor_precision=False,
            )

            if not extracted_text:
                extracted_text = trafilatura.extract(html_content)

            if not extracted_text or len(extracted_text.strip()) < 80:
                raise JobDescriptionScraperError(
                    f"Unable to extract job text from {stripped_source}. The career page may require JavaScript."
                )

            return JobDescription(source=stripped_source, raw_text=extracted_text)

        except Exception as e:
            if isinstance(e, JobDescriptionScraperError):
                raise
            raise JobDescriptionScraperError(f"Error scraping job posting: {e}") from e

    def _extract_json_ld(self, html_content: str, source_url: str) -> JobDescription | None:
        """Extracts job posting from Schema.org JobPosting JSON-LD script tags."""
        script_matches = re.findall(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html_content,
            re.DOTALL | re.IGNORECASE,
        )

        for raw_json in script_matches:
            try:
                data = json.loads(raw_json.strip())
                # Normalize single object or graph array
                candidates = data if isinstance(data, list) else [data]
                if isinstance(data, dict) and "@graph" in data:
                    candidates = data["@graph"]

                for item in candidates:
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "JobPosting":
                        title = str(item.get("title", ""))
                        company = ""
                        hiring_org = item.get("hiringOrganization")
                        if isinstance(hiring_org, dict):
                            company = str(hiring_org.get("name", ""))

                        desc_raw = html.unescape(str(item.get("description", "")))
                        # Convert HTML description to clean readable text
                        clean_desc = re.sub(r"<[^>]+>", " ", desc_raw)
                        clean_desc = "\n".join(
                            line.strip() for line in clean_desc.splitlines() if line.strip()
                        )

                        if len(clean_desc) >= 80:
                            combined_text = f"Job Title: {title}\nCompany: {company}\n\nJob Description:\n{clean_desc}"
                            return JobDescription(
                                source=source_url,
                                title=title,
                                company=company,
                                raw_text=combined_text,
                            )
            except Exception:
                continue

        return None
