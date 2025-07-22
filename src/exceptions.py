# src/exception.py


class ServiceException(Exception):
    """Базовый класс ошибок сервисного слоя"""

    pass


class ReferralException(Exception):
    """Ошибка при обработке реферального кода"""

    pass


class SubscriptionAlreadyExist(ReferralException):
    """Пользователь уже зарегистрирован"""

    pass


class SelfReferralException(ReferralException):
    """Реферальный код не может быть использован для регистрации пользователя самого себя"""

    pass


class ReferralAlreadyExist(ReferralException):
    """Пользователь уже зарегистрирован с таким реферальным кодом"""

    pass


class UserNotFoundException(ServiceException):
    """Пользователь не найден"""

    pass


class SubscriptionNotFoundException(ServiceException):
    """Подписка не найдена для пользователя."""

    pass


class SubscriptionNotActiveException(ServiceException):
    """Подписка не найдена для пользователя."""

    pass


class PaymentException(Exception):
    pass


class TariffNotFoundException(PaymentException):
    pass


class PaymentNotFoundException(PaymentException):
    pass
