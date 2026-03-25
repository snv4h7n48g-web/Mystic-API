def filter_tarot_continuity(context: dict | None) -> dict | None:
    if not context:
        return context
    recent = context.get('recent_flow_types') or []
    filtered = [flow for flow in recent if flow == 'tarot_solo']
    next_context = dict(context)
    next_context['recent_flow_types'] = filtered
    if next_context.get('latest_flow_type') != 'tarot_solo':
        next_context['latest_flow_type'] = filtered[0] if filtered else None
    return next_context
