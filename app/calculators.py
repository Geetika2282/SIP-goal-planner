"""
SIP (Systematic Investment Plan) financial calculators.
Each function is exposed to the LLM as a tool via the @tool decorator.
Docstrings ARE the tool description the model sees - keep them precise.
"""

import math
from langchain_core.tools import tool


@tool
def calculate_sip_future_value(monthly_investment: float, annual_rate_percent: float, years: float) -> dict:
    """
    Calculate the future value of a monthly SIP investment using compound growth.

    Use this when the user gives a monthly investment amount, an expected annual
    return rate, and a duration, and wants to know the maturity value.

    Args:
        monthly_investment: Amount invested every month (in currency units, e.g. INR).
        annual_rate_percent: Expected annual return, as a percentage (e.g. 12 for 12%).
        years: Investment duration in years.

    Returns:
        dict with future_value, total_invested, and total_gain.
    """
    monthly_rate = (annual_rate_percent / 100) / 12
    months = int(round(years * 12))

    if monthly_rate == 0:
        future_value = monthly_investment * months
    else:
        future_value = monthly_investment * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        ) * (1 + monthly_rate)

    total_invested = monthly_investment * months
    return {
        "future_value": round(future_value, 2),
        "total_invested": round(total_invested, 2),
        "total_gain": round(future_value - total_invested, 2),
        "months": months,
    }


@tool
def calculate_required_sip(target_amount: float, annual_rate_percent: float, years: float) -> dict:
    """
    Reverse-solve the monthly SIP amount required to reach a target corpus.

    Use this when the user gives a target amount and duration and wants to know
    how much they need to invest monthly to reach it.

    Args:
        target_amount: The financial goal / target maturity value.
        annual_rate_percent: Expected annual return, as a percentage (e.g. 12 for 12%).
        years: Investment duration in years.

    Returns:
        dict with required_monthly_sip and total_invested_over_period.
    """
    monthly_rate = (annual_rate_percent / 100) / 12
    months = int(round(years * 12))

    if monthly_rate == 0:
        required_sip = target_amount / months
    else:
        factor = ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
        required_sip = target_amount / factor

    return {
        "required_monthly_sip": round(required_sip, 2),
        "total_invested_over_period": round(required_sip * months, 2),
        "months": months,
    }


@tool
def calculate_required_duration(monthly_investment: float, annual_rate_percent: float, target_amount: float) -> dict:
    """
    Estimate how many months/years of SIP investing are needed to hit a target amount,
    given a fixed monthly investment and expected return.

    Use this when the user gives a monthly investment amount and a target, and wants
    to know how long it will take.

    Args:
        monthly_investment: Amount invested every month.
        annual_rate_percent: Expected annual return, as a percentage.
        target_amount: The financial goal / target maturity value.

    Returns:
        dict with required_months and required_years. If the goal is unreachable
        (e.g. monthly_investment is 0), returns an "error" key instead.
    """
    monthly_rate = (annual_rate_percent / 100) / 12

    if monthly_investment <= 0:
        return {"error": "monthly_investment must be greater than 0"}

    if monthly_rate == 0:
        months = target_amount / monthly_investment
    else:
        inner = 1 + (target_amount * monthly_rate) / (monthly_investment * (1 + monthly_rate))
        if inner <= 0:
            return {"error": "Target not reachable with given inputs"}
        months = math.log(inner) / math.log(1 + monthly_rate)

    return {
        "required_months": round(months, 1),
        "required_years": round(months / 12, 2),
    }


@tool
def compare_scenarios(monthly_investment: float, years: float, rates_percent: list[float]) -> dict:
    """
    Compare the future value of the same SIP plan across multiple expected
    annual return rates (e.g. conservative vs moderate vs aggressive).

    Use this when the user wants a side-by-side comparison of outcomes at
    different assumed rates of return.

    Args:
        monthly_investment: Amount invested every month.
        years: Investment duration in years.
        rates_percent: List of annual return rates to compare, e.g. [8, 12, 15].

    Returns:
        dict mapping each rate to its resulting future_value and total_gain.
    """
    months = int(round(years * 12))
    results = {}
    for rate in rates_percent:
        monthly_rate = (rate / 100) / 12
        if monthly_rate == 0:
            fv = monthly_investment * months
        else:
            fv = monthly_investment * (
                ((1 + monthly_rate) ** months - 1) / monthly_rate
            ) * (1 + monthly_rate)
        total_invested = monthly_investment * months
        results[f"{rate}%"] = {
            "future_value": round(fv, 2),
            "total_gain": round(fv - total_invested, 2),
        }
    return results


@tool
def calculate_required_rate(monthly_investment: float, target_amount: float, years: float) -> dict:
    """
    Solve for the annual rate of return required to reach a target amount,
    given a fixed monthly investment and duration.

    Use this whenever the user explicitly asks "at what ROI / rate of return"
    or "what return do I need" - i.e. the rate itself is the unknown they want
    solved for. Do NOT assume a default rate in this case; call this tool instead.

    Args:
        monthly_investment: Amount invested every month.
        target_amount: The financial goal / target maturity value.
        years: Investment duration in years.

    Returns:
        dict with required_annual_rate_percent, or an "error" key if the goal
        is unreachable even at an extremely high assumed return (meaning the
        monthly investment or duration is simply too low for the target).
    """
    if monthly_investment <= 0 or years <= 0:
        return {"error": "monthly_investment and years must both be greater than 0"}

    months = int(round(years * 12))

    def future_value(monthly_rate: float) -> float:
        if monthly_rate == 0:
            return monthly_investment * months
        return monthly_investment * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        ) * (1 + monthly_rate)

    lo, hi = 0.0, 1.0  # monthly rate search bounds: 0% to 100%/month (generous upper bound)

    if future_value(hi) < target_amount:
        return {"error": "Target not reachable within a realistic rate of return for this monthly amount and duration"}

    for _ in range(80):  # binary search, converges far beyond needed precision
        mid = (lo + hi) / 2
        if future_value(mid) < target_amount:
            lo = mid
        else:
            hi = mid

    monthly_rate = (lo + hi) / 2
    annual_rate_percent = monthly_rate * 12 * 100

    return {"required_annual_rate_percent": round(annual_rate_percent, 2)}


ALL_TOOLS = [
    calculate_sip_future_value,
    calculate_required_sip,
    calculate_required_duration,
    calculate_required_rate,
    compare_scenarios,
]
