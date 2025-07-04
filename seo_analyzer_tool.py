import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
import re
import plotly.graph_objects as go

st.set_page_config(page_title="Advanced SEO Analyzer", layout="centered")
st.title("🔍 Advanced SEO Analyzer")
st.markdown("*Developed by **Pravesh Patel***", unsafe_allow_html=True)
st.write("Enter a URL to perform an enhanced on-page SEO analysis including keyword density and SEO scores.")

url = st.text_input("Enter a full URL (e.g., https://example.com)")
target_keyword = st.text_input("Enter your target keyword/phrase (e.g., best SEO tools)").strip().lower()

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

def analyze_seo(html, keyword):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title else "❌ No title tag"

    meta_desc_tag = (
        soup.find("meta", attrs={"name": "description"}) or
        soup.find("meta", attrs={"name": "Description"}) or
        soup.find("meta", attrs={"property": "og:description"}) or
        soup.find("meta", attrs={"name": "twitter:description"})
    )
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.get("content") else "❌ No meta description"

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

    keyword_in_title = 5 if keyword and keyword in title.lower() else 0
    keyword_in_h1 = 5 if keyword and any(keyword in h.lower() for h in h1_tags) else 0
    keyword_in_meta = 5 if keyword and keyword in meta_description.lower() else 0
    canonical_tag = 5 if soup.find("link", rel="canonical") else 0

    keyword_consistency_score = 10 if keyword_in_title and keyword_in_meta and keyword_in_h1 else 0

    weighted_sum = (
        (title_score / 60) * 35 +
        (desc_score / 160) * 25 +
        h1_score + image_score +
        keyword_in_title + keyword_in_meta + keyword_in_h1 +
        canonical_tag + keyword_consistency_score
    )
    total_score = round((weighted_sum / 100) * 100, 2)

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
        "total_score": total_score,
        "keyword_consistent": keyword_consistency_score == 10,
        "keyword": keyword
    }

def render_gauge(label, value, max_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': label},
        gauge={
            'axis': {'range': [0, max_value]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value], 'color': "gray"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

def display_recommendations(score, results):
    st.subheader("📌 Recommendations")

    keyword = results["keyword"]
    title_missing = results["title"] == "❌ No title tag"
    desc_missing = results["meta_description"] == "❌ No meta description"
    h1_missing = not results["h1_tags"] or all(h == "❌ No H1 tag found" for h in results["h1_tags"])
    alt_missing = results["images_total"] > 0 and results["images_missing_alt"] == results["images_total"]

    if title_missing or desc_missing or h1_missing or alt_missing:
        st.warning("⚠️ Some important elements are missing:")
        if title_missing:
            st.write("- Missing **meta title**")
        if desc_missing:
            st.write("- Missing **meta description**")
        if h1_missing:
            st.write("- Missing **H1 tag**")
        if alt_missing:
            st.write("- All images are missing **ALT text**")
    else:
        if score >= 85:
            st.success("✅ Great job! Your page is well-optimized.")
        elif score >= 60:
            st.info("Good work, but there's room for improvement in keyword placement or content structure.")
        else:
            st.warning("SEO score is low. Improve content, metadata, and structure.")

    if keyword and not title_missing and not desc_missing and not h1_missing:
        if not results["keyword_consistent"]:
            st.error("⚠️ Keyword mismatch: The same keyword was not found in the **title**, **meta description**, and **H1 tag**.")

# Run app
if url:
    if not urlparse(url).scheme:
        st.error("Please enter a valid URL with http:// or https://")
    else:
        html = fetch_page_content(url)
        if html:
            st.success("Page fetched successfully!")
            results = analyze_seo(html, target_keyword)

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

            display_recommendations(results['total_score'], results)

            st.markdown("---")
            st.caption("Made with ❤️ using Streamlit | Developed by Pravesh Patel")
