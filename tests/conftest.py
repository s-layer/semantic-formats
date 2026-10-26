from hypothesis import HealthCheck, settings

# The first validation of each model is slow while pydantic warms up, which a per-example
# deadline would report as flaky. CI gets more examples than a local run.
settings.register_profile("default", deadline=None, suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("ci", parent=settings.get_profile("default"), max_examples=500)
settings.load_profile("default")
