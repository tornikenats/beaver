# Beaver - transaction history scraper for Canadian Banks
*Disclaimer: This project is purely for educational purposes. By using any code in this repositry you assume responsibility for your own actions.*

## Supported Banks
* TD Bank
* RBC Bank

## Limitation
* TD Bank: no limits on CSV API
* RBC Bank: 1 year limit on CSV API; 7 year limit for screen scraper

## Usage
1. Install:
`pip install git+https://github.com/TornikeNatsvlishvili/beaver.git`
2. Use:

```python
from beaver import RBCBank

bank = beaver.RBCBank()

transactions = bank.screen_scrape_transactions(
    'Banking number', 'Banking password', '', 'Account name'
)
```