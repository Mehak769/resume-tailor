import pytest

from resume_tailor.core.exceptions import JobDescriptionScraperError
from resume_tailor.scrapers.web_scraper import WebJDScraper


def test_scraper_raw_text():
    scraper = WebJDScraper()
    result = scraper.scrape("Looking for a Python engineer with 5 years experience.")
    assert result.source == "raw_text"
    assert "Python engineer" in result.raw_text


def test_scraper_blocked_host():
    scraper = WebJDScraper()
    with pytest.raises(JobDescriptionScraperError, match="Invalid or blocked target hostname"):
        scraper.scrape("http://localhost/job")
