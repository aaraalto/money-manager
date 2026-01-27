# Radiant Money Manager

A personal finance management application focused on financial empowerment through better data visualization and actionable insights. Radiant helps you understand your financial situation through clear "financial lenses" and turn complex financial data into simple, understandable steps.

## Features

- **Financial Level System**: Get assigned a financial level (0-5) based on your situation
- **Debt Payoff Simulator**: Visualize debt payoff strategies (Avalanche vs Snowball)
- **Dashboard Views**: Level-specific dashboards showing relevant metrics
- **Onboarding Flow**: Step-by-step setup to capture your financial picture
- **Spending Analysis**: Track and categorize your spending

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: Vanilla JavaScript, HTMX, D3.js, TailwindCSS
- **Data Storage**: JSON files (file-based repository)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd money-manager
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your data directory:
```bash
mkdir -p data
# Copy example data files if needed
```

### Running the Application

Start the development server:
```bash
python manage.py run
```

Or use the shell script:
```bash
./manage.sh run
```

The application will be available at `http://localhost:8000`

### Development Mode

Run with auto-reload enabled:
```bash
python manage.py run --reload
```

## Project Structure

```
money-manager/
├── app/
│   ├── core/          # Core configuration and utilities
│   ├── data/          # Data repository layer
│   ├── domain/        # Business logic
│   ├── services/      # Service layer
│   ├── static/        # Frontend assets (CSS, JS)
│   ├── templates/     # Jinja2 templates
│   └── main.py        # FastAPI application entry point
├── data/              # User data files (gitignored)
├── docs/              # Documentation
├── tests/             # Test suite
└── manage.py          # Management script
```

## Testing

Run the test suite:
```bash
pytest
```

Run specific test files:
```bash
pytest tests/test_debt_simulation.py
```

## Security & Privacy

**⚠️ IMPORTANT**: This application stores financial data locally in JSON files. 

- **Never commit personal financial data** to version control
- The `data/` directory is gitignored by default
- See [SECURITY.md](SECURITY.md) for security guidelines
- Use environment variables for any sensitive configuration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license here]

## Acknowledgments

- Design system inspired by modern financial tools
- Debt payoff strategies based on Avalanche and Snowball methods
- Financial level system inspired by Ramit Sethi's "I Will Teach You To Be Rich"
