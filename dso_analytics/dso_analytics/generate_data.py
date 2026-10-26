"""Generate a sample dataset of digital service tickets.

Run:  python generate_data.py
Output: data/service_tickets.csv

Replace this file's output with your real export (same columns) to analyze real data.
"""
import os
import numpy as np
import pandas as pd

SEED = 42
N_TICKETS = 5000

CHANNELS = ["Web Portal", "Mobile App", "Email", "Chat", "Phone"]
CATEGORIES = ["Login Issue", "Payment Failure", "Account Update", "Technical Error", "Billing Query", "Feature Request"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
AGENTS = ["Asha", "Ravi", "Meera", "Kiran", "Sana", "Vikram", "Divya", "Arjun"]

# SLA target in hours for each priority
SLA_HOURS = {"Low": 72, "Medium": 48, "High": 24, "Critical": 8}


def main():
    rng = np.random.default_rng(SEED)

    start = pd.Timestamp("2026-01-01")
    end = pd.Timestamp("2026-09-30 23:59")
    span_minutes = int((end - start).total_seconds() // 60)
    created = start + pd.to_timedelta(rng.integers(0, span_minutes, N_TICKETS), unit="m")

    priority = rng.choice(PRIORITIES, N_TICKETS, p=[0.30, 0.40, 0.22, 0.08])
    channel = rng.choice(CHANNELS, N_TICKETS, p=[0.28, 0.30, 0.17, 0.17, 0.08])
    category = rng.choice(CATEGORIES, N_TICKETS)
    agent = rng.choice(AGENTS, N_TICKETS)

    # Resolution time: lognormal, scaled by priority (urgent tickets are worked faster)
    scale = pd.Series(priority).map({"Low": 30, "Medium": 20, "High": 12, "Critical": 5}).to_numpy()
    resolution_hours = rng.lognormal(mean=0, sigma=0.7, size=N_TICKETS) * scale

    resolved = created + pd.to_timedelta(resolution_hours, unit="h")
    status = np.where(rng.random(N_TICKETS) < 0.04, "Open", "Resolved")
    resolved = pd.Series(resolved).where(status == "Resolved")
    resolution_hours = pd.Series(resolution_hours).where(status == "Resolved")

    csat = rng.choice([1, 2, 3, 4, 5], N_TICKETS, p=[0.05, 0.08, 0.17, 0.35, 0.35]).astype(float)
    # Slow resolutions get lower satisfaction
    csat = np.where(resolution_hours > 48, np.clip(csat - 1, 1, 5), csat)
    csat = pd.Series(csat).where(status == "Resolved")

    df = pd.DataFrame({
        "ticket_id": [f"TKT-{i:05d}" for i in range(1, N_TICKETS + 1)],
        "created_at": created,
        "resolved_at": resolved,
        "channel": channel,
        "category": category,
        "priority": priority,
        "agent": agent,
        "status": status,
        "resolution_hours": resolution_hours.round(2),
        "csat": csat,
    }).sort_values("created_at").reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/service_tickets.csv", index=False)
    print(f"Wrote data/service_tickets.csv with {len(df)} rows")


if __name__ == "__main__":
    main()
