"""Digital Service Operations Analytics

Reads data/service_tickets.csv, computes operational KPIs, saves charts to
output/ and writes a text summary to output/summary_report.txt.

Run:  python analytics.py
"""
import os
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt

DATA_FILE = "data/service_tickets.csv"
OUT_DIR = "output"

SLA_HOURS = {"Low": 72, "Medium": 48, "High": 24, "Critical": 8}
PRIORITY_ORDER = ["Critical", "High", "Medium", "Low"]


# ---------------------------------------------------------------- load & clean
def load_data(path):
    df = pd.read_csv(path, parse_dates=["created_at", "resolved_at"])
    df = df.drop_duplicates(subset="ticket_id")
    df["month"] = df["created_at"].dt.to_period("M").astype(str)
    df["sla_target_hours"] = df["priority"].map(SLA_HOURS)
    resolved = df["status"] == "Resolved"
    df["sla_met"] = pd.NA
    df.loc[resolved, "sla_met"] = df.loc[resolved, "resolution_hours"] <= df.loc[resolved, "sla_target_hours"]
    df["sla_met"] = df["sla_met"].astype("boolean")
    return df


# ---------------------------------------------------------------------- KPIs
def compute_kpis(df):
    resolved = df[df["status"] == "Resolved"]
    return {
        "Total tickets": len(df),
        "Resolved tickets": len(resolved),
        "Open tickets": int((df["status"] == "Open").sum()),
        "Resolution rate (%)": round(len(resolved) / len(df) * 100, 1),
        "Avg resolution time (hrs)": round(resolved["resolution_hours"].mean(), 1),
        "Median resolution time (hrs)": round(resolved["resolution_hours"].median(), 1),
        "SLA compliance (%)": round(resolved["sla_met"].astype(float).mean() * 100, 1),
        "Avg CSAT (1-5)": round(resolved["csat"].mean(), 2),
    }


def summarize(df):
    resolved = df[df["status"] == "Resolved"].copy()
    resolved["sla_met_f"] = resolved["sla_met"].astype(float)

    def group(col):
        return (
            resolved.groupby(col)
            .agg(tickets=("ticket_id", "count"),
                 avg_hours=("resolution_hours", "mean"),
                 sla_pct=("sla_met_f", "mean"),
                 csat=("csat", "mean"))
            .assign(sla_pct=lambda x: x["sla_pct"] * 100)
            .round(2)
        )

    monthly = df.groupby("month").size().rename("tickets")
    return {
        "monthly": monthly,
        "by_channel": group("channel"),
        "by_category": group("category"),
        "by_priority": group("priority").reindex(PRIORITY_ORDER),
        "by_agent": group("agent").sort_values("sla_pct", ascending=False),
    }


# -------------------------------------------------------------------- charts
def save_charts(df, s):
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Monthly ticket volume
    fig, ax = plt.subplots(figsize=(8, 4))
    s["monthly"].plot(kind="line", marker="o", ax=ax, color="#2a6fdb")
    ax.set_title("Monthly Ticket Volume")
    ax.set_xlabel("Month")
    ax.set_ylabel("Tickets")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/monthly_volume.png", dpi=120)
    plt.close(fig)

    # 2. Tickets by channel
    fig, ax = plt.subplots(figsize=(7, 4))
    s["by_channel"]["tickets"].sort_values().plot(kind="barh", ax=ax, color="#2a6fdb")
    ax.set_title("Tickets by Channel")
    ax.set_xlabel("Tickets")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/tickets_by_channel.png", dpi=120)
    plt.close(fig)

    # 3. SLA compliance by priority
    fig, ax = plt.subplots(figsize=(7, 4))
    s["by_priority"]["sla_pct"].plot(kind="bar", ax=ax, color="#2a9d5c")
    ax.axhline(90, color="red", linestyle="--", label="90% target")
    ax.set_title("SLA Compliance by Priority")
    ax.set_ylabel("% within SLA")
    ax.set_ylim(0, 100)
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=0)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/sla_by_priority.png", dpi=120)
    plt.close(fig)

    # 4. Average resolution time by category
    fig, ax = plt.subplots(figsize=(7, 4))
    s["by_category"]["avg_hours"].sort_values().plot(kind="barh", ax=ax, color="#e08a1e")
    ax.set_title("Average Resolution Time by Category")
    ax.set_xlabel("Hours")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/resolution_by_category.png", dpi=120)
    plt.close(fig)

    # 5. Agent performance (SLA % vs CSAT)
    fig, ax = plt.subplots(figsize=(7, 4))
    a = s["by_agent"]
    ax.scatter(a["sla_pct"], a["csat"], s=a["tickets"] / 4, color="#8a4fd6", alpha=0.7)
    for name, row in a.iterrows():
        ax.annotate(name, (row["sla_pct"], row["csat"]), xytext=(5, 5), textcoords="offset points")
    ax.set_title("Agent Performance (bubble size = tickets handled)")
    ax.set_xlabel("SLA compliance (%)")
    ax.set_ylabel("Avg CSAT")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/agent_performance.png", dpi=120)
    plt.close(fig)


# -------------------------------------------------------------------- report
def write_report(kpis, s):
    lines = ["DIGITAL SERVICE OPERATIONS ANALYTICS - SUMMARY REPORT", "=" * 56, "", "KEY METRICS"]
    lines += [f"  {k:<30} {v}" for k, v in kpis.items()]

    for title, key in [("BY CHANNEL", "by_channel"), ("BY CATEGORY", "by_category"),
                       ("BY PRIORITY", "by_priority"), ("BY AGENT", "by_agent")]:
        lines += ["", title, s[key].to_string()]

    best = s["by_agent"].index[0]
    worst = s["by_agent"].index[-1]
    worst_cat = s["by_category"]["avg_hours"].idxmax()
    busiest = s["by_channel"]["tickets"].idxmax()
    lines += [
        "", "INSIGHTS",
        f"  - Busiest channel: {busiest}",
        f"  - Slowest category to resolve: {worst_cat}",
        f"  - Top agent by SLA compliance: {best}",
        f"  - Agent needing support (lowest SLA): {worst}",
    ]

    text = "\n".join(lines)
    with open(f"{OUT_DIR}/summary_report.txt", "w") as f:
        f.write(text)
    return text


def main():
    if not os.path.exists(DATA_FILE):
        raise SystemExit("data/service_tickets.csv not found. Run: python generate_data.py")
    df = load_data(DATA_FILE)
    kpis = compute_kpis(df)
    s = summarize(df)
    os.makedirs(OUT_DIR, exist_ok=True)
    save_charts(df, s)
    report = write_report(kpis, s)
    s["by_agent"].to_csv(f"{OUT_DIR}/agent_performance.csv")
    print(report)
    print(f"\nCharts and report saved in ./{OUT_DIR}/")


if __name__ == "__main__":
    main()
