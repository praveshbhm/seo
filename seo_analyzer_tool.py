# seo_analyzer_tool.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
import pandas as pd
import re
import plotly.graph_objects as go

st.set_page_config(page_title="Advanced SEO Analyzer", layout="centered")
st.title("🔍 Advanced SEO Analyzer")
st.write("Enter a URL to perform an enhanced on-page SEO analysis including keyword density and SEO scores.")

url = st.text_input("Enter a full URL (e.g., https://example.com)")

def fetch_page_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        return response.text
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return None

def clean_and_tokenize(text):
    text = re.sub(r"[^a-zA-Z\s]", "", text.lower())
    words = text.split()
    stopwords = set([
        "the", "and", "is", "in", "to", "of", "for", "on", "with", "a", "an", "as", "by", "at",
        "this", "that", "it", "be", "are", "from", "or", "we", "you", "your", "can", "our"
    ])
    keywords = [word for word in words if word not in stopwords and len(word) > 2]
    return keywords, Counter(keywords), len(words), text

def get_ngram_density(words, n):
    ngrams = zip(*[words[i:] for i in range(n)])
    phrases = [' '.join(gram) for gram in ngrams]
    return Counter(phrases).most_common(10)

def analyze_seo(html):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title else "❌ No title tag"
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag else "❌ No meta description"
    h1_tags = [h1.get_text().strip() for h1 in soup.find_all("h1")]
    h1_info = h1_tags if h1_tags else ["❌ No H1 tag found"]

    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]
    images_total = len(images)
    images_missing_alt = len(missing_alt)

    text = soup.get_text(separator=' ', strip=True)
    words, keyword_counter, total_words, cleaned_text = clean_and_tokenize(text)

    bigrams = get_ngram_density(words, 2)
    trigrams = get_ngram_density(words, 3)
    fourgrams = get_ngram_density(words, 4)

    title_score = min(len(title), 60)
    desc_score = min(len(meta_description), 160)
    h1_score = 10 if h1_tags else 0
    image_score = 10 if images_total == 0 else round(((images_total - images_missing_alt) / images_total) * 10, 2)

    total_score = round((title_score / 60) * 30 + (desc_score / 160) * 30 + h1_score + image_score, 2)

    return {
        "title": title,
        "meta_description": meta_description,
        "h1_tags": h1_info,
        "images_total": images_total,
        "images_missing_alt": images_missing_alt,
        "word_count": total_words,
        "bigrams": bigrams,
        "trigrams": trigrams,
        "fourgrams": fourgrams,
        "title_score": title_score,
        "desc_score": desc_score,
        "total_score": total_score
    }

def render_gauge(label, value, max_value):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': label},
        gauge = {
            'axis': {'range': [0, max_value]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, max_value*0.5], 'color': "lightgray"},
                {'range': [max_value*0.5, max_value], 'color': "gray"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

def display_recommendations(score):
    st.subheader("📌 Recommendations")
    if score >= 85:
        st.success("Great job! Your page is well-optimized.")
    elif score >= 60:
        st.info("Good work, but there's room for improvement. Check title, description, and image ALT tags.")
    else:
        st.warning("SEO score is low. Ensure title, meta description, H1s, and image ALT attributes are all present and optimized.")

if url:
    if not urlparse(url).scheme:
        st.error("Please enter a valid URL with http:// or https://")
    else:
        html = fetch_page_content(url)
        if html:
            st.success("Page fetched successfully!")
            results = analyze_seo(html)

            st.subheader("🔖 Title Tag")
            st.write(results["title"])
            render_gauge("Title Length Score", results['title_score'], 60)

            st.subheader("📝 Meta Description")
            st.write(results["meta_description"])
            render_gauge("Meta Description Length Score", results['desc_score'], 160)

            st.subheader("📢 H1 Tags")
            for i, h1 in enumerate(results["h1_tags"], 1):
                st.write(f"H1 #{i}: {h1}")

            st.subheader("🖼️ Image ALT Tag Check")
            st.write(f"Total Images: {results['images_total']}")
            st.write(f"Missing ALT Text: {results['images_missing_alt']}")

            st.subheader("📊 Word Count")
            st.write(f"{results['word_count']} words on the page")

            st.subheader("🔗 2-Word Phrases (Bigrams)")
            for phrase, freq in results["bigrams"]:
                st.write(f"{phrase} — {freq} times")

            st.subheader("🔗 3-Word Phrases (Trigrams)")
            for phrase, freq in results["trigrams"]:
                st.write(f"{phrase} — {freq} times")

            st.subheader("🔗 4-Word Phrases")
            for phrase, freq in results["fourgrams"]:
                st.write(f"{phrase} — {freq} times")

            st.subheader("🏁 Total SEO Score")
            render_gauge("Total SEO Score", results['total_score'], 100)

            display_recommendations(results['total_score'])

            st.markdown("---")
            st.caption("Made with ❤️ using Streamlit")
