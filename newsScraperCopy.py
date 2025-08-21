import feedparser
import tkinter as tk
from tkinter import ttk
import webbrowser
from collections import defaultdict
from transformers import pipeline

# Load a pre-trained text classification model from HuggingFace
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define categories for classification
CATEGORIES = ["Politics", "Technology", "Sports", "Health", "Business", "World", "Culture", "Weather", "UK", "Entertainment", "Science", "Other"]

def fetch_news(rss_urls):
    """
    Fetches news from a list of RSS feeds.

    Args:
        rss_urls (list): List of RSS feed URLs.

    Returns:
        list: List of news articles with title, link, and publication date.
    """
    articles = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'source': feed.feed.title,
                'published': entry.published if 'published' in entry else 'Unknown date',
            })
    return articles


def categorise_articles_with_ai(articles):
    """
    Categorises articles using AI-based text classification.

    Args:
        articles (list): List of news articles.

    Returns:
        dict: Categorised news articles.
    """
    categorised_articles = defaultdict(list)

    for article in articles:
        title = article['title']
        
        # Use the classifier to predict the category
        result = classifier(title, candidate_labels=CATEGORIES)
        predicted_category = result['labels'][0]  # Get the category with the highest score
        
        categorised_articles[predicted_category].append(article)

    return categorised_articles


def display_news_gui(categorised_news):
    """
    Displays the categorised news articles in a GUI.

    Args:
        categorised_news (dict): Categorised news articles.
    """
    root = tk.Tk()
    root.title("Categorised News Aggregator")

    # Create a Treeview widget
    tree = ttk.Treeview(root, columns=('Source', 'Published', 'Link'), show='tree headings')
    tree.heading('#0', text='Category')
    tree.heading('Source', text='Source')
    tree.heading('Published', text='Published')
    tree.heading('Link', text='Link')

    # Populate Treeview with categorised news
    for category, articles in categorised_news.items():
        category_id = tree.insert('', 'end', text=category)
        for article in articles:
            tree.insert(category_id, 'end', text=article['title'], values=(article['source'], article['published'], article['link']))

    tree.pack(expand=True, fill='both')

    # Open links in a web browser
    def open_link(event):
        selected_item = tree.selection()
        if selected_item:
            values = tree.item(selected_item[0], 'values')
            if values and len(values) > 2:
                webbrowser.open(values[2])  # Open the link in the default browser

    tree.bind('<Double-1>', open_link)

    root.mainloop()


def main():
    rss_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.reuters.com/reuters/topNews",
    ]

    print("Fetching news...")
    articles = fetch_news(rss_feeds)
    categorised_news = categorise_articles_with_ai(articles)
    display_news_gui(categorised_news)


if __name__ == "__main__":
    main()
