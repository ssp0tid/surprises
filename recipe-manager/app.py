"""
Recipe Manager Flask Application
A personal recipe management system with meal planning and shopping lists.
"""

import os
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ============================================================
# CONFIGURATION
# ============================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///recipes.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ============================================================
# MODELS
# ============================================================

class User(UserMixin, db.Model):
    """User account model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recipes = db.relationship('Recipe', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    meal_plans = db.relationship('MealPlan', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    shopping_lists = db.relationship('ShoppingList', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Ingredient(db.Model):
    """Ingredient master list"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50))  # produce, dairy, meat, pantry, frozen, etc.
    default_unit = db.Column(db.String(20))
    # Nutrition per 100g: {calories, protein, carbs, fat, fiber}
    nutrition_json = db.Column(db.Text, default='{}')
    
    # Relationships
    recipe_ingredients = db.relationship('RecipeIngredient', backref='ingredient', lazy='dynamic')
    
    @property
    def nutrition(self):
        import json
        return json.loads(self.nutrition_json) if self.nutrition_json else {}
    
    @nutrition.setter
    def nutrition(self, value):
        import json
        self.nutrition_json = json.dumps(value)
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'


class Recipe(db.Model):
    """Recipe model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer)  # minutes
    cook_time = db.Column(db.Integer)  # minutes
    servings = db.Column(db.Integer, default=4)
    difficulty = db.Column(db.String(20), default='easy')  # easy, medium, hard
    cuisine = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Relationships
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    meal_plans = db.relationship('MealPlan', backref='recipe', lazy='dynamic')
    
    def total_time(self):
        return (self.prep_time or 0) + (self.cook_time or 0)
    
    def __repr__(self):
        return f'<Recipe {self.title}>'


class RecipeIngredient(db.Model):
    """Many-to-many relationship between Recipe and Ingredient"""
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False, index=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String(100))  # e.g., "diced", "room temp"
    
    def __repr__(self):
        return f'<RecipeIngredient {self.recipe_id}: {self.ingredient.name if self.ingredient else "?"}>'


class MealPlan(db.Model):
    """Meal plan entries"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, snack
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    servings = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<MealPlan {self.date}: {self.meal_type}>'


class ShoppingList(db.Model):
    """Shopping list"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('ShoppingListItem', backref='shopping_list', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ShoppingList {self.name}>'


class ShoppingListItem(db.Model):
    """Shopping list item"""
    id = db.Column(db.Integer, primary_key=True)
    shopping_list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'), nullable=False, index=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=True)
    ingredient_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(20))
    checked = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))
    
    # Relationship
    ingredient = db.relationship('Ingredient', backref='shopping_list_items')
    
    def __repr__(self):
        return f'<ShoppingListItem {self.ingredient_name}>'


# ============================================================
# LOGIN MANAGER
# ============================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


# ============================================================
# CONTEXT PROCESSORS
# ============================================================

@app.context_processor
def inject_user():
    return dict(current_user=current_user)


# ============================================================
# DECORATORS
# ============================================================

def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# ROUTES - AUTH
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if len(username) < 3:
            errors.append('Username must be at least 3 characters')
        if len(username) > 80:
            errors.append('Username must be less than 80 characters')
        if not email or '@' not in email:
            errors.append('Valid email is required')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check duplicates
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ============================================================
# ROUTES - RECIPES
# ============================================================

@app.route('/')
def index():
    """Home page with recent recipes"""
    if current_user.is_authenticated:
        recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(
            Recipe.created_at.desc()
        ).limit(6).all()
        meal_plan_today = MealPlan.query.filter_by(
            user_id=current_user.id, 
            date=datetime.now().date()
        ).all()
    else:
        recipes = []
        meal_plan_today = []
    
    return render_template('index.html', 
                         recipes=recipes, 
                         meal_plan_today=meal_plan_today)


@app.route('/recipes')
@login_required
def recipes():
    """List all user recipes"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search = request.args.get('search', '').strip()
    difficulty = request.args.get('difficulty', '')
    cuisine = request.args.get('cuisine', '')
    
    query = Recipe.query.filter_by(user_id=current_user.id)
    
    if search:
        query = query.filter(
            db.or_(
                Recipe.title.ilike(f'%{search}%'),
                Recipe.description.ilike(f'%{search}%')
            )
        )
    
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    if cuisine:
        query = query.filter_by(cuisine=cuisine)
    
    recipes_pagination = query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('recipes.html',
                        recipes=recipes_pagination.items,
                        pagination=recipes_pagination,
                        search=search,
                        difficulty=difficulty,
                        cuisine=cuisine)


@app.route('/recipes/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    """Create new recipe"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        instructions = request.form.get('instructions', '').strip()
        prep_time = request.form.get('prep_time', type=int) or 0
        cook_time = request.form.get('cook_time', type=int) or 0
        servings = request.form.get('servings', type=int) or 4
        difficulty = request.form.get('difficulty', 'easy')
        cuisine = request.form.get('cuisine', '').strip()
        image_url = request.form.get('image_url', '').strip()
        
        # Validation
        errors = []
        if not title:
            errors.append('Title is required')
        if len(title) > 200:
            errors.append('Title must be less than 200 characters')
        if not instructions:
            errors.append('Instructions are required')
        if len(instructions) > 10000:
            errors.append('Instructions too long')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('new_recipe.html')
        
        # Create recipe
        recipe = Recipe(
            title=title,
            description=description,
            instructions=instructions,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=servings,
            difficulty=difficulty,
            cuisine=cuisine,
            image_url=image_url,
            user_id=current_user.id
        )
        db.session.add(recipe)
        db.session.commit()
        
        # Process ingredients
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_quantities = request.form.getlist('ingredient_quantity[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')
        ingredient_notes = request.form.getlist('ingredient_notes[]')
        
        for i, name in enumerate(ingredient_names):
            if not name.strip():
                continue
            
            name = name.strip()
            quantity = float(ingredient_quantities[i]) if ingredient_quantities[i] else 1
            unit = ingredient_units[i] if ingredient_units[i] else 'unit'
            note = ingredient_notes[i].strip() if i < len(ingredient_notes) else ''
            
            # Find or create ingredient
            ingredient = Ingredient.query.filter_by(name=name).first()
            if not ingredient:
                ingredient = Ingredient(name=name, default_unit=unit)
                db.session.add(ingredient)
                db.session.flush()
            
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=quantity,
                unit=unit,
                notes=note
            )
            db.session.add(recipe_ingredient)
        
        db.session.commit()
        flash('Recipe created successfully!', 'success')
        return redirect(url_for('recipe', recipe_id=recipe.id))
    
    return render_template('new_recipe.html')


@app.route('/recipes/<int:recipe_id>')
@login_required
def recipe(recipe_id):
    """View recipe detail"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != current_user.id:
        abort(403)
    
    return render_template('recipe.html', recipe=recipe)


@app.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    """Edit recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        instructions = request.form.get('instructions', '').strip()
        prep_time = request.form.get('prep_time', type=int) or 0
        cook_time = request.form.get('cook_time', type=int) or 0
        servings = request.form.get('servings', type=int) or 4
        difficulty = request.form.get('difficulty', 'easy')
        cuisine = request.form.get('cuisine', '').strip()
        image_url = request.form.get('image_url', '').strip()
        
        # Validation
        errors = []
        if not title:
            errors.append('Title is required')
        if not instructions:
            errors.append('Instructions are required')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('edit_recipe.html', recipe=recipe)
        
        # Update recipe
        recipe.title = title
        recipe.description = description
        recipe.instructions = instructions
        recipe.prep_time = prep_time
        recipe.cook_time = cook_time
        recipe.servings = servings
        recipe.difficulty = difficulty
        recipe.cuisine = cuisine
        recipe.image_url = image_url
        
        # Delete existing ingredients and recreate
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        
        # Process new ingredients
        ingredient_names = request.form.getlist('ingredient_name[]')
        ingredient_quantities = request.form.getlist('ingredient_quantity[]')
        ingredient_units = request.form.getlist('ingredient_unit[]')
        ingredient_notes = request.form.getlist('ingredient_notes[]')
        
        for i, name in enumerate(ingredient_names):
            if not name.strip():
                continue
            
            name = name.strip()
            quantity = float(ingredient_quantities[i]) if ingredient_quantities[i] else 1
            unit = ingredient_units[i] if ingredient_units[i] else 'unit'
            note = ingredient_notes[i].strip() if i < len(ingredient_notes) else ''
            
            # Find or create ingredient
            ingredient = Ingredient.query.filter_by(name=name).first()
            if not ingredient:
                ingredient = Ingredient(name=name, default_unit=unit)
                db.session.add(ingredient)
                db.session.flush()
            
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=quantity,
                unit=unit,
                notes=note
            )
            db.session.add(recipe_ingredient)
        
        db.session.commit()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('recipe', recipe_id=recipe.id))
    
    return render_template('edit_recipe.html', recipe=recipe)


@app.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    """Delete recipe"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != current_user.id:
        abort(403)
    
    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe deleted!', 'success')
    return redirect(url_for('recipes'))


# ============================================================
# ROUTES - SEARCH
# ============================================================

@app.route('/search')
@login_required
def search():
    """Search recipes"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if not query:
        return render_template('search.html', results=[], query='')
    
    query = query[:100]  # Limit query length
    
    recipes = []
    ingredients = []
    
    if search_type in ('all', 'recipes'):
        recipes = Recipe.query.filter(
            Recipe.user_id == current_user.id,
            db.or_(
                Recipe.title.ilike(f'%{query}%'),
                Recipe.description.ilike(f'%{query}%')
            )
        ).limit(20).all()
    
    if search_type in ('all', 'ingredients'):
        ingredients = Ingredient.query.filter(
            Ingredient.name.ilike(f'%{query}%')
        ).limit(20).all()
    
    return render_template('search.html',
                         recipes=recipes,
                         ingredients=ingredients,
                         query=query,
                         search_type=search_type)


@app.route('/api/ingredients')
@login_required
def api_ingredients():
    """API endpoint for ingredient autocomplete"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    ingredients = Ingredient.query.filter(
        Ingredient.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    return jsonify([
        {
            'id': ing.id,
            'name': ing.name,
            'category': ing.category,
            'unit': ing.default_unit
        }
        for ing in ingredients
    ])


@app.route('/search/ingredients')
@login_required
def search_ingredients():
    """Search recipes by ingredient"""
    ingredient_name = request.args.get('ingredient', '').strip()
    
    if not ingredient_name:
        return render_template('search_ingredients.html', results=[], ingredient='')
    
    ingredient = Ingredient.query.filter(
        Ingredient.name.ilike(f'%{ingredient_name}%')
    ).first()
    
    if not ingredient:
        return render_template('search_ingredients.html',
                             results=[],
                             ingredient=ingredient_name,
                             message='No ingredient found')
    
    recipe_ingredients = RecipeIngredient.query.filter_by(
        ingredient_id=ingredient.id
    ).all()
    
    recipes = []
    for ri in recipe_ingredients:
        if ri.recipe.user_id == current_user.id:
            recipes.append(ri.recipe)
    
    return render_template('search_ingredients.html',
                         results=recipes,
                         ingredient=ingredient.name)


# ============================================================
# ROUTES - MEAL PLANNING
# ============================================================

@app.route('/meal-plan')
@login_required
def meal_plan():
    """Meal plan view"""
    start_date = request.args.get('date')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = datetime.now().date()
    else:
        start_date = datetime.now().date()
    
    # Get week dates (Monday to Sunday)
    week_dates = []
    monday = start_date - timedelta(days=start_date.weekday())
    for i in range(7):
        week_dates.append(monday + timedelta(days=i))
    
    # Get meal plans for the week
    meal_plans = MealPlan.query.filter(
        MealPlan.user_id == current_user.id,
        MealPlan.date >= monday,
        MealPlan.date <= monday + timedelta(days=6)
    ).all()
    
    # Organize by date and meal type
    meal_plan_map = {}
    for mp in meal_plans:
        key = (mp.date, mp.meal_type)
        meal_plan_map[key] = mp
    
    return render_template('mealplan.html',
                         week_dates=week_dates,
                         meal_plan_map=meal_plan_map,
                         start_date=start_date)


@app.route('/meal-plan/add', methods=['POST'])
@login_required
def add_meal_plan():
    """Add meal to plan"""
    recipe_id = request.form.get('recipe_id', type=int)
    date_str = request.form.get('date')
    meal_type = request.form.get('meal_type')
    servings = request.form.get('servings', type=int) or 1
    
    # Validation
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        abort(403)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Invalid date', 'error')
        return redirect(url_for('meal_plan'))
    
    if meal_type not in ('breakfast', 'lunch', 'dinner', 'snack'):
        flash('Invalid meal type', 'error')
        return redirect(url_for('meal_plan'))
    
    # Check if there's already a meal for this slot
    existing = MealPlan.query.filter_by(
        user_id=current_user.id,
        date=date,
        meal_type=meal_type
    ).first()
    
    if existing:
        existing.recipe_id = recipe_id
        existing.servings = servings
        flash('Meal updated!', 'success')
    else:
        meal_plan = MealPlan(
            user_id=current_user.id,
            date=date,
            meal_type=meal_type,
            recipe_id=recipe_id,
            servings=servings
        )
        db.session.add(meal_plan)
        flash('Meal added to plan!', 'success')
    
    db.session.commit()
    return redirect(url_for('meal_plan', date=date_str))


@app.route('/meal-plan/<int:meal_plan_id>/delete', methods=['POST'])
@login_required
def delete_meal_plan(meal_plan_id):
    """Remove meal from plan"""
    meal_plan = MealPlan.query.get_or_404(meal_plan_id)
    
    if meal_plan.user_id != current_user.id:
        abort(403)
    
    date_str = meal_plan.date.isoformat()
    db.session.delete(meal_plan)
    db.session.commit()
    flash('Meal removed from plan!', 'success')
    return redirect(url_for('meal_plan', date=date_str))


# ============================================================
# ROUTES - SHOPPING LISTS
# ============================================================

@app.route('/shopping-lists')
@login_required
def shopping_lists():
    """List shopping lists"""
    shopping_lists = ShoppingList.query.filter_by(
        user_id=current_user.id
    ).order_by(ShoppingList.created_at.desc()).all()
    
    return render_template('shopping.html', shopping_lists=shopping_lists)


@app.route('/shopping-lists/new', methods=['POST'])
@login_required
def new_shopping_list():
    """Create shopping list from meal plan"""
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    name = request.form.get('name', '').strip() or 'Shopping List'
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Invalid date range', 'error')
        return redirect(url_for('meal_plan'))
    
    # Get meal plans for date range
    meal_plans = MealPlan.query.filter(
        MealPlan.user_id == current_user.id,
        MealPlan.date >= start_date,
        MealPlan.date <= end_date
    ).all()
    
    if not meal_plans:
        flash('No meals planned for this date range', 'warning')
        return redirect(url_for('meal_plan'))
    
    # Aggregate ingredients
    ingredient_totals = {}  # (ingredient_id, unit) -> quantity
    
    for mp in meal_plans:
        if not mp.recipe:
            continue
        
        multiplier = mp.servings / mp.recipe.servings if mp.recipe.servings else 1
        
        for ri in mp.recipe.ingredients:
            key = (ri.ingredient_id, ri.unit)
            if key in ingredient_totals:
                ingredient_totals[key] += ri.quantity * multiplier
            else:
                ingredient_totals[key] = ri.quantity * multiplier
    
    if not ingredient_totals:
        flash('No ingredients found in planned meals', 'warning')
        return redirect(url_for('meal_plan'))
    
    # Create shopping list
    shopping_list = ShoppingList(
        user_id=current_user.id,
        name=name
    )
    db.session.add(shopping_list)
    db.session.flush()
    
    # Create items
    for (ingredient_id, unit), quantity in ingredient_totals.items():
        ingredient = Ingredient.query.get(ingredient_id)
        
        item = ShoppingListItem(
            shopping_list_id=shopping_list.id,
            ingredient_id=ingredient_id,
            ingredient_name=ingredient.name if ingredient else 'Unknown',
            quantity=round(quantity, 2),
            unit=unit,
            category=ingredient.category if ingredient else None
        )
        db.session.add(item)
    
    db.session.commit()
    flash('Shopping list created!', 'success')
    return redirect(url_for('view_shopping_list', list_id=shopping_list.id))


@app.route('/shopping-lists/<int:list_id>')
@login_required
def view_shopping_list(list_id):
    """View shopping list"""
    shopping_list = ShoppingList.query.get_or_404(list_id)
    
    if shopping_list.user_id != current_user.id:
        abort(403)
    
    # Group items by category
    items = shopping_list.items.all()
    grouped_items = {}
    for item in items:
        category = item.category or 'Other'
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item)
    
    return render_template('shopping_list.html',
                         shopping_list=shopping_list,
                         grouped_items=grouped_items)


@app.route('/shopping-lists/<int:list_id>/toggle', methods=['POST'])
@login_required
def toggle_shopping_item(list_id):
    """Toggle item checked status"""
    item_id = request.form.get('item_id', type=int)
    item = ShoppingListItem.query.get_or_404(item_id)
    
    if item.shopping_list.user_id != current_user.id:
        abort(403)
    
    item.checked = not item.checked
    db.session.commit()
    
    return jsonify({'checked': item.checked})


@app.route('/shopping-lists/<int:list_id>/delete', methods=['POST'])
@login_required
def delete_shopping_list(list_id):
    """Delete shopping list"""
    shopping_list = ShoppingList.query.get_or_404(list_id)
    
    if shopping_list.user_id != current_user.id:
        abort(403)
    
    db.session.delete(shopping_list)
    db.session.commit()
    flash('Shopping list deleted!', 'success')
    return redirect(url_for('shopping_lists'))


# ============================================================
# ROUTES - NUTRITION
# ============================================================

@app.route('/nutrition')
@login_required
def nutrition():
    """Nutrition dashboard"""
    # Get date range (last 7 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    # Get meal plans for the week
    meal_plans = MealPlan.query.filter(
        MealPlan.user_id == current_user.id,
        MealPlan.date >= start_date,
        MealPlan.date <= end_date
    ).all()
    
    # Calculate nutrition totals
    totals = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0,
        'fiber': 0
    }
    
    daily_totals = {}
    for i in range(7):
        date = start_date + timedelta(days=i)
        daily_totals[date] = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
    
    for mp in meal_plans:
        if not mp.recipe:
            continue
        
        multiplier = mp.servings / mp.recipe.servings if mp.recipe.servings else 1
        
        recipe_nutrition = calculate_recipe_nutrition(mp.recipe)
        
        for key in totals:
            value = recipe_nutrition.get(key, 0) * multiplier
            totals[key] += value
            daily_totals[mp.date][key] += value
    
    return render_template('nutrition.html',
                         totals=totals,
                         daily_totals=daily_totals,
                         start_date=start_date,
                         end_date=end_date)


@app.route('/nutrition/recipe/<int:recipe_id>')
@login_required
def recipe_nutrition(recipe_id):
    """Get recipe nutrition breakdown"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != current_user.id:
        abort(403)
    
    nutrition = calculate_recipe_nutrition(recipe)
    ingredients = recipe.ingredients.all()
    
    return render_template('recipe_nutrition.html',
                         recipe=recipe,
                         nutrition=nutrition,
                         ingredients=ingredients)


def calculate_recipe_nutrition(recipe):
    """Calculate nutrition for a recipe"""
    import json
    
    totals = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0,
        'fiber': 0
    }
    
    if not recipe.ingredients:
        return totals
    
    for ri in recipe.ingredients:
        if not ri.ingredient:
            continue
        
        nutrition = ri.ingredient.nutrition
        if not nutrition:
            continue
        
        # Assume quantity is in grams for simplicity
        # (in a real app, would need unit conversion)
        multiplier = ri.quantity / 100
        
        for key in totals:
            totals[key] += (nutrition.get(key, 0) or 0) * multiplier
    
    # Adjust for servings
    if recipe.servings and recipe.servings > 0:
        for key in totals:
            totals[key] = round(totals[key] / recipe.servings, 1)
    
    return totals


# ============================================================
# DATABASE CREATION
# ============================================================

def seed_ingredients():
    """Seed initial ingredients with nutrition data"""
    ingredients_data = [
        # Name, Category, Unit, Nutrition per 100g
        ('Chicken Breast', 'meat', 'g', {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0}),
        ('Brown Rice', 'pantry', 'g', {'calories': 111, 'protein': 2.6, 'carbs': 23, 'fat': 0.9, 'fiber': 1.8}),
        ('Broccoli', 'produce', 'g', {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'fiber': 2.6}),
        ('Olive Oil', 'pantry', 'ml', {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100, 'fiber': 0}),
        ('Garlic', 'produce', 'g', {'calories': 149, 'protein': 6.4, 'carbs': 33, 'fat': 0.5, 'fiber': 2.1}),
        ('Onion', 'produce', 'g', {'calories': 40, 'protein': 1.1, 'carbs': 9, 'fat': 0.1, 'fiber': 1.7}),
        ('Tomato', 'produce', 'g', {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2, 'fiber': 1.2}),
        ('Salmon', 'meat', 'g', {'calories': 208, 'protein': 20, 'carbs': 0, 'fat': 13, 'fiber': 0}),
        ('Egg', 'dairy', 'unit', {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11, 'fiber': 0}),
        ('Milk', 'dairy', 'ml', {'calories': 42, 'protein': 3.4, 'carbs': 5, 'fat': 1, 'fiber': 0}),
        ('Bread', 'pantry', 'g', {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2, 'fiber': 2.7}),
        ('Butter', 'dairy', 'g', {'calories': 717, 'protein': 0.9, 'carbs': 0.1, 'fat': 81, 'fiber': 0}),
        ('Salt', 'pantry', 'g', {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0}),
        ('Black Pepper', 'pantry', 'g', {'calories': 251, 'protein': 10, 'carbs': 64, 'fat': 3.3, 'fiber': 25}),
        ('Beef', 'meat', 'g', {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 15, 'fiber': 0}),
        ('Pasta', 'pantry', 'g', {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1, 'fiber': 1.8}),
        ('Cheese', 'dairy', 'g', {'calories': 402, 'protein': 25, 'carbs': 1.3, 'fat': 33, 'fiber': 0}),
        ('Carrot', 'produce', 'g', {'calories': 41, 'protein': 0.9, 'carbs': 10, 'fat': 0.2, 'fiber': 2.8}),
        ('Potato', 'produce', 'g', {'calories': 77, 'protein': 2, 'carbs': 17, 'fat': 0.1, 'fiber': 2.2}),
        ('Apple', 'produce', 'g', {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2, 'fiber': 2.4}),
    ]
    
    for name, category, unit, nutrition in ingredients_data:
        existing = Ingredient.query.filter_by(name=name).first()
        if not existing:
            ingredient = Ingredient(
                name=name,
                category=category,
                default_unit=unit
            )
            ingredient.nutrition = nutrition
            db.session.add(ingredient)
    
    db.session.commit()


# ============================================================
# TEMPLATE FILTERS
# ============================================================

@app.template_filter('format_time')
def format_time(minutes):
    """Format minutes to human readable time"""
    if not minutes:
        return '0 min'
    if minutes < 60:
        return f'{minutes} min'
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f'{hours} hr'
    return f'{hours} hr {mins} min'


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_ingredients()
    
    app.run(debug=True, host='0.0.0.0', port=5000)