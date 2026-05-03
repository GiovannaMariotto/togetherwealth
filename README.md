# TogetherWealth MVP

A Streamlit MVP for couples to track income, expenses, savings, investments, projections, and export Excel reports.

## Run locally

```bash
cd togetherwealth
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
streamlit run app.py
```

The SQLite database is created automatically at `database/finances.db`.

## Code Structure & Architecture

The project follows a **layered architecture** separating UI, business logic, data models, and utilities for maintainability and scalability.

### Core Layers

#### 1. **Entry Point** (`app.py`)
- **Purpose**: Streamlit application initialization and routing
- **Responsibilities**:
  - Configures the Streamlit app (page config, styling, database setup)
  - Renders the sidebar with page navigation
  - Routes between different pages (Dashboard, Add Values, Categories, Investments, Projections, Excel Export)
  - Manages partner names session state
  - Handles caching and global initialization

#### 2. **Pages/UI Layer** (`app_pages/`)
Streamlit pages that render the user interface. Each file corresponds to a feature:

- **`dashboard.py`**: Main overview page
  - Financial summary (income, expenses, savings, investments)
  - Cashflow charts
  - Partner-specific views
  - Time-period filtering

- **`add_values.py`**: Data entry page
  - Add transactions (income, expenses, savings, investments)
  - Partner assignment
  - Category selection
  - Date and amount input

- **`categories.py`**: Category management
  - Create, edit, delete spending categories
  - Manage subcategories
  - Set default categories

- **`investments.py`**: Investment tracking
  - Record investment entries
  - Track investment returns (EURIBOR-linked calculations)
  - Investment portfolio overview

- **`projections.py`**: Financial projections
  - Generate future financial scenarios
  - Savings/investment growth estimates
  - Goal tracking

- **`excel_export.py`**: Export functionality
  - Generate and download Excel reports
  - Consolidated financial summaries

#### 3. **Business Logic Layer** (`functions/`)
Core application logic separate from UI:

- **`database.py`**: Database operations
  - SQLite connection management
  - CRUD operations for transactions, categories, investments
  - Schema initialization
  - Data queries and filtering

- **`analytics.py`**: Financial calculations and analysis
  - Transaction filtering and summarization
  - Cashflow data preparation
  - Summary statistics (income, expenses, net savings)
  - Dashboard data aggregation

- **`categories.py`**: Category management logic
  - Default category definitions
  - Category validation
  - Subcategory hierarchy

- **`investments.py`**: Investment calculations
  - EURIBOR rate integration
  - Return calculations
  - Investment performance tracking

- **`projections.py`**: Financial forecasting
  - Growth projections
  - Scenario analysis
  - Savings/investment simulations

- **`euribor_service.py`**: External data service
  - Fetches EURIBOR rates from external API
  - Caches rates for performance

- **`export.py`**: Report generation
  - Excel export logic
  - Data formatting for reports
  - Multi-sheet workbook creation

- **`splits.py`**: Transaction splitting logic
  - Partner assignment calculations
  - Shared vs. individual expense handling

#### 4. **Data Models Layer** (`models/`)
Pydantic classes for type safety and data validation:

- **`transaction.py`**: Transaction data structure
  - Date, partner, type, category, amount
  - Validation rules

- **`investment.py`**: Investment record structure
  - Entry details, EURIBOR linking
  - Return tracking

- **`projection.py`**: Projection scenario model
  - Forecast parameters
  - Growth assumptions

- **`user.py`**: Partner/user profile
  - Name, income information

#### 5. **Data Persistence** (`database/`)
- **`finances.db`**: SQLite database (auto-created)
  - Transactions table
  - Categories table
  - Investments table
  - Projections table

#### 6. **Utilities & Helpers** (`utils/`)
Reusable helper functions:

- **`session.py`**: Streamlit session state management
  - Caching partner names
  - EURIBOR rate caching
  - Session-persistent data

- **`ui.py`**: UI component helpers
  - Render headers
  - Category color mapping
  - Common UI patterns

- **`charts.py`**: Chart generation utilities
  - Plotly chart builders
  - Cashflow visualization

- **`formatting.py`**: Data formatting utilities
  - Currency formatting
  - Date formatting
  - Number formatting

- **`styles.py`**: Global styling
  - CSS styling for Streamlit app
  - Visual consistency

- **`transactions.py`**: Transaction utilities
  - Transaction filtering
  - Data transformation helpers

### Data Flow

```
User Interaction (app_pages/)
        ↓
Business Logic (functions/)
        ↓
Data Models (models/)
        ↓
Database (database/finances.db)
```

**Example: Adding a transaction**
1. User enters data in `app_pages/add_values.py` (UI)
2. Data is validated against `models/transaction.py` (Validation)
3. `functions/database.py` saves to SQLite (Persistence)
4. `functions/analytics.py` recalculates summaries (Business Logic)
5. `app_pages/dashboard.py` displays updated results (UI)

### How to Locate Functionality

| What you need | Where to find it |
|---|---|
| Add new feature page | Create new file in `app_pages/` and add route to `app.py` |
| Add calculation logic | Create/update function in `functions/` |
| Add database table | Update schema in `functions/database.py` |
| Add data type/model | Create class in `models/` |
| Add UI component | Create helper in `utils/ui.py` |
| Add chart | Add function to `utils/charts.py` |
| Add styling | Update `utils/styles.py` |
| Fix a bug | Trace data flow from UI → functions → database |
| Add external API integration | Create service file in `functions/` (like `euribor_service.py`) |
