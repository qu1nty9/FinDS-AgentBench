# Audit Note

The flawed workflow uses `feature_future_return_leak`, which is target-derived future information unavailable at the prediction timestamp. This feature must be removed before reporting valid performance.

The workflow also uses a random row split even though the data has temporal structure. A corrected workflow should use a chronological train, public validation, and private temporal holdout split.

Finally, preprocessing is fit on the full dataset. The scaler or any preprocessing step should be fit only on the training period, then applied to later validation and holdout periods.

After removing the leaked feature and using temporal validation, the corrected score is lower than the flawed score. The lower corrected score is the valid result.

