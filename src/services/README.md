# services

Service layer used by the Streamlit UI.

## Role

Services expose a stable API for application features and hide coordinator construction details.

## Files

- `encryption_service.py`: distributed text encryption API.
- `decryption_service.py`: distributed text decryption API.
- `factorization_service.py`: distributed integer factorization API.
- `attack_service.py`: RSA attack flow (factor n, recover phi and private exponent d).
- `agent_pool_service.py`: persistent pool factorization API and runtime stats access.

## Pattern

Each service validates inputs and forwards execution to a coordinator in `core`. Optional runtime overrides (for example workers or chunk size) are applied by creating temporary coordinators when needed.
