import logging
import streamlit as st
import pandas as pd
import tempfile
import os
import re
from src import AVAILABLE_MODELS, INPUT_DIR, OUTPUT_DIR, LOG_DIR, DB_PATH
from src import (
    init_db, 
    insert_upload, 
    insert_metadata, 
    insert_output,
    fetch_all_uploads, 
    fetch_metadata, 
    fetch_upload_blob,
    fetch_output_blob
)
import tempfile, os, re, uuid
from src.utils import setup_logger, DEBUG, INFO
from src.utils import (
    TextExtractionError, DOIParsingError, TitleAuthorParsingError,
    SummarizationError, DatabaseError, FileSaveError
)
from src import extract_text, find_doi_issn, extract_title_authors, Summarizer



def main():
    st.set_page_config(
        page_title="ResearchPaperSummarizer",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    batch_id = uuid.uuid4().hex
    log_path = os.path.join(LOG_DIR, f"{batch_id}.log")

    setup_logger(name=None, level=INFO, log_file=log_path)
    logger = logging.getLogger(__name__)
    logger.info(f"Logger configured, writing to {log_path}")


    try:
        conn = init_db(DB_PATH)
    except DatabaseError as e:
        logger.error("DB init failed", exc_info=e)
        st.error("Internal error initializing database.")
        return
    

    with st.sidebar:
        st.markdown("## How to use")
        st.markdown(
            "1. Upload PDFs  \n"
            "2. Select model  \n"
            "3. Click Process  \n"
            "4. Download Excel"
        )
        st.markdown("---")
        st.markdown("### Tips")
        st.markdown(
            "- OCR for scanned PDFs  \n"
            "- 3–5 sentence summary via LLaMA  \n"
            "- Download appears after processing"
        )
        st.markdown("---")
        st.caption("Built with Streamlit • llms via langchain groq api")


    st.markdown(
        "<h1 style='text-align: center; margin-bottom: 0.5rem;'> Research Paper Summarizer</h1>",
        unsafe_allow_html=True
    )
    st.markdown("<p style='text-align:center; color:#666;'>Extract DOI/ISSN, Title, Authors & summary</p>", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        uploaded = st.file_uploader(" Upload PDF files", type=["pdf"], accept_multiple_files=True)
        st.markdown("---")
        llm_model = st.selectbox(" Choose model", AVAILABLE_MODELS)

        read_all = st.checkbox(" Read all pages", value=True,
                           help="If unchecked, you can specify a maximum number of pages to process")


        if not read_all:
            pages_limit = st.number_input(
                "Max pages to read (must be ≥ 1)",
                min_value=1,
                step=1,
                value=1,
                help="Enter how many pages you want OCR’d/text-extracted"
            )
        else:
            pages_limit = None
        st.markdown("---")
        process_btn = st.button("Summarize")

    
    if uploaded and process_btn:

        logger.info(f"Starting batch {batch_id} ({len(uploaded)} files)")

        records = []
        with mid:
            progress = st.progress(0)
        total = len(uploaded)

        for idx, pdf in enumerate(uploaded, start=1):
            uid = uuid.uuid4().hex
            
            safe_name = pdf.name.replace(" ", "_")
            input_path = os.path.join(INPUT_DIR, f"{uid}_{safe_name}")

            try:

                content = pdf.read()
                with open(input_path, "wb") as f:
                    f.write(content)
                logger.info(f"Saved input: {input_path}")
            except Exception as e:
                logger.error(f"FileSaveError for {pdf.name}: {e}")
                st.warning(f"Could not save {pdf.name}, skipping.")
                continue


            try:
                insert_upload(conn, uid, pdf.name, content, llm_model)
                logger.debug(f"Inserted upload record: UID={uid}")
            except DatabaseError as e:
                logger.error(f"DB Error on upload insert UID={uid}: {e.message}")
                st.warning(f"Database error for {pdf.name}, skipping.")
                continue


            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(content)
            tmp.close()

            try:
                max_pages = None if read_all else pages_limit
                text = extract_text(tmp.name, ocr_max_pages=max_pages)                 
                meta = Summarizer(llm_model).extract_metadata(text)     # your LLM call

                rec = {
                "DOI/ISSN": meta.doi_issn,
                "Title":    meta.title,
                "Authors":  meta.authors,
                "Summary":  meta.summary
                }
                records.append(rec)
                insert_metadata(
                    conn,
                    uid,
                    batch_id,               # now passing batch_id
                    rec["DOI/ISSN"],
                    rec["Title"],
                    rec["Authors"],
                    rec["Summary"],
                    llm_model
                )
                logger.info(f"Processed UID={uid}: {rec['Title']}")
            except TextExtractionError as e:
                logger.warning(f"TextExtractionError UID={uid}: {e.message}")
            except DOIParsingError as e:
                logger.warning(f"DOIParsingError UID={uid}: {e.message}")
            except TitleAuthorParsingError as e:
                logger.warning(f"TitleAuthorParsingError UID={uid}: {e.message}")
            except SummarizationError as e:
                logger.error(f"SummarizationError UID={uid}: {e.message}")
            except DatabaseError as e:
                logger.error(f"DatabaseError on metadata insert UID={uid}: {e.message}")
            except Exception as e:
                logger.exception(f"Unexpected error UID={uid}: {e}")
            finally:
                os.unlink(tmp.name)

            progress.progress(idx / total)

        if records:
            try:
                
                df = pd.DataFrame(records)
                output_path = os.path.join(OUTPUT_DIR, f"{batch_id}.xlsx")
                df.to_excel(output_path, index=False, sheet_name="Metadata")
                logger.info(f"Wrote output Excel: {output_path}")

                
                with open(output_path, "rb") as f:
                    excel_bytes = f.read()
                insert_output(conn, batch_id, excel_bytes)
                logger.debug(f"Inserted output record for batch {batch_id}")

            except DatabaseError as e:
                logger.error(f"DatabaseError on output insert: {e.message}")
            except Exception as e:
                logger.error(f"Unexpected error inserting output: {e}")


            with mid:
                st.success(f" Completed batch {batch_id}")
                st.download_button(
                    " Download Metadata as Excel",
                    data=excel_bytes,
                    file_name=f"papers_{batch_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            with mid:
                st.error(" No metadata extracted; please check logs.")


    with mid:
        st.markdown("---")
        st.header(" Previously Processed File")

    try:
        uploads = fetch_all_uploads(conn)  
        if uploads:
            
            display_map = {
                f"{name} (at {ts}) — {uid}": uid
                for uid, name, ts in uploads
            }
            with mid:
                choice = st.selectbox(
                    "Select a file to view/download",
                    options=list(display_map.keys())
                )
            selected_uid = display_map[choice]

            # Fetch its metadata
            md = fetch_metadata(conn, selected_uid)
            if md:
                
                with mid:
                    st.subheader("Metadata")
                    # st.markdown(f"- **Batch ID:** `{md['batch_id']}`")
                    # st.markdown(f"- **Processed at:** `{md['processed_at']}`")
                    st.markdown(f"- **DOI/ISSN:** {md['doi_issn']}")
                    st.markdown(f"- **Title:** {md['title']}")
                    st.markdown(f"- **Authors:** {md['authors']}")
                    st.markdown(f"- **Summary:**  \n> {md['summary']}")
                    st.markdown(f"- **Model:** {md['model_name']}")

                # Download original PDF
                blob, fname = fetch_upload_blob(conn, selected_uid)
                if blob:
                    with mid:
                        st.download_button(
                            " Download Input PDF",
                            data=blob,
                            file_name=f"{selected_uid}_{fname}",
                            mime="application/pdf"
                        )

                # Download the Excel for this batch
                excel_blob = fetch_output_blob(conn, md["batch_id"])
                if excel_blob:
                    with mid:
                        st.download_button(
                            " Download Summary Excel",
                            data=excel_blob,
                            file_name=f"batch_{md['batch_id']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    with mid:
                        st.warning("No Excel found for this batch.")
            else:
                with mid:
                    st.warning("No metadata found for that UID.")
        else:
            with mid:
                st.info("No previous uploads found.")
    except DatabaseError as e:
        with mid:
            st.error(f"Error retrieving records: {e.message}")

if __name__ == "__main__":
    main()
