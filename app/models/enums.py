import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    tech_lead = "tech_lead"
    compliance = "compliance"
    affiliate_manager = "affiliate_manager"
    mop_lead = "mop_lead"
    sales_manager = "sales_manager"
    smm_manager = "smm_manager"
    analyst = "analyst"


class Dialect(str, enum.Enum):
    levantine = "levantine"
    moroccan_darija = "moroccan_darija"
    gulf_najdi = "gulf_najdi"
    other = "other"


class SourceChannel(str, enum.Enum):
    telegram_ads = "telegram_ads"
    organic = "organic"
    existing_base = "existing_base"
    referral = "referral"


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    registered = "registered"
    kyc_pending = "kyc_pending"
    kyc_approved = "kyc_approved"
    ftd = "ftd"
    active = "active"
    churned = "churned"
    unsubscribed = "unsubscribed"


class ConsentStatus(str, enum.Enum):
    granted = "granted"
    revoked = "revoked"
    unknown = "unknown"


class TrackingEventType(str, enum.Enum):
    click = "click"
    landing_view = "landing_view"
    lead_created = "lead_created"
    conversation_started = "conversation_started"
    manager_assigned = "manager_assigned"
    registration = "registration"
    kyc = "kyc"
    ftd = "ftd"
    deposit = "deposit"
    withdrawal = "withdrawal"
    affiliate_commission = "affiliate_commission"
    unsubscribe = "unsubscribe"
    chargeback = "chargeback"


class CommunicationChannel(str, enum.Enum):
    telegram = "telegram"
    whatsapp = "whatsapp"
    webchat = "webchat"


class CommunicationDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class AffiliateEventType(str, enum.Enum):
    registration = "registration"
    email_confirmed = "email_confirmed"
    kyc_approved = "kyc_approved"
    ftd = "ftd"
    deposit = "deposit"
    withdrawal = "withdrawal"
    commission = "commission"
    chargeback = "chargeback"


class AffiliateEventSource(str, enum.Enum):
    postback = "postback"
    manual = "manual"


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    archived = "archived"


class CommissionModel(str, enum.Enum):
    cpa = "cpa"
    revshare = "revshare"
    hybrid = "hybrid"


class OfferStatus(str, enum.Enum):
    active = "active"
    paused = "paused"


class TaskStatus(str, enum.Enum):
    open = "open"
    done = "done"
    cancelled = "cancelled"
