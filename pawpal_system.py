"""Domain models and scheduling algorithms for PawPal+."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta

VALID_PRIORITIES = ("low", "medium", "high")
VALID_FREQUENCIES = ("once", "daily", "weekly")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _minutes_from_midnight(value: str) -> int:
    """Convert an HH:MM time string to minutes after midnight."""
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError("time must use 24-hour HH:MM format") from exc
    return parsed.hour * 60 + parsed.minute


@dataclass
class Task:
    """A single scheduled pet-care activity."""

    description: str
    time: str
    duration_minutes: int
    priority: str = "medium"
    due_date: date = field(default_factory=date.today)
    frequency: str = "once"
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate task data when an instance is created."""
        self.description = self.description.strip()
        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        if not self.description:
            raise ValueError("description cannot be empty")
        _minutes_from_midnight(self.time)
        if self.duration_minutes <= 0:
            raise ValueError("duration must be positive")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}")

    @property
    def end_minutes(self) -> int:
        """Return the task's end time as minutes after midnight."""
        return _minutes_from_midnight(self.time) + self.duration_minutes

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> "Task | None":
        """Return the next daily or weekly occurrence, if applicable."""
        if self.frequency == "once":
            return None
        days = 1 if self.frequency == "daily" else 7
        return replace(
            self,
            due_date=self.due_date + timedelta(days=days),
            completed=False,
        )


@dataclass
class Pet:
    """A pet and the care tasks assigned to it."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize and validate identifying information."""
        self.name = self.name.strip()
        self.species = self.species.strip().lower()
        if not self.name or not self.species:
            raise ValueError("pet name and species are required")

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)

    def tasks_for_date(self, target_date: date) -> list[Task]:
        """Return tasks scheduled for a specific date."""
        return [task for task in self.tasks if task.due_date == target_date]


@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize and validate the owner's name."""
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("owner name is required")

    def add_pet(self, pet: Pet) -> None:
        """Add a pet, rejecting duplicate names case-insensitively."""
        if self.find_pet(pet.name) is not None:
            raise ValueError(f"a pet named {pet.name} already exists")
        self.pets.append(pet)

    def find_pet(self, name: str) -> Pet | None:
        """Find a pet by name using a case-insensitive comparison."""
        normalized = name.strip().casefold()
        return next(
            (pet for pet in self.pets if pet.name.casefold() == normalized),
            None,
        )

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Retrieve, organize, and manage tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def sort_by_time(
        self,
        entries: list[tuple[Pet, Task]] | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Return task entries ordered chronologically, then by priority."""
        source = self.owner.all_tasks() if entries is None else entries
        return sorted(
            source,
            key=lambda entry: (
                entry[1].due_date,
                _minutes_from_midnight(entry[1].time),
                PRIORITY_RANK[entry[1].priority],
                entry[0].name.casefold(),
            ),
        )

    def filter_tasks(
        self,
        *,
        pet_name: str | None = None,
        completed: bool | None = None,
        target_date: date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter tasks by pet, completion status, and/or due date."""
        entries = self.owner.all_tasks()
        if pet_name:
            normalized = pet_name.strip().casefold()
            entries = [
                entry for entry in entries if entry[0].name.casefold() == normalized
            ]
        if completed is not None:
            entries = [entry for entry in entries if entry[1].completed is completed]
        if target_date is not None:
            entries = [entry for entry in entries if entry[1].due_date == target_date]
        return self.sort_by_time(entries)

    def detect_conflicts(
        self,
        target_date: date | None = None,
    ) -> list[str]:
        """Return warnings for tasks whose time intervals overlap."""
        entries = self.filter_tasks(target_date=target_date, completed=False)
        warnings: list[str] = []
        for index, (first_pet, first_task) in enumerate(entries):
            first_start = _minutes_from_midnight(first_task.time)
            for second_pet, second_task in entries[index + 1 :]:
                if second_task.due_date != first_task.due_date:
                    continue
                second_start = _minutes_from_midnight(second_task.time)
                if second_start >= first_task.end_minutes:
                    break
                if (
                    first_start < second_task.end_minutes
                    and second_start < first_task.end_minutes
                ):
                    warnings.append(
                        f"{first_task.due_date}: {first_pet.name}'s "
                        f"'{first_task.description}' overlaps {second_pet.name}'s "
                        f"'{second_task.description}'."
                    )
        return warnings

    def mark_task_complete(self, pet_name: str, task: Task) -> Task | None:
        """Complete a task and append its next recurrence when required."""
        pet = self.owner.find_pet(pet_name)
        if pet is None or task not in pet.tasks:
            raise ValueError("task does not belong to the selected pet")
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def build_daily_plan(
        self,
        target_date: date,
        available_minutes: int | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Build a chronological plan, optionally limited by available time."""
        entries = self.filter_tasks(completed=False, target_date=target_date)
        if available_minutes is None:
            return entries
        if available_minutes < 0:
            raise ValueError("available minutes cannot be negative")

        selected: list[tuple[Pet, Task]] = []
        remaining = available_minutes
        ranked = sorted(
            entries,
            key=lambda entry: (
                PRIORITY_RANK[entry[1].priority],
                _minutes_from_midnight(entry[1].time),
            ),
        )
        for entry in ranked:
            if entry[1].duration_minutes <= remaining:
                selected.append(entry)
                remaining -= entry[1].duration_minutes
        return self.sort_by_time(selected)

    @staticmethod
    def as_rows(entries: list[tuple[Pet, Task]]) -> list[dict[str, object]]:
        """Convert task entries into display-friendly dictionaries."""
        return [
            {
                "Date": task.due_date.isoformat(),
                "Time": task.time,
                "Pet": pet.name,
                "Task": task.description,
                "Minutes": task.duration_minutes,
                "Priority": task.priority.title(),
                "Frequency": task.frequency.title(),
                "Status": "Done" if task.completed else "Pending",
            }
            for pet, task in entries
        ]
