"""
Ageing Calculation Engine and Follow-Up Mapping Logic.
Processes raw ERP transactions into standard 8-bucket customer ageing records.
"""
import re
import collections
from typing import List, Dict, Any, Optional, Tuple

from backend.app.core.parsers.common import format_inr, clean_customer_name
from backend.app.automations.ageing_report.models import (
    RawTransaction,
    CustomerAgeingSummary,
    AgeingBatchSummary,
    BucketMetric,
    BranchMetric,
    FUPersonMetric
)

# Learned salesperson to Follow-Up Owner mappings from corporate reports
SALES_TO_FU: Dict[str, str] = {
    "Sweety Soni": "Vaibhav",
    "Irfan Shaikh": "Siddhesh",
    "Fasaludheen C A": "Nikita",
    "Narendra Gupta": "Nikita",
    "Rahul Vasawa": "Vaibhav",
    "Samuel Prabhu": "Nikita",
    "Priyanka Gawali": "Vaibhav",
    "Mohnish Arora": "Vaibhav",
    "Ranjith Kuniyil": "Nikita",
    "Hetal Shah": "Vaibhav",
    "Tasneem Haji": "Vaibhav",
    "Jayatheertha L G": "Nikita",
    "Priyanka Sardesai": "Nikita",
    "Shashi Kumar": "Nikita",
    "Rushabh Mehta": "Nikita",
    "Edward Dsouza": "Vaibhav",
    "Sheela Dashauni": "Nikita",
    "Vishal Lachhiramani": "Vaibhav",
    "Parvesh Gupta": "Vaibhav",
    "Mr. P  Gowthamaraju": "Nikita",
    "Akash Mishra": "Vaibhav",
    "Mary Hanse": "Nikita",
    "Parag Mehta": "Vaibhav",
    "Sanjay Rajpurohit": "Nikita",
    "Ashrith Kovver": "Nikita",
    "Gokul T": "Nikita",
    "Anup P": "Nikita",
    "John Pal": "Nikita",
    "Pushpendra Tiwari": "Vaibhav",
    "Dheeraj Chanigalla": "Nikita",
    "Shruti Singh": "Nikita",
    "Swapnil Mukherjee": "Nikita",
    "Dhruv Thanvi": "Nikita",
    "Prasad Ragaiah": "Nikita",
    "Harvind Kumar": "Nikita",
    "Venkata Ganesh": "Nikita",
    "Mourya Roy": "Nikita",
    "Ankit Srivastava": "Nikita",
    "B Thiagu": "Nikita",
    "Anchita Moni": "Vaibhav",
    "Tyra Theknath": "Siddhesh",
    "Rafiq Shaikh": "Nikita",
    "Savita Mane": "Vaibhav",
    "Richard Theknath": "Siddhesh",
    "Shabeer A": "Nikita",
    "Narendra Mahadik": "Nikita",
    "Sharmi Dey": "Nikita",
    "Chetna Morye": "Vaibhav"
}

# Branch fallback allocation
BRANCH_TO_FU: Dict[str, str] = {
    "Banglore": "Nikita",
    "Chennai": "Nikita",
    "Domestic": "Nikita",
    "Hyderabad": "Nikita",
    "Kolkata": "Vaibhav",
    "Kerala": "Nikita",
    "Ahmedabad": "Vaibhav",
    "Delhi": "Vaibhav",
    "Mumbai": "Nikita"
}

def resolve_fu_person(
    sales_person: str,
    branch: str,
    customer_name: str,
    overrides: Optional[Dict[str, str]] = None
) -> str:
    """
    Resolves the Follow-Up (FU) owner for a debtor in order of precedence:
    1. Persistent customer override from database
    2. Exact Sales Person mapping
    3. Branch default fallback
    4. Default to 'Other'
    """
    if overrides and customer_name in overrides:
        return overrides[customer_name]

    if sales_person in SALES_TO_FU:
        return SALES_TO_FU[sales_person]

    for sp_key, fu in SALES_TO_FU.items():
        if sp_key.lower() in sales_person.lower() or sales_person.lower() in sp_key.lower():
            return fu

    if branch in BRANCH_TO_FU:
        return BRANCH_TO_FU[branch]

    return "Other"

def resolve_overdue_start(payment_terms: str) -> Tuple[int, str]:
    """
    Returns (start_bucket_idx, start_col_letter) based on customer payment terms.
    Buckets:
      0: 0-30 days   -> Col 'K'
      1: 31-45 days  -> Col 'L'
      2: 46-60 days  -> Col 'M'
      3: 61-90 days  -> Col 'N'
      4: 91-180 days -> Col 'O'
    """
    if not payment_terms:
        return 1, "L"

    terms_clean = payment_terms.strip().lower()

    if any(k in terms_clean for k in ["immediate", "advance", "cod", "cash"]):
        return 0, "K"

    match = re.search(r'\b(\d+)\b', terms_clean)
    if match:
        days = int(match.group(1))
        if days <= 15:
            return 0, "K"
        elif days <= 30:
            return 1, "L"
        elif days <= 45:
            return 2, "M"
        elif days <= 60:
            return 3, "N"
        else:
            return 4, "O"

    return 1, "L"

def format_crores_lacs(amount: float) -> str:
    """
    Formats currency in human-readable Indian crore/lakh notation for executive cards.
    e.g. ₹ 14.82 Cr, ₹ 94.20 Lacs, ₹ 24,150
    """
    abs_val = abs(amount)
    sign = "-" if amount < 0 else ""
    if abs_val >= 10_000_000:
        return f"{sign}₹ {abs_val / 10_000_000:.2f} Cr"
    elif abs_val >= 100_000:
        return f"{sign}₹ {abs_val / 100_000:.2f} Lacs"
    else:
        return f"{sign}₹ {abs_val:,.0f}"

def aggregate_customer_ageing(
    transactions: List[RawTransaction],
    batch_uuid: str = "",
    overrides: Optional[Dict[str, str]] = None,
    carry_forward: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[CustomerAgeingSummary]:
    """
    Groups individual voucher transactions by Customer, categorizes balances into
    8 standard age buckets, computes IATA terms, and returns sorted customer summaries.
    Applies FIFO payment netting against oldest overdue buckets so invoice tenors remain
    strictly positive and advances/unallocated receipts are isolated in ON A/C.
    """
    # Group transactions by cleaned customer name to prevent split rows
    cust_groups: Dict[str, List[RawTransaction]] = collections.defaultdict(list)
    for tx in transactions:
        c_clean = clean_customer_name(tx.customer.strip()) if tx.customer else ""
        if c_clean:
            cust_groups[c_clean].append(tx)

    customers: List[CustomerAgeingSummary] = []

    for cust_name, tx_list in cust_groups.items():
        # Metadata resolution (majority vote or non-empty)
        sales_counter = collections.Counter(tx.sales_person for tx in tx_list if tx.sales_person)
        sales_person = sales_counter.most_common(1)[0][0] if sales_counter else ""

        branch_counter = collections.Counter(tx.branch for tx in tx_list if tx.branch)
        branch = branch_counter.most_common(1)[0][0] if branch_counter else "Mumbai"

        terms_counter = collections.Counter(tx.payment_terms for tx in tx_list if tx.payment_terms)
        payment_terms = terms_counter.most_common(1)[0][0] if terms_counter else "Net 30"

        # Latest non-empty remark
        latest_remark = ""
        for tx in reversed(tx_list):
            if tx.remarks:
                latest_remark = tx.remarks
                break

        # 8 Age Buckets: [0-30, 31-45, 46-60, 61-90, 91-180, 181-240, 241-365, >365]
        buckets = [0.0] * 8
        unallocated_payments = 0.0
        total_on_ac = 0.0

        for tx in tx_list:
            net = tx.net_outstanding_inr
            age = tx.age_days
            on_ac = tx.on_account_amount

            if on_ac > 0:
                total_on_ac += on_ac

            if net > 0:
                # Debit voucher (Sales Invoice, debit Journal Entry) -> bucket by age
                if age <= 30:
                    buckets[0] += net
                elif age <= 45:
                    buckets[1] += net
                elif age <= 60:
                    buckets[2] += net
                elif age <= 90:
                    buckets[3] += net
                elif age <= 180:
                    buckets[4] += net
                elif age <= 240:
                    buckets[5] += net
                elif age <= 365:
                    buckets[6] += net
                else:
                    buckets[7] += net
            elif net < 0:
                # Credit receipt / Payment Entry / advance payment
                unallocated_payments += abs(net)
                if on_ac == 0:
                    total_on_ac += abs(net)

        # FIFO Netting: Apply unallocated payment receipts against oldest overdue buckets first
        credit_pool = unallocated_payments
        for b_i in range(7, -1, -1):
            if credit_pool <= 0:
                break
            if buckets[b_i] > 0:
                deduct = min(buckets[b_i], credit_pool)
                buckets[b_i] -= deduct
                credit_pool -= deduct

        b_0_30, b_31_45, b_46_60, b_61_90, b_91_180, b_181_240, b_241_365, b_above_365 = buckets
        grand_total = sum(buckets)

        # Overdue outstanding: Overdue balances dynamically determined by customer payment terms
        start_idx, _ = resolve_overdue_start(payment_terms)
        outstanding = sum(buckets[start_idx:])
        received = 0.0

        # Carry-forward previous notes, assigned FU owner, and logged received payments from previous batch
        cf = carry_forward.get(cust_name) if carry_forward else None
        if cf:
            if cf.get("remark"):
                latest_remark = cf["remark"] if not latest_remark else f"{latest_remark} | {cf['remark']}"
            if cf.get("received") is not None and cf["received"] > 0:
                received = cf["received"]

        balance = outstanding - received

        # Freight-specific terms
        this_iata = b_31_45
        last_iata = b_46_60
        on_ac_val = -total_on_ac if total_on_ac > 0 else 0.0

        # Follow-Up Person assignment (precedence: carry_forward -> overrides -> sales mapping -> branch fallback)
        fu_person = resolve_fu_person(sales_person, branch, cust_name, overrides)
        if cf and cf.get("fu_person"):
            fu_person = cf["fu_person"]

        # Item 2 Fix: Skip customers with zero exposure or overall credit balances (net deposits with company)
        if grand_total <= 0.01 and outstanding <= 0.01:
            continue

        item = CustomerAgeingSummary(
            batch_uuid=batch_uuid,
            customer_name=cust_name,
            fu_person=fu_person,
            sales_person=sales_person,
            branch=branch,
            payment_terms=payment_terms,
            outstanding=round(outstanding, 2),
            received=round(received, 2),
            balance=round(balance, 2),
            advance=round(total_on_ac, 2),
            remark=latest_remark,
            bucket_0_30=round(b_0_30, 2),
            bucket_31_45=round(b_31_45, 2),
            bucket_46_60=round(b_46_60, 2),
            bucket_61_90=round(b_61_90, 2),
            bucket_91_180=round(b_91_180, 2),
            bucket_181_240=round(b_181_240, 2),
            bucket_241_365=round(b_241_365, 2),
            bucket_above_365=round(b_above_365, 2),
            grand_total=round(grand_total, 2),
            this_iata=round(this_iata, 2),
            last_iata=round(last_iata, 2),
            on_ac=round(on_ac_val, 2)
        )
        customers.append(item)

    # Sort descending by outstanding (overdue risk priority)
    customers.sort(key=lambda c: (c.outstanding, c.grand_total), reverse=True)
    return customers

def calculate_batch_summary(
    customers: List[CustomerAgeingSummary],
    batch_uuid: str,
    filename: str,
    posting_cutoff_date: str,
    invoice_count: int
) -> AgeingBatchSummary:
    """
    Computes executive metrics, 8-bucket distribution, and branch/FU breakdown.
    """
    total_receivable = sum(c.grand_total for c in customers)
    total_overdue = sum(c.outstanding for c in customers)
    this_iata = sum(c.this_iata for c in customers)
    last_iata = sum(c.last_iata for c in customers)
    critical_365 = sum(c.bucket_above_365 for c in customers)

    # Bucket totals
    b0_30 = sum(c.bucket_0_30 for c in customers)
    b31_45 = sum(c.bucket_31_45 for c in customers)
    b46_60 = sum(c.bucket_46_60 for c in customers)
    b61_90 = sum(c.bucket_61_90 for c in customers)
    b91_180 = sum(c.bucket_91_180 for c in customers)
    b181_240 = sum(c.bucket_181_240 for c in customers)
    b241_365 = sum(c.bucket_241_365 for c in customers)
    b_above = sum(c.bucket_above_365 for c in customers)

    def calc_pct(val: float) -> float:
        return round((val / total_receivable * 100), 1) if total_receivable > 0 else 0.0

    bucket_dist = [
        BucketMetric(label="0-30 Days", amount=round(b0_30, 2), percentage=calc_pct(b0_30), formatted_amount=format_crores_lacs(b0_30)),
        BucketMetric(label="31-45 Days", amount=round(b31_45, 2), percentage=calc_pct(b31_45), formatted_amount=format_crores_lacs(b31_45)),
        BucketMetric(label="46-60 Days", amount=round(b46_60, 2), percentage=calc_pct(b46_60), formatted_amount=format_crores_lacs(b46_60)),
        BucketMetric(label="61-90 Days", amount=round(b61_90, 2), percentage=calc_pct(b61_90), formatted_amount=format_crores_lacs(b61_90)),
        BucketMetric(label="91-180 Days", amount=round(b91_180, 2), percentage=calc_pct(b91_180), formatted_amount=format_crores_lacs(b91_180)),
        BucketMetric(label="181-240 Days", amount=round(b181_240, 2), percentage=calc_pct(b181_240), formatted_amount=format_crores_lacs(b181_240)),
        BucketMetric(label="241-365 Days", amount=round(b241_365, 2), percentage=calc_pct(b241_365), formatted_amount=format_crores_lacs(b241_365)),
        BucketMetric(label="> 365 Days", amount=round(b_above, 2), percentage=calc_pct(b_above), formatted_amount=format_crores_lacs(b_above)),
    ]

    # Branch distribution
    branch_map: Dict[str, Dict[str, Any]] = collections.defaultdict(lambda: {
        "outstanding": 0.0,
        "overdue": 0.0,
        "customer_count": 0
    })
    for c in customers:
        branch_map[c.branch]["outstanding"] += c.grand_total
        branch_map[c.branch]["overdue"] += c.outstanding
        branch_map[c.branch]["customer_count"] += 1

    branch_dist = []
    for b_name, b_data in sorted(branch_map.items(), key=lambda x: x[1]["outstanding"], reverse=True):
        share = round((b_data["outstanding"] / total_receivable * 100), 1) if total_receivable > 0 else 0.0
        branch_dist.append(BranchMetric(
            branch=b_name,
            outstanding=round(b_data["outstanding"], 2),
            overdue=round(b_data["overdue"], 2),
            customer_count=b_data["customer_count"],
            share_pct=share,
            formatted_outstanding=format_crores_lacs(b_data["outstanding"]),
            formatted_overdue=format_crores_lacs(b_data["overdue"])
        ))

    # Follow-up Person distribution
    fu_map: Dict[str, Dict[str, Any]] = collections.defaultdict(lambda: {
        "outstanding": 0.0,
        "received": 0.0,
        "balance": 0.0,
        "customer_count": 0
    })
    for c in customers:
        fu_map[c.fu_person]["outstanding"] += c.outstanding
        fu_map[c.fu_person]["received"] += c.received
        fu_map[c.fu_person]["balance"] += c.balance
        fu_map[c.fu_person]["customer_count"] += 1

    fu_dist = []
    for fu_name, fu_data in sorted(fu_map.items(), key=lambda x: x[1]["outstanding"], reverse=True):
        share = round((fu_data["outstanding"] / total_overdue * 100), 1) if total_overdue > 0 else 0.0
        fu_dist.append(FUPersonMetric(
            fu_person=fu_name,
            outstanding=round(fu_data["outstanding"], 2),
            received=round(fu_data["received"], 2),
            balance=round(fu_data["balance"], 2),
            customer_count=fu_data["customer_count"],
            share_pct=share,
            formatted_outstanding=format_crores_lacs(fu_data["outstanding"]),
            formatted_balance=format_crores_lacs(fu_data["balance"])
        ))

    return AgeingBatchSummary(
        batch_uuid=batch_uuid,
        filename=filename,
        posting_cutoff_date=posting_cutoff_date,
        total_receivable=round(total_receivable, 2),
        total_overdue=round(total_overdue, 2),
        this_iata=round(this_iata, 2),
        last_iata=round(last_iata, 2),
        critical_365=round(critical_365, 2),
        customer_count=len(customers),
        invoice_count=invoice_count,
        formatted_total_receivable=format_crores_lacs(total_receivable),
        formatted_total_overdue=format_crores_lacs(total_overdue),
        formatted_this_iata=format_crores_lacs(this_iata),
        formatted_last_iata=format_crores_lacs(last_iata),
        formatted_critical_365=format_crores_lacs(critical_365),
        bucket_distribution=bucket_dist,
        branch_distribution=branch_dist,
        fu_distribution=fu_dist
    )
