"""Interactive Streamlit interface for PawPal+."""

from datetime import date
import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

def sample_owner() -> Owner:
    owner = Owner("Jordan")
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    mochi.add_task(Task("Morning walk", "08:00", 30, "high", date.today(), "daily"))
    mochi.add_task(Task("Medication", "09:00", 5, "high", date.today(), "daily"))
    luna.add_task(Task("Breakfast", "07:30", 10, "high", date.today(), "daily"))
    luna.add_task(Task("Play session", "08:15", 20, "medium", date.today()))
    owner.add_pet(mochi); owner.add_pet(luna)
    return owner

if "owner" not in st.session_state:
    st.session_state.owner = sample_owner()
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
st.caption("A smart daily planner for consistent, conflict-aware pet care.")

with st.sidebar:
    st.header("Household")
    new_owner_name = st.text_input("Owner name", value=owner.name)
    if new_owner_name.strip(): owner.name = new_owner_name.strip()
    with st.form("add_pet", clear_on_submit=True):
        st.subheader("Add a pet")
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "bird", "other"])
        if st.form_submit_button("Add pet", use_container_width=True):
            try:
                owner.add_pet(Pet(pet_name, species)); st.success(f"Added {pet_name.strip()}.")
            except ValueError as error: st.error(str(error))
    st.write(f"**{len(owner.pets)} pet(s):** " + ", ".join(pet.name for pet in owner.pets))
    if st.button("Restore sample data", use_container_width=True):
        st.session_state.owner = sample_owner(); st.rerun()

add_tab, plan_tab, all_tab = st.tabs(["Add task", "Daily plan", "All tasks"])
with add_tab:
    st.subheader("Add a care task")
    if not owner.pets:
        st.info("Add a pet in the sidebar first.")
    else:
        with st.form("add_task", clear_on_submit=True):
            left, middle, right = st.columns(3)
            with left:
                selected_pet = st.selectbox("Pet", [pet.name for pet in owner.pets])
                description = st.text_input("Task", placeholder="Evening walk")
                task_date = st.date_input("Date", value=date.today())
            with middle:
                task_time = st.time_input("Start time")
                duration = st.number_input("Duration (minutes)", 1, 240, 20)
            with right:
                priority = st.selectbox("Priority", ["high", "medium", "low"])
                frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
            if st.form_submit_button("Add task", type="primary"):
                try:
                    task = Task(description, task_time.strftime("%H:%M"), int(duration), priority, task_date, frequency)
                    pet = owner.find_pet(selected_pet)
                    if pet is not None: pet.add_task(task)
                    st.success(f"Added {description.strip()} for {selected_pet}.")
                except ValueError as error: st.error(str(error))

with plan_tab:
    st.subheader("Build a daily plan")
    plan_date = st.date_input("Plan date", value=date.today(), key="plan_date")
    limit_time = st.checkbox("Limit total care time")
    available = st.slider("Available minutes", 0, 240, 60, disabled=not limit_time)
    plan = scheduler.build_daily_plan(plan_date, available if limit_time else None)
    if plan:
        st.dataframe(Scheduler.as_rows(plan), use_container_width=True, hide_index=True)
        used = sum(task.duration_minutes for _, task in plan)
        st.caption(f"Selected {len(plan)} pending task(s), using {used} minutes. With a time limit, high-priority tasks are selected first and displayed chronologically.")
    else: st.info("No pending tasks fit this plan.")
    conflicts = scheduler.detect_conflicts(plan_date)
    if conflicts: st.warning("Schedule conflicts detected:\n\n" + "\n\n".join(f"• {item}" for item in conflicts))
    else: st.success("No overlapping tasks detected for this date.")

with all_tab:
    st.subheader("Review and complete tasks")
    filter_pet = st.selectbox("Pet filter", ["All"] + [pet.name for pet in owner.pets])
    status = st.selectbox("Status", ["All", "Pending", "Done"])
    entries = scheduler.filter_tasks(pet_name=None if filter_pet == "All" else filter_pet, completed=None if status == "All" else status == "Done")
    if entries:
        st.dataframe(Scheduler.as_rows(entries), use_container_width=True, hide_index=True)
        pending = [(pet, task) for pet, task in entries if not task.completed]
        if pending:
            labels = [f"{task.due_date} · {task.time} · {pet.name} · {task.description}" for pet, task in pending]
            chosen = st.selectbox("Task to complete", range(len(pending)), format_func=lambda i: labels[i])
            if st.button("Mark complete", type="primary"):
                pet, task = pending[chosen]; next_task = scheduler.mark_task_complete(pet.name, task)
                message = "Task completed." + (f" Next occurrence added for {next_task.due_date}." if next_task else "")
                st.success(message); st.rerun()
    else: st.info("No tasks match these filters.")
