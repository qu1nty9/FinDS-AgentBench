joined = pd.merge_asof(features, macro, on="date", direction="forward")
