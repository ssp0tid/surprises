from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from database import init_db, create_client, get_clients, get_client, update_client, delete_client
from database import create_invoice, get_invoices, get_invoice, update_invoice, update_invoice_status, delete_invoice, get_dashboard_stats, client_has_invoices
from pdf_generator import generate_pdf, WEASYPRINT_AVAILABLE
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def safe_float(value, default=0.0):
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


@app.route('/')
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)


@app.route('/clients')
def client_list():
    search = request.args.get('search', '')
    clients = get_clients(search=search if search else None)
    return render_template('clients.html', clients=clients, search=search)


@app.route('/clients/new', methods=['GET', 'POST'])
def client_new():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'company': request.form.get('company', '').strip(),
            'address': request.form.get('address', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'tax_id': request.form.get('tax_id', '').strip(),
        }
        if not data['name']:
            return render_template('client_form.html', client=data, error="Name is required."), 400
        create_client(data)
        return redirect(url_for('client_list'))
    return render_template('client_form.html', client=None, error=None)


@app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
def client_edit(client_id):
    client = get_client(client_id)
    if not client:
        return "Client not found", 404
    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'company': request.form.get('company', '').strip(),
            'address': request.form.get('address', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'tax_id': request.form.get('tax_id', '').strip(),
        }
        if not data['name']:
            return render_template('client_form.html', client=data, error="Name is required."), 400
        update_client(client_id, data)
        return redirect(url_for('client_list'))
    return render_template('client_form.html', client=client, error=None)


@app.route('/clients/<int:client_id>/delete', methods=['POST'])
def client_delete(client_id):
    client = get_client(client_id)
    if not client:
        return "Client not found", 404
    if client_has_invoices(client_id):
        return render_template('clients.html', clients=get_clients(),
                               search='', error="Cannot delete client with existing invoices."), 400
    delete_client(client_id)
    return redirect(url_for('client_list'))


@app.route('/invoices')
def invoice_list():
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args['status']
    if request.args.get('client_id'):
        filters['client_id'] = request.args['client_id']
    if request.args.get('date_from'):
        filters['date_from'] = request.args['date_from']
    if request.args.get('date_to'):
        filters['date_to'] = request.args['date_to']
    invoices = get_invoices(filters=filters if filters else None)
    clients = get_clients()
    return render_template('invoices.html', invoices=invoices, clients=clients, filters=filters)


@app.route('/invoices/new', methods=['GET', 'POST'])
def invoice_new():
    clients = get_clients()
    if request.method == 'POST':
        data = {
            'client_id': request.form.get('client_id'),
            'issue_date': request.form.get('issue_date', '').strip(),
            'due_date': request.form.get('due_date', '').strip(),
            'status': request.form.get('status', 'draft'),
            'notes': request.form.get('notes', '').strip(),
            'tax_rate': safe_float(request.form.get('tax_rate', 0)),
        }
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        items = []
        for i in range(len(descriptions)):
            if descriptions[i].strip():
                items.append({
                    'description': descriptions[i].strip(),
                    'quantity': safe_float(quantities[i], 1),
                    'unit_price': safe_float(unit_prices[i], 0),
                })
        if not data['client_id'] or not data['issue_date'] or not data['due_date']:
            return render_template('invoice_form.html', invoice=data, items=items,
                                   clients=clients, error="Client, issue date, and due date are required."), 400
        if not items:
            return render_template('invoice_form.html', invoice=data, items=items,
                                   clients=clients, error="At least one line item is required."), 400
        invoice_id = create_invoice(data, items)
        return redirect(url_for('invoice_view', invoice_id=invoice_id))
    return render_template('invoice_form.html', invoice=None, items=[], clients=clients, error=None)


@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def invoice_edit(invoice_id):
    clients = get_clients()
    invoice = get_invoice(invoice_id)
    if not invoice:
        return "Invoice not found", 404
    if request.method == 'POST':
        data = {
            'client_id': request.form.get('client_id'),
            'issue_date': request.form.get('issue_date', '').strip(),
            'due_date': request.form.get('due_date', '').strip(),
            'status': request.form.get('status', 'draft'),
            'notes': request.form.get('notes', '').strip(),
            'tax_rate': safe_float(request.form.get('tax_rate', 0)),
        }
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        items = []
        for i in range(len(descriptions)):
            if descriptions[i].strip():
                items.append({
                    'description': descriptions[i].strip(),
                    'quantity': safe_float(quantities[i], 1),
                    'unit_price': safe_float(unit_prices[i], 0),
                })
        if not data['client_id'] or not data['issue_date'] or not data['due_date']:
            return render_template('invoice_form.html', invoice=data, items=items,
                                   clients=clients, error="Client, issue date, and due date are required."), 400
        if not items:
            return render_template('invoice_form.html', invoice=data, items=items,
                                   clients=clients, error="At least one line item is required."), 400
        update_invoice(invoice_id, data, items)
        return redirect(url_for('invoice_view', invoice_id=invoice_id))
    return render_template('invoice_form.html', invoice=invoice, items=invoice.get('items', []),
                           clients=clients, error=None)


@app.route('/invoices/<int:invoice_id>')
def invoice_view(invoice_id):
    invoice = get_invoice(invoice_id)
    if not invoice:
        return "Invoice not found", 404
    return render_template('invoice_view.html', invoice=invoice)


@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
def invoice_delete(invoice_id):
    delete_invoice(invoice_id)
    return redirect(url_for('invoice_list'))


@app.route('/invoices/<int:invoice_id>/status', methods=['POST'])
def invoice_status(invoice_id):
    invoice = get_invoice(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    valid_statuses = ('draft', 'sent', 'paid', 'overdue')
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    update_invoice_status(invoice_id, data['status'])
    return jsonify({'success': True, 'status': data['status']})


@app.route('/invoices/<int:invoice_id>/pdf')
def invoice_pdf(invoice_id):
    invoice = get_invoice(invoice_id)
    if not invoice:
        return "Invoice not found", 404

    pdf_bytes = generate_pdf(invoice, template_folder=app.jinja_loader.searchpath[0])

    if pdf_bytes is None:
        return render_template('invoice_pdf.html', invoice=invoice)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{invoice["invoice_number"]}.pdf"'
    return response


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error("Internal server error: %s", e)
    return render_template('error.html', code=500, message="Something went wrong"), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
