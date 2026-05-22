from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = 'subtrak-dev-key'
DATABASE = 'subtrak.db'

CATEGORIES = ['entertainment', 'productivity', 'dev-tools', 'cloud', 'music', 'other']
CURRENCIES = ['USD', 'EUR', 'GBP']
BILLING_CYCLES = ['monthly', 'yearly', 'weekly']


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if not exist."""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'other',
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            billing_cycle TEXT NOT NULL DEFAULT 'monthly',
            next_renewal DATE NOT NULL,
            url TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def normalize_to_monthly(amount, cycle):
    """Convert any billing cycle to monthly equivalent."""
    if cycle == 'weekly':
        return amount * (52 / 12)
    elif cycle == 'yearly':
        return amount / 12
    return amount


@app.route('/')
def dashboard():
    """Dashboard with total spend, upcoming renewals, and charts."""
    db = get_db()
    try:
        subs = db.execute(
            'SELECT * FROM subscriptions WHERE active = 1'
        ).fetchall()

        total_monthly = sum(
            normalize_to_monthly(s['amount'], s['billing_cycle']) for s in subs
        )

        upcoming = db.execute(
            'SELECT * FROM subscriptions WHERE active = 1 ORDER BY next_renewal ASC LIMIT 5'
        ).fetchall()

        by_category = {}
        for s in subs:
            monthly = normalize_to_monthly(s['amount'], s['billing_cycle'])
            by_category[s['category']] = by_category.get(s['category'], 0) + monthly

        monthly_projection = []
        for i in range(12):
            monthly_projection.append(round(total_monthly * (i + 1), 2))

        return render_template(
            'dashboard.html',
            total_monthly=round(total_monthly, 2),
            total_yearly=round(total_monthly * 12, 2),
            active_count=len(subs),
            upcoming=upcoming,
            by_category=by_category,
            monthly_projection=monthly_projection,
        )
    finally:
        db.close()


@app.route('/subscriptions')
def list_subscriptions():
    """List all subscriptions with filtering and sorting."""
    db = get_db()
    try:
        category_filter = request.args.get('category', '')
        sort_by = request.args.get('sort', 'next_renewal')

        query = 'SELECT * FROM subscriptions'
        params = []

        if category_filter:
            query += ' WHERE category = ?'
            params.append(category_filter)

        if sort_by == 'amount':
            query += ' ORDER BY amount DESC'
        else:
            query += ' ORDER BY next_renewal ASC'

        subs = db.execute(query, params).fetchall()

        return render_template(
            'subscriptions.html',
            subscriptions=subs,
            categories=CATEGORIES,
            current_category=category_filter,
            current_sort=sort_by,
        )
    finally:
        db.close()


@app.route('/subscriptions/add', methods=['GET', 'POST'])
def add_subscription():
    """Add a new subscription."""
    if request.method == 'POST':
        errors = _validate_subscription_form(request.form)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'add.html',
                categories=CATEGORIES,
                currencies=CURRENCIES,
                billing_cycles=BILLING_CYCLES,
                subscription=request.form,
                editing=False,
            )

        db = get_db()
        try:
            db.execute(
                '''INSERT INTO subscriptions
                   (name, category, amount, currency, billing_cycle, next_renewal, url, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    request.form['name'].strip(),
                    request.form['category'],
                    float(request.form['amount']),
                    request.form['currency'],
                    request.form['billing_cycle'],
                    request.form['next_renewal'],
                    request.form.get('url', '').strip(),
                    request.form.get('notes', '').strip(),
                ),
            )
            db.commit()
        except sqlite3.Error as e:
            flash(f'Database error: {e}', 'error')
            return redirect(url_for('add_subscription'))
        finally:
            db.close()

        flash('Subscription added successfully.', 'success')
        return redirect(url_for('list_subscriptions'))

    return render_template(
        'add.html',
        categories=CATEGORIES,
        currencies=CURRENCIES,
        billing_cycles=BILLING_CYCLES,
        subscription=None,
        editing=False,
    )


@app.route('/subscriptions/<int:id>/edit', methods=['GET', 'POST'])
def edit_subscription(id):
    """Edit an existing subscription."""
    db = get_db()
    try:
        sub = db.execute('SELECT * FROM subscriptions WHERE id = ?', (id,)).fetchone()
        if not sub:
            flash('Subscription not found.', 'error')
            return redirect(url_for('list_subscriptions'))

        if request.method == 'POST':
            errors = _validate_subscription_form(request.form)
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template(
                    'add.html',
                    categories=CATEGORIES,
                    currencies=CURRENCIES,
                    billing_cycles=BILLING_CYCLES,
                    subscription=request.form,
                    editing=True,
                    sub_id=id,
                )

            try:
                db.execute(
                    '''UPDATE subscriptions
                       SET name=?, category=?, amount=?, currency=?, billing_cycle=?,
                           next_renewal=?, url=?, notes=?
                       WHERE id=?''',
                    (
                        request.form['name'].strip(),
                        request.form['category'],
                        float(request.form['amount']),
                        request.form['currency'],
                        request.form['billing_cycle'],
                        request.form['next_renewal'],
                        request.form.get('url', '').strip(),
                        request.form.get('notes', '').strip(),
                        id,
                    ),
                )
                db.commit()
            except sqlite3.Error as e:
                flash(f'Database error: {e}', 'error')
                return redirect(url_for('edit_subscription', id=id))
            flash('Subscription updated successfully.', 'success')
            return redirect(url_for('list_subscriptions'))

        return render_template(
            'add.html',
            categories=CATEGORIES,
            currencies=CURRENCIES,
            billing_cycles=BILLING_CYCLES,
            subscription=sub,
            editing=True,
            sub_id=id,
        )
    finally:
        db.close()


@app.route('/subscriptions/<int:id>/delete', methods=['POST'])
def delete_subscription(id):
    """Delete a subscription."""
    db = get_db()
    try:
        cursor = db.execute('DELETE FROM subscriptions WHERE id = ?', (id,))
        db.commit()
        if cursor.rowcount == 0:
            flash('Subscription not found.', 'error')
        else:
            flash('Subscription deleted.', 'success')
    finally:
        db.close()
    return redirect(url_for('list_subscriptions'))


@app.route('/subscriptions/<int:id>/toggle', methods=['POST'])
def toggle_subscription(id):
    """Toggle active/paused status."""
    db = get_db()
    try:
        sub = db.execute('SELECT active FROM subscriptions WHERE id = ?', (id,)).fetchone()
        if sub:
            new_status = 0 if sub['active'] else 1
            db.execute('UPDATE subscriptions SET active = ? WHERE id = ?', (new_status, id))
            db.commit()
            status_text = 'activated' if new_status else 'paused'
            flash(f'Subscription {status_text}.', 'success')
        else:
            flash('Subscription not found.', 'error')
    finally:
        db.close()
    return redirect(url_for('list_subscriptions'))


@app.route('/api/stats')
def api_stats():
    """JSON endpoint: spending statistics."""
    db = get_db()
    try:
        subs = db.execute('SELECT * FROM subscriptions WHERE active = 1').fetchall()

        total_monthly = sum(
            normalize_to_monthly(s['amount'], s['billing_cycle']) for s in subs
        )

        by_category = {}
        for s in subs:
            monthly = normalize_to_monthly(s['amount'], s['billing_cycle'])
            by_category[s['category']] = round(
                by_category.get(s['category'], 0) + monthly, 2
            )

        return jsonify({
            'total_monthly': round(total_monthly, 2),
            'total_yearly': round(total_monthly * 12, 2),
            'count': len(subs),
            'by_category': by_category,
        })
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/upcoming')
def api_upcoming():
    """JSON endpoint: subscriptions renewing within N days."""
    days = request.args.get('days', 30, type=int)
    if days < 0:
        return jsonify({'error': 'days must be non-negative'}), 400
    cutoff = (date.today() + timedelta(days=days)).isoformat()

    db = get_db()
    try:
        subs = db.execute(
            '''SELECT id, name, category, amount, currency, billing_cycle, next_renewal
               FROM subscriptions
               WHERE active = 1 AND next_renewal <= ?
               ORDER BY next_renewal ASC''',
            (cutoff,),
        ).fetchall()

        return jsonify([dict(s) for s in subs])
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/analytics')
def analytics():
    """Analytics page with charts and summary stats."""
    db = get_db()
    try:
        subs = db.execute('SELECT * FROM subscriptions WHERE active = 1').fetchall()

        by_category_spend = {}
        by_category_count = {}
        amounts = []

        for s in subs:
            monthly = normalize_to_monthly(s['amount'], s['billing_cycle'])
            by_category_spend[s['category']] = (
                by_category_spend.get(s['category'], 0) + monthly
            )
            by_category_count[s['category']] = (
                by_category_count.get(s['category'], 0) + 1
            )
            amounts.append(monthly)

        by_category_spend = {k: round(v, 2) for k, v in by_category_spend.items()}

        total_monthly = sum(amounts) if amounts else 0
        avg_cost = round(total_monthly / len(amounts), 2) if amounts else 0
        most_expensive = max(amounts) if amounts else 0
        cheapest = min(amounts) if amounts else 0

        return render_template(
            'analytics.html',
            by_category_spend=by_category_spend,
            by_category_count=by_category_count,
            avg_cost=avg_cost,
            most_expensive=round(most_expensive, 2),
            cheapest=round(cheapest, 2),
            total_monthly=round(total_monthly, 2),
            total_yearly=round(total_monthly * 12, 2),
        )
    finally:
        db.close()


def _validate_subscription_form(form):
    """Validate subscription form data. Returns list of error messages."""
    errors = []
    if not form.get('name', '').strip():
        errors.append('Name is required.')
    try:
        amount = float(form.get('amount', 0))
        if amount <= 0:
            errors.append('Amount must be greater than zero.')
    except (ValueError, TypeError):
        errors.append('Amount must be a valid number.')
    if not form.get('next_renewal'):
        errors.append('Next renewal date is required.')
    else:
        try:
            datetime.strptime(form['next_renewal'], '%Y-%m-%d')
        except ValueError:
            errors.append('Next renewal must be a valid date (YYYY-MM-DD).')
    if form.get('category') not in CATEGORIES:
        errors.append('Invalid category.')
    if form.get('currency') not in CURRENCIES:
        errors.append('Invalid currency.')
    if form.get('billing_cycle') not in BILLING_CYCLES:
        errors.append('Invalid billing cycle.')
    return errors


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
