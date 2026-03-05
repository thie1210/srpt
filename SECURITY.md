# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Py, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report vulnerabilities by emailing:

**security@python.org** (PSF Security Team)

Or for Py-specific issues:
- Create a private security advisory on GitHub: [New Security Advisory](https://github.com/psf/py/security/advisories/new)

### What to Include

Please include:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Affected versions**
4. **Potential impact**
5. **Possible mitigation** (if known)

### Response Time

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix timeline**: Depends on severity
  - Critical: 1-3 days
  - High: 3-7 days
  - Medium: 7-14 days
  - Low: Next release

### Disclosure Policy

- We follow [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure)
- We will coordinate with you before making any public announcement
- CVE IDs will be requested for significant vulnerabilities
- Security advisories will be published via:
  - GitHub Security Advisories
  - Python package security announcement list

### Security Updates

Security updates will be released:
- As patch releases for supported versions
- Announced via GitHub Releases
- Include `[security]` in the commit message

## Security Best Practices

### For Users

1. **Keep srpt updated**: Always use the latest version
2. **Verify package sources**: Only install packages from trusted sources
3. **Check hashes**: Py verifies SHA256 hashes when available
4. **Review dependencies**: Periodically audit your dependencies

### For Contributors

1. **Never commit secrets**: No API keys, tokens, or credentials
2. **Validate inputs**: Always validate user inputs and external data
3. **Use secure defaults**: Security should be the default behavior
4. **Review dependencies**: Be cautious when adding new dependencies

## Known Security Considerations

### Dependency Downloads

Py downloads packages from PyPI (pypi.org) over HTTPS.
- Package hashes are verified when provided by PyPI
- We use certificate pinning for critical endpoints

### Code Execution

Py executes code in the following scenarios:
- Running user scripts: `srpt script.py`
- Running installed console scripts: `srpt run django-admin`
- Package setup.srpt execution (during installation)

**Mitigation**: Only install packages from trusted sources.

### Cache Security

Py stores cached data in:
- `~/.local/share/py/cache/` (SQLite databases)

**Mitigation**: Cache files have restricted permissions (user-only).

## Supported Versions

| Version | Supported | Security Updates |
|---------|-----------|------------------|
| 0.1.x   | Yes | Active |
| < 0.1   | No | None |

We will support the latest minor release with security updates.

## Security Features

### Current Features

- HTTPS-only connections to PyPI
- SHA256 hash verification for packages
- Secure launcher script (no hardcoded paths)
- Safe temporary file handling
- Input validation for package names

### Planned Features

- PGP signature verification
- Dependency vulnerability scanning
- Secure configuration profiles
- Audit logging

## Contact

For security concerns:
- **Email**: security@python.org
- **GitHub**: [Security Advisories](https://github.com/psf/py/security)

For general questions:
- **GitHub Discussions**: [py/discussions](https://github.com/psf/py/discussions)

---

Thank you for helping keep Py secure! 🔒
