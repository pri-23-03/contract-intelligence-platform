"""Generate simple text documents from contract_data.json for RAG ingestion."""

import json
import os

def generate_docs():
    """Create text documents from contract data for vector store ingestion."""
    
    # Load contract data
    with open("contract_data.json", "r") as f:
        contracts = json.load(f)
    
    # Create output directory
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Remove old PDFs
    for f in os.listdir(output_dir):
        if f.endswith(".pdf") or f.endswith(".txt"):
            os.remove(os.path.join(output_dir, f))
    
    print(f"Generating {len(contracts)} contract documents...")
    
    for contract in contracts:
        # Generate comprehensive document content
        doc_content = f"""BILLFLOW SOLUTIONS
BILLING SERVICES AGREEMENT

Agreement Number: {contract['contract_number']}
Client: {contract['client_name']}
Client Tier: {contract['client_tier']}
Location: {contract['city']}, {contract['state']}

SECTION 1: CONTRACT OVERVIEW
This Billing Services Agreement ("Agreement") is entered into between BillFlow Solutions ("Provider") and {contract['client_name']} ("Client").
Effective Date: {contract['start_date']}
End Date: {contract['end_date']}
Contract Term: {contract['contract_length_months']} months

SECTION 2: CLIENT INFORMATION
Client Name: {contract['client_name']}
Client Tier: {contract['client_tier']}
Billing Model: {contract['billing_model']}
Total Subscriber Count: {contract['subscriber_count']:,}
Average Revenue Per User (ARPU): ${contract['avg_arpu']:.2f}
Client Monthly Revenue: ${contract['client_monthly_revenue']:,.2f}
Service Location: {contract['city']}, {contract['state']}
Contact Phone: {contract['phone']}

SECTION 3: FEE STRUCTURE AND COMPENSATION
Billing Model: {contract['billing_model']}
Revenue Share Rate: {contract['revenue_share_pct']}%
Per-Transaction Fee: ${contract['per_transaction_fee']:.2f}
Monthly Platform Fee: ${contract['monthly_platform_fee']:,.2f}

BillFlow Monthly Revenue: ${contract['our_monthly_revenue']:,.2f}
Annual Contract Value (ACV): ${contract['annual_contract_value']:,.2f}
Total Contract Value: ${contract['total_contract_value']:,.2f}

SECTION 4: PAYMENT TERMS
Payment Terms: Net {contract['payment_terms_days']} days
Remittance Frequency: {contract['remittance_frequency']}
Late Payment Penalty: {contract['late_payment_pct']}% per month
Monthly Minimum Transactions: {contract['monthly_minimum_transactions']:,}

SECTION 5: SERVICE LEVEL AGREEMENTS (SLA)
Billing Accuracy SLA: {contract['billing_accuracy_sla']}%
Platform Uptime SLA: {contract['platform_uptime_sla']}%
Support Response Time: {contract['support_response_hours']} hours
Dispute Resolution Timeline: {contract['dispute_resolution_days']} business days
SLA Credit: {contract['sla_credit_pct']}% of monthly fee for SLA breach

SECTION 6: COMPLIANCE AND SECURITY
PCI-DSS Compliant: {'Yes' if contract['pci_compliant'] else 'No'}
SOC 2 Type II Certified: {'Yes' if contract['soc2_certified'] else 'No'}
Data Retention Period: {contract['data_retention_months']} months

SECTION 7: VOLUME DISCOUNTS
Volume Discount Threshold: {contract['volume_discount_threshold']:,} subscribers
Volume Discount Rate: {contract['volume_discount_pct']}%

SECTION 8: TERMINATION PROVISIONS
Early Termination Notice: {contract['early_termination_months']} months
Early Termination Fee: ${contract['early_termination_fee']:,.2f}

This fee represents the remaining contract value and applies if Client terminates
the agreement before the end date of {contract['end_date']}.

SECTION 9: SCOPE OF SERVICES
BillFlow Solutions agrees to provide the following services to {contract['client_name']}:

1. SUBSCRIBER BILLING
   - Monthly invoice generation for {contract['subscriber_count']:,} subscribers
   - Multiple payment method support (credit card, ACH, autopay)
   - Prorated billing for mid-cycle changes
   - Automatic retry for failed payments

2. PAYMENT PROCESSING
   - Secure PCI-DSS compliant payment processing
   - Real-time transaction authorization
   - Fraud detection and prevention
   - Chargeback management

3. COLLECTIONS
   - Automated payment reminders
   - Dunning management
   - Collections escalation procedures
   - Bad debt recovery assistance

4. REPORTING AND ANALYTICS
   - Real-time billing dashboard
   - Revenue analytics and forecasting
   - Subscriber churn analysis
   - Custom report generation

5. CUSTOMER SUPPORT
   - Billing inquiry handling
   - {contract['support_response_hours']}-hour response time for {contract['client_tier']} tier
   - Dispute resolution within {contract['dispute_resolution_days']} business days

SECTION 10: REMITTANCE SCHEDULE
BillFlow Solutions will remit collected funds to {contract['client_name']} on a {contract['remittance_frequency'].lower()} basis.

Remittance Frequency: {contract['remittance_frequency']}
Payment Terms: Net {contract['payment_terms_days']} days
Wire Transfer: Available for amounts over $10,000
ACH Transfer: Standard remittance method

SECTION 11: SIGNATURES

_____________________________     _____________________________
BillFlow Solutions               {contract['client_name']}
Authorized Representative        Authorized Representative

Date: _______________           Date: _______________

---
Contract Number: {contract['contract_number']}
Generated for demo purposes
"""
        
        # Write to text file
        filename = contract['client_name'].lower().replace(" ", "_") + ".txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(doc_content)
        
        print(f"  Created: {filepath}")
    
    print(f"\nGenerated {len(contracts)} contract documents in {output_dir}/")
    print("Next: Run 'python ingestion.py' to index the documents")


if __name__ == "__main__":
    generate_docs()

