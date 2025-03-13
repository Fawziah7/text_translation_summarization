import tkinter as tk
from tkinter import scrolledtext, filedialog
import requests
from googletrans import Translator
from textblob import TextBlob
import os
from docx import Document  
import fitz 

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HUGGINGFACE_API_TOKEN = ""

def translate_to_english(text):
    translator = Translator()
    translated = translator.translate(text, src="auto", dest="en")
    return translated.text

def summarize_text(text, summary_length):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    blob = TextBlob(text)
    sentences = blob.sentences
    num_sentences = len(sentences)

    if num_sentences < 3:
        return "Text is too short to summarize. Here is the original:\n" + text

    if summary_length == "Short":
        min_words, max_words = 30, 60
    elif summary_length == "Medium":
        min_words, max_words = 60, 130
    elif summary_length == "Long":
        min_words, max_words = 130, 200
    else:
        min_words, max_words = 60, 130

    summary_sentences = []
    word_count = 0
    unique_sentences = set()

    for sentence in sentences:
        if str(sentence) not in unique_sentences:
            summary_sentences.append(str(sentence))
            unique_sentences.add(str(sentence))
            word_count += len(sentence.words)
        if word_count >= min_words:
            break

    summary_text = " ".join(summary_sentences)
    payload = {"inputs": summary_text, "parameters": {"min_length": min_words, "max_length": max_words}}
    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)

    try:
        refined_summary = response.json()[0]["summary_text"]
    except:
        refined_summary = summary_text + "\n\n(Note: This is a manually generated summary due to API failure.)"

    final_summary = str(TextBlob(refined_summary).correct())
    return final_summary

def tone_detection(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  
    subjectivity = blob.sentiment.subjectivity  

    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def process_text():
    input_text = input_box.get("1.0", tk.END).strip()
    summary_length = length_var.get()
    if not input_text:
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, "Please enter some text to process.")
        return

    translator = Translator()
    detected_language = translator.detect(input_text).lang
    if detected_language != "en":
        input_text = translate_to_english(input_text)

    summary = summarize_text(input_text, summary_length)
    tone = tone_detection(input_text)

    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, f"Detected Language: {detected_language}\n\n")
    output_box.insert(tk.END, "Summary:\n")
    output_box.insert(tk.END, summary + "\n\n")
    output_box.insert(tk.END, "Tone Detection:\n")
    output_box.insert(tk.END, f"Overall Tone: {tone}\n")

def clear_text():
    input_box.delete("1.0", tk.END)
    output_box.delete("1.0", tk.END)

def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("Word Documents", "*.docx"), ("PDF Files", "*.pdf")])
    if not file_path:
        return

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".txt":
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    elif file_extension == ".docx":
        doc = Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs])
    elif file_extension == ".pdf":
        doc = fitz.open(file_path)
        content = "\n".join([page.get_text("text") for page in doc])
    else:
        return

    input_box.delete("1.0", tk.END)
    input_box.insert(tk.END, content)

window = tk.Tk()
window.title("Text Translator and Summarizer with NLP Features")
window.geometry("800x750")

file_button = tk.Button(window, text="Load File", command=load_file)
file_button.pack(pady=5)

input_label = tk.Label(window, text="Input Text (any language):")
input_label.pack(pady=5)
input_box = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=80, height=15)
input_box.pack(pady=5)

length_label = tk.Label(window, text="Choose Summary Length:")
length_label.pack(pady=5)
length_var = tk.StringVar(value="Medium")
length_menu = tk.OptionMenu(window, length_var, "Short", "Medium", "Long")
length_menu.pack(pady=5)

process_button = tk.Button(window, text="Translate, Summarize, and Analyze", command=process_text)
process_button.pack(pady=10)

clear_button = tk.Button(window, text="Clear Text", command=clear_text)
clear_button.pack(pady=5)

output_label = tk.Label(window, text="Output:")
output_label.pack(pady=5)
output_box = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=80, height=15)
output_box.pack(pady=5)

window.mainloop()
