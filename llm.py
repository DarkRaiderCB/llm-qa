import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from together import Together

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

    def process_text_query(self, document_context, query):
        """
        Process text-based queries with context
        """
        messages = [
            {"role": "system", "content": "You are a chatbot that helps basically answer questions based on the attachments (.doc, .txt, .xlxs, .csv, .pdf, image file). You can also perform math calculations, write codes and answer qurestions."},
            {"role": "user", "content": f"Context: {document_context}\n\nQuestion: {query}\n\nDetailed Answer:"}
        ]
        return self._api_call(self.llm_model, messages)

    def process_image_query(self, image_description):
        """
        Process image-based queries (convert to description before querying)
        """
        messages = [
            {"role": "system", "content": "You are a multimodal assistant capable of processing images."},
            {"role": "user", "content": f"Describe this image: {image_description}"}
        ]
        return self._api_call(self.vision_model, messages)

    def generate_code_for_plot(self, query):
        """
        Generate Plotly graph code for visualization queries
        """
        messages = [
            {"role": "system", "content": "You are a code assistant skilled in Python and Plotly."},
            {"role": "user", "content": f"Create Python code using Plotly to {query}"}
        ]
        return self._api_call(self.llm_model, messages)
