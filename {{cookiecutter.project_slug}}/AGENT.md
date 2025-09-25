# AGENTS.md — Project AI Agents Playbook (Django)

> This file instructs AI coding agents (e.g., Codex) how to contribute code, reviews, tests, and docs in this repository. It mirrors our architecture and rules from `copilot-instructions.md` and MUST be followed.

---

## 1) General Code Style (MUST)

- Adhere to Python's PEP 8 standards for all Python code.
- Ensure docstrings are used for all models, views, forms, and complex functions.
- Avoid long lines of code. Prefer breaking them into multiple, readable lines.
- Use meaningful and descriptive names for variables, functions, and classes.
- Maintain consistent indentation (4 spaces per level).
- Use type hints for function signatures to enhance code clarity and maintainability.
- Avoid using wildcard imports (e.g., `from module import *`).
- Group imports in the following order: standard library, third-party packages, and local application imports. Separate each group with a blank line.
- Use single quotes for strings unless the string contains a single quote that would require escaping.
- Avoid using `print` statements for debugging; use logging instead.
- Ensure all code is compatible with Python 3.8+.
- Use f-strings for string formatting instead of older methods like `%` or `str.format()`.

---

## 2) Other Coding Policies

- **Django Signals** — use only when there's no cleaner alternative; prefer explicit service orchestration. (Signals are powerful but can hide side effects.)
- **DRF `filter_backends`** — not recommended for our APIs. We prefer QueryParams → Selector so we control mapping, sanitization, and permissions.

---

## 3) Project Architecture Overview — Agent Rules

### 3.1 Models (`models/`, `models.py`)

- Use `ForeignKey` for relationships—never store "code"/"uuid" in place of a proper FK.
- Model field names should be `snake_case`.
- Avoid calling Services and Selectors from the methods inside Models.
- Model methods should only touch the model itself and directly-related models like `cart.lines`, not unrelated aggregates.
- Foreign key and many-to-many fields must have a related name (`related_name`) specified.
- Add a `__str__` method to all models for a human-readable representation.
- Ensure database migrations are created after changes to models (`python manage.py makemigrations`).
- Use Django's built-in validators for model fields where applicable (e.g., `EmailField`, `URLField`).
- Avoid using `null=True` on `CharField` and `TextField`; use empty strings instead.
- Use `DateTimeField(auto_now_add=True)` for creation timestamps and `DateTimeField(auto_now=True)` for update timestamps.

### 3.2 Views (`views/`, `views.py`)

- Primary **Service** and **Selector** will be defined as class attributes of the View.
- Prefer **Service** when the use case involves business rules, writes, orchestration, or transactions.
- Use **Selector** for read-only operations.
- Never touch models directly from a View. All ORM access goes through Selectors.

### 3.3 Serializer

- **Purpose**: serialize/deserialize data (+ basic validation).
- Avoid using `ModelSerializer`.
- Avoid running ORM queries or write business logic inside serializers. Use **Services** and **Selectors** instead.
- Avoid `SerializerMethodField` unless the value can't be produced elsewhere (prefer precomputed fields, model properties, or service/selector-enriched data).
- Use nested serializers for related objects, but avoid deep nesting to prevent performance issues.

### 3.4 Service

- Owns business logic + all writes.
- Performs deletes.
- Tightly coupled models (e.g., Cart & CartLine): the parent service orchestrates operations on the child; call `CartService` for add/update/delete of lines—not `CartLineService`.
- Services never read directly from models; they call Selectors. This also reduces service–service cycles.
- A service should avoid calling another service. If it's needed, make sure it's one directional to avoid circular dependencies like `Cart → CartLine` but not `CartLine → Cart`.
- One service initialization inside another service must be **Lazy**. So, we will not initialise all the services inside `__init__`.

**Example of lazy initialization:**

```python
class CartService(BaseModelService):
    model = Cart

    def __init__(self, tenant_code: str, site_profile: SiteProfile):
        self.tenant_code = tenant_code
        self.site_profile = site_profile

    @cached_property
    def contact_service(self) -> ContactService:
        return ContactService(
            tenant_code=self.tenant_code,
            site_profile=self.site_profile,
        )
```

### 3.5 Selector

- Owns all ORM reads.
- Returns ORM instances or QuerySets (not dicts/DTOs).
- Read-only, pure query methods only.
- Enforce read permissions here (e.g., tenant scoping, ownership).
- Avoid calling **Service** from **Selector**.
- Avoid selector→selector cycles; if needed, keep it one-direction only to avoid circular dependencies.
- For tightly coupled models (Cart/CartLine), there will be only one selector for the parent model (Cart in this case) that will have the query methods for the child models.
- Use `select_related` / `prefetch_related` to prevent N+1 in aggregated selectors.
- Use `annotate` to add computed fields to QuerySets when needed.
- Use `values` / `values_list` when only a subset of fields is needed for performance.
- Use `Q` objects for complex queries involving OR conditions.
- Use `exists()` for existence checks instead of fetching objects when only a boolean result is needed.
- Use `defer()` and `only()` to optimize queries by loading only necessary fields.

### 3.6 Dataclasses as DTO (Data Transfer Object)

- DTOs are introduced to clearly define what data are being passed from one layer to another (e.g., from service to view).
- Heavy usage is difficult within the existing PH system, so we are using it where relevant (e.g., `EnrichedProduct`). For new projects, we can think differently.
- We are using **pydantic dataclasses** (https://docs.pydantic.dev/2.10/concepts/dataclasses/) instead of regular Python dataclasses.
  - Benefits: nested dataclasses from nested dicts, validations, etc.
- A single model can have multiple DTOs for different purposes.

---

## 4) Testing — Agent Responsibilities

- New tests live in `tests`.
- Use `pytest` for all test cases.
- Run `pre-commit run --files <changed files>` and `pytest tests` before committing.
- Mark database tests with `pytest.mark.django_db`.

---

## 6) Logging and Monitoring

**TBD**

---

## 7) Security Guidelines (MUST)

- Never expose database id in APIs; prefer opaque identifiers (e.g., uuid).
- Apply proper permissions at view level and ownership checks at Selector and Service level as needed.
- Whitelist query params—accept only known keys and types.
- **Validate User Input**: Always validate and sanitize all user-submitted data, especially in forms. Reject malicious characters in text inputs; validate & sanitize.
