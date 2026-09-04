# ETL Lab Report

Student ID: 67160167
Name: Chanawit Teetung

## 1. Data Quality Problems Found
- **Duplicate Records**: พบข้อมูลซ้ำใน `customers.csv` (เช่น customer_id `C004`, `C009`) และ `orders.csv` (เช่น order_id `O0011`, `O0041`, `O0101`)
- **Inconsistent String Formats & Case**: ชื่อจังหวัดใน `customers.csv` มีหลายรูปแบบทั้งพิมพ์เล็ก/พิมพ์ใหญ่/ภาษาไทย/ตัวย่อ (เช่น `chon buri`, `ชลบุรี`, `BKK`, `กรุงเทพฯ`, `chantaburi`) และ `status` ใน `orders.csv` ตัวพิมพ์เล็ก/พิมพ์ใหญ่ไม่สม่ำเสมอ (เช่น `PAID`, `paid`, `completed`)
- **Missing Values**: พบค่าว่างในช่อง `email` และ `province` ใน `customers.csv` รวมถึง `category.name` ใน `products.json`
- **Invalid Data Types**: ราคา `pricing.price` ใน `products.json` มีข้อมูลที่เป็น String มีเครื่องหมายจุลภาค (เช่น `"1,299.00"`)
- **Mixed Date Formats & Invalid Dates**: วันที่ใน `orders.csv` มีหลายรูปแบบผสมกัน (เช่น `YYYY/MM/DD`, `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-Mon-YYYY`) และมีวันที่ที่ไม่ถูกต้อง (เช่น `not-a-date`)
- **Out of Range / Invalid Numeric Values**: พบค่าปริมาณสินค้าติดลบ (`qty <= 0`), ราคาสินค้าติดลบ (`unit_price <= 0`), และเปอร์เซ็นต์ส่วนลดเกินกำหนด (`discount_pct > 100`)
- **Orphan / Missing Foreign Keys**: พบ `customer_id` (`C999`) และ `product_id` (`P999`) ใน `orders.csv` ที่ไม่มีอยู่ใน master tables

## 2. Cleaning / Transformation Rules
- **Deduplication**: ใช้ `.drop_duplicates()` ลบแถวซ้ำโดยอ้างอิง `customer_id` ใน Customers และ `order_id` ใน Orders
- **Standardize Province**: แปลงค่า `province` โดยลบช่องว่าง แปลงเป็นตัวพิมพ์เล็ก แล้วทำ mapping ผ่าน dictionary `PROVINCE_MAP` หากไม่พบข้อมูลให้เติมด้วย `"Unknown"`
- **Standardize Status**: แปลง `status` ให้เป็นตัวพิมพ์เล็กทั้งหมด (`paid`, `completed`, `pending`, `cancelled`)
- **Numeric Conversion & Parsing**: แปลง `price` ใน Products โดยลบเครื่องหมาย `,` ออก แล้วแปลงเป็น `float` และเติมค่า `category` ที่เป็นค่าว่างด้วย `"Unknown"`
- **Date Standardization**: ใช้ `pd.to_datetime(..., format='mixed', errors='coerce')` เพื่อแปลงวันที่ให้อยู่ในฟอร์แมตมาตรฐาน `YYYY-MM-DD` หากเป็นวันที่ไม่ถูกต้องจะกลายเป็น `NaT`
- **Rejection Logic**: กรองและแยกรายการที่ผิดกฎธุรกิจเข้า `rejects.csv` (ได้แก่ `qty <= 0`, `unit_price <= 0`, `discount_pct < 0` หรือ `> 100`, วันที่เป็น `NaT`, หรือ `customer_id`/`product_id` ไม่มีใน master)
- **Filtering Sales**: กรองเฉพาะคำสั่งซื้อที่มีสถานะเป็น `paid` หรือ `completed` สำหรับคำนวณยอดขาย
- **Calculations**: คำนวณ `gross_amount = qty * unit_price`, `discount_amount = gross_amount * discount_pct / 100`, และ `sales_amount = gross_amount - discount_amount`

## 3. Rejected Records
จำนวน: 6 รายการ

เหตุผลหลัก:
1. `qty <= 0` (order_id `O0007` มี qty = -2)
2. `discount_pct < 0` หรือ `> 100` (order_id `O0021` มี discount_pct = 150)
3. วันที่ไม่ถูกต้อง `invalid order_date` (order_id `O0034` มี order_date = "not-a-date")
4. ไม่พบ `customer_id` ใน master table (order_id `O0049` ใช้ customer_id = "C999")
5. ไม่พบ `product_id` ใน master table (order_id `O0076` ใช้ product_id = "P999")
6. `unit_price <= 0` (order_id `O0091` มี unit_price = -100.0)

## 4. ETL Validation
- Valid transformed rows: 100
- Warehouse rows: 100
- Duplicate order_id: 0
- Source total sales: 192074.66
- Warehouse total sales: 192074.66
- Validation status: PASS

## 5. Idempotency Test
จำนวน fact_sales หลัง run ครั้งที่ 1: 100

จำนวน fact_sales หลัง run ครั้งที่ 2: 100

อธิบายผล:
เมื่อรัน Pipeline ซ้ำเป็นครั้งที่ 2 จำนวนข้อมูลในตาราง `fact_sales` ยังคงเท่าเดิมที่ 100 รายการ และไม่เกิดข้อผิดพลาด Primary Key Duplicate หรือข้อมูลซ้ำซ้อน เนื่องจากในชั้น Load ได้ออกแบบโครงสร้างตาราง SQLite โดยกำหนด `PRIMARY KEY` บนคอลัมน์ `order_id` และใช้คำสั่ง `INSERT OR REPLACE INTO` ซึ่งจะทำการอัปเดตเรคคอร์ดเดิมแทนการเพิ่มแถวใหม่ ทำให้ Pipeline มีคุณสมบัติ Idempotent สามารถ rerun ได้อย่างปลอดภัย
