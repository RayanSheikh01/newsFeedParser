import json
from collections import defaultdict
import feedparser
from transformers import pipeline
import webbrowser
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import pytz

# Load a pre-trained text classification model from HuggingFace
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define categories for classification
CATEGORIES = ["Politics", "Technology", "Sports", "Health", "Crime", "Business", "World", "Culture", "Weather", "UK"]

class NewsCategorizer:
    def __init__(self, file_path="classified_articles.json"):
        self.file_path = file_path
        self.classified_articles = set()
        self.articles_with_categories = {}
        self.load_classified_articles()

    def isOlder(self, published_date):
        """
        Check if the article's published date is older than 7 days.
        """
        # Get the current datetime in UTC as an aware datetime object
        now = datetime.datetime.now(pytz.utc)

        # Calculate the difference between current time and published date
        time_difference = now - published_date
        
        # Check if the time difference is greater than 7 days
        return time_difference.days > 7

    def load_classified_articles(self):
        """Load previously classified articles from a JSON file and remove those older than 7 days."""
        try:
            with open(self.file_path, "r") as file:
                # Check if the file is empty
                content = file.read().strip()
                if content:  # If there's data in the file, load it
                    data = json.loads(content)
                    self.classified_articles = set(data.get("classified_articles", []))
                    self.articles_with_categories = data.get("articles", {})
                    
                    # Ensure all articles have a classification in the loaded JSON
                    for article in list(self.articles_with_categories.values()):
                        if 'category' not in article:
                            print(f"Warning: Article {article['title']} does not have a category.")
                        # Check if the article is older than 7 days and remove it if so
                        published_date = self.parse_date(article['published'])
                        if published_date and self.isOlder(published_date):
                            print(f"Removing article: {article['title']} (older than 7 days)")
                            del self.articles_with_categories[article['link']]  # Remove article from the dictionary
                            self.classified_articles.remove(article['link'])  # Remove from the classified set
                    
                    self.save_articles_to_json()
                    print(f"Loaded {len(self.articles_with_categories)} classified articles.")
                else:
                    print("JSON file is empty. Starting with empty data.")
                    self.classified_articles = set()
                    self.articles_with_categories = {}
        except FileNotFoundError:
            print("No classified articles file found. Starting fresh.")
            self.classified_articles = set()
            self.articles_with_categories = {}

    
    def save_articles_to_json(self):
        """
        Save the current articles with categories to the JSON file.
        """
        try:
            with open("articles.json", "w") as f:
                # Save the current in-memory data (articles with categories)
                json.dump(self.articles_with_categories, f, default=str, indent=4)
                print("Articles saved to JSON.")
        except Exception as e:
            print(f"Error saving articles to JSON: {e}")

    def save_classified_articles(self):
        """Save the classified articles to a JSON file."""
        with open(self.file_path, "w") as file:
            json.dump({
                "classified_articles": list(self.classified_articles),
                "articles": self.articles_with_categories
            }, file, indent=4)
        print(f"Saved {len(self.articles_with_categories)} classified articles.")

    def categorise_articles_with_ai(self, articles):
        """
        Categorises articles using AI-based text classification, skipping already-classified articles.

        Args:
            articles (list): List of news articles.

        Returns:
            dict: Categorised news articles.
        """
        categorised_articles = defaultdict(list)
        new_articles = []

        # Filter out already-classified articles
        for article in articles:
            identifier = article['link']  # Use a unique identifier like 'link'
            if identifier not in self.classified_articles:
                new_articles.append(article)
                self.classified_articles.add(identifier)  # Mark article as classified

        # Classify only new articles
        if new_articles:
            batch_titles = [article['title'] for article in new_articles]
            results = classifier(batch_titles, candidate_labels=CATEGORIES)

            for article, result in zip(new_articles, results):
                predicted_category = result['labels'][0]  # Get the category with the highest score
                categorised_articles[predicted_category].append(article)
                self.articles_with_categories[article['link']] = {
                    'title': article['title'],
                    'category': predicted_category,
                    'published': article['published'],
                    'source': article['source'],
                    'link': article['link']
                }

            # Save the classified articles to the JSON file after classification
            self.save_classified_articles()

        return categorised_articles

    def fetch_feed(self, url):
        """
        Fetches a single RSS feed and returns a list of articles.

        Args:
            url (str): The RSS feed URL.

        Returns:
            list: List of news articles with title, link, and publication date.
        """
        articles = []
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published_date = entry.published if 'published' in entry else datetime.datetime.now(datetime.timezone.utc).isoformat()
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'source': feed.feed.title,
                'published': published_date,
            })
        return articles

    def fetch_news(self, rss_urls):
        """
        Fetches news from a list of RSS feeds concurrently.

        Args:
            rss_urls (list): List of RSS feed URLs.

        Returns:
            list: List of news articles with title, link, and publication date.
        """
        articles = []
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.fetch_feed, url) for url in rss_urls]
            for future in as_completed(futures):
                articles.extend(future.result())
        return articles

    def _insert_article_into_category(self, tree, category_node, article):
        """
        Inserts an article into the specified category node in the Treeview,
        with the most recent articles appearing at the top.

        Args:
            tree (ttk.Treeview): The Treeview widget.
            category_node (str): The ID of the category node in the Treeview.
            article (dict): The article data containing 'title', 'published', and 'link'.
        """
        # Parse the published date and convert it to a datetime object
        published_date = self.parse_date(article['published'])

        # Format the published date to a more readable format (e.g., YYYY-MM-DD HH:MM:SS)
        formatted_published_date = published_date.strftime(' %A %d %B %Y %H:%M:%S')

        # Insert the article into the category node
        tree.insert(category_node, 'end', text=article['title'], 
                    values=(article['source'], formatted_published_date, article['link']),
                    tags=(published_date,))  # Use date as a tag for sorting later


    def display_news_gui(self, categorised_news):
        """
        Displays the categorised news articles in a GUI, ensuring newest articles appear at the top.

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

        # Iterate over categories and add articles to the Treeview
        for category, articles in categorised_news.items():
            # Check if the category already exists in the Treeview
            category_node = self._find_category_node(tree, category)
            
            if not category_node:
                # If the category doesn't exist, create it
                category_node = tree.insert('', 'end', text=category)

            # Sort articles by published date before inserting into category node
            sorted_articles = sorted(articles, key=lambda x: self.parse_date(x['published']), reverse=True)
            
            for article in sorted_articles:
                self._insert_article_into_category(tree, category_node, article)

        # Also show articles that are already classified and stored in the JSON
        for article in self.articles_with_categories.values():
            category = article.get('category', 'Uncategorized')
            category_node = self._find_category_node(tree, category)

            if not category_node:
                category_node = tree.insert('', 'end', text=category)

            self._insert_article_into_category(tree, category_node, article)

        tree.pack(expand=True, fill='both')

        # Open links in a web browser
        def open_link(event):
            selected_item = tree.selection()
            if selected_item:
                values = tree.item(selected_item[0], 'values')
                if values and len(values) > 2:
                    webbrowser.open(values[2])  # Open the link in the default browser

        def sort_treeview_by_datetime():
            for item in tree.get_children():
                tree.move(item, '', 0)  # Unset the item's current position
            for category_node in tree.get_children():
                sorted_items = sorted(tree.get_children(category_node), key=lambda x: tree.item(x)['tags'][0], reverse=True)
                for index, item in enumerate(sorted_items):
                    tree.move(item, category_node, index)
        
        # Sort after insertion
        sort_treeview_by_datetime()

        tree.bind('<Double-1>', open_link)

        root.mainloop()

    def _find_category_node(self, tree, category_name):
        """
        Finds the category node in the Treeview.

        Args:
            tree (ttk.Treeview): The Treeview widget.
            category_name (str): The name of the category to find.

        Returns:
            str: The ID of the category node, or None if the category doesn't exist.
        """
        # Iterate over all items in the Treeview
        for child in tree.get_children():
            # Check if the text of the current node matches the category name
            if tree.item(child, 'text') == category_name:
                return child
        return None  # Return None if the category doesn't exist

    
    def parse_date(self, published_str):
        """
        Convert a date string in the format 'Sat, 11 Jan 2025 11:13:50 GMT' to a datetime object (aware).
        If parsing fails, return the current datetime as an aware datetime.
        """
        try:
            # Define the format to match the string 'Sat, 11 Jan 2025 11:13:50 GMT'
            date_format = "%a, %d %b %Y %H:%M:%S GMT"
            
            # Parse the date string into a naive datetime object
            naive_datetime = datetime.datetime.strptime(published_str, date_format)
            
            # Convert it to an aware datetime by setting the timezone to UTC
            aware_datetime = pytz.utc.localize(naive_datetime)
            
            return aware_datetime
        except ValueError:
            # If parsing fails, return the current aware datetime in UTC
            return datetime.datetime.now(pytz.utc)



def main():
    categorizer = NewsCategorizer()  # Create an instance of the categorizer
    rss_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition_world.rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US%3Aen",
    ]

    print("Fetching news...")
    articles = categorizer.fetch_news(rss_feeds)
    print("Classifying articles...")
    categorised_news = categorizer.categorise_articles_with_ai(articles)
    print("Displaying news...")
    categorizer.display_news_gui(categorised_news)

    # Save classified articles
    categorizer.save_classified_articles()


if __name__ == "__main__":
    main()
