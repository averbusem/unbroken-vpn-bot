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


class SubscriptionException(ServiceException):
    """Ошибка при работе с подпиской"""

    pass


class PaymentException(ServiceException):
    """Ошибка при оплате или создании платежа"""

    pass
