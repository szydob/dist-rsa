from __future__ import annotations

import streamlit as st


def render() -> None:
    st.set_page_config(page_title="Distributed RSA", layout="wide")

    st.title("Distributed RSA System")
    st.caption("Starter interface only — no encryption/decryption logic yet.")

    st.subheader("Input")
    st.text_area("Large input text", height=220, placeholder="Paste any text here...")

    c1, c2 = st.columns(2)
    with c1:
        st.button("Encrypt (mock)", disabled=True, use_container_width=True)
    with c2:
        st.button("Decrypt (mock)", disabled=True, use_container_width=True)


def main() -> None:
    render()


if __name__ == "__main__":
    main()
