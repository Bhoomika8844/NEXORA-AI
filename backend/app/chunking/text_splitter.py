from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(pages):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []

    for page in pages:

        page_text = page["text"]

        page_chunks = splitter.split_text(page_text)

        for chunk_index, chunk_text in enumerate(page_chunks):

            chunks.append({
                "chunk_id": len(chunks) + 1,
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "text": chunk_text
            })

    return chunks