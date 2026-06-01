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
from services.agent_pool_service import AgentPoolService
from services.attack_service import AttackService
from services.encryption_service import EncryptionService
from services.decryption_service import DecryptionService
from services.factorization_service import FactorizationService


@st.cache_resource
def get_service() -> FactorizationService:
    """Return the cached factorization service."""
    return FactorizationService()


@st.cache_resource
def get_attack_service() -> AttackService:
    """Return the cached RSA attack service."""
    return AttackService()


@st.cache_resource
def get_encryption_service() -> EncryptionService:
    """Return the cached encryption service."""
    return EncryptionService()


@st.cache_resource
def get_decryption_service() -> DecryptionService:
    """Return the cached decryption service."""
    return DecryptionService()


@st.cache_resource
def get_agent_pool_service() -> AgentPoolService:
    """Return the cached persistent agent-pool service."""
    return AgentPoolService()


def _parse_positive_int(raw: str, field: str) -> int:
    """Parse a positive integer from a text input.

    Args:
        raw: Raw string value from the UI.
        field: Human-readable field name used in validation errors.

    Returns:
        The parsed positive integer.

    Raises:
        ValueError: If the value is not a positive integer.
    """
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{field} must be an integer")
    if value <= 0:
        raise ValueError(f"{field} must be positive")
    return value


def render() -> None:
    """Render the Streamlit application."""
    st.set_page_config(page_title="Distributed RSA", layout="wide")

    st.title("Distributed RSA System")

    # NOTE: agent pool initialization is handled outside the Streamlit render path
    # to avoid initializing Ray in a Streamlit worker thread. The pool can be
    # started at container startup (recommended) or lazily when the user opens
    # the Agent Pool tab.

    encrypt_tab, decrypt_tab, factor_tab, attack_tab, agent_pool_tab = st.tabs(
        ["Encrypt text", "Decrypt text", "Factorization", "RSA attack", "Agent Pool Attack"]
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

    with agent_pool_tab:
        st.markdown("### Agent Pool Attack")
        st.info(
            "Factorization runs on a persistent Ray agent pool. Metrics and task history are available in Grafana: http://localhost:3000 (admin/admin)"
        )

        service = get_agent_pool_service()

        from concurrent.futures import ThreadPoolExecutor

        if "agent_pool_executor" not in st.session_state:
            st.session_state["agent_pool_executor"] = ThreadPoolExecutor(max_workers=1)

        with st.form("agent_pool_attack_form"):
            st.write("**Huge Number to Factorize (background):**")
            c1, c2 = st.columns(2)
            with c1:
                n_input = st.text_input(
                    "n (use presets or enter custom)",
                    value="10000000000000037",
                    help="Demo size is intentionally huge; adjust if you want a shorter run.",
                )
            with c2:
                chunk_size_input = st.number_input("Chunk size", min_value=1, value=1000, step=1000)

            submitted = st.form_submit_button("Start Pool Attack (background)")

        if submitted:
            try:
                # read values directly from the form inputs
                n_value = _parse_positive_int(n_input, "n")
                chunk_size_value = _parse_positive_int(chunk_size_input, "Chunk size")
                executor = st.session_state["agent_pool_executor"]
                future = executor.submit(service.factor, n_value, chunk_size=chunk_size_value)
                st.session_state["agent_pool_future"] = future
                st.session_state["agent_pool_meta"] = {"n": n_value, "chunk_size": chunk_size_value}
                st.session_state.pop("agent_pool_result", None)
                st.success("Background factorization started.")
            except Exception as exc:
                st.error(f"Error: {exc}")

        st.markdown("---")
        _poll_agent_pool_result(service)

        # Preset example numbers for easy copying/use
        st.markdown("### Example numbers (click to load into input)")
        presets = [
            "91",
            "3233",
            "100000000000000003",
            "100000000000000037",
            "9999999967",
        ]
        cols = st.columns(len(presets))
        for col, val in zip(cols, presets):
            if col.button(val, key=f"preset_{val}"):
                # store selected preset in a separate session key (not the widget key)
                st.session_state["agent_pool_preset_selected"] = val
        # show the selected preset for easy copy/paste
        if st.session_state.get("agent_pool_preset_selected"):
            st.markdown("**Selected preset (copy to input):**")
            st.code(st.session_state.get("agent_pool_preset_selected"))

        # Small debug view to help validate per-agent utilization values
        with st.expander("Agent pool debug / utilization (raw)"):
            try:
                agent_details = service.get_agent_details()
                for a in agent_details:
                    st.write(
                        {
                            "agent_id": a["agent_id"],
                            "efficiency": a["efficiency_level"],
                            "total_jobs": a["total_jobs_completed"],
                            "%util": a["utilization_percent"],
                            "is_busy": a["is_busy"],
                            "pending": a["pending_tasks"],
                        }
                    )
            except Exception as exc:
                st.write(f"Could not fetch agent details: {exc}")


def _render_agent_pool_result(result: FactorizationResult, service: AgentPoolService) -> None:
    """Render the agent-pool factorization result and current pool stats.

    Args:
        result: Factorization result produced by the pool.
        service: Agent-pool service used to query live stats.
    """
    if result.status is FactorizationStatus.FOUND:
        st.success(f"Factor found: p={result.p}, q={result.q}")
    else:
        st.warning(result.message or "No divisor found in search space")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Elapsed (s)", f"{result.elapsed_seconds:.3f}")
    c2.metric("Checked Chunks", str(result.checked_chunks))
    c3.metric("Candidates Checked", str(result.checked_candidates))
    c4.metric("Avg Speed", f"{result.checked_candidates / max(result.elapsed_seconds, 0.001):.0f} candidates/s")

    # Pool stats after run
    pool_stats_after = service.get_pool_stats()
    st.write("**Pool Stats After Attack:**")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs Completed (Pool)", pool_stats_after["total_jobs_completed"])
    col2.metric(
        "Peak Pool Utilization",
        f"{result.peak_pool_utilization_percent or 0.0:.1f}%",
    )
    col3.metric("Idle Agents Now", pool_stats_after["idle_agents"])

    st.caption(f"Task id: {result.task_id}")


@st.fragment(run_every="1s")
def _poll_agent_pool_result(service: AgentPoolService) -> None:
    """Poll the background Agent Pool task and render it when complete."""
    future = st.session_state.get("agent_pool_future")
    result = st.session_state.get("agent_pool_result")

    if result is not None:
        _render_agent_pool_result(result, service)
        return

    if future is None:
        return

    try:
        done = future.done()
    except Exception:
        done = False

    if not done:
        return

    try:
        result = future.result()
        st.session_state["agent_pool_result"] = result
        _render_agent_pool_result(result, service)
    finally:
        st.session_state.pop("agent_pool_future", None)
        st.session_state.pop("agent_pool_meta", None)

def _render_result(result: FactorizationResult) -> None:
    """Render the standard factorization result."""
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
    """Render the RSA attack result."""
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
    """Render the distributed encryption result."""
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
    """Render the distributed decryption result."""
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
    """Application entry point."""
    render()


if __name__ == "__main__":
    main()
