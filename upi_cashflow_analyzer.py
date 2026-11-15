"""
MSME UPI Cash-Flow Analyzer
Starter script for reconciling UPI transactions with invoices and estimating working capital.

Designed for Indian MSMEs. Uses sample data by default.
Extend with real CSV exports from PhonePe/GPay/bank statements and AI matching.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Dict, List

def generate_sample_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create realistic sample UPI transactions and invoices for an Indian MSME."""
    # Sample UPI transactions (common for small retailers / service providers)
    upi_data = {
        "date": ["2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14", "2026-11-14"],
        "amount": [2500.0, 1800.0, 4200.0, -1500.0, 3100.0, -800.0],
        "description": [
            "UPI/PhonePe - Customer Rahul Kumar",
            "UPI/GPay - Invoice INV-1042",
            "UPI/PhonePe - Bulk order Shopkeeper",
            "UPI/Payment to Supplier ABC Traders",
            "UPI/PhonePe - Customer Priya Sharma",
            "UPI/Bank transfer - Electricity bill"
        ],
        "ref": ["UPI12345", "UPI12346", "UPI12347", "UPI12348", "UPI12349", "UPI12350"],
        "type": ["credit", "credit", "credit", "debit", "credit", "debit"]
    }
    upi_df = pd.DataFrame(upi_data)
    upi_df["date"] = pd.to_datetime(upi_df["date"])

    # Sample invoices
    invoice_data = {
        "invoice_id": ["INV-1042", "INV-1045", "INV-1048"],
        "date": ["2026-11-11", "2026-11-12", "2026-11-14"],
        "amount": [1800.0, 4200.0, 3100.0],
        "customer": ["GPay Customer", "Bulk order Shopkeeper", "Priya Sharma"],
        "gst_rate": [0.18, 0.18, 0.05],
        "status": ["paid", "paid", "paid"]
    }
    invoice_df = pd.DataFrame(invoice_data)
    invoice_df["date"] = pd.to_datetime(invoice_df["date"])

    return upi_df, invoice_df

def reconcile_upi_with_invoices(upi_df: pd.DataFrame, invoice_df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple matching logic:
    - Exact amount match within 2 days
    - Bonus if description contains invoice ID or customer name
    """
    results = []

    for _, upi in upi_df.iterrows():
        matched = False
        match_info = "Unmatched"

        # Only try to match credits (incoming payments)
        if upi["type"] != "credit":
            results.append({
                "upi_ref": upi["ref"],
                "upi_amount": upi["amount"],
                "upi_date": upi["date"].date(),
                "match_status": "Debit (outgoing)",
                "matched_invoice": None,
                "notes": "Supplier / expense payment"
            })
            continue

        for _, inv in invoice_df.iterrows():
            date_diff = abs((upi["date"] - inv["date"]).days)
            amount_match = abs(upi["amount"] - inv["amount"]) < 1.0  # tolerance for rounding

            desc_match = (
                inv["invoice_id"].lower() in upi["description"].lower()
                or any(word.lower() in upi["description"].lower() for word in inv["customer"].split() if len(word) > 3)
            )

            if amount_match and date_diff <= 2:
                matched = True
                match_info = f"Matched to {inv['invoice_id']} (confidence: {'high' if desc_match else 'medium'})"
                results.append({
                    "upi_ref": upi["ref"],
                    "upi_amount": upi["amount"],
                    "upi_date": upi["date"].date(),
                    "match_status": "Matched",
                    "matched_invoice": inv["invoice_id"],
                    "notes": match_info
                })
                break

        if not matched:
            results.append({
                "upi_ref": upi["ref"],
                "upi_amount": upi["amount"],
                "upi_date": upi["date"].date(),
                "match_status": "Unmatched",
                "matched_invoice": None,
                "notes": "No invoice found within amount/date window"
            })

    return pd.DataFrame(results)

def compute_cashflow_summary(upi_df: pd.DataFrame) -> Dict:
    """Basic cash-flow metrics useful for MSMEs."""
    credits = upi_df[upi_df["amount"] > 0]["amount"].sum()
    debits = abs(upi_df[upi_df["amount"] < 0]["amount"].sum())
    net = credits - debits

    return {
        "total_inflows": round(credits, 2),
        "total_outflows": round(debits, 2),
        "net_cashflow": round(net, 2),
        "transaction_count": len(upi_df),
        "period": f"{upi_df['date'].min().date()} to {upi_df['date'].max().date()}"
    }

def estimate_working_capital(cashflow: Dict, unmatched_credits: float) -> str:
    """Simple heuristic for short-term working capital need."""
    # Rough rule: if unmatched credits > 20% of inflows or net is negative, flag need
    if cashflow["net_cashflow"] < 0:
        return "Working capital alert: Negative net cash-flow. Consider short-term credit or faster collections."
    if unmatched_credits > cashflow["total_inflows"] * 0.25:
        return f"Working capital note: ~₹{unmatched_credits:,.0f} in unmatched receipts. Verify invoices to unlock liquidity."
    return "Cash position appears stable for the short term. Monitor daily UPI inflows."

def main():
    print("=" * 60)
    print("MSME UPI Cash-Flow Analyzer  |  Indian MSME Focus")
    print("=" * 60)

    upi_df, invoice_df = generate_sample_data()
    print(f"\nLoaded {len(upi_df)} UPI transactions and {len(invoice_df)} invoices.\n")

    reconciliation = reconcile_upi_with_invoices(upi_df, invoice_df)
    print("RECONCILIATION RESULTS")
    print("-" * 60)
    print(reconciliation.to_string(index=False))

    cashflow = compute_cashflow_summary(upi_df)
    print("\nCASH-FLOW SUMMARY")
    print("-" * 60)
    for k, v in cashflow.items():
        print(f"{k.replace('_', ' ').title():<22} : {v}")

    unmatched = reconciliation[
        (reconciliation["match_status"] == "Unmatched") & (reconciliation["upi_amount"] > 0)
    ]["upi_amount"].sum()

    print("\nWORKING CAPITAL ESTIMATE")
    print("-" * 60)
    print(estimate_working_capital(cashflow, unmatched))

    print("\nGST FLAGS (simple)")
    print("-" * 60)
    matched_count = len(reconciliation[reconciliation["match_status"] == "Matched"])
    print(f"Matched transactions: {matched_count}")
    print("Tip: Cross-check matched amounts against GSTR-1 / e-invoices for input credit accuracy.")

    print("\n" + "=" * 60)
    print("Next: Replace sample data with your real UPI CSV export.")
    print("=" * 60)

if __name__ == "__main__":
    main()
