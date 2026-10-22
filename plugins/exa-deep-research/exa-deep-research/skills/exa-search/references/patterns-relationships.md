<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# Query Patterns: Hidden Relationships

Finding connections that aren't explicitly listed anywhere. Direct queries ("X clients") return articles about them, not actual connections. Use indirect signals instead.

**Start with the subject's own platforms:**
```
exa_search { "query": "[subject] official website blog podcast", "numResults": 5 }
exa_search { "query": "[subject] conversation interview testimonial guest", "numResults": 8 }
exa_fetch { "urls": ["https://subject-website.com/blog", "https://subject-website.com/about"] }
```

**For B2B (company -> customers):**
```
exa_search { "query": "[company] case study customer success story", "numResults": 5 }
exa_fetch { "urls": ["https://company.com/customers", "https://company.com/case-studies"] }
```

**Indirect signal searches:**
```
// Testimonials
exa_search { "query": "personal blog [subject] changed my life testimonial", "numResults": 15 }

// Duration markers (high confidence -- people don't fabricate decades)
exa_search { "query": "[subject] years decades longtime worked with known since", "numResults": 10 }

// Terminology detection: find insider terms, then search for people using them
exa_search { "query": "[subject] method terminology concepts framework", "numResults": 5 }
exa_search { "query": "[unique term 1] [unique term 2] personal story", "numResults": 10 }
```
