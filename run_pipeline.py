from src import diferential_privacy, extract, transform, versioning
import yaml

with open("config/pipeline.yaml") as f:
    cfg = yaml.safe_load(f)

privacy_cfg = cfg["privacy"]

data = extract.data_extraction()
df = transform.transform(data)

dp_results, metadata = diferential_privacy.apply_dp(df, privacy_cfg)

import datetime

version_name = "v-" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

versioning.save_version(
    baseline_df = df,
    dp_results = dp_results,
    metadata = metadata,
    version_name = version_name
)
