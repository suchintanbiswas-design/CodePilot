def load_user_details(cursor, users):
    """N+1 query pattern inside a for loop."""
    details = []
    for user in users:
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user.id,))
        profile = cursor.fetchone()
        details.append({"user": user, "profile": profile})
    return details
