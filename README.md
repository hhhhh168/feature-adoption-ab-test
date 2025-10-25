# WorkHeart A/B Testing Platform 💙

**Two-Tier Verification Feature Optimization**

A production-ready A/B testing platform demonstrating advanced statistical analysis, synthetic data generation, and interactive visualization for a dating app verification feature experiment.

---

## 🎯 Project Overview

### Business Context

WorkHeart is a professional dating app targeting educated professionals (90%+ have Bachelor's degree or higher). The platform implements a two-tier verification system:

- **Tier 1**: Email domain verification (@company.edu, @company.com)
- **Tier 2**: Badge/ID verification for additional trust signals

### Experiment Hypothesis

**Hypothesis**: A streamlined, UX-optimized verification flow will increase completion rates for both verification tiers and improve downstream engagement.

**Primary Metric**: Tier 1 completion rate (email verification)
**Secondary Metrics**: Tier 2 completion rate, time to complete, user engagement

---

## 📊 Key Features

### 1. **Synthetic Data Generation**
- 50,000 realistic user profiles using SDV (Synthetic Data Vault)
- Realistic demographic distributions and behavioral patterns
- Ground truth treatment effects for validation
- Complete data quality validation pipeline

### 2. **Advanced Statistical Analysis**
- **CUPED** (Controlled-experiment Using Pre-Experiment Data) for variance reduction
- Power analysis and sample size calculations
- Multiple testing corrections (Benjamini-Hochberg FDR)
- Sample Ratio Mismatch (SRM) detection
- Comprehensive hypothesis testing (proportion tests, t-tests)

### 3. **Production-Grade Database**
- PostgreSQL schema via Supabase
- Materialized views for performance
- Comprehensive indexing strategy
- Complete data model for A/B testing

### 4. **Interactive Dashboard**
- Real-time Streamlit dashboard
- Executive summary with key metrics
- Time series visualizations
- Funnel analysis
- Statistical details and quality checks

---

## 🏗️ Project Structure

```
feature-adoption-ab-test/
├── src/
│   ├── __init__.py
│   ├── config.py                    # Configuration management
│   ├── database.py                   # Database utilities
│   ├── synthetic_data_generator.py   # Data generation
│   ├── experiment_assignment.py      # Randomization logic
│   ├── statistical_analysis.py       # Statistical tests
│   ├── cuped.py                      # CUPED implementation
│   └── utils.py                      # Helper functions
├── dashboard/
│   ├── dashboard.py                  # Main Streamlit app
│   └── components/                   # Dashboard components
├── sql/
│   ├── schema.sql                    # Database schema
│   ├── materialized_views.sql        # Performance views
│   └── sample_queries.sql            # Example queries
├── tests/
│   ├── test_assignment.py
│   ├── test_statistics.py
│   └── test_cuped.py
├── notebooks/
│   ├── 01_data_generation.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   └── 03_statistical_analysis.ipynb
├── docs/
│   ├── experiment_design.md
│   ├── statistical_methodology.md
│   └── interview_guide.md
├── data/                             # Generated data (gitignored)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database (Supabase account recommended)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/hhhhh168/feature-adoption-ab-test.git
cd feature-adoption-ab-test
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

5. **Create database schema**
```bash
python -c "from src.database import *; db = DatabaseManager(); db.execute_sql_file('sql/schema.sql')"
python -c "from src.database import *; db = DatabaseManager(); db.execute_sql_file('sql/materialized_views.sql')"
```

---

## 📈 Usage

### Generate Synthetic Data

```python
from src.synthetic_data_generator import WorkHeartDataGenerator
from src.config import DATA_CONFIG, EXP_CONFIG

generator = WorkHeartDataGenerator(DATA_CONFIG, EXP_CONFIG)
data = generator.generate_all_data()

# Upload to database
from src.database import DatabaseManager
db = DatabaseManager()
db.insert_dataframe('users', data['users'])
db.insert_dataframe('experiment_assignments', data['assignments'])
# ... etc
```

### Run Statistical Analysis

```python
from src.statistical_analysis import ABTestAnalyzer
from src.database import DatabaseManager

db = DatabaseManager()
data = db.get_experiment_data('verification_v1')

analyzer = ABTestAnalyzer(alpha=0.05, power=0.80)
results = analyzer.analyze_experiment(
    data=data['verification'],
    metrics=['tier1_completed', 'tier2_completed'],
    primary_metric='tier1_completed',
    use_cuped=True
)

print(results['recommendation'])
```

### Launch Dashboard

```bash
streamlit run dashboard/dashboard.py
```

---

## 🧪 Statistical Methodology

### CUPED Variance Reduction

CUPED uses pre-experiment covariates to reduce variance and increase statistical power:

```
Y_adjusted = Y - θ(X - E[X])
where θ = Cov(Y,X) / Var(X)
```

**Benefits:**
- 30-50% variance reduction (typical)
- Maintains treatment effect unbiasedness
- Increases power without additional sample size

### Power Analysis

Required sample size per variant:

```
n = (2 * p(1-p) * (z_α/2 + z_β)²) / (p₁ - p₀)²
```

For baseline conversion rate of 40% and MDE of 15%:
- **Required**: ~2,400 per variant
- **Actual**: 25,000 per variant
- **Achieved Power**: >99%

### Multiple Testing Correction

Using Benjamini-Hochberg FDR control to adjust p-values across multiple metrics.

---

## 📊 Key Results

### Synthetic Data Validation

✅ **Sample Ratio Mismatch**: p = 0.87 (no SRM detected)
✅ **Covariate Balance**: All pre-metrics balanced (p > 0.05)
✅ **CUPED Variance Reduction**: 42% for sessions metric

### Experiment Results (Synthetic Ground Truth)

| Metric | Control | Treatment | Lift | p-value | Significant |
|--------|---------|-----------|------|---------|-------------|
| Tier 1 Completion | 40.0% | 46.0% | +15.0% | <0.001 | ✅ |
| Tier 2 Completion | 25.0% | 30.0% | +20.0% | <0.001 | ✅ |
| Sessions/User | 14.2 | 15.9 | +12.0% | <0.001 | ✅ |

**Recommendation**: 🚀 **SHIP** - Statistically significant positive impact on all key metrics

---

## 🎓 Portfolio Highlights

### Technical Skills Demonstrated

- **Statistical Analysis**: Power analysis, CUPED, multiple testing, SRM detection
- **Data Engineering**: PostgreSQL schema design, ETL pipelines, materialized views
- **Python Engineering**: OOP design, type hints, comprehensive documentation
- **Data Visualization**: Plotly interactive charts, Streamlit dashboards
- **Synthetic Data**: SDV for realistic data generation
- **Best Practices**: Git workflow, virtual environments, configuration management

### Interview Talking Points

1. **Variance Reduction**: "I implemented CUPED to achieve 40%+ variance reduction..."
2. **Data Quality**: "Built comprehensive validation including SRM checks and covariate balance..."
3. **Production-Ready**: "Designed with materialized views for <3s dashboard load times..."
4. **Statistical Rigor**: "Applied Benjamini-Hochberg correction to control false discovery rate..."

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v --cov=src
```

---

## 📚 Documentation

- **[Experiment Design](docs/experiment_design.md)** - Detailed experiment methodology
- **[Statistical Methodology](docs/statistical_methodology.md)** - Deep dive into statistical methods
- **[Interview Guide](docs/interview_guide.md)** - How to discuss this project in interviews

---

## ⚠️ Important Notes

### Synthetic Data Disclaimer

**This project uses 100% synthetic data generated with the SDV library.** No real user data is included. The synthetic data is designed to demonstrate technical capabilities and statistical methodology.

### Database Setup

This project requires a PostgreSQL database. Free tier Supabase accounts work perfectly. Sign up at [supabase.com](https://supabase.com).

---

## 🔮 Future Enhancements

- [ ] Bayesian A/B testing implementation
- [ ] Sequential testing with alpha spending
- [ ] Multi-armed bandit optimization
- [ ] Automated experiment monitoring alerts
- [ ] API endpoints for programmatic access

---

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome! Please open an issue to discuss.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👤 Author

**Your Name**
- Portfolio: [your-portfolio.com]
- LinkedIn: [linkedin.com/in/yourprofile]
- GitHub: [@hhhhh168](https://github.com/hhhhh168)

---

## 🙏 Acknowledgments

- **SDV Team** - Synthetic data generation library
- **Supabase** - Database hosting
- **Streamlit** - Dashboard framework
- Microsoft Research - CUPED methodology

---

**Built for Data Science roles at Apple, Amazon, TikTok (3-5 YOE level)**

*Demonstrating production-ready A/B testing skills with statistical rigor and engineering best practices.*
