def risk_band(avg_latency):
    if avg_latency < 3:
        return "low"
    elif avg_latency < 6:
        return "moderate"
    return "elevated"
