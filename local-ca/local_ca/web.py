"""Flask web dashboard for local-ca."""
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime
from io import BytesIO

from . import database, cert_manager
from .crypto_utils import load_certificate, load_private_key


app = Flask(__name__)
app.secret_key = 'local-ca-secret-key-change-in-production'


@app.route('/')
def index():
    """Dashboard home page."""
    if not database.check_database_exists():
        database.init_database()
    
    cas = database.get_all_cas()
    certs = database.get_all_certificates()
    csrs = database.get_all_csrs()
    
    return render_template('index.html',
                         cas=cas,
                         certificates=certs,
                         csrs=csrs,
                         now=datetime.now())


@app.route('/ca')
def ca_list():
    """List all CAs."""
    cas = database.get_all_cas()
    return render_template('ca_list.html', cas=cas)


@app.route('/ca/<int:ca_id>')
def ca_detail(ca_id):
    """CA detail page."""
    ca = database.get_ca(ca_id)
    if not ca:
        flash('CA not found', 'error')
        return redirect(url_for('ca_list'))
    
    certs = database.get_certificates_by_ca(ca_id)
    chain = cert_manager.get_ca_chain(ca_id)
    
    return render_template('ca_detail.html', ca=ca, certs=certs, chain=chain)


@app.route('/ca/create', methods=['GET', 'POST'])
def ca_create():
    """Create a new CA."""
    if request.method == 'POST':
        name = request.form.get('name')
        common_name = request.form.get('common_name')
        ca_type = request.form.get('type')
        parent_id = request.form.get('parent_id')
        parent_id = int(parent_id) if parent_id else None
        
        country = request.form.get('country')
        state = request.form.get('state')
        locality = request.form.get('locality')
        organization = request.form.get('organization')
        validity_years = int(request.form.get('validity_years', 10))
        key_size = int(request.form.get('key_size', 4096))
        
        try:
            if ca_type == 'root':
                success, error, result = cert_manager.create_root_ca(
                    name=name,
                    common_name=common_name,
                    country=country,
                    state=state,
                    locality=locality,
                    organization=organization,
                    validity_years=validity_years,
                    key_size=key_size
                )
            else:
                if not parent_id:
                    flash('Parent CA is required for intermediate CAs', 'error')
                    return redirect(url_for('ca_create'))
                
                success, error, result = cert_manager.create_intermediate_ca(
                    name=name,
                    common_name=common_name,
                    parent_ca_id=parent_id,
                    country=country,
                    state=state,
                    locality=locality,
                    organization=organization,
                    validity_years=validity_years,
                    key_size=key_size
                )
            
            if success:
                flash(f'CA "{name}" created successfully', 'success')
                return redirect(url_for('ca_detail', ca_id=result['id']))
            else:
                flash(f'Error: {error}', 'error')
                
        except Exception as e:
            flash(f'Error creating CA: {e}', 'error')
    
    cas = database.get_all_cas()
    return render_template('ca_create.html', cas=cas)


@app.route('/ca/delete/<int:ca_id>', methods=['POST'])
def ca_delete(ca_id):
    """Delete a CA."""
    success = database.delete_ca(ca_id)
    if success:
        flash('CA deleted successfully', 'success')
    else:
        flash('Error deleting CA', 'error')
    return redirect(url_for('ca_list'))


@app.route('/cert')
def cert_list():
    """List all certificates."""
    ca_id = request.args.get('ca_id', type=int)
    if ca_id:
        certs = database.get_certificates_by_ca(ca_id)
    else:
        certs = database.get_all_certificates()
    
    cas = database.get_all_cas()
    return render_template('cert_list.html', certificates=certs, cas=cas, selected_ca=ca_id)


@app.route('/cert/<int:cert_id>')
def cert_detail(cert_id):
    """Certificate detail page."""
    cert = database.get_certificate(cert_id)
    if not cert:
        flash('Certificate not found', 'error')
        return redirect(url_for('cert_list'))
    
    chain = cert_manager.get_cert_chain(cert_id)
    ca = database.get_ca(cert['ca_id'])
    
    return render_template('cert_detail.html', certificate=cert, chain=chain, ca=ca)


@app.route('/cert/create', methods=['GET', 'POST'])
def cert_create():
    """Create a new certificate."""
    if request.method == 'POST':
        name = request.form.get('name')
        common_name = request.form.get('common_name')
        ca_id = int(request.form.get('ca_id'))
        
        country = request.form.get('country')
        state = request.form.get('state')
        locality = request.form.get('locality')
        organization = request.form.get('organization')
        email = request.form.get('email')
        san_raw = request.form.get('san', '')
        validity_years = int(request.form.get('validity_years', 1))
        key_size = int(request.form.get('key_size', 2048))
        
        # Parse SANs
        san = [s.strip() for s in san_raw.split(',') if s.strip()]
        
        try:
            success, error, result = cert_manager.create_tls_certificate(
                name=name,
                common_name=common_name,
                ca_id=ca_id,
                country=country,
                state=state,
                locality=locality,
                organization=organization,
                email=email,
                san=san if san else None,
                validity_years=validity_years,
                key_size=key_size
            )
            
            if success:
                flash(f'Certificate "{name}" created successfully', 'success')
                return redirect(url_for('cert_detail', cert_id=result['id']))
            else:
                flash(f'Error: {error}', 'error')
                
        except Exception as e:
            flash(f'Error creating certificate: {e}', 'error')
    
    cas = database.get_all_cas()
    return render_template('cert_create.html', cas=cas)


@app.route('/cert/delete/<int:cert_id>', methods=['POST'])
def cert_delete(cert_id):
    """Delete a certificate."""
    success = database.delete_certificate(cert_id)
    if success:
        flash('Certificate deleted successfully', 'success')
    else:
        flash('Error deleting certificate', 'error')
    return redirect(url_for('cert_list'))


@app.route('/cert/download/<int:cert_id>')
def cert_download(cert_id):
    """Download certificate."""
    cert = database.get_certificate(cert_id)
    if not cert:
        flash('Certificate not found', 'error')
        return redirect(url_for('cert_list'))
    
    from pathlib import Path
    cert_data = Path(cert['cert_path']).read_bytes()
    
    return send_file(
        BytesIO(cert_data),
        mimetype='application/x-pem-file',
        as_attachment=True,
        download_name=f'{cert["name"]}.pem'
    )


@app.route('/cert/download-key/<int:cert_id>')
def cert_download_key(cert_id):
    """Download private key."""
    cert = database.get_certificate(cert_id)
    if not cert or not cert.get('key_path'):
        flash('Certificate or key not found', 'error')
        return redirect(url_for('cert_list'))
    
    from pathlib import Path
    key_data = Path(cert['key_path']).read_bytes()
    
    return send_file(
        BytesIO(key_data),
        mimetype='application/x-pem-file',
        as_attachment=True,
        download_name=f'{cert["name"]}-key.pem'
    )


@app.route('/csr')
def csr_list():
    """List all CSRs."""
    csrs = database.get_all_csrs()
    cas = database.get_all_cas()
    return render_template('csr_list.html', csrs=csrs, cas=cas)


@app.route('/csr/sign', methods=['GET', 'POST'])
def csr_sign():
    """Sign a CSR."""
    if request.method == 'POST':
        csr_file = request.files.get('csr_file')
        name = request.form.get('name')
        ca_id = int(request.form.get('ca_id'))
        validity_years = int(request.form.get('validity_years', 1))
        
        if not csr_file or not name:
            flash('CSR file and name are required', 'error')
            return redirect(url_for('csr_sign'))
        
        try:
            csr_data = csr_file.read().decode()
            
            success, error, result = cert_manager.sign_csr_request(
                csr_data=csr_data,
                ca_id=ca_id,
                name=name,
                validity_years=validity_years
            )
            
            if success:
                flash(f'CSR signed successfully', 'success')
                return redirect(url_for('cert_detail', cert_id=result['id']))
            else:
                flash(f'Error: {error}', 'error')
                
        except Exception as e:
            flash(f'Error signing CSR: {e}', 'error')
    
    cas = database.get_all_cas()
    return render_template('csr_sign.html', cas=cas)


@app.route('/csr/delete/<int:csr_id>', methods=['POST'])
def csr_delete(csr_id):
    """Delete a CSR."""
    success = database.delete_csr(csr_id)
    if success:
        flash('CSR deleted successfully', 'success')
    else:
        flash('Error deleting CSR', 'error')
    return redirect(url_for('csr_list'))


@app.route('/export', methods=['GET', 'POST'])
def export_page():
    """Export certificates."""
    if request.method == 'POST':
        cert_id = int(request.form.get('cert_id'))
        output_format = request.form.get('format', 'pem')
        passphrase = request.form.get('passphrase')
        
        cert = database.get_certificate(cert_id)
        if not cert:
            flash('Certificate not found', 'error')
            return redirect(url_for('export_page'))
        
        try:
            import tempfile
            from pathlib import Path
            
            with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as f:
                output_path = f.name
            
            success, error = cert_manager.export_certificate(
                cert_id=cert_id,
                output_path=output_path,
                format=output_format,
                passphrase=passphrase
            )
            
            if success:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f'{cert["name"]}.{output_format}'
                )
            else:
                flash(f'Error: {error}', 'error')
                
        except Exception as e:
            flash(f'Error exporting: {e}', 'error')
    
    certs = database.get_all_certificates()
    return render_template('export.html', certificates=certs)


if __name__ == '__main__':
    app.run(debug=True)