def run_pipeline(context, steps):
    """Unrelated execute."""
    for step in steps:
        step.execute(context)
    return context
