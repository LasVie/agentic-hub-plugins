<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# Query Patterns: People

Use `category:people` for LinkedIn-weighted results. For discovery queries, be specific -- vague queries like `"category:people researcher founder CEO startup"` will match many irrelevant LinkedIn profiles. Include specific companies, timeframes, or roles to narrow results.

```
// By company + role
exa_search { "query": "category:people engineer at OpenAI", "numResults": 10 }
exa_search { "query": "category:people VP director at Cursor", "numResults": 10 }

// By role + location
exa_search { "query": "category:people Head of Growth B2B SaaS startup San Francisco", "numResults": 12 }

// Specific person
exa_search { "query": "category:people Jane Smith Anthropic machine learning", "numResults": 5 }
```

For comprehensive company coverage, search by department and seniority in parallel:
```
exa_search { "query": "category:people engineering at Acme", "numResults": 10 }
exa_search { "query": "category:people product design at Acme", "numResults": 10 }
exa_search { "query": "category:people sales marketing at Acme", "numResults": 10 }
```

Supplement with non-LinkedIn sources:
```
exa_search { "query": "Acme team page employees about us", "numResults": 5 }
exa_search { "query": "joined Acme recently hired new role announcement", "numResults": 5 }
```

Deduplicate by LinkedIn URL (canonical) or name + current company (fallback).
