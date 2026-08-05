"""Gera segredos aleatorios para o .env.

    python -m app.scripts.gen_secrets

Nao escreve no .env automaticamente: imprime para o operador colar. Sobrescrever
um .env existente derrubaria tokens em uso sem aviso.
"""

from __future__ import annotations

import secrets


def main() -> int:
    print("# Cole em backend/.env (e a INTERNAL_API_KEY tambem em frontend/.env)")
    print(f"JWT_SECRET={secrets.token_urlsafe(48)}")
    print(f"API_CLIENT_ID=cliente-planta-{secrets.token_hex(4)}")
    print(f"API_CLIENT_SECRET={secrets.token_urlsafe(32)}")
    print(f"INTERNAL_API_KEY={secrets.token_urlsafe(32)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
