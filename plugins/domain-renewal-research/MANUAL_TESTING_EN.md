# English prompts for the unchanged Chinese package 1.0.0

Import the existing `test-packages/domain-renewal-research-1.0.0-native.zip`, enable **域名续费比价**, and start a new conversation. No separate English port or API key is required for these flows. The tools are language-neutral and the Skill honors an explicit response-language request. Bundled labels/help and raw local errors remain Chinese. An English host UI has not been independently tested.

Native SHA-256: `af6ef3967d0dcb88739abf6bf0df5e88e4eb39f98477b536386d0e93159b0d26`.

Pass arguments directly, without an `arguments` wrapper. Expand actual tool calls; an assistant's claim alone does not prove execution. These optional English checks do not invalidate the user's Chinese confirmation.

## 1. Registrar sources

```text
Reply in English throughout this conversation. Call domain_get_registrars and summarize the actual returned registrars, sources and health states. Use the plugin tool, not web search or memory. If the tool is unavailable, say so.
```

Expected: actual tool call and English summary grounded in the response. Keep dates and partial-coverage warnings.

## 2. Renewal budget

```text
Reply in English. Call domain_search_prices with these exact top-level arguments:
{"q":".com,.org,.dev","sort":"renewal","maxRenewalCents":1500,"limit":3}
List only actual returned offers: TLD, registrar, first-year registration cost, annual renewal cost, source retrieval time and comparison link. Convert USD cents to USD. Preserve partial coverage, stale-data and tax qualifications. Do not check any domain name or invent missing offers.
```

Expected: at most three actual offers, registration and renewal separated; honest empty/partial/error results are acceptable.

## 3. Three-year estimate

```text
Reply in English. From the actual registrar results above, choose a supported registrar and TLD and call domain_estimate_cost with years=3 and other required arguments from its schema. Explain returned line items and source dates. This is a new-registration estimate, not an existing domain's renewal invoice or a future price guarantee. Unknown amounts must remain unknown.
```

Expected: actual call with accurate line items and qualifications.

## 4. Cached availability

```text
Reply in English. Call domain_check_availability_batch with exactly:
{"name":"example","tlds":"com,org","cachedOnly":true}
Read cache only. Do not initiate a live check, refresh or retry. Distinguish evidence from unknown status; missing cache does not prove availability or registration.
```

Expected: cached-only call; unknown values remain unknown.

## 5. Exact invalid input

```text
Test local argument rejection only. Call domain_check_availability once with these exact arguments:
{"name":"中文测试","tld":"com"}
Do not substitute another name, transliterate, retry or make a live availability check. Show the exact error code and original Chinese error message, then explain it in English. If you cannot send those exact arguments, stop and say so instead of changing them.
```

Expected: `INVALID_ARGUMENTS` and Chinese validation message before network access. Inspect actual arguments and raw result. A changed name is an invalid test, not a plugin pass or failure.

## 6. Naming form

```text
Reply in English. Call domain_open_name_finder and show the actual returned form link and host-support explanation. Do not check names. Do not claim the form was opened or rendered unless that actually happened.
```

Expected: actual public form link and honest embedded-app support explanation.
