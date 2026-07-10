# To do list (will be updated at every new task)

**General instructions**:

- If something is unclear, aks me for clarification!
- Whenever you have some suggestions, tell them to me!

## Programming language

I'll use Python as programming language. 

## Internal Event Model

Let's start by defining the event model. Write the first definition of a **class** containing the following attributes of the event:

- `id`
- `summary`
- `start_date`
- `start_time`
- `end_date`
- `end_time`
- `location`
- `description`

If you think that there's more, tell it to me.

**Status:** Implemented in `src/calendar_conversion/event.py`, with automated
tests. Timezone and all-day-event support are proposed as future additions and
need an explicit policy before implementation.

Add to the class the support for the timezone and all-day-event:

- timezone: Europe/Rome
- all-day-event: must be guided by a flag:

```
if(all-day-event) 
  then { set(start_date) and set(end_date); do not set times }
else 
  { set dates and times }
```

For a one-day all-day event, `end_date` is equal to `start_date`.

**Status:** Implemented. Both event types use `start_date` and `end_date`.
`all_day` determines whether the time fields must be omitted or supplied.
Timed events use `Europe/Rome` through Python's timezone-aware `zoneinfo`
support. The Python model uses lowercase `snake_case` attributes; readers and
generators will map external uppercase names at the format boundary.
