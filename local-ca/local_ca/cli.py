"""CLI interface for local-ca."""
import sys
import click
import json
from pathlib import Path

from . import database, cert_manager
from .validators import validate_ca_name, validate_cert_name, validate_common_name


def print_json(data):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


@click.group()
def cli():
    """Local Certificate Authority Management Tool."""
    pass


@cli.command()
def init():
    """Initialize the local-ca database."""
    try:
        database.init_database()
        click.echo("Database initialized successfully.")
        click.echo(f"Database: {database.DATABASE_PATH}")
        click.echo(f"Certificates: {database.CERTS_DIR}")
    except Exception as e:
        click.echo(f"Error initializing database: {e}", err=True)
        sys.exit(1)


@cli.group()
def ca():
    """Certificate Authority management."""
    pass


@ca.command('create')
@click.option('--name', required=True, help='CA name (unique identifier)')
@click.option('--common-name', required=True, help='Common name')
@click.option('--type', type=click.Choice(['root', 'intermediate']), default='root', help='CA type')
@click.option('--parent-id', type=int, help='Parent CA ID (for intermediate)')
@click.option('--country', help='Country code (2 letters)')
@click.option('--state', help='State or province')
@click.option('--locality', help='Locality')
@click.option('--organization', help='Organization name')
@click.option('--validity-years', type=int, default=10, help='Validity in years')
@click.option('--key-size', type=int, default=4096, help='Key size in bits')
def ca_create(name, common_name, type, parent_id, country, state, locality, organization, validity_years, key_size):
    """Create a new CA."""
    # Initialize database if needed
    if not database.check_database_exists():
        database.init_database()
    
    try:
        if type == 'root':
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
                click.echo("--parent-id is required for intermediate CAs", err=True)
                sys.exit(1)
            
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
        
        if not success:
            click.echo(f"Error creating CA: {error}", err=True)
            sys.exit(1)
        
        click.echo(f"CA created successfully!")
        print_json(result)
        
    except Exception as e:
        click.echo(f"Error creating CA: {e}", err=True)
        sys.exit(1)


@ca.command('list')
def ca_list():
    """List all CAs."""
    if not database.check_database_exists():
        click.echo("Database not initialized. Run 'local-ca init' first.")
        sys.exit(1)
    
    try:
        cas = database.get_all_cas()
        if not cas:
            click.echo("No CAs found.")
            return
        
        for ca in cas:
            click.echo(f"\nID: {ca['id']}")
            click.echo(f"  Name: {ca['name']}")
            click.echo(f"  Type: {ca['type']}")
            click.echo(f"  Subject: {ca['subject']}")
            click.echo(f"  Valid until: {ca['not_after']}")
        
    except Exception as e:
        click.echo(f"Error listing CAs: {e}", err=True)
        sys.exit(1)


@ca.command('show')
@click.argument('ca_id', type=int)
def ca_show(ca_id):
    """Show CA details."""
    try:
        ca = database.get_ca(ca_id)
        if not ca:
            click.echo(f"CA with ID {ca_id} not found", err=True)
            sys.exit(1)
        
        click.echo(f"\nID: {ca['id']}")
        click.echo(f"  Name: {ca['name']}")
        click.echo(f"  Type: {ca['type']}")
        click.echo(f"  Subject: {ca['subject']}")
        click.echo(f"  Issuer: {ca['issuer']}")
        click.echo(f"  Valid from: {ca['not_before']}")
        click.echo(f"  Valid until: {ca['not_after']}")
        click.echo(f"  Certificate: {ca['cert_path']}")
        click.echo(f"  Private key: {ca['key_path']}")
        
    except Exception as e:
        click.echo(f"Error showing CA: {e}", err=True)
        sys.exit(1)


@ca.command('delete')
@click.argument('ca_id', type=int)
def ca_delete(ca_id):
    """Delete a CA."""
    try:
        success = database.delete_ca(ca_id)
        if not success:
            click.echo(f"CA with ID {ca_id} not found", err=True)
            sys.exit(1)
        
        click.echo(f"CA {ca_id} deleted successfully.")
        
    except Exception as e:
        click.echo(f"Error deleting CA: {e}", err=True)
        sys.exit(1)


@cli.group()
def cert():
    """Certificate management."""
    pass


@cert.command('create')
@click.option('--name', required=True, help='Certificate name (unique identifier)')
@click.option('--common-name', required=True, help='Common name (typically hostname)')
@click.option('--ca-id', type=int, required=True, help='Signing CA ID')
@click.option('--country', help='Country code (2 letters)')
@click.option('--state', help='State or province')
@click.option('--locality', help='Locality')
@click.option('--organization', help='Organization name')
@click.option('--email', help='Email address')
@click.option('--san', multiple=True, help='Subject Alternative Names (can repeat)')
@click.option('--validity-years', type=int, default=1, help='Validity in years')
@click.option('--key-size', type=int, default=2048, help='Key size in bits')
def cert_create(name, common_name, ca_id, country, state, locality, organization, email, san, validity_years, key_size):
    """Create a new TLS certificate."""
    # Initialize database if needed
    if not database.check_database_exists():
        database.init_database()
    
    try:
        san_list = list(san) if san else None
        
        success, error, result = cert_manager.create_tls_certificate(
            name=name,
            common_name=common_name,
            ca_id=ca_id,
            country=country,
            state=state,
            locality=locality,
            organization=organization,
            email=email,
            san=san_list,
            validity_years=validity_years,
            key_size=key_size
        )
        
        if not success:
            click.echo(f"Error creating certificate: {error}", err=True)
            sys.exit(1)
        
        click.echo(f"Certificate created successfully!")
        print_json(result)
        
    except Exception as e:
        click.echo(f"Error creating certificate: {e}", err=True)
        sys.exit(1)


@cert.command('list')
@click.option('--ca-id', type=int, help='Filter by CA ID')
def cert_list(ca_id):
    """List all certificates."""
    if not database.check_database_exists():
        click.echo("Database not initialized. Run 'local-ca init' first.")
        sys.exit(1)
    
    try:
        if ca_id:
            certs = database.get_certificates_by_ca(ca_id)
        else:
            certs = database.get_all_certificates()
        
        if not certs:
            click.echo("No certificates found.")
            return
        
        for cert in certs:
            click.echo(f"\nID: {cert['id']}")
            click.echo(f"  Name: {cert['name']}")
            click.echo(f"  Common Name: {cert['common_name']}")
            click.echo(f"  Subject: {cert['subject']}")
            click.echo(f"  Valid until: {cert['not_after']}")
            click.echo(f"  Certificate: {cert['cert_path']}")
        
    except Exception as e:
        click.echo(f"Error listing certificates: {e}", err=True)
        sys.exit(1)


@cert.command('show')
@click.argument('cert_id', type=int)
def cert_show(cert_id):
    """Show certificate details."""
    try:
        cert = database.get_certificate(cert_id)
        if not cert:
            click.echo(f"Certificate with ID {cert_id} not found", err=True)
            sys.exit(1)
        
        click.echo(f"\nID: {cert['id']}")
        click.echo(f"  Name: {cert['name']}")
        click.echo(f"  Common Name: {cert['common_name']}")
        click.echo(f"  Subject: {cert['subject']}")
        click.echo(f"  Serial Number: {cert['serial_number']}")
        click.echo(f"  Valid from: {cert['not_before']}")
        click.echo(f"  Valid until: {cert['not_after']}")
        if cert['san']:
            click.echo(f"  SAN: {', '.join(cert['san'])}")
        click.echo(f"  Certificate: {cert['cert_path']}")
        if cert['key_path']:
            click.echo(f"  Private Key: {cert['key_path']}")
        
    except Exception as e:
        click.echo(f"Error showing certificate: {e}", err=True)
        sys.exit(1)


@cert.command('delete')
@click.argument('cert_id', type=int)
def cert_delete(cert_id):
    """Delete a certificate."""
    try:
        success = database.delete_certificate(cert_id)
        if not success:
            click.echo(f"Certificate with ID {cert_id} not found", err=True)
            sys.exit(1)
        
        click.echo(f"Certificate {cert_id} deleted successfully.")
        
    except Exception as e:
        click.echo(f"Error deleting certificate: {e}", err=True)
        sys.exit(1)


@cli.group()
def csr():
    """CSR management."""
    pass


@csr.command('sign')
@click.option('--csr-file', type=click.Path(exists=True), required=True, help='CSR file path')
@click.option('--ca-id', type=int, required=True, help='Signing CA ID')
@click.option('--name', required=True, help='Certificate name for signed certificate')
@click.option('--validity-years', type=int, default=1, help='Validity in years')
def csr_sign(csr_file, ca_id, name, validity_years):
    """Sign a CSR."""
    if not database.check_database_exists():
        database.init_database()
    
    try:
        csr_data = Path(csr_file).read_text()
        
        success, error, result = cert_manager.sign_csr_request(
            csr_data=csr_data,
            ca_id=ca_id,
            name=name,
            validity_years=validity_years
        )
        
        if not success:
            click.echo(f"Error signing CSR: {error}", err=True)
            sys.exit(1)
        
        click.echo(f"CSR signed successfully!")
        print_json(result)
        
    except Exception as e:
        click.echo(f"Error signing CSR: {e}", err=True)
        sys.exit(1)


@cli.command()
def export():
    """Export a certificate in various formats."""
    click.echo("Use 'cert export' subcommand for export operations.")


@cert.command('export')
@click.argument('cert_id', type=int)
@click.option('--output', required=True, help='Output file path')
@click.option('--format', type=click.Choice(['pem', 'p12']), default='pem', help='Export format')
@click.option('--passphrase', help='Passphrase for P12 format')
def cert_export(cert_id, output, format, passphrase):
    """Export a certificate."""
    try:
        success, error = cert_manager.export_certificate(
            cert_id=cert_id,
            output_path=output,
            format=format,
            passphrase=passphrase
        )
        
        if not success:
            click.echo(f"Error exporting certificate: {error}", err=True)
            sys.exit(1)
        
        click.echo(f"Certificate exported to {output}")
        
    except Exception as e:
        click.echo(f"Error exporting certificate: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def web(host, port, debug):
    """Start the web dashboard."""
    if not database.check_database_exists():
        database.init_database()
    
    try:
        from .web import app
        click.echo(f"Starting web dashboard at http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        click.echo(f"Error starting web dashboard: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()