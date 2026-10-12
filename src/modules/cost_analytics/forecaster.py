"""
Cost Forecasting and Budget Analysis Engine for AI Control Center.
Provides moving averages, linear run-rate trend projections,
and department budget threshold breach early-warning mechanisms.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np


class CostForecaster:
    """Forecasting and budget tracking analytics."""

    @staticmethod
    def calculate_department_budgets(
        requests_df: pd.DataFrame,
        departments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate current spending against allocated monthly budgets per department.
        Returns budget utilization status, warning flags, and depletion velocity.
        """
        if requests_df.empty:
            return [
                {
                    "department_id": d["id"],
                    "department_name": d["name"],
                    "budget": d["monthly_budget"],
                    "current_spend": 0.0,
                    "utilization_pct": 0.0,
                    "remaining_budget": d["monthly_budget"],
                    "status": "SAFE",
                    "projected_month_end": 0.0,
                    "days_remaining_est": 30,
                }
                for d in departments
            ]

        # Calculate current monthly spend per department
        current_month = datetime.now().strftime("%Y-%m")
        req_copy = requests_df.copy()
        req_copy["month"] = pd.to_datetime(req_copy["timestamp"]).dt.strftime("%Y-%m")
        this_month_reqs = req_copy[req_copy["month"] == current_month]

        dept_spend = this_month_reqs.groupby("department_id")["estimated_cost_usd"].sum().to_dict()

        now = datetime.now()
        day_of_month = max(1, now.day)
        days_in_month = 30  # Standard normalized MBA projection month

        results = []
        for d in departments:
            spend = float(dept_spend.get(d["id"], 0.0))
            budget = float(d["monthly_budget"])
            utilization = (spend / budget * 100.0) if budget > 0 else 0.0
            remaining = max(0.0, budget - spend)

            # Daily run rate
            daily_run_rate = spend / day_of_month
            projected_month_end = round(daily_run_rate * days_in_month, 2)
            projected_utilization = (projected_month_end / budget * 100.0) if budget > 0 else 0.0

            if daily_run_rate > 0:
                days_until_exhaustion = int(remaining / daily_run_rate)
            else:
                days_until_exhaustion = 999

            if utilization >= 90.0 or projected_utilization >= 105.0:
                status = "CRITICAL"
            elif utilization >= 70.0 or projected_utilization >= 85.0:
                status = "WARNING"
            else:
                status = "HEALTHY"

            results.append({
                "department_id": d["id"],
                "department_name": d["name"],
                "budget": budget,
                "current_spend": round(spend, 4),
                "utilization_pct": round(utilization, 1),
                "remaining_budget": round(remaining, 2),
                "status": status,
                "daily_run_rate": round(daily_run_rate, 2),
                "projected_month_end": projected_month_end,
                "projected_utilization_pct": round(projected_utilization, 1),
                "days_remaining_est": days_until_exhaustion,
            })

        return sorted(results, key=lambda x: x["utilization_pct"], reverse=True)

    @staticmethod
    def generate_spend_forecast(
        daily_spend_df: pd.DataFrame,
        forecast_days: int = 14
    ) -> Dict[str, Any]:
        """
        Generate time-series forecast using 7-day rolling moving average and linear extrapolation.
        Returns historical series, projected series, and confidence boundaries.
        """
        if daily_spend_df.empty or len(daily_spend_df) < 3:
            return {
                "historical": [],
                "forecast": [],
                "trend": "Insufficient data",
                "avg_daily_spend": 0.0,
                "projected_period_spend": 0.0,
            }

        df = daily_spend_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # 7-day rolling average
        df["rolling_7d"] = df["cost_usd"].rolling(window=7, min_periods=1).mean()

        last_date = df["date"].max()
        x_vals = np.arange(len(df))
        y_vals = df["cost_usd"].values

        # Linear regression slope and intercept
        slope, intercept = np.polyfit(x_vals, y_vals, 1)

        # Baseline stats
        avg_daily = float(df["cost_usd"].mean())
        recent_daily = float(df["cost_usd"].tail(7).mean())

        # Generate future forecast points
        forecast_points = []
        projected_total = 0.0

        for i in range(1, forecast_days + 1):
            f_date = last_date + timedelta(days=i)
            # Weighted forecast blending linear trend and recent rolling average
            linear_pred = max(0.0, slope * (len(df) + i - 1) + intercept)
            blended_pred = max(0.01, 0.6 * recent_daily + 0.4 * linear_pred)

            # Volatility margin (~15%)
            upper_bound = blended_pred * 1.18
            lower_bound = max(0.0, blended_pred * 0.82)

            projected_total += blended_pred
            forecast_points.append({
                "date": f_date.strftime("%Y-%m-%d"),
                "forecast_cost_usd": round(blended_pred, 4),
                "upper_bound_usd": round(upper_bound, 4),
                "lower_bound_usd": round(lower_bound, 4),
            })

        trend_direction = "Rising" if slope > 0.05 else ("Declining" if slope < -0.05 else "Stable")

        return {
            "historical": df.to_dict(orient="records"),
            "forecast": forecast_points,
            "trend": trend_direction,
            "slope": round(float(slope), 4),
            "avg_daily_spend": round(avg_daily, 2),
            "recent_daily_spend": round(recent_daily, 2),
            "projected_period_spend": round(projected_total, 2),
        }
