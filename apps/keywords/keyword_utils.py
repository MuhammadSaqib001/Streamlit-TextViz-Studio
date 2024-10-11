import pandas as pd
import hashlib  # To create unique identifiers
from PyPDF2 import PdfReader
import re
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import zipfile

# Function to create unique identifiers for each document
def create_unique_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# Extract text from PDF files
def extract_text_from_pdfs(files):
    all_texts = []
    for file in files:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        all_texts.append((file.name, text))  # Store file name and text as a tuple
    return all_texts

# Extract text from CSV files
def extract_text_from_csvs(files):
    all_texts = []
    for file in files:
        df = pd.read_csv(file)
        if 'text' in df.columns:
            text = " ".join(df['text'].dropna().tolist())
            all_texts.append((file.name, text))  # Store file name and text as a tuple
        else:
            st.error(f"CSV file {file.name} must contain a 'text' column.")
    return all_texts

# Preprocessing functions for different languages
def clean_text(text, selected_language="English"):
    if selected_language == "English":
        return clean_text_english(text)
    elif selected_language == "French":
        return clean_text_french(text)
    elif selected_language == "Spanish":
        return clean_text_spanish(text)
    elif selected_language == "Italian":
        return clean_text_italian(text)
    elif selected_language == "Portuguese":
        return clean_text_portuguese(text)
    elif selected_language == "Chinese":
        return clean_text_chinese(text)
    elif selected_language == "Arabic":
        return clean_text_arabic(text)
    else:
        return text

# Function to clean English text
def clean_text_english(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Function to clean French text
def clean_text_french(text):
    text = text.lower()
    text = re.sub(r"[^a-zàâäéèêëîïôùûüç\s]", " ", text).strip()
    return text

# Function to clean Spanish text
def clean_text_spanish(text):
    text = text.lower()
    text = re.sub(r"[^a-záéíóúüñ\s]", " ", text).strip()
    return text

# Function to clean Italian text
def clean_text_italian(text):
    text = text.lower()
    text = re.sub(r"[^a-zàèéìòù\s]", " ", text).strip()
    return text

# Function to clean Portuguese text
def clean_text_portuguese(text):
    text = text.lower()
    text = re.sub(r"[^a-záàâãéêíóôõúç\s]", " ", text).strip()
    return text

# Function to clean Chinese text
def clean_text_chinese(text):
    text = re.sub(r"[^\u4e00-\u9fff\s]", " ", text)  # Remove non-Chinese characters
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Function to clean Arabic text
def clean_text_arabic(text):
    text = re.sub(r"[^\u0600-\u06FF\s]", " ", text)  # Remove non-Arabic characters
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Function to analyze custom keywords and generate the required dataframe
def analyze_custom_keywords(text_data, keywords):
    keyword_freq = { "Features": keywords }
    # Collect the frequency of each keyword in each document
    for file_name, text in text_data:
        keyword_counts = []
        for keyword in keywords:
            matches = re.findall(keyword.lower(), text.lower())  # Case-insensitive matching
            count = len(matches)
            keyword_counts.append(count)
        keyword_freq[file_name] = keyword_counts
    keyword_df = pd.DataFrame(keyword_freq)
    return keyword_df

# Function to generate word clouds and return as BytesIO object for display and download
def generate_wordcloud(df, colormap):
    if colormap:
        wordcloud = WordCloud(width=3840, height=2160, background_color="white", colormap=colormap).generate_from_frequencies(dict(zip(df['Features'], df[df.columns[1]])))
    else:
        wordcloud = WordCloud(width=3840, height=2160, background_color="white").generate_from_frequencies(dict(zip(df['Features'], df[df.columns[1]])))
    
# Function to create a ZIP file of all outputs
def create_zip_with_outputs(result_df):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        # Add DataFrame CSV to the ZIP
        csv_data = result_df.to_csv(index=False).encode('utf-8')
        zip_file.writestr('analysis_results.csv', csv_data)
        
        # Add WordCloud PNGs to the ZIP (if they exist)
        wordcloud_image = generate_wordcloud(result_df, colormap_options[color_scheme])
        zip_file.writestr('custom_keyword_wordcloud.png', wordcloud_image.read())

    zip_buffer.seek(0)
    return zip_buffer

# Function to display and download the results with all outputs bundled in a ZIP file
def display_custom_keyword_results(keyword_df):
    # Create tabs for DataFrame and WordClouds
    tab1, tab2 = st.tabs(["DataFrame", "Custom Keyword Word Cloud"])
    