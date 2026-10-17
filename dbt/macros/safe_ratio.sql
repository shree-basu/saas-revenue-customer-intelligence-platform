{% macro safe_ratio(numerator, denominator) -%}
    (case when ({{ denominator }}) is null or ({{ denominator }}) = 0
        then null else ({{ numerator }}) / ({{ denominator }}) end)
{%- endmacro %}
