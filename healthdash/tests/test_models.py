import pytest
from datetime import datetime
from healthdash import create_app
from healthdash.models import db, Service, HealthCheck


@pytest.fixture
def app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_service_model_creation(app):
    with app.app_context():
        service = Service(
            name="Test API",
            url="https://example.com",
            method="GET",
            expected_status=200,
        )
        db.session.add(service)
        db.session.commit()

        retrieved = Service.query.first()
        assert retrieved is not None
        assert retrieved.name == "Test API"
        assert retrieved.url == "https://example.com"


def test_health_check_model_creation(app):
    with app.app_context():
        service = Service(name="Test Service", url="https://example.com")
        db.session.add(service)
        db.session.commit()

        check = HealthCheck(
            service_id=service.id,
            is_up=True,
            response_time=125.5,
            status_code=200,
        )
        db.session.add(check)
        db.session.commit()

        retrieved = HealthCheck.query.first()
        assert retrieved is not None
        assert retrieved.is_up is True
        assert retrieved.service_id == service.id


def test_service_uptime_percentage(app):
    with app.app_context():
        service = Service(name="Test Service", url="https://example.com")
        db.session.add(service)
        db.session.commit()

        for i in range(10):
            check = HealthCheck(
                service_id=service.id,
                is_up=(i < 8),
                response_time=100.0,
                status_code=200,
            )
            db.session.add(check)
        db.session.commit()

        assert service.uptime_percentage == 80.0


def test_service_avg_response_time(app):
    with app.app_context():
        service = Service(name="Test Service", url="https://example.com")
        db.session.add(service)
        db.session.commit()

        response_times = [100.0, 150.0, 200.0, 250.0, 300.0]
        for rt in response_times:
            check = HealthCheck(
                service_id=service.id,
                is_up=True,
                response_time=rt,
                status_code=200,
            )
            db.session.add(check)
        db.session.commit()

        assert service.avg_response_time == 200.0


def test_service_repr(app):
    with app.app_context():
        service = Service(name="MyService", url="https://example.com")
        db.session.add(service)
        db.session.commit()

        assert repr(service) == "<Service MyService>"
