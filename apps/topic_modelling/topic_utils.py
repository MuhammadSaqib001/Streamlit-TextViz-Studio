import streamlit as st
import pandas as pd
import numpy as np
import random
import openai
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, OpenAI, TextGeneration
from sentence_transformers import SentenceTransformer
from umap import UMAP
from sklearn.feature_extraction.text import CountVectorizer
import ast  # To safely evaluate string input to list format
import hashlib  # To create unique identifiers
from transformers import pipeline

# Function to create unique identifiers for each document
def create_unique_id(text):
    return hashlib.md5(text.encode()).hexdigest()

# Function to extract text from CSV file and add unique identifiers (doc_id)
def extract_topic_text_from_csv(file):
    df = pd.read_csv(file)
    if 'text' in df.columns:
        df = df.dropna(subset=['text'])
        df['doc_id'] = df['text'].apply(create_unique_id)  # Create unique doc_id for each text
        return df[['doc_id', 'text']].reset_index(drop=True), df
    else:
        st.error("The CSV file must contain a 'text' column.")
        return None, None

# Define function to display outputs (reused after both model fitting and topic merging)
def display_outputs(BERTmodel, text_data, doc_ids):
    # Use the built-in method to fetch topic info
    topic_info_df = BERTmodel.get_topic_info()  # This will include topic numbers, counts, and possibly labels
    
    # Remove "Name" column if it exists
    columns_to_remove = ['Name', 'Representation']
    topic_info_df = topic_info_df.drop(columns=[col for col in columns_to_remove if col in topic_info_df.columns], errors='ignore')
    
    # Show the identified topics and intertopic distance map
    topic_col, map_col = st.columns([1, 1])
    with topic_col:
        st.write("Identified Topics:")
        st.dataframe(topic_info_df)

    with map_col:
        st.write("Intertopic Distance Map:")
        intertopic_map = BERTmodel.visualize_topics()
        st.plotly_chart(intertopic_map)

    # Show document-topic probabilities with doc_id
    st.write("Document-Topic Probabilities:")
    doc_info_df = BERTmodel.get_document_info(text_data)

    # Add the doc_id to document-topic probabilities for easy merging later
    doc_info_df['doc_id'] = doc_ids['doc_id'].tolist()

    # Remove unnecessary columns
    columns_to_remove = ['Name', 'Top_n_words', 'Representative Docs', 'Representative_document']
    doc_info_df = doc_info_df.drop(columns=[col for col in columns_to_remove if col in doc_info_df.columns])

    st.dataframe(doc_info_df)

# Function to create download link for DataFrame as CSV
def create_download_link(df, filename, link_text):
    csv = df.to_csv(index=False)
    st.download_button(label=link_text, data=csv, file_name=filename)