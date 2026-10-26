# Digital Service Operations Analytics

A simple Python project that analyzes digital service operations (support tickets
across web, mobile, email, chat and phone) and reports on volume, resolution time,
SLA compliance, customer satisfaction (CSAT) and agent performance.

## Project structure

```
dso_analytics/
├── generate_data.py     # creates sample data -> data/service_tickets.csv
├── analytics.py         # KPIs, charts and summary report
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python generate_data.py     # creates data/service_tickets.csv (5,000 sample tickets)
python analytics.py         # prints report, saves charts + report to output/
```

## What it produces (in `output/`)

| File | Description |
|------|-------------|
| `summary_report.txt` | KPIs, breakdowns by channel / category / priority / agent, insights |
| `monthly_volume.png` | Ticket volume trend by month |
| `tickets_by_channel.png` | Ticket count per channel |
| `sla_by_priority.png` | SLA compliance per priority vs 90% target |
| `resolution_by_category.png` | Average resolution hours per category |
| `agent_performance.png` | SLA % vs CSAT per agent |
| `agent_performance.csv` | Agent table |

## KPIs

- **Resolution rate** = resolved tickets / total tickets
- **SLA compliance** = % of resolved tickets closed within the priority's SLA target
  (Critical 8h, High 24h, Medium 48h, Low 72h)
- **Avg / median resolution time** in hours
- **Avg CSAT** on a 1-5 scale

## Using your own data

Replace `data/service_tickets.csv` with your export using the same columns:
`ticket_id, created_at, resolved_at, channel, category, priority, agent, status, resolution_hours, csat`.
Adjust `SLA_HOURS` in `analytics.py` to match your own SLA rules.

## Ideas to extend

- Add a Streamlit dashboard
- Forecast ticket volume
- Predict SLA breaches with a simple classifier
