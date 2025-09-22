import json
from pathlib import Path
import argparse

DATA = Path("tasks.json")

def load_tasks():
    if DATA.exists():
        return json.loads(DATA.read_text())
    return []

def save_tasks(tasks):
    DATA.write_text(json.dumps(tasks, indent=2))

def add_task(title):
    tasks = load_tasks()
    tasks.append({"id": len(tasks) + 1, "title": title, "done": False})
    save_tasks(tasks)
    print(f"Added: {title}")

def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("No tasks yet.")
        return
    for t in tasks:
        status = "✓" if t["done"] else "•"
        print(f"{t['id']:>2} {status} {t['title']}")

def done_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            save_tasks(tasks)
            print(f"Marked done: {t['title']}")
            return
    print("Task not found.")

def delete_task(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    for i, t in enumerate(tasks, start=1):
        t["id"] = i
    save_tasks(tasks)
    print(f"Deleted task {task_id}")

def main():
    parser = argparse.ArgumentParser(description="Simple CLI To-Do")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title", nargs="+", help="Task title")

    sub.add_parser("list", help="List tasks")

    p_done = sub.add_parser("done", help="Mark a task as done")
    p_done.add_argument("id", type=int)

    p_del = sub.add_parser("del", help="Delete a task")
    p_del.add_argument("id", type=int)

    args = parser.parse_args()
    if args.cmd == "add":
        add_task(" ".join(args.title))
    elif args.cmd == "list":
        list_tasks()
    elif args.cmd == "done":
        done_task(args.id)
    elif args.cmd == "del":
        delete_task(args.id)

if __name__ == "__main__":
    main()