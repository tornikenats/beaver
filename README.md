# Canadian Bank scraper

## Supported Banks
* TD Bank

## Example

Showing accounts
```
python bank.py accounts --card <card#> --password <pass> --security <security_answer>
```

Showing transactions for account
```
python bank.py transactions --card <card#> --password <pass> --security <security_answer> --account <account#> --days-ago <#>
```