# seo_analyzer_tool.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
import pandas as pd
import re

st.set_page_config(page_title="Advanced SEO Analyzer", layout="centered")
st.title("🔍 Advanced SEO Analyzer")
st.write("Enter a URL to perform an enhanced on-page SEO analysis including keyword density.")

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
    return Counter(keywords), len(words)

def analyze_seo(html):
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title = soup.title.string.strip() if soup.title else "❌ No title tag"

    # Meta Description
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag else "❌ No meta description"

    # H1 Tags
    h1_tags = [h1.get_text().strip() for h1 in soup.find_all("h1")]
    h1_info = h1_tags if h1_tags else ["❌ No H1 tag found"]

    # Image ALT tags
    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]
    images_total = len(images)
    images_missing_alt = len(missing_alt)

    # Word count & keyword density
    text = soup.get_text(separator=' ', strip=True)
    word_count = len(text.split())
    keyword_counter, total_words = clean_and_tokenize(text)

    keyword_density = []
    for word, count in keyword_counter.most_common(20):
        density = round((count / total_words) * 100, 2)
        keyword_density.append({"Keyword": word, "Frequency": count, "Density (%)": density})

    return {
        "title": title,
        "meta_description": meta_description,
        "h1_tags": h1_info,
        "images_total": images_total,
        "images_missing_alt": images_missing_alt,
        "word_count": word_count,
        "keyword_density": keyword_density,
    }

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

            st.subheader("📝 Meta Description")
            st.write(results["meta_description"])

            st.subheader("📢 H1 Tags")
            for i, h1 in enumerate(results["h1_tags"], 1):
                st.write(f"H1 #{i}: {h1}")

            st.subheader("🖼️ Image ALT Tag Check")
            st.write(f"Total Images: {results['images_total']}")
            st.write(f"Missing ALT Text: {results['images_missing_alt']}")

            st.subheader("📊 Word Count")
            st.write(f"{results['word_count']} words on the page")

            st.subheader("🔑 Keyword Density Analysis")
            keyword_df = pd.DataFrame(results["keyword_density"])
            st.dataframe(keyword_df, use_container_width=True)

            st.markdown("---")
            st.caption("Made with ❤️ using Streamlit")
