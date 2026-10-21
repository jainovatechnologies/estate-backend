import pytest
from app.services.ingestion_service import (
    is_url_permitted,
    normalize_url,
    clean_html_to_text,
    chunk_text
)


def test_domain_allowlist():
    assert is_url_permitted("https://darglobal.co.uk")
    assert is_url_permitted("https://darglobal.co.uk/about")
    assert is_url_permitted("https://wasalt.sa/en")
    assert is_url_permitted("https://cdn.wasalt.sa/sitemap/static_sitemap_en_sa.xml.gz")

    assert not is_url_permitted("https://malicious-domain.com")
    assert not is_url_permitted("http://localhost:8000")
    assert not is_url_permitted("http://169.254.169.254/latest/meta-data")
    assert not is_url_permitted("ftp://darglobal.co.uk")
    assert not is_url_permitted("file:///etc/passwd")


def test_url_normalization():
    assert normalize_url("https://darglobal.co.uk/about/") == "https://darglobal.co.uk/about"
    assert normalize_url("https://DarGlobal.co.uk/press") == "https://darglobal.co.uk/press"
    assert normalize_url("https://wasalt.sa/") == "https://wasalt.sa/"


def test_clean_html_to_text():
    html_sample = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Dar Global Luxury Portfolio</title>
            <meta name="description" content="Premier luxury developer in UAE and London.">
            <style>body { color: red; }</style>
            <script>console.log("tracker");</script>
        </head>
        <body>
            <header><nav><a href="/">Home</a></nav></header>
            <main>
                <h1>Trump International Hotel Dubai</h1>
                <p>Located in the heart of the city with luxury branded residences.</p>
            </main>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    title, text, desc = clean_html_to_text(html_sample)
    assert title == "Dar Global Luxury Portfolio"
    assert desc == "Premier luxury developer in UAE and London."
    assert "Trump International Hotel Dubai" in text
    assert "Located in the heart of the city" in text
    assert "console.log" not in text
    assert "color: red" not in text
    assert "Copyright 2026" not in text


def test_chunking_with_overlap():
    sample_text = (
        "Dar Global is an international real estate developer.\n"
        "It is listed on the London Stock Exchange under ticker DAR.\n"
        "The portfolio gross development value is 23 billion dollars.\n"
        "Major developments include AIDA clifftop in Oman.\n"
        "Another landmark project is Trump International Simaisma in Qatar.\n"
        "Brand partnerships include Fendi Casa, Pagani, and Aston Martin."
    )
    chunks = chunk_text(sample_text, chunk_size=150, chunk_overlap=40)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) > 0
