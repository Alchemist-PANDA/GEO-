def render_progress_bar(percentage: float, color_hex: str = "#7C3AED") -> str:
    """Render a sleek, linear progress bar using raw HTML/CSS."""
    # Ensure percentage is between 0 and 100
    pct = max(0.0, min(100.0, float(percentage)))
    
    return f"""
    <div style="width: 100%; background-color: rgba(255, 255, 255, 0.05); border-radius: 9999px; height: 8px; overflow: hidden; margin-top: 8px; border: 1px solid rgba(255, 255, 255, 0.05);">
        <div style="height: 100%; width: {pct}%; background: {color_hex}; border-radius: 9999px; transition: width 0.8s ease;"></div>
    </div>
    """
