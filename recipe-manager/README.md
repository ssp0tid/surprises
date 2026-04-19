# Recipe Manager

A self-hosted Flask web application for managing personal recipes, planning meals, and generating shopping lists.

## Features

- **Recipe Management** — Create, view, edit, and delete personal recipes with ingredients, instructions, and metadata
- **Ingredient Search** — Search recipes by ingredient with real-time autocomplete
- **Meal Planning** — Weekly calendar view to plan breakfast, lunch, dinner, and snacks
- **Shopping Lists** — Auto-generate shopping lists from meal plans with ingredient combining
- **Nutrition Tracking** — Per-recipe nutrition calculation and daily/weekly summaries
- **Dark Theme** — Modern dark UI with Tailwind CSS

## Tech Stack

- **Backend:** Flask 3.x (Python 3.11+)
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** Flask-Login
- **Frontend:** Jinja2 templates with Tailwind CSS (CDN)

## Quick Start

### Prerequisites

- Python 3.11 or higher

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd recipe-manager
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY and other variables
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   python run.py
   ```

### Running the Application

```bash
python run.py
```

The app will be available at `http://localhost:5000`.

## Project Structure

```
recipe-manager/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration settings
│   ├── models.py            # SQLAlchemy models
│   ├── routes/              # Route handlers
│   │   ├── auth.py          # Authentication
│   │   ├── recipes.py       # Recipe CRUD
│   │   ├── search.py        # Search
│   │   ├── meal_plan.py     # Meal planning
│   │   ├── shopping.py      # Shopping lists
│   │   └── nutrition.py     # Nutrition
│   ├── services/            # Business logic
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS/JS assets
├── migrations/              # Database migrations
├── instance/                # SQLite database
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point
└── PLAN.md                  # Implementation plan
```

## Database Models

- **User** — Account with username, email, password hash
- **Recipe** — Title, description, instructions, prep/cook time, servings, difficulty, cuisine
- **Ingredient** — Name, category, default unit, nutrition data per 100g
- **RecipeIngredient** — Many-to-many relationship with quantity and unit
- **MealPlan** — Date, meal type (breakfast/lunch/dinner/snack), recipe, servings
- **ShoppingList** — Generated lists with items and check status

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new user |
| POST | `/auth/login` | User login |
| GET | `/recipes` | List all user recipes |
| GET | `/recipes/<id>` | Get recipe detail |
| POST | `/recipes` | Create recipe |
| PUT | `/recipes/<id>` | Update recipe |
| DELETE | `/recipes/<id>` | Delete recipe |
| GET | `/search/ingredients` | Search by ingredient |
| GET | `/meal-plan` | Get meal plan (date range) |
| POST | `/meal-plan` | Add meal to plan |
| POST | `/shopping-lists` | Create from meal plan |

## Configuration

Key environment variables (`.env`):

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key for sessions |
| `FLASK_ENV` | Development mode (default: production) |
| `DATABASE_URL` | SQLite path (default: instance/recipes.db) |

## License

MIT