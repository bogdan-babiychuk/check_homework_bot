class ErrorMessageException(Exception):
    """Сообщение не доставлено"""
    pass 


class ErrorStatusCode(Exception):
    """Статус запроса не равен ожидаемому"""
    pass
