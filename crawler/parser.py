from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup


SOCIAL_DOMAINS = [
    "facebook.com",
    "linkedin.com",
    "github.com",
    "gitlab.com",
    "reddit.com",
    "x.com",
    "instagram.com",
    "youtube.com",
]


@dataclass
class ParsedPage:
    title: str
    description: str
    keywords: str
    text: str

    images: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    contact_links: list[str] = field(default_factory=list)
    privacy_links: list[str] = field(default_factory=list)
    social_links: list[str] = field(default_factory=list)


class PageParser:

    @staticmethod
    def parse(html: str, base_url: str) -> ParsedPage:
        """Extract useful information from a HTML page."""

        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
        ]):
            tag.decompose()

        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)

        description = ""
        description_tag = soup.find(
            "meta",
            attrs={"name": "description"},
        )
        if description_tag:
            description = description_tag.get("content", "")

        keywords = ""
        keywords_tag = soup.find(
            "meta",
            attrs={"name": "keywords"},
        )
        if keywords_tag:
            keywords = keywords_tag.get("content", "")

        text = soup.get_text(" ", strip=True)

        images = []
        emails = []
        contact_links = []
        privacy_links = []
        social_links = []

        # Images
        for img in soup.find_all("img", src=True):
            images.append(
                urljoin(base_url, img["src"])
            )

        # Links
        for link in soup.find_all("a", href=True):

            href = urljoin(base_url, link["href"])
            link_text = link.get_text(strip=True).lower()

            # Email links
            if href.startswith("mailto:"):
                emails.append(
                    href.replace("mailto:", "")
                )
                continue

            # Contact page
            if "contact" in link_text:
                contact_links.append(href)

            # Privacy policy
            if "privacy" in link_text:
                privacy_links.append(href)

            # Social links
            if any(site in href for site in SOCIAL_DOMAINS):
                social_links.append(href)

        return ParsedPage(
            title=title,
            description=description,
            keywords=keywords,
            text=text,
            images=list(dict.fromkeys(images)),
            emails=list(dict.fromkeys(emails)),
            contact_links=list(dict.fromkeys(contact_links)),
            privacy_links=list(dict.fromkeys(privacy_links)),
            social_links=list(dict.fromkeys(social_links)),
        )