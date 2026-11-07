
import ollama

MODEL_NAME = "qwen2.5:3b"


def rewrite_query(query: str) -> str:

    if not query or not query.strip():
        raise ValueError("Question cannot be empty.")

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You rewrite questions into concise search queries. "
                        "Your task is only to rewrite the question. "
                        "Never answer it. Return only the rewritten query."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Rewrite this question for searching an uploaded document:\n"
                        + query.strip()
                    )
                }
            ],
            options={
                "temperature": 0.0,
                "num_predict": 80
            }
        )

        rewritten_query = response["message"]["content"].strip()

        if not rewritten_query:
            return query.strip()

        return rewritten_query

    except Exception as error:
        print(f"Query rewriting failed: {error}")
        return query.strip()
