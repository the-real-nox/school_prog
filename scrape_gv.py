from enum import Enum
import sqlite3
from colorama import Fore, Style
from colorama import init as init_colorama
from datetime import date, datetime, timedelta
import configparser
from requests import get
from bs4 import BeautifulSoup
import json
from re import compile
import locale

# Pretty simple implementation, doesn't have to be too fancy
class CustomLogger():
    def ok(self, msg: str) -> None:
        print(Fore.GREEN + f'[+] {msg}' + Style.RESET_ALL)
    
    def fatal(self, msg: str) -> None:
        print(Fore.RED + Style.BRIGHT + f'[-] {msg}' + Style.RESET_ALL)

    def warn(self, msg: str) -> None:
        print(Fore.YELLOW + f'[!] {msg}' + Style.RESET_ALL)

    def info(self, msg: str) -> None:
        print(Fore.BLACK + Style.BRIGHT + f'[#] {msg}' + Style.RESET_ALL)
logger = CustomLogger()
BASE_URL = 'https://www.bmbwf.gv.at/Themen/schule/schulpraxis/termine/ferientermine_{start_year}_{end_year}.html'

class Config():
    def __init__(self):
        parser = configparser.ConfigParser()
        parser.read('./config.cfg')
        if not parser.has_section('web_scraper'):

            parser['web_scraper'] = {
                'start_year': date.today().year,
                'end_year': date.today().year + 1
            }

            with open('config.cfg', 'w') as conf_file:
                parser.write(conf_file)

        self.start_year = parser.getint('web_scraper', 'start_year') % 2000
        self.end_year = parser.getint('web_scraper', 'end_year') % 2000

        if self.start_year > date.today().year:
            raise ValueError('`start_year` must be smaller than current year!')
        
        if self.start_year > self.end_year:
            raise ValueError('`start_year` must be smaller than `end_year`!')
        
        if self.start_year < 20:
            raise ValueError('`start_year` must be 20 at minimum!')

        logger.ok('Config initialized!')

class HolidayDate:
    STATES = {
        'Steiermark': 2**0,
        'Kärnten': 2**1,
        'Salzburg': 2**2,
        'Tirol': 2**3,
        'Burgenland': 2**4,
        'Oberösterreich': 2**5,
        'Niederösterreich': 2**6,
        'Vorarlberg': 2**7,
        'Wien': 2**8,
        'alle Bundesländer': 2**9
    }


    def __init__(self, start: date, end: date, states: list[str]):
        self.start = start
        self.end = end
        self.states = self.__encode_states(states)


    @classmethod
    def __encode_states(cls, states: list[str]):
        bitmask = 0

        for state in states:
            if state not in cls.STATES:
                state = state.replace(' ', '') # remove random spaces (don't know why they are there)
                logger.warn(f'Unknown state: {state}')
                print(states)
                continue

            bitmask |= cls.STATES[state]

        return bitmask


    def toJSON(self):
        return f"{self.start}, {self.end}, {self.states}"


class Holiday:
    def __init__(self, name: str, dates: dict):
        self.name = name
        self.dates = dates
        

def init_db(cur: sqlite3.Cursor) -> None:
    cur.execute("CREATE TABLE IF NOT EXISTS holidays(year STRING, holiday_name STRING, styria BOOLEAN, carinthia BOOLEAN, salzburg BOOLEAN, tirol BOOLEAN, vienna BOOLEAN, upper_austria BOOLEAN, lower_austria BOOLEAN,  start DATE, end DATE)")
    cur.execute("CREATE TABLE IF NOT EXISTS start_end(year STRING UNIQUE, start DATE, end DATE)")
    logger.ok('Db initialized!')

def handle_res(start_year: int, end_year: int) -> object:
    res = get(BASE_URL.format(start_year=start_year, end_year=end_year))
    print(res.encoding)
    year = f'{start_year}/{end_year}'
    if not res.ok:
        logger.warn(f'Request failed for {start_year}/{end_year}. Got code: {res.status_code}')
        return
    logger.info(f'Got year {year}...')

    soup = BeautifulSoup(res.text, 'html.parser').main
    for tag in soup.find_all(['sup', 'a']):
        tag.extract()

    wanted = soup.find_all(['h3', 'p'])
    holidays_raw = {}
    current = ''
    valid_holidays = [
        'Herbstferien',
        'Sommerferien Hauptferien',
        'Semesterferien',
        'Osterferien',
        'Pfingstferien',
        'Weihnachtsferien'
    ]
    for tag in wanted:
        content = tag.get_text().strip().replace('\xa0', ' ')
        if content in valid_holidays:
            current = content.replace('Sommerferien Hauptferien', 'Sommerferien')
            holidays_raw.update({current: []})
        elif current != '' and content != '':
            holidays_raw.get(current).extend(content.split('\n'))

    pattern = compile(r'^(\d{1,2}\. \w+ \d{4}) bis (\d{1,2}\. \w+ \d{4}), ([A-Za-zöüä ]+(?:, [A-Za-zöüä ]+)*)$')
    date_fmt = '%d. %B %Y'
    holidays = {}
    for key, value in holidays_raw.items():
        holiday_dates = []
        
        for el in value: 
            match = pattern.match(el)
            if match != None:
                holiday_dates.append(
                    HolidayDate(
                        datetime.strptime(match[1], date_fmt) - timedelta(days=2),
                        datetime.strptime(match[2], date_fmt),
                        match[3].split(', ')
                    )
                )
        holidays.update({key: holiday_dates})
    return holidays

def request_gv(conf: Config):
    for year in range(conf.start_year, conf.end_year):
        yield tuple((f'{year}/{year + 1}', handle_res(year, year + 1)))

def main():
    locale.setlocale(locale.LC_ALL, 'de_AT.UTF-8')
    init_colorama()
    conf = Config()
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    init_db(cur)
    years = list(request_gv(conf))
    print(json.dumps(years, default=lambda o: o.toJSON()))
    # for i in range(1, len(years)):
    #     year_start = years[i - 1][1]['Sommerferien'].end_date
    #     year_end = years[i][1]['Sommerferien'].start_date
    #     cur.execute('REPLACE INTO start_end(year, start, end) VALUES (?, ?, ?)', years[i][0], year_start, year_end)
    #     logger.info(f'Added start/end for year {years[i][0]}!')


if __name__ == '__main__' :
    # try:
       main()
    # except Exception as e:
        # logger.fatal('Quit: %s' % e)