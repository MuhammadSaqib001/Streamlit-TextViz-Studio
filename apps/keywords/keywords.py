import streamlit as st
import pandas as pd
import hashlib  # To create unique identifiers
from PyPDF2 import PdfReader
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import zipfile

# Set the page layout option in Streamlit for wide format
st.set_page_config(page_title='Text2Keywords', page_icon='🏷️', layout="wide", initial_sidebar_state="expanded")

# Sidebar: Title and description
st.sidebar.title("Keyword & N-gram Analysis Tool")
st.sidebar.markdown("""
**Analyze keyword frequency and discover n-grams from your text data.**

- **Upload multiple CSV or PDF files** for analysis.
- **Input custom keywords** or let the app automatically discover the most frequent unigrams, bigrams, and trigrams.
- **Download your analysis results** in a convenient ZIP format with all outputs.
""")

# Initialize session state to keep track of uploaded data
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None
    st.session_state.analysis_data = None

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

st.subheader("Import Data")

# File uploader to handle CSV or PDF files
uploaded_files = st.file_uploader("Upload CSV or PDF files", type=["csv", "pdf"], accept_multiple_files=True)
if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

st.warning("For CSV files, ensure that the text data is in a column named 'text'.")

# Move language selection to the main page
language_option = st.selectbox(
    "Select the language of your text:",
    ("English", "French", "Spanish", "Italian", "Portuguese", "Chinese", "Arabic")
)

# Instructions for custom keyword input, with examples
st.subheader("Setting Parameters")

# Give users a choice between inputting custom keywords or automatic discovery
analysis_option = st.radio("How would you like to perform the analysis?", ("Input Custom Keywords", "Discover Automatically"))

# If user selects custom keywords, show the input box for entering keywords
custom_keywords = None
if analysis_option == "Input Custom Keywords":
    st.warning("**Instructions:** Enter one keyword or regular expression per line. For example: \n - **word** finds exact matches of the word 'word'. \n - **word(s|ing|ed)**: Finds 'word', 'words', 'wording', and 'worded'. \n - **\\d+** finds any sequence of digits (e.g., 123).")   
    custom_keywords = st.text_area("Enter your custom keywords (one per line)", height=150)
else:
    top_n = st.number_input("Select how many top terms to discover for each n-gram type", min_value=1, max_value=100, value=10)

# Add the transpose option before running the analysis
transpose_data = st.checkbox("Transpose the DataFrame for analysis and download", value=False)

# Restrict colormap options for the word cloud
colormap_options = {
    "Default": None,
    "Monochromatic Blue": "Blues",
    "Monochromatic Green": "Greens",
    "Warm Tones": "autumn",
    "Cool Tones": "cool",
    "Pastel Colors": "Pastel1",
    "Grayscale": "gray",
    "Earth Tones": "terrain",
    "High Contrast": "Set1",
    "Colorblind-Friendly": "tab10"
}

# WordCloud color scheme selection
color_scheme = st.selectbox("Select WordCloud Color Scheme", options=list(colormap_options.keys()))

# Analysis button
analyze_button = st.button("Run Analysis")

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
    
    # Save the word cloud image to a BytesIO buffer
    buffer = BytesIO()
    plt.figure(figsize=(16, 9), dpi=300)  # High-quality 4K-like resolution
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
    buffer.seek(0)
    plt.close()
    return buffer

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
    
    # Display DataFrame in the first tab
    with tab1:
        st.subheader("Custom Keywords Analysis Results")
        st.dataframe(keyword_df)

    # Display Custom Keyword Word Cloud in the second tab
    with tab2:
        st.subheader("Custom Keyword Word Cloud")
        wordcloud_image = generate_wordcloud(keyword_df, colormap_options[color_scheme])
        st.image(wordcloud_image, use_column_width=True)

    # Create ZIP file with all outputs
    zip_file = create_zip_with_outputs(keyword_df)

    # Provide download button for the ZIP file
    st.download_button(
        label="Download All Outputs (ZIP)",
        data=zip_file,
        file_name="analysis_results.zip",
        mime="application/zip"
    )

# Run the analysis when the user clicks the button
if analyze_button and st.session_state.uploaded_files is not None:
    with st.spinner("Analyzing data..."):
        text_data = []

        # Separate PDFs and CSVs
        pdf_files = [file for file in st.session_state.uploaded_files if file.type == "application/pdf"]
        csv_files = [file for file in st.session_state.uploaded_files if file.type == "text/csv"]

        # Extract text from files
        if pdf_files:
            pdf_texts = extract_text_from_pdfs(pdf_files)
            text_data.extend(pdf_texts)
        if csv_files:
            csv_texts = extract_text_from_csvs(csv_files)
            text_data.extend(csv_texts)

        # Clean text based on language option
        text_data = [(file_name, clean_text(text, selected_language=language_option)) for file_name, text in text_data]

        if analysis_option == "Input Custom Keywords" and custom_keywords:
            # Analyze custom keywords
            keywords = custom_keywords.splitlines()
            keyword_df = analyze_custom_keywords(text_data, keywords)
            display_custom_keyword_results(keyword_df)