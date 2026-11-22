def query_target_spread(store, target_name):
    return store.threats_by_target(target_name) if hasattr(store, 'threats_by_target') else store.common_targets(target_name)
