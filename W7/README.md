# Retail Data Warehouse ETL

## Run
Open the notebook in Google Colab, upload the provided XLSX dataset, then Run all.

## Pipeline
Extract -> Transform -> Validate -> Quarantine -> Load

## Star Schema
- dim_customer
- dim_product
- dim_date
- fact_sales

## Idempotency
fact_sales uses order_id as the primary key. Re-running an existing batch does not create duplicate fact rows. A record is updated only when its updated_at is newer.

## Outputs
- retail_dw.db
- quarantine.csv
- pipeline_run_log.csv
