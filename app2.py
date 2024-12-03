import streamlit as st
from process2 import DocumentLoader
from llm2 import MultimodalProcessor
import pandas as pd
from PIL import Image
import plotly.graph_objects as go

def main():
    st.title("💬 Multimodal Document Chat App")

    # Document Upload
    uploaded_files = st.file_uploader(
        "Upload Documents",
        accept_multiple_files=True,
        type=['txt', 'pdf', 'docx', 'xlsx', 'csv', 'jpg', 'png']
    )

    # Initialize processors
    document_loader = DocumentLoader()
    llm_processor = MultimodalProcessor()

    # Session state for chat history and uploaded documents
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}

    if uploaded_files:
        for file in uploaded_files:
            file_key = file.name

            if file_key not in st.session_state.chat_history:
                st.session_state.chat_history[file_key] = []

            # Load document
            document_content = document_loader.load_document(file)

            # Display file content
            st.subheader(f"Document: {file.name}")

            if isinstance(document_content, pd.DataFrame):
                st.dataframe(document_content)

            elif isinstance(document_content, Image.Image):
                st.image(document_content, caption=f"Uploaded Image: {file.name}")
                image_description = llm_processor.process_image_query("Image uploaded for processing")
                if image_description:
                    st.write("Image Description:", image_description)

            elif document_content:
                st.text(document_content[:500] + "...")  # Preview

            # Chat-like interaction
            st.subheader("Chat")
            chat_container = st.container()

            with chat_container:
                for query, response in st.session_state.chat_history[file_key]:
                    st.markdown(f"**You:** {query}")
                    st.markdown(f"**Bot:** {response}")

            query = st.text_input(f"Ask a question about {file.name} or generate visualizations")

            if query:
                history_context = "\n".join(
                    f"User: {q}\nBot: {r}" for q, r in st.session_state.chat_history[file_key]
                )
                context = f"{document_content}\n\n{history_context}"

                # Handle plot requests
                if isinstance(document_content, pd.DataFrame) and query.lower().startswith("plot"):
                    plot_code = llm_processor.generate_code_for_plot(query)
                    st.code(plot_code, language="python")
                    try:
                        exec_globals = {"pd": pd, "go": go, "st": st, "data": document_content}
                        exec(plot_code, exec_globals)
                        st.plotly_chart(exec_globals.get("fig"))
                        response = "Plot generated successfully."
                    except Exception as e:
                        response = f"Error in generating plot: {e}"
                else:
                    response = llm_processor.process_text_query(context, query)

                st.session_state.chat_history[file_key].append((query, response))
                st.markdown(f"**Bot:** {response}")

if __name__ == "__main__":
    main()
