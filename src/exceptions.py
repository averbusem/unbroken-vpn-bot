class ServiceException(Exception):
    """Базовый класс всех ошибок сервисного слоя."""

    pass


# === Технические ошибки сервисов (неожиданные) ===
class UserException(ServiceException):
    """Неожиданные технические ошибки UserService."""

    pass


class SubscriptionException(ServiceException):
    """Неожиданные технические ошибки SubscriptionService."""

    pass


class ReferralException(ServiceException):
    """Неожиданные технические ошибки ReferralService."""

    pass


class PaymentException(ServiceException):
    """Неожиданные технические ошибки PaymentService."""

    pass


# === Бизнес-исключения (ожидаемые, обрабатываемые) ===
class BusinessException(ServiceException):
    """Базовый класс для бизнес-логики исключений."""

    pass


class TariffNotFoundException(BusinessException):
    """Тариф не найден."""

    pass


class UserNotFoundException(BusinessException):
    """Пользователь не найден."""

    pass


class SelfReferralException(BusinessException):
    """Попытка использовать собственный реферальный код."""

    pass


class SubscriptionAlreadyExistException(BusinessException):
    """У пользователя уже есть подписка."""

    pass


class ReferralAlreadyExistException(BusinessException):
    """Пользователь уже использовал реферальный код."""

    pass


class SubscriptionNotActiveException(BusinessException):
    """Подписка не активна."""

    pass


class SubscriptionNotFoundException(BusinessException):
    """Подписка не найдена."""

    pass


class PaymentNotFoundException(BusinessException):
    """Платеж не найден."""

    pass


class ReferralCodeGenerationException(BusinessException):
    """Все попытки создания кода неудачны."""

    pass


class TrialAlreadyUsedException(BusinessException):
    """Пробный период уже использован."""

    pass
