# PawPal+ Project Reflection

## 1. System Design

My initial UML used `Owner`, `Pet`, `Task`, and `Scheduler`. Owner manages the household, Pet owns care tasks, Task represents one activity, and Scheduler works across pets. During implementation I stopped Scheduler from storing a duplicate task list. Instead, `Owner.all_tasks()` returns `(Pet, Task)` pairs, so there is one source of truth and every schedule entry retains its pet. I also added duration and a calculated end time because start time alone cannot detect overlaps.

## 2. Scheduling Logic and Tradeoffs

The scheduler considers due date, completion status, start time, duration, priority, pet, recurrence, and available minutes. It removes tasks that are not pending on the selected date. With limited time, it selects high-priority work first and then displays it chronologically.

This greedy priority rule may leave minutes unused where several shorter, lower-priority tasks could fit. That is reasonable because medication and other high-priority care should come before maximizing schedule fullness, and the behavior is easy to explain.

## 3. AI Collaboration

I used an AI coding agent to turn the class plan into stubs, implement methods, identify edge cases, connect Streamlit, and run tests. Prompts that named required behaviors and asked for test evidence were most useful. I did not accept adding database persistence or a repository class. It would add setup complexity without improving the required demonstration, so I kept Streamlit session state and verified the smaller design through the CLI, compilation, and tests.

## 4. Testing and Verification

I tested completion, adding tasks, duplicate pet prevention, ordering, filters, daily/weekly recurrence, overlaps, adjacent tasks, available-time selection, and malformed times. These matter because scheduling bugs often occur at interval boundaries or after state changes. All 11 tests pass. Next I would test tasks spanning midnight, daylight-saving changes, deleting a recurring series, and browser-session persistence.

## 5. Reflection

I am most satisfied that the CLI and app share the same domain classes instead of duplicating rules. Next I would add editing, deletion, saved user data, and a visual calendar. My key takeaway is that UML exposes ownership questions early, while tests make it safe to refine those decisions with AI assistance.
