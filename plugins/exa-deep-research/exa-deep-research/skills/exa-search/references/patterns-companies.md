<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# Query Patterns: Companies

Use `category:company` for structured company data (funding, headcount, description).

```
// By category
exa_search { "query": "category:company AI infrastructure startups San Francisco", "numResults": 10 }

// By stage
exa_search { "query": "category:company Series B fintech payments", "numResults": 10 }

// Similar to known company
exa_search { "query": "category:company companies like Stripe", "numResults": 8 }
```

For competitive intelligence, layer multiple angles:
```
exa_search { "query": "category:company companies like [target]", "numResults": 10 }
exa_search { "query": "category:company [category] software tools", "numResults": 15 }
exa_search { "query": "[category] startup launch funding announcement recently", "numResults": 15 }
```

For funding/investors:
```
exa_search { "query": "[company] funding round raised investors", "numResults": 5 }
exa_search { "query": "category:company [company]", "numResults": 5 }
```
