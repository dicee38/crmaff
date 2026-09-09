from app.models.enums import LeadStatus

_STATUS_RANK = {
    LeadStatus.new: 0,
    LeadStatus.contacted: 1,
    LeadStatus.qualified: 2,
    LeadStatus.registered: 3,
    LeadStatus.kyc_pending: 4,
    LeadStatus.kyc_approved: 5,
    LeadStatus.ftd: 6,
    LeadStatus.active: 7,
    LeadStatus.churned: 8,
    LeadStatus.unsubscribed: 8,
}

# Событие Binolla -> статус лида. Только для событий, однозначно двигающих
# воронку вперёд; email_confirmed не меняет статус (нет прямого аналога в
# нашей модели статусов - см. CLAUDE.md).
BINOLLA_EVENT_TO_LEAD_STATUS = {
    "registration": LeadStatus.registered,
    "ftd": LeadStatus.ftd,
    "deposit": LeadStatus.active,
}


def is_forward_transition(current: LeadStatus, target: LeadStatus) -> bool:
    """Статус лида не должен откатываться назад при повторных/задержанных
    постбэках (напр. поздний 'reg' после уже случившегося 'ftd')."""
    return _STATUS_RANK[target] > _STATUS_RANK[current]
