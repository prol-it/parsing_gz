import requests
from bs4 import BeautifulSoup
import csv
import time
import os


def convert_namePos(x):
    # Удаляем впередистоящие знаки, отличные от символьных и кавычки
    while x[0].isdecimal():
        x = x[1:]
    x = x.replace('"', '')
    x = x.replace("'", '')

    return x.strip()


def convert_num(x):
    # Удаляем внутренние непереносимые пробелы и меняем запятую на точку (PNI 4)
    x = x.replace(',', '.')
    x = x.replace('\xa0', '')
    return x


def parsing(contract, org):
    URL_HEADER = 'https://zakupki.gov.ru/epz/contract/contractCard/payment-info-and-target-of-order.html?reestrNumber=' + contract + '&#contractSubjects'
    URL_POSITIONS = 'https://zakupki.gov.ru/epz/contract/contractCard/payment-info-and-target-of-order-list.html?reestrNumber=' + contract + '&page=1&pageSize=200'
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
    }

    r_head = requests.get(URL_HEADER, headers=HEADERS)
    soup_head = BeautifulSoup(r_head.text, 'html.parser')
    r_pos = requests.get(URL_POSITIONS, headers=HEADERS)
    soup_pos = BeautifulSoup(r_pos.text, 'html.parser')

    line = soup_pos.find_all('tr', class_='tableBlock__row')

    data = []
    pos = 0
    total = 0
    total_site = 0

    for item in line:
        name = item.find('div', class_='padBtm5 inline js-expand-all-list--not-count')
        qtyIzm = item.find('div', class_='align-items-center w-space-nowrap')
        priceInPage = item.find_all('td', class_='tableBlock__col tableBlock__col_right')
        if (name is not None) and (qtyIzm is not None) and (priceInPage is not None):
            name = convert_namePos(name.text.strip())
            # Преобразование столбцов количества и единиц измерений
            qtyIzm = qtyIzm.text.strip()
            razd = qtyIzm.find('\n')
            qty = convert_num(qtyIzm[:razd])
            izm = qtyIzm[razd + 1:].strip().replace(';', '').replace('"', '')
            # Преобразование столбцов цены и суммы
            price = convert_num(priceInPage[0].text.strip())
            sum = priceInPage[1].text.strip()
            sum = convert_num(sum[:sum.find('\n')])

            pos += 1
            total += float(sum)

            data.append({'name': name, 'qtyIzm': qtyIzm, 'qty': qty, 'izm': izm, 'price': price, 'sum': sum})

    # org_full_name = soup_head.find('div', class_='sectionMainInfo__body').find_all('span', class_='cardMainInfo__content')[0].text.strip()
    year_finish = soup_head.find('div', class_='date mt-auto').find_all('div', class_='cardMainInfo__section')[
                      1].text.strip()[-4:]

    line_footer = soup_pos.find('tfoot', class_='tableBlock__foot').find_all('tr', class_='tableBlock__row')
    for items in line_footer:
        total_site = items.find('td', class_='tableBlock__col tableBlock__col_right cost').text.strip()

    total_site = ''.join(total_site.split())
    total_site = float(total_site.replace(',', '.'))
    total = round(total, 2)

    if total == total_site:
        with open(contract + '--' + year_finish + '--' + str(pos) + '.csv', 'w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            for i in data:
                writer.writerow(
                    (
                        i['name'],
                        i['qty'],
                        i['izm'],
                        i['price'],
                        i['sum'],
                        contract,
                        year_finish,
                        org
                        # org_full_name
                    )
                )
        print('Контракт: ' + contract + ' Позиций - ', pos)
        print('Сумма импортированных позиций - ', total)
        print('Сумма позиций на сайте - ', total_site, end="\n" * 2)
    else:
        print('!!!!! СУММА ИМПОРТИРОВАННЫХ ПОЗИЦИЙ РАСХОДИТСЯ С ОБЩЕЙ СУММОЙ КОНТРАКТОВ НА САЙТЕ!!!!!')
        print('Позиций - ', pos)
        print('Сумма импортированных позиций - ', total)
        print('Сумма позиций на сайте - ', total_site)


# Идентификатор организации
org = 'SPB_PNI-6'
# Список контрактов
list_contract = [
    2780604280221000020
]

for i in list_contract:
    print(list_contract.index(i) + 1)
    parsing(str(i), org)
    time.sleep(5)

ls = [i for i in os.listdir() if i.endswith('.csv')]
ls.sort()
with open(org + '.csv', 'w') as f:
    for j in ls:
        s = open(j).read()
        f.write(s)