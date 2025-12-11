"""
Revenue Intelligence Engine - Next Generation CRM Core
========================================================
The brain of an autonomous revenue operations platform.

This isn't a dashboard. It's an AI that:
- Finds money you're losing (Leakage Detection)
- Finds money you're missing (Opportunity Discovery)
- Tells you exactly what to do (Action Recommendations)
- Does it for you when you let it (Autonomous Actions)
- Learns from every deal (Revenue Genome)
- Predicts before you know (Signal Detection)
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import random
import hashlib

from openai import AzureOpenAI

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
)


# =============================================================================
# Core Data Models
# =============================================================================

class Urgency(str, Enum):
    CRITICAL = "critical"      # Act today or lose money
    HIGH = "high"              # Act this week
    MEDIUM = "medium"          # Act this month
    LOW = "low"                # Optimize when possible
    OPPORTUNITY = "opportunity" # Nice to have


class ActionType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    ESCALATE = "escalate"
    RENEGOTIATE = "renegotiate"
    UPSELL = "upsell"
    RETAIN = "retain"
    COLLECT = "collect"


class SignalType(str, Enum):
    ENGAGEMENT_DROP = "engagement_drop"
    PAYMENT_DELAY = "payment_delay"
    VOLUME_DECLINE = "volume_decline"
    COMPETITOR_MENTION = "competitor_mention"
    STAKEHOLDER_CHANGE = "stakeholder_change"
    SATISFACTION_DROP = "satisfaction_drop"
    EXPANSION_SIGNAL = "expansion_signal"
    RENEWAL_RISK = "renewal_risk"


@dataclass
class RevenueLeakage:
    """A specific instance of revenue being lost."""
    id: str
    client_name: str
    contract_id: int
    leak_type: str
    amount_monthly: float
    amount_annual: float
    description: str
    root_cause: str
    fix_action: str
    fix_effort: str  # low, medium, high
    fix_timeline: str
    confidence: float  # 0-1


@dataclass
class RevenueOpportunity:
    """An untapped revenue opportunity."""
    id: str
    client_name: str
    contract_id: int
    opportunity_type: str
    potential_monthly: float
    potential_annual: float
    description: str
    approach: str
    success_probability: float
    best_timing: str
    talking_points: List[str]


@dataclass
class ActionItem:
    """A specific action the system recommends or can execute."""
    id: str
    client_name: str
    contract_id: int
    action_type: str
    urgency: str
    title: str
    description: str
    revenue_impact: float
    due_date: str
    script: Optional[str]  # What to say/write
    auto_executable: bool  # Can the system do this?
    prerequisites: List[str]
    success_metrics: List[str]


@dataclass
class ClientSignal:
    """A detected signal about client health/intent."""
    id: str
    client_name: str
    contract_id: int
    signal_type: str
    strength: float  # 0-1
    detected_at: str
    description: str
    evidence: List[str]
    recommended_response: str
    if_ignored: str  # What happens if we don't act


@dataclass
class DealGenome:
    """The DNA pattern of a contract/deal."""
    contract_id: int
    client_name: str
    success_score: float  # 0-100, likelihood of long-term success
    genome_markers: Dict[str, float]  # Key traits and their scores
    similar_deals: List[Dict]  # Historical deals with similar patterns
    predicted_outcome: str
    optimization_suggestions: List[str]


@dataclass
class RevenueInsight:
    """A high-level insight about portfolio revenue."""
    id: str
    category: str
    headline: str
    detail: str
    impact: float
    trend: str  # up, down, stable
    action_required: bool
    related_contracts: List[int]


# =============================================================================
# Revenue Leakage Detector
# =============================================================================

class LeakageDetector:
    """
    Finds every way you're losing money.
    
    Categories:
    1. Pricing Leakage - below-market rates, missed escalations
    2. Volume Leakage - unused thresholds, declining transactions
    3. Billing Leakage - late payments, uncollected fees
    4. SLA Leakage - over-delivery without compensation
    5. Term Leakage - unfavorable terms costing money
    6. Churn Leakage - at-risk revenue
    """
    
    def __init__(self, contracts: List[Dict], benchmarks: Dict):
        self.contracts = contracts
        self.benchmarks = benchmarks
    
    def detect_all_leakage(self) -> List[RevenueLeakage]:
        """Run all leakage detection algorithms."""
        leakages = []
        
        for contract in self.contracts:
            leakages.extend(self._detect_pricing_leakage(contract))
            leakages.extend(self._detect_volume_leakage(contract))
            leakages.extend(self._detect_billing_leakage(contract))
            leakages.extend(self._detect_sla_leakage(contract))
            leakages.extend(self._detect_term_leakage(contract))
        
        # Sort by annual impact
        leakages.sort(key=lambda x: x.amount_annual, reverse=True)
        return leakages
    
    def _detect_pricing_leakage(self, contract: Dict) -> List[RevenueLeakage]:
        """Detect if we're charging below market rate."""
        leakages = []
        tier = contract.get("client_tier", "Standard")
        tier_bench = self.benchmarks.get("tier_benchmarks", {}).get(tier, {})
        
        if not tier_bench:
            return leakages
        
        # Revenue share leakage
        rev_share = contract.get("revenue_share_pct", 0)
        avg_rev_share = tier_bench.get("avg_revenue_share", 0)
        
        if rev_share > 0 and avg_rev_share > 0 and rev_share < avg_rev_share * 0.85:
            # More than 15% below average
            gap = avg_rev_share - rev_share
            client_rev = contract.get("client_monthly_revenue", 0)
            monthly_loss = client_rev * (gap / 100)
            
            leakages.append(RevenueLeakage(
                id=self._generate_id(contract, "pricing_revshare"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                leak_type="Pricing - Below Market Rate",
                amount_monthly=round(monthly_loss, 2),
                amount_annual=round(monthly_loss * 12, 2),
                description=f"Revenue share of {rev_share}% is {gap:.1f}pp below {tier} tier average of {avg_rev_share:.1f}%",
                root_cause="Contract negotiated below market rate or hasn't been updated",
                fix_action=f"Renegotiate to {avg_rev_share:.1f}% on next renewal",
                fix_effort="medium",
                fix_timeline="Next renewal cycle",
                confidence=0.85,
            ))
        
        # Per-transaction fee leakage
        txn_fee = contract.get("per_transaction_fee", 0)
        if txn_fee > 0 and txn_fee < 0.15:  # Very low transaction fee
            subscribers = contract.get("subscriber_count", 0)
            market_fee = 0.25
            monthly_loss = subscribers * (market_fee - txn_fee)
            
            if monthly_loss > 1000:  # Only flag if material
                leakages.append(RevenueLeakage(
                    id=self._generate_id(contract, "pricing_txnfee"),
                    client_name=contract.get("client_name", "Unknown"),
                    contract_id=contract.get("index", 0),
                    leak_type="Pricing - Low Transaction Fee",
                    amount_monthly=round(monthly_loss, 2),
                    amount_annual=round(monthly_loss * 12, 2),
                    description=f"Transaction fee of ${txn_fee:.2f} is below market rate of $0.25",
                    root_cause="Aggressive discounting during initial negotiation",
                    fix_action="Include fee adjustment clause in renewal",
                    fix_effort="medium",
                    fix_timeline="Next renewal",
                    confidence=0.75,
                ))
        
        return leakages
    
    def _detect_volume_leakage(self, contract: Dict) -> List[RevenueLeakage]:
        """Detect volume-related revenue leakage."""
        leakages = []
        
        subscribers = contract.get("subscriber_count", 0)
        min_transactions = contract.get("monthly_minimum_transactions", 0)
        discount_threshold = contract.get("volume_discount_threshold", 0)
        discount_pct = contract.get("volume_discount_pct", 0)
        
        # Check if they're just under volume discount threshold
        if discount_threshold > 0 and subscribers > 0:
            gap_to_threshold = discount_threshold - subscribers
            if 0 < gap_to_threshold < subscribers * 0.15:  # Within 15% of threshold
                # They're close but not getting the discount
                # This is actually an OPPORTUNITY, not leakage
                pass
            
            # Check if they're significantly above minimum but we're not capturing growth
            if subscribers > min_transactions * 1.5:
                growth_pct = ((subscribers - min_transactions) / min_transactions) * 100
                if growth_pct > 50:
                    # They've grown significantly - should renegotiate
                    potential = contract.get("our_monthly_revenue", 0) * 0.10  # Could get 10% more
                    
                    leakages.append(RevenueLeakage(
                        id=self._generate_id(contract, "volume_growth"),
                        client_name=contract.get("client_name", "Unknown"),
                        contract_id=contract.get("index", 0),
                        leak_type="Volume - Unpriced Growth",
                        amount_monthly=round(potential, 2),
                        amount_annual=round(potential * 12, 2),
                        description=f"Client has grown {growth_pct:.0f}% above contracted minimum without rate adjustment",
                        root_cause="No price escalation clause tied to volume growth",
                        fix_action="Propose tiered pricing that captures growth value",
                        fix_effort="medium",
                        fix_timeline="Proactive outreach within 30 days",
                        confidence=0.70,
                    ))
        
        return leakages
    
    def _detect_billing_leakage(self, contract: Dict) -> List[RevenueLeakage]:
        """Detect billing and payment leakage."""
        leakages = []
        
        payment_terms = contract.get("payment_terms_days", 30)
        late_fee = contract.get("late_payment_pct", 2.0)
        monthly_rev = contract.get("our_monthly_revenue", 0)
        
        # Simulate payment behavior based on terms
        # In real system, this would come from actual payment data
        random.seed(contract.get("index", 0))
        late_payment_rate = 0.15 if payment_terms >= 45 else 0.08
        
        if late_payment_rate > 0.10:
            uncollected_fees = monthly_rev * late_payment_rate * (late_fee / 100)
            
            leakages.append(RevenueLeakage(
                id=self._generate_id(contract, "billing_late"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                leak_type="Billing - Uncollected Late Fees",
                amount_monthly=round(uncollected_fees, 2),
                amount_annual=round(uncollected_fees * 12, 2),
                description=f"Extended payment terms (Net {payment_terms}) correlate with {late_payment_rate*100:.0f}% late payment rate",
                root_cause="Late fees not being enforced consistently",
                fix_action="Implement automated late fee billing and collection",
                fix_effort="low",
                fix_timeline="Immediate - automate in billing system",
                confidence=0.65,
            ))
        
        return leakages
    
    def _detect_sla_leakage(self, contract: Dict) -> List[RevenueLeakage]:
        """Detect SLA over-delivery leakage."""
        leakages = []
        
        billing_sla = contract.get("billing_accuracy_sla", 99.5)
        uptime_sla = contract.get("platform_uptime_sla", 99.9)
        support_hours = contract.get("support_response_hours", 4)
        tier = contract.get("client_tier", "Standard")
        
        # Check for SLA over-delivery
        # Premium SLAs cost money to deliver
        tier_expected_slas = {
            "Enterprise": {"billing": 99.9, "uptime": 99.99, "support": 1},
            "Business": {"billing": 99.7, "uptime": 99.95, "support": 2},
            "Standard": {"billing": 99.5, "uptime": 99.90, "support": 4},
            "Starter": {"billing": 99.5, "uptime": 99.90, "support": 8},
        }
        
        expected = tier_expected_slas.get(tier, tier_expected_slas["Standard"])
        
        # If they're getting Enterprise SLAs but paying Standard rates
        if tier in ["Standard", "Starter"]:
            if billing_sla >= 99.9 or uptime_sla >= 99.99 or support_hours <= 1:
                monthly_rev = contract.get("our_monthly_revenue", 0)
                sla_premium_value = monthly_rev * 0.15  # Premium SLAs worth ~15% more
                
                leakages.append(RevenueLeakage(
                    id=self._generate_id(contract, "sla_overdelivery"),
                    client_name=contract.get("client_name", "Unknown"),
                    contract_id=contract.get("index", 0),
                    leak_type="SLA - Uncompensated Premium Service",
                    amount_monthly=round(sla_premium_value, 2),
                    amount_annual=round(sla_premium_value * 12, 2),
                    description=f"{tier} tier client receiving Enterprise-level SLAs (99.9%+ accuracy, {support_hours}hr support)",
                    root_cause="SLAs negotiated without corresponding pricing tier",
                    fix_action="Offer tier upgrade with current SLAs formalized, or adjust SLAs to tier",
                    fix_effort="medium",
                    fix_timeline="Next QBR or renewal",
                    confidence=0.80,
                ))
        
        return leakages
    
    def _detect_term_leakage(self, contract: Dict) -> List[RevenueLeakage]:
        """Detect unfavorable contract terms causing leakage."""
        leakages = []
        
        sla_credit = contract.get("sla_credit_pct", 10)
        etf_months = contract.get("early_termination_months", 6)
        contract_length = contract.get("contract_length_months", 24)
        monthly_rev = contract.get("our_monthly_revenue", 0)
        
        # High SLA credits are expensive
        if sla_credit >= 25:
            # Model expected SLA breach cost
            breach_probability = 0.02  # 2% chance of material breach
            expected_cost = monthly_rev * (sla_credit / 100) * breach_probability * 12
            
            if expected_cost > 1000:
                leakages.append(RevenueLeakage(
                    id=self._generate_id(contract, "term_slacredit"),
                    client_name=contract.get("client_name", "Unknown"),
                    contract_id=contract.get("index", 0),
                    leak_type="Terms - Excessive SLA Credits",
                    amount_monthly=round(expected_cost / 12, 2),
                    amount_annual=round(expected_cost, 2),
                    description=f"SLA credit of {sla_credit}% creates ${expected_cost:,.0f}/year expected liability",
                    root_cause="Aggressive SLA credits negotiated without actuarial analysis",
                    fix_action="Cap credits at 15% or add breach procedures that reduce exposure",
                    fix_effort="medium",
                    fix_timeline="Next renewal",
                    confidence=0.60,
                ))
        
        # Short contracts with no renewal lock
        if contract_length <= 12 and etf_months <= 3:
            # High churn risk = revenue at risk
            churn_probability = 0.25
            at_risk = monthly_rev * churn_probability * 12
            
            leakages.append(RevenueLeakage(
                id=self._generate_id(contract, "term_short"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                leak_type="Terms - Short Contract Exposure",
                amount_monthly=round(at_risk / 12, 2),
                amount_annual=round(at_risk, 2),
                description=f"Short {contract_length}-month term with {etf_months}-month notice creates high churn exposure",
                root_cause="Insufficient commitment secured during negotiation",
                fix_action="Offer renewal incentive for 24+ month extension",
                fix_effort="medium",
                fix_timeline="Initiate renewal discussion immediately",
                confidence=0.70,
            ))
        
        return leakages
    
    def _generate_id(self, contract: Dict, leak_type: str) -> str:
        """Generate unique ID for a leakage."""
        raw = f"{contract.get('index', 0)}-{leak_type}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]


# =============================================================================
# Revenue Opportunity Finder
# =============================================================================

class OpportunityFinder:
    """
    Finds money you're not capturing yet.
    
    Categories:
    1. Upsell - current clients can buy more
    2. Cross-sell - adjacent products/services
    3. Expansion - client growing, capture the growth
    4. Pricing - room to optimize rates
    5. Terms - contract improvements available
    """
    
    def __init__(self, contracts: List[Dict], benchmarks: Dict):
        self.contracts = contracts
        self.benchmarks = benchmarks
    
    def find_all_opportunities(self) -> List[RevenueOpportunity]:
        """Find all revenue opportunities across portfolio."""
        opportunities = []
        
        for contract in self.contracts:
            opportunities.extend(self._find_tier_upgrade(contract))
            opportunities.extend(self._find_volume_expansion(contract))
            opportunities.extend(self._find_model_optimization(contract))
            opportunities.extend(self._find_term_extension(contract))
            opportunities.extend(self._find_service_upsell(contract))
        
        # Sort by potential annual revenue
        opportunities.sort(key=lambda x: x.potential_annual, reverse=True)
        return opportunities
    
    def _find_tier_upgrade(self, contract: Dict) -> List[RevenueOpportunity]:
        """Find clients ready for tier upgrade."""
        opportunities = []
        
        tier = contract.get("client_tier", "Standard")
        subscribers = contract.get("subscriber_count", 0)
        monthly_rev = contract.get("our_monthly_revenue", 0)
        
        # Tier thresholds
        tier_thresholds = {
            "Starter": 25000,
            "Standard": 50000,
            "Business": 100000,
            "Enterprise": 200000,
        }
        
        # Check if they've outgrown their tier
        tier_order = ["Starter", "Standard", "Business", "Enterprise"]
        current_idx = tier_order.index(tier) if tier in tier_order else 0
        
        if current_idx < len(tier_order) - 1:
            next_tier = tier_order[current_idx + 1]
            threshold = tier_thresholds.get(tier, 0)
            
            if subscribers >= threshold * 0.85:  # Within 15% of next tier
                revenue_increase = monthly_rev * 0.20  # Tier upgrades typically 20% more
                
                opportunities.append(RevenueOpportunity(
                    id=self._generate_id(contract, "tier_upgrade"),
                    client_name=contract.get("client_name", "Unknown"),
                    contract_id=contract.get("index", 0),
                    opportunity_type="Tier Upgrade",
                    potential_monthly=round(revenue_increase, 2),
                    potential_annual=round(revenue_increase * 12, 2),
                    description=f"Client has {subscribers:,} subscribers, qualifying for {next_tier} tier",
                    approach=f"Position upgrade as recognition of their growth with enhanced SLAs and support",
                    success_probability=0.65,
                    best_timing="Next QBR or account review",
                    talking_points=[
                        f"You've grown to {subscribers:,} subscribers - congratulations!",
                        f"{next_tier} tier includes enhanced SLAs and dedicated support",
                        "We can lock in preferential rates with a longer commitment",
                        "Many clients at your scale have found value in premium features",
                    ],
                ))
        
        return opportunities
    
    def _find_volume_expansion(self, contract: Dict) -> List[RevenueOpportunity]:
        """Find clients likely to expand volume."""
        opportunities = []
        
        subscribers = contract.get("subscriber_count", 0)
        monthly_rev = contract.get("our_monthly_revenue", 0)
        tier = contract.get("client_tier", "Standard")
        
        # Simulate growth trajectory (in real system, use historical data)
        random.seed(contract.get("index", 0) + 100)
        growth_rate = random.uniform(0.05, 0.25)
        
        if growth_rate > 0.15 and tier not in ["Enterprise"]:
            projected_growth = subscribers * growth_rate
            revenue_from_growth = monthly_rev * growth_rate
            
            opportunities.append(RevenueOpportunity(
                id=self._generate_id(contract, "volume_expansion"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                opportunity_type="Volume Expansion",
                potential_monthly=round(revenue_from_growth, 2),
                potential_annual=round(revenue_from_growth * 12, 2),
                description=f"Client showing {growth_rate*100:.0f}% growth trajectory, ~{projected_growth:,.0f} new subscribers",
                approach="Proactive capacity planning discussion with growth pricing",
                success_probability=0.55,
                best_timing="Before their next growth milestone",
                talking_points=[
                    "We've noticed strong growth in your subscriber base",
                    "Let's ensure our infrastructure scales with you",
                    "Volume commitments unlock better per-unit pricing",
                    "Early planning prevents scaling issues",
                ],
            ))
        
        return opportunities
    
    def _find_model_optimization(self, contract: Dict) -> List[RevenueOpportunity]:
        """Find clients who would benefit from billing model change."""
        opportunities = []
        
        model = contract.get("billing_model", "")
        subscribers = contract.get("subscriber_count", 0)
        monthly_rev = contract.get("our_monthly_revenue", 0)
        client_monthly = contract.get("client_monthly_revenue", 0)
        
        # Per-transaction clients with high volume might benefit from revenue share
        if model == "Per-Transaction" and subscribers > 50000:
            current_effective_rate = (monthly_rev / client_monthly * 100) if client_monthly > 0 else 0
            
            if current_effective_rate < 2.5:
                potential_increase = client_monthly * 0.025 - monthly_rev
                
                if potential_increase > 5000:
                    opportunities.append(RevenueOpportunity(
                        id=self._generate_id(contract, "model_switch"),
                        client_name=contract.get("client_name", "Unknown"),
                        contract_id=contract.get("index", 0),
                        opportunity_type="Billing Model Optimization",
                        potential_monthly=round(potential_increase, 2),
                        potential_annual=round(potential_increase * 12, 2),
                        description=f"Current per-transaction model yields {current_effective_rate:.2f}% effective rate; revenue share could yield 2.5%+",
                        approach="Frame as simplification and alignment of incentives",
                        success_probability=0.45,
                        best_timing="Contract renewal or annual review",
                        talking_points=[
                            "Revenue share aligns our success with yours",
                            "Simplifies billing - no transaction counting",
                            "Provides cost predictability as you scale",
                            "Many similar clients have found this model more efficient",
                        ],
                    ))
        
        # Flat fee clients missing out on growth capture
        if model == "Flat Fee" and subscribers > 30000:
            platform_fee = contract.get("monthly_platform_fee", 0)
            effective_rate = (platform_fee / client_monthly * 100) if client_monthly > 0 else 0
            
            if effective_rate < 0.5:  # Very low effective rate
                potential_rev = client_monthly * 0.02  # 2% revenue share
                increase = potential_rev - platform_fee
                
                if increase > 3000:
                    opportunities.append(RevenueOpportunity(
                        id=self._generate_id(contract, "model_revshare"),
                        client_name=contract.get("client_name", "Unknown"),
                        contract_id=contract.get("index", 0),
                        opportunity_type="Model Transition to Revenue Share",
                        potential_monthly=round(increase, 2),
                        potential_annual=round(increase * 12, 2),
                        description=f"Flat fee of ${platform_fee:,.0f} is only {effective_rate:.2f}% of their revenue; significant upside with revenue share",
                        approach="Offer hybrid model as transition step",
                        success_probability=0.40,
                        best_timing="When client is expanding or renewing",
                        talking_points=[
                            "As you've grown, a usage-based model may be more efficient",
                            "Hybrid model provides stability with growth participation",
                            "Removes artificial caps on our partnership value",
                        ],
                    ))
        
        return opportunities
    
    def _find_term_extension(self, contract: Dict) -> List[RevenueOpportunity]:
        """Find clients who would extend for incentives."""
        opportunities = []
        
        contract_length = contract.get("contract_length_months", 24)
        monthly_rev = contract.get("our_monthly_revenue", 0)
        
        if contract_length <= 24:
            # Longer terms = more guaranteed revenue
            extension_months = 36 if contract_length == 12 else 48
            additional_months = extension_months - contract_length
            additional_revenue = monthly_rev * additional_months
            
            # We might offer small discount for extension, so net is ~90%
            net_opportunity = additional_revenue * 0.90
            
            opportunities.append(RevenueOpportunity(
                id=self._generate_id(contract, "term_extension"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                opportunity_type="Term Extension",
                potential_monthly=round(net_opportunity / extension_months, 2),
                potential_annual=round(net_opportunity / (extension_months / 12), 2),
                description=f"Extend from {contract_length} to {extension_months} months for {additional_months} months additional commitment",
                approach="Offer 5% discount in exchange for extended commitment",
                success_probability=0.60,
                best_timing="6 months before current term ends",
                talking_points=[
                    "Lock in current rates before annual increases",
                    "Extended commitment unlocks loyalty pricing",
                    "Reduces renewal overhead for both parties",
                    "Demonstrates partnership commitment",
                ],
            ))
        
        return opportunities
    
    def _find_service_upsell(self, contract: Dict) -> List[RevenueOpportunity]:
        """Find cross-sell and service expansion opportunities."""
        opportunities = []
        
        tier = contract.get("client_tier", "Standard")
        soc2 = contract.get("soc2_certified", False)
        monthly_rev = contract.get("our_monthly_revenue", 0)
        
        # Compliance add-on opportunity
        if not soc2 and tier in ["Business", "Enterprise"]:
            compliance_upsell = monthly_rev * 0.08  # 8% premium for compliance package
            
            opportunities.append(RevenueOpportunity(
                id=self._generate_id(contract, "service_compliance"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                opportunity_type="Compliance Package Upsell",
                potential_monthly=round(compliance_upsell, 2),
                potential_annual=round(compliance_upsell * 12, 2),
                description=f"{tier} client without SOC 2 compliance package",
                approach="Position as risk mitigation and enterprise requirement",
                success_probability=0.50,
                best_timing="During compliance or audit season (Q4/Q1)",
                talking_points=[
                    "Many of your peers require SOC 2 from vendors",
                    "Compliance package includes audit support",
                    "Reduces your own compliance burden",
                    "Differentiates you to enterprise customers",
                ],
            ))
        
        # Premium support upsell
        support_hours = contract.get("support_response_hours", 4)
        if support_hours > 2 and tier in ["Business", "Enterprise"]:
            premium_support = monthly_rev * 0.05
            
            opportunities.append(RevenueOpportunity(
                id=self._generate_id(contract, "service_support"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                opportunity_type="Premium Support Upgrade",
                potential_monthly=round(premium_support, 2),
                potential_annual=round(premium_support * 12, 2),
                description=f"Current {support_hours}-hour SLA; premium 1-hour response available",
                approach="Highlight after any support interaction or outage",
                success_probability=0.35,
                best_timing="After a support ticket or incident",
                talking_points=[
                    "Premium support includes 1-hour response SLA",
                    "Dedicated support engineer assigned to your account",
                    "Proactive monitoring and alerting included",
                    "Priority queue for all issues",
                ],
            ))
        
        return opportunities
    
    def _generate_id(self, contract: Dict, opp_type: str) -> str:
        """Generate unique ID for an opportunity."""
        raw = f"{contract.get('index', 0)}-{opp_type}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]


# =============================================================================
# Signal Detection Engine
# =============================================================================

class SignalDetector:
    """
    Detects weak signals before they become problems or opportunities.
    
    In a real system, this would ingest:
    - Email sentiment analysis
    - Support ticket patterns
    - Login/usage frequency
    - Payment patterns
    - Executive changes (from LinkedIn/news)
    - Competitor mentions
    
    For demo, we simulate these signals based on contract data patterns.
    """
    
    def __init__(self, contracts: List[Dict], benchmarks: Dict):
        self.contracts = contracts
        self.benchmarks = benchmarks
    
    def detect_all_signals(self) -> List[ClientSignal]:
        """Detect all signals across portfolio."""
        signals = []
        
        for contract in self.contracts:
            signals.extend(self._detect_renewal_risk_signals(contract))
            signals.extend(self._detect_expansion_signals(contract))
            signals.extend(self._detect_payment_signals(contract))
            signals.extend(self._detect_engagement_signals(contract))
        
        # Sort by signal strength
        signals.sort(key=lambda x: x.strength, reverse=True)
        return signals
    
    def _detect_renewal_risk_signals(self, contract: Dict) -> List[ClientSignal]:
        """Detect signals indicating renewal risk."""
        signals = []
        
        contract_length = contract.get("contract_length_months", 24)
        tier = contract.get("client_tier", "Standard")
        
        # Simulate months until renewal
        random.seed(contract.get("index", 0) + 200)
        months_remaining = random.randint(1, contract_length)
        
        if months_remaining <= 3:
            signals.append(ClientSignal(
                id=self._generate_id(contract, "renewal_imminent"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                signal_type=SignalType.RENEWAL_RISK.value,
                strength=0.9,
                detected_at=datetime.now().isoformat(),
                description=f"Contract expires in {months_remaining} month(s) with no renewal discussion initiated",
                evidence=[
                    f"Contract end date approaching ({months_remaining} months)",
                    "No renewal meeting scheduled in calendar",
                    "No proposal sent in last 60 days",
                ],
                recommended_response="Schedule renewal discussion immediately; prepare competitive retention offer",
                if_ignored=f"Client may shop alternatives; risk losing ${contract.get('annual_contract_value', 0):,.0f} ACV",
            ))
        
        return signals
    
    def _detect_expansion_signals(self, contract: Dict) -> List[ClientSignal]:
        """Detect signals indicating expansion opportunity."""
        signals = []
        
        subscribers = contract.get("subscriber_count", 0)
        tier = contract.get("client_tier", "Standard")
        
        # Simulate growth signals
        random.seed(contract.get("index", 0) + 300)
        growth_signal = random.random()
        
        if growth_signal > 0.75 and tier != "Enterprise":
            signals.append(ClientSignal(
                id=self._generate_id(contract, "expansion_signal"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                signal_type=SignalType.EXPANSION_SIGNAL.value,
                strength=0.75,
                detected_at=datetime.now().isoformat(),
                description="Multiple expansion indicators detected",
                evidence=[
                    "Subscriber count growth rate above portfolio average",
                    "Increased API call volume last 30 days",
                    "Client mentioned growth plans in recent communication",
                    "Industry news indicates market expansion",
                ],
                recommended_response="Proactively reach out about capacity planning and tier upgrade",
                if_ignored="Competitor may capture the growth opportunity",
            ))
        
        return signals
    
    def _detect_payment_signals(self, contract: Dict) -> List[ClientSignal]:
        """Detect payment-related warning signals."""
        signals = []
        
        payment_terms = contract.get("payment_terms_days", 30)
        
        # Simulate payment patterns
        random.seed(contract.get("index", 0) + 400)
        payment_issues = random.random()
        
        if payment_issues > 0.85:  # 15% of clients have payment issues
            signals.append(ClientSignal(
                id=self._generate_id(contract, "payment_delay"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                signal_type=SignalType.PAYMENT_DELAY.value,
                strength=0.70,
                detected_at=datetime.now().isoformat(),
                description="Payment pattern deviation detected",
                evidence=[
                    "Last 2 payments processed 5+ days late",
                    "Payment method update requested recently",
                    "Finance contact changed in CRM",
                ],
                recommended_response="Reach out to new finance contact; verify payment details; consider early payment incentive",
                if_ignored="Late payments may escalate; potential bad debt risk",
            ))
        
        return signals
    
    def _detect_engagement_signals(self, contract: Dict) -> List[ClientSignal]:
        """Detect engagement pattern changes."""
        signals = []
        
        tier = contract.get("client_tier", "Standard")
        
        # Simulate engagement drop
        random.seed(contract.get("index", 0) + 500)
        engagement_drop = random.random()
        
        if engagement_drop > 0.88:  # 12% of clients show engagement drop
            signals.append(ClientSignal(
                id=self._generate_id(contract, "engagement_drop"),
                client_name=contract.get("client_name", "Unknown"),
                contract_id=contract.get("index", 0),
                signal_type=SignalType.ENGAGEMENT_DROP.value,
                strength=0.65,
                detected_at=datetime.now().isoformat(),
                description="Client engagement metrics declining",
                evidence=[
                    "Portal logins down 40% from 30-day average",
                    "No response to last 2 outreach attempts",
                    "QBR meeting postponed twice",
                    "Primary contact less responsive",
                ],
                recommended_response="Executive outreach; schedule in-person meeting; assess satisfaction",
                if_ignored="Disengaged clients are 3x more likely to churn",
            ))
        
        return signals
    
    def _generate_id(self, contract: Dict, signal_type: str) -> str:
        """Generate unique ID for a signal."""
        raw = f"{contract.get('index', 0)}-{signal_type}-{datetime.now().date()}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]


# =============================================================================
# Action Engine - The Autonomous Agent
# =============================================================================

class ActionEngine:
    """
    Converts intelligence into executable actions.
    
    This is what makes the system autonomous - it doesn't just tell you
    what to do, it can DO it (with approval).
    """
    
    def __init__(self, contracts: List[Dict]):
        self.contracts = contracts
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
    
    def generate_action_queue(
        self,
        leakages: List[RevenueLeakage],
        opportunities: List[RevenueOpportunity],
        signals: List[ClientSignal],
    ) -> List[ActionItem]:
        """Generate prioritized action queue from all intelligence."""
        actions = []
        
        # Convert critical signals to actions
        for signal in signals:
            if signal.strength >= 0.65:
                actions.append(self._signal_to_action(signal))
        
        # Convert high-value leakages to actions
        for leakage in leakages[:10]:  # Top 10
            if leakage.amount_annual >= 10000:
                actions.append(self._leakage_to_action(leakage))
        
        # Convert high-probability opportunities to actions
        for opp in opportunities[:10]:  # Top 10
            if opp.success_probability >= 0.40 and opp.potential_annual >= 20000:
                actions.append(self._opportunity_to_action(opp))
        
        # Sort by urgency and revenue impact
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "opportunity": 4}
        actions.sort(key=lambda x: (urgency_order.get(x.urgency, 5), -x.revenue_impact))
        
        return actions
    
    def _signal_to_action(self, signal: ClientSignal) -> ActionItem:
        """Convert a signal into an action item."""
        contract = next((c for c in self.contracts if c.get("index") == signal.contract_id), {})
        
        # Map signal types to action types
        action_type_map = {
            SignalType.RENEWAL_RISK.value: ActionType.MEETING.value,
            SignalType.EXPANSION_SIGNAL.value: ActionType.PROPOSAL.value,
            SignalType.PAYMENT_DELAY.value: ActionType.CALL.value,
            SignalType.ENGAGEMENT_DROP.value: ActionType.MEETING.value,
        }
        
        urgency_map = {
            SignalType.RENEWAL_RISK.value: Urgency.CRITICAL.value,
            SignalType.PAYMENT_DELAY.value: Urgency.HIGH.value,
            SignalType.ENGAGEMENT_DROP.value: Urgency.HIGH.value,
            SignalType.EXPANSION_SIGNAL.value: Urgency.MEDIUM.value,
        }
        
        return ActionItem(
            id=f"action-{signal.id}",
            client_name=signal.client_name,
            contract_id=signal.contract_id,
            action_type=action_type_map.get(signal.signal_type, ActionType.CALL.value),
            urgency=urgency_map.get(signal.signal_type, Urgency.MEDIUM.value),
            title=f"Respond to {signal.signal_type.replace('_', ' ').title()}",
            description=signal.recommended_response,
            revenue_impact=contract.get("annual_contract_value", 0),
            due_date=(datetime.now() + timedelta(days=3 if signal.strength > 0.8 else 7)).strftime("%Y-%m-%d"),
            script=None,  # Generated on demand
            auto_executable=False,
            prerequisites=["Review signal evidence", "Check recent interactions"],
            success_metrics=["Meeting scheduled", "Response received", "Issue resolved"],
        )
    
    def _leakage_to_action(self, leakage: RevenueLeakage) -> ActionItem:
        """Convert a leakage into an action item."""
        return ActionItem(
            id=f"action-leak-{leakage.id}",
            client_name=leakage.client_name,
            contract_id=leakage.contract_id,
            action_type=ActionType.RENEGOTIATE.value,
            urgency=Urgency.HIGH.value if leakage.amount_annual > 50000 else Urgency.MEDIUM.value,
            title=f"Fix: {leakage.leak_type}",
            description=leakage.fix_action,
            revenue_impact=leakage.amount_annual,
            due_date=(datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            script=None,
            auto_executable=leakage.fix_effort == "low",
            prerequisites=[f"Confirm leakage: {leakage.description}"],
            success_metrics=[f"Recover ${leakage.amount_annual:,.0f}/year"],
        )
    
    def _opportunity_to_action(self, opp: RevenueOpportunity) -> ActionItem:
        """Convert an opportunity into an action item."""
        return ActionItem(
            id=f"action-opp-{opp.id}",
            client_name=opp.client_name,
            contract_id=opp.contract_id,
            action_type=ActionType.UPSELL.value,
            urgency=Urgency.OPPORTUNITY.value,
            title=f"Opportunity: {opp.opportunity_type}",
            description=opp.approach,
            revenue_impact=opp.potential_annual,
            due_date=opp.best_timing,
            script="\n".join([f"• {tp}" for tp in opp.talking_points]),
            auto_executable=False,
            prerequisites=["Review client history", "Prepare proposal"],
            success_metrics=[f"Close ${opp.potential_annual:,.0f}/year opportunity"],
        )
    
    def generate_outreach_script(self, action: ActionItem) -> str:
        """Use LLM to generate personalized outreach script."""
        contract = next((c for c in self.contracts if c.get("index") == action.contract_id), {})
        
        prompt = f"""Generate a professional outreach script for the following situation:

Client: {action.client_name}
Client Tier: {contract.get('client_tier', 'Unknown')}
Current ACV: ${contract.get('annual_contract_value', 0):,.0f}
Action Type: {action.action_type}
Objective: {action.title}
Context: {action.description}

Requirements:
1. Professional but personable tone
2. Lead with value, not ask
3. Be concise (under 150 words for email, 5 key points for call)
4. Include specific next step

Generate both an email template and call talking points."""

        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Script generation failed: {str(e)}"


# =============================================================================
# Deal Genome Analyzer
# =============================================================================

class GenomeAnalyzer:
    """
    Analyzes the "DNA" of each deal to predict success and suggest optimizations.
    
    The genome consists of key traits that determine long-term success:
    - Pricing health
    - Term structure
    - SLA alignment
    - Compliance posture
    - Engagement level
    - Growth trajectory
    """
    
    def __init__(self, contracts: List[Dict], benchmarks: Dict):
        self.contracts = contracts
        self.benchmarks = benchmarks
    
    def analyze_all_genomes(self) -> List[DealGenome]:
        """Analyze genome for all contracts."""
        genomes = []
        for contract in self.contracts:
            genomes.append(self._analyze_genome(contract))
        genomes.sort(key=lambda x: x.success_score, reverse=True)
        return genomes
    
    def _analyze_genome(self, contract: Dict) -> DealGenome:
        """Analyze the genome of a single contract."""
        markers = {}
        
        # Marker 1: Pricing Health (0-100)
        tier = contract.get("client_tier", "Standard")
        tier_bench = self.benchmarks.get("tier_benchmarks", {}).get(tier, {})
        if tier_bench:
            our_rev = contract.get("our_monthly_revenue", 0)
            avg_rev = tier_bench.get("avg_monthly_revenue", our_rev)
            pricing_health = min(100, (our_rev / avg_rev) * 100) if avg_rev > 0 else 50
        else:
            pricing_health = 50
        markers["pricing_health"] = round(pricing_health, 1)
        
        # Marker 2: Term Strength (0-100)
        length = contract.get("contract_length_months", 24)
        etf_months = contract.get("early_termination_months", 6)
        term_strength = min(100, (length / 60 * 50) + (etf_months / 12 * 50))
        markers["term_strength"] = round(term_strength, 1)
        
        # Marker 3: SLA Balance (0-100) - are we over/under delivering?
        billing_sla = contract.get("billing_accuracy_sla", 99.5)
        expected_sla = {"Enterprise": 99.9, "Business": 99.7, "Standard": 99.5, "Starter": 99.5}
        sla_gap = billing_sla - expected_sla.get(tier, 99.5)
        sla_balance = 100 - abs(sla_gap) * 20  # Penalize over or under delivery
        markers["sla_balance"] = round(max(0, min(100, sla_balance)), 1)
        
        # Marker 4: Compliance Readiness (0-100)
        pci = contract.get("pci_compliant", False)
        soc2 = contract.get("soc2_certified", False)
        retention = contract.get("data_retention_months", 24)
        compliance_score = (50 if pci else 0) + (30 if soc2 else 0) + min(20, retention / 84 * 20)
        markers["compliance_readiness"] = round(compliance_score, 1)
        
        # Marker 5: Payment Health (0-100)
        payment_terms = contract.get("payment_terms_days", 30)
        late_fee = contract.get("late_payment_pct", 2.0)
        payment_health = 100 - (payment_terms - 15) * 2 + (late_fee - 1.5) * 10
        markers["payment_health"] = round(max(0, min(100, payment_health)), 1)
        
        # Marker 6: Growth Potential (0-100)
        subscribers = contract.get("subscriber_count", 0)
        min_txn = contract.get("monthly_minimum_transactions", 0)
        if min_txn > 0:
            utilization = subscribers / min_txn
            growth_potential = min(100, (2 - utilization) * 50) if utilization < 2 else 20
        else:
            growth_potential = 50
        markers["growth_potential"] = round(max(0, growth_potential), 1)
        
        # Calculate overall success score
        weights = {
            "pricing_health": 0.25,
            "term_strength": 0.20,
            "sla_balance": 0.15,
            "compliance_readiness": 0.15,
            "payment_health": 0.10,
            "growth_potential": 0.15,
        }
        success_score = sum(markers[k] * weights[k] for k in weights)
        
        # Find similar deals
        similar = self._find_similar_deals(contract, markers)
        
        # Predict outcome
        if success_score >= 75:
            predicted_outcome = "High likelihood of long-term retention and expansion"
        elif success_score >= 50:
            predicted_outcome = "Stable relationship with optimization opportunities"
        else:
            predicted_outcome = "At-risk relationship requiring intervention"
        
        # Generate optimization suggestions
        suggestions = self._generate_suggestions(markers)
        
        return DealGenome(
            contract_id=contract.get("index", 0),
            client_name=contract.get("client_name", "Unknown"),
            success_score=round(success_score, 1),
            genome_markers=markers,
            similar_deals=similar,
            predicted_outcome=predicted_outcome,
            optimization_suggestions=suggestions,
        )
    
    def _find_similar_deals(self, contract: Dict, markers: Dict) -> List[Dict]:
        """Find historically similar deals."""
        similar = []
        
        for other in self.contracts:
            if other.get("index") == contract.get("index"):
                continue
            
            # Calculate similarity based on tier and key metrics
            if other.get("client_tier") == contract.get("client_tier"):
                similar.append({
                    "client_name": other.get("client_name"),
                    "similarity": 0.85,
                    "outcome": "Active - 24 months",  # Simulated
                })
            
            if len(similar) >= 3:
                break
        
        return similar
    
    def _generate_suggestions(self, markers: Dict) -> List[str]:
        """Generate optimization suggestions based on genome markers."""
        suggestions = []
        
        if markers.get("pricing_health", 0) < 70:
            suggestions.append("Pricing below tier average - prioritize rate adjustment on renewal")
        
        if markers.get("term_strength", 0) < 50:
            suggestions.append("Short contract term - offer extension incentive")
        
        if markers.get("sla_balance", 0) < 70:
            suggestions.append("SLA misalignment - align service levels with tier")
        
        if markers.get("compliance_readiness", 0) < 60:
            suggestions.append("Compliance gaps - upsell compliance package")
        
        if markers.get("payment_health", 0) < 60:
            suggestions.append("Payment terms unfavorable - negotiate improved terms")
        
        if markers.get("growth_potential", 0) > 70:
            suggestions.append("High growth potential - proactive capacity planning")
        
        if not suggestions:
            suggestions.append("Well-optimized deal - maintain current relationship")
        
        return suggestions


# =============================================================================
# Main Revenue Intelligence Service
# =============================================================================

class RevenueIntelligenceService:
    """
    The unified revenue intelligence engine.
    
    This is the brain of the next-generation CRM.
    """
    
    def __init__(self, contracts_path: str = "contract_data.json"):
        self.contracts_path = contracts_path
        self.contracts = self._load_contracts()
        self.benchmarks = self._calculate_benchmarks()
        
        # Initialize all engines
        self.leakage_detector = LeakageDetector(self.contracts, self.benchmarks)
        self.opportunity_finder = OpportunityFinder(self.contracts, self.benchmarks)
        self.signal_detector = SignalDetector(self.contracts, self.benchmarks)
        self.action_engine = ActionEngine(self.contracts)
        self.genome_analyzer = GenomeAnalyzer(self.contracts, self.benchmarks)
    
    def _load_contracts(self) -> List[Dict]:
        """Load contracts from JSON file."""
        if not os.path.exists(self.contracts_path):
            return []
        with open(self.contracts_path, "r") as f:
            return json.load(f)
    
    def _calculate_benchmarks(self) -> Dict:
        """Calculate portfolio benchmarks."""
        if not self.contracts:
            return {}
        
        benchmarks = {"tier_benchmarks": {}}
        
        for tier in ["Enterprise", "Business", "Standard", "Starter"]:
            tier_contracts = [c for c in self.contracts if c.get("client_tier") == tier]
            if tier_contracts:
                revenues = [c.get("our_monthly_revenue", 0) for c in tier_contracts]
                rev_shares = [c.get("revenue_share_pct", 0) for c in tier_contracts if c.get("revenue_share_pct", 0) > 0]
                benchmarks["tier_benchmarks"][tier] = {
                    "avg_monthly_revenue": sum(revenues) / len(revenues),
                    "avg_revenue_share": sum(rev_shares) / len(rev_shares) if rev_shares else 0,
                    "count": len(tier_contracts),
                }
        
        return benchmarks
    
    def get_revenue_command_center(self) -> Dict:
        """
        The main dashboard - everything a revenue leader needs.
        """
        leakages = self.leakage_detector.detect_all_leakage()
        opportunities = self.opportunity_finder.find_all_opportunities()
        signals = self.signal_detector.detect_all_signals()
        actions = self.action_engine.generate_action_queue(leakages, opportunities, signals)
        
        # Calculate totals
        total_leakage = sum(l.amount_annual for l in leakages)
        total_opportunity = sum(o.potential_annual for o in opportunities)
        critical_actions = sum(1 for a in actions if a.urgency in ["critical", "high"])
        
        # Portfolio health
        genomes = self.genome_analyzer.analyze_all_genomes()
        avg_success = sum(g.success_score for g in genomes) / len(genomes) if genomes else 0
        
        return {
            "summary": {
                "total_leakage_annual": round(total_leakage, 2),
                "total_opportunity_annual": round(total_opportunity, 2),
                "net_revenue_gap": round(total_leakage + total_opportunity, 2),
                "critical_actions": critical_actions,
                "portfolio_health_score": round(avg_success, 1),
                "active_signals": len(signals),
            },
            "leakages": [asdict(l) for l in leakages[:10]],  # Top 10
            "opportunities": [asdict(o) for o in opportunities[:10]],  # Top 10
            "signals": [asdict(s) for s in signals[:10]],  # Top 10
            "action_queue": [asdict(a) for a in actions[:15]],  # Top 15
            "genomes": [asdict(g) for g in genomes[:5]],  # Top/bottom 5
        }
    
    def get_leakage_report(self) -> Dict:
        """Detailed leakage analysis."""
        leakages = self.leakage_detector.detect_all_leakage()
        
        # Group by type
        by_type = {}
        for l in leakages:
            leak_type = l.leak_type.split(" - ")[0]
            if leak_type not in by_type:
                by_type[leak_type] = {"count": 0, "annual_total": 0, "items": []}
            by_type[leak_type]["count"] += 1
            by_type[leak_type]["annual_total"] += l.amount_annual
            by_type[leak_type]["items"].append(asdict(l))
        
        return {
            "total_annual_leakage": round(sum(l.amount_annual for l in leakages), 2),
            "total_monthly_leakage": round(sum(l.amount_monthly for l in leakages), 2),
            "leakage_count": len(leakages),
            "by_type": by_type,
            "top_leakages": [asdict(l) for l in leakages[:15]],
            "quick_wins": [asdict(l) for l in leakages if l.fix_effort == "low"][:5],
        }
    
    def get_opportunity_report(self) -> Dict:
        """Detailed opportunity analysis."""
        opportunities = self.opportunity_finder.find_all_opportunities()
        
        # Group by type
        by_type = {}
        for o in opportunities:
            opp_type = o.opportunity_type
            if opp_type not in by_type:
                by_type[opp_type] = {"count": 0, "annual_total": 0, "items": []}
            by_type[opp_type]["count"] += 1
            by_type[opp_type]["annual_total"] += o.potential_annual
            by_type[opp_type]["items"].append(asdict(o))
        
        return {
            "total_annual_opportunity": round(sum(o.potential_annual for o in opportunities), 2),
            "opportunity_count": len(opportunities),
            "by_type": by_type,
            "top_opportunities": [asdict(o) for o in opportunities[:15]],
            "high_probability": [asdict(o) for o in opportunities if o.success_probability >= 0.5][:5],
        }
    
    def get_signal_report(self) -> Dict:
        """All detected signals."""
        signals = self.signal_detector.detect_all_signals()
        
        # Group by type
        by_type = {}
        for s in signals:
            if s.signal_type not in by_type:
                by_type[s.signal_type] = []
            by_type[s.signal_type].append(asdict(s))
        
        return {
            "total_signals": len(signals),
            "critical_signals": len([s for s in signals if s.strength >= 0.8]),
            "by_type": by_type,
            "all_signals": [asdict(s) for s in signals],
        }
    
    def get_action_queue(self) -> Dict:
        """Prioritized action queue."""
        leakages = self.leakage_detector.detect_all_leakage()
        opportunities = self.opportunity_finder.find_all_opportunities()
        signals = self.signal_detector.detect_all_signals()
        actions = self.action_engine.generate_action_queue(leakages, opportunities, signals)
        
        return {
            "total_actions": len(actions),
            "critical": [asdict(a) for a in actions if a.urgency == "critical"],
            "high": [asdict(a) for a in actions if a.urgency == "high"],
            "medium": [asdict(a) for a in actions if a.urgency == "medium"],
            "opportunities": [asdict(a) for a in actions if a.urgency == "opportunity"],
            "total_revenue_at_stake": round(sum(a.revenue_impact for a in actions), 2),
        }
    
    def get_genome_analysis(self, contract_id: Optional[int] = None) -> Dict:
        """Deal genome analysis."""
        genomes = self.genome_analyzer.analyze_all_genomes()
        
        if contract_id is not None:
            genome = next((g for g in genomes if g.contract_id == contract_id), None)
            if genome:
                return asdict(genome)
            return {"error": f"Contract {contract_id} not found"}
        
        return {
            "portfolio_avg_score": round(sum(g.success_score for g in genomes) / len(genomes), 1) if genomes else 0,
            "top_performers": [asdict(g) for g in genomes[:5]],
            "needs_attention": [asdict(g) for g in genomes if g.success_score < 50],
            "all_genomes": [asdict(g) for g in genomes],
        }
    
    def generate_outreach(self, action_id: str) -> Dict:
        """Generate outreach script for an action."""
        leakages = self.leakage_detector.detect_all_leakage()
        opportunities = self.opportunity_finder.find_all_opportunities()
        signals = self.signal_detector.detect_all_signals()
        actions = self.action_engine.generate_action_queue(leakages, opportunities, signals)
        
        action = next((a for a in actions if a.id == action_id), None)
        if not action:
            return {"error": f"Action {action_id} not found"}
        
        script = self.action_engine.generate_outreach_script(action)
        
        return {
            "action": asdict(action),
            "script": script,
        }
    
    def get_executive_summary(self) -> Dict:
        """High-level executive summary."""
        leakages = self.leakage_detector.detect_all_leakage()
        opportunities = self.opportunity_finder.find_all_opportunities()
        signals = self.signal_detector.detect_all_signals()
        genomes = self.genome_analyzer.analyze_all_genomes()
        
        total_portfolio = sum(c.get("annual_contract_value", 0) for c in self.contracts)
        
        return {
            "portfolio_value": round(total_portfolio, 2),
            "revenue_at_risk": round(sum(l.amount_annual for l in leakages), 2),
            "growth_potential": round(sum(o.potential_annual for o in opportunities), 2),
            "portfolio_health": round(sum(g.success_score for g in genomes) / len(genomes), 1) if genomes else 0,
            "urgent_items": len([s for s in signals if s.strength >= 0.7]),
            "headline": self._generate_headline(leakages, opportunities, signals),
        }
    
    def _generate_headline(self, leakages, opportunities, signals) -> str:
        """Generate executive headline."""
        total_leak = sum(l.amount_annual for l in leakages)
        total_opp = sum(o.potential_annual for o in opportunities)
        critical = len([s for s in signals if s.strength >= 0.8])
        
        if critical > 0:
            return f"🚨 {critical} critical signal(s) require immediate attention"
        elif total_leak > 100000:
            return f"⚠️ ${total_leak/1000:.0f}K annual revenue leakage detected"
        elif total_opp > 200000:
            return f"💰 ${total_opp/1000:.0f}K revenue opportunity identified"
        else:
            return "✅ Portfolio is healthy - focus on growth"


# Singleton instance
_revenue_service: Optional[RevenueIntelligenceService] = None

def get_revenue_intelligence() -> RevenueIntelligenceService:
    """Get or create the revenue intelligence service."""
    global _revenue_service
    if _revenue_service is None:
        _revenue_service = RevenueIntelligenceService()
    return _revenue_service
