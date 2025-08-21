import tkinter as tk
from tkinter import messagebox
import feedparser
from newspaper import Article
from transformers import pipeline

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Function to fetch the BBC News RSS feed
def fetch_bbc_news_rss():
    url = 'http://feeds.bbci.co.uk/news/rss.xml'
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        author = entry.get('author', 'N/A')
        date = entry.published

        articles.append({
            'title': title,
            'author': author,
            'date': date,
            'link': link
        })

    return articles

# Function to fetch and summarize the full article
def summarize_article(url):
    # Fetch the article content using Newspaper3k
    article = Article(url)
    article.download()
    article.parse()

    # Summarize the article content using the BART model
    full_text = article.text
    input_length = len(full_text.split())
    ml = 150 if input_length > 150 else input_length
    minl = ml // 2
    summary = summarizer(full_text, max_length=ml, min_length=minl, do_sample=False)

    return summary[0]['summary_text']

# Function to show the summary in a popup window
def show_summary(url):
    try:
        summary = summarize_article(url)
        # Display summary in a new window or popup
        summary_window = tk.Toplevel(root)
        summary_window.title("Article Summary")
        
        summary_text = tk.Text(summary_window, wrap=tk.WORD, height=10, width=60)
        summary_text.insert(tk.END, summary)
        summary_text.config(state=tk.DISABLED)
        summary_text.pack(pady=10)
    except Exception as e:
        messagebox.showerror("Error", f"Error summarizing the article: {e}")

# Function to display articles
def display_articles():
    articles = fetch_bbc_news_rss()
    if not articles:
        messagebox.showerror("Error", "No articles found.")
        return

    # Create a frame for each article
    for article in articles:
        article_frame = tk.Frame(root)
        article_frame.pack(fill='x', pady=5)

        # Title, Author, and Date
        title_label = tk.Label(article_frame, text=article['title'], font=("Arial", 12, 'bold'), anchor='w', width=50, relief='solid', padx=5)
        title_label.pack(fill='x', pady=2)

        author_label = tk.Label(article_frame, text=f"Author: {article['author']}", anchor='w', width=50, relief='solid', padx=5)
        author_label.pack(fill='x', pady=2)

        date_label = tk.Label(article_frame, text=f"Published on: {article['date']}", anchor='w', width=50, relief='solid', padx=5)
        date_label.pack(fill='x', pady=2)

        # Summary button
        summary_button = tk.Button(article_frame, text="Show Summary", command=lambda url=article['link']: show_summary(url))
        summary_button.pack(pady=5)

# Create the main window
root = tk.Tk()
root.title("BBC News Scraper")

# Create a refresh button
refresh_button = tk.Button(root, text="Refresh", command=display_articles)
refresh_button.pack(pady=10)

# Run the initial fetch and display
display_articles()

# Start the GUI
root.mainloop()
