"""
Contract Intelligence Module for BillFlow
==========================================
Provides AI-powered contract analysis including:
1. Clause Extraction & Structured Knowledge Base
2. Risk Scoring & Red Flag Detection
3. Churn Prediction & Renewal Intelligence
4. What-If Scenario Simulation
5. Natural Language Contract Generation
6. Contract Diff & Version Comparison
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from openai import AzureOpenAI

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
)


# =============================================================================
# Data Models
# =============================================================================

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChurnRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class RiskFlag:
    """A single risk flag identified in a contract."""
    category: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    recommendation: str
    impact_score: int  # 1-25 points added to risk


@dataclass
class ExtractedClause:
    """A structured clause extracted from a contract."""
    clause_type: str
    value: Any
    raw_text: str
    is_standard: bool
    deviation_from_standard: Optional[str] = None


@dataclass
class ContractRiskScore:
    """Complete risk assessment for a contract."""
    contract_id: int
    client_name: str
    overall_score: int  # 0-100, higher = more risk
    risk_level: str
    flags: List[Dict]
    strengths: List[str]
    summary: str


@dataclass 
class ChurnPrediction:
    """Churn risk prediction for a contract."""
    contract_id: int
    client_name: str
    churn_probability: float  # 0-1
    risk_level: str
    risk_factors: List[Dict]
    recommended_actions: List[str]
    optimal_renewal_timing: str
    price_sensitivity: str


@dataclass
class ContractComparison:
    """Comparison between two contracts or versions."""
    contract_a: str
    contract_b: str
    differences: List[Dict]
    summary: str
    financial_impact: Dict


# =============================================================================
# Portfolio Benchmarks (calculated from contract data)
# =============================================================================

class PortfolioBenchmarks:
    """Calculates and stores portfolio-wide benchmarks for comparison."""
    
    def __init__(self, contracts: List[Dict]):
        self.contracts = contracts
        self._calculate_benchmarks()
    
    def _calculate_benchmarks(self):
        if not self.contracts:
            self._set_defaults()
            return
            
        # SLA benchmarks
        slas = [c.get("billing_accuracy_sla", 99.5) for c in self.contracts]
        self.avg_billing_sla = sum(slas) / len(slas)
        self.min_billing_sla = min(slas)
        self.max_billing_sla = max(slas)
        
        uptimes = [c.get("platform_uptime_sla", 99.9) for c in self.contracts]
        self.avg_uptime_sla = sum(uptimes) / len(uptimes)
        
        # Revenue benchmarks by tier
        self.tier_benchmarks = {}
        for tier in ["Enterprise", "Business", "Standard", "Starter"]:
            tier_contracts = [c for c in self.contracts if c.get("client_tier") == tier]
            if tier_contracts:
                revenues = [c.get("our_monthly_revenue", 0) for c in tier_contracts]
                rev_shares = [c.get("revenue_share_pct", 0) for c in tier_contracts if c.get("revenue_share_pct", 0) > 0]
                self.tier_benchmarks[tier] = {
                    "avg_monthly_revenue": sum(revenues) / len(revenues),
                    "avg_revenue_share": sum(rev_shares) / len(rev_shares) if rev_shares else 0,
                    "count": len(tier_contracts),
                }
        
        # Payment terms
        terms = [c.get("payment_terms_days", 30) for c in self.contracts]
        self.avg_payment_terms = sum(terms) / len(terms)
        
        # Contract length
        lengths = [c.get("contract_length_months", 24) for c in self.contracts]
        self.avg_contract_length = sum(lengths) / len(lengths)
        
        # Compliance
        self.pci_compliance_rate = sum(1 for c in self.contracts if c.get("pci_compliant")) / len(self.contracts) * 100
        self.soc2_compliance_rate = sum(1 for c in self.contracts if c.get("soc2_certified")) / len(self.contracts) * 100
    
    def _set_defaults(self):
        self.avg_billing_sla = 99.7
        self.min_billing_sla = 99.5
        self.max_billing_sla = 99.95
        self.avg_uptime_sla = 99.95
        self.tier_benchmarks = {}
        self.avg_payment_terms = 30
        self.avg_contract_length = 24
        self.pci_compliance_rate = 100
        self.soc2_compliance_rate = 70


# =============================================================================
# Risk Scoring Engine
# =============================================================================

class RiskScoringEngine:
    """
    Analyzes contracts and assigns risk scores based on multiple factors.
    Score: 0-100 (0 = minimal risk, 100 = critical risk)
    """
    
    # Risk weights by category
    CATEGORY_WEIGHTS = {
        "sla": 20,
        "compliance": 20,
        "financial": 25,
        "terms": 20,
        "concentration": 15,
    }
    
    def __init__(self, benchmarks: PortfolioBenchmarks):
        self.benchmarks = benchmarks
    
    def score_contract(self, contract: Dict, all_contracts: List[Dict]) -> ContractRiskScore:
        """Generate comprehensive risk score for a contract."""
        flags: List[RiskFlag] = []
        strengths: List[str] = []
        
        # 1. SLA Risk Analysis
        self._analyze_sla_risks(contract, flags, strengths)
        
        # 2. Compliance Risk Analysis
        self._analyze_compliance_risks(contract, flags, strengths)
        
        # 3. Financial Risk Analysis
        self._analyze_financial_risks(contract, all_contracts, flags, strengths)
        
        # 4. Terms & Conditions Risk
        self._analyze_terms_risks(contract, flags, strengths)
        
        # 5. Concentration Risk
        self._analyze_concentration_risks(contract, all_contracts, flags, strengths)
        
        # Calculate overall score
        total_impact = sum(f.impact_score for f in flags)
        overall_score = min(100, total_impact)
        
        # Determine risk level
        if overall_score >= 70:
            risk_level = RiskLevel.CRITICAL
        elif overall_score >= 50:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Generate summary
        summary = self._generate_summary(contract, overall_score, flags, strengths)
        
        return ContractRiskScore(
            contract_id=contract.get("index", 0),
            client_name=contract.get("client_name", "Unknown"),
            overall_score=overall_score,
            risk_level=risk_level.value,
            flags=[asdict(f) for f in flags],
            strengths=strengths,
            summary=summary,
        )
    
    def _analyze_sla_risks(self, contract: Dict, flags: List[RiskFlag], strengths: List[str]):
        """Analyze SLA-related risks."""
        billing_sla = contract.get("billing_accuracy_sla", 99.5)
        uptime_sla = contract.get("platform_uptime_sla", 99.9)
        
        # Check billing SLA
        if billing_sla < 99.5:
            flags.append(RiskFlag(
                category="sla",
                severity="high",
                title="Below-Standard Billing SLA",
                description=f"Billing accuracy SLA of {billing_sla}% is below industry standard of 99.5%",
                recommendation="Renegotiate to at least 99.5% billing accuracy commitment",
                impact_score=15,
            ))
        elif billing_sla < self.benchmarks.avg_billing_sla:
            flags.append(RiskFlag(
                category="sla",
                severity="medium",
                title="Below-Portfolio Billing SLA",
                description=f"Billing SLA {billing_sla}% is below portfolio average of {self.benchmarks.avg_billing_sla:.2f}%",
                recommendation="Consider aligning with portfolio standard on renewal",
                impact_score=8,
            ))
        elif billing_sla >= 99.9:
            strengths.append(f"Excellent billing accuracy SLA of {billing_sla}%")
        
        # Check uptime SLA
        if uptime_sla < 99.9:
            flags.append(RiskFlag(
                category="sla",
                severity="medium",
                title="Low Platform Uptime SLA",
                description=f"Platform uptime SLA of {uptime_sla}% may not meet client expectations",
                recommendation="Consider upgrading to 99.95%+ for enterprise clients",
                impact_score=10,
            ))
        elif uptime_sla >= 99.99:
            strengths.append(f"Premium uptime SLA of {uptime_sla}%")
        
        # Check SLA credit percentage
        sla_credit = contract.get("sla_credit_pct", 10)
        if sla_credit >= 25:
            flags.append(RiskFlag(
                category="sla",
                severity="medium",
                title="High SLA Credit Exposure",
                description=f"SLA credit of {sla_credit}% creates significant financial exposure on breach",
                recommendation="Consider capping SLA credits or adding breach procedures",
                impact_score=8,
            ))
    
    def _analyze_compliance_risks(self, contract: Dict, flags: List[RiskFlag], strengths: List[str]):
        """Analyze compliance-related risks."""
        pci = contract.get("pci_compliant", True)
        soc2 = contract.get("soc2_certified", False)
        tier = contract.get("client_tier", "Standard")
        
        if not pci:
            flags.append(RiskFlag(
                category="compliance",
                severity="critical",
                title="Missing PCI-DSS Compliance",
                description="Contract does not require PCI-DSS compliance for billing data",
                recommendation="Add PCI-DSS compliance requirement immediately",
                impact_score=20,
            ))
        else:
            strengths.append("PCI-DSS compliance required")
        
        if not soc2:
            if tier in ["Enterprise", "Business"]:
                flags.append(RiskFlag(
                    category="compliance",
                    severity="high",
                    title="Missing SOC 2 Certification",
                    description=f"SOC 2 certification not required for {tier} tier client",
                    recommendation="Add SOC 2 Type II requirement for data security assurance",
                    impact_score=12,
                ))
            else:
                flags.append(RiskFlag(
                    category="compliance",
                    severity="low",
                    title="No SOC 2 Requirement",
                    description="Contract does not include SOC 2 certification requirement",
                    recommendation="Consider adding for enhanced security posture",
                    impact_score=5,
                ))
        else:
            strengths.append("SOC 2 certification required")
        
        # Data retention
        retention = contract.get("data_retention_months", 24)
        if retention < 24:
            flags.append(RiskFlag(
                category="compliance",
                severity="medium",
                title="Short Data Retention Period",
                description=f"Data retention of {retention} months may not meet regulatory requirements",
                recommendation="Extend to minimum 24 months for audit compliance",
                impact_score=8,
            ))
        elif retention >= 84:
            strengths.append(f"Comprehensive {retention}-month data retention")
    
    def _analyze_financial_risks(self, contract: Dict, all_contracts: List[Dict], 
                                  flags: List[RiskFlag], strengths: List[str]):
        """Analyze financial risks."""
        tier = contract.get("client_tier", "Standard")
        monthly_rev = contract.get("our_monthly_revenue", 0)
        rev_share = contract.get("revenue_share_pct", 0)
        late_fee = contract.get("late_payment_pct", 2.0)
        payment_terms = contract.get("payment_terms_days", 30)
        
        # Check if below tier benchmark
        if tier in self.benchmarks.tier_benchmarks:
            benchmark = self.benchmarks.tier_benchmarks[tier]
            if monthly_rev < benchmark["avg_monthly_revenue"] * 0.5:
                flags.append(RiskFlag(
                    category="financial",
                    severity="medium",
                    title="Below-Average Revenue for Tier",
                    description=f"Monthly revenue ${monthly_rev:,.0f} is well below {tier} average of ${benchmark['avg_monthly_revenue']:,.0f}",
                    recommendation="Review pricing structure or consider tier adjustment",
                    impact_score=10,
                ))
            
            if rev_share > 0 and rev_share > benchmark["avg_revenue_share"] * 1.2:
                strengths.append(f"Above-average revenue share of {rev_share}%")
            elif rev_share > 0 and rev_share < benchmark["avg_revenue_share"] * 0.8:
                flags.append(RiskFlag(
                    category="financial",
                    severity="low",
                    title="Below-Average Revenue Share",
                    description=f"Revenue share of {rev_share}% is below {tier} tier average",
                    recommendation="Negotiate higher rate on renewal",
                    impact_score=5,
                ))
        
        # Payment terms risk
        if payment_terms > 30:
            flags.append(RiskFlag(
                category="financial",
                severity="low",
                title="Extended Payment Terms",
                description=f"Payment terms of Net {payment_terms} create cash flow delay",
                recommendation="Negotiate to Net 30 or offer early payment discount",
                impact_score=5,
            ))
        elif payment_terms <= 15:
            strengths.append(f"Favorable Net {payment_terms} payment terms")
        
        # Late payment fee
        if late_fee < 1.5:
            flags.append(RiskFlag(
                category="financial",
                severity="low",
                title="Low Late Payment Penalty",
                description=f"Late payment fee of {late_fee}% may not deter delayed payments",
                recommendation="Increase to 2%+ to encourage timely payment",
                impact_score=3,
            ))
    
    def _analyze_terms_risks(self, contract: Dict, flags: List[RiskFlag], strengths: List[str]):
        """Analyze contract terms risks."""
        length = contract.get("contract_length_months", 24)
        etf_months = contract.get("early_termination_months", 6)
        dispute_days = contract.get("dispute_resolution_days", 10)
        
        # Short contract term
        if length <= 12:
            flags.append(RiskFlag(
                category="terms",
                severity="medium",
                title="Short Contract Term",
                description=f"Contract length of {length} months provides limited revenue visibility",
                recommendation="Negotiate 24+ month terms with renewal incentives",
                impact_score=8,
            ))
        elif length >= 48:
            strengths.append(f"Long-term {length}-month commitment")
        
        # ETF notice period
        if etf_months <= 3:
            flags.append(RiskFlag(
                category="terms",
                severity="medium",
                title="Short Early Termination Notice",
                description=f"Only {etf_months}-month notice required for early termination",
                recommendation="Extend notice period to 6+ months",
                impact_score=7,
            ))
        elif etf_months >= 12:
            strengths.append(f"Strong {etf_months}-month early termination protection")
        
        # Dispute resolution
        if dispute_days > 10:
            flags.append(RiskFlag(
                category="terms",
                severity="low",
                title="Extended Dispute Resolution Period",
                description=f"{dispute_days}-day dispute resolution may prolong conflicts",
                recommendation="Tighten to 5-7 days for faster resolution",
                impact_score=4,
            ))
        elif dispute_days <= 5:
            strengths.append("Fast 5-day dispute resolution")
    
    def _analyze_concentration_risks(self, contract: Dict, all_contracts: List[Dict],
                                      flags: List[RiskFlag], strengths: List[str]):
        """Analyze revenue concentration risks."""
        total_revenue = sum(c.get("our_monthly_revenue", 0) for c in all_contracts)
        contract_revenue = contract.get("our_monthly_revenue", 0)
        
        if total_revenue > 0:
            concentration = (contract_revenue / total_revenue) * 100
            
            if concentration > 20:
                flags.append(RiskFlag(
                    category="concentration",
                    severity="critical",
                    title="High Revenue Concentration",
                    description=f"This client represents {concentration:.1f}% of total revenue",
                    recommendation="Diversify portfolio to reduce single-client dependency",
                    impact_score=20,
                ))
            elif concentration > 15:
                flags.append(RiskFlag(
                    category="concentration",
                    severity="high",
                    title="Elevated Revenue Concentration",
                    description=f"Client represents {concentration:.1f}% of portfolio revenue",
                    recommendation="Monitor closely and develop contingency plans",
                    impact_score=12,
                ))
            elif concentration > 10:
                flags.append(RiskFlag(
                    category="concentration",
                    severity="medium",
                    title="Notable Revenue Concentration",
                    description=f"Client represents {concentration:.1f}% of portfolio",
                    recommendation="Continue diversification efforts",
                    impact_score=6,
                ))
    
    def _generate_summary(self, contract: Dict, score: int, flags: List[RiskFlag], 
                          strengths: List[str]) -> str:
        """Generate a human-readable risk summary."""
        client = contract.get("client_name", "Unknown")
        tier = contract.get("client_tier", "Unknown")
        
        if score < 30:
            status = "healthy"
        elif score < 50:
            status = "has some areas for improvement"
        elif score < 70:
            status = "requires attention"
        else:
            status = "needs immediate review"
        
        critical_count = sum(1 for f in flags if f.severity == "critical")
        high_count = sum(1 for f in flags if f.severity == "high")
        
        summary = f"The {tier} contract with {client} {status}. "
        
        if critical_count > 0:
            summary += f"Found {critical_count} critical issue(s) requiring immediate action. "
        if high_count > 0:
            summary += f"Identified {high_count} high-priority concern(s). "
        if strengths:
            summary += f"Key strengths include: {', '.join(strengths[:2])}."
        
        return summary


# =============================================================================
# Churn Prediction Engine
# =============================================================================

class ChurnPredictionEngine:
    """
    Predicts churn risk based on contract terms, tenure, and engagement signals.
    """
    
    def __init__(self, benchmarks: PortfolioBenchmarks):
        self.benchmarks = benchmarks
    
    def predict_churn(self, contract: Dict, risk_score: ContractRiskScore) -> ChurnPrediction:
        """Generate churn prediction for a contract."""
        risk_factors = []
        probability = 0.0
        
        # Factor 1: Contract length remaining
        prob_delta, factor = self._analyze_contract_timeline(contract)
        probability += prob_delta
        if factor:
            risk_factors.append(factor)
        
        # Factor 2: Risk score correlation
        prob_delta, factor = self._analyze_risk_correlation(risk_score)
        probability += prob_delta
        if factor:
            risk_factors.append(factor)
        
        # Factor 3: SLA satisfaction proxy
        prob_delta, factor = self._analyze_sla_satisfaction(contract)
        probability += prob_delta
        if factor:
            risk_factors.append(factor)
        
        # Factor 4: Price competitiveness
        prob_delta, factor = self._analyze_price_competitiveness(contract)
        probability += prob_delta
        if factor:
            risk_factors.append(factor)
        
        # Factor 5: Tier and engagement
        prob_delta, factor = self._analyze_tier_engagement(contract)
        probability += prob_delta
        if factor:
            risk_factors.append(factor)
        
        # Normalize probability
        probability = max(0.0, min(1.0, probability))
        
        # Determine risk level
        if probability >= 0.7:
            risk_level = ChurnRisk.VERY_HIGH
        elif probability >= 0.5:
            risk_level = ChurnRisk.HIGH
        elif probability >= 0.3:
            risk_level = ChurnRisk.MODERATE
        else:
            risk_level = ChurnRisk.LOW
        
        # Generate recommendations
        recommendations = self._generate_recommendations(contract, risk_factors, probability)
        
        # Optimal renewal timing
        renewal_timing = self._calculate_optimal_renewal(contract, probability)
        
        # Price sensitivity
        price_sensitivity = self._assess_price_sensitivity(contract, probability)
        
        return ChurnPrediction(
            contract_id=contract.get("index", 0),
            client_name=contract.get("client_name", "Unknown"),
            churn_probability=round(probability, 2),
            risk_level=risk_level.value,
            risk_factors=risk_factors,
            recommended_actions=recommendations,
            optimal_renewal_timing=renewal_timing,
            price_sensitivity=price_sensitivity,
        )
    
    def _analyze_contract_timeline(self, contract: Dict) -> Tuple[float, Optional[Dict]]:
        """Analyze contract timeline for churn signals."""
        length = contract.get("contract_length_months", 24)
        
        # Simulate days remaining (in real app, calculate from end_date)
        # For demo, assume contracts are at various stages
        import random
        random.seed(contract.get("index", 0))
        months_elapsed = random.randint(1, length)
        months_remaining = length - months_elapsed
        
        if months_remaining <= 3:
            return 0.25, {
                "factor": "Contract Expiring Soon",
                "detail": f"Only {months_remaining} months until renewal",
                "impact": "high",
                "weight": 0.25,
            }
        elif months_remaining <= 6:
            return 0.15, {
                "factor": "Approaching Renewal Window",
                "detail": f"{months_remaining} months until contract end",
                "impact": "medium",
                "weight": 0.15,
            }
        return 0.0, None
    
    def _analyze_risk_correlation(self, risk_score: ContractRiskScore) -> Tuple[float, Optional[Dict]]:
        """Higher risk scores correlate with higher churn probability."""
        score = risk_score.overall_score
        
        if score >= 70:
            return 0.20, {
                "factor": "Critical Risk Score",
                "detail": f"Risk score of {score}/100 indicates contract issues",
                "impact": "high",
                "weight": 0.20,
            }
        elif score >= 50:
            return 0.12, {
                "factor": "Elevated Risk Score",
                "detail": f"Risk score of {score}/100 suggests improvement needed",
                "impact": "medium",
                "weight": 0.12,
            }
        elif score >= 30:
            return 0.05, {
                "factor": "Moderate Risk Score",
                "detail": f"Risk score of {score}/100",
                "impact": "low",
                "weight": 0.05,
            }
        return 0.0, None
    
    def _analyze_sla_satisfaction(self, contract: Dict) -> Tuple[float, Optional[Dict]]:
        """Analyze SLA terms as proxy for satisfaction."""
        billing_sla = contract.get("billing_accuracy_sla", 99.5)
        uptime_sla = contract.get("platform_uptime_sla", 99.9)
        
        if billing_sla < 99.5 or uptime_sla < 99.9:
            return 0.10, {
                "factor": "Below-Standard SLAs",
                "detail": "Lower SLAs may indicate cost pressure or dissatisfaction",
                "impact": "medium",
                "weight": 0.10,
            }
        return 0.0, None
    
    def _analyze_price_competitiveness(self, contract: Dict) -> Tuple[float, Optional[Dict]]:
        """Analyze if pricing is competitive for the tier."""
        tier = contract.get("client_tier", "Standard")
        rev_share = contract.get("revenue_share_pct", 0)
        
        if tier in self.benchmarks.tier_benchmarks:
            benchmark = self.benchmarks.tier_benchmarks[tier]
            avg_share = benchmark.get("avg_revenue_share", 0)
            
            if rev_share > avg_share * 1.3:
                return 0.15, {
                    "factor": "Above-Market Pricing",
                    "detail": f"Revenue share {rev_share}% exceeds tier average by 30%+",
                    "impact": "high",
                    "weight": 0.15,
                }
        return 0.0, None
    
    def _analyze_tier_engagement(self, contract: Dict) -> Tuple[float, Optional[Dict]]:
        """Starter tier contracts have higher natural churn."""
        tier = contract.get("client_tier", "Standard")
        
        if tier == "Starter":
            return 0.10, {
                "factor": "Starter Tier Profile",
                "detail": "Starter clients have historically higher churn rates",
                "impact": "medium",
                "weight": 0.10,
            }
        elif tier == "Standard":
            return 0.05, {
                "factor": "Standard Tier Profile",
                "detail": "Standard tier has moderate retention challenges",
                "impact": "low",
                "weight": 0.05,
            }
        return 0.0, None
    
    def _generate_recommendations(self, contract: Dict, risk_factors: List[Dict], 
                                   probability: float) -> List[str]:
        """Generate actionable recommendations based on churn risk."""
        recommendations = []
        tier = contract.get("client_tier", "Standard")
        
        if probability >= 0.5:
            recommendations.append("Schedule executive check-in meeting within 2 weeks")
            recommendations.append("Prepare competitive pricing analysis for renewal discussion")
        
        if probability >= 0.3:
            recommendations.append("Review recent support tickets and billing disputes")
            recommendations.append("Consider offering loyalty incentives or tier upgrade")
        
        if any(f.get("factor") == "Contract Expiring Soon" for f in risk_factors):
            recommendations.append("Initiate renewal discussion 90 days before expiration")
        
        if any(f.get("factor") == "Above-Market Pricing" for f in risk_factors):
            recommendations.append("Prepare value proposition documentation")
            recommendations.append("Consider volume discount or extended term discount")
        
        if tier in ["Starter", "Standard"]:
            recommendations.append("Present tier upgrade benefits and ROI analysis")
        
        if not recommendations:
            recommendations.append("Maintain regular quarterly business reviews")
            recommendations.append("Continue monitoring engagement metrics")
        
        return recommendations[:5]  # Limit to top 5
    
    def _calculate_optimal_renewal(self, contract: Dict, probability: float) -> str:
        """Calculate optimal timing for renewal discussion."""
        if probability >= 0.5:
            return "Immediately - high churn risk requires urgent engagement"
        elif probability >= 0.3:
            return "Within 30 days - proactive engagement recommended"
        else:
            return "90 days before expiration - standard renewal timeline"
    
    def _assess_price_sensitivity(self, contract: Dict, probability: float) -> str:
        """Assess how price-sensitive the client likely is."""
        tier = contract.get("client_tier", "Standard")
        
        if tier in ["Starter", "Standard"] and probability >= 0.3:
            return "High - likely comparing alternatives, lead with value"
        elif tier == "Business":
            return "Moderate - balance value and pricing in discussions"
        else:
            return "Low - focus on service quality and relationship"


# =============================================================================
# Scenario Simulation Engine
# =============================================================================

class ScenarioEngine:
    """
    Multi-contract what-if scenario simulation.
    """
    
    def __init__(self, contracts: List[Dict]):
        self.contracts = contracts
        self.base_revenue = sum(c.get("our_monthly_revenue", 0) for c in contracts)
        self.base_acv = sum(c.get("annual_contract_value", 0) for c in contracts)
    
    def simulate_rate_change(self, tier: Optional[str], rate_change_pct: float, 
                              billing_model: Optional[str] = None) -> Dict:
        """Simulate impact of rate changes across portfolio."""
        affected = []
        total_impact = 0
        
        for c in self.contracts:
            if tier and c.get("client_tier") != tier:
                continue
            if billing_model and c.get("billing_model") != billing_model:
                continue
            
            current = c.get("our_monthly_revenue", 0)
            delta = current * (rate_change_pct / 100)
            new_revenue = current + delta
            
            affected.append({
                "client_name": c.get("client_name"),
                "current_monthly": round(current, 2),
                "new_monthly": round(new_revenue, 2),
                "monthly_delta": round(delta, 2),
                "annual_delta": round(delta * 12, 2),
            })
            total_impact += delta
        
        return {
            "scenario": "rate_change",
            "parameters": {
                "tier_filter": tier,
                "billing_model_filter": billing_model,
                "rate_change_pct": rate_change_pct,
            },
            "affected_contracts": len(affected),
            "total_monthly_impact": round(total_impact, 2),
            "total_annual_impact": round(total_impact * 12, 2),
            "new_portfolio_monthly": round(self.base_revenue + total_impact, 2),
            "new_portfolio_acv": round(self.base_acv + total_impact * 12, 2),
            "contracts": affected,
        }
    
    def simulate_client_loss(self, client_names: List[str]) -> Dict:
        """Simulate impact of losing specified clients."""
        lost = []
        retained = []
        lost_revenue = 0
        
        for c in self.contracts:
            name = c.get("client_name", "")
            if name in client_names:
                lost.append({
                    "client_name": name,
                    "monthly_revenue": c.get("our_monthly_revenue", 0),
                    "annual_revenue": c.get("annual_contract_value", 0),
                    "subscribers": c.get("subscriber_count", 0),
                })
                lost_revenue += c.get("our_monthly_revenue", 0)
            else:
                retained.append(name)
        
        return {
            "scenario": "client_loss",
            "lost_clients": lost,
            "lost_monthly_revenue": round(lost_revenue, 2),
            "lost_annual_revenue": round(lost_revenue * 12, 2),
            "remaining_monthly": round(self.base_revenue - lost_revenue, 2),
            "remaining_acv": round(self.base_acv - lost_revenue * 12, 2),
            "revenue_impact_pct": round((lost_revenue / self.base_revenue) * 100, 2) if self.base_revenue > 0 else 0,
            "retained_clients": len(retained),
        }
    
    def simulate_sla_standardization(self, target_sla: float) -> Dict:
        """Simulate standardizing all contracts to a target SLA."""
        upgrades = []
        downgrades = []
        
        for c in self.contracts:
            current_sla = c.get("billing_accuracy_sla", 99.5)
            if current_sla < target_sla:
                upgrades.append({
                    "client_name": c.get("client_name"),
                    "current_sla": current_sla,
                    "new_sla": target_sla,
                    "improvement": round(target_sla - current_sla, 2),
                })
            elif current_sla > target_sla:
                downgrades.append({
                    "client_name": c.get("client_name"),
                    "current_sla": current_sla,
                    "new_sla": target_sla,
                    "reduction": round(current_sla - target_sla, 2),
                })
        
        return {
            "scenario": "sla_standardization",
            "target_sla": target_sla,
            "contracts_upgraded": len(upgrades),
            "contracts_downgraded": len(downgrades),
            "upgrades": upgrades,
            "downgrades": downgrades,
            "recommendation": "SLA downgrades may increase churn risk" if downgrades else "Safe to proceed",
        }
    
    def forecast_revenue(self, months: int, churn_rate_pct: float, 
                         growth_rate_pct: float) -> Dict:
        """Forecast revenue over specified period."""
        monthly_churn = churn_rate_pct / 100
        monthly_growth = growth_rate_pct / 100
        
        projections = []
        current_revenue = self.base_revenue
        
        for month in range(1, months + 1):
            # Apply churn
            churned = current_revenue * monthly_churn
            # Apply growth
            new = current_revenue * monthly_growth
            # Net revenue
            current_revenue = current_revenue - churned + new
            
            projections.append({
                "month": month,
                "revenue": round(current_revenue, 2),
                "churned": round(churned, 2),
                "new": round(new, 2),
            })
        
        return {
            "scenario": "revenue_forecast",
            "parameters": {
                "months": months,
                "monthly_churn_rate": churn_rate_pct,
                "monthly_growth_rate": growth_rate_pct,
            },
            "starting_revenue": round(self.base_revenue, 2),
            "ending_revenue": round(current_revenue, 2),
            "total_change": round(current_revenue - self.base_revenue, 2),
            "change_pct": round(((current_revenue - self.base_revenue) / self.base_revenue) * 100, 2) if self.base_revenue > 0 else 0,
            "projections": projections,
        }


# =============================================================================
# Contract Generation Engine
# =============================================================================

class ContractGenerator:
    """
    Generate contracts from natural language descriptions.
    """
    
    TEMPLATE = """
BILLING SERVICES AGREEMENT
Contract Number: {contract_number}

PARTIES:
Provider: BillFlow Services Inc.
Client: {client_name}

EFFECTIVE DATE: {start_date}
TERM: {contract_length_months} months (ending {end_date})

1. SERVICE TIER
Client Tier: {client_tier}
Subscriber Count: {subscriber_count:,}
Average Revenue Per User (ARPU): ${avg_arpu:.2f}

2. BILLING MODEL & FEES
Billing Model: {billing_model}
{fee_structure}

3. SERVICE LEVEL AGREEMENTS
- Billing Accuracy: {billing_accuracy_sla}%
- Platform Uptime: {platform_uptime_sla}%
- Support Response Time: {support_response_hours} hours
- Dispute Resolution: {dispute_resolution_days} business days

4. SLA REMEDIES
Service credits of {sla_credit_pct}% of monthly fees for each SLA breach.

5. PAYMENT TERMS
- Payment Due: Net {payment_terms_days} days
- Remittance Frequency: {remittance_frequency}
- Late Payment Fee: {late_payment_pct}% per month

6. EARLY TERMINATION
- Notice Period: {early_termination_months} months
- Early Termination Fee: ${early_termination_fee:,.2f}

7. COMPLIANCE
- PCI-DSS Compliance: {"Required" if pci_compliant else "Not Required"}
- SOC 2 Certification: {"Required" if soc2_certified else "Not Required"}
- Data Retention Period: {data_retention_months} months

8. VOLUME TERMS
- Minimum Monthly Transactions: {monthly_minimum_transactions:,}
- Volume Discount Threshold: {volume_discount_threshold:,} transactions
- Volume Discount: {volume_discount_pct}%

SIGNATURES:
_______________________  Date: ________
BillFlow Services Inc.

_______________________  Date: ________
{client_name}
"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
    
    def generate_from_description(self, description: str, 
                                   existing_contracts: List[Dict]) -> Dict:
        """Generate a contract from natural language description."""
        # Use LLM to parse the description
        prompt = f"""Parse this contract description into structured data. 
        
Description: {description}

Return a JSON object with these fields (use reasonable defaults if not specified):
- client_name: string
- client_tier: "Enterprise" | "Business" | "Standard" | "Starter"
- subscriber_count: number
- avg_arpu: number (default 65.00)
- billing_model: "Revenue Share" | "Flat Fee" | "Per-Transaction" | "Hybrid"
- revenue_share_pct: number (0 if not applicable)
- per_transaction_fee: number (0 if not applicable)
- monthly_platform_fee: number (0 if not applicable)
- contract_length_months: number (default 24)
- billing_accuracy_sla: number (default 99.5)
- platform_uptime_sla: number (default 99.9)
- support_response_hours: number (default 4)
- dispute_resolution_days: number (default 10)
- payment_terms_days: number (default 30)
- remittance_frequency: "Weekly" | "Bi-weekly" | "Monthly"
- sla_credit_pct: number (default 10)
- late_payment_pct: number (default 2.0)
- early_termination_months: number (default 6)
- pci_compliant: boolean (default true)
- soc2_certified: boolean
- data_retention_months: number (default 24)
- monthly_minimum_transactions: number
- volume_discount_threshold: number
- volume_discount_pct: number (default 5)

Return ONLY valid JSON, no explanation."""

        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            
            result = response.choices[0].message.content
            # Clean up response
            result = result.strip()
            if result.startswith("```"):
                result = re.sub(r'^```json?\n?', '', result)
                result = re.sub(r'\n?```$', '', result)
            
            contract_data = json.loads(result)
        except Exception as e:
            # Fallback to basic parsing
            contract_data = self._fallback_parse(description)
        
        # Generate contract number
        max_index = max((c.get("index", 0) for c in existing_contracts), default=0)
        contract_data["index"] = max_index + 1
        contract_data["contract_number"] = f"BSA-2024-{contract_data['index']:05d}"
        
        # Calculate derived fields
        contract_data = self._calculate_derived_fields(contract_data)
        
        # Generate document text
        document = self._generate_document(contract_data)
        
        return {
            "contract_data": contract_data,
            "document": document,
        }
    
    def _fallback_parse(self, description: str) -> Dict:
        """Basic fallback parsing if LLM fails."""
        return {
            "client_name": "New Client",
            "client_tier": "Standard",
            "subscriber_count": 50000,
            "avg_arpu": 65.00,
            "billing_model": "Revenue Share",
            "revenue_share_pct": 3.0,
            "per_transaction_fee": 0,
            "monthly_platform_fee": 0,
            "contract_length_months": 24,
            "billing_accuracy_sla": 99.5,
            "platform_uptime_sla": 99.9,
            "support_response_hours": 4,
            "dispute_resolution_days": 10,
            "payment_terms_days": 30,
            "remittance_frequency": "Monthly",
            "sla_credit_pct": 10,
            "late_payment_pct": 2.0,
            "early_termination_months": 6,
            "pci_compliant": True,
            "soc2_certified": False,
            "data_retention_months": 24,
            "monthly_minimum_transactions": 40000,
            "volume_discount_threshold": 60000,
            "volume_discount_pct": 5,
        }
    
    def _calculate_derived_fields(self, data: Dict) -> Dict:
        """Calculate revenue and other derived fields."""
        subscribers = data.get("subscriber_count", 50000)
        arpu = data.get("avg_arpu", 65.00)
        
        # Client monthly revenue
        client_monthly = subscribers * arpu
        data["client_monthly_revenue"] = round(client_monthly, 2)
        
        # Our monthly revenue based on billing model
        model = data.get("billing_model", "Revenue Share")
        if model == "Revenue Share":
            our_monthly = client_monthly * (data.get("revenue_share_pct", 3.0) / 100)
        elif model == "Flat Fee":
            our_monthly = data.get("monthly_platform_fee", 10000)
        elif model == "Per-Transaction":
            our_monthly = subscribers * data.get("per_transaction_fee", 0.25) + data.get("monthly_platform_fee", 0)
        else:  # Hybrid
            rev_share = client_monthly * (data.get("revenue_share_pct", 2.0) / 100)
            txn_fee = subscribers * data.get("per_transaction_fee", 0.10)
            platform = data.get("monthly_platform_fee", 500)
            our_monthly = rev_share + txn_fee + platform
        
        data["our_monthly_revenue"] = round(our_monthly, 2)
        
        # Contract values
        months = data.get("contract_length_months", 24)
        data["annual_contract_value"] = round(our_monthly * 12, 2)
        data["total_contract_value"] = round(our_monthly * months, 2)
        
        # Early termination fee (6 months revenue)
        etf_months = data.get("early_termination_months", 6)
        data["early_termination_fee"] = round(our_monthly * etf_months, 2)
        
        # Dates
        from datetime import datetime, timedelta
        start = datetime.now()
        end = start + timedelta(days=months * 30)
        data["start_date"] = start.strftime("%B %d, %Y")
        data["end_date"] = end.strftime("%B %d, %Y")
        
        # Minimums and thresholds if not set
        if "monthly_minimum_transactions" not in data:
            data["monthly_minimum_transactions"] = int(subscribers * 0.8)
        if "volume_discount_threshold" not in data:
            data["volume_discount_threshold"] = int(subscribers * 1.2)
        
        return data
    
    def _generate_document(self, data: Dict) -> str:
        """Generate the contract document text."""
        # Build fee structure text
        model = data.get("billing_model", "Revenue Share")
        if model == "Revenue Share":
            fee_text = f"Revenue Share: {data.get('revenue_share_pct', 3.0)}% of client billing revenue"
        elif model == "Flat Fee":
            fee_text = f"Monthly Platform Fee: ${data.get('monthly_platform_fee', 10000):,.2f}"
        elif model == "Per-Transaction":
            fee_text = f"Per-Transaction Fee: ${data.get('per_transaction_fee', 0.25):.2f}\nMonthly Platform Fee: ${data.get('monthly_platform_fee', 1000):,.2f}"
        else:  # Hybrid
            fee_text = f"""Revenue Share: {data.get('revenue_share_pct', 2.0)}%
Per-Transaction Fee: ${data.get('per_transaction_fee', 0.10):.2f}
Monthly Platform Fee: ${data.get('monthly_platform_fee', 500):,.2f}"""
        
        data["fee_structure"] = fee_text
        
        return self.TEMPLATE.format(**data)


# =============================================================================
# Contract Comparison Engine
# =============================================================================

class ContractComparisonEngine:
    """
    Compare two contracts and highlight differences.
    """
    
    COMPARABLE_FIELDS = [
        ("billing_model", "Billing Model", "category"),
        ("revenue_share_pct", "Revenue Share %", "percentage"),
        ("per_transaction_fee", "Per-Transaction Fee", "currency"),
        ("monthly_platform_fee", "Monthly Platform Fee", "currency"),
        ("our_monthly_revenue", "Monthly Revenue", "currency"),
        ("annual_contract_value", "Annual Contract Value", "currency"),
        ("contract_length_months", "Contract Length", "months"),
        ("billing_accuracy_sla", "Billing Accuracy SLA", "percentage"),
        ("platform_uptime_sla", "Platform Uptime SLA", "percentage"),
        ("support_response_hours", "Support Response Time", "hours"),
        ("dispute_resolution_days", "Dispute Resolution", "days"),
        ("payment_terms_days", "Payment Terms", "days"),
        ("sla_credit_pct", "SLA Credit %", "percentage"),
        ("late_payment_pct", "Late Payment Fee", "percentage"),
        ("early_termination_months", "ETF Notice Period", "months"),
        ("early_termination_fee", "Early Termination Fee", "currency"),
        ("pci_compliant", "PCI Compliance", "boolean"),
        ("soc2_certified", "SOC 2 Certified", "boolean"),
        ("data_retention_months", "Data Retention", "months"),
        ("volume_discount_pct", "Volume Discount", "percentage"),
    ]
    
    def compare_contracts(self, contract_a: Dict, contract_b: Dict) -> ContractComparison:
        """Compare two contracts and return differences."""
        differences = []
        financial_impact = {
            "monthly_revenue_delta": 0,
            "annual_revenue_delta": 0,
        }
        
        name_a = contract_a.get("client_name", "Contract A")
        name_b = contract_b.get("client_name", "Contract B")
        
        for field, label, field_type in self.COMPARABLE_FIELDS:
            val_a = contract_a.get(field)
            val_b = contract_b.get(field)
            
            if val_a != val_b:
                diff = {
                    "field": label,
                    "contract_a": self._format_value(val_a, field_type),
                    "contract_b": self._format_value(val_b, field_type),
                    "raw_a": val_a,
                    "raw_b": val_b,
                }
                
                # Calculate delta for numeric fields
                if field_type in ["currency", "percentage", "months", "days", "hours"] and val_a is not None and val_b is not None:
                    delta = val_b - val_a
                    diff["delta"] = self._format_value(delta, field_type, show_sign=True)
                    
                    if field == "our_monthly_revenue":
                        financial_impact["monthly_revenue_delta"] = delta
                        financial_impact["annual_revenue_delta"] = delta * 12
                
                # Determine which is "better"
                diff["comparison"] = self._compare_values(field, val_a, val_b)
                
                differences.append(diff)
        
        # Generate summary
        summary = self._generate_comparison_summary(name_a, name_b, differences, financial_impact)
        
        return ContractComparison(
            contract_a=name_a,
            contract_b=name_b,
            differences=differences,
            summary=summary,
            financial_impact=financial_impact,
        )
    
    def _format_value(self, value: Any, field_type: str, show_sign: bool = False) -> str:
        """Format a value for display."""
        if value is None:
            return "N/A"
        
        sign = ""
        if show_sign and isinstance(value, (int, float)) and value > 0:
            sign = "+"
        
        if field_type == "currency":
            return f"{sign}${value:,.2f}"
        elif field_type == "percentage":
            return f"{sign}{value}%"
        elif field_type == "months":
            return f"{sign}{value} months"
        elif field_type == "days":
            return f"{sign}{value} days"
        elif field_type == "hours":
            return f"{sign}{value} hours"
        elif field_type == "boolean":
            return "Yes" if value else "No"
        else:
            return str(value)
    
    def _compare_values(self, field: str, val_a: Any, val_b: Any) -> str:
        """Determine which value is better for the provider."""
        # Higher is better
        higher_better = [
            "revenue_share_pct", "per_transaction_fee", "monthly_platform_fee",
            "our_monthly_revenue", "annual_contract_value", "contract_length_months",
            "billing_accuracy_sla", "platform_uptime_sla", "early_termination_months",
            "early_termination_fee", "late_payment_pct", "volume_discount_pct",
            "data_retention_months",
        ]
        
        # Lower is better
        lower_better = [
            "support_response_hours", "dispute_resolution_days", "payment_terms_days",
            "sla_credit_pct",
        ]
        
        if val_a is None or val_b is None:
            return "neutral"
        
        if field in higher_better:
            if val_b > val_a:
                return "b_better"
            elif val_a > val_b:
                return "a_better"
        elif field in lower_better:
            if val_b < val_a:
                return "b_better"
            elif val_a < val_b:
                return "a_better"
        
        return "neutral"
    
    def _generate_comparison_summary(self, name_a: str, name_b: str, 
                                     differences: List[Dict], 
                                     financial_impact: Dict) -> str:
        """Generate a summary of the comparison."""
        if not differences:
            return f"The contracts with {name_a} and {name_b} have identical terms."
        
        a_wins = sum(1 for d in differences if d.get("comparison") == "a_better")
        b_wins = sum(1 for d in differences if d.get("comparison") == "b_better")
        
        delta = financial_impact.get("annual_revenue_delta", 0)
        
        summary = f"Comparing {name_a} vs {name_b}: Found {len(differences)} differences. "
        
        if a_wins > b_wins:
            summary += f"{name_a} has more favorable terms in {a_wins} areas. "
        elif b_wins > a_wins:
            summary += f"{name_b} has more favorable terms in {b_wins} areas. "
        else:
            summary += "Both contracts have similar overall favorability. "
        
        if delta != 0:
            if delta > 0:
                summary += f"{name_b} generates ${delta:,.0f} more annual revenue."
            else:
                summary += f"{name_a} generates ${-delta:,.0f} more annual revenue."
        
        return summary


# =============================================================================
# Main Intelligence Service
# =============================================================================

class ContractIntelligenceService:
    """
    Main service that orchestrates all contract intelligence features.
    """
    
    def __init__(self, contracts_path: str = "contract_data.json"):
        self.contracts_path = contracts_path
        self.contracts = self._load_contracts()
        self.benchmarks = PortfolioBenchmarks(self.contracts)
        self.risk_engine = RiskScoringEngine(self.benchmarks)
        self.churn_engine = ChurnPredictionEngine(self.benchmarks)
        self.scenario_engine = ScenarioEngine(self.contracts)
        self.generator = ContractGenerator()
        self.comparison_engine = ContractComparisonEngine()
    
    def _load_contracts(self) -> List[Dict]:
        """Load contracts from JSON file."""
        if not os.path.exists(self.contracts_path):
            return []
        with open(self.contracts_path, "r") as f:
            return json.load(f)
    
    def refresh_contracts(self):
        """Reload contracts from file."""
        self.contracts = self._load_contracts()
        self.benchmarks = PortfolioBenchmarks(self.contracts)
        self.risk_engine = RiskScoringEngine(self.benchmarks)
        self.churn_engine = ChurnPredictionEngine(self.benchmarks)
        self.scenario_engine = ScenarioEngine(self.contracts)
    
    # Feature 1 & 2: Risk Scoring and Clause Analysis
    def get_portfolio_risk_analysis(self) -> Dict:
        """Get risk analysis for entire portfolio."""
        results = []
        for contract in self.contracts:
            risk_score = self.risk_engine.score_contract(contract, self.contracts)
            results.append(asdict(risk_score))
        
        # Sort by risk score descending
        results.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # Portfolio summary
        scores = [r["overall_score"] for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        risk_distribution = {
            "critical": sum(1 for r in results if r["risk_level"] == "critical"),
            "high": sum(1 for r in results if r["risk_level"] == "high"),
            "medium": sum(1 for r in results if r["risk_level"] == "medium"),
            "low": sum(1 for r in results if r["risk_level"] == "low"),
        }
        
        return {
            "portfolio_avg_score": round(avg_score, 1),
            "risk_distribution": risk_distribution,
            "contracts": results,
            "total_flags": sum(len(r["flags"]) for r in results),
            "critical_flags": sum(len([f for f in r["flags"] if f["severity"] == "critical"]) for r in results),
        }
    
    def get_contract_risk(self, contract_id: int) -> Dict:
        """Get risk analysis for a specific contract."""
        contract = next((c for c in self.contracts if c.get("index") == contract_id), None)
        if not contract:
            return {"error": f"Contract {contract_id} not found"}
        
        risk_score = self.risk_engine.score_contract(contract, self.contracts)
        return asdict(risk_score)
    
    # Feature 3: Churn Prediction
    def get_portfolio_churn_analysis(self) -> Dict:
        """Get churn predictions for entire portfolio."""
        results = []
        for contract in self.contracts:
            risk_score = self.risk_engine.score_contract(contract, self.contracts)
            churn_pred = self.churn_engine.predict_churn(contract, risk_score)
            results.append(asdict(churn_pred))
        
        # Sort by churn probability descending
        results.sort(key=lambda x: x["churn_probability"], reverse=True)
        
        # Summary
        probs = [r["churn_probability"] for r in results]
        avg_prob = sum(probs) / len(probs) if probs else 0
        
        at_risk_revenue = sum(
            c.get("our_monthly_revenue", 0) * 12
            for c, r in zip(self.contracts, results)
            if r["churn_probability"] >= 0.3
        )
        
        return {
            "avg_churn_probability": round(avg_prob, 2),
            "high_risk_count": sum(1 for r in results if r["risk_level"] in ["high", "very_high"]),
            "at_risk_annual_revenue": round(at_risk_revenue, 2),
            "contracts": results,
        }
    
    def get_contract_churn(self, contract_id: int) -> Dict:
        """Get churn prediction for a specific contract."""
        contract = next((c for c in self.contracts if c.get("index") == contract_id), None)
        if not contract:
            return {"error": f"Contract {contract_id} not found"}
        
        risk_score = self.risk_engine.score_contract(contract, self.contracts)
        churn_pred = self.churn_engine.predict_churn(contract, risk_score)
        return asdict(churn_pred)
    
    # Feature 4: Scenario Simulation
    def simulate_scenario(self, scenario_type: str, params: Dict) -> Dict:
        """Run a what-if scenario simulation."""
        if scenario_type == "rate_change":
            return self.scenario_engine.simulate_rate_change(
                tier=params.get("tier"),
                rate_change_pct=params.get("rate_change_pct", 0),
                billing_model=params.get("billing_model"),
            )
        elif scenario_type == "client_loss":
            return self.scenario_engine.simulate_client_loss(
                client_names=params.get("client_names", []),
            )
        elif scenario_type == "sla_standardization":
            return self.scenario_engine.simulate_sla_standardization(
                target_sla=params.get("target_sla", 99.5),
            )
        elif scenario_type == "revenue_forecast":
            return self.scenario_engine.forecast_revenue(
                months=params.get("months", 12),
                churn_rate_pct=params.get("churn_rate_pct", 1.0),
                growth_rate_pct=params.get("growth_rate_pct", 2.0),
            )
        else:
            return {"error": f"Unknown scenario type: {scenario_type}"}
    
    # Feature 5: Contract Generation
    def generate_contract(self, description: str) -> Dict:
        """Generate a new contract from natural language description."""
        return self.generator.generate_from_description(description, self.contracts)
    
    # Feature 6: Contract Comparison
    def compare_contracts(self, contract_id_a: int, contract_id_b: int) -> Dict:
        """Compare two contracts."""
        contract_a = next((c for c in self.contracts if c.get("index") == contract_id_a), None)
        contract_b = next((c for c in self.contracts if c.get("index") == contract_id_b), None)
        
        if not contract_a:
            return {"error": f"Contract {contract_id_a} not found"}
        if not contract_b:
            return {"error": f"Contract {contract_id_b} not found"}
        
        comparison = self.comparison_engine.compare_contracts(contract_a, contract_b)
        return asdict(comparison)
    
    # Get benchmarks
    def get_benchmarks(self) -> Dict:
        """Get portfolio benchmarks."""
        return {
            "avg_billing_sla": round(self.benchmarks.avg_billing_sla, 2),
            "avg_uptime_sla": round(self.benchmarks.avg_uptime_sla, 2),
            "avg_payment_terms": round(self.benchmarks.avg_payment_terms, 1),
            "avg_contract_length": round(self.benchmarks.avg_contract_length, 1),
            "pci_compliance_rate": round(self.benchmarks.pci_compliance_rate, 1),
            "soc2_compliance_rate": round(self.benchmarks.soc2_compliance_rate, 1),
            "tier_benchmarks": self.benchmarks.tier_benchmarks,
        }


# Singleton instance
_service: Optional[ContractIntelligenceService] = None

def get_intelligence_service() -> ContractIntelligenceService:
    """Get or create the intelligence service singleton."""
    global _service
    if _service is None:
        _service = ContractIntelligenceService()
    return _service
