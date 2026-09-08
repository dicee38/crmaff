export type UserRole =
  | "admin"
  | "tech_lead"
  | "compliance"
  | "affiliate_manager"
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

export interface AffiliateEvent {
  id: string;
  lead_id: string | null;
  partner: string;
  event_type: "registration" | "kyc_approved" | "ftd" | "deposit" | "withdrawal" | "commission" | "chargeback";
  amount: number | null;
  currency: string | null;
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
