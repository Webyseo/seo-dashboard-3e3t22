import pandas as pd
import logging

# Configure logging for metrics verification
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metrics_hardener")

def get_visibility_stats(visibility_series: pd.Series):
    """
    Standardizes visibility calculation and formatting.
    Target range: 0-100 (percentage points).
    
    Returns:
        dict: {
            'current': float,
            'prev': float | None,
            'delta_pp': float | None,
            'formatted_value': str,
            'formatted_delta': str | None
        }
    """
    if visibility_series.empty:
        return {
            'current': 0.0, 'prev': None, 'delta_pp': None,
            'formatted_value': "0.0%", 'formatted_delta': None
        }

    # 1. HARDENING: Anti-scale guards
    # We work with 0-100 scale.
    series = visibility_series.copy().astype(float)
    
    # Auto-correction for common errors (e.g. multiplied by 100 twice)
    last_val = series.iloc[-1]
    if last_val > 1000:
        logger.warning(f"Extreme visibility value detected ({last_val}). Applying anti-scale correction (/100).")
        series = series / 100.0
    
    # Double-check range and clamp as a safety measure (but log it)
    def clamp_and_log(val):
        if val > 100.0:
            logger.error(f"Visibility value {val} exceeds 100%. Clamping to 100.")
            return 100.0
        if val < 0.0:
            logger.error(f"Visibility value {val} is negative. Clamping to 0.")
            return 0.0
        return val

    series = series.apply(clamp_and_log)

    # 2. CALCULATION
    current = series.iloc[-1]
    prev = series.iloc[-2] if len(series) > 1 else None
    delta_pp = current - prev if prev is not None else None

    # 3. FORMATTING
    formatted_value = f"{current:.1f}%"
    formatted_delta = f"{delta_pp:+.1f} pp" if delta_pp is not None else None

    return {
        'current': current,
        'prev': prev,
        'delta_pp': delta_pp,
        'formatted_value': formatted_value,
        'formatted_delta': formatted_delta,
        'series': series # Return corrected series for chart consistency
    }
