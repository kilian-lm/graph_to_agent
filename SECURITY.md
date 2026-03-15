# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in graph-to-agent, please report it responsibly:

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the details to the maintainer directly
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Any suggested fixes (optional)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: Next release

## Security Best Practices for Users

### Environment Variables

This project uses environment variables for all sensitive credentials:

```bash
# Required for OpenAI integration
OPENAI_API_KEY=sk-...

# Required for BigQuery persistence (JSON stringified)
BQ_CLIENT_SECRETS={"type":"service_account",...}

# Optional
EULA_O_K=TRUE
```

**Never commit `.env` files or credentials to version control.**

### Deployment Security

When deploying to production:

1. Use secret management (GCP Secret Manager, AWS Secrets Manager, etc.)
2. Enable HTTPS for all endpoints
3. Implement rate limiting
4. Add authentication for the web interface
5. Review CORS settings in production

### Known Limitations (Demo Version)

As noted in `eula.txt`, the demo version:
- Does not include CSRF protection
- Does not implement comprehensive input validation
- Is intended for local development/testing only

For production use, implement:
- CSRF tokens for all forms
- Input sanitization and validation
- Authentication and authorization
- Rate limiting
- Security headers (CSP, HSTS, etc.)

## Security Scanning

This repository uses:
- GitHub Dependabot for dependency updates
- Pre-commit hooks with `detect-secrets` (recommended)

To enable secret scanning locally:

```bash
pip install pre-commit detect-secrets
detect-secrets scan > .secrets.baseline
pre-commit install
```
