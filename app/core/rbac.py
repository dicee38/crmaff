from app.models.enums import UserRole

# Кто может видеть ВСЕХ лидов (не только своих).
# mop_lead по матрице видит только "свою команду" - в схеме пока нет понятия
# команды/иерархии менеджеров (появится в Sprint 5 вместе с cashflow-отчётом
# и лидербордом), поэтому временно приравниваем к полному доступу, как
# affiliate_manager/compliance. Сузить до реальной команды - после того как
# появится team_id/иерархия в модели users.
CAN_VIEW_ALL_LEADS = {
    UserRole.admin,
    UserRole.affiliate_manager,
    UserRole.mop_lead,
    UserRole.compliance,
    UserRole.analyst,
}

# Кто может видеть revenue/commission данные
CAN_VIEW_REVENUE = {
    UserRole.admin,
    UserRole.affiliate_manager,
    UserRole.mop_lead,
    UserRole.compliance,
    UserRole.analyst,
}

# Кто может назначать менеджера на лида
CAN_ASSIGN_MANAGER = {
    UserRole.admin,
    UserRole.affiliate_manager,
}

# Кто может редактировать лида (sales_manager — только своих, проверяется отдельно)
CAN_EDIT_LEAD = {
    UserRole.admin,
    UserRole.affiliate_manager,
    UserRole.sales_manager,
}

# Кто может управлять пользователями
CAN_MANAGE_USERS = {
    UserRole.admin,
}

# Кто может настраивать webhook/интеграции
CAN_MANAGE_INTEGRATIONS = {
    UserRole.admin,
}

# Кто может просматривать audit logs
CAN_VIEW_AUDIT_LOGS = {
    UserRole.admin,
    UserRole.compliance,
}

# Аналитик не видит PII — используется для маскирования полей в сериализации
ANALYST_HIDDEN_FIELDS = {"telegram_user_id", "external_click_id"}
