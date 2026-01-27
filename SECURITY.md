# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please email [your-email@example.com] with details about the vulnerability.

## Security Guidelines

### Data Privacy

**CRITICAL**: This application handles sensitive financial information. Follow these guidelines:

1. **Never commit personal financial data** to version control
   - All data files in `data/` are gitignored
   - Do not include real account numbers, balances, or personal identifiers
   - Use anonymized demo data for testing

2. **Local Storage Only**
   - This application stores data locally in JSON files
   - No data is transmitted to external servers
   - Keep your `data/` directory secure and backed up

3. **Environment Variables**
   - Use `.env` files for configuration (gitignored)
   - Never commit API keys, secrets, or credentials
   - Review `.gitignore` before committing changes

### Best Practices

1. **Regular Backups**: Keep regular backups of your `data/` directory
2. **File Permissions**: Ensure data files have appropriate permissions (not world-readable)
3. **Updates**: Keep dependencies updated (`pip install -r requirements.txt --upgrade`)
4. **HTTPS**: If deploying, always use HTTPS in production

### For Contributors

When contributing code:

- ✅ Use anonymized test data
- ✅ Remove any hardcoded credentials
- ✅ Review changes for sensitive information
- ✅ Test with demo data, not real financial data
- ❌ Never commit real account numbers or balances
- ❌ Never commit API keys or secrets
- ❌ Never commit personal identifiers

### Data Files to Exclude

The following patterns are gitignored and should never be committed:

- `data/*.json` - All JSON data files
- `data/*.csv` - CSV data files
- `data/bill/` - Personal data directories
- `data/onboarded/` - User-specific data
- `.env` - Environment variables
- `*.log` - Log files

## Security Features

- Rate limiting on API endpoints
- Security headers middleware
- Input validation on all forms
- XSS protection via template escaping
- CSRF protection (via FastAPI session handling)

## Known Limitations

- This is a local-first application - no built-in encryption for data files
- No authentication system (single-user by design)
- File-based storage (not suitable for multi-user deployments without modifications)

## Updates

Security updates will be released as needed. Please keep the application and dependencies up to date.
