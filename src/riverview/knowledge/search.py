"""Classification-first lexical retrieval over normalized turns."""

from __future__ import annotations

from riverview.database import connect


class KnowledgeSearch:
    def search(self, query: str, *, classification: str = "operational", limit: int = 20) -> list[dict[str, object]]:
        if not query.strip() or classification not in {"public", "operational", "private", "sensitive"}:
            raise ValueError("RIV-KNW-0003: query and classification are bounded and required.")
        limit = max(1, min(limit, 50))
        with connect() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT turn_id,conversation_id,source_message_id,speaker,occurred_at,body,classification,turn_order,
                                      ts_rank(to_tsvector('simple',body), plainto_tsquery('simple',%s)) AS rank
                               FROM knowledge_turns
                               WHERE classification=%s
                                 AND to_tsvector('simple',body) @@ plainto_tsquery('simple',%s)
                               ORDER BY rank DESC,occurred_at,turn_order LIMIT %s""", (query, classification, query, limit))
            names=[item.name for item in cursor.description]
            return [dict(zip(names,row,strict=True)) for row in cursor.fetchall()]
