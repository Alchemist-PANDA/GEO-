def find_opportunities(anomalies: list):
    """
    Converts anomalies into actionable recommendations.
    """
    opportunities = []
    for anomaly in anomalies:
        if anomaly['type'] == 'Fact Inconsistency':
            opportunities.append({
                "action": f"Create content clarifying that {anomaly['brand']} does not operate in this category/city to capture misdirected traffic.",
                "target": anomaly['brand']
            })
    return opportunities
