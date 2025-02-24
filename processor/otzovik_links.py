import requests
from bs4 import BeautifulSoup


for name in ['афобазол','авиандр','эсциталопрам']:
    payload = {
        'api_key': 'c2546573dab2450029c6cb845bae833d',
        'url': f'https://otzovik.com/?search_text={name}&x=0&y=0'}

    r = requests.get('https://api.scraperapi.com/', params=payload)
    soup = BeautifulSoup(r.text, 'html.parser')

    base_url = 'https://otzovik.com'
    product_links = []

    # Find all product entries in the search results
    for product in soup.select('.product-list a.product-name'):
        relative_link = product['href']
        absolute_link = base_url + relative_link
        product_links.append(absolute_link)

    print("Found product links:")
    for link in product_links:
        print(link)