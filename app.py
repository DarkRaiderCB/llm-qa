import streamlit as st
from llm import MultimodalProcessor
import pandas as pd
from PIL import Image
import re
import plotly.graph_objects as go
import plotly_express as px

MAX_HISTORY_LENGTH = 5  # Limit chat to the last 5 interactions

PLOT_KEYWORDS = ['plot', 'chart', 'graph', 'visualize', 'show', 'draw', 'depict', 'represent']

def main():
    st.title("💬 Multimodal Document Chat App")

    # Document Upload
    uploaded_files = st.file_uploader(
        "Upload Documents",
        accept_multiple_files=True,
        type=['txt', 'pdf', 'docx', 'xlsx', 'csv', 'jpg', 'png']
    )

    # Initialize processor
    llm_processor = MultimodalProcessor()

    # Session state for chat history and uploaded documents
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}

    if uploaded_files:
        for file in uploaded_files:
            file_key = file.name

            if file_key not in st.session_state.chat_history:
                st.session_state.chat_history[file_key] = []

            # Process document
            document_content = llm_processor.process_document(file)

            # Display file content
            st.subheader(f"Document: {file.name}")

            if isinstance(document_content, pd.DataFrame):
                st.dataframe(document_content)

            elif isinstance(document_content, Image.Image):
                st.image(document_content, caption=f"Uploaded Image: {file.name}")
                image_description = llm_processor.process_image_query("Image uploaded for processing")
                if image_description:
                    st.write("Image Description:", image_description)

            elif isinstance(document_content, str):
                st.text(document_content[:500] + "...")  # Preview

            else:
                st.error("Unsupported file type or content could not be processed.")

            # Chat-like interaction
            st.subheader("Chat")
            chat_container = st.container()

            with chat_container:
                for query, response in st.session_state.chat_history[file_key]:
                    st.markdown(f"**You:** {query}")
                    st.markdown(f"**Bot:** {response}")

            query = st.text_input(f"Ask a question about {file.name} or generate visualizations")

            if query:
                # Limit the number of interactions in the context
                history_context = "\n".join(
                    f"User: {q}\nBot: {r}" for q, r in st.session_state.chat_history[file_key][-MAX_HISTORY_LENGTH:]
                )

                # Focus context: Add the most relevant part of the document and chat history
                relevant_document_content = document_content if isinstance(document_content, str) else ""
                context = f"{relevant_document_content[-1000:]}\n\n{history_context}"

                # Check if the query contains any of the plot-related keywords
                if any(keyword in query.lower() for keyword in PLOT_KEYWORDS):
                    if isinstance(document_content, pd.DataFrame):
                        # Check if the required column exists in the DataFrame
                        if 'engagement_rate' in document_content.columns:
                            content_summary = (
                                f"The uploaded document contains a DataFrame with {document_content.shape[0]} rows "
                                f"and {document_content.shape[1]} columns. Here are the column names: "
                                f"{', '.join(document_content.columns)}."
                            )

                            # Generate the plot code based on the content summary
                            plot_code = llm_processor.generate_code_for_plot(query, document_content)

                            # Regex to extract code between ```python and ```
                            match = re.search(r'```python(.*?)```', plot_code, re.DOTALL)

                            if match:
                                plot_code = match.group(1).strip()
                                st.code(plot_code, language="python")

                                try:
                                    # Dynamically execute the code using `exec`
                                    local_vars = {}
                                    # Inject the DataFrame into the local execution context
                                    exec(plot_code, {"pd": pd, "px": px, "df": document_content}, local_vars)

                                    # Check for 'fig' in local_vars and display it
                                    if "fig" in local_vars and isinstance(local_vars["fig"], go.Figure):
                                        st.plotly_chart(local_vars["fig"], use_container_width=True)
                                    else:
                                        st.error("Plot code executed, but no valid Plotly figure ('fig') was generated.")
                                except Exception as e:
                                    st.error(f"Error executing plot code: {e}")
                            else:
                                st.error("No valid Python code found in the response.")
                        else:
                            st.error("The column 'engagement_rate' does not exist in the uploaded dataset.")
                    else:
                        st.error("The uploaded file is not a valid CSV or Excel file for generating plots.")


                else:
                    response = llm_processor.process_text_query(context, query)
                    st.session_state.chat_history[file_key].append((query, response))
                    st.markdown(f"**Bot:** {response}")

if __name__ == "__main__":
    main()
