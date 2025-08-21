import feedparser
import tkinter as tk
from tkinter import ttk
import webbrowser
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define function to fetch related articles
def get_related_articles(article_url):
    search_url = f"https://news.google.com/search?q={article_url}&hl=en-US&gl=US&ceid=US:en"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    related_articles = []

    # Find related articles in the Google News results
    for item in soup.find_all('a', class_='DY5T1d'):
        title = item.get_text()
        link = "https://news.google.com" + item['href'][1:]
        related_articles.append({'title': title, 'link': link})

    print(f"Found {len(related_articles)} related articles.")
    return related_articles

# Define function to fetch article content
def fetch_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the article text, this may vary based on the website structure
    paragraphs = soup.find_all('p')
    content = ' '.join([para.get_text() for para in paragraphs])

    print(f"Fetched article content: {content[:100]}...")  # Print the first 100 characters as a preview
    return content

# Define function to display the articles in the GUI
def display_related_articles_gui(original_article, related_articles):
    root = tk.Tk()
    root.title("Related Articles")

    # Create Treeview widget to display related articles
    tree = ttk.Treeview(root, columns=('Title', 'Link'), show='headings')
    tree.heading('Title', text='Title')
    tree.heading('Link', text='Link')

    # Insert the original article
    tree.insert('', 'end', values=(original_article['title'], original_article['link']))

    # Insert related articles
    for article in related_articles:
        tree.insert('', 'end', values=(article['title'], article['link']))

    tree.pack(expand=True, fill='both')

    # Open link in browser on double click
    def open_link(event):
        selected_item = tree.selection()
        if selected_item:
            values = tree.item(selected_item[0], 'values')
            if values:
                webbrowser.open(values[1])

    tree.bind('<Double-1>', open_link)

    root.mainloop()

# Main function to find similar articles and display in GUI
def find_similar_articles(article_url):
    # Fetch the main article
    article_content = fetch_article_content(article_url)
    
    # Get related articles using Google News
    related_articles = get_related_articles(article_url)

    # Display related articles in GUI
    original_article = {'title': 'Original Article', 'link': article_url}
    display_related_articles_gui(original_article, related_articles)

if __name__ == "__main__":
    # Example article URL (replace with the actual URL you want to analyze)
    article_url = "https://www.bbc.co.uk/news/articles/cly74mpy8klo"
    find_similar_articles(article_url)
