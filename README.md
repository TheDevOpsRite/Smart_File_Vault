
# Smart File Vault

Smart File Vault is a lightweight, open-source desktop application to securely store and manage sensitive files and credentials locally. It provides strong encryption, user authentication, and a simple UI to protect your private data.

**Why Use Smart File Vault**
- **Privacy:** Files are encrypted locally using proven cryptographic primitives in `crypto_utils.py` before being stored.
- **Simplicity:** Friendly GUI via `vault_ui.py` for everyday users.
- **Portable:** Can be run from source (`main.py`) or packaged as a standalone executable using the included build scripts.

**Features**
- **Encrypted storage:** AES-based file encryption (see `crypto_utils.py`).
- **User authentication:** Password-based login managed in `auth.py`.
- **Graphical UI:** Manage files with `vault_ui.py`.
- **Command-line entry:** `main.py` launches the app directly.
- **Build tooling:** Build and packaging helpers: `build.bat`, `build.py`, `SmartFileVault.spec`.
- **Cross-platform packaging:** Includes PyInstaller spec and build outputs in `build/` for offline distribution.

DONWLOAD
Download here at https://github.com/TheDevOpsRite/Smart_File_Vault/releases/tag/v1.0.0

**Quick Start**
- Install dependencies: `pip install -r requirements.txt` ([requirements.txt](requirements.txt)).
- Run from source: `python main.py` ([main.py](main.py)).
- Build an executable (Windows example): run `build.bat` or follow `BUILD_GUIDE.md`.

**Upgrade Options**

Pro (one-time or subscription):
- **Cloud sync:** Optional encrypted sync to your cloud storage (end-to-end encrypted).
- **Multiple vault profiles:** Keep work and personal vaults separate.
- **Automated backups:** Scheduled, encrypted backups to a chosen folder or cloud provider.
- **Priority updates:** Faster access to new features and security fixes.

Premium (business / enterprise):
- **Team sharing:** Securely share vault items with team members using asymmetric encryption.
- **Hardware token support:** Integrate with YubiKey / FIDO2 for MFA and key storage.
- **Remote wipe & auditing:** Remote revocation and access logs for managed deployments.
- **Dedicated support & SLA:** Priority support and fast incident response for business customers.

If you'd like, I can draft pricing and feature tiers, or add UI text and placeholder screens for the upgrade flow.

**Security & Privacy Notes**
- Keys and secrets should never be committed to source control. See `.gitignore` to avoid accidental commits.
- This project is provided as-is; review cryptographic choices before using in production.

**Contributing**
- Bug reports, feature requests, and pull requests are welcome. Follow standard GitHub workflow: fork, branch, PR.

**License**
- This project is released under the MIT License. See [LICENSE](LICENSE).
