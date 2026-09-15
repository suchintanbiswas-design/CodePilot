def get_user_profiles(session, user_ids):
    """ORM N+1 query (missed by simple execute heuristic)."""
    from models import Profile
    profiles = []
    for uid in user_ids:
        # CodePilot's regex/AST doesn't flag .query().filter_by()
        p = session.query(Profile).filter_by(user_id=uid).first()
        if p:
            profiles.append(p)
    return profiles
