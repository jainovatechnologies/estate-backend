import logging
import re
from typing import List, Dict, Any, Optional
from app.database import DatabaseManager
from app.models.chat import Citation

logger = logging.getLogger(__name__)


class RetrievedContext:
    def __init__(self, chunk_id: str, source_url: str, domain: str, title: str, content: str, score: float):
        self.chunk_id = chunk_id
        self.source_url = source_url
        self.domain = domain
        self.title = title
        self.content = content
        self.score = score

    def to_citation(self) -> Citation:
        snippet = self.content.split("\n")[0][:180] + ("..." if len(self.content) > 180 else "")
        return Citation(
            title=self.title or "Verified Source",
            domain=self.domain,
            url=self.source_url,
            excerpt=snippet
        )


class RetrievalService:
    @classmethod
    async def retrieve_relevant_chunks(cls, query: str, top_k: int = 5) -> List[RetrievedContext]:
        if not query or not query.strip():
            return []

        db = DatabaseManager.get_database()
        clean_query = query.strip()
        results: List[RetrievedContext] = []
        seen_chunks = set()

        try:
            cursor = db.content_chunks.find(
                {"$text": {"$search": clean_query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(top_k)

            async for doc in cursor:
                c_id = doc.get("chunk_id", str(doc.get("_id")))
                if c_id not in seen_chunks:
                    seen_chunks.add(c_id)
                    results.append(RetrievedContext(
                        chunk_id=c_id,
                        source_url=doc.get("source_url", ""),
                        domain=doc.get("domain", ""),
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        score=float(doc.get("score", 1.0))
                    ))
        except Exception as e:
            logger.warning(f"Full-text search error: {e}. Executing regex token fallback.")

        if len(results) < top_k:
            stopwords = {"what", "which", "where", "when", "about", "there", "their", "information", "available", "does", "have", "with", "from", "both", "show", "tell"}
            tokens = [t.lower() for t in re.findall(r"\b[A-Za-z0-9\$\-]{3,}\b", clean_query) if t.lower() not in stopwords]

            if tokens:
                regex_pattern = "|".join([re.escape(t) for t in tokens])
                try:
                    fallback_cursor = db.content_chunks.find({
                        "content": {"$regex": regex_pattern, "$options": "i"}
                    }).limit(top_k * 2)

                    async for doc in fallback_cursor:
                        c_id = doc.get("chunk_id", str(doc.get("_id")))
                        if c_id not in seen_chunks:
                            seen_chunks.add(c_id)
                            content_lower = doc.get("content", "").lower()
                            match_count = sum(1 for t in tokens if t in content_lower)
                            results.append(RetrievedContext(
                                chunk_id=c_id,
                                source_url=doc.get("source_url", ""),
                                domain=doc.get("domain", ""),
                                title=doc.get("title", ""),
                                content=doc.get("content", ""),
                                score=float(match_count)
                            ))
                            if len(results) >= top_k:
                                break
                except Exception as ex:
                    logger.error(f"Keyword search fallback error: {ex}")

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    @classmethod
    def format_context_for_prompt(cls, chunks: List[RetrievedContext]) -> str:
        if not chunks:
            return "NO RETRIEVED CONTEXT AVAILABLE."

        formatted_parts = []
        for i, c in enumerate(chunks, 1):
            formatted_parts.append(
                f"--- SOURCE [{i}] ---\n"
                f"Title: {c.title}\n"
                f"URL: {c.source_url}\n"
                f"Domain: {c.domain}\n"
                f"Content:\n{c.content}\n"
            )
        return "\n".join(formatted_parts)

    @classmethod
    def deduplicate_citations(cls, chunks: List[RetrievedContext]) -> List[Citation]:
        citations: List[Citation] = []
        seen_urls = set()

        for c in chunks:
            if c.source_url and c.source_url not in seen_urls:
                seen_urls.add(c.source_url)
                citations.append(c.to_citation())

        return citations
