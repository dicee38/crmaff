export type UserRole =
  | "admin"
  | "tech_lead"
  | "compliance"
  | "affiliate_manager"
  | "mop_lead"
  | "sales_manager"
  | "smm_manager"
  | "analyst";

export type LeadStatus =
  | "new"
  | "contacted"
  | "qualified"
  | "registered"
  | "kyc_pending"
  | "kyc_approved"
  | "ftd"
  | "active"
  | "churned"
  | "unsubscribed";

export type SourceChannel = "telegram_ads" | "organic" | "existing_base" | "referral";
export type Dialect = "levantine" | "moroccan_darija" | "gulf_najdi" | "other";
export type ConsentStatus = "granted" | "revoked" | "unknown";

export interface CurrentUser {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  geo_coverage: string[];
  dialects: string[];
  is_active: boolean;
}

export interface Lead {
  lead_id: string;
  external_click_id: string | null;
  geo: string | null;
  language: string | null;
  dialect: Dialect | null;
  source_channel: SourceChannel;
  status: LeadStatus;
  assigned_manager_id: string | null;
  offer_id: string | null;
  telegram_user_id: string | null;
  consent_status: ConsentStatus;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  items: Lead[];
  next_cursor: string | null;
}

export interface AcquisitionInfo {
  source_channel: SourceChannel;
  click_id: string | null;
  campaign_id: string | null;
  adset_id: string | null;
  creative_id: string | null;
  landing_id: string | null;
  first_seen_at: string | null;
}

export interface ManagerSummary {
  id: string;
  full_name: string;
  email: string;
}

export interface Communication {
  id: string;
  lead_id: string;
  manager_id: string | null;
  channel: "telegram" | "whatsapp" | "webchat";
  direction: "inbound" | "outbound";
  message_text: string | null;
  is_ai_suggested: boolean;
  created_at: string;
}

export type AffiliateEventType =
  | "registration"
  | "email_confirmed"
  | "kyc_approved"
  | "ftd"
  | "deposit"
  | "withdrawal"
  | "commission"
  | "chargeback";

export interface AffiliateEvent {
  id: string;
  lead_id: string | null;
  partner: string;
  source: "postback" | "manual";
  entered_by: string | null;
  channel: string | null;
  event_type: AffiliateEventType;
  amount: number | null;
  currency: string | null;
  validation_flags: Record<string, boolean> | null;
  received_at: string;
  processed_at: string | null;
}

export interface LeadCard {
  profile: Lead;
  acquisition: AcquisitionInfo | null;
  manager: ManagerSummary | null;
  communications: Communication[];
  affiliate: AffiliateEvent[];
}

// --- Sprint 5 ---

export interface FunnelData {
  clicks: number;
  leads_created: number;
  manager_assigned: number;
  registered: number;
  ftd: number;
  commission_total: number;
}

export interface KpiData {
  total_leads: number;
  total_registered: number;
  total_ftd: number;
  total_revenue: number;
  lead2reg_pct: number;
  reg2fd_pct: number;
}

export interface CashflowRow {
  key: string | null;
  label: string | null;
  reg: number;
  fd_count: number;
  fd_sum: number;
  rd_count: number;
  rd_sum: number;
  cashflow: number;
  lead2reg_pct: number | null;
  reg2fd_pct: number;
}

export interface CashflowReport {
  total: CashflowRow;
  groups: CashflowRow[];
}

export type LeaderboardMetric = "cashflow" | "fd_revenue_per_lead" | "lead_to_fd" | "fd_to_rd";
export type LeaderboardPeriod = "week" | "month";

export interface LeaderboardEntry {
  rank: number;
  manager_id: string;
  label: string;
  value: number;
  is_current_user: boolean;
}

export interface LeaderboardData {
  metric: LeaderboardMetric;
  period: LeaderboardPeriod;
  total_participants: number;
  rows: LeaderboardEntry[];
  current_user_rank: number | null;
  delta_to_rank_above: number | null;
  delta_over_rank_below: number | null;
}

export interface ActionRow {
  id: string;
  received_at: string;
  partner: string;
  channel: string | null;
  event_type: AffiliateEventType;
  source: "postback" | "manual";
  player_external_id: string | null;
  amount: number | null;
  currency: string | null;
  lead_id: string | null;
  manager_full_name: string | null;
  manager_role: string | null;
  validation_flags: Record<string, boolean> | null;
}

export interface ActionListResponse {
  items: ActionRow[];
  next_cursor: string | null;
  aggregates: {
    total_actions: number;
    lead_count: number;
    deposit_count: number;
    deposit_sum: number;
  };
}

export interface ManualActionCreate {
  player_id: string;
  partner_name: string;
  channel?: string;
  event_type: "registration" | "ftd" | "deposit" | "withdrawal" | "chargeback";
  amount?: string;
  currency?: string;
  occurred_at?: string;
}

export interface Partner {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface Channel {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export type TaskStatus = "open" | "done" | "cancelled";

export interface Task {
  id: string;
  lead_id: string;
  manager_id: string | null;
  title: string;
  due_at: string | null;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: Task[];
  next_cursor: string | null;
}
