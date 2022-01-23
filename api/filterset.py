from django_filters import FilterSet, DateFilter

from cms.models import HealthDataHistory


class HealthDataHistoryFilterSet(FilterSet):
    start_at = DateFilter(
        label='Start At',
        field_name='create',
        lookup_expr='gte'
    )
    end_at = DateFilter(
        label='End At',
        field_name='create',
        lookup_expr='lte'
    )

    class Meta:
        model = HealthDataHistory
        fields = []
