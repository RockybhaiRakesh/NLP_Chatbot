import re
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY not found in .env")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

def semantic_keywords_gemini(query):
    """Extract search keywords using Gemini"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
Extract the top 20 most important keywords from this question that would help search a text file.
Focus on specific nouns, names, and meaningful phrases. Exclude common words.

Query: "{query}"

Respond as a Python list: ["keyword1", "keyword2", ...]
"""
    try:
        response = model.generate_content(prompt)
        match = re.findall(r'\[.*?\]', response.text)
        if match:
            return eval(match[0])  # Convert string list to actual list
    except Exception as e:
        st.error(f"Keyword extraction error: {e}")
    return []

def search_text_file(file_content, keywords):
    """Search text file for keywords and return matching snippets"""
    if not keywords:
        return "No keywords found."

    # Create regex pattern that matches any keyword
    pattern = "|".join(sorted([re.escape(k) for k in keywords], key=len, reverse=True))
    matches = list(re.finditer(pattern, file_content, re.IGNORECASE))

    snippets = []
    for match in matches[:10]:  # Limit to 10 snippets
        start = max(match.start() - 100, 0)  # 100 chars before match
        end = min(match.end() + 100, len(file_content))  # 100 chars after match
        
        # Adjust to nearest word boundaries
        while start > 0 and file_content[start - 1].isalnum():
            start -= 1
        while end < len(file_content) and file_content[end].isalnum():
            end += 1
            
        snippet = file_content[start:end].strip()
        snippets.append(f"...{snippet}...")  # Add ellipsis for context

    return "\n\n".join(snippets) if snippets else "No matches found."

def ask_gemini(question, context):
    """Ask Gemini to answer based on the text file content"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
Answer this question based ONLY on the provided text content.
If the answer isn't found, say "Not found in the text."

Question: "{question}"

Text Content:
\"\"\"
{context}
\"\"\"

Provide a concise answer with relevant details if available.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    st.title("🔍 Smart Text File Search")
    st.markdown("Upload a text file and ask questions about its content")

    # File upload
    uploaded_file = st.file_uploader("Choose a text file", type=["txt"])
    
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8", errors="ignore")
        
        # Question input
        question = st.text_input("Ask a question about the file content:")
        
        if question:
            with st.spinner("Processing..."):
                # Step 1: Extract keywords
                keywords = semantic_keywords_gemini(question)
                if not keywords:
                    st.warning("Couldn't extract keywords. Trying with full question.")
                    keywords = [question]
                
                st.info(f"Searching for: {', '.join(keywords)}")
                
                # Step 2: Search file
                context = search_text_file(file_content, keywords)
                
                # Show snippets if found
                if "No matches" not in context:
                    with st.expander("📝 Matching Text Snippets"):
                        st.text(context)
                
                # Step 3: Ask Gemini
                answer = ask_gemini(question, context)
                st.subheader("Answer:")
                st.write(answer)

if __name__ == "__main__":
    main()