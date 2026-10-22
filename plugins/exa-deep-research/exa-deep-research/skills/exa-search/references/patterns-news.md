<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# Query Patterns: News and Recent Events

```
exa_search { "query": "category:news [topic] announcement", "numResults": 15 }
exa_search { "query": "[topic] news update latest development [month year]", "numResults": 15 }
```

For reactions/sentiment on recent events, search across platforms:
```
exa_search { "query": "[event] reaction analysis commentary", "numResults": 12 }
exa_search { "query": "[event] criticism concerns issues bugs", "numResults": 15 }
```
