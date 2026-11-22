def query_threat_history(store, source_name):
    return store.history_by_source(source_name)
