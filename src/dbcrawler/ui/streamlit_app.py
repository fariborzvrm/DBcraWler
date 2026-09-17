"""Streamlit UI for DBcraWler (Phase 4).

Run against the Phase 4 API:

    uv run uvicorn dbcrawler.api.app:create_app --factory --port 8000
    uv run --extra ui streamlit run src/dbcrawler/ui/streamlit_app.py

Requires the API to be running (DB + OPENROUTER_API_KEY in .env).
"""

import json
import os
import time

import httpx
import streamlit as st

API_URL = os.environ.get("DBCRAWLER_API_URL", "http://127.0.0.1:8000")


def api(path: str) -> httpx.Response:
    return httpx.get(f"{API_URL}{path}", timeout=10.0)


def ask(question: str) -> httpx.Response:
    return httpx.post(
        f"{API_URL}/v1/query", json={"question": question}, timeout=300.0
    )


def send_feedback(entry_id: str, correct: bool, comment: str = "") -> None:
    httpx.post(
        f"{API_URL}/v1/feedback/{entry_id}",
        json={"correct": correct, "comment": comment},
        timeout=10.0,
    )


def render_history() -> None:
    with st.expander("Session query history"):
        try:
            history = api("/v1/history?limit=50").json()
        except httpx.HTTPError as exc:
            st.warning(f"History unavailable: {exc}")
            return
        if not history:
            st.caption("No queries yet.")
            return
        feedback_map = {"True": "correct", "False": "incorrect"}
        for entry in history:
            when = time.strftime("%H:%M:%S", time.localtime(entry["timestamp"]))
            label = (
                f"{when} - {entry['question'][:60]} "
                f"[{entry['status']}, conf={entry['confidence']['final'] if entry['confidence'] else 'n/a'}"
                + (
                    f", {feedback_map[str(entry['feedback']['correct'])]}]"
                    if entry["feedback"]
                    else "]"
                )
            )
            with st.expander(label):
                st.code(entry["sql"] or "-", language="sql")
                cols = st.columns(2)
                if cols[0].button("Correct", key=f"ok-{entry['id']}"):
                    send_feedback(entry["id"], True)
                    st.rerun()
                if cols[1].button("Incorrect", key=f"bad-{entry['id']}"):
                    send_feedback(entry["id"], False)
                    st.rerun()


def render_breakdown(confidence: dict | None) -> None:
    if not confidence:
        st.info("No confidence breakdown for this result.")
        return
    st.metric("Confidence", f"{confidence['final']:.2f}")
    for field in (
        "llm_self_report",
        "intent_alignment",
        "sanity_pass_rate",
        "schema_coverage",
        "multiquery_agreement",
    ):
        value = confidence.get(field)
        if value is not None:
            st.write(f"**{field}**: `{value}`")


def main() -> None:
    st.set_page_config(page_title="DBcraWler", layout="wide")
    st.title("DBcraWler")
    st.caption("Natural language -> guarded SQL -> validated results")

    question = st.text_input("Your question", key="question")
    run = st.button("Ask", type="primary", disabled=len((question or "").strip()) < 3)
    if run:
        with st.spinner("Generating, guarding, executing, validating..."):
            try:
                response = ask(question.strip())
            except httpx.HTTPError as exc:
                st.error(f"API unreachable: {exc}")
                return
        if response.status_code != 200:
            st.error(f"API error {response.status_code}: {response.text}")
            return

        body = response.json()
        st.info(f"status: **{body['status']}**  |  id: `{body['id']}`")
        if body.get("warnings"):
            st.warning("warnings: " + "; ".join(body["warnings"]))

        if body["status"] == "clarification_needed":
            st.subheader("Question is ambiguous - please clarify")
            for inter in body.get("ambiguity") or []:
                st.markdown(f"- {inter['description']}")
                st.code(inter["example_sql"], language="sql")
        elif body["status"] == "blocked":
            st.error("Generated SQL was blocked by guardrails.")
        else:
            st.subheader("SQL")
            st.code(body["sql"] or "-", language="sql")

            st.subheader("Results")
            results = body.get("results") or []
            if results:
                st.dataframe(results, use_container_width=True)
                st.caption(
                    f"{body.get('row_count')} rows"
                    f"{' (truncated)' if body.get('truncated') else ''}"
                    f" - {body.get('execution_time_ms')}ms"
                )
            else:
                st.caption("No rows returned.")

            st.subheader("Confidence & breakdown")
            render_breakdown(body.get("confidence"))

            if body.get("sanity"):
                st.markdown("**Sanity checks**")
                for finding in body["sanity"]:
                    icon = "pass" if finding["passed"] else "FAIL"
                    st.write(f"- {icon}: {finding['check']} - {finding['message']}")

            if body.get("intent"):
                st.markdown("**Intent check (back-translation)**")
                st.write(body["intent"]["back_translated_question"])
                st.write(f"alignment: `{body['intent']['alignment_score']}`")

            if body.get("multiquery"):
                st.markdown("**Multi-query agreement**")
                st.write(f"agreement: `{body['multiquery']['agree']}`")

            st.expander("Full response").code(
                json.dumps(body, indent=2, default=str), language="json"
            )

    render_history()


main()

