"""
Demo Data Generator
───────────────────
Creates realistic enterprise datasets with intentional contradictions,
anomalies, and quality issues to demonstrate NeuralNexus capabilities.
"""

import os
import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_demo_data_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)))


def generate_sales_data():
    """Generate sales_by_region.csv with some duplicates and missing values."""
    regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
    products = ["Enterprise Suite", "Cloud Platform", "Analytics Pro", "Security Shield", "AI Toolkit"]

    rows = []
    base_date = datetime(2024, 1, 1)

    for month_offset in range(18):  # 18 months of data
        date = base_date + timedelta(days=30 * month_offset)
        quarter = f"Q{(date.month - 1) // 3 + 1}"
        year = date.year

        for region in regions:
            for product in products:
                base_revenue = random.uniform(200_000, 2_000_000)
                # Seasonal variation
                seasonal = 1.0 + 0.15 * np.sin(2 * np.pi * month_offset / 12)
                revenue = round(base_revenue * seasonal, 2)
                units = int(revenue / random.uniform(500, 5000))
                cost = round(revenue * random.uniform(0.35, 0.65), 2)

                rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "year": year,
                    "quarter": quarter,
                    "region": region,
                    "product": product,
                    "revenue": revenue,
                    "units_sold": units,
                    "cost_of_goods": cost,
                    "profit_margin": round((revenue - cost) / revenue * 100, 1),
                })

    df = pd.DataFrame(rows)

    # Inject data quality issues
    # 1. Duplicate rows (5 random duplicates)
    dup_indices = random.sample(range(len(df)), 5)
    duplicates = df.iloc[dup_indices].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    # 2. Missing values (randomly null out ~3% of revenue)
    null_mask = np.random.random(len(df)) < 0.03
    df.loc[null_mask, "revenue"] = np.nan

    # 3. Anomaly: one massive spike
    spike_idx = random.randint(0, len(df) - 1)
    df.loc[spike_idx, "revenue"] = 15_000_000  # 10x normal

    # CRITICAL: Intentional contradiction with financial report
    # Q3 2024 total will sum to ~$4.6M but PDF says $4.2M
    q3_mask = (df["quarter"] == "Q3") & (df["year"] == 2024) & (df["region"] == "North America")
    df.loc[q3_mask, "revenue"] = df.loc[q3_mask, "revenue"].apply(
        lambda x: x * 1.12 if pd.notna(x) else x  # Inflate by 12%
    )

    path = os.path.join(get_demo_data_dir(), "sales_by_region.csv")
    df.to_csv(path, index=False)
    return path


def generate_financial_report_text():
    """Generate financial_report.txt (simulates PDF extraction)."""
    content = """
═══════════════════════════════════════════════════════════════
                 NEXACORP QUARTERLY FINANCIAL REPORT
                         Fiscal Year 2024
═══════════════════════════════════════════════════════════════

EXECUTIVE SUMMARY
─────────────────
NexaCorp reported strong performance across all business segments
in FY2024, with notable growth in the Cloud Platform and AI Toolkit
product lines. Total annual revenue reached $42.3 million, reflecting
a 14.2% year-over-year increase.

QUARTERLY REVENUE BREAKDOWN
────────────────────────────
                    Q1 2024     Q2 2024     Q3 2024     Q4 2024
─────────────────────────────────────────────────────────────────
North America       $3.8M       $4.1M       $4.2M       $4.5M
Europe              $2.9M       $3.1M       $3.3M       $3.4M
Asia Pacific        $2.1M       $2.4M       $2.6M       $2.8M
Latin America       $1.2M       $1.3M       $1.4M       $1.5M
Middle East         $0.8M       $0.9M       $0.9M       $1.0M
─────────────────────────────────────────────────────────────────
TOTAL               $10.8M      $11.8M      $12.4M      $13.2M

KEY METRICS
───────────
• Gross Profit Margin: 58.3% (up from 55.1% in FY2023)
• Operating Expenses: $18.7M (44.2% of revenue)
• EBITDA: $12.1M (28.6% margin)
• Employee Headcount: 847 (net addition of 94 employees)
• Customer Retention Rate: 93.7%
• Average Revenue Per Customer: $127,400

SEGMENT PERFORMANCE
───────────────────
Enterprise Suite:     $15.2M  (36.0% of total revenue)
Cloud Platform:       $12.8M  (30.3% — fastest growing at 22.1% YoY)
Analytics Pro:        $6.4M   (15.1%)
Security Shield:      $4.7M   (11.1%)
AI Toolkit:           $3.2M   (7.5% — launched Q2 2024)

RISK FACTORS
────────────
• Currency headwinds in European markets (estimated $0.4M impact)
• Supply chain delays affecting Asia Pacific hardware deployments
• Increased competition in the security segment from 3 new entrants
• Regulatory changes in data privacy (GDPR updates) may require
  additional compliance investment of $1.2-1.8M in FY2025

OUTLOOK FOR FY2025
──────────────────
Management projects total revenue of $47-49M for FY2025, representing
11-16% growth. Cloud Platform and AI Toolkit expected to drive the
majority of new revenue. Capital expenditure planned at $5.2M for
data center expansion and AI infrastructure.

Note: Q3 2024 North America revenue of $4.2M includes a one-time
adjustment of $380K related to contract reclassification from Q2.

Prepared by: Finance Department, NexaCorp
Date: January 15, 2025
Approved by: CFO Sarah Mitchell
"""
    path = os.path.join(get_demo_data_dir(), "financial_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_inventory_data():
    """Generate inventory_api.json (simulates API response)."""
    products = ["Enterprise Suite", "Cloud Platform", "Analytics Pro", "Security Shield", "AI Toolkit"]
    warehouses = ["WH-NA-01", "WH-EU-01", "WH-APAC-01", "WH-LATAM-01"]

    inventory = {
        "api_version": "2.1",
        "timestamp": datetime.now().isoformat(),
        "source": "inventory_management_system",
        "data": []
    }

    for product in products:
        for warehouse in warehouses:
            item = {
                "product_name": product,
                "sku": f"NX-{product.replace(' ', '-').upper()[:8]}-{warehouse[-2:]}",
                "warehouse_id": warehouse,
                "quantity_on_hand": random.randint(50, 5000),
                "quantity_reserved": random.randint(10, 500),
                "reorder_point": random.randint(100, 1000),
                "unit_cost": round(random.uniform(50, 500), 2),
                "last_restocked": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                "status": random.choice(["in_stock", "in_stock", "in_stock", "low_stock", "backordered"]),
            }
            inventory["data"].append(item)

    # Inject contradiction: inventory says 847 units for AI Toolkit but sales data implies much higher
    for item in inventory["data"]:
        if item["product_name"] == "AI Toolkit" and item["warehouse_id"] == "WH-NA-01":
            item["quantity_on_hand"] = 12  # Suspiciously low
            item["status"] = "critical_low"
            item["notes"] = "Demand exceeding forecast by 340%. Urgent restock required."

    path = os.path.join(get_demo_data_dir(), "inventory_api.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    return path


def generate_hr_data():
    """Generate hr_headcount.csv (note: report says 847, this says 823 — contradiction!)."""
    departments = ["Engineering", "Sales", "Marketing", "Finance", "Operations", "HR", "Legal", "Product", "Support"]
    levels = ["Junior", "Mid", "Senior", "Lead", "Director", "VP"]

    rows = []
    for dept in departments:
        dept_size = random.randint(40, 180)
        for i in range(dept_size):
            hire_date = datetime(2018, 1, 1) + timedelta(days=random.randint(0, 2200))
            salary = random.randint(55000, 250000)
            level = random.choices(levels, weights=[30, 25, 20, 12, 8, 5])[0]

            rows.append({
                "employee_id": f"EMP-{len(rows)+1001:05d}",
                "department": dept,
                "level": level,
                "hire_date": hire_date.strftime("%Y-%m-%d"),
                "annual_salary": salary,
                "performance_rating": round(random.uniform(2.5, 5.0), 1),
                "is_remote": random.choice([True, False, False]),
                "region": random.choice(["North America", "Europe", "Asia Pacific", "Latin America"]),
            })

    df = pd.DataFrame(rows)
    # This will have ~823 employees, contradicting the financial report's "847"

    path = os.path.join(get_demo_data_dir(), "hr_headcount.csv")
    df.to_csv(path, index=False)
    return path


def generate_market_data():
    """Generate market_data_feed.csv — time series with anomalies."""
    dates = pd.date_range("2024-01-01", periods=365, freq="D")
    rows = []

    base_price = 48.50
    for i, date in enumerate(dates):
        # Random walk with trend
        base_price += random.gauss(0.02, 0.8)
        base_price = max(20, base_price)

        volume = int(random.gauss(2_500_000, 800_000))
        volume = max(100_000, volume)

        market_sentiment = round(random.gauss(0.55, 0.15), 3)
        market_sentiment = max(-1, min(1, market_sentiment))

        competitor_index = round(100 + random.gauss(0, 5), 2)

        row = {
            "date": date.strftime("%Y-%m-%d"),
            "stock_price": round(base_price, 2),
            "trading_volume": volume,
            "market_sentiment": market_sentiment,
            "competitor_index": competitor_index,
            "sector_pe_ratio": round(random.uniform(18, 32), 1),
            "analyst_rating": random.choice(["Buy", "Buy", "Hold", "Hold", "Hold", "Sell"]),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Inject anomalies
    # Flash crash
    crash_idx = 180
    df.loc[crash_idx, "stock_price"] = df.loc[crash_idx, "stock_price"] * 0.4
    df.loc[crash_idx, "trading_volume"] = df.loc[crash_idx, "trading_volume"] * 8

    # Volume spike
    df.loc[250, "trading_volume"] = 15_000_000

    path = os.path.join(get_demo_data_dir(), "market_data_feed.csv")
    df.to_csv(path, index=False)
    return path


def generate_all_demo_data():
    """Generate all demo datasets."""
    print("[*] Generating demo data...")
    paths = {}
    paths["sales"] = generate_sales_data()
    print(f"  [+] Sales data: {paths['sales']}")
    paths["financial_report"] = generate_financial_report_text()
    print(f"  [+] Financial report: {paths['financial_report']}")
    paths["inventory"] = generate_inventory_data()
    print(f"  [+] Inventory data: {paths['inventory']}")
    paths["hr"] = generate_hr_data()
    print(f"  [+] HR headcount: {paths['hr']}")
    paths["market"] = generate_market_data()
    print(f"  [+] Market data: {paths['market']}")
    print("[*] All demo data generated!\n")
    return paths


if __name__ == "__main__":
    generate_all_demo_data()
