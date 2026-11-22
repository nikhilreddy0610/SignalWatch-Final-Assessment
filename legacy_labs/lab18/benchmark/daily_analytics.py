def query_daily_analytics(store):
    return store.daily_volume() if hasattr(store, 'daily_volume') else store.daily_patterns()
