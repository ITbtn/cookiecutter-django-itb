from typing import Type, TypeVar, Generic, Dict, Any, Optional, Sequence, List, Union

from django.db import models
from django.db.models import Q, QuerySet
from django.core.exceptions import ObjectDoesNotExist


T = TypeVar("T", bound=models.Model)


class BaseSelector(Generic[T]):
    model_class: Type[T]
    tenant_field: str = "tenant_code"
    not_found_exception = ObjectDoesNotExist  # Default exception - subclasses can override this

    def __init__(self, tenant_code: str, request_user):
        self.tenant_code = tenant_code
        self.request_user = request_user

        # Validate that model_class is properly set
        if not hasattr(self, 'model_class') or self.model_class is None:
            raise ValueError(f"{self.__class__.__name__} must define a model_class attribute")

    def get_filtered_qs(self, 
                       filters: Dict[str, Any] = None, 
                       or_filters: Dict[str, Any] = None,
                       exclude_filters: Dict[str, Any] = None,
                       values_fields: Optional[Sequence[str]] = None,
                       order_by: Optional[List[str]] = None,
                       default_ordering: Optional[Union[str, List[str]]] = None,
                       select_related: Optional[Sequence[str]] = None,
                       prefetch_related: Optional[Sequence[str]] = None) -> QuerySet:
        """
        Get filtered queryset with comprehensive options for filtering and ordering
        
        :param filters: Dictionary for AND conditions (required fields must match)
        :param or_filters: Dictionary for OR conditions (any field can match)
        :param exclude_filters: Dictionary for NOT/EXCLUDE conditions (fields to exclude)
        :param values_fields: Specific fields to return in the queryset
        :param order_by: List of fields to sort by
        :param default_ordering: Default field(s) to sort by if order_by is None
        :param select_related: Fields to join using select_related for performance optimization
        :param prefetch_related: Fields to prefetch using prefetch_related for performance optimization
        :return: Filtered queryset
        """
        # Always apply tenant filtering
        filters = filters.copy() if filters else {}
        filters[self.tenant_field] = self.tenant_code

        # Start with base queryset
        queryset = self.model_class.objects.filter(**filters)

        # Apply OR filters if any
        if or_filters:
            or_condition = None
            for key, val in or_filters.items():
                temp_dict = {key: val}
                if not or_condition:
                    or_condition = Q(**temp_dict)
                else:
                    or_condition |= Q(**temp_dict)
            if or_condition:
                queryset = queryset.filter(or_condition)

        # Apply NOT/EXCLUDE filters if any
        if exclude_filters:
            queryset = queryset.exclude(**exclude_filters)

        # Apply ordering if specified
        if order_by:
            queryset = queryset.order_by(*order_by)
        elif default_ordering:
            if isinstance(default_ordering, list):
                queryset = queryset.order_by(*default_ordering)
            else:
                queryset = queryset.order_by(default_ordering)

        # Apply query optimizations
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        # Apply values() if fields specified
        if values_fields:
            queryset = queryset.values(*values_fields)

        return queryset

    def get_by_uuid(self, uuid: str, filters: Dict[str, Any] = None, values_fields: Optional[Sequence[str]] = None) -> T:
        """Get an object by UUID with custom exception handling"""
        if filters is None:
            filters = {"uuid": uuid}
        else:
            filters = filters.copy()  # Avoid mutating the original filters dictionary
            filters["uuid"] = uuid
        try:
            filtered_qs = self.get_filtered_qs(filters=filters, values_fields=values_fields)
            return filtered_qs.get()
        except ObjectDoesNotExist:
            model_name = self.model_class.__name__ if self.model_class else "Object"
            raise self.not_found_exception(f"{model_name} with uuid={uuid} does not exist")

    def get_by_code(self, code: str, filters: Dict[str, Any] = None, values_fields: Optional[Sequence[str]] = None) -> T:
        """Get an object by code with custom exception handling"""
        if filters is None:
            filters = {"code": code}
        else:
            filters = filters.copy()  # Avoid mutating the original filters dictionary
            filters["code"] = code
        try:
            filtered_qs = self.get_filtered_qs(filters=filters, values_fields=values_fields)
            return filtered_qs.get()
        except ObjectDoesNotExist:
            model_name = self.model_class.__name__ if self.model_class else "Object"
            raise self.not_found_exception(f"{model_name} with code={code} does not exist")

    def get_by_pk(self, pk: Union[int, str], filters: Dict[str, Any] = None, values_fields: Optional[Sequence[str]] = None) -> T:
        """Get an object by primary key with custom exception handling"""
        if filters is None:
            filters = {"pk": pk}
        else:
            filters = filters.copy()  # Avoid mutating the original filters dictionary
            filters["pk"] = pk
        try:
            filtered_qs = self.get_filtered_qs(filters=filters, values_fields=values_fields)
            return filtered_qs.get()
        except ObjectDoesNotExist:
            model_name = self.model_class.__name__ if self.model_class else "Object"
            raise self.not_found_exception(f"{model_name} with pk={pk} does not exist")
