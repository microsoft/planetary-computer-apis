from opencensus.ext.azure import metrics_exporter
from opencensus.stats import stats as stats_module

from pccommon.config import CommonConfig

_config = CommonConfig.from_environment()

_instrumentation_key = _config.app_insights_instrumentation_key

if _instrumentation_key:
    _exporter = metrics_exporter.new_metrics_exporter(
        connection_string=f"InstrumentationKey={_instrumentation_key}"
    )

    stats = stats_module.stats
    view_manager = stats.view_manager
    view_manager.register_exporter(_exporter)

    stats_recorder = stats.stats_recorder
else:
    view_manager = None
    stats_recorder = None
