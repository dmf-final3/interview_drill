from django import template

register = template.Library()

@register.filter(name='parse_interview')
def parse_interview(value):
    # 필터 로직
    return "Processed value"