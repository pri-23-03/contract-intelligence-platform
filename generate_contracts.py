"""Generate 100 B2B billing service agreements (ISPs as our billing clients) and tiered eval set."""

import csv
import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from fpdf import FPDF
from langchain_openai import AzureChatOpenAI

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
)

random.seed(42)

# ISP Client Company Names
COMPANY_PREFIXES = [
    "Clearwave", "Coastal", "Evergreen", "Lakeside", "Mountain", "Pioneer",
    "Prairie", "River", "Sky", "Sunset", "Northern", "Southern", "Eastern",
    "Western", "Central", "Pacific", "Atlantic", "Metro", "Valley", "Highland",
    "Golden", "Silver", "Crystal", "Diamond", "Platinum", "Summit", "Harbor",
    "Bay", "Ocean", "Forest", "Desert", "Thunder", "Lightning", "Storm",
    "Breeze", "Wind", "Solar", "Lunar", "Star", "Galaxy", "Quantum", "Nexus",
    "Vertex", "Apex", "Prime", "Elite", "Supreme", "Ultra", "Mega", "Hyper",
]

COMPANY_SUFFIXES = [
    "Internet", "Broadband", "Networks", "Fiber", "Telecom", "Communications",
    "Connect", "Online", "Net", "Link", "Tech", "Digital", "Data", "Stream",
    "Wave", "Speed", "Flash", "Rapid", "Swift", "Quick",
]

CITIES = [
    "Springfield", "Riverside", "Lakewood", "Fairview", "Madison", "Georgetown",
    "Clinton", "Franklin", "Greenville", "Bristol", "Salem", "Manchester",
    "Newport", "Arlington", "Burlington", "Cambridge", "Dayton", "Edison",
    "Fremont", "Glendale", "Hampton", "Irving", "Jackson", "Kingston",
    "Lancaster", "Milton", "Newton", "Oakland", "Portland", "Quincy",
]

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
]

# Client tiers affect pricing and terms
CLIENT_TIERS = ["Enterprise", "Business", "Standard", "Starter"]
BILLING_MODELS = ["Revenue Share", "Per-Transaction", "Hybrid", "Flat Fee"]


def get_llm():
    return AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def generate_company_name(index: int) -> str:
    prefix = COMPANY_PREFIXES[index % len(COMPANY_PREFIXES)]
    suffix = COMPANY_SUFFIXES[index % len(COMPANY_SUFFIXES)]
    return f"{prefix} {suffix}"


def generate_contract_data(index: int) -> Dict:
    """Generate B2B billing service agreement data."""
    company_name = generate_company_name(index)
    client_tier = CLIENT_TIERS[index % len(CLIENT_TIERS)]
    billing_model = BILLING_MODELS[index % len(BILLING_MODELS)]
    
    # Base metrics vary by tier
    tier_multipliers = {"Enterprise": 1.0, "Business": 0.8, "Standard": 0.6, "Starter": 0.4}
    tier_mult = tier_multipliers[client_tier]
    
    # Monthly subscriber count (client's customer base we bill for)
    subscriber_count = int((50000 + (index * 1337) % 450000) * tier_mult)
    
    # Average revenue per user (ARPU) - what client charges their customers
    avg_arpu = round(45 + (index * 7) % 120, 2)
    
    # Our billing service fees
    if billing_model == "Revenue Share":
        revenue_share_pct = round(2.5 + (index * 0.3) % 4.5, 2)  # 2.5% - 7%
        per_transaction_fee = 0
        monthly_platform_fee = 0
    elif billing_model == "Per-Transaction":
        revenue_share_pct = 0
        per_transaction_fee = round(0.15 + (index * 0.02) % 0.35, 2)  # $0.15 - $0.50
        monthly_platform_fee = round(500 + (index * 100) % 4500, 2)
    elif billing_model == "Hybrid":
        revenue_share_pct = round(1.0 + (index * 0.2) % 2.0, 2)  # 1% - 3%
        per_transaction_fee = round(0.10 + (index * 0.01) % 0.15, 2)
        monthly_platform_fee = round(250 + (index * 50) % 1000, 2)
    else:  # Flat Fee
        revenue_share_pct = 0
        per_transaction_fee = 0
        monthly_platform_fee = round(2000 + (index * 500) % 18000, 2)
    
    # Client's monthly revenue (what they bill their subscribers)
    client_monthly_revenue = round(subscriber_count * avg_arpu, 2)
    
    # Our monthly revenue from this client
    our_monthly_revenue = round(
        (client_monthly_revenue * revenue_share_pct / 100) +
        (subscriber_count * per_transaction_fee) +
        monthly_platform_fee, 2
    )
    
    # Contract terms
    contract_length = [12, 24, 36, 60][index % 4]
    start_date = datetime(2024, 1, 1) + timedelta(days=index * 3)
    end_date = start_date + timedelta(days=contract_length * 30)
    
    # Payment and remittance terms
    payment_terms_days = [15, 30, 45][index % 3]
    remittance_frequency = ["Weekly", "Bi-weekly", "Monthly"][index % 3]
    
    # SLA commitments
    billing_accuracy_sla = round(99.5 + (index % 5) * 0.1, 1)  # 99.5% - 99.9%
    platform_uptime_sla = round(99.9 + (index % 10) * 0.01, 2)  # 99.90% - 99.99%
    support_response_hours = [1, 2, 4, 8][index % 4]
    dispute_resolution_days = [5, 7, 10, 14][index % 4]
    
    # Penalties and fees
    early_termination_months = [3, 6, 12][index % 3]
    early_termination_fee = round(our_monthly_revenue * early_termination_months, 2)
    sla_credit_pct = [5, 10, 15, 25][index % 4]
    late_payment_pct = round(1.5 + (index % 3) * 0.5, 1)
    
    # Compliance and security
    pci_compliant = True
    soc2_certified = index % 5 != 0  # 80% have SOC2
    data_retention_months = [12, 24, 36, 84][index % 4]
    
    # Volume commitments
    monthly_minimum_transactions = int((1000 + (index * 500) % 9000) * tier_mult)
    volume_discount_threshold = subscriber_count * 1.2
    volume_discount_pct = round(5 + (index % 6), 1)

    return {
        "index": index,
        "client_name": company_name,
        "contract_number": f"BSA-2024-{index + 1:05d}",
        "client_tier": client_tier,
        "billing_model": billing_model,
        
        # Client metrics
        "subscriber_count": subscriber_count,
        "avg_arpu": avg_arpu,
        "client_monthly_revenue": client_monthly_revenue,
        
        # Our fees
        "revenue_share_pct": revenue_share_pct,
        "per_transaction_fee": per_transaction_fee,
        "monthly_platform_fee": monthly_platform_fee,
        "our_monthly_revenue": our_monthly_revenue,
        "annual_contract_value": round(our_monthly_revenue * 12, 2),
        "total_contract_value": round(our_monthly_revenue * contract_length, 2),
        
        # Contract terms
        "contract_length_months": contract_length,
        "start_date": start_date.strftime("%B %d, %Y"),
        "end_date": end_date.strftime("%B %d, %Y"),
        "payment_terms_days": payment_terms_days,
        "remittance_frequency": remittance_frequency,
        
        # SLAs
        "billing_accuracy_sla": billing_accuracy_sla,
        "platform_uptime_sla": platform_uptime_sla,
        "support_response_hours": support_response_hours,
        "dispute_resolution_days": dispute_resolution_days,
        
        # Penalties
        "early_termination_fee": early_termination_fee,
        "early_termination_months": early_termination_months,
        "sla_credit_pct": sla_credit_pct,
        "late_payment_pct": late_payment_pct,
        
        # Compliance
        "pci_compliant": pci_compliant,
        "soc2_certified": soc2_certified,
        "data_retention_months": data_retention_months,
        
        # Volume
        "monthly_minimum_transactions": monthly_minimum_transactions,
        "volume_discount_threshold": int(volume_discount_threshold),
        "volume_discount_pct": volume_discount_pct,
        
        # Location
        "city": CITIES[index % len(CITIES)],
        "state": STATES[index % len(STATES)],
        "phone": f"1-800-{100 + index:03d}-{1000 + index * 7:04d}",
    }


def generate_rich_sections(llm, data: Dict) -> Dict[str, str]:
    """Use LLM to generate rich B2B billing agreement text sections."""
    
    prompt = f"""Generate detailed legal contract sections for a B2B Billing Services Agreement.

Our Company: BillFlow Solutions (the billing services provider)
Client: {data['client_name']} (an ISP that needs billing services)
Client Tier: {data['client_tier']}
Billing Model: {data['billing_model']}

Key Terms:
- Subscriber Count: {data['subscriber_count']:,} customers
- Client Monthly Revenue: ${data['client_monthly_revenue']:,.2f}
- Our Revenue Share: {data['revenue_share_pct']}%
- Per-Transaction Fee: ${data['per_transaction_fee']:.2f}
- Monthly Platform Fee: ${data['monthly_platform_fee']:,.2f}
- Our Monthly Revenue: ${data['our_monthly_revenue']:,.2f}
- Contract Term: {data['contract_length_months']} months
- Payment Terms: Net {data['payment_terms_days']} days
- Remittance: {data['remittance_frequency']}
- Billing Accuracy SLA: {data['billing_accuracy_sla']}%
- Platform Uptime SLA: {data['platform_uptime_sla']}%
- Support Response: {data['support_response_hours']} hours
- Early Termination Fee: ${data['early_termination_fee']:,.2f}

Generate these sections (2-3 paragraphs each, formal B2B legal language):

1. SCOPE OF SERVICES - Detail the billing, invoicing, payment processing, collections, and reporting services we provide to the ISP client.

2. FEES AND COMPENSATION - Explain our fee structure, billing frequency, payment terms, and how we calculate and remit funds to the client.

3. SERVICE LEVEL AGREEMENTS - Detail uptime guarantees, billing accuracy commitments, support response times, and remedies for SLA failures.

4. DATA SECURITY AND COMPLIANCE - Cover PCI-DSS compliance, SOC 2 certification, data encryption, access controls, and regulatory compliance.

5. CONFIDENTIALITY AND DATA HANDLING - Explain subscriber data handling, confidentiality obligations, permitted uses, and data retention policies.

6. PAYMENT PROCESSING AND REMITTANCE - Detail how we process subscriber payments, fraud prevention, chargebacks, and remittance schedules.

7. DISPUTE RESOLUTION AND BILLING ERRORS - Cover error correction procedures, dispute timelines, credits, and escalation processes.

8. TERM AND TERMINATION - Contract duration, renewal terms, termination for cause, termination for convenience, and transition assistance.

Format each section with the header in caps followed by the content. Be specific with numbers and terms."""

    response = llm.invoke(prompt)
    content = response.content
    
    sections = {}
    current_section = None
    current_text = []
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        for header in ["SCOPE OF SERVICES", "FEES AND COMPENSATION", "SERVICE LEVEL AGREEMENTS",
                       "DATA SECURITY AND COMPLIANCE", "CONFIDENTIALITY AND DATA HANDLING", 
                       "PAYMENT PROCESSING AND REMITTANCE", "DISPUTE RESOLUTION AND BILLING ERRORS",
                       "TERM AND TERMINATION"]:
            if header in line.upper():
                if current_section and current_text:
                    sections[current_section] = '\n'.join(current_text)
                current_section = header
                current_text = []
                break
        else:
            if current_section:
                current_text.append(line)
    
    if current_section and current_text:
        sections[current_section] = '\n'.join(current_text)
    
    return sections


class ContractPDF(FPDF):
    def __init__(self, client_name: str):
        super().__init__()
        self.client_name = client_name

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "BILLFLOW SOLUTIONS", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "BILLING SERVICES AGREEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 5, f"Client: {self.client_name}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} | BillFlow Solutions - {self.client_name} | Confidential", align="C")

    def section_header(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def section_body(self, text: str):
        self.set_font("Helvetica", "", 9)
        text = text.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 4.5, text)
        self.ln(3)

    def key_value(self, key: str, value: str):
        self.set_font("Helvetica", "B", 9)
        self.cell(70, 5, key + ":", new_x="RIGHT")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, str(value), new_x="LMARGIN", new_y="NEXT")


def create_contract_pdf(data: Dict, rich_sections: Dict[str, str], output_dir: str) -> str:
    pdf = ContractPDF(data["client_name"])
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Agreement Number: {data['contract_number']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Effective: {data['start_date']} through {data['end_date']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.section_header("SECTION 1: CLIENT INFORMATION")
    pdf.key_value("Client Name", data['client_name'])
    pdf.key_value("Client Tier", data['client_tier'])
    pdf.key_value("Billing Model", data['billing_model'])
    pdf.key_value("Subscriber Count", f"{data['subscriber_count']:,}")
    pdf.key_value("Client Monthly Revenue", f"${data['client_monthly_revenue']:,.2f}")
    pdf.key_value("Location", f"{data['city']}, {data['state']}")
    pdf.ln(3)

    pdf.section_header("SECTION 2: FEE STRUCTURE")
    pdf.key_value("Revenue Share Rate", f"{data['revenue_share_pct']}%")
    pdf.key_value("Per-Transaction Fee", f"${data['per_transaction_fee']:.2f}")
    pdf.key_value("Monthly Platform Fee", f"${data['monthly_platform_fee']:,.2f}")
    pdf.key_value("Our Monthly Revenue", f"${data['our_monthly_revenue']:,.2f}")
    pdf.key_value("Annual Contract Value", f"${data['annual_contract_value']:,.2f}")
    pdf.key_value("Total Contract Value", f"${data['total_contract_value']:,.2f}")
    pdf.ln(3)

    pdf.section_header("SECTION 3: PAYMENT TERMS")
    pdf.key_value("Payment Terms", f"Net {data['payment_terms_days']} days")
    pdf.key_value("Remittance Frequency", data['remittance_frequency'])
    pdf.key_value("Late Payment Penalty", f"{data['late_payment_pct']}% per month")
    pdf.key_value("Monthly Minimum Transactions", f"{data['monthly_minimum_transactions']:,}")
    pdf.ln(3)

    pdf.section_header("SECTION 4: SERVICE LEVEL AGREEMENTS")
    pdf.key_value("Billing Accuracy SLA", f"{data['billing_accuracy_sla']}%")
    pdf.key_value("Platform Uptime SLA", f"{data['platform_uptime_sla']}%")
    pdf.key_value("Support Response Time", f"{data['support_response_hours']} hours")
    pdf.key_value("Dispute Resolution", f"{data['dispute_resolution_days']} business days")
    pdf.key_value("SLA Credit", f"{data['sla_credit_pct']}% of monthly fee")
    pdf.ln(3)

    pdf.section_header("SECTION 5: COMPLIANCE & SECURITY")
    pdf.key_value("PCI-DSS Compliant", "Yes" if data['pci_compliant'] else "No")
    pdf.key_value("SOC 2 Certified", "Yes" if data['soc2_certified'] else "No")
    pdf.key_value("Data Retention Period", f"{data['data_retention_months']} months")
    pdf.ln(3)

    pdf.section_header("SECTION 6: VOLUME TERMS")
    pdf.key_value("Volume Discount Threshold", f"{data['volume_discount_threshold']:,} subscribers")
    pdf.key_value("Volume Discount Rate", f"{data['volume_discount_pct']}%")
    pdf.ln(3)

    section_map = {
        "SCOPE OF SERVICES": "SECTION 7: SCOPE OF SERVICES",
        "FEES AND COMPENSATION": "SECTION 8: FEES AND COMPENSATION",
        "SERVICE LEVEL AGREEMENTS": "SECTION 9: SERVICE LEVEL AGREEMENTS",
        "DATA SECURITY AND COMPLIANCE": "SECTION 10: DATA SECURITY AND COMPLIANCE",
        "CONFIDENTIALITY AND DATA HANDLING": "SECTION 11: CONFIDENTIALITY AND DATA HANDLING",
        "PAYMENT PROCESSING AND REMITTANCE": "SECTION 12: PAYMENT PROCESSING AND REMITTANCE",
        "DISPUTE RESOLUTION AND BILLING ERRORS": "SECTION 13: DISPUTE RESOLUTION",
        "TERM AND TERMINATION": "SECTION 14: TERM AND TERMINATION",
    }

    for orig_key, section_title in section_map.items():
        if orig_key in rich_sections:
            pdf.section_header(section_title)
            pdf.section_body(rich_sections[orig_key])

    pdf.add_page()
    pdf.section_header("SECTION 15: TERMINATION AND TRANSITION")
    
    term_text = f"""Early Termination: Either party may terminate this Agreement for cause with 30 days written notice. Client may terminate for convenience with {data['early_termination_months']} months notice or payment of the Early Termination Fee of ${data['early_termination_fee']:,.2f}.

Transition Assistance: Upon termination, BillFlow Solutions shall provide reasonable transition assistance for up to 90 days, including data export, API support, and knowledge transfer to the replacement provider.

Final Settlement: All outstanding fees shall be due within {data['payment_terms_days']} days of termination. BillFlow Solutions shall remit any collected funds owed to Client within 5 business days of final reconciliation."""

    pdf.section_body(term_text)
    
    pdf.section_header("SECTION 16: SIGNATURES")
    
    sig_text = f"""By signing below, the parties agree to be bound by all terms of this Billing Services Agreement.

BillFlow Solutions agrees to provide billing, payment processing, and related services to {data['client_name']} under the terms specified herein.

{data['client_name']} agrees to pay the fees specified and comply with all obligations under this Agreement."""

    pdf.section_body(sig_text)
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(90, 5, "_" * 40, new_x="RIGHT")
    pdf.cell(0, 5, "_" * 40, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 5, "BillFlow Solutions", new_x="RIGHT")
    pdf.cell(0, 5, data['client_name'], new_x="LMARGIN", new_y="NEXT")

    filename = data["client_name"].lower().replace(" ", "_") + ".pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)
    return filepath


def generate_tiered_questions(contracts: List[Dict]) -> List[Tuple[str, str, str]]:
    """Generate tiered evaluation questions for billing contractor use case."""
    questions = []
    
    # TIER 1: Simple lookups (120 questions)
    for c in contracts[:30]:
        name = c["client_name"]
        questions.extend([
            (f"What is the revenue share percentage for {name}?", f"{c['revenue_share_pct']}%", "simple"),
            (f"What is the monthly platform fee for {name}?", f"${c['monthly_platform_fee']:,.2f}", "simple"),
            (f"What is the billing accuracy SLA for {name}?", f"{c['billing_accuracy_sla']}%", "simple"),
            (f"What is the payment terms for {name}?", f"Net {c['payment_terms_days']} days", "simple"),
        ])
    
    # TIER 2: Calculated/derived questions (50 questions)
    for c in contracts[:25]:
        name = c["client_name"]
        questions.extend([
            (f"What is our annual contract value for {name}?", 
             f"${c['annual_contract_value']:,.2f}", "calculated"),
            (f"What is the total contract value for {name} over the full term?", 
             f"${c['total_contract_value']:,.2f}", "calculated"),
        ])
    
    # TIER 3: Comparison/analytical questions (30 questions)
    by_revenue = sorted(contracts, key=lambda x: x['our_monthly_revenue'], reverse=True)
    by_accuracy = sorted(contracts, key=lambda x: x['billing_accuracy_sla'], reverse=True)
    by_share = sorted(contracts, key=lambda x: x['revenue_share_pct'], reverse=True)
    
    questions.append((
        "Which client generates the highest monthly revenue for us?",
        by_revenue[0]['client_name'], "comparison"
    ))
    questions.append((
        "Which client has the highest billing accuracy SLA?",
        by_accuracy[0]['client_name'], "comparison"
    ))
    questions.append((
        "Which client has the highest revenue share rate?",
        by_share[0]['client_name'], "comparison"
    ))
    
    # Pairwise comparisons
    pairs = [(contracts[i], contracts[i+1]) for i in range(0, 20, 2)]
    for c1, c2 in pairs:
        higher = c1 if c1['our_monthly_revenue'] > c2['our_monthly_revenue'] else c2
        questions.append((
            f"Between {c1['client_name']} and {c2['client_name']}, which generates more monthly revenue?",
            higher['client_name'], "comparison"
        ))
        
        better_sla = c1 if c1['billing_accuracy_sla'] > c2['billing_accuracy_sla'] else c2
        questions.append((
            f"Between {c1['client_name']} and {c2['client_name']}, which has the higher billing accuracy SLA?",
            better_sla['client_name'], "comparison"
        ))
    
    # Tier-based questions
    enterprise = [c for c in contracts if c['client_tier'] == "Enterprise"]
    if enterprise:
        highest_enterprise = max(enterprise, key=lambda x: x['our_monthly_revenue'])
        questions.append((
            "Which Enterprise tier client generates the most revenue?",
            highest_enterprise['client_name'], "comparison"
        ))
    
    soc2 = [c for c in contracts if c['soc2_certified']]
    if soc2:
        questions.append((
            "How many clients require SOC 2 certification?",
            str(len(soc2)), "comparison"
        ))
    
    random.shuffle(questions)
    
    simple = [q for q in questions if q[2] == "simple"][:120]
    calculated = [q for q in questions if q[2] == "calculated"][:50]
    comparison = [q for q in questions if q[2] == "comparison"][:30]
    
    return simple + calculated + comparison


def main():
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    for f in os.listdir(output_dir):
        if f.endswith(".pdf"):
            os.remove(os.path.join(output_dir, f))

    print("Initializing LLM...")
    llm = get_llm()

    print("Generating 100 B2B billing service agreements...")
    contracts = []
    section_cache = {}

    for i in range(100):
        data = generate_contract_data(i)
        contracts.append(data)
        
        cache_key = i // 10
        if cache_key not in section_cache:
            print(f"  Generating rich text for batch {cache_key + 1}/10...")
            section_cache[cache_key] = generate_rich_sections(llm, data)
        
        rich_sections = section_cache[cache_key]
        filepath = create_contract_pdf(data, rich_sections, output_dir)
        print(f"  [{i+1:3d}/100] {filepath}")

    with open("contract_data.json", "w") as f:
        json.dump(contracts, f, indent=2)

    print("\nGenerating tiered evaluation questions...")
    questions = generate_tiered_questions(contracts)
    
    tier_counts = {}
    for _, _, tier in questions:
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    with open("eval_set.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "answer", "tier"])
        for q, a, t in questions:
            writer.writerow([q, a, t])

    print(f"Created eval_set.csv:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  - {tier}: {count} questions")
    print(f"  - Total: {len(questions)} questions")
    
    # Print portfolio summary
    total_acv = sum(c['annual_contract_value'] for c in contracts)
    total_subscribers = sum(c['subscriber_count'] for c in contracts)
    print(f"\nPortfolio Summary:")
    print(f"  - Total Annual Contract Value: ${total_acv:,.2f}")
    print(f"  - Total Subscribers Managed: {total_subscribers:,}")
    print(f"  - Average Monthly Revenue per Client: ${total_acv/12/100:,.2f}")
    
    print("\nNext: python ingestion.py && python eval.py")


if __name__ == "__main__":
    main()

