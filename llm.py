# import streamlit as st
# from transformers import pipeline
# from langchain.llms import HuggingFacePipeline
# from langchain.prompts import PromptTemplate
# import pandas as pd
# import plotly.graph_objects as go

# class MultimodalProcessor:
#     def __init__(self):
#         """
#         Initialize multimodal processor with Hugging Face LLM
#         """
#         self.llm = self._initialize_llm()
#         self.vision_model = self._initialize_vision_model()

#     def _initialize_llm(self):
#         """
#         Initialize language model (Hugging Face)
#         """
#         model_name = "google/flan-t5-large"
#         pipe = pipeline("text2text-generation", model=model_name, max_length=512)
#         return HuggingFacePipeline(pipeline=pipe)

#     def _initialize_vision_model(self):
#         """
#         Initialize vision-language model
#         """
#         try:
#             vision_model = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")
#             return vision_model
#         except Exception as e:
#             st.warning(f"Vision model initialization failed: {e}")
#             return None

#     def process_text_query(self, document_context, query):
#         """
#         Process text-based queries with context
#         """
#         prompt_template = PromptTemplate(
#             input_variables=["context", "query"],
#             template="Context: {context}\n\nQuestion: {query}\n\nDetailed Answer:"
#         )
#         prompt = prompt_template.format(context=document_context, query=query)
#         return self.llm(prompt)

#     def process_image_query(self, image):
#         """
#         Process image-based queries
#         """
#         if self.vision_model is None:
#             st.error("Vision model not available")
#             return None

#         try:
#             image_desc = self.vision_model(image)[0]['generated_text']
#             return image_desc
#         except Exception as e:
#             st.error(f"Image processing error: {e}")
#             return None

#     def generate_code_for_plot(self, query):
#         """
#         Generate Plotly graph code for visualization queries
#         """
#         prompt = f"Create Python code using Plotly to {query}"
#         result = self.llm(prompt)
#         return result



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
        self.vision_model = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"  # Use the same or appropriate model for vision queries

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
            {"role": "system", "content": "You are a helpful assistant."},
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
