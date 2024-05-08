import requests
from bs4 import BeautifulSoup

news_api_key = 'a0ff4132-cf60-48d7-b23f-d0523e7c67aa' 
news_endpoint = 'https://content.guardianapis.com/search'

def get_news(topic):
    #get news url
    params = {
        'api-key': news_api_key,
        'q': topic,  # Search term, can be customized
        'page-size': 1,  # Number of results per page
        'order-by': 'relevance',  # or relevance
    }

    response = requests.get(news_endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        articles = data.get('response', {}).get('results', [])

        for article in articles:
            news_title = article.get('webTitle', 'No title')
            news_url = article.get('webUrl', '#')
            print(f"Title: {news_title}")
            print(f"URL: {news_url}")
            print()
    else:
        print("Failed to fetch content. HTTP status code:", response.status_code)
    
    #get news content
    response = requests.get(news_url)

    if response.status_code == 200:
        #clear the original txt file
        with open("../data/news_content.txt", 'w') as file:
            pass

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract relevant parts of the article (e.g., the headline and content)
        headline = soup.find('h1')  # Assuming the headline is in an <h1> tag
        paragraphs = soup.find_all('p')  # Extract all paragraph content

        # Display the headline
        if headline:
            print(f"Headline: {headline.get_text()}")

        # Display the content of the article
        for p in paragraphs:
            with open("../data/news_content.txt", 'a') as file:
                file.write('\n' + p.get_text())
            print(p.get_text())
    else:
        print('Failed to fetch the article content. Status Code:', response.status_code)

def main():
    topic = input()
    get_news(topic)

if __name__ == "__main__":
    main()    