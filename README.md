# PawPal+

PawPal+ is a Python and Streamlit pet-care planner. It handles multiple pets, builds daily plans, prioritizes work when time is limited, warns about overlaps, and creates daily or weekly recurrences.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run `python main.py` for the CLI demo or `pytest -q` for automated checks.

## Design

- `Owner` manages pets and collects household tasks.
- `Pet` owns its care tasks.
- `Task` validates data, tracks completion, and produces recurrences.
- `Scheduler` sorts, filters, detects conflicts, selects plans, and completes tasks.

The draft and final Mermaid diagrams are in `diagrams/`.

## Sample output

```text
Today's Schedule for Jordan
07:30 | Luna   | Breakfast        | 10 min | high
08:00 | Mochi  | Morning walk     | 30 min | high
08:15 | Luna   | Play session     | 20 min | medium
09:00 | Mochi  | Medication       |  5 min | high

Conflict: Morning walk overlaps Play session.
Recurrence: completed Morning walk; next due tomorrow
```

## Testing

```text
$ pytest -q
...........                                                              [100%]
11 passed
```

Tests cover validation, pets and tasks, sorting, combined filters, daily/weekly recurrence, overlapping versus adjacent tasks, and time-limited priority selection.

## Smarter scheduling

| Feature | Method(s) | Behavior |
|---|---|---|
| Sorting | `sort_by_time` | Date/time, then priority and pet |
| Filtering | `filter_tasks`, `build_daily_plan` | Pet/status/date filters and priority-based time limit |
| Conflicts | `detect_conflicts` | Reports interval overlaps but allows adjacent tasks |
| Recurrence | `next_occurrence`, `mark_task_complete` | Adds the next daily or weekly occurrence |

## Demo walkthrough

1. Open the app to see sample household data.
2. Add pets in the sidebar and tasks with date, time, duration, priority, and frequency.
3. Choose a date in **Daily plan** and optionally limit available minutes.
4. Review the chronological plan and conflict warnings.
5. Filter **All tasks** and mark one complete; recurring work gets its next date automatically.
