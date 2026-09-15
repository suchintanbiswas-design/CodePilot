def calculate_triple_interactions(particles):
    """Triple-nested computation O(N^3)."""
    energy = 0.0
    for p1 in particles:
        for p2 in particles:
            for p3 in particles:
                if p1 != p2 and p2 != p3 and p1 != p3:
                    energy += (p1.mass * p2.mass * p3.mass) / 100.0
    return energy
