import React, { useState, useRef, useEffect, useCallback, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Role = "user" | "assistant";
type Message = {
  id: string;
  role: Role;
  content: string;
  sources?: { source: string; page?: number | null }[];
  attachments?: { name: string; type: string }[];
};

type Contract = {
  id: number;
  company: string;
  contract_number: string;
  client_tier: string;
  billing_model: string;
  our_monthly_revenue: number;
  annual_contract_value: number;
  subscriber_count: number;
  term_months: number;
  end_date: string;
  billing_accuracy_sla: number;
  city: string;
  state: string;
};

type Metrics = {
  total_contracts: number;
  total_acv: number;
  monthly_revenue: number;
  total_subscribers: number;
  avg_billing_accuracy_sla: number;
  contracts_by_tier: Record<string, number>;
  expiring_soon: number;
};

// Intelligence Types
type RiskFlag = {
  category: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
  impact_score: number;
};

type ContractRisk = {
  contract_id: number;
  client_name: string;
  overall_score: number;
  risk_level: string;
  flags: RiskFlag[];
  strengths: string[];
  summary: string;
};

type ChurnPrediction = {
  contract_id: number;
  client_name: string;
  churn_probability: number;
  risk_level: string;
  risk_factors: { factor: string; detail: string; impact: string; weight: number }[];
  recommended_actions: string[];
  optimal_renewal_timing: string;
  price_sensitivity: string;
};

type PortfolioRisk = {
  portfolio_avg_score: number;
  risk_distribution: { critical: number; high: number; medium: number; low: number };
  contracts: ContractRisk[];
  total_flags: number;
  critical_flags: number;
};

type PortfolioChurn = {
  avg_churn_probability: number;
  high_risk_count: number;
  at_risk_annual_revenue: number;
  contracts: ChurnPrediction[];
};

type ContractComparison = {
  contract_a: string;
  contract_b: string;
  differences: {
    field: string;
    contract_a: string;
    contract_b: string;
    delta?: string;
    comparison: string;
  }[];
  summary: string;
  financial_impact: { monthly_revenue_delta: number; annual_revenue_delta: number };
};

type ScenarioResult = {
  scenario: string;
  parameters?: Record<string, unknown>;
  total_monthly_impact?: number;
  total_annual_impact?: number;
  contracts?: unknown[];
  projections?: { month: number; revenue: number }[];
  [key: string]: unknown;
};

type GeneratedContract = {
  contract_data: Record<string, unknown>;
  document: string;
};

type ActiveView = "dashboard" | "chat" | "intelligence" | "revenue";

// Revenue Intelligence Types
type RevenueLeakage = {
  id: string;
  client_name: string;
  contract_id: number;
  leak_type: string;
  amount_monthly: number;
  amount_annual: number;
  description: string;
  root_cause: string;
  fix_action: string;
  fix_effort: string;
  fix_timeline: string;
  confidence: number;
};

type RevenueOpportunity = {
  id: string;
  client_name: string;
  contract_id: number;
  opportunity_type: string;
  potential_monthly: number;
  potential_annual: number;
  description: string;
  approach: string;
  success_probability: number;
  best_timing: string;
  talking_points: string[];
};

type ActionItem = {
  id: string;
  client_name: string;
  contract_id: number;
  action_type: string;
  urgency: string;
  title: string;
  description: string;
  revenue_impact: number;
  due_date: string;
  script: string | null;
  auto_executable: boolean;
  prerequisites: string[];
  success_metrics: string[];
};

type ClientSignal = {
  id: string;
  client_name: string;
  contract_id: number;
  signal_type: string;
  strength: number;
  detected_at: string;
  description: string;
  evidence: string[];
  recommended_response: string;
  if_ignored: string;
};

type DealGenome = {
  contract_id: number;
  client_name: string;
  success_score: number;
  genome_markers: Record<string, number>;
  similar_deals: { client_name: string; similarity: number; outcome: string }[];
  predicted_outcome: string;
  optimization_suggestions: string[];
};

type CommandCenterData = {
  summary: {
    total_leakage_annual: number;
    total_opportunity_annual: number;
    net_revenue_gap: number;
    critical_actions: number;
    portfolio_health_score: number;
    active_signals: number;
  };
  leakages: RevenueLeakage[];
  opportunities: RevenueOpportunity[];
  signals: ClientSignal[];
  action_queue: ActionItem[];
  genomes: DealGenome[];
};

const API_BASE = "http://localhost:8001";

// Sparkline Chart Component
const Sparkline = ({ data, color = "#6366f1", height = 32 }: { data: number[]; color?: string; height?: number }) => {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 80;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ');
  
  const areaPath = `M0,${height} L${points} L${width},${height} Z`;
  
  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`spark-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#spark-${color.replace('#', '')})`} />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

// Donut Chart Component
const DonutChart = ({ data, size = 64 }: { data: { label: string; value: number; color: string }[]; size?: number }) => {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  
  let offset = 0;
  
  return (
    <svg width={size} height={size} className="transform -rotate-90">
      {data.map((d, i) => {
        const percentage = d.value / total;
        const strokeDasharray = `${percentage * circumference} ${circumference}`;
        const strokeDashoffset = -offset * circumference;
        offset += percentage;
        
        return (
          <circle
            key={i}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={d.color}
            strokeWidth={strokeWidth}
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        );
      })}
    </svg>
  );
};

// Progress Ring Component
const ProgressRing = ({ value, max = 100, size = 48, color = "#22c55e" }: { value: number; max?: number; size?: number; color?: string }) => {
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(value / max, 1);
  const strokeDasharray = `${progress * circumference} ${circumference}`;
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-100"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={strokeDasharray}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[10px] font-semibold text-gray-700">{value.toFixed(1)}%</span>
      </div>
    </div>
  );
};

// Timeline Bar Component
const TimelineBar = ({ contracts }: { contracts: { company: string; daysLeft: number }[] }) => {
  const sorted = [...contracts].sort((a, b) => a.daysLeft - b.daysLeft).slice(0, 5);
  const maxDays = 90;
  
  return (
    <div className="space-y-2">
      {sorted.map((c, i) => {
        const progress = Math.max(0, Math.min(100, ((maxDays - c.daysLeft) / maxDays) * 100));
        const urgency = c.daysLeft < 30 ? "#ef4444" : c.daysLeft < 60 ? "#f59e0b" : "#22c55e";
        
        return (
          <div key={i} className="group">
            <div className="flex items-center justify-between text-[11px] mb-1">
              <span className="text-gray-600 truncate max-w-[100px]">{c.company}</span>
              <span className="text-gray-400">{c.daysLeft}d</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${progress}%`, backgroundColor: urgency }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Icons
const Icons = {
  logo: (
    <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
      <rect x="3" y="3" width="18" height="18" rx="4" className="fill-indigo-500" />
      <path d="M8 9h8M8 12h6M8 15h4" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  send: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path d="M10 3a1 1 0 01.707.293l6 6a1 1 0 01-1.414 1.414L11 6.414V16a1 1 0 11-2 0V6.414L4.707 10.707a1 1 0 01-1.414-1.414l6-6A1 1 0 0110 3z" />
    </svg>
  ),
  doc: (
    <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5">
      <path d="M4 1h5l4 4v9a1 1 0 01-1 1H4a1 1 0 01-1-1V2a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.2" />
      <path d="M9 1v4h4" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  ),
  folder: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M3 5a2 2 0 012-2h3l2 2h5a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V5z" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10.5 10.5l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  x: (
    <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5">
      <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  plus: (
    <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
      <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  sparkles: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zM14 6a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1V7a1 1 0 011-1zM7 12a1 1 0 011 1v1h1a1 1 0 110 2H8v1a1 1 0 11-2 0v-1H5a1 1 0 110-2h1v-1a1 1 0 011-1z" />
    </svg>
  ),
  attach: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M15.5 9.5l-6 6a4 4 0 01-5.7-5.7l6-6a2.5 2.5 0 013.5 3.5l-6 6a1 1 0 01-1.4-1.4l5.5-5.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  mic: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <rect x="7" y="2" width="6" height="10" rx="3" stroke="currentColor" strokeWidth="1.3" />
      <path d="M4 9a6 6 0 0012 0M10 15v3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  refresh: (
    <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5">
      <path d="M3 10a7 7 0 0113.5-2.5M17 10a7 7 0 01-13.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M16 3v5h-5M4 17v-5h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  edit: (
    <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5">
      <path d="M13.5 3.5l3 3M4 13l-1 4 4-1 9-9-3-3-9 9z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  copy: (
    <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5">
      <rect x="6" y="6" width="10" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M4 14V4a2 2 0 012-2h6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  check: (
    <svg viewBox="0 0 20 20" fill="none" className="w-3.5 h-3.5">
      <path d="M4 10l4 4 8-8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  arrowUp: (
    <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3">
      <path d="M8 12V4M4 7l4-4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  arrowDown: (
    <svg viewBox="0 0 16 16" fill="none" className="w-3 h-3">
      <path d="M8 4v8M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  clock: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" />
      <path d="M10 6v4l2.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  zap: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path d="M11 3L5 12h4l-1 5 6-9h-4l1-5z" />
    </svg>
  ),
  shield: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M10 2l7 3v4c0 4.5-3 8-7 9.5-4-1.5-7-5-7-9.5V5l7-3z" stroke="currentColor" strokeWidth="1.3" />
      <path d="M7 10l2 2 4-4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  warning: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  ),
  trending: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M3 17l4-4 4 2 6-8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 7h3v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  brain: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M10 2C6.5 2 4 4.5 4 7c0 1.5.6 2.8 1.5 3.8C4.6 12 4 13.4 4 15c0 1.7.9 3 2.5 3.7M10 2c3.5 0 6 2.5 6 5 0 1.5-.6 2.8-1.5 3.8.9 1.2 1.5 2.6 1.5 4.2 0 1.7-.9 3-2.5 3.7M10 2v16" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  compare: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M4 6h5M4 10h3M4 14h5M11 6h5M11 10h5M11 14h3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M10 4v12" stroke="currentColor" strokeWidth="1.3" strokeDasharray="2 2" />
    </svg>
  ),
  generate: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <rect x="3" y="4" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.3" />
      <path d="M6 8h8M6 11h5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M13 10l2 2-2 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  scenario: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" />
      <path d="M10 6v4l2.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M14 3l2 2M3 14l2 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  chart: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M3 17h14" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M5 17V9M9 17V5M13 17V11M17 17V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  users: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <circle cx="7" cy="7" r="3" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2 17c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <circle cx="14" cy="6" r="2" stroke="currentColor" strokeWidth="1.3" />
      <path d="M14 10c2 0 4 1.5 4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  dollar: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" />
      <path d="M10 5v10M7 7.5c0-1 1.3-1.5 3-1.5s3 .5 3 1.5-1.3 1.5-3 2-3 1-3 2 1.3 1.5 3 1.5 3-.5 3-1.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  leak: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M10 2v4M7 4l3 2 3-2M10 6c-3 3-5 6-5 9a5 5 0 0010 0c0-3-2-6-5-9z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  rocket: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M10 18c-1-1-2-3-2-5 0-3 2-7 5-10 3 3 5 7 5 10 0 2-1 4-2 5M6 12c-2 1-3 3-3 5 2 0 4-1 5-3M14 12c2 1 3 3 3 5-2 0-4-1-5-3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  signal: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M4 14a8 8 0 0112 0" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M6 11a5 5 0 018 0" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M8 8a3 3 0 014 0" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <circle cx="10" cy="16" r="1" fill="currentColor" />
    </svg>
  ),
  dna: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <path d="M6 2c0 4 8 4 8 8s-8 4-8 8M14 2c0 4-8 4-8 8s8 4 8 8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M6 6h8M6 14h8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  ),
  play: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path d="M6 4l10 6-10 6V4z" />
    </svg>
  ),
  target: (
    <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" />
      <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="1.3" />
      <circle cx="10" cy="10" r="1" fill="currentColor" />
    </svg>
  ),
};

// Mock revenue trend data
const generateTrendData = () => Array.from({ length: 12 }, () => Math.random() * 50 + 50);

// Dashboard Card Component
const DashboardCard = ({ 
  title, 
  value, 
  subtitle, 
  trend, 
  trendUp,
  children,
  className = ""
}: { 
  title: string;
  value: string;
  subtitle?: string;
  trend?: string;
  trendUp?: boolean;
  children?: React.ReactNode;
  className?: string;
}) => (
  <div className={`bg-white rounded-2xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow ${className}`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-semibold text-gray-900 mt-1 tracking-tight">{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
      {trend && (
        <div className={`flex items-center gap-0.5 text-xs font-medium px-1.5 py-0.5 rounded-full ${
          trendUp ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
        }`}>
          {trendUp ? Icons.arrowUp : Icons.arrowDown}
          {trend}
        </div>
      )}
    </div>
    {children && <div className="mt-3">{children}</div>}
  </div>
);

// Quick Action Button
const QuickAction = ({ icon, label, onClick }: { icon: React.ReactNode; label: string; onClick: () => void }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-2 px-3 py-2 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all text-sm text-gray-600 hover:text-gray-900"
  >
    <span className="text-indigo-500">{icon}</span>
    {label}
  </button>
);

// Contract Browser Panel
const ContractBrowser = ({ 
  contracts, 
  isLoading, 
  onSelect, 
  onClose 
}: { 
  contracts: Contract[];
  isLoading: boolean;
  onSelect: (c: Contract) => void;
  onClose: () => void;
}) => {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string>("all");

  const clientTiers = [...new Set(contracts.map(c => c.client_tier))];
  
  const filtered = contracts.filter(c => {
    const matchesSearch = search === "" || 
      c.company.toLowerCase().includes(search.toLowerCase()) ||
      c.contract_number.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === "all" || c.client_tier === filter;
    return matchesSearch && matchesFilter;
  });

  const sorted = [...filtered].sort((a, b) => b.our_monthly_revenue - a.our_monthly_revenue);

  const formatCurrency = (n: number) => 
    n >= 10000 ? `$${(n / 1000).toFixed(0)}K` : `$${n.toFixed(0)}`;

  return (
    <div className="fixed inset-y-0 right-0 w-[400px] bg-white shadow-2xl z-50 flex flex-col">
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Client Portfolio</h2>
            <p className="text-sm text-gray-400">{contracts.length} active agreements</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-50 rounded-lg transition-colors">
            {Icons.x}
          </button>
        </div>
        
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            {Icons.search}
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search clients..."
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-50 rounded-xl border-0 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:bg-white transition-all"
          />
        </div>

        <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
              filter === "all" 
                ? "bg-indigo-500 text-white" 
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            All
          </button>
          {clientTiers.map(tier => (
            <button
              key={tier}
              onClick={() => setFilter(tier)}
              className={`px-3 py-1 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
                filter === tier 
                  ? "bg-indigo-500 text-white" 
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : sorted.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No clients found</div>
        ) : (
          <div className="p-2">
            {sorted.map((c) => (
              <button
                key={c.id}
                onClick={() => onSelect(c)}
                className="w-full p-3 text-left rounded-xl hover:bg-gray-50 transition-colors mb-1"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-medium text-gray-900 truncate">{c.company}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{c.contract_number}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-sm font-semibold text-indigo-600">{formatCurrency(c.our_monthly_revenue)}<span className="text-gray-400 font-normal">/mo</span></div>
                    <span className="inline-block text-[10px] px-2 py-0.5 bg-gray-100 rounded-full text-gray-500 mt-1">
                      {c.client_tier}
                    </span>
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                  <span>{c.billing_model}</span>
                  <span>{c.subscriber_count?.toLocaleString() || 0} subscribers</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const TypingIndicator = () => (
  <div className="flex items-start gap-3 py-4">
    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-sm">
      {Icons.sparkles}
    </div>
    <div className="flex items-center gap-1.5 pt-2">
      <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  </div>
);

// Welcome Dashboard
const WelcomeDashboard = ({ 
  onQuery, 
  metrics,
  contracts 
}: { 
  onQuery: (q: string) => void; 
  metrics: Metrics | null;
  contracts: Contract[];
}) => {
  const trendData = useMemo(() => generateTrendData(), []);
  
  const tierData = useMemo(() => {
    const tiers = metrics?.contracts_by_tier || {};
    const colors = { Enterprise: "#6366f1", Business: "#8b5cf6", Standard: "#a855f7", Starter: "#d946ef" };
    return Object.entries(tiers).map(([label, value]) => ({
      label,
      value: value as number,
      color: colors[label as keyof typeof colors] || "#94a3b8"
    }));
  }, [metrics]);

  const expiringContracts = useMemo(() => {
    return contracts.map(c => {
      // Simple calculation - in real app would parse actual dates
      const daysLeft = Math.floor(Math.random() * 120) + 1;
      return { company: c.company, daysLeft };
    }).filter(c => c.daysLeft <= 90);
  }, [contracts]);

  const formatCurrency = (n: number) => 
    n >= 1000000 ? `$${(n / 1000000).toFixed(1)}M` : n >= 1000 ? `$${(n / 1000).toFixed(0)}K` : `$${n}`;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
              {Icons.zap}
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Good morning</h1>
              <p className="text-sm text-gray-400">Here's your portfolio overview</p>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <DashboardCard
            title="Annual Revenue"
            value={formatCurrency(metrics?.total_acv || 0)}
            trend="+12.5%"
            trendUp={true}
          >
            <Sparkline data={trendData} color="#6366f1" />
          </DashboardCard>
          
          <DashboardCard
            title="Active Clients"
            value={String(metrics?.total_contracts || 0)}
            subtitle="Billing agreements"
            trend="+3"
            trendUp={true}
          />
          
          <DashboardCard
            title="Subscribers"
            value={formatCurrency(metrics?.total_subscribers || 0).replace('$', '')}
            subtitle="Total managed"
          />
          
          <DashboardCard
            title="Avg SLA"
            value=""
            className="flex flex-col"
          >
            <div className="flex items-center gap-3 -mt-1">
              <ProgressRing 
                value={metrics?.avg_billing_accuracy_sla || 99.5} 
                size={52} 
                color="#22c55e" 
              />
              <div>
                <p className="text-xs text-gray-400">Billing Accuracy</p>
                <p className="text-lg font-semibold text-gray-900">{metrics?.avg_billing_accuracy_sla || 99.5}%</p>
              </div>
            </div>
          </DashboardCard>
        </div>

        {/* Secondary Row */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {/* Client Distribution */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Client Tiers</p>
            <div className="flex items-center gap-4">
              {tierData.length > 0 ? (
                <>
                  <DonutChart data={tierData} size={72} />
                  <div className="flex-1 space-y-1">
                    {tierData.map((d, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                          <span className="text-gray-600">{d.label}</span>
                        </div>
                        <span className="font-medium text-gray-900">{d.value}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-gray-400">No tier data</p>
              )}
            </div>
          </div>

          {/* Expiring Soon */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Expiring Soon</p>
              <span className="text-xs text-amber-500 font-medium">{expiringContracts.length} contracts</span>
            </div>
            <TimelineBar contracts={expiringContracts} />
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">This Month</p>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Processed</span>
                <span className="text-sm font-semibold text-gray-900">$2.4M</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Disputes</span>
                <span className="text-sm font-semibold text-green-600">3 resolved</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">SLA Breaches</span>
                <span className="text-sm font-semibold text-gray-900">0</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-6">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Quick Actions</p>
          <div className="flex flex-wrap gap-2">
            <QuickAction 
              icon={Icons.clock} 
              label="Expiring Contracts" 
              onClick={() => onQuery("List all contracts expiring in the next 90 days with renewal terms")}
            />
            <QuickAction 
              icon={Icons.sparkles} 
              label="Revenue Report" 
              onClick={() => onQuery("Generate a revenue analysis showing top 10 clients by annual contract value")}
            />
            <QuickAction 
              icon={<span className="text-green-500">{Icons.check}</span>} 
              label="SLA Compliance" 
              onClick={() => onQuery("Generate an SLA compliance report showing billing accuracy and uptime commitments")}
            />
            <QuickAction 
              icon={Icons.folder} 
              label="Portfolio Summary" 
              onClick={() => onQuery("Provide a complete portfolio overview with breakdown by client tier and billing model")}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Urgency Badge
const UrgencyBadge = ({ urgency }: { urgency: string }) => {
  const colors: Record<string, string> = {
    critical: "bg-red-500 text-white",
    high: "bg-orange-500 text-white",
    medium: "bg-amber-500 text-white",
    low: "bg-blue-500 text-white",
    opportunity: "bg-green-500 text-white",
  };
  return (
    <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-full ${colors[urgency] || colors.medium}`}>
      {urgency}
    </span>
  );
};

// Revenue Command Center Component
const RevenueCommandCenter = () => {
  const [activeTab, setActiveTab] = useState<"overview" | "leakage" | "opportunities" | "signals" | "actions" | "genome">("overview");
  const [data, setData] = useState<CommandCenterData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [generatingScript, setGeneratingScript] = useState<string | null>(null);
  const [generatedScript, setGeneratedScript] = useState<{ id: string; script: string } | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/revenue/command-center`)
      .then(res => res.json())
      .then(d => setData(d))
      .catch(() => setError("Failed to load revenue intelligence"))
      .finally(() => setIsLoading(false));
  }, []);

  const generateOutreach = async (actionId: string) => {
    setGeneratingScript(actionId);
    try {
      const res = await fetch(`${API_BASE}/revenue/generate-outreach`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId }),
      });
      const result = await res.json();
      setGeneratedScript({ id: actionId, script: result.script });
    } catch {
      setError("Failed to generate script");
    } finally {
      setGeneratingScript(null);
    }
  };

  const formatCurrency = (n: number) =>
    n >= 1000000 ? `$${(n / 1000000).toFixed(1)}M` : n >= 1000 ? `$${(n / 1000).toFixed(0)}K` : `$${n.toFixed(0)}`;

  const tabs = [
    { id: "overview" as const, label: "Command Center", icon: Icons.target },
    { id: "leakage" as const, label: "Leakage", icon: Icons.leak },
    { id: "opportunities" as const, label: "Opportunities", icon: Icons.rocket },
    { id: "signals" as const, label: "Signals", icon: Icons.signal },
    { id: "actions" as const, label: "Actions", icon: Icons.play },
    { id: "genome" as const, label: "Genome", icon: Icons.dna },
  ];

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading Revenue Intelligence...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-red-500">
          <p>{error || "Failed to load data"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-emerald-500/30">
              {Icons.dollar}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Revenue Command Center</h1>
              <p className="text-gray-400">AI-powered autonomous revenue operations</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? "bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-lg shadow-emerald-500/25"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white border border-gray-700"
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Hero Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-red-500/20 to-red-600/10 rounded-2xl p-6 border border-red-500/30">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center text-red-400">
                    {Icons.leak}
                  </div>
                  <div>
                    <p className="text-red-300 text-xs font-medium uppercase">Revenue Leakage</p>
                    <p className="text-3xl font-bold text-white">{formatCurrency(data.summary.total_leakage_annual)}</p>
                  </div>
                </div>
                <p className="text-red-300/80 text-sm">Money being lost annually</p>
              </div>

              <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-2xl p-6 border border-emerald-500/30">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                    {Icons.rocket}
                  </div>
                  <div>
                    <p className="text-emerald-300 text-xs font-medium uppercase">Opportunities</p>
                    <p className="text-3xl font-bold text-white">{formatCurrency(data.summary.total_opportunity_annual)}</p>
                  </div>
                </div>
                <p className="text-emerald-300/80 text-sm">Untapped revenue potential</p>
              </div>

              <div className="bg-gradient-to-br from-cyan-500/20 to-cyan-600/10 rounded-2xl p-6 border border-cyan-500/30">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center text-cyan-400">
                    {Icons.zap}
                  </div>
                  <div>
                    <p className="text-cyan-300 text-xs font-medium uppercase">Total Revenue Gap</p>
                    <p className="text-3xl font-bold text-white">{formatCurrency(data.summary.net_revenue_gap)}</p>
                  </div>
                </div>
                <p className="text-cyan-300/80 text-sm">Your optimization potential</p>
              </div>
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-gray-400 text-xs uppercase mb-1">Portfolio Health</p>
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-bold text-white">{data.summary.portfolio_health_score}</p>
                  <span className="text-gray-500">/100</span>
                </div>
              </div>
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-gray-400 text-xs uppercase mb-1">Critical Actions</p>
                <p className="text-2xl font-bold text-red-400">{data.summary.critical_actions}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-gray-400 text-xs uppercase mb-1">Active Signals</p>
                <p className="text-2xl font-bold text-amber-400">{data.summary.active_signals}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-gray-400 text-xs uppercase mb-1">Actions in Queue</p>
                <p className="text-2xl font-bold text-white">{data.action_queue.length}</p>
              </div>
            </div>

            {/* Action Queue Preview */}
            <div className="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden">
              <div className="p-4 border-b border-gray-700 flex items-center justify-between">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  {Icons.play}
                  Priority Actions
                </h3>
                <button onClick={() => setActiveTab("actions")} className="text-sm text-emerald-400 hover:text-emerald-300">
                  View all →
                </button>
              </div>
              <div className="divide-y divide-gray-700">
                {data.action_queue.slice(0, 5).map(action => (
                  <div key={action.id} className="p-4 hover:bg-gray-700/50 transition-colors">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <UrgencyBadge urgency={action.urgency} />
                          <span className="text-white font-medium">{action.title}</span>
                        </div>
                        <p className="text-gray-400 text-sm">{action.client_name} · {action.description}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-emerald-400 font-semibold">{formatCurrency(action.revenue_impact)}</p>
                        <p className="text-gray-500 text-xs">at stake</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-2 gap-6">
              {/* Top Leakages */}
              <div className="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                  <h3 className="text-white font-semibold flex items-center gap-2">
                    <span className="text-red-400">{Icons.leak}</span>
                    Top Revenue Leaks
                  </h3>
                </div>
                <div className="p-4 space-y-3">
                  {data.leakages.slice(0, 4).map(leak => (
                    <div key={leak.id} className="bg-gray-900 rounded-xl p-3 border border-red-500/20">
                      <div className="flex justify-between mb-1">
                        <span className="text-white font-medium text-sm">{leak.client_name}</span>
                        <span className="text-red-400 font-semibold text-sm">{formatCurrency(leak.amount_annual)}/yr</span>
                      </div>
                      <p className="text-gray-400 text-xs">{leak.leak_type}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Opportunities */}
              <div className="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                  <h3 className="text-white font-semibold flex items-center gap-2">
                    <span className="text-emerald-400">{Icons.rocket}</span>
                    Top Opportunities
                  </h3>
                </div>
                <div className="p-4 space-y-3">
                  {data.opportunities.slice(0, 4).map(opp => (
                    <div key={opp.id} className="bg-gray-900 rounded-xl p-3 border border-emerald-500/20">
                      <div className="flex justify-between mb-1">
                        <span className="text-white font-medium text-sm">{opp.client_name}</span>
                        <span className="text-emerald-400 font-semibold text-sm">{formatCurrency(opp.potential_annual)}/yr</span>
                      </div>
                      <p className="text-gray-400 text-xs">{opp.opportunity_type} · {(opp.success_probability * 100).toFixed(0)}% probability</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Leakage Tab */}
        {activeTab === "leakage" && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-red-500/10 to-transparent rounded-2xl p-6 border border-red-500/30 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-red-500/20 flex items-center justify-center text-red-400 text-2xl">
                  {Icons.leak}
                </div>
                <div>
                  <p className="text-red-300 text-sm">Total Annual Leakage</p>
                  <p className="text-4xl font-bold text-white">{formatCurrency(data.summary.total_leakage_annual)}</p>
                  <p className="text-red-300/60 text-sm mt-1">Across {data.leakages.length} identified leaks</p>
                </div>
              </div>
            </div>

            {data.leakages.map(leak => (
              <div
                key={leak.id}
                className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden hover:border-red-500/50 transition-colors"
              >
                <button
                  onClick={() => setExpandedItem(expandedItem === leak.id ? null : leak.id)}
                  className="w-full p-4 text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-white font-semibold">{leak.client_name}</span>
                        <span className="px-2 py-0.5 bg-red-500/20 text-red-300 text-xs rounded-full">{leak.leak_type}</span>
                      </div>
                      <p className="text-gray-400 text-sm">{leak.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-red-400">{formatCurrency(leak.amount_annual)}</p>
                      <p className="text-gray-500 text-xs">annual loss</p>
                    </div>
                  </div>
                </button>
                {expandedItem === leak.id && (
                  <div className="px-4 pb-4 space-y-3 border-t border-gray-700 pt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-gray-500 text-xs uppercase mb-1">Root Cause</p>
                        <p className="text-gray-300 text-sm">{leak.root_cause}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs uppercase mb-1">Fix Timeline</p>
                        <p className="text-gray-300 text-sm">{leak.fix_timeline}</p>
                      </div>
                    </div>
                    <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/30">
                      <p className="text-emerald-300 text-xs uppercase mb-1">Recommended Action</p>
                      <p className="text-white text-sm">{leak.fix_action}</p>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-gray-500">Effort: <span className={`font-medium ${leak.fix_effort === 'low' ? 'text-green-400' : leak.fix_effort === 'medium' ? 'text-amber-400' : 'text-red-400'}`}>{leak.fix_effort}</span></span>
                      <span className="text-gray-500">Confidence: <span className="text-white font-medium">{(leak.confidence * 100).toFixed(0)}%</span></span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Opportunities Tab */}
        {activeTab === "opportunities" && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-emerald-500/10 to-transparent rounded-2xl p-6 border border-emerald-500/30 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-2xl">
                  {Icons.rocket}
                </div>
                <div>
                  <p className="text-emerald-300 text-sm">Total Annual Opportunity</p>
                  <p className="text-4xl font-bold text-white">{formatCurrency(data.summary.total_opportunity_annual)}</p>
                  <p className="text-emerald-300/60 text-sm mt-1">Across {data.opportunities.length} opportunities</p>
                </div>
              </div>
            </div>

            {data.opportunities.map(opp => (
              <div
                key={opp.id}
                className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden hover:border-emerald-500/50 transition-colors"
              >
                <button
                  onClick={() => setExpandedItem(expandedItem === opp.id ? null : opp.id)}
                  className="w-full p-4 text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-white font-semibold">{opp.client_name}</span>
                        <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-xs rounded-full">{opp.opportunity_type}</span>
                        <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 text-xs rounded-full">{(opp.success_probability * 100).toFixed(0)}% prob</span>
                      </div>
                      <p className="text-gray-400 text-sm">{opp.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-400">{formatCurrency(opp.potential_annual)}</p>
                      <p className="text-gray-500 text-xs">potential</p>
                    </div>
                  </div>
                </button>
                {expandedItem === opp.id && (
                  <div className="px-4 pb-4 space-y-3 border-t border-gray-700 pt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-gray-500 text-xs uppercase mb-1">Approach</p>
                        <p className="text-gray-300 text-sm">{opp.approach}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs uppercase mb-1">Best Timing</p>
                        <p className="text-gray-300 text-sm">{opp.best_timing}</p>
                      </div>
                    </div>
                    <div className="bg-cyan-500/10 rounded-lg p-3 border border-cyan-500/30">
                      <p className="text-cyan-300 text-xs uppercase mb-2">Talking Points</p>
                      <ul className="space-y-1">
                        {opp.talking_points.map((tp, i) => (
                          <li key={i} className="text-white text-sm flex items-start gap-2">
                            <span className="text-cyan-400 mt-0.5">{Icons.check}</span>
                            {tp}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Signals Tab */}
        {activeTab === "signals" && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-amber-500/10 to-transparent rounded-2xl p-6 border border-amber-500/30 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-amber-500/20 flex items-center justify-center text-amber-400 text-2xl">
                  {Icons.signal}
                </div>
                <div>
                  <p className="text-amber-300 text-sm">Active Signals</p>
                  <p className="text-4xl font-bold text-white">{data.signals.length}</p>
                  <p className="text-amber-300/60 text-sm mt-1">Early warnings & opportunities detected</p>
                </div>
              </div>
            </div>

            {data.signals.map(signal => (
              <div
                key={signal.id}
                className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden"
              >
                <button
                  onClick={() => setExpandedItem(expandedItem === signal.id ? null : signal.id)}
                  className="w-full p-4 text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-white font-semibold">{signal.client_name}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          signal.signal_type.includes('risk') || signal.signal_type.includes('drop') || signal.signal_type.includes('delay')
                            ? 'bg-red-500/20 text-red-300'
                            : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {signal.signal_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm">{signal.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${signal.strength >= 0.8 ? 'bg-red-500' : signal.strength >= 0.6 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                          style={{ width: `${signal.strength * 100}%` }}
                        />
                      </div>
                      <p className="text-gray-500 text-xs mt-1">{(signal.strength * 100).toFixed(0)}% strength</p>
                    </div>
                  </div>
                </button>
                {expandedItem === signal.id && (
                  <div className="px-4 pb-4 space-y-3 border-t border-gray-700 pt-4">
                    <div>
                      <p className="text-gray-500 text-xs uppercase mb-2">Evidence</p>
                      <ul className="space-y-1">
                        {signal.evidence.map((e, i) => (
                          <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                            <span className="text-amber-400">•</span>
                            {e}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="bg-cyan-500/10 rounded-lg p-3 border border-cyan-500/30">
                      <p className="text-cyan-300 text-xs uppercase mb-1">Recommended Response</p>
                      <p className="text-white text-sm">{signal.recommended_response}</p>
                    </div>
                    <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/30">
                      <p className="text-red-300 text-xs uppercase mb-1">If Ignored</p>
                      <p className="text-red-200 text-sm">{signal.if_ignored}</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Actions Tab */}
        {activeTab === "actions" && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-indigo-500/10 to-transparent rounded-2xl p-6 border border-indigo-500/30 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 text-2xl">
                  {Icons.play}
                </div>
                <div>
                  <p className="text-indigo-300 text-sm">Prioritized Action Queue</p>
                  <p className="text-4xl font-bold text-white">{data.action_queue.length}</p>
                  <p className="text-indigo-300/60 text-sm mt-1">{data.summary.critical_actions} critical · AI-prioritized by impact</p>
                </div>
              </div>
            </div>

            {data.action_queue.map(action => (
              <div
                key={action.id}
                className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden"
              >
                <button
                  onClick={() => setExpandedItem(expandedItem === action.id ? null : action.id)}
                  className="w-full p-4 text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <UrgencyBadge urgency={action.urgency} />
                        <span className="text-white font-semibold">{action.title}</span>
                      </div>
                      <p className="text-gray-400 text-sm">{action.client_name} · {action.action_type} · Due: {action.due_date}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-400">{formatCurrency(action.revenue_impact)}</p>
                      <p className="text-gray-500 text-xs">revenue impact</p>
                    </div>
                  </div>
                </button>
                {expandedItem === action.id && (
                  <div className="px-4 pb-4 space-y-3 border-t border-gray-700 pt-4">
                    <p className="text-gray-300 text-sm">{action.description}</p>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-gray-500 text-xs uppercase mb-2">Prerequisites</p>
                        <ul className="space-y-1">
                          {action.prerequisites.map((p, i) => (
                            <li key={i} className="text-gray-400 text-sm flex items-center gap-2">
                              <span className="w-4 h-4 rounded border border-gray-600" />
                              {p}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs uppercase mb-2">Success Metrics</p>
                        <ul className="space-y-1">
                          {action.success_metrics.map((m, i) => (
                            <li key={i} className="text-gray-400 text-sm flex items-center gap-2">
                              <span className="text-emerald-400">{Icons.target}</span>
                              {m}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={() => generateOutreach(action.id)}
                        disabled={generatingScript === action.id}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-lg font-medium text-sm hover:opacity-90 disabled:opacity-50"
                      >
                        {generatingScript === action.id ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            {Icons.sparkles}
                            Generate AI Outreach Script
                          </>
                        )}
                      </button>
                      {action.auto_executable && (
                        <button className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg font-medium text-sm hover:bg-emerald-600">
                          {Icons.zap}
                          Auto-Execute
                        </button>
                      )}
                    </div>

                    {generatedScript?.id === action.id && (
                      <div className="mt-4 bg-gray-900 rounded-xl p-4 border border-indigo-500/30">
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-indigo-300 text-xs uppercase font-medium">AI-Generated Outreach Script</p>
                          <button
                            onClick={() => navigator.clipboard.writeText(generatedScript.script)}
                            className="text-gray-400 hover:text-white text-sm flex items-center gap-1"
                          >
                            {Icons.copy} Copy
                          </button>
                        </div>
                        <pre className="text-gray-300 text-sm whitespace-pre-wrap font-sans">{generatedScript.script}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Genome Tab */}
        {activeTab === "genome" && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-purple-500/10 to-transparent rounded-2xl p-6 border border-purple-500/30 mb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-purple-500/20 flex items-center justify-center text-purple-400 text-2xl">
                  {Icons.dna}
                </div>
                <div>
                  <p className="text-purple-300 text-sm">Deal Genome Analysis</p>
                  <p className="text-4xl font-bold text-white">{data.summary.portfolio_health_score}/100</p>
                  <p className="text-purple-300/60 text-sm mt-1">Portfolio health score</p>
                </div>
              </div>
            </div>

            {data.genomes.map(genome => (
              <div
                key={genome.contract_id}
                className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden"
              >
                <button
                  onClick={() => setExpandedItem(expandedItem === `genome-${genome.contract_id}` ? null : `genome-${genome.contract_id}`)}
                  className="w-full p-4 text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-white font-semibold">{genome.client_name}</span>
                      <p className="text-gray-400 text-sm mt-1">{genome.predicted_outcome}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="w-32">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-500">Success Score</span>
                          <span className="text-white font-medium">{genome.success_score}</span>
                        </div>
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              genome.success_score >= 75 ? 'bg-emerald-500' :
                              genome.success_score >= 50 ? 'bg-amber-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${genome.success_score}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </button>
                {expandedItem === `genome-${genome.contract_id}` && (
                  <div className="px-4 pb-4 space-y-4 border-t border-gray-700 pt-4">
                    {/* Genome Markers */}
                    <div>
                      <p className="text-gray-500 text-xs uppercase mb-3">Genome Markers</p>
                      <div className="grid grid-cols-3 gap-3">
                        {Object.entries(genome.genome_markers).map(([key, value]) => (
                          <div key={key} className="bg-gray-900 rounded-lg p-3">
                            <p className="text-gray-400 text-xs mb-1">{key.replace(/_/g, ' ')}</p>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    value >= 75 ? 'bg-emerald-500' :
                                    value >= 50 ? 'bg-amber-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${value}%` }}
                                />
                              </div>
                              <span className="text-white text-sm font-medium w-8">{value}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Optimization Suggestions */}
                    <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/30">
                      <p className="text-purple-300 text-xs uppercase mb-2">Optimization Suggestions</p>
                      <ul className="space-y-1">
                        {genome.optimization_suggestions.map((s, i) => (
                          <li key={i} className="text-white text-sm flex items-start gap-2">
                            <span className="text-purple-400 mt-0.5">{Icons.sparkles}</span>
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Risk Score Badge
const RiskBadge = ({ level }: { level: string }) => {
  const colors: Record<string, string> = {
    critical: "bg-red-100 text-red-700 border-red-200",
    high: "bg-orange-100 text-orange-700 border-orange-200",
    medium: "bg-amber-100 text-amber-700 border-amber-200",
    low: "bg-green-100 text-green-700 border-green-200",
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${colors[level] || colors.medium}`}>
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </span>
  );
};

// Churn Badge
const ChurnBadge = ({ level }: { level: string }) => {
  const colors: Record<string, string> = {
    very_high: "bg-red-100 text-red-700",
    high: "bg-orange-100 text-orange-700",
    moderate: "bg-amber-100 text-amber-700",
    low: "bg-green-100 text-green-700",
  };
  const labels: Record<string, string> = {
    very_high: "Very High",
    high: "High",
    moderate: "Moderate",
    low: "Low",
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${colors[level] || colors.moderate}`}>
      {labels[level] || level}
    </span>
  );
};

// Intelligence Dashboard Component
const IntelligenceDashboard = ({ contracts }: { contracts: Contract[] }) => {
  const [activeTab, setActiveTab] = useState<"risk" | "churn" | "scenarios" | "compare" | "generate">("risk");
  const [portfolioRisk, setPortfolioRisk] = useState<PortfolioRisk | null>(null);
  const [portfolioChurn, setPortfolioChurn] = useState<PortfolioChurn | null>(null);
  const [selectedRiskContract, setSelectedRiskContract] = useState<ContractRisk | null>(null);
  const [selectedChurnContract, setSelectedChurnContract] = useState<ChurnPrediction | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Scenario state
  const [scenarioType, setScenarioType] = useState<string>("rate_change");
  const [scenarioParams, setScenarioParams] = useState<Record<string, string | number>>({ rate_change_pct: 5 });
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(null);
  
  // Compare state
  const [compareA, setCompareA] = useState<number | "">(0);
  const [compareB, setCompareB] = useState<number | "">(1);
  const [comparison, setComparison] = useState<ContractComparison | null>(null);
  
  // Generate state
  const [generatePrompt, setGeneratePrompt] = useState("");
  const [generatedContract, setGeneratedContract] = useState<GeneratedContract | null>(null);

  // Load risk data
  useEffect(() => {
    if (activeTab === "risk" && !portfolioRisk) {
      setIsLoading(true);
      setError(null);
      fetch(`${API_BASE}/intelligence/risk`)
        .then(res => res.json())
        .then(data => setPortfolioRisk(data))
        .catch(e => setError("Failed to load risk data"))
        .finally(() => setIsLoading(false));
    }
  }, [activeTab, portfolioRisk]);

  // Load churn data
  useEffect(() => {
    if (activeTab === "churn" && !portfolioChurn) {
      setIsLoading(true);
      setError(null);
      fetch(`${API_BASE}/intelligence/churn`)
        .then(res => res.json())
        .then(data => setPortfolioChurn(data))
        .catch(e => setError("Failed to load churn data"))
        .finally(() => setIsLoading(false));
    }
  }, [activeTab, portfolioChurn]);

  const runScenario = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/intelligence/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_type: scenarioType, params: scenarioParams }),
      });
      const data = await res.json();
      setScenarioResult(data);
    } catch {
      setError("Failed to run scenario");
    } finally {
      setIsLoading(false);
    }
  };

  const runComparison = async () => {
    if (compareA === "" || compareB === "") return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/intelligence/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contract_id_a: compareA, contract_id_b: compareB }),
      });
      const data = await res.json();
      setComparison(data);
    } catch {
      setError("Failed to compare contracts");
    } finally {
      setIsLoading(false);
    }
  };

  const generateContract = async () => {
    if (!generatePrompt.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/intelligence/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: generatePrompt }),
      });
      const data = await res.json();
      setGeneratedContract(data);
    } catch {
      setError("Failed to generate contract");
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: "risk" as const, label: "Risk Analysis", icon: Icons.shield },
    { id: "churn" as const, label: "Churn Prediction", icon: Icons.trending },
    { id: "scenarios" as const, label: "What-If", icon: Icons.scenario },
    { id: "compare" as const, label: "Compare", icon: Icons.compare },
    { id: "generate" as const, label: "Generate", icon: Icons.generate },
  ];

  const formatCurrency = (n: number) =>
    n >= 1000000 ? `$${(n / 1000000).toFixed(1)}M` : n >= 1000 ? `$${(n / 1000).toFixed(0)}K` : `$${n.toFixed(0)}`;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-purple-500/25">
              {Icons.brain}
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Contract Intelligence</h1>
              <p className="text-sm text-gray-400">AI-powered analysis, predictions & simulations</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/25"
                  : "bg-white text-gray-600 hover:bg-gray-50 border border-gray-200"
              }`}
            >
              <span className={activeTab === tab.id ? "text-white" : "text-indigo-500"}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {error}
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Risk Analysis Tab */}
        {activeTab === "risk" && !isLoading && portfolioRisk && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-4 gap-4">
              <DashboardCard
                title="Portfolio Risk"
                value={`${portfolioRisk.portfolio_avg_score}/100`}
                subtitle="Average score"
              >
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mt-2">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${portfolioRisk.portfolio_avg_score}%`,
                      backgroundColor: portfolioRisk.portfolio_avg_score >= 70 ? "#ef4444" :
                        portfolioRisk.portfolio_avg_score >= 50 ? "#f59e0b" :
                        portfolioRisk.portfolio_avg_score >= 30 ? "#eab308" : "#22c55e"
                    }}
                  />
                </div>
              </DashboardCard>
              <DashboardCard title="Critical Issues" value={String(portfolioRisk.critical_flags)} subtitle="Immediate attention" />
              <DashboardCard title="Total Flags" value={String(portfolioRisk.total_flags)} subtitle="Across all contracts" />
              <DashboardCard title="High Risk" value={String(portfolioRisk.risk_distribution.critical + portfolioRisk.risk_distribution.high)} subtitle="Contracts" />
            </div>

            {/* Risk Distribution */}
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Risk Distribution</h3>
              <div className="flex gap-4">
                {Object.entries(portfolioRisk.risk_distribution).map(([level, count]) => (
                  <div key={level} className="flex-1 text-center">
                    <div className="text-2xl font-bold text-gray-900">{count}</div>
                    <RiskBadge level={level} />
                  </div>
                ))}
              </div>
            </div>

            {/* Contract Risk List */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900">Contract Risk Scores</h3>
              </div>
              <div className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
                {portfolioRisk.contracts.map(contract => (
                  <button
                    key={contract.contract_id}
                    onClick={() => setSelectedRiskContract(selectedRiskContract?.contract_id === contract.contract_id ? null : contract)}
                    className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">{contract.client_name}</div>
                        <div className="text-xs text-gray-400 mt-0.5">{contract.flags.length} flags · {contract.strengths.length} strengths</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="text-lg font-bold text-gray-900">{contract.overall_score}</div>
                          <div className="text-xs text-gray-400">/ 100</div>
                        </div>
                        <RiskBadge level={contract.risk_level} />
                      </div>
                    </div>
                    {selectedRiskContract?.contract_id === contract.contract_id && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <p className="text-sm text-gray-600 mb-3">{contract.summary}</p>
                        {contract.flags.length > 0 && (
                          <div className="mb-3">
                            <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">Risk Flags</div>
                            <div className="space-y-2">
                              {contract.flags.map((flag, i) => (
                                <div key={i} className="p-3 bg-red-50 rounded-lg border border-red-100">
                                  <div className="flex items-start justify-between">
                                    <div className="font-medium text-red-800 text-sm">{flag.title}</div>
                                    <span className="text-xs text-red-600">+{flag.impact_score} pts</span>
                                  </div>
                                  <p className="text-xs text-red-700 mt-1">{flag.description}</p>
                                  <p className="text-xs text-red-600 mt-2 font-medium">→ {flag.recommendation}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {contract.strengths.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">Strengths</div>
                            <div className="flex flex-wrap gap-2">
                              {contract.strengths.map((s, i) => (
                                <span key={i} className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded-lg border border-green-100">{s}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Churn Prediction Tab */}
        {activeTab === "churn" && !isLoading && portfolioChurn && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-4 gap-4">
              <DashboardCard
                title="Avg Churn Risk"
                value={`${(portfolioChurn.avg_churn_probability * 100).toFixed(0)}%`}
                subtitle="Probability"
              />
              <DashboardCard title="High Risk" value={String(portfolioChurn.high_risk_count)} subtitle="Contracts at risk" />
              <DashboardCard title="At-Risk Revenue" value={formatCurrency(portfolioChurn.at_risk_annual_revenue)} subtitle="Annual value" />
              <DashboardCard title="Total Contracts" value={String(portfolioChurn.contracts.length)} subtitle="Analyzed" />
            </div>

            {/* Churn List */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900">Churn Predictions by Client</h3>
              </div>
              <div className="divide-y divide-gray-100 max-h-[500px] overflow-y-auto">
                {portfolioChurn.contracts.map(contract => (
                  <button
                    key={contract.contract_id}
                    onClick={() => setSelectedChurnContract(selectedChurnContract?.contract_id === contract.contract_id ? null : contract)}
                    className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">{contract.client_name}</div>
                        <div className="text-xs text-gray-400 mt-0.5">{contract.risk_factors.length} risk factors</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${contract.churn_probability * 100}%`,
                              backgroundColor: contract.churn_probability >= 0.7 ? "#ef4444" :
                                contract.churn_probability >= 0.5 ? "#f59e0b" :
                                contract.churn_probability >= 0.3 ? "#eab308" : "#22c55e"
                            }}
                          />
                        </div>
                        <div className="text-sm font-bold text-gray-900 w-12 text-right">
                          {(contract.churn_probability * 100).toFixed(0)}%
                        </div>
                        <ChurnBadge level={contract.risk_level} />
                      </div>
                    </div>
                    {selectedChurnContract?.contract_id === contract.contract_id && (
                      <div className="mt-4 pt-4 border-t border-gray-100 space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">Optimal Renewal</div>
                            <p className="text-sm text-gray-700">{contract.optimal_renewal_timing}</p>
                          </div>
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">Price Sensitivity</div>
                            <p className="text-sm text-gray-700">{contract.price_sensitivity}</p>
                          </div>
                        </div>
                        {contract.risk_factors.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">Risk Factors</div>
                            <div className="space-y-2">
                              {contract.risk_factors.map((factor, i) => (
                                <div key={i} className="p-3 bg-amber-50 rounded-lg border border-amber-100">
                                  <div className="font-medium text-amber-800 text-sm">{factor.factor}</div>
                                  <p className="text-xs text-amber-700 mt-1">{factor.detail}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {contract.recommended_actions.length > 0 && (
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-2 uppercase">Recommended Actions</div>
                            <ul className="space-y-1">
                              {contract.recommended_actions.map((action, i) => (
                                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                  <span className="text-indigo-500 mt-0.5">{Icons.check}</span>
                                  {action}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Scenarios Tab */}
        {activeTab === "scenarios" && !isLoading && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">What-If Scenario Simulator</h3>
              
              <div className="grid grid-cols-4 gap-4 mb-4">
                {[
                  { id: "rate_change", label: "Rate Change", icon: Icons.chart },
                  { id: "client_loss", label: "Client Loss", icon: Icons.users },
                  { id: "revenue_forecast", label: "Forecast", icon: Icons.trending },
                  { id: "sla_standardization", label: "SLA Change", icon: Icons.shield },
                ].map(s => (
                  <button
                    key={s.id}
                    onClick={() => {
                      setScenarioType(s.id);
                      setScenarioParams({});
                      setScenarioResult(null);
                    }}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      scenarioType === s.id
                        ? "border-indigo-500 bg-indigo-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className={`mb-2 ${scenarioType === s.id ? "text-indigo-600" : "text-gray-400"}`}>{s.icon}</div>
                    <div className={`font-medium text-sm ${scenarioType === s.id ? "text-indigo-900" : "text-gray-700"}`}>{s.label}</div>
                  </button>
                ))}
              </div>

              {/* Scenario Params */}
              <div className="p-4 bg-gray-50 rounded-xl mb-4">
                {scenarioType === "rate_change" && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="text-xs font-medium text-gray-500 block mb-1">Rate Change %</label>
                      <input
                        type="number"
                        value={scenarioParams.rate_change_pct ?? 5}
                        onChange={e => setScenarioParams(p => ({ ...p, rate_change_pct: Number(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500 block mb-1">Tier (optional)</label>
                      <select
                        value={String(scenarioParams.tier ?? "")}
                        onChange={e => {
                          const val = e.target.value;
                          if (val) {
                            setScenarioParams(p => ({ ...p, tier: val }));
                          } else {
                            setScenarioParams(p => {
                              const { tier: _, ...rest } = p as Record<string, string | number> & { tier?: string };
                              return rest;
                            });
                          }
                        }}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                      >
                        <option value="">All Tiers</option>
                        <option value="Enterprise">Enterprise</option>
                        <option value="Business">Business</option>
                        <option value="Standard">Standard</option>
                        <option value="Starter">Starter</option>
                      </select>
                    </div>
                  </div>
                )}
                {scenarioType === "revenue_forecast" && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="text-xs font-medium text-gray-500 block mb-1">Months</label>
                      <input
                        type="number"
                        value={scenarioParams.months ?? 12}
                        onChange={e => setScenarioParams(p => ({ ...p, months: Number(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500 block mb-1">Monthly Churn %</label>
                      <input
                        type="number"
                        step="0.1"
                        value={scenarioParams.churn_rate_pct ?? 1}
                        onChange={e => setScenarioParams(p => ({ ...p, churn_rate_pct: Number(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-gray-500 block mb-1">Monthly Growth %</label>
                      <input
                        type="number"
                        step="0.1"
                        value={scenarioParams.growth_rate_pct ?? 2}
                        onChange={e => setScenarioParams(p => ({ ...p, growth_rate_pct: Number(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                      />
                    </div>
                  </div>
                )}
                {scenarioType === "client_loss" && (
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Client Names (comma-separated)</label>
                    <input
                      type="text"
                      placeholder="e.g., Sky Digital, Lakeside Fiber"
                      value={String(scenarioParams.client_names ?? "")}
                      onChange={e => setScenarioParams(p => ({ ...p, client_names: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                    />
                  </div>
                )}
                {scenarioType === "sla_standardization" && (
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Target SLA %</label>
                    <input
                      type="number"
                      step="0.01"
                      value={scenarioParams.target_sla ?? 99.7}
                      onChange={e => setScenarioParams(p => ({ ...p, target_sla: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm max-w-[200px]"
                    />
                  </div>
                )}
              </div>

              <button
                onClick={() => {
                  const params: Record<string, unknown> = { ...scenarioParams };
                  if (scenarioType === "client_loss" && typeof params.client_names === "string") {
                    params.client_names = params.client_names.split(",").map((s: string) => s.trim()).filter(Boolean);
                  }
                  setScenarioParams(params as Record<string, string | number>);
                  runScenario();
                }}
                className="px-6 py-2.5 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition-colors font-medium text-sm"
              >
                Run Simulation
              </button>
            </div>

            {/* Scenario Results */}
            {scenarioResult && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Simulation Results</h3>
                
                {scenarioResult.total_monthly_impact !== undefined && (
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <DashboardCard
                      title="Monthly Impact"
                      value={formatCurrency(Math.abs(scenarioResult.total_monthly_impact))}
                      subtitle={scenarioResult.total_monthly_impact >= 0 ? "Increase" : "Decrease"}
                      trend={`${scenarioResult.total_monthly_impact >= 0 ? "+" : ""}${((scenarioResult.total_monthly_impact / 3000000) * 100).toFixed(1)}%`}
                      trendUp={scenarioResult.total_monthly_impact >= 0}
                    />
                    <DashboardCard
                      title="Annual Impact"
                      value={formatCurrency(Math.abs(scenarioResult.total_annual_impact || 0))}
                      subtitle="Projected"
                    />
                    <DashboardCard
                      title="Contracts Affected"
                      value={String(scenarioResult.contracts?.length || 0)}
                      subtitle="In portfolio"
                    />
                  </div>
                )}

                {scenarioResult.projections && (
                  <div className="mt-4">
                    <div className="text-xs font-semibold text-gray-500 mb-3 uppercase">Revenue Projection</div>
                    <div className="h-48 flex items-end gap-1">
                      {scenarioResult.projections.map((p: { month: number; revenue: number }) => {
                        const maxRev = Math.max(...scenarioResult.projections!.map((x: { revenue: number }) => x.revenue));
                        const height = (p.revenue / maxRev) * 100;
                        return (
                          <div key={p.month} className="flex-1 flex flex-col items-center gap-1">
                            <div
                              className="w-full bg-indigo-500 rounded-t transition-all hover:bg-indigo-600"
                              style={{ height: `${height}%` }}
                              title={formatCurrency(p.revenue)}
                            />
                            <span className="text-[10px] text-gray-400">M{p.month}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <pre className="mt-4 p-4 bg-gray-50 rounded-xl text-xs text-gray-600 overflow-x-auto">
                  {JSON.stringify(scenarioResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Compare Tab */}
        {activeTab === "compare" && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Compare Contracts</h3>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Contract A</label>
                  <select
                    value={compareA}
                    onChange={e => setCompareA(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                  >
                    {contracts.map(c => (
                      <option key={c.id} value={c.id}>{c.company}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Contract B</label>
                  <select
                    value={compareB}
                    onChange={e => setCompareB(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                  >
                    {contracts.map(c => (
                      <option key={c.id} value={c.id}>{c.company}</option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                onClick={runComparison}
                disabled={isLoading || compareA === compareB}
                className="px-6 py-2.5 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition-colors font-medium text-sm disabled:opacity-50"
              >
                Compare
              </button>
            </div>

            {comparison && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-900 mb-2">
                  {comparison.contract_a} vs {comparison.contract_b}
                </h3>
                <p className="text-sm text-gray-600 mb-4">{comparison.summary}</p>

                {comparison.financial_impact.annual_revenue_delta !== 0 && (
                  <div className="p-4 bg-indigo-50 rounded-xl mb-4">
                    <div className="text-sm font-medium text-indigo-900">
                      Annual Revenue Difference: {formatCurrency(Math.abs(comparison.financial_impact.annual_revenue_delta))}
                      {comparison.financial_impact.annual_revenue_delta > 0 ? ` (${comparison.contract_b} higher)` : ` (${comparison.contract_a} higher)`}
                    </div>
                  </div>
                )}

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 px-3 font-medium text-gray-500">Field</th>
                        <th className="text-left py-2 px-3 font-medium text-gray-500">{comparison.contract_a}</th>
                        <th className="text-left py-2 px-3 font-medium text-gray-500">{comparison.contract_b}</th>
                        <th className="text-left py-2 px-3 font-medium text-gray-500">Delta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.differences.map((diff, i) => (
                        <tr key={i} className="border-b border-gray-100">
                          <td className="py-2 px-3 text-gray-900 font-medium">{diff.field}</td>
                          <td className={`py-2 px-3 ${diff.comparison === "a_better" ? "text-green-600 font-medium" : "text-gray-600"}`}>
                            {diff.contract_a}
                          </td>
                          <td className={`py-2 px-3 ${diff.comparison === "b_better" ? "text-green-600 font-medium" : "text-gray-600"}`}>
                            {diff.contract_b}
                          </td>
                          <td className="py-2 px-3 text-gray-400">{diff.delta || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Generate Tab */}
        {activeTab === "generate" && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Generate Contract from Description</h3>
              
              <div className="mb-4">
                <label className="text-xs font-medium text-gray-500 block mb-2">Contract Description</label>
                <textarea
                  value={generatePrompt}
                  onChange={e => setGeneratePrompt(e.target.value)}
                  placeholder="e.g., Create an Enterprise tier contract for TechCorp with 150,000 subscribers, 2.5% revenue share, 99.9% billing SLA, 48-month term, Net 15 payment terms, and SOC 2 compliance required."
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm min-h-[120px] resize-none"
                />
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                <span className="text-xs text-gray-400">Examples:</span>
                {[
                  "Business tier, 50K subs, 3% rev share, 24 months",
                  "Starter tier, 10K subs, per-transaction $0.35, 12 months",
                  "Enterprise, 200K subs, hybrid model, 60 months",
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => setGeneratePrompt(example)}
                    className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-lg hover:bg-gray-200"
                  >
                    {example}
                  </button>
                ))}
              </div>

              <button
                onClick={generateContract}
                disabled={isLoading || !generatePrompt.trim()}
                className="px-6 py-2.5 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition-colors font-medium text-sm disabled:opacity-50"
              >
                Generate Contract
              </button>
            </div>

            {generatedContract && (
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-900">Generated Contract</h3>
                  <button
                    onClick={() => navigator.clipboard.writeText(generatedContract.document)}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg"
                  >
                    {Icons.copy}
                    Copy
                  </button>
                </div>

                <div className="grid grid-cols-4 gap-3 mb-4">
                  {[
                    ["Client", generatedContract.contract_data.client_name as string],
                    ["Tier", generatedContract.contract_data.client_tier as string],
                    ["Model", generatedContract.contract_data.billing_model as string],
                    ["Monthly", formatCurrency(generatedContract.contract_data.our_monthly_revenue as number)],
                  ].map(([label, value]) => (
                    <div key={label} className="p-3 bg-gray-50 rounded-xl">
                      <div className="text-xs text-gray-400">{label}</div>
                      <div className="font-medium text-gray-900">{value}</div>
                    </div>
                  ))}
                </div>

                <pre className="p-4 bg-gray-900 text-gray-100 rounded-xl text-xs overflow-x-auto whitespace-pre-wrap font-mono max-h-[400px] overflow-y-auto">
                  {generatedContract.document}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Message Actions
const MessageActions = ({ 
  message, 
  onRegenerate, 
  onEdit,
  onCopy,
  isLoading 
}: { 
  message: Message; 
  onRegenerate?: () => void;
  onEdit?: () => void;
  onCopy: () => void;
  isLoading: boolean;
}) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = () => {
    onCopy();
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity ${isUser ? "justify-end" : ""}`}>
      <button
        onClick={handleCopy}
        className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
        title="Copy"
      >
        {copied ? Icons.check : Icons.copy}
      </button>
      {isUser && onEdit && (
        <button
          onClick={onEdit}
          className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          title="Edit"
          disabled={isLoading}
        >
          {Icons.edit}
        </button>
      )}
      {!isUser && onRegenerate && (
        <button
          onClick={onRegenerate}
          className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          title="Regenerate"
          disabled={isLoading}
        >
          {Icons.refresh}
        </button>
      )}
    </div>
  );
};

// Message Bubble
const MessageBubble = ({ 
  message, 
  onRegenerate,
  onEdit,
  isLoading,
  isEditing,
  editValue,
  onEditChange,
  onEditSubmit,
  onEditCancel,
}: { 
  message: Message;
  onRegenerate?: () => void;
  onEdit?: () => void;
  isLoading: boolean;
  isEditing?: boolean;
  editValue?: string;
  onEditChange?: (v: string) => void;
  onEditSubmit?: () => void;
  onEditCancel?: () => void;
}) => {
  const isUser = message.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
  };

  return (
    <div className={`group flex items-start gap-3 py-4 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
        isUser 
          ? "bg-gray-100" 
          : "bg-gradient-to-br from-indigo-500 to-purple-500 text-white shadow-sm"
      }`}>
        {isUser ? <span className="text-xs font-semibold text-gray-500">You</span> : Icons.sparkles}
      </div>

      <div className={`flex-1 max-w-2xl ${isUser ? "text-right" : ""}`}>
        <div className={`inline-block text-left ${isUser ? "max-w-[85%]" : "w-full"}`}>
          {isEditing && isUser ? (
            <div className="bg-gray-50 rounded-2xl p-4 border border-gray-200">
              <textarea
                value={editValue}
                onChange={(e) => onEditChange?.(e.target.value)}
                className="w-full bg-transparent text-[15px] text-gray-900 resize-none focus:outline-none min-h-[80px]"
                autoFocus
              />
              <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-200">
                <button
                  onClick={onEditCancel}
                  className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={onEditSubmit}
                  className="px-4 py-2 text-sm bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors font-medium"
                >
                  Save & Submit
                </button>
              </div>
            </div>
          ) : (
            <>
              {isUser ? (
                <div className="bg-indigo-500 text-white rounded-2xl rounded-tr-md px-4 py-3 shadow-sm text-[15px] leading-relaxed">
                  {message.content.split('\n').map((line, i) => (
                    <React.Fragment key={i}>
                      {line}
                      {i < message.content.split('\n').length - 1 && <br />}
                    </React.Fragment>
                  ))}
                </div>
              ) : (
                <div className="prose prose-sm max-w-none text-gray-700 prose-headings:text-gray-900 prose-headings:font-semibold prose-h2:text-lg prose-h2:mt-4 prose-h2:mb-2 prose-p:my-2 prose-strong:text-gray-900 prose-table:my-3 prose-table:w-full prose-table:border prose-table:border-gray-200 prose-table:rounded-lg prose-table:overflow-hidden prose-th:bg-gray-50 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-th:text-xs prose-th:font-semibold prose-th:text-gray-600 prose-th:border-b prose-th:border-gray-200 prose-td:px-3 prose-td:py-2 prose-td:text-sm prose-td:border-b prose-td:border-gray-100 prose-ul:my-2 prose-ul:pl-4 prose-li:my-1 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              )}

              {!isUser && message.sources && message.sources.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {message.sources.slice(0, 4).map((s, idx) => (
                    <span
                      key={`${message.id}-src-${idx}`}
                      className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg bg-gray-100 text-gray-500"
                    >
                      {Icons.doc}
                      {s.source.replace('data/', '').replace('.pdf', '').replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              )}

              <MessageActions
                message={message}
                onRegenerate={onRegenerate}
                onEdit={onEdit}
                onCopy={handleCopy}
                isLoading={isLoading}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// Main App
export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showBrowser, setShowBrowser] = useState(false);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [contractsLoading, setContractsLoading] = useState(false);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [activeView, setActiveView] = useState<ActiveView>("dashboard");
  
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    fetch(`${API_BASE}/metrics`)
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(() => setMetrics(null));
    
    // Also load contracts for dashboard
    fetch(`${API_BASE}/contracts`)
      .then(res => res.json())
      .then(data => setContracts(data.contracts || []))
      .catch(() => setContracts([]));
  }, []);

  useEffect(() => {
    if (showBrowser && contracts.length === 0) {
      setContractsLoading(true);
      fetch(`${API_BASE}/contracts`)
        .then(res => res.json())
        .then(data => setContracts(data.contracts || []))
        .catch(() => setContracts([]))
        .finally(() => setContractsLoading(false));
    }
  }, [showBrowser, contracts.length]);

  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", "default");
    
    try {
      await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
    } catch (e) {
      console.error("Upload failed:", e);
    }
  };

  const send = async (text: string, files: File[] = []) => {
    if ((!text.trim() && files.length === 0) || isLoading) return;

    for (const file of files) {
      await uploadFile(file);
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      attachments: files.map(f => ({ name: f.name, type: f.type })),
    };

    setMessages((m) => [...m, userMessage]);
    setInput("");
    setAttachments([]);
    setIsLoading(true);
    if (inputRef.current) inputRef.current.style.height = "auto";

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });
      const data = await res.json();
      setMessages((m) => [...m, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        sources: data.sources,
      }]);
    } catch {
      setMessages((m) => [...m, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Unable to connect. Please verify the backend service is running.",
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const regenerate = useCallback(async () => {
    if (isLoading || messages.length < 2) return;
    
    const lastUserMsgIndex = [...messages].reverse().findIndex(m => m.role === "user");
    if (lastUserMsgIndex === -1) return;
    
    const actualIndex = messages.length - 1 - lastUserMsgIndex;
    const lastUserMsg = messages[actualIndex];
    const newMessages = messages.slice(0, actualIndex + 1);
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: lastUserMsg.content,
          history: newMessages.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
        }),
      });
      const data = await res.json();
      setMessages((m) => [...m, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        sources: data.sources,
      }]);
    } catch {
      setMessages((m) => [...m, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Failed to regenerate. Please try again.",
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [messages, isLoading]);

  const startEdit = (msgId: string) => {
    const msg = messages.find(m => m.id === msgId);
    if (msg) {
      setEditingId(msgId);
      setEditValue(msg.content);
    }
  };

  const submitEdit = async () => {
    if (!editingId || !editValue.trim() || isLoading) return;
    
    const msgIndex = messages.findIndex(m => m.id === editingId);
    if (msgIndex === -1) return;
    
    const newMessages = messages.slice(0, msgIndex);
    setMessages(newMessages);
    setEditingId(null);
    await send(editValue);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");

        try {
          const res = await fetch(`${API_BASE}/stt`, { method: "POST", body: formData });
          const data = await res.json();
          if (data.text) setInput((prev) => prev + (prev ? " " : "") + data.text);
        } catch (e) {
          console.error("STT failed:", e);
        }
        
        stream.getTracks().forEach(track => track.stop());
      };

      setIsRecording(true);
      mediaRecorder.start();

      setTimeout(() => {
        if (mediaRecorder.state === "recording") {
          mediaRecorder.stop();
          setIsRecording(false);
        }
      }, 10000);

      const stopHandler = () => {
        if (mediaRecorder.state === "recording") {
          mediaRecorder.stop();
          setIsRecording(false);
        }
        document.removeEventListener("click", stopHandler);
      };
      setTimeout(() => document.addEventListener("click", stopHandler), 100);
    } catch (e) {
      console.error("Mic access denied:", e);
    }
  };

  const handleContractSelect = (contract: Contract) => {
    const query = `Show me all details for the ${contract.company} billing agreement (${contract.contract_number}), including fee structure, payment terms, SLA commitments, and compliance requirements.`;
    send(query);
    setShowBrowser(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input, attachments);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) setAttachments(prev => [...prev, ...Array.from(files)]);
    e.target.value = "";
  };

  return (
    <div className="min-h-screen bg-[#f8f9fb] flex flex-col">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,image/*"
        multiple
        className="hidden"
        onChange={handleFileSelect}
      />

      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {Icons.logo}
            <span className="text-[15px] font-semibold text-gray-900">BillFlow</span>
            
            {/* Navigation Tabs */}
            <div className="hidden sm:flex items-center gap-1 ml-6 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveView("dashboard")}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                  activeView === "dashboard" 
                    ? "bg-white text-gray-900 shadow-sm" 
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveView("chat")}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                  activeView === "chat" 
                    ? "bg-white text-gray-900 shadow-sm" 
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setActiveView("intelligence")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                  activeView === "intelligence" 
                    ? "bg-white text-gray-900 shadow-sm" 
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <span className="text-purple-500">{Icons.brain}</span>
                Intelligence
              </button>
              <button
                onClick={() => setActiveView("revenue")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                  activeView === "revenue" 
                    ? "bg-white text-gray-900 shadow-sm" 
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <span className="text-emerald-500">{Icons.dollar}</span>
                Revenue
              </button>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {metrics && (
              <div className="hidden md:flex items-center gap-1 px-2 py-1 bg-gray-50 rounded-lg mr-2">
                <span className="text-xs text-gray-400">{metrics.total_contracts} clients</span>
                <span className="text-gray-300">·</span>
                <span className="text-xs font-medium text-indigo-600">${(metrics.monthly_revenue / 1000).toFixed(0)}K/mo</span>
              </div>
            )}
            <button
              onClick={() => setShowBrowser(true)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
            >
              {Icons.folder}
              <span className="hidden sm:inline">Clients</span>
            </button>
            {activeView === "chat" && messages.length > 0 && (
              <button
                onClick={() => setMessages([])}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
              >
                {Icons.plus}
                <span>New</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex flex-col">
        {activeView === "dashboard" && (
          <WelcomeDashboard 
            onQuery={(q) => { setActiveView("chat"); send(q); }} 
            metrics={metrics} 
            contracts={contracts}
          />
        )}
        
        {activeView === "chat" && (
          messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center px-6">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25 mb-6">
                {Icons.sparkles}
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Ask anything about your contracts</h2>
              <p className="text-gray-400 text-center max-w-md mb-8">
                Query SLAs, compare clients, analyze revenue, or get insights from your billing agreements.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
                {[
                  "Show me all Enterprise tier contracts",
                  "Which contracts are expiring soon?",
                  "Compare SLAs across all clients",
                  "What's our total annual contract value?",
                ].map((q, i) => (
                  <button
                    key={i}
                    onClick={() => send(q)}
                    className="px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm text-gray-600 hover:border-indigo-500 hover:text-indigo-600 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-3xl mx-auto px-6 py-6">
                {messages.map((m, idx) => {
                  const isLastAssistant = m.role === "assistant" && idx === messages.length - 1;
                  return (
                    <MessageBubble
                      key={m.id}
                      message={m}
                      onRegenerate={isLastAssistant ? regenerate : undefined}
                      onEdit={m.role === "user" ? () => startEdit(m.id) : undefined}
                      isLoading={isLoading}
                      isEditing={editingId === m.id}
                      editValue={editValue}
                      onEditChange={setEditValue}
                      onEditSubmit={submitEdit}
                      onEditCancel={cancelEdit}
                    />
                  );
                })}
                {isLoading && <TypingIndicator />}
                <div ref={endRef} className="h-4" />
              </div>
            </div>
          )
        )}
        
        {activeView === "intelligence" && (
          <IntelligenceDashboard contracts={contracts} />
        )}
        
        {activeView === "revenue" && (
          <RevenueCommandCenter />
        )}
      </main>

      {/* Input - Only show for chat view */}
      {activeView === "chat" && (
        <div className="sticky bottom-0 bg-gradient-to-t from-[#f8f9fb] via-[#f8f9fb] to-transparent pt-6 pb-6">
          <div className="max-w-3xl mx-auto px-6">
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {attachments.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-200 shadow-sm text-sm">
                    {Icons.doc}
                    <span className="text-gray-600 max-w-[150px] truncate">{file.name}</span>
                    <button onClick={() => setAttachments(a => a.filter((_, i) => i !== idx))} className="text-gray-400 hover:text-gray-600">
                      {Icons.x}
                    </button>
                  </div>
                ))}
              </div>
            )}

            <form
              onSubmit={(e) => { e.preventDefault(); send(input, attachments); }}
              className="bg-white rounded-2xl shadow-lg shadow-gray-200/50 border border-gray-100 overflow-hidden"
            >
              <div className="flex items-end p-3 gap-3">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-xl hover:bg-gray-50 transition-colors"
                  title="Attach file"
                >
                  {Icons.attach}
                </button>

                <textarea
                  ref={inputRef}
                  rows={1}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    e.target.style.height = "auto";
                    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about contracts, SLAs, or revenue..."
                  className="flex-1 bg-transparent resize-none text-[15px] text-gray-900 placeholder:text-gray-400 focus:outline-none min-h-[40px] max-h-[120px] py-2"
                />

                <button
                  type="button"
                  onClick={startRecording}
                  className={`p-2 rounded-xl transition-colors ${
                    isRecording 
                      ? "bg-red-500 text-white animate-pulse" 
                      : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"
                  }`}
                  title={isRecording ? "Recording..." : "Voice input"}
                >
                  {Icons.mic}
                </button>

                <button
                  type="submit"
                  disabled={isLoading || (!input.trim() && attachments.length === 0)}
                  className="p-2.5 rounded-xl bg-indigo-500 text-white hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  {Icons.send}
                </button>
              </div>
            </form>
            
            <p className="text-center text-xs text-gray-400 mt-3">
              AI-powered contract analysis · {metrics?.total_contracts || 0} agreements indexed
            </p>
          </div>
        </div>
      )}

      {/* Contract Browser */}
      {showBrowser && (
        <>
          <div className="fixed inset-0 bg-gray-900/20 backdrop-blur-sm z-40" onClick={() => setShowBrowser(false)} />
          <ContractBrowser
            contracts={contracts}
            isLoading={contractsLoading}
            onSelect={handleContractSelect}
            onClose={() => setShowBrowser(false)}
          />
        </>
      )}
    </div>
  );
}
