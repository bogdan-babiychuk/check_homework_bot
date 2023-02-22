import time 
import telegram
import os
from dotenv import load_dotenv
import requests
from dotenv import load_dotenv 
from logging.handlers import RotatingFileHandler
import logging
from http import HTTPStatus

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log', 
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('YANDEX_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])

    

def send_message(bot, message):
    """ Сообщает удаолсь ли отправить сообщение или нет """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Сообщение <{message}> отправлено')
    except Exception:
        logging.error(f'Сообщение <{message}> не отправлено')
        raise('Сообщение не отправлено')


def get_api_answer(timestamp):
    """ Делаем API запрос к указаному URL и проверям на доступность"""
    try:
        payload = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            raise 'Ошибка статуса в ответе.'
        response_api = response.json()
        return response_api
    except Exception:
        logging.ERROR(f'ENDPOINT не доступен')
        
    

def check_response(response):
    """ Проверка ответа от API, соответствуют ли типы днанных ожидаемым"""
    if not isinstance(response, dict):
        logging.error('Ошибка в ответе API')
        raise TypeError('Ошибка данных')

    elif 'homeworks' not in response.keys():
        logging.error('Ключ homeworks не найден')
        raise Exception('Нет ответа API')

    elif not isinstance(response['homeworks'], list):
        raise TypeError('Ожидается тип list.')

    elif response['homeworks'] is None:
        logging.debug('Список Пустой')
    
    return response

        

def parse_status(homework)-> str: 
    """ Проверка обновленние статуса запроса"""
    try:
        homework_status = homework.get('status')
        homework_name = homework['homework_name']
        verdict = str(HOMEWORK_VERDICTS[homework_status])
        if 'homework_name' not in homework:
            logging.error('Такого имени не существует')
            raise KeyError(f'Имя {homework_name}, не существует')
    
        if homework_status not in HOMEWORK_VERDICTS:
            logging.error('Отсутствие статуса')
            raise KeyError(f'Статус {homework_status}, не существует')

    except KeyError as error:
        logger.error(f'API ответ не содержит искомого ключа : {error}')
        return (f"Изменился статус проверки работы {homework_name}. {verdict}")
         



def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Какой то токен отсутствует')
        raise ValueError('Проверьте переменные окружения')
    
    timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    
    while True:
        timestamp = int(time.time())
        empty_status = ''
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)[0]
            message = parse_status(homework)
            if empty_status != message:
                send_message(bot, message)

            else:
                logging.error('Чучуть надо подождать')

        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            send_message(bot, f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)
                

if __name__ == '__main__':
    main()
