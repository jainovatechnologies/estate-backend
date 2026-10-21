import pytest
from app.services.retrieval_service import RetrievalService, RetrievedContext


def test_deduplicate_citations():
    chunks = [
        RetrievedContext(
            chunk_id="c1",
            source_url="https://darglobal.co.uk/about",
            domain="darglobal.co.uk",
            title="About Dar Global",
            content="London-listed luxury real estate developer.",
            score=5.0
        ),
        RetrievedContext(
            chunk_id="c2",
            source_url="https://darglobal.co.uk/about",
            domain="darglobal.co.uk",
            title="About Dar Global Part 2",
            content="Portfolio gross development value reaches $23 billion.",
            score=4.0
        ),
        RetrievedContext(
            chunk_id="c3",
            source_url="https://wasalt.sa/en/s/wasalt-business",
            domain="wasalt.sa",
            title="Wasalt Business Overview",
            content="Saudi Arabian digital property platform.",
            score=3.5
        )
    ]

    citations = RetrievalService.deduplicate_citations(chunks)
    assert len(citations) == 2
    urls = [c.url for c in citations]
    assert "https://darglobal.co.uk/about" in urls
    assert "https://wasalt.sa/en/s/wasalt-business" in urls


def test_format_context_for_prompt():
    chunks = [
        RetrievedContext(
            chunk_id="c1",
            source_url="https://darglobal.co.uk/landing-page/aida",
            domain="darglobal.co.uk",
            title="AIDA Oman",
            content="Clifftop community 130 meters above sea level.",
            score=5.0
        )
    ]
    prompt_str = RetrievalService.format_context_for_prompt(chunks)
    assert "AIDA Oman" in prompt_str
    assert "https://darglobal.co.uk/landing-page/aida" in prompt_str
    assert "Clifftop community" in prompt_str


def test_format_empty_context():
    prompt_str = RetrievalService.format_context_for_prompt([])
    assert "NO RETRIEVED CONTEXT" in prompt_str
