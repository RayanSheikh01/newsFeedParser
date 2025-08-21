import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext
from xml.etree import ElementTree as ET
import re

# Function to fetch the RSS feed and parse articles
rss_feed_url = 'http://feeds.bbci.co.uk/news/rss.xml'
response = requests.get(rss_feed_url)

tree = ET.ElementTree(ET.fromstring(response.text))
root = tree.getroot()

# BBC RSS items are under 'channel' > 'item'
items = root.find('channel').findall('item')

def extract_article_details(article_url):
    article_response = requests.get(article_url)
    article_soup = BeautifulSoup(article_response.text, 'html.parser')

    article_details = {}

    article_details['headline'] = article_soup.find('h1').text.strip() if article_soup.find('h1') else 'No headline found'
    source = article_soup.find('meta', attrs={'name': 'author'})
    article_details['author'] = source['content'] if source else 'Unknown author'
    article_details['source'] = 'BBC News'

    date_time = article_soup.find('meta', attrs={'name': 'date'})
    article_details['date'] = date_time['content'] if date_time else 'Unknown date'

    article_details['main_event'] = article_soup.find('p').text.strip() if article_soup.find('p') else 'No main event found'

    # Extracting and splitting the key facts into separate sentences
    facts_paragraphs = article_soup.find_all('p')
    key_facts = []
    for fact in facts_paragraphs:
        sentences = re.split(r'(?<=\.)\s', fact.text.strip())  # Split by period followed by space
        key_facts.extend([sentence.strip() for sentence in sentences if sentence.strip()])  # Clean and add non-empty sentences

    article_details['key_facts'] = key_facts

    article_details['background_context'] = article_soup.find('section', class_='story-body__inner') or 'No background context available'

    if any(word in article_details['headline'].lower() for word in ['shocking', 'dramatic', 'unprecedented']):
        article_details['emotional_tone'] = 'Sensational'
    else:
        article_details['emotional_tone'] = 'Neutral'

    article_details['implications'] = 'Analyze based on content'
    article_details['perspectives_and_bias'] = 'Analyze multiple viewpoints'

    return article_details

# GUI Setup
class NewsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BBC News Article Details")
        self.root.geometry("800x600")

        self.label = tk.Label(root, text="Enter the article URL:", font=("Arial", 14))
        self.label.pack(pady=10)

        self.url_entry = tk.Entry(root, width=50, font=("Arial", 14))
        self.url_entry.pack(pady=10)

        self.fetch_button = tk.Button(root, text="Fetch Article Details", command=self.display_article_details, font=("Arial", 14))
        self.fetch_button.pack(pady=10)

        self.text_area = scrolledtext.ScrolledText(root, width=80, height=20, font=("Arial", 12))
        self.text_area.pack(pady=20)

    def display_article_details(self):
        article_url = self.url_entry.get()
        if article_url:
            article_data = extract_article_details(article_url)

            # Display the results in the text area
            self.text_area.delete(1.0, tk.END)  # Clear previous content
            for key, value in article_data.items():
                self.text_area.insert(tk.END, f"{key.capitalize()}: \n")
                if isinstance(value, list):  # Key facts will be in a list
                    for fact in value:
                        self.text_area.insert(tk.END, f" - {fact}\n")
                else:
                    self.text_area.insert(tk.END, f"{value}\n\n")

# Create the Tkinter window
root = tk.Tk()
app = NewsApp(root)

# Run the GUI
root.mainloop()
