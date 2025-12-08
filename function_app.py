import datetime
import logging
import azure.functions as func
from etl_pipeline import main as etl_main

app = func.FunctionApp()


@app.function_name(name="FinSightETLTimer")
@app.schedule(schedule="0 0 */6 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False)
def run_etl(mytimer: func.TimerRequest) -> None:
    """Azure Function timer trigger to run the ETL pipeline."""
    utc_timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    logging.info(f"FinSight ETL Timer triggered at {utc_timestamp}")

    try:
        etl_main.main()
        logging.info("ETL pipeline executed successfully.")
    except Exception as e:
        logging.error(f"ETL execution failed: {e}", exc_info=True)
