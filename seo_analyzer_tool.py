# seo_analyzer_tool.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

st.set_page_config(page_title="Basic SEO Analyzer", layout="centered")
st.title("🔍 Basic SEO Analyzer")
st.write("Enter a URL to perform a simple on-page SEO analysis.")

url = st.text_input("Enter a full URL (e.g., https://example.com)")

def fetch_page_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        return response.text
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return None

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

    # Word count
    text = soup.get_text(separator=' ', strip=True)
    word_count = len(text.split())

    return {
        "title": title,
        "meta_description": meta_description,
        "h1_tags": h1_info,
        "images_total": images_total,
        "images_missing_alt": images_missing_alt,
        "word_count": word_count,
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

            st.markdown("---")
            st.caption("Made with ❤️ using Streamlit")
