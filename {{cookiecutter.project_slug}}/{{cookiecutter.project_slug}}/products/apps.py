from django.apps import AppConfig


class ProductsConfig(AppConfig):
    name = "{{cookiecutter.project_slug}}.products"

    def ready(self):
        import {{cookiecutter.project_slug}}.products.signals  # noqa
