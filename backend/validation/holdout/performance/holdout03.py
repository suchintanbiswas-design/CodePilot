class Task:
    def execute(self):
        pass

def run_tasks(tasks):
    """Unrelated .execute() calls."""
    for task in tasks:
        task.execute()  # Not a DB cursor execute
