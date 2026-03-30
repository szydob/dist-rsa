from __future__ import annotations

import streamlit as st

from dist_rsa.core.models import FactorizationResult, FactorizationStatus
from dist_rsa.services.factorization_service import FactorizationService


@st.cache_resource
def get_service() -> FactorizationService:
    return FactorizationService()


def _parse_positive_int(raw: str, field: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{field} must be an integer")
    if value <= 0:
        raise ValueError(f"{field} must be positive")
    return value


def render() -> None:
    st.set_page_config(page_title="Distributed RSA", layout="wide")

    st.title("Distributed RSA System")
    st.caption("Factorization core powered by Ray; encryption/decryption to be added later.")

    with st.form("factor_form"):
        n_input = st.text_input("n (integer to factor)", value="91")
        chunk_input = st.text_input("Chunk size", value="5000")
        submitted = st.form_submit_button("Run factorization", use_container_width=True)

    if submitted:
        try:
            n_value = _parse_positive_int(n_input, "n")
            chunk_size = _parse_positive_int(chunk_input, "Chunk size")

            with st.spinner("Running factorization..."):
                service = get_service()
                result = service.factor(n_value, chunk_size=chunk_size)

            _render_result(result)
        except Exception as exc:
            st.error(f"Error: {exc}")

    st.divider()
    st.subheader("Roadmap")
    st.markdown(
        "- Encryption/decryption UI will hook into the same backend service.\n"
        "- Additional RSA features (key recovery, performance comparisons) planned.\n"
        "- This page currently focuses on the factorization pipeline only."
    )


def _render_result(result: FactorizationResult) -> None:
    if result.status is FactorizationStatus.FOUND:
        st.success(f"Factor found: p={result.p}, q={result.q}")
    else:
        st.warning(result.message or "No divisor found in the search space.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Elapsed (s)", f"{result.elapsed_seconds:.3f}")
    c2.metric("Checked chunks", str(result.checked_chunks))
    c3.metric("Checked candidates", str(result.checked_candidates))

    st.caption(f"Task id: {result.task_id} — status: {result.status.value}")


def main() -> None:
    render()


if __name__ == "__main__":
    main()
