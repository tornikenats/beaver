import requests
import time
import re
import calendar
import datetime
import csv
import copy
import logging
import logging
import sys
import re
import json
import dateutil
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import lxml.html
from beaver.scrapers import Scraper


class RBCBank(Scraper):
    def __init__(self, driver="firefox", silent=True, headless=True):
        super().__init__(driver, headless=headless, silent=silent)

    def get_session_cookies(self, username, password, security_answer):
        logger = logging.getLogger('beaver.main')
        logger.info('Getting session cookies')

        self.driver.get("https://www1.royalbank.com/cgi-bin/rbaccess/rbunxcgi?F6=1&F7=IB&F21=IB&F22=IB&REQUEST=ClientSignin&LANGUAGE=ENGLISH")
        self.driver.implicitly_wait(20)  # seconds

        self.driver.find_element_by_id("K1").send_keys(username)
        self.driver.find_element_by_id("Q1").send_keys(password)
        self.driver.find_element_by_id("rbunxcgi").submit()

        # Wait until logged in, just in case we need to deal with MFA.
        while not self.driver.current_url.startswith('https://www1.royalbank.com/cgi-bin/rbaccess/'):
            time.sleep(1)

        time.sleep(10)
        ##allow time for cookies to initialize
        cookies = ['{}={}'.format(cookie['name'], cookie['value']) for cookie in self.driver.get_cookies()]
        self.cookies = '; '.join(cookies)
        self.driver.close()

    def screen_scrape_transactions(self, username, password, security_answer, account_name):
        '''
            Will scrape the account name you pass in for transaction for the last 7 years
        '''
        logger = logging.getLogger('beaver.main')
        logger.info('Started scraping {}'.format(account_name))

        def select_in_select(id, option_text):
            el = self.driver.find_element_by_id(id)
            for option in el.find_elements_by_tag_name('option'):
                if option.text == option_text:
                    option.click() # select() in earlier versions of webdriver
                    break
        
        def month_year_iter( start_month, start_year, end_month, end_year ):
            ym_start= 12*start_year + start_month - 1
            ym_end= 12*end_year + end_month - 1
            for ym in range( ym_start, ym_end ):
                y, m = divmod( ym, 12 )
                yield y, m+1

        # navigate to login page
        self.driver.get("https://www1.royalbank.com/cgi-bin/rbaccess/rbunxcgi?F6=1&F7=IB&F21=IB&F22=IB&REQUEST=ClientSignin&LANGUAGE=ENGLISH")
        self.driver.implicitly_wait(20)  # seconds

        # log in
        self.driver.find_element_by_id("K1").send_keys(username)
        self.driver.find_element_by_id("Q1").send_keys(password)
        self.driver.find_element_by_id("rbunxcgi").submit()

        # navigate to transaction search
        timeout = 5
        try:
            element_present = EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '{}')]".format(account_name)))
            WebDriverWait(self.driver, timeout).until(element_present)
        except Exception:
            logger.error("Couldn't find account named {}".format(account_name))
        self.driver.find_elements_by_xpath("//a[contains(text(), '{}')]".format(account_name))[0].click()
        
        element_present = EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Search')]"))
        WebDriverWait(self.driver, timeout).until(element_present)
        self.driver.find_elements_by_xpath("//a[contains(text(), 'Search')]")[0].click()
        
        element_present = EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Transaction Type:')]"))
        WebDriverWait(self.driver, timeout).until(element_present)

        transactions = []
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        # iterate every month from 7 years ago
        start_date = datetime.datetime.now().date().replace(day=1) + dateutil.relativedelta.relativedelta(years=-7, months=+1)
        end_date = start_date + dateutil.relativedelta.relativedelta(years=+7)
        for year, start_month_i in month_year_iter(start_date.month, start_date.year, end_date.month, end_date.year):
            start_month = months[start_month_i-1]
            end_month = months[(start_month_i)%12]
            next_year = year if start_month_i < 12 else year+1
            logger.info('Searching for {}, {} - {}, {}'.format(start_month, year, end_month, next_year))
            
            # fill in search fields
            select_in_select('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_RetrieveTransactionPortletFormSearchMonth1', start_month)
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-DD1').clear()
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-DD1').send_keys('1')
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-YYYY1').clear()
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-YYYY1').send_keys(str(year))

            select_in_select('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_RetrieveTransactionPortletFormSearchMonth2', end_month)
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-DD2').clear()
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-DD2').send_keys('1')
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-YYYY2').clear()
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_date2-YYYY2').send_keys(str(next_year))
            
            self.driver.find_element_by_id('ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_SearchTransactions').submit()

            # wait for search results
            element_present = EC.presence_of_element_located((By.XPATH, '//table[@id="ns_Z7_H1541AS0G0VN00AHHMF4HF2C26_table1"]|//*[contains(text(), "There are no items to be displayed.")]'))
            WebDriverWait(self.driver, timeout).until(element_present)
            
            # read search results
            root = lxml.html.fromstring(self.driver.page_source)
            for row in root.xpath('.//table[contains(@id,"ns_Z7_H1541AS0G0VN00AHHMF4HF2C26")]//tr'):
                cells = row.xpath('.//td/text()')
                if cells and cells[1].strip() != '':
                    if len(cells) == 7:
                        transaction = {
                            'date': cells[1].strip(),
                            'desc2': cells[2].strip(),
                            'desc': cells[3].strip(),
                            'credit': re.sub('[-$,]', '', cells[4].strip()),
                            'debit': re.sub('[-$,]', '', cells[5].strip()),
                            'balance': re.sub('[-$,]', '', cells[6].strip()),
                        }
                    elif len(cells) == 6:
                        transaction = {
                            'date': cells[1].strip(),
                            'desc': cells[2].strip(),
                            'credit': re.sub('[-$,]', '', cells[3].strip()),
                            'debit': re.sub('[-$,]', '', cells[4].strip()),
                            'balance': re.sub('[-$,]', '', cells[5].strip()),
                        }
                    transactions.append(transaction)
            logger.info('Downloaded {} transactions so far'.format(len(transactions)))
            time.sleep(2)
        
        self.driver.close()
        return transactions

    def download_transactions_csv(self):
        logger = logging.getLogger('beaver.main')
        logger.info('Downloading transactions')
        url = "https://www1.royalbank.com/wps/myportal/OLB/%21ut/p/a1/jZLJboMwEEC_hmPwsEXQm4USTKQkrVBb4ktkI5dYARMZWpq_r0HqqY2TOdmj92bGC6KoRFSxL1mzQXaKNdOeLo_Ei0IPF5DB2w4AE7Jdh2Tth0VkgIMB4EZgsPkZ_PrhcxyTJIMEVhBAvtu-JOkSA6yCx_rf8v0HfcuAFj8NA7s_AXf6F0IdU4zeEZ1J20FmwHbTtl57P7ID2ca7M4N5jA2iddPx-WMcsOJBXCOqxYfQQruf2qRPw3DpnxxwYBxHz9XdlTWcqbNbda0DVS0XXCoHNGdVJfp-Wplk0IL3X8lT1w-o_FsJXdpXE-V3LvMF5dfxBy_PaWA%21/dl5/d5/L2dBISEvZ0FBIS9nQSEh/pw/Z7_H1541AS0G0VN00AHHMF4HF2422/res/c=cacheLevelPage/=/"

        querystring = {"initialPage":"N"}

        payload = "RESUBMIT_ACTION=%252Fwps%252Fmyportal%252FOLB%252F%2521ut%252Fp%252Fa1%252F04_Sj9CPykssy0xPLMnMz0vMAfGjzOI9DE1NDB2DDdwNwvwMDBw9PHzdTDzcjEyCTfUj9SOjzHEqMDLSDyekIMo5w7_SssDY3D--XD88MRlks35BdpqPo6OiIgDahoXI%252F&RESUBMIT_PARAMS=REQUEST%252CFROM%252CDLTYPE%252CSOFTWARE%252CACCOUNT_INFO%252CINCLUDE%252CSTATEMENT%252CFROMDAY%252CFROMMONTH%252CFROMYEAR%252CTODAY%252CTOMONTH%252CTOYEAR&F22=HTPCBINET&REQUEST=OFXTransactionInquiry&FROM=Download&DLTYPE=%252B&STATEMENT=P&SOFTWARE=EXCEL&ACCOUNT_INFO=P&INCLUDE=A&FROMDAY=1&FROMMONTH=1&TODAY=1&TOMONTH=1"
        headers = {
            'Host': "www1.royalbank.com",
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            'Accept-Language': "en-US,en;q=0.5",
            'Referer': "https://www1.royalbank.com/wps/myportal/OLB/!ut/p/a1/jZFBb4IwFMc_yw4cpa8UDOzWEKWYqFsMG_ZiWtIhEYopbMxvPyS7bVZ7al9-v_f-eUUc5Yhr8VWVoq9aLerrm88PDAc-pjtI4G0DQBlbL3229GKfjMB-BODGoWDzEwh-ff8lDFmUQAQLIJBu1q9RPKcAC_LY_Fu-96BvCXjH3yl9iCl6R3wibUEmwLYp26ytF9iBZIXvZBiXuUK8rFs5feyeaknCEnGjPpRRxv00Y_nY9-fu2QEHhmHArmkvopZCn9yibRwoymomK-2AkaIoVNddb2ORNID_a3lsux7lfzuhc5NlWf6dVumMy8vw9AO2-h75/dl5/d5/L2dJQSEvUUt3QS80SmlFL1o2X0gxNTQxQVMwRzBWTjAwQUhITUY0SEYyNFM1/",
            'Content-Type': "application/x-www-form-urlencoded",
            'Cookie': self.cookies,
            'Connection': "keep-alive",
            'Upgrade-Insecure-Requests': "1",
            'Cache-Control': "no-cache",
        }

        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        decoded_content = response.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        out_csv = list(cr)
        if len(out_csv[0]) != 8:
            raise Exception(f'Could not parse response: {deco}')
        return out_csv