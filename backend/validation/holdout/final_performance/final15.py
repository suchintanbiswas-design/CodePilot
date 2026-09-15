def audit_user_permissions(db, departments):
    """N^2 + N+1 database queries."""
    for dept in departments:
        for team in dept.teams:
            db.execute("SELECT * FROM permissions WHERE team_id=?", (team.id,))
            perms = db.fetchall()
            for p in perms:
                # O(N^3) + N+1 queries
                db.execute("INSERT INTO audit_log (perm_id) VALUES (?)", (p.id,))
