"""Automated tests for PawPal+ domain and scheduling behavior."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


@pytest.fixture
def household():
    """Return a reusable household and scheduler."""
    owner = Owner("Miguel")
    dog = Pet("Milo", "dog")
    cat = Pet("Nala", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner, dog, cat, Scheduler(owner)


def test_mark_complete_changes_status():
    task = Task("Walk", "08:00", 20)
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Milo", "dog")
    pet.add_task(Task("Walk", "08:00", 20))
    assert len(pet.tasks) == 1


def test_owner_rejects_duplicate_pet_names():
    owner = Owner("Miguel")
    owner.add_pet(Pet("Milo", "dog"))
    with pytest.raises(ValueError, match="already exists"):
        owner.add_pet(Pet("milo", "cat"))


def test_sorting_is_chronological_across_pets(household):
    _, dog, cat, scheduler = household
    dog.add_task(Task("Walk", "09:00", 20))
    cat.add_task(Task("Feed", "07:30", 10))
    assert [task.description for _, task in scheduler.sort_by_time()] == [
        "Feed",
        "Walk",
    ]


def test_filtering_by_pet_and_status(household):
    _, dog, cat, scheduler = household
    dog.add_task(Task("Walk", "09:00", 20))
    completed = Task("Feed", "07:30", 10, completed=True)
    cat.add_task(completed)
    pending = scheduler.filter_tasks(pet_name="Milo", completed=False)
    assert [(pet.name, task.description) for pet, task in pending] == [
        ("Milo", "Walk")
    ]


def test_daily_recurrence_creates_tomorrows_task(household):
    _, dog, _, scheduler = household
    today = date.today()
    task = Task("Walk", "09:00", 20, due_date=today, frequency="daily")
    dog.add_task(task)
    next_task = scheduler.mark_task_complete("Milo", task)
    assert task.completed is True
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task in dog.tasks


def test_weekly_recurrence_advances_seven_days(household):
    _, dog, _, scheduler = household
    today = date.today()
    task = Task("Groom", "10:00", 30, due_date=today, frequency="weekly")
    dog.add_task(task)
    assert scheduler.mark_task_complete("Milo", task).due_date == today + timedelta(
        days=7
    )


def test_conflict_detection_flags_overlapping_intervals(household):
    _, dog, cat, scheduler = household
    today = date.today()
    dog.add_task(Task("Walk", "09:00", 30, due_date=today))
    cat.add_task(Task("Medication", "09:15", 5, due_date=today))
    warnings = scheduler.detect_conflicts(today)
    assert len(warnings) == 1
    assert "overlaps" in warnings[0]


def test_adjacent_tasks_do_not_conflict(household):
    _, dog, cat, scheduler = household
    today = date.today()
    dog.add_task(Task("Walk", "09:00", 30, due_date=today))
    cat.add_task(Task("Feed", "09:30", 10, due_date=today))
    assert scheduler.detect_conflicts(today) == []


def test_available_time_prioritizes_high_priority_tasks(household):
    _, dog, cat, scheduler = household
    today = date.today()
    dog.add_task(Task("Brush", "08:00", 30, "low", today))
    cat.add_task(Task("Medication", "09:00", 10, "high", today))
    plan = scheduler.build_daily_plan(today, available_minutes=20)
    assert [task.description for _, task in plan] == ["Medication"]


def test_invalid_time_is_rejected():
    with pytest.raises(ValueError, match="HH:MM"):
        Task("Walk", "9am", 20)
