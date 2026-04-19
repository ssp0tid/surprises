import pytest
from healthdash import create_app
from healthdash.models import db, Service, HealthCheck
from healthdash.services.checker import perform_health_check
from healthdash.services.scheduler import schedule_service_checks


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


def test_perform_health_check(app):
    with app.app_context():
        service = Service(
            name="Test Service",
            url="https://httpbin.org/status/200",
            method="GET",
            expected_status=200,
            is_active=True,
        )
        db.session.add(service)
        db.session.commit()

        check = perform_health_check(service.id)

        assert check is not None
        assert check.service_id == service.id
        assert check.is_up is True
        assert check.status_code == 200


def test_schedule_service_checks(app):
    with app.app_context():
        schedule_service_checks(app)


def test_health_check_inactive_service(app):
    with app.app_context():
        service = Service(
            name="Inactive Service",
            url="https://httpbin.org/status/200",
            is_active=False,
        )
        db.session.add(service)
        db.session.commit()

        result = perform_health_check(service.id)

        assert result is None
