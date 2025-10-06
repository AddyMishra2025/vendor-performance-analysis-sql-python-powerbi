# Vendor Performance Analysis Report (Power BI)

This Power BI project provides a **comprehensive vendor performance analysis**, combining profitability insights, pricing diagnostics, and portfolio risk assessment into a single executive dashboard.  
The goal is to help stakeholders **identify top-performing vendors**, uncover **margin improvement opportunities**, and **optimize procurement decisions** using real-time data intelligence.

---

## 📊 Executive Summary

[Executive Dashboard] - https://github.com/AddyMishra2025/vendor-performance-analysis-sql-python-powerbi/blob/main/Screenshot%202025-10-06%20at%2001.17.30.png

The **Executive Summary Report** consolidates key performance indicators, visual analytics, and diagnostic tables to answer all major business questions in one view.

---

## 🧭 Objectives

- Evaluate overall **financial health** through key KPIs (Sales, Purchases, Profit Margin).
- Highlight **top-performing vendors** and their contribution to total revenue.
- Diagnose **pricing inefficiencies** across brands.
- Identify **underperforming brands** and **vendors at risk**.
- Provide actionable insights for **margin improvement** and **vendor negotiations**.

---

## ⚙️ Features & Highlights

### **1. Financial Health Overview**
- **KPIs:**  
  - Total Sales → **13.01T**  
  - Total Purchases → **251.50bn**  
  - Gross Profit → **1276.19T%**  
  - Profit Margin → **0.98**
- Displays overall business performance at a glance.

### **2. Portfolio & Risk**
- **Underperforming Brands %:** 0.48  
- **Vendors at Risk %:** 1.00  
- **Distinct Vendors:** 124  
- **Distinct Brands:** 10K  
- Quickly identifies concentration risk and diversification status.

### **3. Sales by Top Vendors**
- Bar chart showing **Top 10 Vendors by Total Sales**.
- Helps spot revenue concentration and key strategic partners.

### **4. Pareto Chart (Cumulative Contribution to Sales)**
- Plots **Total Sales vs Total SalesDollars** by brand.
- Visualizes the **80/20 rule**, identifying top contributors to total revenue.

### **5. Vendor Action Scorecard**
- Interactive table showing:
  - **Vendor Name**
  - **Sum of Total Sales Dollars**
  - **Sum of Total Purchase Dollars**
- Tracks vendor contribution and profitability for informed decision-making.

### **6. Total Sales by Brand**
- Donut chart summarizing **sales distribution across all brands**.
- Color-coded by brand IDs to visualize brand-level sales contribution.

### **7. Brand Pricing Diagnostics**
- Detailed comparison table showing:
  - **Avg Sales Price**
  - **Total Purchase Dollars**
  - **Total Sales Dollars**
- Highlights pricing disparities and brand-level performance gaps.

### **8. Pricing Opportunities (Bubble Chart)**
- Scatter plot showing **Total Sales Dollars vs Current Profit Margin %**.
- Each bubble represents a brand — ideal for identifying pricing outliers and improvement potential.

---

## 🧩 Data Model

| Dataset | Purpose | Key Columns |
|----------|----------|-------------|
| `final_all.csv` | Core vendor-brand linkage dataset | VendorNumber, VendorName, Brand, TotalSalesDollars |
| `final_brand.csv` | Brand-level performance data | Brand, GrossProfit, CurrentMargin, TotalSalesDollars |
| `final_vendor.csv` | Vendor-level aggregates | VendorName, TotalSalesDollars, GrossProfit, ProfitMargin |
| `brand_pricing.csv` | Price diagnostics | Brand, AvgSalesPrice, TotalPurchaseDollars |
| `underperforming_brands.csv` | Brands below profitability threshold | Brand, ProfitMargin |
| `top_vendors_by_grossprofit.csv` | Top revenue and margin vendors | VendorName, GrossProfit |
| `bottom_vendors_by_margin.csv` | Vendors with lowest margins | VendorName, ProfitMargin |

---

## 🖥️ Dashboard Components

| Section | Visual Type | Data Source | Purpose |
|----------|--------------|-------------|----------|
| KPIs | Card visuals | `Measures_Table` | Financial health overview |
| Total Sales by Brand | Donut chart | `final_brand` | Brand-level sales share |
| Sales by Top Vendors | Bar chart | `top_vendors_by_grossprofit` | Identify top vendors |
| Pareto Chart | Combo chart | `final_brand` | Revenue distribution |
| Vendor Action Scorecard | Table | `final_vendor` | Vendor-level comparison |
| Brand Pricing Diagnostics | Table | `brand_pricing` | Price and cost evaluation |
| Pricing Opportunities | Bubble chart | `final_brand` | Profit margin improvement zones |

---

## 💡 Key Insights

- **80% of sales** are driven by a small cluster of vendors.  
- **High-margin vendors** include *Diageo North America* and *Pernod Ricard USA*, contributing ~50% of total profit.  
- **Underperforming brands** are minimal (0.48%), indicating strong product portfolio health.  
- **Total price opportunity** across brands ≈ **£4.7M**, representing untapped profitability.  
- **Low-margin vendors** highlight renegotiation or efficiency improvement areas.

---

## 🧰 Tools Used

- **Power BI Desktop** — Data modeling & visualization  
- **Power Query** — Data cleaning & transformation  
- **Microsoft Excel / CSV** — Raw data management  
- **GitHub** — Version control & documentation  
- **DAX Measures** — Custom KPI calculations (e.g., Gross Profit %, Average Spend per Vendor)

---

## 🧱 Folder Structure
Vendor-Performance-Report/
│
├── README.md
├── Vendor_Performance_Analysis_Report.pbix

│
├── /data/
│ ├── final_all.csv
│ ├── final_brand.csv
│ ├── final_vendor.csv
│ ├── brand_pricing.csv
│ ├── underperforming_brands.csv
│ ├── top_vendors_by_grossprofit.csv
│ └── bottom_vendors_by_margin.csv

│
├── /images/
│ ├── executive_summary_report.png
│ ├── vendor_action_scorecard.png
│ └── brand_pricing_diagnostics.png

│
└── /docs/
├── data_model_explanation.md
├── business_questions.md
└── transformation_steps.md


---

## 🚀 How to Use

1. Download the `.pbix` file.  
2. Open it in **Power BI Desktop**.  
3. Under **Transform Data → Data Source Settings**, update file paths if needed.  
4. Refresh the dataset to load visuals.  
5. Interact with slicers, hover tooltips, and vendor tables for drill-down analysis.

---

## 🌐 Publish & Access
To view or share the report online please click the link :
> https://app.powerbi.com/view?r=eyJrIjoiMTFkNWJmYjQtNTIyYi00YzU3LWFiNjEtODViMWU5MjliNDMyIiwidCI6ImVlMWM5MDU5LWQ0MGQtNDQyMy1iZDNiLTVhNjJkYWE5MjUxMiJ9
---

## 🧠 Author

**Adyasa Mishra**  
MSc Strategic Marketing, Cranfield University  
📧 adyasa.mishrawork@gmail.com
🔗 https://www.linkedin.com/in/adyasamishra/

---

## 🪪 License

This project is for **academic and analytical demonstration** purposes.  
All data used is synthetic and does not represent real vendor or brand information.

---


