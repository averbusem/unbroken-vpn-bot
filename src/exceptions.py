# src/exception.py


class ServiceException(Exception):
    """Базовый класс всех ошибок сервисного слоя."""

    pass


# === Referral domain ===


class ReferralException(ServiceException):
    """Ошибки, для ReferralService."""

    pass


class UserNotFoundException(ReferralException):
    """Пользователь не найден."""

    pass


# === User domain ===


class UserException(ServiceException):
    """Ошибки для UserService."""

    pass


class SelfReferralException(UserException):
    """Реферальный код не может быть использован для регистрации пользователя самого себя."""

    pass


class SubscriptionAlreadyExistException(UserException):
    """Пользователь уже зарегистрирован."""

    pass


class ReferralAlreadyExistException(UserException):
    """Пользователь уже зарегистрирован с таким реферальным кодом."""

    pass


class ReferralCodeGenerationException(UserException):
    """Все попытки создания кода неудачны."""

    pass


# === Subscription domain ===


class SubscriptionException(ServiceException):
    """Ошибки для SubscriptionService."""

    pass


class SubscriptionNotActiveException(SubscriptionException):
    """Подписка не активна у пользователя."""

    pass


class SubscriptionNotFoundException(SubscriptionException):
    """Подписка не найдена для пользователя."""

    pass


# === Payment domain ===


class PaymentException(ServiceException):
    """Ошибки для PaymentService."""

    pass


class TariffNotFoundException(PaymentException):
    pass


class PaymentNotFoundException(PaymentException):
    pass
