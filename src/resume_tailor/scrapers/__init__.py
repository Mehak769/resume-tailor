"""Job description scraping package."""

from resume_tailor.scrapers.base import BaseJDScraper
from resume_tailor.scrapers.web_scraper import WebJDScraper

__all__ = ["BaseJDScraper", "WebJDScraper"]
