<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# Query Patterns: Publications/Research Papers

Use `category:publication` for Exa's publication index.

```
// By topic
exa_search { "query": "category:publication sparse attention mechanisms for long context transformers", "numResults": 12 }

// Survey/review papers
exa_search { "query": "category:publication [topic] comprehensive survey review", "numResults": 10 }

// By author
exa_search { "query": "category:publication [author name] [topic]", "numResults": 5 }

// By recency (encode time in query)
exa_search { "query": "category:publication large language model advances 2025 2026", "numResults": 15 }
```

To find seminal papers: search for survey papers first, then deep-read them to extract foundational references.
