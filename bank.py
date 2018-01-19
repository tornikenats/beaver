from TDBank.TDBank import TDBank
from dateutil import parser
from dateutil.rrule import rrule, MONTHLY
from pymongo import MongoClient, ASCENDING
import time
import click
import datetime

client = MongoClient()
db = client.tdbank


@click.group()
def cli():
    pass


def save_transactions(account, csv):
    if 'transactions' not in db.collection_names():
        transactions = db.transactions
        transactions.create_index(
            [
                ('account', ASCENDING), ('date', ASCENDING), 
                ('description', ASCENDING), ('balance', ASCENDING)
            ],
            unique=True
        )
    else:
        transactions = db.transactions

    for date, desc, debit, credit, balance in csv:
        doc = {
            'account': account,
            'date': parser.parse(date),
            'description': desc,
            'debit': float(debit or '0'),
            'credit': float(credit or '0'),
            'balance': float(balance or '0')
        }
        
        try:
            transactions.insert_one(doc)
        except Exception as e:
            print(e)


def save_accounts(card, account_list):
    if 'accounts' not in db.collection_names():
        accounts = db.accounts
        accounts.create_index(
            [('card', ASCENDING), ('account', ASCENDING)],
            unique=True
        )
    else:
        accounts = db.accounts

    
    for account in account_list:
        doc = {
            'card': card,
            'account': account,
        }
        
        try:
            accounts.insert_one(doc)
        except Exception as e:
            print(e)


@cli.command()
@click.option('--card', help="Card number")
@click.option('--password', help="Account password")
@click.option('--security', help="Security question answer")
def accounts(card, password, security):
    tdbank = TDBank()
    creds = {
        'username': card,
        'password': password,
        'security_answer': security
    }
    print('Getting cookies..')
    tdbank.get_session_cookies(**creds)
    print('Finding accounts..')
    tdbank.find_accounts()
    print('Saving accounts..')
    save_accounts(card, tdbank.accounts)


@cli.command()
@click.option('--card', help="Card number")
@click.option('--password', help="Account password")
@click.option('--security', help="Security question answer")
@click.option('--account', help="Account number", required=True)
@click.option('--days-ago', default=0, help="Number of days back to get transactions")
def transactions(card, password, security, account, days_ago):
    tdbank = TDBank()
    options = {
        'username': card,
        'password': password,
        'security_answer': security,
    }
    print('Getting cookies..')
    tdbank.get_session_cookies(**options)

    end_date = datetime.datetime.today().date()
    start_date = end_date - datetime.timedelta(days=days_ago)
    print(f'Downloading transactions from {start_date}')
    try:
        transaction_csv = tdbank.get_transaction_csv(account, start_date, end_date)
    except Exception as e:
        print(str(e))
    print('\tsaving..')
    save_transactions(account, transaction_csv)


@cli.command()
@click.option('--card', help="Card number")
@click.option('--password', help="Account password")
@click.option('--security', help="Security question answer")
@click.option('--account', help="Account number", required=True)
@click.option('--days-ago', default=0, help="Number of days back to get transactions")
def credit_transactions(card, password, security, account, days_ago):
    tdbank = TDBank()
    options = {
        'username': card,
        'password': password,
        'security_answer': security
    }
    print('Getting cookies..')
    tdbank.get_session_cookies(**options)

    print('Getting credit transactions')
    for cycleId in range(1, 7):
        print('Downloading cycle {}'.format(cycleId))
        
        try:
            transaction_csv = tdbank.get_credit_transactions(account, cycleId)
        except Exception as e:
            print(str(e))
        print('\tsaving..')
        save_transactions(account, transaction_csv)



if __name__ == "__main__":
    cli()