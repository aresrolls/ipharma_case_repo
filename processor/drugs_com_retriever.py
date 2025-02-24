from datetime import datetime as dt, timedelta
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import time
import csv
import random  # Added for random delay generation

HEADERS_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15'
]

def get_headers():
    return {
        'User-Agent': random.choice(HEADERS_LIST),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.drugs.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }


SCRAPER_API_KEY = 'c2546573dab2450029c6cb845bae833d'
BASE_URL = 'https://api.scraperapi.com/'


def scrape_reviews(drug_name, years_ago=1):
    reviews = []
    page_num = 1
    cutoff_date = dt.now() - timedelta(days=365 * years_ago)
    stop_processing = False

    while not stop_processing:
        # Configure ScraperAPI request with most recent sorting
        params = {
            'api_key': SCRAPER_API_KEY,
            'url': f'https://www.drugs.com/comments/{drug_name}/',
            'retry_404': 'true'
        }

        # Add pagination and sorting parameters
        params['url'] += f'?page={page_num}&sort_reviews=most_recent'

        try:
            response = requests.get(BASE_URL, params=params)
            if response.status_code != 200:
                print(f"Failed to retrieve page {page_num}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            review_containers = soup.find_all('div', class_='ddc-comment')

            if not review_containers:
                print("No more reviews found.")
                break

            for container in review_containers:
                # Extract date
                header = container.find('ul', class_='ddc-comment-header')
                if not header:
                    continue

                date_element = header.find_all('li')[-1]
                date_str = date_element.get_text(strip=True)

                try:
                    review_date = dt.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    # Handle different date format if necessary
                    continue

                # Stop if review is older than cutoff date
                if review_date < cutoff_date:
                    stop_processing = True
                    break

                # Extract review details
                author = container.find('abbr', class_='no-border').get_text(strip=True) if container.find(
                    'abbr') else 'Anonymous'

                rating_div = container.find('div', class_='ddc-rating-summary')
                rating = rating_div.find('div').get_text(strip=True).split('/')[0] if rating_div else 'N/A'

                helpful = container.find('a', {'data-like': '1'}).get_text(strip=True) if container.find('a', {
                    'data-like': '1'}) else '0'

                comment = container.find('p').get_text(strip=True) if container.find('p') else 'N/A'

                reviews.append({
                    'Author': author,
                    'Date': date_str,
                    'Rating': rating,
                    'Helpful Votes': helpful,
                    'Comment': comment
                })

            if stop_processing:
                break

            # Check for next page
            next_page = soup.find('a', class_='ddc-paging-item-next')
            if not next_page:
                break

            page_num += 1
            time.sleep(2)  # Respectful delay

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            break

    return reviews


def validate_page(soup, page_num):
    """Check if page contains expected elements"""
    title = soup.find('title')
    if not title or 'Rifaximin Reviews' not in title.text:
        return False
    if page_num == 1 and not soup.find('div', class_='ddc-comment-container'):
        return False
    return True


def save_to_csv(reviews, name):
    if not reviews:
        return

    keys = reviews[0].keys()
    filename = f'reviews_{name}_{dt.now().date()}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(reviews)
    return filename


def create_pdf(reviews, name):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for review in reviews:
        # Header
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Review by {review['Author']}", ln=1)
        pdf.set_font('Arial', '', 12)

        # Details
        pdf.cell(0, 6, f"Date: {review['Date']}", ln=1)
        pdf.cell(0, 6, f"Rating: {review['Rating']}/5 stars", ln=1)
        pdf.cell(0, 6, f"Helpful Votes: {review['Helpful Votes']}", ln=1)

        # Comment
        pdf.multi_cell(0, 6, f"Comment:\n{review['Comment']}", ln=1)
        pdf.ln(8)  # Add space between reviews

    pdf.output('reviews.pdf')


if __name__ == '__main__':
    print("Successfully scraped reviews and generated files:")

    for name in ['rifaximin','escitalopram','exenatide']:
        reviews_data = scrape_reviews(name)

        if reviews_data:
            filename = save_to_csv(reviews_data, name)
            # create_pdf(reviews_data)

            print(f"{filename}")
            # print("- reviews.pdf")
        else:
            print("No reviews were scraped")