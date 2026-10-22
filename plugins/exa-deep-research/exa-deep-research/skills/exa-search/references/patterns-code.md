<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# Query Patterns: Code and Documentation

Always include programming language and framework/library in your query.

```
// API usage
exa_search { "query": "Stripe API create subscription Node.js code example", "numResults": 5 }

// Error resolution
exa_search { "query": "React hydration mismatch server client explanation fix", "numResults": 10 }

// GitHub implementations
exa_search { "query": "GitHub repository [library] example project open source", "numResults": 10 }
```

Use `exa_fetch` to read official docs when you know the URL.
