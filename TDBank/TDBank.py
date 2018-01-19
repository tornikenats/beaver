import requests
from selenium import webdriver
import time
import re
import calendar
import datetime
import csv
import copy


class TDBank:
    def __init__(self, driver="firefox"):
        if driver == 'firefox':
            self.init_firefox_driver()
        elif driver == 'chrome':
            self.init_chrome_driver()

    def init_chrome_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Firefox(chrome_options=options)

    def init_firefox_driver(self):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Firefox(firefox_options=options)

    def get_session_cookies(self, username, password, security_answer):
        self.driver.get("https://easyweb.td.com/waw/idp/login.htm")
        self.driver.implicitly_wait(20)  # seconds

        self.driver.find_element_by_id("login:AccessCard").send_keys(username)
        self.driver.find_element_by_id("login:Webpassword").send_keys(password)
        self.driver.find_element_by_id("login").submit()

        # Wait until logged in, just in case we need to deal with MFA.
        while not self.driver.current_url.startswith('https://easyweb.td.com/waw/idp/authenticate.htm') and not self.driver.current_url.startswith('https://easyweb.td.com'):
            time.sleep(1)

        # check if we hit security question
        if self.driver.current_url.startswith('https://easyweb.td.com/waw/idp/authenticate.htm'):
            self.driver.find_element_by_id(
                "MFAChallengeForm:answer").send_keys(security_answer)
            self.driver.find_element_by_id("MFAChallengeForm:next").submit()

        while not self.driver.current_url.startswith('https://easyweb.td.com'):
            time.sleep(1)

        time.sleep(10)
        ##allow time for cookies to initialize
        cookies = ['{}={}'.format(cookie['name'], cookie['value']) for cookie in self.driver.get_cookies()]
        self.cookies = '; '.join(cookies)
        self.driver.close()

    def find_accounts(self):
        url = 'https://easyweb.td.com/waw/ezw/servlet/ca.tdbank.banking.servlet.FinancialSummaryServlet'
        resp = requests.get(url, headers=TDBank.headers)
        accounts_str_list = re.findall(
            r"JavaScript:fnActivity\('-*[0-9]+',", resp.text)
        self.accounts = list(map(lambda x: re.search(
            r"[\-0-9]+", x).group(), accounts_str_list))

    def get_transaction_csv(self, account, start_date, end_date):
        url = 'https://easyweb.td.com/waw/ezw/servlet/ca.tdbank.banking.servlet.DownloadAccountActivityServlet'
        payload = {
            'selaccounts': account,
            'DateRange': 'CTM',
            'PFM': 'csv',
            'xptype': 'PRXP',
            'actiontaken': 'D',
            'referer': 'AA',
            'commingfrom': 'AA',
            'ExprtInfo': '',
            'fromDate': f'{start_date.year}-{start_date.month}-{start_date.day}',
            'toDate': f'{end_date.year}-{end_date.month}-{end_date.day}',
            'filter': 'f1'
        }
     
        headers = {
            'Host': "easyweb.td.com",
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'Accept-Language': "en-US,en;q=0.5",
            'Referer': "https://easyweb.td.com/waw/ezw/servlet/ca.tdbank.banking.servlet.AccountDetailsServlet",
            'Content-Type': "application/x-www-form-urlencoded",
            'Connection': "keep-alive",
            'Upgrade-Insecure-Requests': "1",
            'Cache-Control': "no-cache",
            'Cookie': self.cookies
        }

        with requests.Session() as s:
            download = s.post(url, data=payload, headers=TDBank.headers)

            decoded_content = download.content.decode('utf-8')

            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            out_csv = list(cr)
            if len(out_csv[0]) != 5:
                raise Exception(f'Could not load transactions for {year}, {month}')
            return out_csv

    def get_credit_transactions(self, account, cycleId):
        url = "https://easyweb.td.com/waw/api/account/creditcard/download"

        querystring = {"accountKey": account,"cycleId": str(cycleId), "downloadAccountFormat":"CSV"}

        headers = {
            'Host': "easyweb.td.com",
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0",
            'Accept': "application/json, text/plain, */*",
            'Accept-Language': "en-US,en;q=0.5",
            'Referer': "https://easyweb.td.com/waw/exp/",
            'Connection': "keep-alive",
            'Cache-Control': "no-cache",
            # 'Cookie': self.cookies,
            'Cookie': "",
        }

        with requests.Session() as s:
            resp = s.get(url, headers=headers, params=querystring)

            decoded_content = resp.content.decode('utf-8')

            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            out_csv = list(cr)
            if len(out_csv[0]) != 5:
                raise Exception(f'Could not load transactions for {cycleId}')
            return out_csv

    # NOT TESTED
    def get_account(self, account):
        url = 'https://easyweb.td.com/waw/ezw/servlet/ca.tdbank.banking.servlet.AccountDetailsServlet?selectedAccount=C-853230284&period=CTM&filter=f1&reverse=&xptype=PRXP&fromYear=&fromMonth=&fromDate=&toYear=&toMonth=&toDate=&NumberOfDays=&StartOrEnd=&DateRangeMonth=4&DateRangeDay=&DateRangeYear=2017&requestedPage=0&sortBy=date&sortByOrder=&fromjsp=activity&DateRangeMonth1=&DateRangeDay1=&DateRangeYear1=&DateRangeMonth2=&DateRangeDay2=&DateRangeYear2=&DateRangeMonth3=&DateRangeDay3=&DateRangeYear3='

        cookie_whitelist = ['com.td.ew.SSO_GUID']
        cookie_subset = {key: value for key,
                         value in cookies.items() if key in cookie_whitelist}
        resp = requests.post(url, headers=headers, cookies=cookie_subset)
        with open('test.html', 'w') as f:
            f.write(resp.text)
