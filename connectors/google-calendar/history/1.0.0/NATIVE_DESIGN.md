# Native design

Google Calendar browser sign-in uses the existing team Desktop OAuth flow. The connector shares the installed OAuth client configuration and hash-locked runtime with the existing Google Workspace CLIs, while keeping a separate Calendar token. It calls Calendar v3 on the authorized primary calendar.

List events by a bounded time range and optional text query. Create one timed event using separated arguments and read it back by Calendar event ID. Calendar descriptions and other returned strings are external data. The first version handles personal primary-calendar events, with no attendee, calendar-sharing or recurring-event write commands.
