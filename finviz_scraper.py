import requests
from bs4 import BeautifulSoup
import time

def get_finviz_tickers(url, output_file='original_and_fetched.txt'):
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/134.0.0.0 Safari/537.36',
        'Referer': 'https://finviz.com/',
    }
    
    tickers = []
    page = 1
    delay = 0.1
    backoff = 10

    while True:
        paged_url = f"{url}&r={1 + (page - 1) * 20}"
        time.sleep(delay)

        try:
            res = session.get(paged_url, headers=headers, timeout=10)
        except requests.RequestException as e:
            print(f"Request error on page {page}: {e}")
            time.sleep(backoff)
            continue

        if res.status_code == 429:
            print(f"Rate-limited on page {page}, backing off {backoff}s...")
            time.sleep(backoff)
            continue

        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table.screener_table tr[valign="top"]')

        if not rows:
            break

        for row in rows:
            cols = row.select('td')
            if cols and len(cols) > 1:
                ticker = cols[1].text.strip()
                tickers.append(ticker)

        print(f"Fetched page {page}, got {len(rows)} tickers")
        page += 1

    with open(output_file, 'w') as f:
        for ticker in tickers:
            f.write(f"{ticker}\n")

    print(f"Exported {len(tickers)} tickers to {output_file}")
    return tickers

def main(stock_url: str, etf_url: str) -> list:
    stock_tickers = get_finviz_tickers(stock_url)
    etf_tickers   = get_finviz_tickers(etf_url)
    combined = sorted(set(stock_tickers + etf_tickers))
    return combined

if __name__ == "__main__":
    main()
