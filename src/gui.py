from __future__ import annotations

import streamlit as st

from core.shared.models import (
    AttackResult,
    AttackStatus,
    DecryptionResult,
    DecryptionStatus,
    FactorizationResult,
    FactorizationStatus,
    EncryptionResult,
    EncryptionStatus,
)
from services.attack_service import AttackService
from services.encryption_service import EncryptionService
from services.decryption_service import DecryptionService
from services.factorization_service import FactorizationService


@st.cache_resource
def get_service() -> FactorizationService:
    return FactorizationService()


@st.cache_resource
def get_attack_service() -> AttackService:
    return AttackService()


@st.cache_resource
def get_encryption_service() -> EncryptionService:
    return EncryptionService()


@st.cache_resource
def get_decryption_service() -> DecryptionService:
    return DecryptionService()


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

    encrypt_tab, decrypt_tab, factor_tab, attack_tab = st.tabs(
        ["Encrypt text", "Decrypt text", "Factorization", "RSA attack"]
    )

    with encrypt_tab:
        service = get_encryption_service()
        recipients = service.list_recipients()
        if not recipients:
            st.error("No recipients available in key storage.")
        else:
            with st.form("encrypt_form"):
                plaintext = st.text_area("Plaintext", height=180, placeholder="Enter text to encrypt...")
                recipient_id = st.selectbox("Recipient", recipients)
                c1, c2 = st.columns(2)
                with c1:
                    workers_count = st.number_input(
                        "Workers count",
                        min_value=1,
                        max_value=64,
                        value=4,
                        step=1,
                        help="Upper limit is 64 to avoid Ray/GCS overload in Docker.",
                    )
                with c2:
                    chunk_size = st.number_input("Chunk size (bytes)", min_value=1, value=32, step=1)
                submitted = st.form_submit_button("Run encryption", use_container_width=True)

            if submitted:
                try:
                    if not plaintext.strip():
                        raise ValueError("Plaintext must not be empty")

                    with st.spinner("Running encryption..."):
                        result = service.encrypt(
                            plaintext,
                            recipient_id,
                            workers_count=int(workers_count),
                            chunk_size=int(chunk_size),
                        )

                    _render_encryption_result(result)
                except Exception as exc:
                    st.error(f"Error: {exc}")

    with decrypt_tab:
        service = get_decryption_service()
        owners = service.list_owners()
        if not owners:
            st.error("No private key owners available in key storage.")
        else:
            with st.form("decrypt_form"):
                ciphertext = st.text_area(
                    "Ciphertext numbers",
                    height=180,
                    placeholder="Paste numbers separated by spaces or commas...",
                )
                owner_id = st.selectbox("Owner", owners)
                c1, c2 = st.columns(2)
                with c1:
                    workers_count = st.number_input(
                        "Workers count",
                        min_value=1,
                        max_value=64,
                        value=4,
                        step=1,
                        help="Upper limit is 64 to avoid Ray/GCS overload in Docker.",
                    )
                with c2:
                    chunk_size = st.number_input("Chunk size", min_value=1, value=32, step=1)
                submitted = st.form_submit_button("Run decryption", use_container_width=True)

            if submitted:
                try:
                    ciphertext_numbers = [int(part) for part in ciphertext.replace(",", " ").split() if part.strip()]
                    if not ciphertext_numbers:
                        raise ValueError("Ciphertext must not be empty")

                    with st.spinner("Running decryption..."):
                        result = service.decrypt(
                            ciphertext_numbers,
                            owner_id,
                            workers_count=int(workers_count),
                            chunk_size=int(chunk_size),
                        )

                    _render_decryption_result(result)
                except Exception as exc:
                    st.error(f"Error: {exc}")

    with factor_tab:
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

    with attack_tab:
        attack_service = get_attack_service()
        with st.form("attack_form"):
            n_input = st.text_input("n (RSA modulus)", value="3233")
            e_input = st.text_input("e (public exponent)", value="65537")
            c1, c2 = st.columns(2)
            with c1:
                workers_count = st.number_input(
                    "Workers count",
                    min_value=1,
                    max_value=64,
                    value=4,
                    step=1,
                    help="Upper limit is 64 to avoid Ray/GCS overload in Docker.",
                )
            with c2:
                chunk_input = st.number_input("Chunk size", min_value=1, value=5000, step=1)
            submitted = st.form_submit_button("Run RSA attack", use_container_width=True)

        if submitted:
            try:
                n_value = _parse_positive_int(n_input, "n")
                e_value = _parse_positive_int(e_input, "e")
                if e_value >= n_value:
                    raise ValueError("e should be smaller than n")

                with st.spinner("Running RSA attack..."):
                    result = attack_service.attack(
                        n_value,
                        e_value,
                        workers_count=int(workers_count),
                        chunk_size=int(chunk_input),
                    )

                _render_attack_result(result)
            except Exception as exc:
                st.error(f"Error: {exc}")



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


def _render_attack_result(result: AttackResult) -> None:
    if result.status is AttackStatus.COMPLETED:
        st.success("RSA attack completed successfully")
    else:
        st.error(result.message or "RSA attack failed")

    c1, c2, c3 = st.columns(3)
    c1.metric("Factorization (s)", f"{result.factorization_elapsed_seconds:.3f}")
    c2.metric("Total (s)", f"{result.total_elapsed_seconds:.3f}")
    c3.metric("Status", result.status.value)

    st.caption(f"Task id: {result.task_id} — n: {result.n} — e: {result.e}")

    if result.p is not None and result.q is not None:
        st.write({"p": result.p, "q": result.q, "phi": result.phi, "d": result.d})


def _render_encryption_result(result: EncryptionResult) -> None:
    if result.status is EncryptionStatus.COMPLETED:
        st.success(f"Encrypted text for recipient {result.recipient_id}")
    else:
        st.error(result.message or "Encryption failed")

    c1, c2, c3 = st.columns(3)
    c1.metric("Elapsed (s)", f"{result.elapsed_seconds:.3f}")
    c2.metric("Chunks", str(len(result.chunks)))
    c3.metric("Workers", str(result.workers_count))

    st.caption(
        f"Task id: {result.task_id} — recipient: {result.recipient_id} — key: {result.public_key_id}"
    )

    if result.ciphertext_numbers:
        st.text_area(
            "Ciphertext numbers",
            value=" ".join(str(value) for value in result.ciphertext_numbers),
            height=140,
        )

    with st.expander("Chunk details"):
        for chunk in result.chunks:
            st.write(
                {
                    "chunk_id": chunk.chunk_id,
                    "worker_id": chunk.worker_id,
                    "byte_length": chunk.byte_length,
                    "elapsed_seconds": round(chunk.elapsed_seconds, 6),
                    "status": chunk.status.value,
                }
            )


def _render_decryption_result(result: DecryptionResult) -> None:
    if result.status is DecryptionStatus.COMPLETED:
        st.success(f"Decrypted text for owner {result.owner_id}")
    else:
        st.error(result.message or "Decryption failed")

    c1, c2, c3 = st.columns(3)
    c1.metric("Elapsed (s)", f"{result.elapsed_seconds:.3f}")
    c2.metric("Chunks", str(len(result.chunks)))
    c3.metric("Workers", str(result.workers_count))

    st.caption(
        f"Task id: {result.task_id} — owner: {result.owner_id} — key: {result.private_key_id}"
    )

    st.text_area("Plaintext", value=result.plaintext, height=180)

    with st.expander("Chunk details"):
        for chunk in result.chunks:
            st.write(
                {
                    "chunk_id": chunk.chunk_id,
                    "worker_id": chunk.worker_id,
                    "byte_length": chunk.byte_length,
                    "elapsed_seconds": round(chunk.elapsed_seconds, 6),
                    "status": chunk.status.value,
                }
            )


def main() -> None:
    render()


if __name__ == "__main__":
    main()
