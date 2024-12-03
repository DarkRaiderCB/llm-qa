import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from together import Together
from PIL import Image
import io
import pdfplumber
import docx
import base64

class MultimodalProcessor:
    def __init__(self):
        """
        Initialize multimodal processor with Together API
        """
        self.client = Together()
        self.llm_model = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"
        self.vision_model = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"

    def _api_call(self, model, messages):
        """
        Perform an API call to Together
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=None,
                temperature=0.7,
                top_p=0.6,
                top_k=70,
                repetition_penalty=1.2,
                stop=["<|eot_id|>", "<|eom_id|>"],
                stream=True
            )

            # Accumulate the response content
            output = ""
            for token in response:
                if hasattr(token, 'choices') and token.choices:
                    output += token.choices[0].delta.content

            return output
        except Exception as e:
            st.error(f"API call failed: {e}")
            return None

    def process_document(self, uploaded_file):
        """
        Process document to extract relevant text for querying Llama
        """
        filename = uploaded_file.name
        file_extension = filename.split('.')[-1].lower()
        try:
            if file_extension == 'txt':
                return uploaded_file.getvalue().decode('utf-8')

            elif file_extension == 'pdf':
                text = ""
                with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text()
                return text

            elif file_extension == 'docx':
                doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
                return '\n'.join([para.text for para in doc.paragraphs])

            elif file_extension in ['xlsx', 'csv']:
                df = pd.read_csv(uploaded_file) if file_extension == 'csv' else pd.read_excel(uploaded_file)
                return df

            elif file_extension in ['jpg', 'jpeg', 'png']:
                return Image.open(io.BytesIO(uploaded_file.getvalue()))

            else:
                raise ValueError(f"Unsupported file type: {file_extension}")

        except Exception as e:
            st.error(f"Error processing document: {e}")
            return None


    def process_text_query(self, document_context, query):
        """
        Process text-based queries with context
        """
        messages = [
            {"role": "system", "content": "You are a chatbot that helps basically answer questions based on the attachments (.doc, .txt, .xlxs, .csv, .pdf, image file). You can also perform math calculations, write codes and answer questions."},
            {"role": "user", "content": f"Context: {document_context}\n\nQuestion: {query}\n\nDetailed Answer:"}
        ]
        return self._api_call(self.llm_model, messages)

    def process_image_query(self, image):
        """
        Process image-based queries (convert to description before querying)
        """
        # Convert image to base64 and send it to the model
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        messages = [
            {"role": "system", "content": "You are a multimodal assistant capable of processing images."},
            {"role": "user", "content": f"Provide a description for this image (base64 encoded): {image_base64}"}
        ]
        return self._api_call(self.vision_model, messages)

    def generate_code_for_plot(self, query, document_content):
        """
        Generate Plotly graph code based on the query and document content.
        """
        # If the content is a DataFrame, include a summary for the LLM
        if isinstance(document_content, pd.DataFrame):
            content_summary = (
                f"The uploaded document contains a DataFrame with {document_content.shape[0]} rows "
                f"and {document_content.shape[1]} columns. Here are the column names: "
                f"{', '.join(document_content.columns)}."
            )
        else:
            content_summary = "The uploaded document is not a DataFrame."

        messages = [
            {"role": "system", "content": "You are a Python assistant skilled in creating Plotly visualizations based on uploaded attachment."},
            {"role": "user", "content": f"{content_summary} Generate Python code to {query} using this data. Just provide the code, nothing else. Assume df is the name of dataframe."}
        ]
        
        return self._api_call(self.llm_model, messages)

