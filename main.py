"""Command-line demonstration of the PawPal+ scheduling workflow."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo() -> tuple[Owner, Scheduler]:
    """Create a two-pet household with representative care tasks."""
    today = date.today()
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "08:00", 30, "high", today, "daily"))
    luna.add_task(Task("Breakfast", "07:30", 10, "high", today, "daily"))
    mochi.add_task(Task("Medication", "09:00", 5, "high", today))
    luna.add_task(Task("Play session", "08:15", 20, "medium", today))
    luna.add_task(Task("Vet call", "09:00", 15, "medium", today))
    return owner, Scheduler(owner)


def main() -> None:
    """Print the daily plan, filters, conflicts, and recurrence behavior."""
    owner, scheduler = build_demo()
    today = date.today()

    print(f"Today's Schedule for {owner.name}")
    print("-" * 58)
    for pet, task in scheduler.build_daily_plan(today):
        print(
            f"{task.time} | {pet.name:<6} | {task.description:<16} | "
            f"{task.duration_minutes:>2} min | {task.priority}"
        )

    print("\nPending tasks for Mochi:")
    for _, task in scheduler.filter_tasks(pet_name="Mochi", completed=False):
        print(f"- {task.time} {task.description}")

    print("\nConflict warnings:")
    for warning in scheduler.detect_conflicts(today):
        print(f"- {warning}")

    daily_task = owner.find_pet("Mochi").tasks[0]
    next_task = scheduler.mark_task_complete("Mochi", daily_task)
    print(
        "\nRecurrence: "
        f"completed {daily_task.description}; next due {next_task.due_date}"
    )


if __name__ == "__main__":
    main()
