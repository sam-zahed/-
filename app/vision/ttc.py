# Simple TTC estimation example using distance and relative speed.
def estimate_ttc(distance_m: float, relative_speed_m_s: float) -> float:
    """Return TTC in seconds. If relative speed <= 0, returns inf."""
    if relative_speed_m_s <= 0:
        return float('inf')
    return distance_m / relative_speed_m_s
