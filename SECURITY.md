## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of CodePilot seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

1. Email us at security@codepilot.dev
2. Include a description of the vulnerability
3. Steps to reproduce the issue
4. Potential impact assessment
5. Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 5 business days
- **Resolution**: Dependent on severity

### Severity Levels

| Level    | Description                                    | Response Time |
| -------- | ---------------------------------------------- | ------------- |
| Critical | Remote code execution, data breach             | 24 hours      |
| High     | Authentication bypass, privilege escalation    | 48 hours      |
| Medium   | XSS, CSRF, information disclosure              | 5 days        |
| Low      | Minor information leakage, best practice       | 10 days       |

## Security Best Practices

- Always use environment variables for secrets
- Never commit `.env` files
- Keep dependencies updated
- Use strong, unique passwords
- Enable HTTPS in production
