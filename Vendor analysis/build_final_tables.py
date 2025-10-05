#!/usr/bin/env python3
# build_final_tables.py
from pathlib import Path
import sqlite3, time, argparse, logging
import pandas as pd

# ---------- utils ----------
def connect(db_path: str) -> sqlite3.Connection:
    Path("logs").mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)
    # pragmatic speed-ups (safe)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-500000;")
    return conn

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(),
                  logging.FileHandler("logs/build_final_tables.log", mode="a")]
    )

def require_tables(conn: sqlite3.Connection, names: list[str]):
    have = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    missing = [n for n in names if n not in have]
    if missing:
        raise RuntimeError(f"Missing base tables in DB: {missing}")

def ensure_indexes(conn: sqlite3.Connection):
    logging.info("Ensuring indexes…")
    conn.executescript("""
    CREATE INDEX IF NOT EXISTS idx_sales_inventory      ON sales(InventoryId);
    CREATE INDEX IF NOT EXISTS idx_purchases_inventory  ON purchases(InventoryId);
    CREATE INDEX IF NOT EXISTS idx_purchases_vendor     ON purchases(VendorNumber, Brand);
    CREATE INDEX IF NOT EXISTS idx_vi_vendor            ON vendor_invoice(VendorNumber);
    """)

# ---------- build steps ----------
def build_vendor_sales_summary(conn: sqlite3.Connection):
    logging.info("Building vendor_sales_summary (brand-level with qty + freight allocation)…")
    conn.executescript("""
    DROP TABLE IF EXISTS vendor_sales_summary;
    CREATE TABLE vendor_sales_summary AS
    WITH
    sales_agg AS (
      SELECT p.VendorNumber, p.VendorName, s.Brand,
             SUM(s.SalesQuantity) AS TotalSalesQuantity,
             SUM(s.SalesDollars)  AS TotalSalesDollars
      FROM sales s
      JOIN purchases p ON p.InventoryId = s.InventoryId
      GROUP BY p.VendorNumber, p.VendorName, s.Brand
    ),
    brand_purch AS (
      SELECT p.VendorNumber, p.Brand,
             SUM(p.Quantity)                   AS BrandPurchaseQuantity,
             SUM(p.PurchasePrice * p.Quantity) AS BrandPurchaseDollars
      FROM purchases p
      GROUP BY p.VendorNumber, p.Brand
    ),
    bp_vendor_tot AS (
      SELECT VendorNumber,
             SUM(BrandPurchaseDollars) AS VendorBrandPurchDollars
      FROM brand_purch
      GROUP BY VendorNumber
    ),
    vi AS (
      SELECT VendorNumber,
             SUM(Quantity) AS InvoicePurchaseQuantity,
             SUM(Dollars)  AS InvoicePurchaseDollars,
             SUM(Freight)  AS Freight
      FROM vendor_invoice
      GROUP BY VendorNumber
    ),
    joined AS (
      SELECT
        s.VendorNumber,
        s.VendorName,
        s.Brand,
        COALESCE(s.TotalSalesQuantity,0)       AS TotalSalesQuantity,
        COALESCE(s.TotalSalesDollars,0)        AS TotalSalesDollars,
        COALESCE(bp.BrandPurchaseQuantity,0)   AS TotalPurchaseQuantity,
        COALESCE(bp.BrandPurchaseDollars,0)    AS TotalPurchaseDollars,
        CASE
          WHEN COALESCE(vi.Freight,0) > 0 AND COALESCE(t.VendorBrandPurchDollars,0) > 0
            THEN vi.Freight * COALESCE(bp.BrandPurchaseDollars,0) * 1.0 / t.VendorBrandPurchDollars
          ELSE 0
        END AS FreightCost
      FROM sales_agg s
      LEFT JOIN brand_purch   bp ON bp.VendorNumber = s.VendorNumber AND bp.Brand = s.Brand
      LEFT JOIN bp_vendor_tot t  ON t.VendorNumber  = s.VendorNumber
      LEFT JOIN vi              ON vi.VendorNumber = s.VendorNumber
    )
    SELECT
      *,
      (TotalSalesDollars - TotalPurchaseDollars - FreightCost) AS GrossProfit,
      CASE WHEN TotalSalesDollars > 0
           THEN 100.0 * (TotalSalesDollars - TotalPurchaseDollars - FreightCost) / TotalSalesDollars
           ELSE 0 END AS ProfitMargin
    FROM joined;
    """)

def build_vendor_rollup(conn: sqlite3.Connection):
    logging.info("Building vendor_summary_by_vendor (rollup with quantities)…")
    conn.executescript("""
    DROP TABLE IF EXISTS vendor_summary_by_vendor;
    CREATE TABLE vendor_summary_by_vendor AS
    SELECT
      VendorNumber,
      MAX(VendorName)                         AS VendorName,
      SUM(TotalSalesDollars)                  AS TotalSalesDol_in_summary,
      SUM(TotalSalesQuantity)                 AS TotalSalesQty,
      SUM(TotalPurchaseDollars)               AS TotalPurchaseDol,
      SUM(TotalPurchaseQuantity)              AS TotalPurchaseQty,
      SUM(FreightCost)                        AS FreightCost,
      SUM(TotalSalesDollars - TotalPurchaseDollars - FreightCost) AS GrossProfit,
      CASE WHEN SUM(TotalSalesDollars) > 0
           THEN 100.0 * (SUM(TotalSalesDollars) - SUM(TotalPurchaseDollars) - SUM(FreightCost)) / SUM(TotalSalesDollars)
           ELSE 0 END AS ProfitMargin,
      COUNT(DISTINCT Brand)                   AS BrandCount
    FROM vendor_sales_summary
    GROUP BY VendorNumber;
    """)

def build_spend_and_risk(conn: sqlite3.Connection):
    logging.info("Building spend_by_vendor and vendor_risk_flags…")
    conn.executescript("""
    DROP TABLE IF EXISTS spend_by_vendor;
    CREATE TABLE spend_by_vendor AS
    SELECT
      vi.VendorNumber,
      SUM(vi.Dollars)  AS TotalPurchaseDollars,
      (SELECT COALESCE(SUM(TotalSalesDollars),0)
         FROM vendor_sales_summary s
         WHERE s.VendorNumber = vi.VendorNumber) AS TotalSalesDollars
    FROM vendor_invoice vi
    GROUP BY vi.VendorNumber;

    DROP TABLE IF EXISTS vendor_risk_flags;
    CREATE TABLE vendor_risk_flags AS
    SELECT VendorNumber,
           SUM(CASE WHEN TotalSalesQuantity    < 0 THEN 1 ELSE 0 END) AS neg_SalesQty,
           SUM(CASE WHEN TotalSalesDollars     < 0 THEN 1 ELSE 0 END) AS neg_SalesDol,
           SUM(CASE WHEN TotalPurchaseQuantity < 0 THEN 1 ELSE 0 END) AS neg_PurchQty,
           SUM(CASE WHEN TotalPurchaseDollars  < 0 THEN 1 ELSE 0 END) AS neg_PurchDol,
           SUM(CASE WHEN FreightCost           < 0 THEN 1 ELSE 0 END) AS neg_Freight
    FROM vendor_sales_summary
    GROUP BY VendorNumber;
    """)

def build_brand_pricing(conn: sqlite3.Connection):
    logging.info("Building brand_pricing…")
    conn.executescript("""
    DROP TABLE IF EXISTS brand_pricing;
    CREATE TABLE brand_pricing AS
    SELECT
      VendorNumber, VendorName, Brand,
      SUM(TotalSalesQuantity)    AS TotalSalesQuantity,
      SUM(TotalSalesDollars)     AS TotalSalesDollars,
      SUM(TotalPurchaseDollars)  AS TotalPurchaseDollars,
      SUM(FreightCost)           AS FreightCost
    FROM vendor_sales_summary
    GROUP BY VendorNumber, VendorName, Brand;
    """)

def build_brand_pricing_opps(conn: sqlite3.Connection, target_margin: float):
    logging.info("Building brand_pricing_opportunities… target=%.2f", target_margin)
    conn.execute("DROP TABLE IF EXISTS brand_pricing_opportunities;")
    conn.execute("""
    CREATE TABLE brand_pricing_opportunities AS
    WITH b AS (
      SELECT *,
             CASE WHEN TotalSalesDollars > 0
                  THEN TotalSalesDollars/(TotalSalesQuantity*1.0)
                  ELSE NULL END AS AvgSalesPrice,
             CASE WHEN TotalPurchaseDollars > 0
                  THEN TotalPurchaseDollars/(TotalSalesQuantity*1.0)
                  ELSE NULL END AS AvgPurchasePrice
      FROM brand_pricing
    ),
    need AS (
      SELECT *,
             CASE
               WHEN (TotalPurchaseDollars + FreightCost) <= 0 THEN 0
               ELSE (TotalPurchaseDollars + FreightCost) * 1.0 / (1.0 - ?)
             END AS RequiredSalesDollars
      FROM b
    ),
    calc AS (
      SELECT *,
             CASE WHEN RequiredSalesDollars > TotalSalesDollars
                  THEN RequiredSalesDollars - TotalSalesDollars ELSE 0 END AS UpsideDollars,
             CASE WHEN TotalSalesQuantity > 0
                  THEN (CASE WHEN RequiredSalesDollars > TotalSalesDollars
                             THEN (RequiredSalesDollars - TotalSalesDollars)/(TotalSalesQuantity*1.0)
                             ELSE 0 END)
                  ELSE NULL END AS NeededPriceDeltaPerUnit
      FROM need
    )
    SELECT
      VendorNumber, VendorName, Brand,
      TotalSalesQuantity, TotalSalesDollars, TotalPurchaseDollars, FreightCost,
      AvgSalesPrice,
      ? AS TargetMargin,
      RequiredSalesDollars, UpsideDollars, NeededPriceDeltaPerUnit
    FROM calc
    """, (target_margin, target_margin))

def build_finals(conn: sqlite3.Connection):
    logging.info("Building final_vendor / final_brand / final_all…")
    conn.executescript("""
    DROP TABLE IF EXISTS final_vendor;
    CREATE TABLE final_vendor AS
    SELECT
      v.VendorNumber, v.VendorName,
      v.TotalSalesDol_in_summary AS TotalSalesDollars,
      v.TotalSalesQty            AS TotalSalesQuantity,
      v.TotalPurchaseDol         AS TotalPurchaseDollars,
      v.TotalPurchaseQty         AS TotalPurchaseQuantity,
      v.FreightCost,
      v.GrossProfit,
      v.ProfitMargin             AS CurrentMargin,
      NULL AS TargetMargin, NULL AS RequiredSalesDollars,
      NULL AS UpsideDollars, NULL AS NeededPriceDeltaPerUnit
    FROM vendor_summary_by_vendor v;

    DROP TABLE IF EXISTS final_brand;
    CREATE TABLE final_brand AS
    SELECT
      s.VendorNumber, s.VendorName, s.Brand,
      s.TotalSalesDollars, s.TotalSalesQuantity,
      s.TotalPurchaseDollars, s.TotalPurchaseQuantity,
      s.FreightCost,
      s.GrossProfit,
      s.ProfitMargin            AS CurrentMargin,
      bpo.TargetMargin,
      bpo.RequiredSalesDollars, bpo.UpsideDollars, bpo.NeededPriceDeltaPerUnit
    FROM vendor_sales_summary s
    LEFT JOIN brand_pricing_opportunities bpo
      ON bpo.VendorNumber = s.VendorNumber AND bpo.Brand = s.Brand;

    DROP TABLE IF EXISTS final_all;
    CREATE TABLE final_all AS
    SELECT 'vendor' AS Level, VendorNumber, VendorName, NULL AS Brand,
           TotalSalesDollars, TotalSalesQuantity, TotalPurchaseDollars, TotalPurchaseQuantity,
           FreightCost, GrossProfit, CurrentMargin, NULL AS BrandCount,
           TargetMargin, RequiredSalesDollars, UpsideDollars, NeededPriceDeltaPerUnit
    FROM final_vendor
    UNION ALL
    SELECT 'brand'  AS Level, VendorNumber, VendorName, Brand,
           TotalSalesDollars, TotalSalesQuantity, TotalPurchaseDollars, TotalPurchaseQuantity,
           FreightCost, GrossProfit, CurrentMargin, NULL AS BrandCount,
           TargetMargin, RequiredSalesDollars, UpsideDollars, NeededPriceDeltaPerUnit
    FROM final_brand;
    """)

def export_csvs(conn: sqlite3.Connection, outdir: Path):
    logging.info("Exporting CSVs to %s", outdir)
    outdir.mkdir(exist_ok=True)
    for name in [
        "vendor_sales_summary",
        "vendor_summary_by_vendor",
        "spend_by_vendor",
        "vendor_risk_flags",
        "brand_pricing",
        "brand_pricing_opportunities",
        "final_vendor",
        "final_brand",
        "final_all",
    ]:
        df = pd.read_sql(f"SELECT * FROM {name};", conn)
        df.to_csv(outdir / f"{name}.csv", index=False)

# ---------- main ----------
def main():
    setup_logging()
    p = argparse.ArgumentParser(description="Build vendor analytics summary tables")
    p.add_argument("--db", default="inventory.db", help="Path to SQLite DB")
    p.add_argument("--target", type=float, default=0.35, help="Target margin (e.g., 0.35 for 35%)")
    args = p.parse_args()

    t0 = time.time()
    conn = connect(args.db)
    logging.info("Connected to %s", args.db)

    try:
        # Only the 3 base tables we actually use
        require_tables(conn, ["purchases", "vendor_invoice", "sales"])
        ensure_indexes(conn)
        build_vendor_sales_summary(conn)
        build_vendor_rollup(conn)
        build_spend_and_risk(conn)
        build_brand_pricing(conn)
        build_brand_pricing_opps(conn, args.target)
        build_finals(conn)
        export_csvs(conn, Path("outputs"))
        conn.execute("ANALYZE;")
    finally:
        conn.close()

    logging.info("Done in %.2f min. CSVs in outputs/, tables in %s",
                 (time.time()-t0)/60.0, args.db)

if __name__ == "__main__":
    main()

